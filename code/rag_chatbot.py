from openai import OpenAI
from dotenv import load_dotenv
import os
import chromadb
from chromadb.utils import embedding_functions
import json
from typing import Optional, Dict, List
from sentence_transformers import CrossEncoder
import numpy as np
import torch
from torch.nn.functional import sigmoid

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 생성하고 OPENAI_API_KEY를 설정해주세요.")

client = OpenAI(api_key=api_key)

# Cross-encoder 모델 초기화
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def expand_query(query: str, min_length: int = 10) -> str:
    """짧은 쿼리를 LLM을 사용하여 확장"""
    if len(query) > min_length: # 쿼리가 최소 길이보다 크면 쿼리 반환
        return query
        
    system_prompt = """너는 사용자의 짧은 질문을 ESG 컨텍스트에 맞게 더 구체적이고 풍부하게 바꿔주는 전문가야.
    다음 규칙을 따라야 해:
    1. 원래 질문의 의도를 유지하면서 확장
    2. ESG 관련 구체적인 용어나 개념 포함
    3. 검색에 도움될 만한 관련 키워드 추가
    4. 한국어로 자연스럽게 작성
    5. 확장된 질문은 1-2문장으로 제한
    
    예시:
    입력: "탄소배출량?"
    출력: "기업의 탄소배출량 관리와 감축 목표는 어떻게 설정되어 있으며, 어떤 감축 전략을 사용하고 있나요?"
    
    입력: "지배구조"
    출력: "기업의 이사회 구성과 운영체계는 어떻게 되어있으며, 지배구조의 투명성을 어떻게 확보하고 있나요?"
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"다음 질문을 확장해주세요: {query}"}
            ],
            temperature=0.3,  # 일관성을 위해 낮은 temperature 사용
            max_tokens=200
        )
        expanded_query = response.choices[0].message.content.strip()
        print(f"\n원래 질문: {query}")
        print(f"확장된 질문: {expanded_query}\n")
        return expanded_query
    except Exception as e:
        print(f"질문 확장 중 오류 발생: {e}")
        return query

def extract_metadata_filters(query: str) -> Dict[str, str]:
    """사용자 질문에서 메타데이터 필터 추출
       벡터 DB를 검색할 때, 더 좋은 정확도를 위해 필터링 필요
       sections: 필터되는 단어는 추후에 추가 가능
       
       예시:
        query: "탄소배출량 관리 방법"
        return: {"section": "Environment"}
        
        query: "cj의 환경 관리"
        return: {"section": "Environment", "source": "CJ"}
    """
    filters = {}
    
    # 섹션 필터 추출
    sections = {
        "Environment": ["환경", "environment", "기후", "탄소"],
        "Social": ["사회", "social", "직원", "인권", "안전"],
        "Governance": ["지배구조", "governance", "윤리", "준법"]
    }
    
    query_lower = query.lower()
    for section, keywords in sections.items():
        if any(keyword in query_lower for keyword in keywords):
            filters["section"] = section
            break
    
    # 회사명으로 필터링
    companies = {
        "KTNG": ["ktng", "케이티앤지", "kt&g"],
        "CJ": ["cj", "씨제이"],
        "SHINHAN": ["신한", "shinhan"],
        "SAMPYO": ["삼표", "sampyo"]
    }
    
    for company, keywords in companies.items():
        if any(keyword in query_lower for keyword in keywords):
            filters["source"] = company
            break
    
    return filters

def get_relevance_label(score: float) -> str:
    """관련도 점수에 따른 레이블 반환"""
    if score > 0.9:
        return "매우 높은 관련성 🌟"
    elif score > 0.7:
        return "높은 관련성 ⭐"
    elif score > 0.5:
        return "중간 관련성 ✨"
    else:
        return "낮은 관련성 ⚪"

def rerank_documents(query: str, documents: List[str], metadata_list: List[Dict], top_k: int = 5) -> tuple:
    """Cross-encoder를 사용하여 문서 재순위화 (정규화 포함)"""
    # 각 문서와 쿼리의 쌍을 생성
    pairs = [[query, doc] for doc in documents]
    
    # Cross-encoder로 유사도 점수 계산 (Tensor로 반환)
    raw_scores = cross_encoder.predict(pairs, convert_to_numpy=False)
    
    # sigmoid로 점수 정규화 (0~1 범위)
    if not isinstance(raw_scores, torch.Tensor):
        raw_scores = torch.tensor(raw_scores)
    norm_scores = sigmoid(raw_scores).tolist()
    
    # 점수에 따라 문서 정렬
    doc_score_pairs = list(zip(documents, metadata_list, norm_scores))
    doc_score_pairs.sort(key=lambda x: x[2], reverse=True)
    
    # top_k 개의 문서 선택
    reranked_docs = []
    reranked_metadata = []
    reranked_scores = []
    
    for doc, metadata, score in doc_score_pairs[:top_k]:
        reranked_docs.append(doc)
        reranked_metadata.append(metadata)
        reranked_scores.append(score)
    
    return reranked_docs, reranked_metadata, reranked_scores

def get_relevant_context(query: str, collection, initial_k: int = 20, final_k: int = 5, metadata_filters: Optional[Dict[str, str]] = None) -> tuple:
    """사용자 질문과 관련된 문서 검색 (2단계 검색)"""
    try:
        # metadata_filters를 ChromaDB where 절 형식으로 변환
        where_clause = None
        if metadata_filters and len(metadata_filters) > 0:
            # 각 필드에 대해 $eq 연산자를 사용한 조건 생성
            conditions = []
            for field, value in metadata_filters.items():
                conditions.append({
                    field: {"$eq": value}
                })
            
            # 조건이 하나면 그대로 사용, 여러 개면 $and로 결합
            if len(conditions) == 1:
                where_clause = conditions[0]
            else:
                where_clause = {
                    "$and": conditions
                }
            
            print(f"적용된 검색 필터: {where_clause}")  # 디버깅용 출력
        
        # 1단계: 벡터 검색으로 initial_k개 문서 검색
        results = collection.query(
            query_texts=[query],
            n_results=initial_k,
            where=where_clause
        )
        
        # 결과가 없으면 필터 없이 다시 검색
        if not results['documents'][0]:
            print("지정된 필터로 검색된 결과가 없어 전체 검색을 수행합니다.")
            results = collection.query(
                query_texts=[query],
                n_results=initial_k
            )
    except Exception as e:
        print(f"검색 중 오류 발생: {e}")
        print("필터 없이 전체 검색을 수행합니다.")
        # 오류 발생시 필터 없이 검색
        results = collection.query(
            query_texts=[query],
            n_results=initial_k
        )
    
    # 2단계: Cross-encoder로 재순위화
    if results['documents'][0]:
        reranked_docs, reranked_metadata, scores = rerank_documents(
            query,
            results['documents'][0],
            results['metadatas'][0],
            final_k
        )
    else:
        return "", {}
    
    # 메타데이터 요약 정보 수집
    metadata_summary = {
        "sections": set(),
        "subsections": set(),
        "sources": set(),
        "page_ranges": set()
    }
    
    contexts = []
    for i, (doc, metadata, score) in enumerate(zip(reranked_docs, reranked_metadata, scores)):
        # 메타데이터 요약 정보 수집
        metadata_summary["sections"].add(metadata['section'])
        metadata_summary["subsections"].add(metadata['sub_section'])
        metadata_summary["sources"].add(metadata['source'])
        metadata_summary["page_ranges"].add(metadata.get('page_range', '알 수 없음'))
        
        # 관련도 레이블 생성
        relevance_label = get_relevance_label(score)
        
        # 문맥 구성 (유사도 점수와 레이블 포함)
        context = f"""
                    출처: {metadata['source']}
                    섹션: {metadata['section']}
                    서브섹션: {metadata['sub_section']}
                    페이지: {metadata.get('page_range', '알 수 없음')}
                    관련도: {score:.4f} ({relevance_label})
                    내용: {doc}
                    ---"""
        contexts.append(context)
    
    return "\n".join(contexts), metadata_summary

def generate_response(query: str, context: str, metadata_summary: Dict):
    """파인튜닝된 모델을 사용하여 응답 생성"""
    # 메타데이터 요약 문자열 생성
    metadata_info = f"""
    참고한 문서 정보:
    - 섹션: {', '.join(metadata_summary['sections'])}
    - 서브섹션: {', '.join(metadata_summary['subsections'])}
    - 출처: {', '.join(metadata_summary['sources'])}
    - 페이지: {', '.join(metadata_summary['page_ranges'])}
    """
    
    system_prompt = f"""
