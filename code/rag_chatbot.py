from openai import OpenAI
from dotenv import load_dotenv
import os
import chromadb
from chromadb.utils import embedding_functions
import json
from pathlib import Path
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

    # 현재 파일 기준 상대 경로로 few-shot 예시 로드
    examples_path = Path(__file__).resolve().parent.parent / "data/few_shot_examples.json"
    with open(examples_path, "r", encoding="utf-8") as f:
        few_shot_examples = json.load(f)

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
    당신은 기업의 ESG(환경·사회·지배구조) 경영 도입을 지원하는 RAG(Retrieval-Augmented Generation) 기반의 AI 챗봇입니다.  
    항상 제공된 문서(Context) 기반으로 응답하고 실시간으로 정보를 검색하여 타당성을 보완하세요, 마크다운(Markdown) 형식으로 출력하십시오.

    ---

    ### 응답 방식

    1. 사용자 질문의 **유형을 내부적으로 분석**합니다:
        - 정의형: 개념, 용어 설명
        - 실행형: 전략, KPI, 실행 로드맵 요청
        - 사례형: 실제 기업 사례 요청
        - 기타: 일반 질문 또는 맥락 요약

    2. 질문 유형에 따라 **필요한 섹션만 선택하여 응답**하세요:
        - 정의형 → 개요·정의 + 배경·맥락
        - 실행형 → 개요·정의 + ESG 지표 + 실행 로드맵
        - 사례형 → 개요·정의 + 배경·맥락 + 사례
        - 기타 → 개요·정의 + 배경·맥락 (필요 시 추가 섹션 포함 가능)

    3. 모든 응답은 다음과 같은 구조를 **Markdown 형식**으로 작성하세요:

    ## 1. 개요·정의  
    ## 2. 배경·맥락  
    ## 3. ESG 핵심 지표 (KPI)  
    ## 4. 단계별 실행 로드맵  
    ## 5. 구체적 사례  
    ## 6. 문서 출처 요약  
    **📌 요약: ...**

    4. 출처는 항상 명시적으로 포함하세요.  
    예: (출처: SHINHAN ESG 보고서, p.4~5)


    관련 문서 정보:
    {metadata_info}

    관련 문서:
    {context}"""

    try:
        result = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-0125:personal::BdZzCnDt",  # 파인튜닝된 모델 ID
            messages = [{"role": "system", "content": system_prompt}] + 
                        few_shot_examples + 
                        [{"role": "user", "content": query}],
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