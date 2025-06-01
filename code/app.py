import streamlit as st
import torch
import types
# torch.classes 패치 (Streamlit 에러 우회용)
torch.classes = types.SimpleNamespace()
st.set_page_config(
    page_title="ESG 전문가 AI",
    page_icon="🌱",
    layout="wide"
)

# 메인 타이틀
st.title("🌱 ESG 전문가 AI")
st.markdown("""
### 파인튜닝된 GPT 모델을 활용한 ESG 전문가 AI 시스템

이 시스템은 ESG(환경, 사회, 지배구조) 분야의 전문 지식을 가진 AI 챗봇을 제공합니다.
파인튜닝된 GPT 모델을 통해 ESG 관련 질문에 전문적이고 정확한 답변을 제공합니다.
""")

# 주요 기능 소개
st.markdown("### ✨ 주요 기능")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    #### 💬 전문가 수준의 대화
    - ESG 전문가 수준의 상세한 답변
    - 맥락을 이해하는 자연스러운 대화
    - 전문 용어에 대한 명확한 설명
    """)

with col2:
    st.markdown("""
    #### 📚 다양한 ESG 주제
    - 환경(Environmental) 관련 정보
    - 사회(Social) 책임 활동
    - 지배구조(Governance) 관련 지식
    - ESG 평가 및 보고서
    """)

with col3:
    st.markdown("""
    #### 🔄 실시간 응답
    - 즉각적인 답변 제공
    - 대화 기록 유지
    - 쉬운 대화 초기화
    """)

# 시작하기 섹션
st.markdown("### 🚀 시작하기")
st.markdown("""
1. 왼쪽 사이드바의 '챗봇' 메뉴를 클릭하세요.
2. 파인튜닝된 모델 ID를 입력하세요.
3. ESG 관련 질문을 자유롭게 입력하세요.

더 자세한 사용 방법은 '사용방법' 메뉴를 참고해주세요.
""")

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>ESG 전문가 AI 시스템 | 파인튜닝된 GPT 모델 기반</p>
</div>
""", unsafe_allow_html=True) 