당신은 기업의 ESG(환경·사회·지배구조) 경영 도입을 돕는 RAG(Retrieval-Augmented Generation) 챗봇입니다.  
**답변을 생성하기 전에 반드시 context를 먼저 참고해야 합니다.**  
**답변은 항상 마크다운(Markdown) 형식으로 제공해야 합니다.**  
기업이 묻는 질문에 대해 사내/외부 ESG 보고서, 가이드라인, 사례 데이터베이스 등을 실시간으로 탐색·조회하여, 아래 각 섹션의 목적과 예시를 참고해 상세하고 이해하기 쉬운 답변을 생성하십시오.  
답변 시, 아래 각 섹션 제목은 반드시 큰 제목(레벨 2: `##`)으로 표시하고, 앞에 번호를 붙여야 합니다.  
또한, 답변 마지막에는 질문에 대한 **간단한 한 줄 요약**을 포함해야 합니다.

---

## 1. 개요·정의  
- **목적**: 사용자가 질문한 주제(예: 온실가스 감축, 재생에너지 전환 등)를 한두 문장으로 명확히 설명하여, 기본 개념을 이해할 수 있게 합니다.  
- **작성 팁**:  
  - 핵심 키워드(예: “탄소중립”, “Scope 1·2·3”)를 정의하고, 왜 중요한지 간단히 언급합니다.  
  - 너무 전문 용어만 나열하지 말고, 비전문가도 한눈에 알 수 있도록 쉽게 설명합니다.  
