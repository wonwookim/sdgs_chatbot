# ESG
import streamlit as st
import torch
import types
import os
# torch.classes 패치 (Streamlit 에러 우회용)
torch.classes = types.SimpleNamespace()
st.set_page_config(
    page_title="ESG 전문가 AI",
    page_icon="🌱",
    layout="wide"
)

# 스타일 (폰트X, 카드/로고/리스트만)
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        background: #f6f8fa;
    }
    .card-hover:hover {
        box-shadow: 0 6px 24px rgba(0,0,0,0.10);
        transform: translateY(-4px) scale(1.02);
        transition: 0.2s;
    }
    .card-hover {
        transition: 0.2s;
    }
    .pretty-list {
        list-style: none;
        padding-left: 0;
        margin-top: 12px;
    }
    .pretty-list li {
        margin-bottom: 8px;
        padding-left: 0;
        position: relative;
    }
    .pretty-list li:before {
        content: "✔️";
        position: absolute;
        left: -28px;
        font-size: 1.1em;
        top: 0;
    }
    .logo-row {
        display: flex;
        gap: 18px;
        align-items: center;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .logo-row img {
        width: 48px;
        height: 48px;
        border-radius: 10px;
        background: #fff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        object-fit: contain;
        border: 1px solid #e0e0e0;
    }
    .block-container {
        padding-left: 2.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌱 ESG 전문가 AI")
st.markdown("""
### <b>파인튜닝된 GPT 모델을 활용한 ESG 전문가 AI 시스템</b>
이 시스템은 ESG(환경, 사회, 지배구조) 분야의 전문 지식을 가진 AI 챗봇을 제공합니다.<br>
파인튜닝된 GPT 모델을 통해 ESG 관련 질문에 전문적이고 정확한 답변을 제공합니다.
""", unsafe_allow_html=True)

st.markdown("### ✨ 주요 기능")

# 카드 스타일 (min-height 늘림, flex:1)
card_style = """
    <div class='card-hover' style='
        border: 2px solid #e0e0e0; border-radius: 18px; padding: 28px 22px; 
        background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,0.04); 
        min-height: 280px; display: flex; flex-direction: column; justify-content: flex-start; flex:1;'>
        {content}
    </div>
"""

# 카드 컬럼 (gap 줄임)
col1, col2, col3 = st.columns([1.3, 1.3, 1.3], gap='small')

with col1:
    st.markdown(card_style.format(content="""
    <div style='display: flex; align-items: center; gap: 10px; white-space: nowrap;'>
        <span style='font-size:2.1rem;'>💬</span>
        <h4 style='margin:0; display:inline-block; vertical-align:middle;'>전문가 수준의 대화</h4>
    </div>
    <ul class='pretty-list'>
        <li>ESG 전문가 수준의 상세한 답변</li>
        <li>맥락을 이해하는 자연스러운 대화</li>
        <li>전문 용어에 대한 명확한 설명</li>
    </ul>
    """), unsafe_allow_html=True)

with col2:
    st.markdown(card_style.format(content="""
    <div style='display: flex; align-items: center; gap: 10px;'>
        <span style='font-size:2.1rem;'>📚</span>
        <h4 style='margin:0;'>다양한 ESG 주제</h4>
    </div>
    <ul class='pretty-list'>
        <li>환경(Environmental) 관련 정보</li>
        <li>사회(Social) 책임 활동</li>
        <li>지배구조(Governance) 관련 지식</li>
        <li>ESG 평가 및 보고서</li>
    </ul>
    """), unsafe_allow_html=True)

with col3:
    st.markdown(card_style.format(content="""
    <div style='display: flex; align-items: center; gap: 10px;'>
        <span style='font-size:2.1rem;'>🔄</span>
        <h4 style='margin:0;'>실시간 응답</h4>
    </div>
    <ul class='pretty-list'>
        <li>즉각적인 답변 제공</li>
        <li>대화 기록 유지</li>
        <li>쉬운 대화 초기화</li>
    </ul>
    """), unsafe_allow_html=True)

# 시작하기 + 로고 (박스 길이 자동, 로고 옆에)
st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
st.markdown("### 🚀 시작하기")
start_col, logo_col = st.columns([1, 1])

with start_col:
    st.markdown("""
    <div class='card-hover' style='
        display: inline-block;
        border: 2px solid #e0e0e0; border-radius: 18px; padding: 28px 22px;
        background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        min-width: 320px; max-width: 480px; vertical-align: middle;'>
        <div style='display: flex; align-items: center; gap: 10px;'>
            <span style='font-size:2.1rem;'></span>
        </div>
        <ul class='pretty-list'>
            <li>왼쪽 사이드바의 '챗봇' 메뉴를 클릭하세요.</li>
            <li>파인튜닝된 모델 ID를 입력하세요.</li>
            <li>ESG 관련 질문을 자유롭게 입력하세요.</li>
            <li>더 자세한 사용 방법은 '사용방법' 메뉴를 참고해주세요.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with logo_col:
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    st.image(os.path.join(os.path.dirname(__file__), 'pages', 'assets', 'logos.png'), width=800)
    st.markdown("""
    <div style='text-align:center; font-size:1.1rem; color:#444; font-weight:500;'>
        한국ESG기준원 선정 2023 우수기업
    </div>
    """, unsafe_allow_html=True)

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>ESG 전문가 AI 시스템 | 파인튜닝된 GPT 모델 기반</p>
</div>
""", unsafe_allow_html=True) 