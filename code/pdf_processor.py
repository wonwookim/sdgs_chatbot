import PyPDF2
import re
from pathlib import Path
import json
import chromadb
from chromadb.utils import embedding_functions
import os

def extract_sections(text):
    """
    텍스트를 E, S, G 섹션으로 구분합니다.
    """
    sections = {
        'Environmental': [],
        'Social': [],
        'Governance': []
    }
    
    # 각 섹션의 시작과 끝을 찾는 패턴
    patterns = {
        'Environmental': r"Environmental.*?(?=Social|$)",
        'Social': r"Social.*?(?=Governance|$)",
        'Governance': r"Governance.*?(?=다음 섹션|$)"
    }
    
    for section, pattern in patterns.items():
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            sections[section] = matches[0].strip()
    
    return sections

def create_chunks(text, section_type, chunk_size=1000):
    """
    텍스트를 청크로 나누고 메타데이터를 추가합니다.
    """
    # 텍스트를 문장 단위로 분리
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        if current_length + len(sentence) > chunk_size:
            # 현재 청크가 완성되면 저장
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunk = {
                    'text': chunk_text,
                    'metadata': {
                        'section': section_type,
                        'source': '신한라이프 2023 ESG 보고서'
                    }
                }
                chunks.append(chunk)
            
            # 새로운 청크 시작
            current_chunk = [sentence]
            current_length = len(sentence)
        else:
            current_chunk.append(sentence)
            current_length += len(sentence)
    
    # 마지막 청크 처리
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunk = {
            'text': chunk_text,
            'metadata': {
                'section': section_type,
                'source': '신한라이프 2023 ESG 보고서'
            }
        }
        chunks.append(chunk)
    
    return chunks

def extract_esg_performance(pdf_path):
    """
    PDF 파일에서 ESG Performance 섹션을 추출하고 청크로 나눕니다.
    """
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        
        # 모든 페이지의 텍스트 추출
        for page in reader.pages:
            text += page.extract_text()
    
    # ESG Performance 섹션 찾기
    pattern = r"ESG Performance.*?(?=다음 섹션|$)"
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if not matches:
        return None
        
    esg_text = matches[0]
    
    # 섹션별로 분리
    sections = extract_sections(esg_text)
    
    # 각 섹션을 청크로 나누기
    all_chunks = []
    for section_type, section_text in sections.items():
        if section_text:
            chunks = create_chunks(section_text, section_type)
            all_chunks.extend(chunks)
    
    return all_chunks

def store_in_chroma(chunks):
    """
    청크를 ChromaDB에 저장합니다.
    """
    # ChromaDB 클라이언트 초기화
    client = chromadb.PersistentClient(path="temp/data/chroma_db")
    
    # 컬렉션 생성 또는 가져오기
    collection = client.get_or_create_collection(
        name="esg_data",
        metadata={"hnsw:space": "cosine"}
    )
    
    # 청크 데이터 준비
    documents = []
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        documents.append(chunk['text'])
        metadatas.append(chunk['metadata'])
        ids.append(f"chunk_{i}")
    
    # 데이터 추가
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"총 {len(chunks)}개의 청크가 ChromaDB에 저장되었습니다.")

def main():
    # PDF 파일 경로
    pdf_path = "temp/data/pdfs/2023 신한라이프 지속가능경영보고서.pdf"
    
    # ESG Performance 섹션 추출 및 청크 생성
    chunks = extract_esg_performance(pdf_path)
    
    if chunks:
        # 청크를 JSON 파일로 저장
        output_path = "temp/data/processed/esg_chunks.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        print(f"ESG 데이터가 {len(chunks)}개의 청크로 나뉘어 {output_path}에 저장되었습니다.")
        
        # ChromaDB에 저장
        store_in_chroma(chunks)
    else:
        print("ESG Performance 섹션을 찾을 수 없습니다.")

if __name__ == "__main__":
    main() 