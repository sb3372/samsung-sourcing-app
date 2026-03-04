"""
Streamlit 웹 앱
- DB에서만 기사 로드 (1초)
- 크롤링은 scheduler.py가 백그라운드에서 함
"""
import streamlit as st
import time
import logging
from config import CATEGORIES, WEBSITES
from crawler import WebCrawler
from ai import AIProcessor
import db
import os

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

st.title("📱 Samsung Electronics Europe IPC")
st.markdown("유럽 기술 뉴스 - AI 기반 분류")
st.divider()

# ============ 관리자: DB 초기화 + 크롤링 ============
with st.expander("🔧 관리자: DB 초기화 (첫 실행만)", expanded=False):
    st.warning("⚠️ 첫 실행 시에만 이 버튼을 클릭하세요")
    
    if st.button("🔄 DB 초기화 + 기사 크롤링", use_container_width=True, type="primary"):
        status = st.empty()
        progress = st.progress(0)
        
        try:
            # Step 1: DB 초기화
            status.text("1️⃣ DB 초기화 중...")
            progress.progress(5)
            db.init_db()
            time.sleep(1)
            
            # Step 2: 크롤링
            status.text("2️⃣ 50개 사이트에서 기사 크롤링 중... (5-10분 소요)")
            progress.progress(10)
            
            crawler = WebCrawler()
            articles = crawler.crawl_all_websites_optimized(WEBSITES, max_workers=10)
            logger.info(f"✅ {len(articles)}개 기사 수집")
            
            if not articles:
                st.error("❌ 크롤링 실패")
                progress.progress(0)
            else:
                progress.progress(40)
                
                # Step 3: AI 분류
                api_key = os.getenv('GEMINI_API_KEY')
                
                if not api_key:
                    status.text("3️⃣ 기본값으로 저장 중... (GEMINI_API_KEY 없음)")
                    progress.progress(70)
                    
                    for article in articles:
                        article['categories'] = ['반도체']
                        article['summary'] = article.get('content', '')[:200]
                        article['companies'] = []
                        article['is_europe_relevant'] = True
                    
                    db.batch_insert_articles(articles, week_range=1)
                    progress.progress(95)
                
                else:
                    status.text("3️⃣ AI로 기사 분류 중... (병렬 처리)")
                    progress.progress(60)
                    
                    ai = AIProcessor(api_key)
                    processed = ai.process_articles_parallel(articles, max_workers=5)
                    
                    valid_articles = [a for a in processed if a.get('is_europe_relevant')]
                    logger.info(f"✅ {len(valid_articles)}개 기사 분류")
                    
                    status.text("4️⃣ DB에 저장 중...")
                    progress.progress(80)
                    
                    db.batch_insert_articles(valid_articles, week_range=1)
                    progress.progress(95)
                
                time.sleep(1)
                status.text("5️⃣ 완료!")
                progress.progress(100)
                
                st.success(f"✅ {len(articles)}개 기사 DB에 저장 완료!")
                st.info("📥 이제 아래에서 '기사 로드'를 클릭하세요")
        
        except Exception as e:
            st.error(f"❌ 오류: {str(e)}")
            logger.error(f"오류: {str(e)}", exc_info=True)
        
        finally:
            progress.progress(0)
            status.empty()

st.divider()

# ============ 로그인 ============
if not st.session_state.user_id:
    st.subheader("🔑 로그인")
    
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("사용자 ID", placeholder="example@samsung.com")
    with col2:
        api_key = st.text_input("Gemini API Key (선택)", type="password")
    
    if st.button("로그인", use_container_width=True, type="primary"):
        if user_id and user_id.strip():
            db.get_or_create_user(user_id.strip(), api_key or "")
            st.session_state.user_id = user_id.strip()
            st.success(f"✅ {user_id}로 로그인했습니다!")
            st.rerun()
        else:
            st.error("❌ ID를 입력하세요")

# ============ 로그인 후 ============
else:
    # 로그아웃
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"👤 **{st.session_state.user_id}**")
    with col2:
        if st.button("로그아웃"):
            st.session_state.user_id = None
            st.session_state.all_articles = []
            st.rerun()
    
    st.divider()
    
    # 카테고리 선택
    with st.sidebar:
        st.subheader("📂 카테고리 선택")
        selected_categories = []
        for cat in CATEGORIES:
            if st.checkbox(cat, value=True):
                selected_categories.append(cat)
    
    # 기사 로드 버튼
    if st.button("📥 기사 로드", use_container_width=True, type="primary"):
        if not selected_categories:
            st.error("❌ 카테고리를 선택하세요")
        else:
            start = time.time()
            
            # DB에서 로드 (1초 안에)
            all_articles = db.get_cached_articles_filtered(selected_categories, limit=1000)
            
            # 사용자가 읽은 기사 제외
            filtered = [
                a for a in all_articles
                if not db.is_read_article(st.session_state.user_id, a['link'])
            ]
            
            st.session_state.all_articles = filtered
            st.session_state.current_page = 0
            
            elapsed = time.time() - start
            
            if filtered:
                st.success(f"✅ {len(filtered)}개 기사 로드 완료 ({elapsed:.2f}초)")
            else:
                st.info("ℹ️ 해당 카테고리의 기사가 없습니다")
            
            st.rerun()
    
    st.divider()
    
    # 기사 표시
    if st.session_state.all_articles:
        start_idx = st.session_state.current_page * 10
        end_idx = start_idx + 10
        page_articles = st.session_state.all_articles[start_idx:end_idx]
        
        total_pages = (len(st.session_state.all_articles) + 9) // 10
        st.subheader(f"📰 기사 (페이지 {st.session_state.current_page + 1}/{total_pages})")
        
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
                if st.button("⬅️ 이전 페이지"):
                    st.session_state.current_page -= 1
                    st.rerun()
        
        with col2:
            if end_idx < len(st.session_state.all_articles):
                if st.button("다음 페이지 ➡️"):
                    st.session_state.current_page += 1
                    st.rerun()
    
    else:
        st.info("📥 '기사 로드' 버튼을 클릭하세요")