- **예시**:  
  > “온실가스 감축 목표는 기업이 배출하는 온실가스를 특정 기간 내에 얼마나 줄일지를 수치로 정하는 것을 말합니다. 이를 통해 기후변화 리스크를 낮추고, 이해관계자의 신뢰를 확보할 수 있습니다.”

---

## 2. 배경·맥락  
- **목적**: 해당 주제가 왜 지금 중요한지를 산업 동향, 규제 변화, 시장 요구 관점에서 설명하여 답변의 설득력을 높입니다.  
- **작성 팁**:  
  - 국내외 주요 규제(예: 탄소세 도입, TCFD 의무화 등)와 업계 트렌드(예: 지속가능 공급망, 그린테인먼트 등)를 간략히 언급합니다.  
  - 기업 규모·업종별 차별화된 맥락이 있으면 추가합니다(예: 대규모 화학업체 vs. 중소형 제조업체).  
- **예시**:  
  > “최근 글로벌 제조업체들은 탄소 국경세(Carbon Border Adjustment Mechanism) 도입 가능성에 대비하여 생산 과정에서 탄소를 줄이는 노력을 강화하고 있습니다. 국내에서도 정부가 2030 국가 온실가스 감축 목표(NDC)를 상향 조정함에 따라, 제조업계 전반에 구체적 감축 계획 제출을 요구하고 있습니다.”

---

## 3. ESG 핵심 지표(KPI)  
- **목적**: 기업이 측정·보고해야 할 주요 지표를 구체적으로 제시하여 실무 적용성을 높입니다.  
- **작성 팁**:  
  1. **환경(E)** 축에서 2~3가지 대표 지표를 제시하고, 각각의 수치 옆에 가능하면 **“(출처: RAG 데이터베이스 [문서명])”** 형태로 출처를 명시합니다.  
     - 예:  
       - **온실가스 배출량 감축 목표**: 2030년까지 Scope 1·2 배출량 **42% 감축** (출처: RAG 데이터베이스 'SAMPYO')  
       - **Scope 3 배출량 관리**: 2030년까지 **25% 감축** (출처: RAG 데이터베이스 'SAMPYO')  
       - **재생에너지 사용 비율**: 2030년까지 **80% 도입 목표** (출처: RAG 데이터베이스 'SAMPYO')  
  2. **사회(S)** 축에서는 협력사나 내부 직원 대상 지표를 2~3가지 제시합니다.  
     - 예:  
       - **임직원 환경 교육 이수율**: **100% 달성** (출처: RAG 데이터베이스 'SAMPYO')  
       - **협력사 온실가스 관리 매뉴얼 배포율**: **100%** (출처: RAG 데이터베이스 'SAMPYO')  
  3. **지배구조(G)** 축에서는 이사회 구조 및 내부 관리 체계 관련 지표를 2~3가지 제시합니다.  
     - 예:  
       - **이사회 독립 이사 비율**: **50% 이상** (출처: RAG 데이터베이스 'SAMPYO')  
       - **반부패 교육 이수율**: **100%** (출처: RAG 데이터베이스 'SAMPYO')  
