"""
Streamlit 메인 애플리케이션
Samsung Electronics Europe IPC - 유럽 기술 뉴스
"""
import streamlit as st
import time
import logging
from config import WEBSITES, CATEGORIES
from crawler import WebCrawler
from processor import DataProcessor
import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 페이지 설정
st.set_page_config(
    page_title="Samsung Electronics Europe IPC",
    page_icon="📱",
    layout="wide"
)

st.markdown("""
    <style>
    .article-title { font-size: 1.3rem; font-weight: 600; color: #1e88e5; margin-bottom: 0.5rem; }
    .article-meta { font-size: 0.9rem; color: #666; margin-bottom: 0.8rem; }
    .article-summary { font-size: 1rem; color: #333; margin-bottom: 1rem; line-height: 1.5; }
    .article-source { background: #e3f2fd; padding: 0.3rem 0.8rem; border-radius: 4px; display: inline-block; margin-right: 0.5rem; font-size: 0.85rem; }
    .article-company { background: #fff3e0; padding: 0.3rem 0.8rem; border-radius: 4px; display: inline-block; margin-right: 0.5rem; font-size: 0.85rem; }
    .article-category { background: #1e88e5; color: white; padding: 0.3rem 0.8rem; border-radius: 4px; display: inline-block; margin-right: 0.5rem; font-size: 0.85rem; }
    .divider { margin: 1.5rem 0; border-top: 1px solid #eee; }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "all_articles" not in st.session_state:
    st.session_state.all_articles = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
if "week_range" not in st.session_state:
    st.session_state.week_range = 1
if "selected_categories" not in st.session_state:
    st.session_state.selected_categories = CATEGORIES

# ============ 로그인 섹션 ============
st.title("📱 Samsung Electronics Europe IPC")
st.markdown("유럽 기술 뉴스 - AI 기반 분류")
st.divider()

if not st.session_state.user_id:
    st.subheader("🔑 로그인")
    
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("사용자 ID", placeholder="example@samsung.com")
    with col2:
        api_key = st.text_input("Gemini API Key", type="password", placeholder="API Key 입력")
    
    if st.button("로그인", use_container_width=True, type="primary"):
        if user_id and api_key:
            db.get_or_create_user(user_id, api_key)
            st.session_state.user_id = user_id
            st.session_state.api_key = api_key
            st.success(f"✅ {user_id}로 로그인했습니다!")
            st.rerun()
        else:
            st.error("❌ ID와 API Key를 입력하세요")

else:
    # ============ 로그아웃 & 설정 ============
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.write(f"👤 로그인: **{st.session_state.user_id}**")
    with col3:
        if st.button("로그아웃"):
            st.session_state.user_id = None
            st.session_state.api_key = None
            st.session_state.all_articles = []
            st.rerun()
    
    st.divider()
    
    # ============ 사이드바 ============
    with st.sidebar:
        st.header("⚙️ 설정")
        st.divider()
        
        st.subheader("📂 카테고리 선택")
        selected_categories = []
        for category in CATEGORIES:
            if st.checkbox(category, value=True):
                selected_categories.append(category)
        
        st.session_state.selected_categories = selected_categories
    
    # ============ 상태 표시 ============
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 기사", len(st.session_state.all_articles))
    with col2:
        st.metric("현재 페이지", st.session_state.current_page + 1)
    with col3:
        st.metric("조회 범위", f"{st.session_state.week_range}주일")
    with col4:
        st.metric("선택 카테고리", len(st.session_state.selected_categories))
    
    st.divider()
    
    # ============ 기사 로드 버튼 ============
    if st.button("📥 기사 로드", use_container_width=True, type="primary"):
        if not st.session_state.selected_categories:
            st.error("❌ 카테고리를 선택하세요")
        else:
            status = st.empty()
            progress_bar = st.progress(0)
            
            try:
                # 1단계: 크롤링
                status.text(f"🔗 {st.session_state.week_range}주일 기사 크롤링 중...")
                progress_bar.progress(10)
                
                crawler = WebCrawler()
                raw_articles = crawler.crawl_all_websites(WEBSITES, max_workers=10)
                
                status.text(f"✅ {len(raw_articles)}개 기사 수집")
                progress_bar.progress(30)
                time.sleep(1)
                
                # 2단계: AI 분류 & 필터링
                status.text(f"🤖 AI 분류 중... (이 과정은 시간이 걸릴 수 있습니다)")
                progress_bar.progress(40)
                
                processor = DataProcessor(st.session_state.api_key)
                processed_articles = processor.process_articles(
                    raw_articles,
                    st.session_state.user_id,
                    st.session_state.week_range
                )
                
                progress_bar.progress(70)
                time.sleep(1)
                
                # 3단계: 카테고리 필터링
                status.text(f"📂 카테고리 필터링 중...")
                filtered_articles = []
                for article in processed_articles:
                    # 선택한 카테고리와 겹치는지 확인
                    if any(cat in article['categories'] for cat in st.session_state.selected_categories):
                        filtered_articles.append(article)
                
                progress_bar.progress(90)
                time.sleep(1)
                
                # 결과 저장
                st.session_state.all_articles = filtered_articles
                st.session_state.current_page = 0
                
                progress_bar.progress(100)
                status.empty()
                progress_bar.empty()
                
                st.success(f"✅ {len(filtered_articles)}개 기사 준비 완료!")
                st.rerun()
            
            except Exception as e:
                st.error(f"❌ 오류 발생: {str(e)}")
                logger.error(f"오류: {str(e)}", exc_info=True)
    
    st.divider()
    
    # ============ 기사 표시 ============
    if st.session_state.all_articles:
        start_idx = st.session_state.current_page * 10
        end_idx = start_idx + 10
        page_articles = st.session_state.all_articles[start_idx:end_idx]
        
        total_pages = (len(st.session_state.all_articles) + 9) // 10
        st.subheader(f"📰 기사 (페이지 {st.session_state.current_page + 1}/{total_pages})")
        
        for idx, article in enumerate(page_articles, 1):
            # 제목
            st.markdown(f'<div class="article-title">{start_idx + idx}. {article["title"]}</div>', unsafe_allow_html=True)
            
            # 메타정보
            meta_html = f'<div class="article-meta">'
            meta_html += f'<span class="article-source">📰 {article["source"]}</span>'
            for company in article.get('companies', []):
                meta_html += f'<span class="article-company">🏢 {company}</span>'
            for cat in article.get('categories', []):
                meta_html += f'<span class="article-category">📁 {cat}</span>'
            meta_html += '</div>'
            st.markdown(meta_html, unsafe_allow_html=True)
            
            # 요약
            st.markdown(f'<div class="article-summary">{article.get("summary", "요약 없음")}</div>', unsafe_allow_html=True)
            
            # 링크
            st.markdown(f'[🔗 원문 읽기]({article["link"]})')
            
            # 기사를 읽음으로 표시
            db.mark_article_read(st.session_state.user_id, article["link"])
            
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # ============ 페이지네이션 ============
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.session_state.current_page > 0:
                if st.button("⬅️ 이전 페이지", use_container_width=True):
                    st.session_state.current_page -= 1
                    st.rerun()
        
        with col2:
            if end_idx < len(st.session_state.all_articles):
                if st.button("➡️ 다음 페이지", use_container_width=True):
                    st.session_state.current_page += 1
                    st.rerun()
        
        with col3:
            if end_idx >= len(st.session_state.all_articles) and st.session_state.week_range < 12:
                if st.button("📅 1주일 추가 로드", use_container_width=True):
                    st.session_state.week_range += 1
                    st.session_state.all_articles = []
                    st.session_state.current_page = 0
                    st.rerun()
        
        with col4:
            if st.button("🔄 처음부터", use_container_width=True):
                st.session_state.all_articles = []
                st.session_state.current_page = 0
                st.session_state.week_range = 1
                st.rerun()
    
    else:
        st.info("📥 '기사 로드' 버튼을 클릭하여 시작하세요")
