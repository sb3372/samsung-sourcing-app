"""
Streamlit 웹 앱
- 로그인 → 자동으로 기사 표시
- DB 초기화 + 크롤링 자동 진행
"""
import streamlit as st
import time
import logging
from config import CATEGORIES, WEBSITES
from crawler import WebCrawler
from ai import AIProcessor
import db
import os
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Samsung Electronics Europe IPC", page_icon="📱", layout="wide")

st.markdown("""
    <style>
    .article-title { font-size: 1.3rem; font-weight: 600; color: #1e88e5; margin-bottom: 0.5rem; }
    .article-summary { font-size: 1rem; color: #333; line-height: 1.5; margin-bottom: 1rem; }
    .article-source { background: #e3f2fd; padding: 0.3rem 0.8rem; border-radius: 4px; display: inline-block; margin-right: 0.5rem; font-size: 0.85rem; }
    .article-category { background: #1e88e5; color: white; padding: 0.3rem 0.8rem; border-radius: 4px; display: inline-block; margin-right: 0.5rem; font-size: 0.85rem; }
    .divider { margin: 1.5rem 0; border-top: 1px solid #eee; }
    </style>
""", unsafe_allow_html=True)

# 세션 초기화
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "all_articles" not in st.session_state:
    st.session_state.all_articles = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
if "db_initialized" not in st.session_state:
    st.session_state.db_initialized = False

st.title("📱 Samsung Electronics Europe IPC")
st.markdown("유럽 기술 뉴스 - AI 기반 분류")
st.divider()

# ============ DB 초기화 + 크롤링 (자동) ============
def initialize_db_and_crawl():
    """DB 초기화 + 크롤링 한 번에 진행"""
    
    # DB 파일 확인
    try:
        conn = sqlite3.connect("samsung_news.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cached_articles")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            logger.info(f"✅ DB에 이미 {count}개 기사 있음")
            return True
    except:
        pass
    
    # DB 초기화
    logger.info("🔧 DB 초기화 중...")
    db.init_db()
    
    # 크롤링
    logger.info("🔗 크롤링 시작...")
    crawler = WebCrawler()
    articles = crawler.crawl_all_websites_optimized(WEBSITES, max_workers=10)
    logger.info(f"✅ {len(articles)}개 기사 수집")
    
    if not articles:
        logger.error("❌ 크롤링 실패")
        return False
    
    # AI 분류
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        logger.warning("⚠️ GEMINI_API_KEY 없음 - 기본값으로 저장")
        for article in articles:
            article['categories'] = ['반도체']
            article['summary'] = article.get('content', '')[:200]
            article['companies'] = []
            article['is_europe_relevant'] = True
    else:
        logger.info("🤖 AI 분류 중...")
        ai = AIProcessor(api_key)
        processed = ai.process_articles_parallel(articles, max_workers=5)
        articles = [a for a in processed if a.get('is_europe_relevant')]
    
    # DB 저장
    logger.info("💾 DB에 저장 중...")
    db.batch_insert_articles(articles, week_range=1)
    logger.info(f"✅ {len(articles)}개 기사 저장 완료")
    
    return True

# ============ 로그인 ============
if not st.session_state.user_id:
    st.subheader("🔑 로그인")
    
    user_id = st.text_input("사용자 ID", placeholder="example@samsung.com")
    
    if st.button("로그인", use_container_width=True, type="primary"):
        if user_id and user_id.strip():
            db.get_or_create_user(user_id.strip(), "")
            st.session_state.user_id = user_id.strip()
            st.success(f"✅ {user_id}로 로그인했습니다!")
            st.rerun()
        else:
            st.error("❌ ID를 입력하세요")

# ============ 로그인 후: 기사 표시 ============
else:
    # 로그아웃
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"👤 **{st.session_state.user_id}**")
    with col2:
        if st.button("로그아웃"):
            st.session_state.user_id = None
            st.session_state.all_articles = []
            st.session_state.current_page = 0
            st.rerun()
    
    st.divider()
    
    # DB 초기화 + 크롤링 (1회만)
    if not st.session_state.db_initialized:
        with st.spinner("⏳ DB 초기화 + 기사 로딩 중... (처음 1회만 시간이 걸립니다)"):
            success = initialize_db_and_crawl()
            st.session_state.db_initialized = True
        
        if success:
            st.rerun()
        else:
            st.error("❌ DB 초기화 실패")
    
    # 기사 로드
    if not st.session_state.all_articles:
        all_articles = db.get_cached_articles_filtered(CATEGORIES, limit=1000)
        filtered = [
            a for a in all_articles
            if not db.is_read_article(st.session_state.user_id, a['link'])
        ]
        st.session_state.all_articles = filtered
    
    # 기사 표시
    if st.session_state.all_articles:
        start_idx = st.session_state.current_page * 10
        end_idx = start_idx + 10
        page_articles = st.session_state.all_articles[start_idx:end_idx]
        
        total_pages = (len(st.session_state.all_articles) + 9) // 10
        st.subheader(f"📰 기사 (페이지 {st.session_state.current_page + 1}/{total_pages}) - 총 {len(st.session_state.all_articles)}개")
        
        for idx, article in enumerate(page_articles, 1):
            # 제목
            st.markdown(
                f"<div class='article-title'>{start_idx + idx}. {article.get('title', 'N/A')}</div>",
                unsafe_allow_html=True
            )
            
            # 메타정보
            meta_html = f"<div class='article-source'>📰 {article.get('source', 'N/A')}</div>"
            for cat in article.get('categories', []):
                if cat.strip():
                    meta_html += f"<div class='article-category'>📁 {cat.strip()}</div>"
            st.markdown(meta_html, unsafe_allow_html=True)
            
            # 요약
            st.markdown(
                f"<div class='article-summary'>{article.get('summary', '요약 없음')}</div>",
                unsafe_allow_html=True
            )
            
            # 링크
            st.markdown(f"[🔗 원문 읽기]({article.get('link', '#')})")
            
            # 읽음 표시
            db.mark_article_read(st.session_state.user_id, article['link'])
            
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # 페이지네이션
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.current_page > 0:
                if st.button("⬅️ 이전"):
                    st.session_state.current_page -= 1
                    st.rerun()
        
        with col2:
            if end_idx < len(st.session_state.all_articles):
                if st.button("다음 ➡️"):
                    st.session_state.current_page += 1
                    st.rerun()
    
    else:
        st.info("📥 기사를 로딩 중입니다...")
