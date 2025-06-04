import streamlit as st
import os

st.set_page_config(
    page_title="ESG 전문가 AI - ESG 소개",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 ESG 소개")

# 1. ESG란? 맨 위
st.markdown("""
### ESG란?
ESG는 환경(Environmental),사회(Social),지배구조(Governance)의 영문 첫 글자를 조합한 단어로,<br>
기업 경영에서 지속가능성을 달성하기 위한 3가지 핵심 요소입니다.
""", unsafe_allow_html=True)

# 카드 스타일 (min-width 줄이고 width:100% 추가)
card_style = """
    <div class='card-hover' style='
        border: 2px solid #e0e0e0; border-radius: 18px; padding: 18px 18px; 
        background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,0.04); 
        min-width: 160px; max-width: 340px; width: 100%; margin-left:auto; margin-right:auto;
        display: flex; flex-direction: column; justify-content: flex-start; flex:1; margin-bottom: 0;'>
        {content}
    </div>
"""

# 카드 스타일 CSS 복구
st.markdown("""
    <style>
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
    </style>
""", unsafe_allow_html=True)

# 기존 아이콘 3개 대신 중앙에 circles.png 이미지만 띄우기
st.image(os.path.join(os.path.dirname(__file__), 'assets', 'circles_2.png'), width=850)

st.markdown("""
<div style='display:flex; justify-content:center; gap:36px; flex-wrap:wrap;'>
    <div style='min-width:220px; max-width:320px;'>
        <div style='font-size:1.25rem; font-weight:700; text-align:center;'>Environmental<br><span style="font-size:1.1rem; font-weight:500;">(환경)</span></div>
        <ul class='pretty-list'>
            <li>탄소 배출 감축 및 기후 변화 대응</li>
            <li>오염물질 관리와 친환경 기술 도입</li>
            <li>생물다양성 보존과 생태계 보호</li>
        </ul>
    </div>
    <div style='min-width:220px; max-width:320px;'>
        <div style='font-size:1.25rem; font-weight:700; text-align:center;'>Social<br><span style="font-size:1.1rem; font-weight:500;">(사회)</span></div>
        <ul class='pretty-list'>
            <li>개인정보 보호 및 정보 보안 강화</li>
            <li>다양성과 포용을 중시한 안전경영</li>
            <li>지역사회와의 지속가능한 상생 관계</li>
        </ul>
    </div>
    <div style='min-width:220px; max-width:320px;'>
        <div style='font-size:1.25rem; font-weight:700; text-align:center;'>Governance<br><span style="font-size:1.1rem; font-weight:500;">(지배구조)</span></div>
        <ul class='pretty-list'>
            <li>투명한 이사회 및 위원회 운영</li>
            <li>윤리적 책임과 공정한 내부 통제</li>
            <li>부패 방지 및 준법 경영</li>
        </ul>
    </div>
</div>
""", unsafe_allow_html=True)

# ESG의 중요성 (가로 3개 카드)
st.markdown("<div style='margin-top:36px;'></div>", unsafe_allow_html=True)
st.markdown("### 💡 ESG의 중요성")
col4, col5, col6 = st.columns(3, gap='small')
with col4:
    st.markdown(card_style.format(content="""
    <h4>1. 투자 관점</h4>
    <ul class='pretty-list'>
        <li>장기적 가치 창출</li>
        <li>리스크 관리 강화</li>
        <li>투자자 선호도 증가</li>
        <li>기업 가치 평가 기준</li>
    </ul>
    """), unsafe_allow_html=True)
with col5:
    st.markdown(card_style.format(content="""
    <h4>2. 기업 관점</h4>
    <ul class='pretty-list'>
        <li>지속가능한 경쟁력 확보</li>
        <li>브랜드 가치 향상</li>
        <li>인재 유치 및 유지</li>
        <li>규제 대응력 강화</li>
    </ul>
    """), unsafe_allow_html=True)
with col6:
    st.markdown(card_style.format(content="""
    <h4>3. 사회적 관점</h4>
    <ul class='pretty-list'>
        <li>지속가능한 발전</li>
        <li>사회적 책임 실현</li>
        <li>이해관계자 만족도 향상</li>
        <li>글로벌 표준 준수</li>
    </ul>
    """), unsafe_allow_html=True)

# ESG 트렌드 (가로 3개 카드)
st.markdown("<div style='margin-top:36px;'></div>", unsafe_allow_html=True)
st.markdown("### 🔮 ESG 트렌드")
col7, col8, col9 = st.columns(3, gap='small')
with col7:
    st.markdown(card_style.format(content="""
    <h4>1. 글로벌 동향</h4>
    <ul class='pretty-list'>
        <li>탄소중립 목표 확대</li>
        <li>ESG 정보공시 의무화</li>
        <li>그린뉴딜 정책 확산</li>
        <li>ESG 투자 규모 증가</li>
    </ul>
    """), unsafe_allow_html=True)
with col8:
    st.markdown(card_style.format(content="""
    <h4>2. 국내 동향</h4>
    <ul class='pretty-list'>
        <li>ESG 평가체계 도입</li>
        <li>그린뉴딜 정책 추진</li>
        <li>ESG 채권 발행 증가</li>
        <li>기업 ESG 경영 확대</li>
    </ul>
    """), unsafe_allow_html=True)
with col9:
    st.markdown(card_style.format(content="""
    <h4>3. 미래 전망</h4>
    <ul class='pretty-list'>
        <li>ESG 통합 경영 확대</li>
        <li>디지털 ESG 발전</li>
        <li>ESG 데이터 표준화</li>
        <li>글로벌 협력 강화</li>
    </ul>
    """), unsafe_allow_html=True) 