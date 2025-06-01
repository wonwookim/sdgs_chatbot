import streamlit as st

st.set_page_config(
    page_title="ESG 전문가 AI - ESG 소개",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 ESG 소개")

# ESG 개요
st.markdown("""
### ESG란?
ESG는 환경(Environmental), 사회(Social), 지배구조(Governance)의 약자로, 기업의 지속가능성을 평가하는 핵심 지표입니다.
""")

# ESG 구성요소 설명
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🌱 환경 (Environmental)
    - 기후변화 대응
    - 탄소배출량 관리
    - 에너지 효율성
    - 자원 재활용
    - 생물다양성 보존
    - 환경오염 방지
    """)

with col2:
    st.markdown("""
    ### 👥 사회 (Social)
    - 노동인권
    - 안전보건
    - 공급망 관리
    - 지역사회 관계
    - 고객 보호
    - 다양성과 포용성
    """)

with col3:
    st.markdown("""
    ### ⚖️ 지배구조 (Governance)
    - 이사회 구성
    - 주주권리 보호
    - 부패방지
    - 윤리경영
    - 투명한 정보공시
    - 리스크 관리
    """)

# ESG의 중요성
st.markdown("""
### 💡 ESG의 중요성

#### 1. 투자 관점
- 장기적 가치 창출
- 리스크 관리 강화
- 투자자 선호도 증가
- 기업 가치 평가 기준

#### 2. 기업 관점
- 지속가능한 경쟁력 확보
- 브랜드 가치 향상
- 인재 유치 및 유지
- 규제 대응력 강화

#### 3. 사회적 관점
- 지속가능한 발전
- 사회적 책임 실현
- 이해관계자 만족도 향상
- 글로벌 표준 준수
""")

# ESG 평가체계
st.markdown("""
### 📊 주요 ESG 평가체계

1. **MSCI ESG Ratings**
   - 글로벌 기업 ESG 평가
   - AAA~CCC 등급 체계
   - 37개 산업별 평가

2. **Sustainalytics**
   - ESG 리스크 평가
   - 0-100점 점수 체계
   - 상세한 리스크 분석

3. **CDP (Carbon Disclosure Project)**
   - 기후변화 대응 평가
   - A-F 등급 체계
   - 탄소배출량 관리

4. **Korea ESG Standards**
   - 국내 기업 ESG 평가
   - 환경/사회/지배구조 세부 평가
   - 산업별 특화 지표
""")

# ESG 트렌드
st.markdown("""
### 🔮 ESG 트렌드

#### 1. 글로벌 동향
- 탄소중립 목표 확대
- ESG 정보공시 의무화
- 그린뉴딜 정책 확산
- ESG 투자 규모 증가

#### 2. 국내 동향
- ESG 평가체계 도입
- 그린뉴딜 정책 추진
- ESG 채권 발행 증가
- 기업 ESG 경영 확대

#### 3. 미래 전망
- ESG 통합 경영 확대
- 디지털 ESG 발전
- ESG 데이터 표준화
- 글로벌 협력 강화
""") 