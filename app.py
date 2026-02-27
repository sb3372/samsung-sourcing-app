import streamlit as st
import time
import logging
from config import WEBSITES, CATEGORIES
from crawler import WebCrawler
from categorizer import Categorizer
from deduplicator import Deduplicator
from collections import defaultdict

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

if "cached_articles" not in st.session_state:
    st.session_state.cached_articles = []  # 크롤링 결과 캐시
if "displayed_articles" not in st.session_state:
    st.session_state.displayed_articles = []  # 표시할 기사
if "week_range" not in st.session_state:
    st.session_state.week_range = 1  # 1주일, 2주일, 3주일...
if "deduplicator" not in st.session_state:
    st.session_state.deduplicator = Deduplicator()

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

col1, col2 = st.columns([3, 1])

with col1:
    st.header("🔄 뉴스 수집")

with col2:
    if st.button("🔄 처음부터", use_container_width=True):
        st.session_state.cached_articles = []
        st.session_state.displayed_articles = []
        st.session_state.week_range = 1
        st.rerun()

# 크롤링 버튼
if st.button("📥 기사 로드", use_container_width=True, type="primary"):
    
    if "gemini_key" not in st.session_state:
        st.error("API 키를 입력하세요")
    elif not st.session_state.selected_categories:
        st.error("카테고리를 선택하세요")
    else:
        status = st.empty()
        
        try:
            status.text(f"🔗 {st.session_state.week_range}주일 기사 크롤링 중...")
            crawler = WebCrawler()
            all_articles = crawler.crawl_all_websites(WEBSITES, max_workers=10)
            status.text(f"✅ {len(all_articles)}개 기사 수집")
            time.sleep(0.5)
            
            # 캐시에 추가 (새 기사만)
            for article in all_articles:
                if not st.session_state.deduplicator.is_duplicate(article):
                    st.session_state.cached_articles.append(article)
            
            logger.info(f"캐시됨: {len(st.session_state.cached_articles)}개")
            status.text(f"✅ 캐시됨: {len(st.session_state.cached_articles)}개")
            time.sleep(0.5)
            
            # AI 분류
            status.text("🤖 AI 분류 중...")
            categorizer = Categorizer(st.session_state.gemini_key)
            
            categorized_articles = []
            for idx, article in enumerate(st.session_state.cached_articles):
                if 'categories' not in article or not article['categories']:
                    status.text(f"🤖 분류 중: {idx + 1}/{len(st.session_state.cached_articles)}")
                    ai_categories = categorizer.categorize_article(article['title_en'])
                    article['categories'] = ai_categories
                    time.sleep(0.2)
                
                categorized_articles.append(article)
            
            st.session_state.cached_articles = categorized_articles
            status.text("✅ 분류 완료")
            time.sleep(0.5)
            
            # 필터링 (선택한 카테고리만)
            status.text("📂 필터링 중...")
            filtered_articles = []
            for article in st.session_state.cached_articles:
                if any(cat in article.get('categories', []) for cat in st.session_state.selected_categories):
                    filtered_articles.append(article)
            
            status.text(f"✅ {len(filtered_articles)}개 기사 필터링")
            time.sleep(0.5)
            
            # 다양한 소스에서 10개 선택
            articles_by_source = defaultdict(list)
            for article in filtered_articles:
                articles_by_source[article['source']].append(article)
            
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
                
                if len(final_articles) < 10:
                    for source in list(articles_by_source.keys()):
                        source_index[source] = 0
            
            st.session_state.displayed_articles = final_articles[:10]
            
            # CSV 저장
            for article in st.session_state.displayed_articles:
                st.session_state.deduplicator.save_article({
                    'title_en': article['title_en'],
                    'link': article['link'],
                    'source': article['source'],
                    'categories': ','.join(article.get('categories', []))
                })
            
            status.empty()
            st.success(f"✅ {len(st.session_state.displayed_articles)}개 기사 준비 완료!")
            
            # 다음 주일 클릭 유도
            if len(st.session_state.cached_articles) < 50:
                st.info(f"💡 기사가 부족하면 '주일 확장' 버튼을 클릭하세요")
        
        except Exception as e:
            st.error(f"오류: {str(e)}")
            logger.error(f"오류: {str(e)}")

# 주일 확장 버튼
if st.button("📅 주일 확장 (더 많은 기사)", use_container_width=True):
    st.session_state.week_range += 1
    st.info(f"다음 조회는 {st.session_state.week_range}주일 범위로 진행됩니다")

st.divider()

# 기사 표시
if st.session_state.displayed_articles:
    st.subheader(f"📰 기사 ({len(st.session_state.displayed_articles)}개)")
    
    for idx, article in enumerate(st.session_state.displayed_articles, 1):
        st.markdown(f'<div class="article-title">{idx}. {article["title_en"]}</div>', unsafe_allow_html=True)
        
        meta_html = f'<div class="article-meta">'
        meta_html += f'<span class="article-source">{article["source"]}</span>'
        for cat in article.get('categories', []):
            meta_html += f'<span class="article-category">{cat}</span>'
        meta_html += '</div>'
        st.markdown(meta_html, unsafe_allow_html=True)
        
        st.markdown(f'[🔗 원문 읽기]({article["link"]})')
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

else:
    st.info("기사를 로드하려면 '기사 로드' 버튼을 클릭하세요")
