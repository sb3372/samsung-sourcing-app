import streamlit as st
from tavily import TavilyClient

st.set_page_config(page_title="Samsung Sourcing Agent", layout="wide")
st.title("🛡️ Strategic Sourcing Intelligence - Samsung Europe")

# Input for API Key
tavily_key = st.sidebar.text_input("Tavily API Key", type="password")

if st.button("Start Live Search"):
    if not tavily_key:
        st.warning("Please enter your Tavily API Key.")
    else:
        try:
            client = TavilyClient(api_key=tavily_key)
            results = client.search(query="European electronic component price volatility 2026", search_depth="advanced")
            for res in results['results']:
                st.subheader(res['title'])
                st.write(f"[Source Link]({res['url']})")
                st.info(f"**Content:** {res['content'][:500]}...")
                st.divider()
        except Exception as e:
            st.error(f"Error: {e}")
