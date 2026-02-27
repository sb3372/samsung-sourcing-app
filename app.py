import streamlit as st
import time
import logging
from config import WEBSITES, CATEGORIES
from crawler import WebCrawler
from deduplicator import Deduplicator
from categorizer import Categorizer
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Samsung 뉴스", page_icon="📰", layout="wide")

if "articles" not in st.session_state:
    st.session_state.articles = []
if "deduplicator" not in st.session_state:
    st.session_state.deduplicator = Deduplicator()

st.title("📰 Samsung 국제 조달센터")
st.markdown("유럽 기술 뉴스 - AI 카테고리 분류")
st.markdown("---")

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    
    # Gemini API 키
    api_key = st.text_input(
        "🔑 Gemini API 키",
        type="password",
        help="https://aistudio.google.com/app/apikey에서 발급"
    )
    
    if api_key:
        st.session_state.gemini_key = api_key
        st.success("✅ API 준비 완료")
    
    st.markdown("---")
    
    st.header("📂 카테고리 선택")
    selected_categories = []
    
    for category in CATEGORIES:
        if st.checkbox(category, value=True):
            selected_categories.append(category)
    
    st.session_state.selected_categories = selected_categories

st.header("🔄 뉴스 수집")

if st.button("🔄 새로운 기사 로드", use_container_width=True, type="primary"):
    
    if "gemini_key" not in st.session_state:
        st.error("❌ API 키를 먼저 입력하세요")
    elif not st.session_state.selected_categories:
        st.error("❌ 카테고리를 선택하세요")
    else:
        status_text = st.empty()
        
        try:
            # 1단계: 병렬 웹 크롤링
            status_text.text("🔗 웹사이트 병렬 크롤링 중...")
            
            crawler = WebCrawler()
            all_articles = crawler.crawl_all_websites(WEBSITES, max_workers=10)
            
            logger.info(f"총 {len(all_articles)}개 기사 수집")
            status_text.text(f"✅ {len(all_articles)}개 기사 수집 완료")
            time.sleep(1)
            
            # 2단계: 중복 제거
            status_text.text("🔍 중복 제거 중...")
            unique_articles = []
            
            for article in all_articles:
                if not st.session_state.deduplicator.is_duplicate(article):
                    unique_articles.append(article)
            
            logger.info(f"중복 제거 후 {len(unique_articles)}개 기사")
            status_text.text(f"✅ {len(unique_articles)}개 새 기사 발견")
            time.sleep(1)
            
            # 3단계: AI로 카테고리 분류
            status_text.text("🤖 AI 카테고리 분류 중...")
            categorizer = Categorizer(st.session_state.gemini_key)
            
            categorized_articles = []
            for idx, article in enumerate(unique_articles):
                status_text.text(f"분류 중: {idx + 1}/{len(unique_articles)}")
                
                # AI로 카테고리 분류
                ai_categories = categorizer.categorize_article(article['title_en'])
                article['categories'] = ai_categories
                categorized_articles.append(article)
                
                time.sleep(0.3)  # API 요청 간격
            
            logger.info(f"카테고리 분류 완료")
            status_text.text(f"✅ 카테고리 분류 완료")
            time.sleep(1)
            
            # 4단계: 선택된 카테고리로 필터링
            status_text.text("📂 카테고리 필터링 중...")
            filtered_articles = []
            
            for article in categorized_articles:
                # 선택된 카테고리와 겹치는지 확인
                if any(cat in article['categories'] for cat in st.session_state.selected_categories):
                    filtered_articles.append(article)
            
            logger.info(f"필터링 후 {len(filtered_articles)}개 기사")
            status_text.text(f"📂 {len(filtered_articles)}개 기사 필터링 완료")
            time.sleep(1)
            
            # 5단계: 다양한 소스에서 10개 선택
            status_text.text("🎯 다양한 소스에서 기사 선택 중...")
            
            # 소스별로 기사 분류
            articles_by_source = defaultdict(list)
            for article in filtered_articles:
                articles_by_source[article['source']].append(article)
            
            # 각 소스에서 고르게 선택
            final_articles = []
            source_index = defaultdict(int)
            
            while len(final_articles) < 10 and len(articles_by_source) > 0:
                for source in list(articles_by_source.keys()):
                    if len(final_articles) >= 10:
                        break
                    
                    if source_index[source] < len(articles_by_source[source]):
                        article = articles_by_source[source][source_index[source]]
                        final_articles.append(article)
                        source_index[source] += 1
                
                # 모든 소스를 한 번 순회했는데도 10개 미만이면, 중복 선택
                if len(final_articles) < 10:
                    for source in list(articles_by_source.keys()):
                        if len(final_articles) >= 10:
                            break
                        source_index[source] = 0  # 초기화
            
            top_articles = final_articles[:10]
            
            # 기사를 CSV에 저장 (중복 등록)
            for article in top_articles:
                st.session_state.deduplicator.save_article({
                    'title_en': article['title_en'],
                    'link': article['link'],
                    'source': article['source'],
                    'categories': ','.join(article['categories'])
                })
            
            st.session_state.articles = top_articles
            
            time.sleep(1)
            status_text.empty()
            st.success(f"✅ {len(top_articles)}개 기사 로드 완료!")
        
        except Exception as e:
            st.error(f"❌ 오류 발생: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            logger.error(f"전체 오류: {str(e)}")

st.markdown("---")

if st.session_state.articles:
    st.header(f"📊 수집된 기사 ({len(st.session_state.articles)}개)")
    
    for idx, article in enumerate(st.session_state.articles, 1):
        with st.container():
            st.subheader(f"{idx}. {article['title_en']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                categories_str = ", ".join(article['categories'])
                st.caption(f"📂 {categories_str}")
            with col2:
                st.caption(f"출처: {article['source']}")
            with col3:
                st.markdown(f"[🔗 원문]({article['link']})")
            
            st.divider()

else:
    st.info("🔄 '새로운 기사 로드' 버튼을 클릭하여 기사를 수집하세요")
