import streamlit as st

st.set_page_config(
    page_title="Samsung 국제 조달센터 뉴스 수집기",
    page_icon="📰",
    layout="wide",
)

st.title("📰 Samsung 국제 조달센터 뉴스 수집기")
st.markdown("---")

# 테스트: API 키 입력만
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input(
        "🔑 Gemini API 키 입력",
        type="password",
    )
    
    if api_key:
        st.success("✅ API 키 수신 완료!")

st.info("✅ 앱이 정상 작동합니다!")
