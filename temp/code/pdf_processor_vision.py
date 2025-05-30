# 이 파일은 pdf_processor.py의 복사본입니다. 이미지 기반 도표 구조 인식 실험용으로 사용됩니다.

# --- 이하 pdf_processor.py 전체 코드 복사 --- 

import PyPDF2
import re
from pathlib import Path
import json
import chromadb
from chromadb.utils import embedding_functions
import os
import fitz  # PyMuPDF 추가
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import numpy as np
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTTextLineHorizontal, LAParams

def rgb_from_int(color_int):
    r = (color_int >> 16) & 255
    g = (color_int >> 8) & 255
    b = color_int & 255
    return (r, g, b)

def is_gray_or_black(rgb):
    return (rgb[0] == rgb[1] == rgb[2]) or (max(rgb) - min(rgb) < 10)

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
                            rgb = rgb_from_int(color)
                            toc_candidates.append((text, rgb))
        colored = [(text, rgb) for text, rgb in toc_candidates if not is_gray_or_black(rgb)]
        color_count = {}
        for _, rgb in colored:
            color_count[rgb] = color_count.get(rgb, 0) + 1
        if color_count:
            main_color = max(color_count, key=color_count.get)
            sub_section = [text for text, rgb in colored if rgb == main_color]
            sub_sections[page_num] = sub_section[0] if sub_section else None
        else:
            sub_sections[page_num] = None
    return sub_sections

def create_chunks_with_subsection(text, section_type, sub_section, chunk_size=1000):
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

@dataclass
class StructuredElement:
    """구조화된 요소를 나타내는 클래스"""
    type: str  # 'text', 'table', 'diagram', 'box', 'arrow'
    content: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    children: List['StructuredElement']
    metadata: Dict
    color: Optional[Tuple[int, int, int]] = None

class PDFStructureExtractor:
    """PDF에서 구조화된 데이터를 추출하는 클래스"""
    def __init__(self, pdf_path: str):
        self.doc = fitz.open(pdf_path)
        self.current_page = None
        self.elements = []

    def extract_page_structure(self, page_num: int) -> List[StructuredElement]:
        """특정 페이지의 구조화된 데이터를 추출 (계층화 없이 평면적)"""
        self.current_page = self.doc[page_num]
        self.elements = []
        # 1. 텍스트 블록 추출
        blocks = self.current_page.get_text("dict")['blocks']
        for block in blocks:
            if 'lines' in block:
                elem = self._process_text_block(block)
                if elem:
                    self.elements.append(elem)
            elif 'image' in block:
                self.elements.append(self._process_image_block(block))
        # 2. 도형(선, 화살표, 박스) 추출
        shapes = self.current_page.get_drawings()
        for shape in shapes:
            elem = self._process_shape(shape)
            if elem:
                self.elements.append(elem)
        return self.elements

    def _process_text_block(self, block: Dict):
        text = ""
        bbox = block['bbox']
        color = None
        for line in block['lines']:
            for span in line['spans']:
                text += span['text']
                if not color:
                    color = rgb_from_int(span['color'])
        if text.strip():
            return StructuredElement(
                type='text',
                content=text.strip(),
                bbox=bbox,
                children=[],
                metadata={'font_size': block.get('size', 0)},
                color=color
            )
        return None

    def _process_shape(self, shape: Dict):
        if shape['type'] == 'rect':
            return StructuredElement(
                type='box',
                content='',
                bbox=shape['rect'],
                children=[],
                metadata={'stroke_width': shape.get('width', 1)},
                color=rgb_from_int(shape.get('color', 0))
            )
        elif shape['type'] == 'line':
            return StructuredElement(
                type='arrow',
                content='',
                bbox=shape['rect'],
                children=[],
                metadata={'stroke_width': shape.get('width', 1)},
                color=rgb_from_int(shape.get('color', 0))
            )
        return None

    def _process_image_block(self, block: Dict):
        return StructuredElement(
            type='image',
            content='',
            bbox=block['bbox'],
            children=[],
            metadata={'image_type': 'embedded'}
        )

