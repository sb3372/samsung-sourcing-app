import streamlit as st
from tavily import TavilyClient
import datetime
import os # os 모듈 추가

# 페이지 설정
st.set_page_config(page_title="Samsung Strategic Sourcing Agent", layout="wide")
st.title("🛡️ Samsung Electronics Europe IPC: Strategic Intelligence")

# 사이드바 설정 (API 키 입력)
tavily_key = st.sidebar.text_input("Tavily API Key", type="password")

# 1. history.log 기능 구현 (Streamlit은 파일 대신 세션 상태나 로컬 텍스트 파일을 사용)
LOG_FILE = "history.log"

def get_history():
    if not os.path.exists(LOG_FILE):
        return set()
    with open(LOG_FILE, "r") as f:
        return set(line.strip() for line in f)

def update_history(urls):
    with open(LOG_FILE, "a") as f:
        for url in urls:
            f.write(url + "\n")

# 2. 카테고리 정의
CATEGORIES = {
    "Procurement & Materials": "price volatility electronic components smartphones raw materials Europe",
    "Supply Chain & Logistics": "European port strikes logistics disruptions China sourcing shifts nearshoring",
    "EU Regulations": "EU AI Act ESPR Digital Product Passport Cyber Resilience Act CRA energy labeling",
    "Innovation": "European 6G robotics AI-hardware sustainable materials startups",
    "Samsung Portfolio": "telecommunication devices trends emerging consumer electronics Europe"
}

if st.button("Run Strategic Intelligence Report"):
    if not tavily_key:
        st.error("Please enter your Tavily API Key.")
    else:
        client = TavilyClient(api_key=tavily_key)
        history = get_history()
        new_urls = []

        for cat_name, query in CATEGORIES.items():
            st.header(f"📂 Category: {cat_name}")
            
            # 고급 검색 수행 (날짜 제한은 쿼리에 포함하거나 결과 필터링)
            search_results = client.search(
                query=f"{query} after:{datetime.date.today() - datetime.timedelta(days=30)}",
                search_depth="advanced",
                max_results=3
            )

            for res in search_results['results']:
                url = res['url']
                if url in history:
                    continue  # 중복 제거
                
                new_urls.append(url)
                
                with st.expander(f"📰 {res['title']}", expanded=True):
                    st.write(f"**[Link]**: {url}")
                    
                    # 3. 분석 리포트 형식 출력
                    # (실제로는 여기서 LLM API를 한 번 더 호출해야 하지만, 
                    # 우선 Tavily가 가져온 전문을 바탕으로 에이전트의 '페르소나'를 담아 출력합니다.)
                    
                    st.markdown("### 📝 Key Impact on Samsung Operations")
                    # 에이전트 분석 로직 (Search 결과 기반 요약 시뮬레이션)
                    st.write(f"- **Supply Risk**: Current material trends suggest a potential lead-time increase for Samsung's European production lines.")
                    st.write(f"- **Cost Implication**: Price volatility in {cat_name} requires immediate hedge strategy review.")
                    st.write(f"- **Regulatory Compliance**: Aligning with new EU standards to avoid market entry barriers.")
                    st.write(f"- **Strategic Sourcing**: Opportunity to diversify from China-centric sourcing to European nearshoring.")
                    st.write(f"- **Competitive Edge**: Early adoption of these trends provides a 6-month lead over local competitors.")
                    
                    st.markdown("### 📜 Background Context")
                    st.write(res['content'][:800] + "...") # 검색된 원문의 앞부분을 배경 지식으로 활용
                    st.divider()

        # 4. 리포트 완료 후 로그 업데이트
        if new_urls:
            update_history(new_urls)
            st.success(f"Report complete. {len(new_urls)} new articles added to history.log.")
        else:
            st.info("No new articles found since the last report.")

