import streamlit as st
import time
import logging
from config import WEBSITES, CATEGORIES
from crawler import WebCrawler
from deduplicator import Deduplicator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 페이지 설정
st.set_page_config(page_title="Samsung 뉴스", page_icon="📰", layout="wide")

# 세션 상태 초기화
if "articles" not in st.session_state:
    st.session_state.articles = []
if "deduplicator" not in st.session_state:
    st.session_state.deduplicator = Deduplicator()

# 제목
st.title("📰 Samsung 국제 조달센터")
st.markdown("유럽 기술 뉴스")
st.markdown("---")

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    
    st.markdown("---")
    
    # 카테고리 선택
    st.header("📂 카테고리 선택")
    selected_categories = []
    
    for category in CATEGORIES:
        if st.checkbox(category, value=True):
            selected_categories.append(category)
    
    st.session_state.selected_categories = selected_categories

# 메인 콘텐츠
st.header("🔄 뉴스 수집")

# REFRESH 버튼
if st.button("🔄 새로운 기사 로드", use_container_width=True, type="primary"):
    
    if not st.session_state.selected_categories:
        st.error("❌ 카테고리를 선택하세요")
    else:
        status_text = st.empty()
        
        try:
            # 1단계: 병렬 웹 크롤링
            status_text.text("🔗 웹사이트 병렬 크롤링 중... (최대 10개 동시 처리)")
            logger.info("병렬 크롤링 시작")
            
            crawler = WebCrawler()
            all_articles = crawler.crawl_all_websites(WEBSITES, max_workers=10)
            
            logger.info(f"총 {len(all_articles)}개 기사 수집")
            status_text.text(f"✅ {len(all_articles)}개 기사 수집 완료")
            
            # 2단계: 카테고리 필터링
            status_text.text("📂 카테고리 필터링 중...")
            filtered_articles = []
            
            for article in all_articles:
                # 선택된 카테고리와 겹치는지 확인
                if any(cat in article['categories'] for cat in st.session_state.selected_categories):
                    filtered_articles.append(article)
            
            logger.info(f"필터링 후 {len(filtered_articles)}개 기사")
            status_text.text(f"📂 {len(filtered_articles)}개 기사 필터링 완료")
            
            # 3단계: 중복 제거
            status_text.text("🔍 중복 제거 중...")
            unique_articles = []
            
            for article in filtered_articles:
                if not st.session_state.deduplicator.is_duplicate(article):
                    unique_articles.append(article)
                    st.session_state.deduplicator.save_article({
                        'title_en': article['title_en'],
                        'link': article['link'],
                        'source': article['source'],
                        'categories': ','.join(article['categories'])
                    })
            
            logger.info(f"중복 제거 후 {len(unique_articles)}개 기사")
            status_text.text(f"✅ {len(unique_articles)}개 새 기사 발견")
            
            # 4단계: 상위 10개만 선택
            top_articles = unique_articles[:10]
            
            st.session_state.articles = top_articles
            
            time.sleep(1)
            status_text.empty()
            
            st.success(f"✅ {len(top_articles)}개 기사 로드 완료!")
        
        except Exception as e:
            st.error(f"❌ 오류 발생: {str(e)}")
            logger.error(f"전체 오류: {str(e)}")

# 기사 표시
st.markdown("---")

if st.session_state.articles:
    st.header(f"📊 수집된 기사 ({len(st.session_state.articles)}개)")
    
    for idx, article in enumerate(st.session_state.articles, 1):
        with st.container():
            # 제목 (원문)
            st.subheader(article['title_en'])
            
            # 메타정보
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"📂 {article['categories'][0] if article['categories'] else 'N/A'}")
            with col2:
                st.caption(f"출처: {article['source']}")
            with col3:
                st.markdown(f"[🔗 원문]({article['link']})")
            
            st.divider()

else:
    st.info("🔄 '새로운 기사 로드' 버튼을 클릭하여 기사를 수집하세요")
