import os
from typing import List, Dict
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import sys

def main():
    try:
        # 환경 변수 로드
        load_dotenv()
        
        # API 키 확인
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY가 설정되지 않았습니다.")
            print(".env 파일에 OPENAI_API_KEY를 설정해주세요.")
            return
            
        print("ESG 챗봇을 초기화하는 중...")
        
        # 벡터 DB 로드
        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma(
            persist_directory="data/vector_db",
            embedding_function=embeddings
        )
        
        # 대화 기록을 저장할 메모리
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # LLM 모델 설정
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7
        )
        
        # 대화 체인 설정
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(
                search_kwargs={"k": 3}
            ),
            return_source_documents=True
        )
        
        print("\nESG 챗봇이 시작되었습니다!")
        print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
        print("대화 기록을 초기화하려면 'clear'를 입력하세요.\n")
        
        while True:
            try:
                # 사용자 입력 받기
                question = input("\n질문을 입력하세요: ").strip()
                
                # 종료 조건 확인
                if question.lower() in ['quit', 'exit']:
                    print("\n챗봇을 종료합니다.")
                    break
                    
                # 대화 기록 초기화
                if question.lower() == 'clear':
                    memory.clear()
                    print("\n대화 기록이 초기화되었습니다.")
                    continue
                    
                # 빈 입력 처리
                if not question:
                    continue
                    
                # 답변 생성
                result = qa_chain({
                    "question": question,
                    "chat_history": []
                })
                
                # 답변 출력
                if "answer" in result:
                    print("\n답변:", result["answer"])
                else:
                    print("\n답변을 생성하는데 실패했습니다.")
                    continue
                
                # 참조 문서 정보 출력
                if "source_documents" in result and result["source_documents"]:
                    print("\n참조한 문서:")
                    for i, doc in enumerate(result["source_documents"], 1):
                        print(f"\n{i}. {doc.metadata['source']} (청크 {doc.metadata['chunk']})")
                        print(f"   내용: {doc.page_content[:200]}...")
                        
            except KeyboardInterrupt:
                print("\n\n챗봇을 종료합니다.")
                break
            except Exception as e:
                import traceback
                print(f"오류가 발생했습니다: {str(e)}")
                traceback.print_exc()
                print("다시 시도해주세요.")
                
    except Exception as e:
        import traceback
        print(f"초기화 중 오류가 발생했습니다: {str(e)}")
        traceback.print_exc()
        return

if __name__ == "__main__":
    main() 