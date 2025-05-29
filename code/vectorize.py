import os
from typing import List, Dict
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

class TextVectorizer:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        텍스트 벡터화를 위한 클래스 초기화
        
        Args:
            persist_directory (str): 벡터 저장소가 저장될 디렉토리
        """
        load_dotenv()  # .env 파일에서 환경 변수 로드
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings()
        
    def read_text_file(self, file_path: str) -> str:
        """
        텍스트 파일을 읽어옴
        
        Args:
            file_path (str): 텍스트 파일 경로
            
        Returns:
            str: 파일 내용
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    def split_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """
        텍스트를 청크로 분할
        
        Args:
            text (str): 분할할 텍스트
            chunk_size (int): 각 청크의 최대 크기
            chunk_overlap (int): 청크 간 중복되는 문자 수
            
        Returns:
            List[str]: 분할된 텍스트 청크 리스트
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        return text_splitter.split_text(text)
        
    def create_vector_store(self, texts: List[str], metadatas: List[Dict] = None) -> Chroma:
        """
        텍스트 청크를 벡터 저장소에 저장
        
        Args:
            texts (List[str]): 벡터화할 텍스트 청크 리스트
            metadatas (List[Dict], optional): 각 청크에 대한 메타데이터
            
        Returns:
            Chroma: 벡터 저장소 객체
        """
        if metadatas is None:
            metadatas = [{"source": f"chunk_{i}"} for i in range(len(texts))]
            
        vectorstore = Chroma.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas,
            persist_directory=self.persist_directory
        )
        
        vectorstore.persist()
        return vectorstore
        
    def process_text_file(self, file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        텍스트 파일을 처리하여 벡터 저장소 생성
        
        Args:
            file_path (str): 처리할 텍스트 파일 경로
            chunk_size (int): 각 청크의 최대 크기
            chunk_overlap (int): 청크 간 중복되는 문자 수
        """
        print(f"\n{os.path.basename(file_path)} 처리 중...")
        
        # 텍스트 파일 읽기
        text = self.read_text_file(file_path)
        
        # 텍스트를 청크로 분할
        chunks = self.split_text(text, chunk_size, chunk_overlap)
        print(f"- 총 {len(chunks)}개의 청크로 분할됨")
        
        # 메타데이터 생성 (파일명과 청크 번호 포함)
        metadatas = [{
            "source": os.path.basename(file_path),
            "chunk": i,
            "total_chunks": len(chunks)
        } for i in range(len(chunks))]
        
        # 벡터 저장소 생성
        vectorstore = self.create_vector_store(chunks, metadatas)
        print(f"- 벡터 저장소가 {self.persist_directory}에 저장됨")
        
        return vectorstore

def process_directory(input_dir: str, persist_directory: str = "./chroma_db"):
    """
    디렉토리 내의 모든 텍스트 파일을 처리
    
    Args:
        input_dir (str): 텍스트 파일이 있는 디렉토리
        persist_directory (str): 벡터 저장소가 저장될 디렉토리
    """
    vectorizer = TextVectorizer(persist_directory)
    text_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    
    for text_file in text_files:
        file_path = os.path.join(input_dir, text_file)
        try:
            vectorizer.process_text_file(file_path)
        except Exception as e:
            print(f"Error processing {text_file}: {str(e)}")

if __name__ == "__main__":
    # 처리된 텍스트 파일이 있는 디렉토리와 벡터 저장소 디렉토리 설정
    input_directory = "data/processed"  # 처리된 텍스트 파일이 있는 디렉토리
    persist_directory = "data/vector_db"  # 벡터 저장소가 저장될 디렉토리
    
    # 디렉토리 내의 모든 텍스트 파일 처리
    process_directory(input_directory, persist_directory) 