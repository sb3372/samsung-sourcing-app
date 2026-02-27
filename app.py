import streamlit as st

st.set_page_config(page_title="Samsung 뉴스 수집기", page_icon="📰")

st.title("📰 Samsung 국제 조달센터")
st.markdown("유럽 기술 뉴스 - 자동 한국어 요약")
st.markdown("---")

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
        st.caption(f"출처: {article['source']} | [원문]({article['link']})")
        st.divider()
else:
    st.info("🔄 REFRESH 버튼을 클릭하여 기사를 로드하세요")
