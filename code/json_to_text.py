import json
from pathlib import Path

def convert_json_to_text(json_file_path, output_dir):
    """JSON 파일을 읽어서 슬라이드/페이지 형식의 텍스트 파일로 변환합니다."""
    
    # JSON 파일 읽기
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 출력 디렉토리 생성
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 출력 파일 경로
    output_file = output_dir / f"{Path(json_file_path).stem}_text.txt"
    
    # 텍스트 파일 작성
    with open(output_file, 'w', encoding='utf-8') as f:
        for page in data:
            # 슬라이드/페이지 헤더
            f.write(f"--- Slide {page['slide_number']} (PPT Page {page['ppt_page_number']}) ---\n")
            
            # 카테고리 정보 출력
            for category in page['metadata']['categories']:
                f.write(f"Main Category: {category['main_category']}\n")
                f.write(f"Sub Category: {category['sub_category']}\n")
            
            f.write("\nContent:\n")
            # 내용을 줄 단위로 분리하고 각 줄을 처리
            content_lines = page['content'].split('\n')
            
            # 각 줄을 처리하여 출력
            for line in content_lines:
                # 빈 줄이 아닌 경우에만 처리
                if line.strip():
                    f.write(f"{line.strip()}\n")
            
            # 페이지 구분을 위한 빈 줄
            f.write("\n" + "="*50 + "\n\n")
    
    return output_file

def main():
    # 파일 경로 설정
    json_file = "output.json"  # PPT 처리 결과 JSON 파일
    output_dir = "data"        # 출력 디렉토리
    
    # JSON을 텍스트로 변환
    output_file = convert_json_to_text(json_file, output_dir)
    print(f"텍스트 파일이 생성되었습니다: {output_file}")

if __name__ == "__main__":
    main() 