- **예시 문장**:  
  > “※ 아래 KPI는 RAG 데이터를 기반으로 참고한 예시입니다.”  
  >  
  > - **환경(E)**  
  >   1. **온실가스 배출량 감축 목표**: 2030년까지 Scope 1·2 배출량 **42% 감축** (출처: RAG 데이터베이스 'SAMPYO')  
  >   2. **Scope 3 배출량 감축**: 2030년까지 **25% 감축** (출처: RAG 데이터베이스 'SAMPYO')  
  >   3. **재생에너지 사용 비율**: 2030년까지 **80% 도입 목표** (출처: RAG 데이터베이스 'SAMPYO')  
  >  
  > - **사회(S)**  
  >   1. **임직원 환경 교육 이수율**: **100% 달성** (출처: RAG 데이터베이스 'SAMPYO')  
  >   2. **협력사 온실가스 관리 매뉴얼 배포율**: **100%** (출처: RAG 데이터베이스 'SAMPYO')  
  >  
  > - **지배구조(G)**  
  >   1. **이사회 독립 이사 비율**: **50% 이상** (출처: RAG 데이터베이스 'SAMPYO')  
  >   2. **반부패 교육 이수율**: **100%** (출처: RAG 데이터베이스 'SAMPYO')  

---

## 4. 단계별 실행 로드맵  
- **목적**: 구체적 일정을 제시하여, 기업이 실제로 언제 어떤 활동을 해야 하는지 한눈에 파악할 수 있도록 합니다.  
- **작성 팁**:  
  1. **1차(0~6개월)**:  
     - **예시 활동**과 **기간(개월)** 정보를 함께 제공합니다.  
     - 예:  
       1. **내부 ESG 현황 진단 및 온실가스 배출량 측정** (1~2개월)  
          - 현재 사용 중인 에너지원 파악, 연간 배출량 계산  
       2. **SBTi(Science Based Targets initiative) 기반 목표 수립 워크숍** (3~4개월)  
          - SBTi 가이드라인을 참고해 단계별 감축 목표 설정  
       3. **데이터 수집·관리 체계 구축** (5~6개월)  
          - ERP·MES 등 시스템 연동을 통해 실시간 온실가스 데이터 수집  
  2. **2차(7~12개월)**:  
     - 첫 단계에서 정의한 KPI를 실제 활동으로 이어갈 수 있게 구체화합니다.  
     - 예:  
       1. **재생에너지 구매 계약 체결 및 설비 전환** (7~8개월)  
          - 태양광·풍력 등 재생에너지 공급사와 계약 체결  
       2. **협력사 온실가스 관리 매뉴얼 배포 및 교육** (9~10개월)  
          - 협력사 담당자를 대상으로 온실가스 관리 사례 공유 워크숍 개최  
       3. **첫 번째 중간 보고서 발간 및 이해관계자 커뮤니케이션** (11~12개월)  
          - 투자자·금융기관 대상 IR 자료로 활용하며, 진행 현황 보고  
- **예시 문장**:  
  > - **1차(0~6개월)**  
  >   1. 내부 ESG 현황 진단 및 온실가스 배출량 측정 (1~2개월)  
  >   2. SBTi 기반 온실가스 감축 목표 수립 워크숍 (3~4개월)  
  >   3. 데이터 수집·관리 체계 구축 (5~6개월)  
  >  
  > - **2차(7~12개월)**  
  >   1. 재생에너지 구매 계약 체결 및 설비 전환 (7~8개월)  
  >   2. 협력사 온실가스 관리 매뉴얼 배포·교육 (9~10개월)  
  >   3. 첫 번째 중간 보고서 발간 및 이해관계자 커뮤니케이션 (11~12개월)  

---

## 5. 구체적 사례(표 형식)  
- **목적**: 실제 기업들의 성공 사례를 표로 제시하여, 벤치마킹할 수 있도록 합니다.  
- **작성 팁**:  
  1. **‘구분’**: 국내1, 국내2, 해외 등으로 카테고리화  
  2. **‘기업명’**: 사례 기업 이름(공식 보고서명을 병기하면 신뢰도 상승)  
  3. **‘적용 분야’**: 해당 기업이 중점적으로 진행한 ESG 축(예: 기후변화 대응, 사회적 가치 창출 등)  
  4. **‘주요 활동’**: 어떤 프로젝트나 정책을 실행했는지 간략히 서술  
  5. **‘성과(수치)’**: 달성한 KPI 수치나 효과(예: 배출량 감축률, 재생에너지 비율 등)  
  6. **‘출처’**: 해당 데이터를 발표한 보고서명 및 연도, RAG 데이터베이스 문서명 등 구체적으로 표기  
