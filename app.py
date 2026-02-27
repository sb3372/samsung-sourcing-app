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

# 페이지 설정
st.set_page_config(
    page_title="Samsung Electronics Europe IPC",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 커스터마이징
st.markdown("""
    <style>
    /* 전체 배경 */
    .main {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    }
    
    /* 헤더 스타일 */
    .header-main {
        background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(30, 136, 229, 0.3);
        color: white;
    }
    
    .header-main h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: 1px;
    }
    
    .header-main p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* 카드 스타일 */
    .article-card {
        background: linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%);
        border-left: 5px solid #1e88e5;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .article-card:hover {
        box-shadow: 0 4px 20px rgba(30, 136, 229, 0.2);
        transform: translateX(5px);
    }
    
    .article-card h3 {
        margin: 0 0 1rem 0;
        color: #1565c0;
        font-size: 1.3rem;
        line-height: 1.5;
    }
    
    /* 카테고리 태그 */
    .category-tag {
        display: inline-block;
        background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%);
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
        font-weight: 500;
    }
    
    /* 소스 배지 */
    .source-badge {
        display: inline-block;
        background: #f0f0f0;
        color: #666;
        padding: 0.3rem 0.7rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    
    /* 링크 버튼 */
    .link-button {
        display: inline-block;
        background: #1e88e5;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        text-decoration: none;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }
    
    .link-button:hover {
        background: #1565c0;
        transform: scale(1.05);
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.8rem 2rem !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(30, 136, 229, 0.3) !important;
    }
    
    .stButton > button:hover {
        box-shadow: 0 6px 20px rgba(30, 136, 229, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    /* 사이드바 */
    .sidebar .sidebar-content {
        background: #f8f9fa;
    }
    
    /* 체크박스 */
    .stCheckbox {
        padding: 0.3rem 0;
    }
    
    /* 섹션 헤더 */
    .section-header {
        background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    /* 통계 정보 */
    .stat-info {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        color: #1565c0;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    /* 메타정보 */
    .article-meta {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin: 1rem 0;
        font-size: 0.9rem;
        color: #666;
    }
    
    /* 성공 메시지 */
    .success-message {
        background: #c8e6c9;
        color: #2e7d32;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2e7d32;
    }
    
    /* 에러 메시지 */
    .error-message {
        background: #ffcdd2;
        color: #c62828;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #c62828;
    }
    </style>
""", unsafe_allow_html=True)

if "articles" not in st.session_state:
    st.session_state.articles = []
if "deduplicator" not in st.session_state:
    st.session_state.deduplicator = Deduplicator()

# 헤더
st.markdown("""
    <div class="header-main">
        <h1>📱 Samsung Electronics Europe IPC</h1>
        <p>유럽 기술 뉴스 - AI 기반 카테고리 분류</p>
    </div>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    st.divider()
    
    # Gemini API 키
    st.markdown("#### 🔑 API 키")
    api_key = st.text_input(
        "Gemini API 키 입력",
        type="password",
        help="https://aistudio.google.com/app/apikey에서 발급받으세요",
        label_visibility="collapsed"
    )
    
    if api_key:
        st.session_state.gemini_key = api_key
        st.success("✅ API 연결 완료")
    else:
        st.info("ℹ️ API 키를 입력해주세요")
    
    st.divider()
    
    # 카테고리 선택
    st.markdown("#### 📂 카테고리 선택")
    st.markdown("<small>뉴스를 수집할 카테고리를 선택하세요</small>", unsafe_allow_html=True)
    
    selected_categories = []
    
    # 2개 열로 배치
    col1, col2 = st.columns(2)
    categories_list = CATEGORIES
    
    for idx, category in enumerate(categories_list):
        if idx % 2 == 0:
            with col1:
                if st.checkbox(category, value=True):
                    selected_categories.append(category)
        else:
            with col2:
                if st.checkbox(category, value=True):
                    selected_categories.append(category)
    
    st.session_state.selected_categories = selected_categories

# 메인 콘텐츠
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<div class="section-header">🔄 뉴스 수집</div>', unsafe_allow_html=True)

with col2:
    refresh_button = st.button("🔄 새로운 기사 로드", use_container_width=True)

if refresh_button:
    
    if "gemini_key" not in st.session_state:
        st.error("❌ API 키를 먼저 입력하세요")
    elif not st.session_state.selected_categories:
        st.error("❌ 카테고리를 선택하세요")
    else:
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        try:
            # 1단계: 병렬 웹 크롤링
            status_placeholder.info("🔗 웹사이트 병렬 크롤링 중... (최대 10개 동시 처리)")
            progress_bar.progress(10)
            
            crawler = WebCrawler()
            all_articles = crawler.crawl_all_websites(WEBSITES, max_workers=10)
            
            logger.info(f"총 {len(all_articles)}개 기사 수집")
            status_placeholder.info(f"✅ {len(all_articles)}개 기사 수집 완료")
            progress_bar.progress(25)
            time.sleep(0.5)
            
            # 2단계: 중복 제거
            status_placeholder.info("🔍 중복 제거 중...")
            unique_articles = []
            
            for article in all_articles:
                if not st.session_state.deduplicator.is_duplicate(article):
                    unique_articles.append(article)
            
            logger.info(f"중복 제거 후 {len(unique_articles)}개 기사")
            status_placeholder.info(f"✅ {len(unique_articles)}개 새 기사 발견")
            progress_bar.progress(40)
            time.sleep(0.5)
            
            # 3단계: AI로 카테고리 분류
            status_placeholder.info("🤖 AI 카테고리 분류 중...")
            categorizer = Categorizer(st.session_state.gemini_key)
            
            categorized_articles = []
            for idx, article in enumerate(unique_articles):
                progress = 40 + int((idx / len(unique_articles)) * 25)
                progress_bar.progress(progress)
                
                # AI로 카테고리 분류
                ai_categories = categorizer.categorize_article(article['title_en'])
                article['categories'] = ai_categories
                categorized_articles.append(article)
                
                time.sleep(0.3)
            
            logger.info(f"카테고리 분류 완료")
            status_placeholder.info(f"✅ 카테고리 분류 완료")
            progress_bar.progress(65)
            time.sleep(0.5)
            
            # 4단계: 선택된 카테고리로 필터링
            status_placeholder.info("📂 카테고리 필터링 중...")
            filtered_articles = []
            
            for article in categorized_articles:
                if any(cat in article['categories'] for cat in st.session_state.selected_categories):
                    filtered_articles.append(article)
            
            logger.info(f"필터링 후 {len(filtered_articles)}개 기사")
            status_placeholder.info(f"📂 {len(filtered_articles)}개 기사 필터링 완료")
            progress_bar.progress(80)
            time.sleep(0.5)
            
            # 5단계: 다양한 소스에서 10개 선택
            status_placeholder.info("🎯 다양한 소스에서 기사 선택 중...")
            
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
            
            # 기사를 CSV에 저장
            for article in top_articles:
                st.session_state.deduplicator.save_article({
                    'title_en': article['title_en'],
                    'link': article['link'],
                    'source': article['source'],
                    'categories': ','.join(article['categories'])
                })
            
            st.session_state.articles = top_articles
            
            progress_bar.progress(100)
            time.sleep(0.5)
            status_placeholder.empty()
            progress_bar.empty()
            
            st.markdown(f"""
                <div class="success-message">
                    ✅ {len(top_articles)}개 기사 로드 완료!
                </div>
            """, unsafe_allow_html=True)
        
        except Exception as e:
            st.markdown(f"""
                <div class="error-message">
                    ❌ 오류 발생: {str(e)[:100]}
                </div>
            """, unsafe_allow_html=True)
            logger.error(f"전체 오류: {str(e)}")

# 기사 표시
st.divider()

if st.session_state.articles:
    st.markdown(f"""
        <div class="stat-info">
            📊 수집된 기사 ({len(st.session_state.articles)}개)
        </div>
    """, unsafe_allow_html=True)
    
    for idx, article in enumerate(st.session_state.articles, 1):
        st.markdown(f"""
            <div class="article-card">
                <h3>#{idx} {article['title_en']}</h3>
                <div class="article-meta">
                    <span class="source-badge">📰 {article['source']}</span>
                    <span class="category-tag">📂 {', '.join(article['categories'])}</span>
                </div>
                <a href="{article['link']}" target="_blank" class="link-button">🔗 원문 읽기</a>
            </div>
        """, unsafe_allow_html=True)

else:
    st.markdown("""
        <div style="background: #f0f4ff; padding: 2rem; border-radius: 10px; text-align: center;">
            <h3 style="color: #1565c0;">🔄 기사를 아직 로드하지 않았습니다</h3>
            <p style="color: #666;">위의 "새로운 기사 로드" 버튼을 클릭하여 시작하세요</p>
        </div>
    """, unsafe_allow_html=True)