def extract_images_from_page(pdf_path, page_num, output_dir="temp/data/processed/images"):
    """해당 페이지의 이미지를 추출하여 파일로 저장하고, 메타데이터 리스트 반환"""
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    image_metadata = []
    img_list = page.get_images(full=True)
    for img_idx, img in enumerate(img_list):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        ext = base_image["ext"]
        img_path = os.path.join(output_dir, f"page_{page_num+1}_img_{img_idx+1}.{ext}")
        with open(img_path, "wb") as f:
            f.write(image_bytes)
        # bbox 정보는 get_images에서 직접 제공하지 않으므로 None 처리 (필요시 추가 로직 구현)
        image_metadata.append({
            "page": page_num + 1,
            "img_idx": img_idx + 1,
            "path": img_path,
            "width": base_image.get("width"),
            "height": base_image.get("height"),
            "ext": ext,
            "xref": xref,
            "bbox": None  # bbox 정보는 별도 추출 필요
        })
    return image_metadata

def extract_structured_data(pdf_path: str, page_num: int) -> Dict:
    """특정 페이지의 구조화된 데이터를 추출하여 JSON 형식으로 반환 (이미지 메타데이터 포함)"""
    extractor = PDFStructureExtractor(pdf_path)
    elements = extractor.extract_page_structure(page_num)
    images = extract_images_from_page(pdf_path, page_num)
    structured_data = {
        'page_number': page_num + 1,
        'elements': [
            {
                'type': elem.type,
                'content': elem.content,
                'bbox': elem.bbox,
                'metadata': elem.metadata,
                'color': elem.color
            }
            for elem in elements
        ],
        'images': images
    }
    return structured_data

def create_chunks_with_structure(text: str, section_type: str, sub_section: str, 
                               structured_data: Optional[Dict] = None, 
                               chunk_size: int = 1000) -> List[Dict]:
    """구조화된 데이터를 포함한 청크 생성"""
    chunks = create_chunks_with_subsection(text, section_type, sub_section, chunk_size)
    
    # 구조화된 데이터가 있는 경우 메타데이터에 추가
    if structured_data:
        for chunk in chunks:
            chunk['metadata']['structured_data'] = structured_data
    
    return chunks

def extract_esg_performance(pdf_path: str):
    """
    PDF 파일에서 Environmental, Social, Governance 섹션을 페이지 범위로 구분하여 청크로 나눕니다.
    각 페이지의 강조 목차(sub_section)와 구조화된 데이터를 metadata에 포함합니다.
    """
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
        
        # sub_section 추출
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
                        # 구조화된 데이터 추출
                        structured_data = extract_structured_data(pdf_path, page_num)
                        section_texts[section].append((page_text, sub_sections.get(page_num), structured_data))
    
    all_chunks = []
    for section_type, page_texts in section_texts.items():
        for text, sub_section, structured_data in page_texts:
            if text.strip():
                chunks = create_chunks_with_structure(text, section_type, sub_section, structured_data)
                all_chunks.extend(chunks)
                print(f"{section_type} 섹션({sub_section})에서 {len(chunks)}개의 청크 생성됨")
    
    return all_chunks

def store_in_chroma(chunks):
    """
    청크를 ChromaDB에 저장합니다.
    structured_data가 dict일 경우, JSON 문자열로 변환해서 저장합니다.
    """
    import json as _json
    client = chromadb.PersistentClient(path="temp/data/chroma_db")
    collection = client.get_or_create_collection(
        name="esg_data",
        metadata={"hnsw:space": "cosine"}
    )
    documents = []
    metadatas = []
    ids = []
    for i, chunk in enumerate(chunks):
        documents.append(chunk['text'])
        meta = dict(chunk['metadata'])
        # structured_data가 dict면 문자열로 변환
        if 'structured_data' in meta and isinstance(meta['structured_data'], dict):
            meta['structured_data'] = _json.dumps(meta['structured_data'], ensure_ascii=False)
        metadatas.append(meta)
        ids.append(f"chunk_{i}")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"총 {len(chunks)}개의 청크가 ChromaDB에 저장되었습니다.")

