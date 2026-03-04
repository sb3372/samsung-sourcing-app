"""
Streamlit 메인 앱 - DB에서 즉시 로드
"""
import streamlit as st
import time
import logging
from config import CATEGORIES
import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Samsung Electronics Europe IPC", page_icon="📱", layout="wide")

st.markdown("""
    <style>
    .article-title { font-size: 1.3rem; font-weight: 600; color: #1e88e5; }
    .article-summary { font-size: 1rem; color: #333; line-height: 1.5; }
    .article-source { background: #e3f2fd; padding: 0.3rem 0.8rem; border-radius: 4px; display: inline-block; margin-right: 0.5rem; }
    .article-category { background: #1e88e5; color: white; padding: 0.3rem 0.8rem; border-radius: 4px; display: inline-block; margin-right: 0.5rem; }
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

# 로그인
if not st.session_state.user_id:
    st.subheader("🔑 로그인")
    
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("사용자 ID")
    with col2:
        api_key = st.text_input("Gemini API Key (선택)", type="password")
    
    if st.button("로그인", use_container_width=True, type="primary"):
        if user_id:
            db.get_or_create_user(user_id, api_key or "")
            st.session_state.user_id = user_id
            st.success(f"✅ {user_id}로 로그인했습니다!")
            st.rerun()
        else:
            st.error("❌ ID를 입력하세요")

else:
    # 로그아웃
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"👤 {st.session_state.user_id}")
    with col2:
        if st.button("로그아웃"):
            st.session_state.user_id = None
            st.rerun()
    
    st.divider()
    
    # 카테고리 선택
    with st.sidebar:
        st.subheader("📂 카테고리")
        selected_categories = []
        for cat in CATEGORIES:
            if st.checkbox(cat, value=True):
                selected_categories.append(cat)
    
    # "기사 로드" 버튼 - DB에서 즉시 로드
    if st.button("📥 기사 로드", use_container_width=True, type="primary"):
        if not selected_categories:
            st.error("❌ 카테고리를 선택하세요")
        else:
            # DB에서 기사 로드 (1초 안에)
            start = time.time()
            
            # DB에서 필터링해서 로드
            all_articles = db.get_cached_articles_filtered(
                selected_categories,
                limit=1000
            )
            
            # 사용자가 읽은 기사 제외
            filtered = [
                a for a in all_articles
                if not db.is_read_article(st.session_state.user_id, a['link'])
            ]
            
            st.session_state.all_articles = filtered
            st.session_state.current_page = 0
            
            elapsed = time.time() - start
            st.success(f"✅ {len(filtered)}개 기사 로드 완료 ({elapsed:.2f}초)")
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
            st.markdown(f"<div class='article-title'>{start_idx + idx}. {article['title']}</div>", unsafe_allow_html=True)
            
            meta = f"<div class='article-source'>📰 {article['source']}</div>"
            for cat in article.get('categories', []):
                meta += f"<div class='article-category'>📁 {cat}</div>"
            st.markdown(meta, unsafe_allow_html=True)
            
            st.markdown(f"<div class='article-summary'>{article.get('summary', '')}</div>", unsafe_allow_html=True)
            st.markdown(f"[🔗 원문]({article['link']})")
            
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
        st.info("📥 '기사 로드'를 클릭하세요")
