import streamlit as st
import os
import sys
from pathlib import Path
from rag_chatbot import get_relevant_context, generate_response, extract_metadata_filters, expand_query
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# ... existing code ... 
# .env 파일 로드
load_dotenv()

# ChromaDB 설정
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="jhgan/ko-sroberta-multitask"
    )
    

client = chromadb.PersistentClient(path="./data/chromadb")
collection = client.get_collection(
    name="ppt_documents_collection",
    embedding_function=embedding_function
)

# 페이지 설정
st.set_page_config(
    page_title="ESG 전문가 AI - 챗봇",
    page_icon="💬",
    layout="wide"
)

# 제목
st.title("💬 ESG 전문가 AI 챗봇")
st.markdown("RAG(Retrieval Augmented Generation) 기반 ESG 전문가 AI와 대화해보세요.")

# 사이드바에 모델 ID 입력
with st.sidebar:
    st.header("모델 설정")
    model_id = st.text_input(
        "파인튜닝된 모델 ID",
        help="파인튜닝이 완료된 모델의 ID를 입력하세요"
    )
    
    if not model_id:
        st.warning("모델 ID를 입력해주세요.")
        st.stop()

# 채팅 인터페이스
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 내용 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "metadata_summary" in message:
            with st.expander("참고 문서 정보"):
                st.json(message["metadata_summary"])

# 사용자 입력
if prompt := st.chat_input("ESG 관련 질문을 입력하세요"):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("답변 생성 중..."):
            try:
                # 질문 확장
                expanded_query = expand_query(prompt)
                
                # 메타데이터 필터 추출
                metadata_filters = extract_metadata_filters(expanded_query)
                
                # 관련 문서 검색
                context, metadata_summary = get_relevant_context(
                    expanded_query,
                    collection,
                    metadata_filters=metadata_filters
                )
                
                # 응답 생성
                response = generate_response(expanded_query, context, metadata_summary)
                
                st.markdown(response)
                
                # 메타데이터 요약 정보 표시
                if metadata_summary:
                    with st.expander("참고 문서 정보"):
                        st.json(metadata_summary)
                
                # 응답 저장
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "metadata_summary": metadata_summary
                })
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")

# 대화 초기화 버튼
if st.sidebar.button("대화 초기화"):
    st.session_state.messages = []
    st.rerun() 