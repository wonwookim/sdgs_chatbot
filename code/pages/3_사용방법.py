import streamlit as st

st.set_page_config(
    page_title="ESG 전문가 AI - 사용방법",
    page_icon="📖",
    layout="wide"
)

st.title("📖 사용방법")

# 사용 가이드 섹션
st.subheader("🛠 ESG 전문가 AI 사용 가이드")
# 1행 3열 배치
col1, col2, col3 = st.columns(3)

# col1~3: 박스 규격 통일
box_style = """
    border: 1px solid #E0E0E0;
    border-radius: 10px;
    padding: 15px;
    background-color: #FAFAFA;
    margin-bottom: 15px;
    min-height: 250px;
"""

# 모델 설정 안내
with col1:
    st.markdown(f"""
    <div style="{box_style}">
        <h5 style="color: black;">1. 모델 설정</h5>
        <ul style="color: black;">
            <li>왼쪽 사이드바에서 모델 설정을 선택하세요.</li>
            <li><strong>ESG 전문가 모델</strong>을 사용하려면 스위치를 켜세요.</li>
            <li>기본 GPT-3.5 모델을 사용하려면 스위치를 끄세요.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 챗봇 사용법 안내
with col2:
    st.markdown(f"""
    <div style="{box_style}">
        <h5 style="color: black;">2. 챗봇 사용하기</h5>
        <ul style="color: black;">
            <li>하단 입력창에 ESG 관련 질문을 입력하세요.</li>
            <li>AI가 우수 기업 사례 기반으로 전문 답변을 제공합니다.</li>
            <li>대화 내용은 세션 동안 유지되며, ‘대화 초기화’로 새로 시작할 수 있습니다.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 주의사항 안내
with col3:
    st.markdown("""
    <div style="
        border: 1px solid #FFF3CD;
        border-radius: 10px;
        padding: 15px;
        background-color: #FFFBEB;
        margin-bottom: 15px;
        min-height: 250px;">
        <h5 style="color: black;">⚠️ 주의사항</h5>
        <ul style="color: black;">   
            <li><strong>회사의 <u>ESG 전략이나 실행 계획</u>을 구체적으로 입력해 주세요.</strong></li>
            <li><strong>AI는 우수 사례와의 비교를 통해 전략의 적절성과 개선점을 제시합니다.</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 예시 질문 섹션
st.subheader("💡 예시 질문")
# 2행 3열 배치
col4, col5, col6 = st.columns(3)

# col4~6: 박스 규격 통일(색상 제외)
example_style = "padding: 15px; border-radius: 8px; margin-bottom: 10px; min-height: 250px;"

# 환경 예시 질문
with col4:
    st.markdown(f"""
    <div style="border: 1px solid #C5E1A5; background-color: #F9FFF3; {example_style}">
        <h5 style="color: black;">🌱 환경 (Environment)</h5>
        <ul style="color: black;">
            <li>사옥 전력의 30%를 태양광으로 전환했는데, 이런 점이 ESG 우수 전략으로 인정되나요?</li>
            <li>일회용 플라스틱 용기를 전 매장에서 사용 중인데, ESG 평가 시 감점 요인이 될까요?</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 사회 예시 질문
with col5:
    st.markdown(f"""
    <div style="border: 1px solid #B3E5FC; background-color: #F2FBFF; {example_style}">
        <h5 style="color: black;">👥 사회 (Social)</h5>
        <ul style="color: black;">
            <li>여성 임원 비율이 20% 감소했는데, 다양성 측면에서 부정적 평가를 받을 수 있나요?</li>
            <li>협력사 ESG 평가를 연 1회 실시하고 결과를 공개하는 방식은 일반적인가요?</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown(f"""
    <div style="border: 1px solid #D1C4E9; background-color: #FAF5FF; {example_style}">
        <h5 style="color: black;">🏛 지배구조 (Governance)</h5>
        <ul style="color: black;">
            <li>사내 윤리강령을 전 구성원에게 교육하고 서약을 받는 방식은 효과적인가요?</li>
            <li>내부 고발 제도에서 익명성이 부족하다는 지적을 받았는데, 좋은 운영 사례는?</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
