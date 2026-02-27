import streamlit as st
from config import SEARCH_QUERIES, SYSTEM_PROMPT
from news_scraper import NewsScraper
import time

st.set_page_config(
    page_title="Samsung 뉴스 수집기",
    page_icon="📰",
    layout="wide",
)

st.title("📰 Samsung 국제 조달센터 뉴스 수집기")
st.markdown("유럽 다언어 뉴스 → 한국어 요약")
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
    
    # 카테고리 선택 (지역 선택 제거)
    st.header("📂 카테고리")
    selected_categories = []
    
    for category in SEARCH_QUERIES.keys():
        if st.checkbox(category, value=True):
            selected_categories.append(category)
    
    st.markdown("---")
    
    # 수집 버튼
    if st.button("🔍 뉴스 수집", use_container_width=True, type="primary"):
        if not st.session_state.api_key_set:
            st.error("❌ API 키 입력 필요")
        elif not selected_categories:
            st.error("❌ 카테고리 선택 필요")
        else:
            st.session_state.articles = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 선택된 카테고리의 총 쿼리 수 계산
            total_queries = sum(len(SEARCH_QUERIES[cat]) for cat in selected_categories)
            current = 0
            
            for category in selected_categories:
                queries = SEARCH_QUERIES[category]
                
                for query in queries:
                    current += 1
                    progress = current / total_queries
                    progress_bar.progress(min(progress, 0.99))
                    status_text.text(f"수집 중: {category} ({current}/{total_queries})")
                    
                    try:
                        # RSS에서 기사 가져오기
                        articles = st.session_state.scraper.fetch_rss_feed(query)
                        
                        for article in articles:
                            processed = st.session_state.scraper.process_article(article)
                            if processed:
                                processed["category"] = category
                                st.session_state.articles.append(processed)
                    
                    except Exception as e:
                        print(f"오류: {e}")
                    
                    time.sleep(0.1)
            
            progress_bar.progress(1.0)
            status_text.empty()
            
            if st.session_state.articles:
                st.success(f"✅ {len(st.session_state.articles)}개 기사 수집 완료")
            else:
                st.warning("⚠️ 수집된 기사 없음")

# 메인 콘텐츠
if st.session_state.articles:
    st.header(f"📊 수집된 뉴스 ({len(st.session_state.articles)}개)")
    st.markdown("---")
    
    for idx, article in enumerate(st.session_state.articles):
        st.subheader(article["title"])
        
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"📂 {article['category']}")
        with col2:
            st.caption(f"📅 {article.get('published', 'N/A')[:10]}")
        
        # 한국어 요약만 표시
        st.markdown(article["summary"])
        
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"출처: {article['source']}")
        with col2:
            st.markdown(f"[🔗 원문]({article['link']})")
        
        st.divider()

else:
    if st.session_state.api_key_set:
        st.info("📋 '뉴스 수집' 버튼을 클릭하세요")
    else:
        st.warning("⚠️ API 키를 먼저 입력하세요")
