import streamlit as st

st.set_page_config(page_title="Samsung 뉴스 수집기", page_icon="📰")
st.title("📰 Samsung 국제 조달센터 뉴스 수집기")

with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("🔑 Gemini API 키", type="password")
    
    if api_key:
        st.success("✅ API 키 설정 완료!")

st.info("✅ 앱이 정상 작동합니다!")
