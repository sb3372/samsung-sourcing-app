import streamlit as st
import time
import logging
from config import WEBSITES, CATEGORIES
from crawler import WebCrawler
from categorizer import Categorizer
from deduplicator import Deduplicator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Samsung Electronics Europe IPC", page_icon="📱", layout="wide")

st.markdown("""
    <style>
    .article-title { font-size: 1.2rem; font-weight: 600; color: #1e88e5; margin-bottom: 0.5rem; }
    .article-meta { font-size: 0.9rem; color: #666; margin-bottom: 0.8rem; }
    .article-source { background: #e3f2fd; padding: 0.3rem 0.8rem; border-radius: 4px; display: inline-block; margin-right: 0.5rem; }
    .article-category { background: #1e88e5; color: white; padding: 0.3rem 0.8rem; border-radius: 4px; display: inline-block; margin-right: 0.5rem; font-size: 0.85rem; }
    .divider { margin: 1.5rem 0; border-top: 1px solid #eee; }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "all_articles" not in st.session_state:
    st.session_state.all_articles = []  # 크롤링 + 분류된 모든 기사
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
if "week_range" not in st.session_state:
    st.session_state.week_range = 1
if "deduplicator" not in st.session_state:
    st.session_state.deduplicator = Deduplicator()
if "last_crawled_week" not in st.session_state:
    st.session_state.last_crawled_week = 0

st.title("📱 Samsung Electronics Europe IPC")
st.markdown("유럽 기술 뉴스 - AI 카테고리 분류")
st.divider()

with st.sidebar:
    st.header("⚙️ 설정")
    
    api_key = st.text_input("🔑 Gemini API 키", type="password")
    if api_key:
        st.session_state.gemini_key = api_key
        st.success("API 연결됨")
    
    st.divider()
    
    st.subheader("카테고리 선택")
    selected_categories = []
    for category in CATEGORIES:
        if st.checkbox(category, value=True):
            selected_categories.append(category)
    
    st.session_state.selected_categories = selected_categories

# 상태 표시
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("전체 기사", len(st.session_state.all_articles))
with col2:
    st.metric("현재 페이지", st.session_state.current_page + 1)
with col3:
    st.metric("조회 범위", f"{st.session_state.week_range}주일")

st.divider()

# 크롤링 버튼
if st.button("📥 시작 (1주일)", use_container_width=True, type="primary"):
    if "gemini_key" not in st.session_state:
        st.error("API 키를 입력하세요")
    elif not st.session_state.selected_categories:
        st.error("카테고리를 선택하세요")
    else:
        # 새로운 주일 범위로 크롤링해야 할 때만
        if st.session_state.last_crawled_week != st.session_state.week_range:
            status = st.empty()
            
            try:
                # 1단계: 크롤링
                status.text(f"🔗 {st.session_state.week_range}주일 기사 크롤링 중...")
                crawler = WebCrawler()
                all_articles = crawler.crawl_all_websites(WEBSITES, max_workers=10)
                status.text(f"✅ {len(all_articles)}개 기사 수집")
                time.sleep(0.5)
                
                # 2단계: 중복 제거
                status.text("🔍 중복 제거 중...")
                unique_articles = []
                for article in all_articles:
                    if not st.session_state.deduplicator.is_duplicate(article):
                        unique_articles.append(article)
                status.text(f"✅ {len(unique_articles)}개 새 기사")
                time.sleep(0.5)
                
                # 3단계: AI 분류
                status.text("🤖 AI 분류 중...")
                categorizer = Categorizer(st.session_state.gemini_key)
                
                categorized_articles = []
                for idx, article in enumerate(unique_articles):
                    status.text(f"🤖 분류 중: {idx + 1}/{len(unique_articles)}")
                    ai_categories = categorizer.categorize_article(article['title_en'])
                    article['categories'] = ai_categories
                    categorized_articles.append(article)
                    time.sleep(0.1)
                
                status.text("✅ 분류 완료")
                time.sleep(0.5)
                
                # 4단계: 선택 카테고리 필터링
                status.text("📂 필터링 중...")
                filtered_articles = []
                for article in categorized_articles:
                    if any(cat in article.get('categories', []) for cat in st.session_state.selected_categories):
                        filtered_articles.append(article)
                
                status.text(f"✅ {len(filtered_articles)}개 기사 필터링")
                time.sleep(0.5)
                
                st.session_state.all_articles = filtered_articles
                st.session_state.current_page = 0
                st.session_state.last_crawled_week = st.session_state.week_range
                
                status.empty()
                st.success(f"✅ {len(filtered_articles)}개 기사 준비 완료!")
                st.rerun()
            
            except Exception as e:
                st.error(f"오류: {str(e)}")
                logger.error(f"오류: {str(e)}")

st.divider()

# 기사 표시 (10개씩)
if st.session_state.all_articles:
    start_idx = st.session_state.current_page * 10
    end_idx = start_idx + 10
    page_articles = st.session_state.all_articles[start_idx:end_idx]
    
    st.subheader(f"📰 기사 (페이지 {st.session_state.current_page + 1}/{(len(st.session_state.all_articles) + 9) // 10})")
    
    for idx, article in enumerate(page_articles, 1):
        st.markdown(f'<div class="article-title">{start_idx + idx}. {article["title_en"]}</div>', unsafe_allow_html=True)
        
        meta_html = f'<div class="article-meta">'
        meta_html += f'<span class="article-source">{article["source"]}</span>'
        for cat in article.get('categories', []):
            meta_html += f'<span class="article-category">{cat}</span>'
        meta_html += '</div>'
        st.markdown(meta_html, unsafe_allow_html=True)
        
        st.markdown(f'[🔗 원문 읽기]({article["link"]})')
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # CSV 저장
        st.session_state.deduplicator.save_article({
            'title_en': article['title_en'],
            'link': article['link'],
            'source': article['source'],
            'categories': ','.join(article.get('categories', []))
        })
    
    # 페이지네이션
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
        if end_idx >= len(st.session_state.all_articles) and st.session_state.week_range < 4:
            if st.button("📅 주일 확장", use_container_width=True):
                st.session_state.week_range += 1
                st.rerun()
    
    with col4:
        if st.button("🔄 처음부터", use_container_width=True):
            st.session_state.all_articles = []
            st.session_state.current_page = 0
            st.session_state.week_range = 1
            st.session_state.last_crawled_week = 0
            st.rerun()

else:
    st.info("📥 '시작 (1주일)' 버튼을 클릭하여 기사를 로드하세요")