def print_pdf_structure_with_pdfminer(pdf_path, page_number):
    """pdfminer.six를 사용해 해당 페이지의 구조/태그 정보를 출력"""
    laparams = LAParams()
    for i, page_layout in enumerate(extract_pages(pdf_path, laparams=laparams)):
        if i == page_number:
            print(f"[pdfminer] Page {page_number+1} 구조 정보:")
            for element in page_layout:
                if isinstance(element, LTTextBoxHorizontal):
                    print(f"  [TextBox] {element.get_text().strip()}")
                elif isinstance(element, LTTextLineHorizontal):
                    print(f"    [TextLine] {element.get_text().strip()}")
            break

def print_tables_with_pdfplumber(pdf_path, page_number):
    """pdfplumber를 사용해 해당 페이지의 표 구조를 추출/출력"""
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]
        tables = page.extract_tables()
        print(f"[pdfplumber] Page {page_number+1} 표 개수: {len(tables)}")
        for t_idx, table in enumerate(tables):
            print(f"  [Table {t_idx+1}]")
            for row in table:
                print("    ", row)

def group_texts_by_y(pdf_path, page_num, y_margin=10):
    """텍스트 요소를 y좌표 기준으로 그룹핑(행 추정)하여 출력"""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    blocks = page.get_text("dict")['blocks']
    texts = []
    for block in blocks:
        if 'lines' in block:
            for line in block['lines']:
                for span in line['spans']:
                    text = span['text'].strip()
                    if text:
                        y0 = span['bbox'][1]
                        y1 = span['bbox'][3]
                        x0 = span['bbox'][0]
                        x1 = span['bbox'][2]
                        font_size = span.get('size', 0)
                        color = rgb_from_int(span['color'])
                        texts.append({
                            'text': text,
                            'y0': y0,
                            'y1': y1,
                            'x0': x0,
                            'x1': x1,
                            'font_size': font_size,
                            'color': color
                        })
    # y좌표 기준 그룹핑
    groups = []
    for t in sorted(texts, key=lambda x: x['y0']):
        found = False
        for g in groups:
            if abs(g[0]['y0'] - t['y0']) < y_margin:
                g.append(t)
                found = True
                break
        if not found:
            groups.append([t])
    # 그룹별 x좌표 정렬 및 출력
    print(f"[y좌표 그룹핑] page {page_num+1} (총 {len(groups)}개 그룹)")
    for i, g in enumerate(groups):
        g_sorted = sorted(g, key=lambda x: x['x0'])
        texts_in_row = [x['text'] for x in g_sorted]
        print(f"  [row {i+1}] {texts_in_row}")

def group_page_26_semantic(pdf_path, page_num=25):
    """26페이지를 시각적/의미적 영역(환경경영 방침, 환경경영 거버넌스, ISO14001 인증)별로 그룹핑"""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    blocks = page.get_text("dict")['blocks']
    texts = []
    for block in blocks:
        if 'lines' in block:
            for line in block['lines']:
                for span in line['spans']:
                    text = span['text'].strip()
                    if text:
                        y0 = span['bbox'][1]
                        y1 = span['bbox'][3]
                        x0 = span['bbox'][0]
                        x1 = span['bbox'][2]
                        font_size = span.get('size', 0)
                        color = rgb_from_int(span['color'])
                        texts.append({
                            'text': text,
                            'y0': y0,
                            'y1': y1,
                            'x0': x0,
                            'x1': x1,
                            'font_size': font_size,
                            'color': color
                        })
    # 영역 기준(대략):
    # 환경경영 방침: x0 < 400
    # 환경경영 거버넌스: 400 <= x0 < 800
    # ISO14001 인증: x0 >= 800
    grouped = {
        '환경경영 방침': [],
        '환경경영 거버넌스': [],
        'ISO14001 인증': []
    }
    for t in texts:
        if t['x0'] < 400:
            grouped['환경경영 방침'].append(t['text'])
        elif t['x0'] < 800:
            grouped['환경경영 거버넌스'].append(t['text'])
        else:
            grouped['ISO14001 인증'].append(t['text'])
    print("[26페이지 의미적 그룹핑 결과]")
    print(json.dumps(grouped, ensure_ascii=False, indent=2))

def main():
    # PDF 파일 경로
    pdf_path = "temp/data/pdfs/2023 신한라이프 지속가능경영보고서.pdf"
    
    print("프로그램 시작")
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