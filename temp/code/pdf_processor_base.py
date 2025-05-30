import PyPDF2
import re
from pathlib import Path
import json
import os
import fitz  # PyMuPDF

def extract_page_sub_sections(pdf_path, page_indices, toc_x_max=200):
    doc = fitz.open(pdf_path)
    sub_sections = {}
    for page_num in page_indices:
        page = doc[page_num]
        blocks = page.get_text("dict")['blocks']
        toc_candidates = []
        for block in blocks:
            if 'lines' in block:
                for line in block['lines']:
                    for span in line['spans']:
                        text = span['text'].strip()
                        color = span['color']
                        bbox = span['bbox']
                        if text and bbox[2] <= toc_x_max:
                            toc_candidates.append(text)
        sub_sections[page_num] = toc_candidates[0] if toc_candidates else None
    return sub_sections

def create_chunks_base(text, section_type, sub_section, chunk_size=1000):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_length = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if current_length + len(sentence) > chunk_size:
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunk = {
                    'text': chunk_text,
                    'metadata': {
                        'section': section_type,
                        'sub_section': sub_section,
                        'source': '신한라이프 2023 ESG 보고서'
                    }
                }
                chunks.append(chunk)
            current_chunk = [sentence]
            current_length = len(sentence)
        else:
            current_chunk.append(sentence)
            current_length += len(sentence)
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunk = {
            'text': chunk_text,
            'metadata': {
                'section': section_type,
                'sub_section': sub_section,
                'source': '신한라이프 2023 ESG 보고서'
            }
        }
        chunks.append(chunk)
    return chunks

def extract_esg_performance_base(pdf_path):
    print(f"PDF 파일을 읽는 중: {pdf_path}")
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        num_pages = len(reader.pages)
        print(f"PDF 총 페이지 수: {num_pages}")
        section_ranges = {
            'Environmental': (24, 38),  # 25~39
            'Social': (40, 79),         # 41~80
            'Governance': (81, 99),    # 82~100
        }
        all_page_indices = list(range(24, 39)) + list(range(40, 80)) + list(range(81, 100))
        sub_sections = extract_page_sub_sections(pdf_path, all_page_indices)
        section_texts = {
            'Environmental': [],
            'Social': [],
            'Governance': []
        }
        for section, (start, end) in section_ranges.items():
            for page_num in range(start, end + 1):
                if page_num < num_pages:
                    print(f"{section} 섹션 - 페이지 {page_num + 1} 처리 중...")
                    page_text = reader.pages[page_num].extract_text()
                    if page_text:
                        section_texts[section].append((page_text, sub_sections.get(page_num)))
    all_chunks = []
    for section_type, page_texts in section_texts.items():
        for text, sub_section in page_texts:
            if text.strip():
                chunks = create_chunks_base(text, section_type, sub_section)
                all_chunks.extend(chunks)
                print(f"{section_type} 섹션({sub_section})에서 {len(chunks)}개의 청크 생성됨")
    return all_chunks

def main():
    pdf_path = "temp/data/pdfs/2023 신한라이프 지속가능경영보고서.pdf"
    print("프로그램 시작")
    chunks = extract_esg_performance_base(pdf_path)
    if chunks:
        output_path = "temp/data/processed/esg_chunks_base.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        print(f"ESG 데이터가 {len(chunks)}개의 청크로 나뉘어 {output_path}에 저장되었습니다.")
    else:
        print("ESG Performance 섹션을 찾을 수 없습니다.")

if __name__ == "__main__":
    main() 