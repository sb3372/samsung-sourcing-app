import streamlit as st
from config import SEARCH_CATEGORIES, REGIONS, SYSTEM_PROMPT, LANGUAGE_NAMES
from news_scraper import NewsScraper
import time

st.set_page_config(
    page_title="Samsung 뉴스 수집기",
    page_icon="📰",
    layout="wide",
)

st.title("📰 Samsung 국제 조달센터 뉴스 수집기")
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
    
    # API 키 입력
    api_key = st.text_input(
        "🔑 Gemini API 키",
        type="password",
        help="https://aistudio.google.com/app/apikey에서 발급"
    )
    
    if api_key:
        st.session_state.api_key_set = True
        if st.session_state.scraper is None:
            st.session_state.scraper = NewsScraper(api_key, SYSTEM_PROMPT)
            st.success("✅ API 키 설정 완료!")
    else:
        st.session_state.api_key_set = False
        st.warning("⚠️ API 키를 입력해주세요")
    
    st.markdown("---")
    
    # 카테고리 선택
    st.header("📂 카테고리 선택")
    selected_categories = []
    
    for category_name in SEARCH_CATEGORIES.keys():
        if st.checkbox(category_name, value=True):
            selected_categories.append(category_name)
    
    st.markdown("---")
    
    # 새로 불러오기 버튼
    if st.button("🔍 새로 불러오기", use_container_width=True, type="primary"):
        if not st.session_state.api_key_set:
            st.error("❌ API 키를 먼저 입력해주세요!")
        elif not selected_categories:
            st.error("❌ 최소 1개 카테고리를 선택해주세요!")
        else:
            st.session_state.articles = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_tasks = len(selected_categories) * len(REGIONS)
            current_task = 0
            
            for category_name in selected_categories:
                category_data = SEARCH_CATEGORIES[category_name]
                
                for region_name, region_data in REGIONS.items():
                    current_task += 1
                    progress = current_task / total_tasks
                    progress_bar.progress(progress)
                    status_text.text(f"수집 중... {category_name} - {region_name}")
                    
                    for keyword in category_data["keywords"]:
                        try:
                            articles = st.session_state.scraper.fetch_rss_feed(
                                keyword,
                                region_data["lang"],
                                region_data["region"]
                            )
                            
                            for article in articles:
                                processed = st.session_state.scraper.process_article(article)
                                if processed:
                                    processed["category"] = category_name
                                    st.session_state.articles.append(processed)
                        
                        except Exception as e:
                            print(f"오류: {e}")
                    
                    time.sleep(0.5)
            
            progress_bar.empty()
            status_text.empty()
            
            if st.session_state.articles:
                st.success(f"✅ 수집 완료! {len(st.session_state.articles)}개 기사")
            else:
                st.warning("⚠️ 수집된 기사가 없습니다.")

# 메인 콘텐츠
if st.session_state.articles:
    st.header(f"📊 수집된 뉴스 ({len(st.session_state.articles)}개)")
    st.markdown("---")
    
    for idx, article in enumerate(st.session_state.articles):
            for idx, article in enumerate(st.session_state.articles):
        with st.container():  # border=True 제거
            # 헤더
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                st.caption(f"📂 {article['category']}")
            
            with col2:
                st.caption(f"🌍 {article['region']} | 🗣️ {LANGUAGE_NAMES.get(article['language'], article['language'])}")
            
            with col3:
                if st.button("🔄", key=f"refresh_{idx}"):
                    st.info("재분석 기능은 추후 추가됩니다.")
            
            st.divider()  # 구분선 추가
            
            # 제목
            st.subheader(article["title"])
            
            # 요약
            st.markdown("### 📝 요약")
            st.markdown(article["summary"])
            
            # 소스 정보
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"**출처:** {article['source']}")
            with col2:
                st.caption(f"**발행일:** {article['published'][:10]}")
            with col3:
                st.markdown(f"[🔗 원본](https://news.google.com/search?q=cache:{article['link']})")

else:
    if st.session_state.api_key_set:
        st.info("📋 '새로 불러오기'를 클릭하여 뉴스를 수집하세요.")
    else:
        st.warning("⚠️ 먼저 API 키를 입력하세요.")
