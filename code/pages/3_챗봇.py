import streamlit as st
import os
import sys
from pathlib import Path
from rag_chatbot import get_relevant_context, generate_response, extract_metadata_filters, expand_query
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import time
import pandas as pd

# 페이지 설정 
st.set_page_config(
    page_title="ESG 전문가",
    page_icon="💬",
    layout="wide"
)

@st.cache_resource
def load_data():
    # .env 파일 로드
    load_dotenv()

    # 데이터 로딩
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="jhgan/ko-sroberta-multitask"
    )
    
    client = chromadb.PersistentClient(path="./data/chromadb")
    collection = client.get_collection(
        name="ppt_documents_collection",
        embedding_function=embedding_function
    )

    return collection

with st.spinner("ChromaDB 컬렉션을 초기화하는 중입니다. 잠시만 기다려주세요..."):
    # 데이터 로딩 및 세션 상태에 저장
    if "collection" not in st.session_state:
        st.session_state.collection = load_data()

# 스타일 설정
st.markdown("""
    <style>
    .user-message {
        background-color: #F5C05C;
        color: #000000;
        padding: 10px 15px;
        border-radius: 15px 15px 0 15px;
        margin: 5px 0;
        max-width: 80%;
        margin-left: auto;
        margin-right: 0;
        word-wrap: break-word;
        white-space: pre-wrap;
        text-align: left;
        float: right;
        clear: both;
    }
    </style>
    """, unsafe_allow_html=True)

# 제목
st.title("💬 ESG 전문가 AI 채드번")
st.markdown("RAG(Retrieval Augmented Generation) 기반 ESG 전문가 AI와 대화해보세요.")

# 사이드바에 모델 선택
with st.sidebar:
    st.header("모델 설정")
    use_finetuned = st.toggle(
        "ESG 전문가",
        value=True,
        help="파인튜닝된 모델을 사용하려면 켜고, 기본 모델(gpt-3.5-turbo)을 사용하려면 끄세요"
    )
    
    if use_finetuned:
        model_id = "ft:gpt-3.5-turbo-0125:personal::BdZzCnDt"
    else:
        model_id = "gpt-3.5-turbo"

# 채팅 인터페이스
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 내용 표시
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant"):
            st.markdown(message["content"])
            if "metadata_summary" in message:
                with st.expander("참고 문서 정보"):
                    st.json(message["metadata_summary"])

# 사용자 입력
if prompt := st.chat_input("ESG 관련 질문을 입력하세요"):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)

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
                    st.session_state.collection,
                    metadata_filters=metadata_filters
                )
                
                # 응답 생성
                response, metadata_info = generate_response(expanded_query, context, metadata_summary)
                
                st.markdown(response)
                
                # 메타데이터 요약 정보 표시
                if context:
                    with st.expander("참고 문서 정보"):
                        st.code(context, language="text")
                
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