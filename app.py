import streamlit as st
from config import SEARCH_QUERIES, REGIONS, SYSTEM_PROMPT, LANGUAGE_NAMES
from news_scraper import NewsScraper
import time

st.set_page_config(
    page_title="Samsung 뉴스 수집기",
    page_icon="📰",
    layout="wide",
)

st.title("📰 Samsung 국제 조달센터 뉴스 수집기")
st.markdown("전문 기술 매트릭스 기반 유럽 뉴스 수집")
st.markdown("---")

# 세션 초기화
if "scraper" not in st.session_state:
    st.session_state.scraper = None
if "articles" not in st.session_state:
    st.session_state.articles = []
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = False

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    
    # API 키
    api_key = st.text_input(
        "🔑 Gemini API 키",
        type="password",
        help="https://aistudio.google.com/app/apikey"
    )
    
    if api_key:
        st.session_state.api_key_set = True
        if st.session_state.scraper is None:
            st.session_state.scraper = NewsScraper(api_key, SYSTEM_PROMPT)
            st.success("✅ API 설정 완료!")
    else:
        st.session_state.api_key_set = False
        st.warning("⚠️ API 키 입력 필요")
    
    st.markdown("---")
    
    # 카테고리 선택
    st.header("📂 카테고리")
    selected_categories = []
    
    for category in SEARCH_QUERIES.keys():
        if st.checkbox(category, value=True):
            selected_categories.append(category)
    
    st.markdown("---")
    
    # 지역 선택
    st.header("🌍 지역")
    selected_regions = []
    for region in REGIONS.keys():
        if st.checkbox(region, value=True):
            selected_regions.append(region)
    
    st.markdown("---")
    
    # 수집 버튼
    if st.button("🔍 뉴스 수집", use_container_width=True, type="primary"):
        if not st.session_state.api_key_set:
            st.error("❌ API 키 입력 필요")
        elif not selected_categories or not selected_regions:
            st.error("❌ 카테고리/지역 선택 필요")
        else:
            st.session_state.articles = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total = len(selected_categories) * len(selected_regions) * 3
            current = 0
            
            for category in selected_categories:
                category_queries = SEARCH_QUERIES[category]["queries"]
                
                for region in selected_regions:
                    region_data = REGIONS[region]
                    
                    # 각 언어별 쿼리 실행
                    if region_data["lang"] + "_" + region in category_queries:
                        queries = category_queries[region_data["lang"] + "_" + region]
                    else:
                        queries = category_queries.get("en_US", [])
                    
                    for query in queries:
                        current += 1
                        progress = current / total
                        progress_bar.progress(min(progress, 0.99))
                        status_text.text(f"수집: {category} - {region}")
                        
                        try:
                            articles = st.session_state.scraper.fetch_rss_feed(
                                query,
                                region_data["lang"],
                                region_data["ceid"]
                            )
                            
                            for article in articles:
                                processed = st.session_state.scraper.process_article(article)
                                if processed:
                                    processed["category"] = category
                                    st.session_state.articles.append(processed)
                        
                        except Exception as e:
                            print(f"오류: {e}")
                        
                        time.sleep(0.3)
            
            progress_bar.progress(1.0)
            status_text.empty()
            
            if st.session_state.articles:
                st.success(f"✅ {len(st.session_state.articles)}개 기사 수집 완료")
            else:
                st.warning("⚠️ 수집된 기사 없음")

# 메인
if st.session_state.articles:
    st.header(f"📊 수집된 뉴스 ({len(st.session_state.articles)}개)")
    st.markdown("---")
    
    for idx, article in enumerate(st.session_state.articles):
        st.subheader(article["title"])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.caption(f"📂 {article['category']}")
        with col2:
            st.caption(f"🌍 {article['region']}")
        with col3:
            st.caption(f"🗣️ {LANGUAGE_NAMES.get(article['language'], article['language'])}")
        with col4:
            st.caption(f"📅 {article['published'][:10]}")
        
        st.markdown(article["summary"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"출처: {article['source']}")
        with col2:
            st.caption(f"처리: {article['processed_at'][:19]}")
        with col3:
            st.markdown(f"[🔗 원문]({article['link']})")
        
        st.divider()

else:
    if st.session_state.api_key_set:
        st.info("📋 '뉴스 수집' 버튼을 클릭하세요")
    else:
        st.warning("⚠️ API 키를 먼저 입력하세요")
