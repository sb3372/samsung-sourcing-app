import streamlit as st

st.set_page_config(page_title="Samsung 뉴스 수집기", page_icon="📰", layout="wide")

st.title("📰 Samsung 국제 조달센터")
st.markdown("유럽 기술 뉴스 - 자동 한국어 요약")
st.markdown("---")

# 카테고리
CATEGORIES = [
    "반도체 (고전 & 차세대)",
    "원자재 (희토류 & 채광)",
    "첨단소재 (그래핀, 나노기술, CMF)",
    "컴포넌트 (센서, 디스플레이, 액추에이터)",
    "소비자전자 (모바일, 홈, 웨어러블)",
    "포토닉스 & 양자",
    "연결성/6G",
    "로봇공학",
    "에너지/전력 (배터리 & 에너지 수확)",
    "지속가능/순환 공학"
]

# 세션 상태
if "articles" not in st.session_state:
    st.session_state.articles = []

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("🔑 Gemini API", type="password")
    
    if api_key:
        st.session_state.api_key = api_key
        st.success("✅ API 설정됨")
    
    st.markdown("---")
    
    st.header("📂 카테고리 선택")
    selected_categories = []
    for cat in CATEGORIES:
        if st.checkbox(cat, value=True):
            selected_categories.append(cat)

# REFRESH 버튼
if st.button("🔄 새로운 기사 로드", use_container_width=True, type="primary"):
    if "api_key" not in st.session_state:
        st.error("❌ API 키를 먼저 입력하세요")
    else:
        st.info("✅ 기사 수집 중... (개발 중)")

# 기사 표시
if st.session_state.articles:
    st.header(f"📊 기사 ({len(st.session_state.articles)}개)")
    for article in st.session_state.articles:
        st.subheader(article["title_ko"])
        st.caption(f"_원제목: {article['title_en']}_")
        st.markdown(article["summary"])
        st.caption(f"📂 {article['category']}")
        st.caption(f"출처: {article['source']} | [원문]({article['link']})")
        st.divider()
else:
    st.info("🔄 REFRESH 버튼을 클릭하여 기사를 로드하세요")
