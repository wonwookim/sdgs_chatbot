import os
from pptx import Presentation
from typing import List, Dict, Any, Tuple
import pandas as pd
import json

class PPTProcessor:
    def __init__(self, ppt_dir: str, mapping_file: str):
        """
        PPT 프로세서 초기화
        Args:
            ppt_dir (str): PPT 파일이 있는 디렉토리 경로
            mapping_file (str): ESG 매핑 정보가 있는 파일 경로
        """
        self.ppt_dir = ppt_dir
        self.presentations = {}
        self.esg_mapping = self.load_esg_mapping(mapping_file)
        
    def load_esg_mapping(self, mapping_file: str) -> Dict[str, List[Dict[str, str]]]:
        """
        ESG 매핑 파일 로드
        Args:
            mapping_file (str): 매핑 파일 경로
        Returns:
            Dict: 페이지별 ESG 매핑 정보
        """
        mapping = {}
        with open(mapping_file, 'r', encoding='utf-8') as f:
            for line in f:
                main_category, sub_category, pages = line.strip().split('|')
                # 페이지 범위 처리 (예: "1-2" -> [1, 2])
                page_numbers = []
                for page_range in pages.split(','):
                    if '-' in page_range:
                        start, end = map(int, page_range.split('-'))
                        page_numbers.extend(range(start, end + 1))
                    else:
                        page_numbers.append(int(page_range))
                
                # 각 페이지에 대한 매핑 정보 저장
                for page in page_numbers:
                    if page not in mapping:
                        mapping[page] = []
                    mapping[page].append({
                        "main_category": main_category,
                        "sub_category": sub_category
                    })
        return mapping
        
    def load_ppt(self, file_name: str) -> None:
        """
        PPT 파일 로드
        Args:
            file_name (str): PPT 파일명
        """
        file_path = os.path.join(self.ppt_dir, file_name)
        try:
            prs = Presentation(file_path)
            self.presentations[file_name] = prs
            print(f"Successfully loaded: {file_name}")
        except Exception as e:
            print(f"Error loading {file_name}: {str(e)}")
            
    def extract_text_by_slide(self, file_name: str) -> List[str]:
        """
        각 슬라이드의 텍스트 추출
        Args:
            file_name (str): PPT 파일명
        Returns:
            List[str]: 각 슬라이드의 텍스트 리스트
        """
        if file_name not in self.presentations:
            print(f"Please load {file_name} first using load_ppt()")
            return []
            
        prs = self.presentations[file_name]
        slide_texts = []
        
        for slide in prs.slides:
            texts = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    texts.append(shape.text.strip())
            slide_texts.append(" ".join(texts))
            
        return slide_texts
        
    def extract_text_by_category(self, file_name: str, categories: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        카테고리별 텍스트 추출
        Args:
            file_name (str): PPT 파일명
            categories (Dict[str, List[str]]): 카테고리별 키워드 딕셔너리
        Returns:
            Dict[str, List[str]]: 카테고리별 텍스트
        """
        slide_texts = self.extract_text_by_slide(file_name)
        categorized_texts = {category: [] for category in categories.keys()}
        
        for text in slide_texts:
            for category, keywords in categories.items():
                if any(keyword.lower() in text.lower() for keyword in keywords):
                    categorized_texts[category].append(text)
                    
        return categorized_texts
        
    def save_to_excel(self, data: Dict[str, List[str]], output_file: str) -> None:
        """
        결과를 엑셀 파일로 저장
        Args:
            data (Dict[str, List[str]]): 저장할 데이터
            output_file (str): 출력 파일명
        """
        df = pd.DataFrame.from_dict(data, orient='index').transpose()
        df.to_excel(output_file, index=False)
        print(f"Results saved to {output_file}")

    def create_json_output(self, file_name: str, slide_number: int, content: str) -> Dict:
        """
        JSON 출력 형식 생성
        Args:
            file_name (str): PPT 파일명
            slide_number (int): 슬라이드 번호
            content (str): 슬라이드 내용
        Returns:
            Dict: JSON 형식의 출력 데이터
        """
        prs = self.presentations[file_name]
        
        # 해당 슬라이드 번호에 대한 매핑 정보 가져오기
        categories = self.esg_mapping.get(slide_number, [{
            "main_category": "기타",
            "sub_category": "미분류"
        }])

        return {
            "slide_number": slide_number,
            "ppt_page_number": slide_number,
            "content": content,
            "metadata": {
                "source": file_name,
                "slide": slide_number,
                "ppt_page_number": slide_number,
                "total_slides": len(prs.slides),
                "categories": categories
            }
        }

    def process_and_save_json(self, file_name: str, output_file: str) -> None:
        """
        PPT 처리 후 JSON 파일로 저장
        Args:
            file_name (str): PPT 파일명
            output_file (str): 출력 JSON 파일명
        """
        if file_name not in self.presentations:
            print(f"Please load {file_name} first using load_ppt()")
            return

        slide_texts = self.extract_text_by_slide(file_name)
        results = []
        
        for idx, text in enumerate(slide_texts, 1):
            if text.strip():  # 빈 슬라이드가 아닌 경우만 처리
                slide_data = self.create_json_output(file_name, idx, text)
                results.append(slide_data)

        # JSON 파일 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"JSON file saved to {output_file}")

if __name__ == "__main__":
    # 사용 예시
    processor = PPTProcessor("data/ppt", "data/esg_mapping.txt")
    processor.load_ppt("2023 삼표시멘트 ESG보고서 수정본.pptx")
    processor.process_and_save_json("2023 삼표시멘트 ESG보고서 수정본.pptx", "output.json") 