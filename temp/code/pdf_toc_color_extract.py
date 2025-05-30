import fitz  # PyMuPDF

PDF_PATH = "temp/data/pdfs/2023 신한라이프 지속가능경영보고서.pdf"

# 일반적으로 목차는 왼쪽에 위치하므로, 좌측 영역만 추출 (예: x0~x1 범위 지정)
TOC_X_MAX = 200  # 실험적으로 조정 필요

# 색상값을 사람이 보기 쉽게 변환
def rgb_from_int(color_int):
    r = (color_int >> 16) & 255
    g = (color_int >> 8) & 255
    b = color_int & 255
    return (r, g, b)

def is_gray_or_black(rgb):
    # 회색/검정 계열(기본 목차, 비강조) 색상 필터
    return (rgb[0] == rgb[1] == rgb[2]) or (max(rgb) - min(rgb) < 10)

def extract_colored_toc_for_pages(pdf_path, page_indices):
    doc = fitz.open(pdf_path)
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
                        if text and bbox[2] <= TOC_X_MAX:
                            rgb = rgb_from_int(color)
                            toc_candidates.append((text, rgb))
        # 비회색/비검정색만 추출
        colored = [(text, rgb) for text, rgb in toc_candidates if not is_gray_or_black(rgb)]
        # 가장 많이 등장하는 색상 그룹 추출
        color_count = {}
        for _, rgb in colored:
            color_count[rgb] = color_count.get(rgb, 0) + 1
        if color_count:
            main_color = max(color_count, key=color_count.get)
            sub_sections = [text for text, rgb in colored if rgb == main_color]
        else:
            sub_sections = []
        print(f"[Page {page_num+1}] 강조 sub_section 후보: {sub_sections}")

if __name__ == "__main__":
    extract_colored_toc_for_pages(PDF_PATH, [26, 54]) 