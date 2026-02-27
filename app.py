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
if "debug_logs" not in st.session_state:
    st.session_state.debug_logs = []

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
            st.session_state.debug_logs = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            debug_area = st.empty()
            
            total_queries = 0
            for category in selected_categories:
                for region in selected_regions:
                    region_lang = REGIONS[region]["lang"]
                    category_queries = SEARCH_QUERIES[category]["queries"]
                    
                    lang_key = region_lang + "_" + region
                    if lang_key in category_queries:
                        total_queries += len(category_queries[lang_key])
                    elif "en_US" in category_queries:
                        total_queries += len(category_queries["en_US"])
            
            current = 0
            
            for category in selected_categories:
                category_queries = SEARCH_QUERIES[category]["queries"]
                
                for region in selected_regions:
                    region_data = REGIONS[region]
                    region_lang = region_data["lang"]
                    
                    # 해당 언어의 쿼리 가져오기
                    lang_key = region_lang + "_" + region
                    if lang_key in category_queries:
                        queries = category_queries[lang_key]
                    elif "en_US" in category_queries:
                        queries = category_queries["en_US"]
                    else:
                        queries = []
                    
                    for query in queries:
                        current += 1
                        progress = current / max(total_queries, 1)
                        progress_bar.progress(min(progress, 0.99))
                        status_text.text(f"수집: {category} - {region} ({current}/{total_queries})")
                        
                        try:
                            st.session_state.debug_logs.append(f"🔍 쿼리: {query[:60]}... ({region})")
                            debug_area.text_area(
                                "📋 디버그 로그",
                                "\n".join(st.session_state.debug_logs[-10:]),
                                height=150,
                                disabled=True
                            )
                            
                            articles = st.session_state.scraper.fetch_rss_feed(
                                query,
                                region_lang,
                                region_data["ceid"]
                            )
                            
                            if articles:
                                st.session_state.debug_logs.append(f"✅ {len(articles)}개 기사 발견")
                            else:
                                st.session_state.debug_logs.append(f"⚠️ 기사 없음")
                            
                            for article in articles:
                                processed = st.session_state.scraper.process_article(article)
                                if processed:
                                    processed["category"] = category
                                    st.session_state.articles.append(processed)
                                    st.session_state.debug_logs.append(f"✓ 기사 추가: {processed['title'][:40]}...")
                        
                        except Exception as e:
                            st.session_state.debug_logs.append(f"❌ 오류: {str(e)[:50]}")
                        
                        time.sleep(0.2)
            
            progress_bar.progress(1.0)
            status_text.empty()
            
            if st.session_state.articles:
                st.success(f"✅ {len(st.session_state.articles)}개 기사 수집 완료")
            else:
                st.warning("⚠️ 수집된 기사 없음 - 디버그 로그 확인")
                with st.expander("📋 전체 디버그 로그"):
                    st.text_area(
                        "로그",
                        "\n".join(st.session_state.debug_logs),
                        height=300,
                        disabled=True
                    )

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
