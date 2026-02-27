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

st.set_page_config(page_title="Samsung Electronics Europe IPC", page_icon="📱", layout="wide")

# 간단한 스타일
st.markdown("""
    <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .article-title { font-size: 1.2rem; font-weight: 600; color: #1e88e5; margin-bottom: 0.5rem; }
    .article-meta { font-size: 0.9rem; color: #666; margin-bottom: 0.8rem; }
    .article-source { background: #e3f2fd; padding: 0.3rem 0.8rem; border-radius: 4px; display: inline-block; margin-right: 0.5rem; }
    .article-category { background: #1e88e5; color: white; padding: 0.3rem 0.8rem; border-radius: 4px; display: inline-block; margin-right: 0.5rem; font-size: 0.85rem; }
    .divider { margin: 1.5rem 0; border-top: 1px solid #eee; }
    </style>
""", unsafe_allow_html=True)

if "articles" not in st.session_state:
    st.session_state.articles = []
if "deduplicator" not in st.session_state:
    st.session_state.deduplicator = Deduplicator()

# 타이틀
st.title("📱 Samsung Electronics Europe IPC")
st.markdown("유럽 기술 뉴스 - AI 기반 카테고리 분류")
st.divider()

# 사이드바 - 설정만
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

# 메인 - 버튼만
if st.button("🔄 기사 로드", use_container_width=True, type="primary"):
    
    if "gemini_key" not in st.session_state:
        st.error("API 키를 입력하세요")
    elif not st.session_state.selected_categories:
        st.error("카테고리를 선택하세요")
    else:
        status = st.empty()
        
        try:
            # 크롤링
            status.text("🔗 웹사이트 크롤링 중...")
            crawler = WebCrawler()
            all_articles = crawler.crawl_all_websites(WEBSITES, max_workers=10)
            status.text(f"✅ {len(all_articles)}개 기사 수집")
            time.sleep(0.5)
            
            # 중복 제거
            status.text("🔍 중복 제거 중...")
            unique_articles = []
            for article in all_articles:
                if not st.session_state.deduplicator.is_duplicate(article):
                    unique_articles.append(article)
            status.text(f"✅ {len(unique_articles)}개 새 기사")
            time.sleep(0.5)
            
            # AI 분류
            status.text("🤖 AI 분류 중...")
            categorizer = Categorizer(st.session_state.gemini_key)
            categorized_articles = []
            for idx, article in enumerate(unique_articles):
                status.text(f"🤖 분류 중: {idx + 1}/{len(unique_articles)}")
                ai_categories = categorizer.categorize_article(article['title_en'])
                article['categories'] = ai_categories
                categorized_articles.append(article)
                time.sleep(0.2)
            status.text("✅ 분류 완료")
            time.sleep(0.5)
            
            # 필터링
            status.text("📂 필터링 중...")
            filtered_articles = []
            for article in categorized_articles:
                if any(cat in article['categories'] for cat in st.session_state.selected_categories):
                    filtered_articles.append(article)
            status.text(f"✅ {len(filtered_articles)}개 기사 필터링")
            time.sleep(0.5)
            
            # 다양한 소스에서 10개 선택
            status.text("🎯 기사 선택 중...")
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
                        if len(final_articles) >= 10:
                            break
                        source_index[source] = 0
            
            top_articles = final_articles[:10]
            
            # CSV 저장
            for article in top_articles:
                st.session_state.deduplicator.save_article({
                    'title_en': article['title_en'],
                    'link': article['link'],
                    'source': article['source'],
                    'categories': ','.join(article['categories'])
                })
            
            st.session_state.articles = top_articles
            status.empty()
            st.success(f"✅ {len(top_articles)}개 기사 로드 완료!")
        
        except Exception as e:
            st.error(f"오류: {str(e)}")
            logger.error(f"오류: {str(e)}")

# 기사 표시
st.divider()

if st.session_state.articles:
    st.subheader(f"📰 기사 ({len(st.session_state.articles)}개)")
    
    for idx, article in enumerate(st.session_state.articles, 1):
        st.markdown(f'<div class="article-title">{idx}. {article["title_en"]}</div>', unsafe_allow_html=True)
        
        meta_html = f'<div class="article-meta">'
        meta_html += f'<span class="article-source">{article["source"]}</span>'
        for cat in article['categories']:
            meta_html += f'<span class="article-category">{cat}</span>'
        meta_html += '</div>'
        st.markdown(meta_html, unsafe_allow_html=True)
        
        st.markdown(f'[🔗 원문 읽기]({article["link"]})')
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

else:
    st.info("기사를 로드하려면 '기사 로드' 버튼을 클릭하세요")