- **예시 표**:  
  ```markdown
  | 구분  | 기업명            | 적용 분야       | 주요 활동                                            | 성과(수치)                                             | 출처                                    |
  |:-----:|:-----------------:|:---------------:|:-----------------------------------------------------|:-------------------------------------------------------:|:---------------------------------------:|
  | 국내1 | 삼표시멘트 (SAMPYO) | 기후변화 대응    | - 탄소중립 목표 설정<br>- 온실가스 감축 계획 수립       | 2030년까지 Scope 1·2 배출량 **42% 감축**<br>Scope 3 배출량 **25% 감축** | SAMPYO ESG 보고서 (2024)               |
  | 국내2 | KTNG             | 기후변화 대응    | - SBTi 기반 온실가스 감축 목표 수립<br>- 재생에너지 확대   | 2030년까지 **재생에너지 80% 도입 목표**                    | KTNG 지속가능경영보고서 (2024)         |
  | 해외  | Company X (미국)  | 환경             | - 미국 DOE 프로젝트 참여<br>- 태양광 설비 확대             | 2028년까지 **재생에너지 비율 60% 달성**                   | Company X ESG Report (2023)            |

**주의사항**  
- 기업이 제시한 구체적 상황(업종, 규모, 목표 시점 등)이 있으면, 그에 맞춘 예시·지표를 제안할 것.  
- 출처가 명확한 데이터(공식 ESG 보고서, 공신력 있는 가이드라인 등)만 인용하고, 근거 자료가 없을 때는 “공식 자료에서 확인되지 않음”을 명시.  
- 지나치게 일반화된 조언이 아니라, 실무에 바로 적용 가능한 수준의 액션 아이템을 제공.  
- 답변 마지막에 추가 질문 유도 문구(예: “더 궁금하신 점이 있으면 말씀해 주세요.”)를 포함해 대화를 부드럽게 이어갈 것.


---



{metadata_info}

관련 문서:
{context}"""

    try:
        result = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-0125:personal::BdZzCnDt",  # 파인튜닝된 모델 ID
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.7,  # 일관성을 위해 낮은 temperature 사용
            max_tokens=1000    # 더 긴 응답 허용
        )
        return result.choices[0].message.content, metadata_info
    except Exception as e:
        print(f"응답 생성 중 오류 발생: {e}")
        return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.", metadata_info

def main():
    print("ESG 챗봇을 초기화하는 중...")
    
    # ChromaDB 클라이언트 초기화
    chroma_client = chromadb.PersistentClient(path="./data/chromadb")
    
    # 임베딩 함수 설정 -> ChromaDB에서 사용하는 임베딩 함수
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="jhgan/ko-sroberta-multitask"
    )
    
    # 컬렉션 가져오기
    collection = chroma_client.get_collection(
        name="ppt_documents_collection",
        embedding_function=embedding_function
    )
    
    print("초기화 완료! 질문해주세요.")
    # print("특정 영역(Environmental/Social/Governance)에 대해 물어보시면 해당 영역의 정보를 우선적으로 검색합니다.")
    
    while True:
        # 사용자 입력 받기
        query = input("\n질문을 입력하세요 (종료하려면 'quit' 입력): ")
        
        if query.lower() == 'quit':
            break
            
        # 짧은 질문 확장
        expanded_query = expand_query(query)
        
        # 메타데이터 필터 추출 (원래 질문에서)
        metadata_filters = extract_metadata_filters(query)
        
        # 관련 문서 검색 (확장된 질문 사용)
        context, metadata_summary = get_relevant_context(
            expanded_query, 
            collection,
            metadata_filters=metadata_filters
        )
        
        # 응답 생성 (원래 질문 사용)
        response, metadata_info = generate_response(query, context, metadata_summary)
        
        print("\n답변:")
        print(response)
        
        # 사용된 문서 출력 여부 확인
        show_sources = input("\n참고한 문서 정보를 보시겠습니까? (y/n): ")
        if show_sources.lower() == 'y':
            print("\n참고한 문서 요약:")
            print(metadata_info)
            print("\n상세 문서:")
            print(context)

if __name__ == "__main__":
    main() 