import os
from pypdf import PdfReader
from typing import List, Dict
import json
import re
import unicodedata

def clean_text(text: str) -> str:
    """
    텍스트를 정제하는 함수
    
    Args:
        text (str): 정제할 텍스트
        
    Returns:
        str: 정제된 텍스트
    """
    # 유니코드 정규화 (한글 등)
    text = unicodedata.normalize('NFKC', text)
    
    # 불필요한 공백 제거 (연속된 공백을 하나로)
    text = re.sub(r'\s+', ' ', text)
    
    # 페이지 번호 형식 정리 (=== Page X === 형식 제거)
    text = re.sub(r'=== Page \d+ ===', '', text)
    
    # 특수문자 정리 (단, 한글, 영문, 숫자, 기본 문장부호는 유지)
    text = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ.,!?;:()\[\]{}""\'\'-]', '', text)
    
    # 문단 구분을 위한 패턴 추가
    # 1. 제목 패턴 (숫자로 시작하는 제목)
    text = re.sub(r'(\d+\.\s*[가-힣a-zA-Z])', r'\n\n\1', text)
    # 2. 부제목 패턴 ((가), (나) 등으로 시작하는 부제목)
    text = re.sub(r'(\([가-힣]\))', r'\n\n\1', text)
    # 3. 항목 패턴 ((1), (2) 등으로 시작하는 항목)
    text = re.sub(r'(\(\d+\))', r'\n\n\1', text)
    
    # 연속된 줄바꿈 정리 (3개 이상의 줄바꿈을 2개로)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 문단 시작 부분의 불필요한 공백 제거
    text = re.sub(r'\n\s+', '\n', text)
    
    # 문장 끝 부분의 불필요한 공백 제거
    text = re.sub(r'\s+\n', '\n', text)
    
    # 헤더/푸터로 보이는 반복되는 텍스트 제거 (예: 페이지 번호)
    text = re.sub(r'\d+\s*/\s*\d+', '', text)
    
    # 연속된 마침표 제거
    text = re.sub(r'\.{2,}', '.', text)
    
    # 문장 단위로 줄바꿈 추가 (마침표, 물음표, 느낌표 뒤에)
    text = re.sub(r'([.!?])\s+', r'\1\n', text)
    
    # 앞뒤 공백 제거
    text = text.strip()
    
    # 빈 줄 제거
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text

def read_pdf(pdf_path: str) -> str:
    """
    PDF 파일을 읽어서 텍스트로 변환
    
    Args:
        pdf_path (str): PDF 파일 경로
        
    Returns:
        str: PDF 파일의 텍스트 내용
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
    reader = PdfReader(pdf_path)
    text = ""
    
    for page_num, page in enumerate(reader.pages, 1):
        page_text = page.extract_text()
        # 각 페이지의 텍스트를 정제
        cleaned_page_text = clean_text(page_text)
        text += f"\n{cleaned_page_text}"
        
    # 전체 텍스트 한 번 더 정제
    text = clean_text(text)
    return text

def save_text_to_file(text: str, output_path: str):
    """
    텍스트를 파일로 저장
    
    Args:
        text (str): 저장할 텍스트
        output_path (str): 저장할 파일 경로
    """
    # 텍스트를 문단 단위로 분리하여 저장
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and len(p.strip()) > 10]  # 최소 10자 이상인 문단만 포함
    
    # 문단 길이가 너무 긴 경우 분할 (1000자 이상)
    split_paragraphs = []
    for p in paragraphs:
        if len(p) > 1000:
            # 문장 단위로 분할
            sentences = re.split(r'([.!?])\s+', p)
            current_para = ''
            for i in range(0, len(sentences)-1, 2):
                if i+1 < len(sentences):
                    sentence = sentences[i] + sentences[i+1]
                else:
                    sentence = sentences[i]
                if len(current_para) + len(sentence) < 1000:
                    current_para += ' ' + sentence
                else:
                    if current_para:
                        split_paragraphs.append(current_para.strip())
                    current_para = sentence
            if current_para:
                split_paragraphs.append(current_para.strip())
        else:
            split_paragraphs.append(p)
    
    formatted_text = '\n\n'.join(split_paragraphs)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(formatted_text)
    print(f"텍스트가 {output_path}에 저장되었습니다.")
    
    # 통계 정보 출력
    print(f"\n처리된 텍스트 통계:")
    print(f"- 총 문자 수: {len(formatted_text)}")
    print(f"- 총 문단 수: {len(split_paragraphs)}")
    print(f"- 평균 문단 길이: {len(formatted_text)/len(split_paragraphs):.1f} 문자")
    print(f"- 가장 긴 문단: {max(len(p) for p in split_paragraphs)} 문자")
    print(f"- 가장 짧은 문단: {min(len(p) for p in split_paragraphs)} 문자")

def process_pdf_directory(input_dir: str, output_dir: str):
    """
    디렉토리 내의 모든 PDF 파일을 처리
    
    Args:
        input_dir (str): PDF 파일이 있는 디렉토리
        output_dir (str): 처리된 텍스트를 저장할 디렉토리
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        output_path = os.path.join(output_dir, f"{os.path.splitext(pdf_file)[0]}.txt")
        
        try:
            print(f"\n{pdf_file} 처리 중...")
            text = read_pdf(pdf_path)
            save_text_to_file(text, output_path)
        except Exception as e:
            print(f"Error processing {pdf_file}: {str(e)}")

if __name__ == "__main__":
    # PDF 파일이 있는 디렉토리와 출력 디렉토리 설정
    input_directory = "data/pdfs"  # PDF 파일들이 있는 디렉토리
    output_directory = "data/processed"  # 처리된 텍스트 파일이 저장될 디렉토리
    
    # 디렉토리 내의 모든 PDF 파일 처리
    process_pdf_directory(input_directory, output_directory) 