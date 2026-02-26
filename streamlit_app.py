import streamlit as st
from tavily import TavilyClient
from datetime import datetime, timedelta
import os
import json
import hashlib
from collections import defaultdict
import re

# ===== PAGE CONFIGURATION =====
st.set_page_config(
    page_title="Samsung Strategic Sourcing Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CUSTOM CSS FOR BETTER DESIGN =====
st.markdown("""
<style>
    :root {
        --samsung-blue: #1428a0;
        --samsung-accent: #0066ff;
        --dark-bg: #0f1419;
        --card-bg: #1a1f2e;
        --text-primary: #ffffff;
        --text-secondary: #b0b8c1;
        --success-color: #10b981;
        --warning-color: #f59e0b;
    }
    
    .main {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%);
    }
    
    .header-container {
        background: linear-gradient(90deg, #1428a0 0%, #0066ff 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(20, 40, 160, 0.3);
    }
    
    .header-container h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .header-container p {
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #1428a0 0%, #0066ff 100%);
        color: white;
        border: none;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        border-radius: 6px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        box-shadow: 0 4px 12px rgba(0, 102, 255, 0.4);
    }
    
    [data-testid="stSidebar"] {
        background: #1a1f2e;
    }
    
    [data-testid="metric-container"] {
        background: #1a1f2e;
        border-left: 3px solid #0066ff;
    }
    
    a {
        color: #0066ff !important;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    hr {
        border: none;
        border-top: 1px solid rgba(0, 102, 255, 0.2);
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ===== CONFIGURATION =====
LANGUAGES = {
    "English": "en",
    "German": "de",
    "French": "fr",
    "Spanish": "es",
    "Italian": "it",
    "Polish": "pl",
    "Dutch": "nl",
    "Danish": "da",
    "Norwegian": "no",
    "Swedish": "sv"
}

CATEGORIES = {
    "조달 및 소재": {
        "emoji": "💰",
        "queries": {
            "en": "semiconductor price volatility Europe 2024 2025",
            "de": "Halbleiter Preise Europa",
            "fr": "prix semiconducteur Europe",
            "es": "precios semiconductores Europa",
            "it": "prezzi semiconduttori Europa",
            "pl": "ceny półprzewodników Europa",
            "nl": "prijzen semiconductors Europa",
            "da": "priser halvledere Europa",
            "no": "priser halvledere Europa",
            "sv": "priser halvledare Europa"
        },
    },
    "공급망 및 물류": {
        "emoji": "🚢",
        "queries": {
            "en": "logistics disruption Europe port strikes 2024",
            "de": "Logistik Störungen Europa Hafenstreiks",
            "fr": "perturbations logistiques Europe grèves portuaires",
            "es": "disrupciones logísticas Europa huelgas portuarias",
            "it": "interruzioni logistiche Europa scioperi portuali",
            "pl": "zakłócenia logistyczne Europa strajki portowe",
            "nl": "logistieke verstoringen Europa havenstakingen",
            "da": "logistiske forstyrrelser Europa havnestrejker",
            "no": "logistiske forstyrrelser Europa havnestreiker",
            "sv": "logistiska störningar Europa hamnstrejker"
        },
    },
    "EU 규제 및 준수": {
        "emoji": "⚖️",
        "queries": {
            "en": "EU AI Act CRA regulation electronics 2024",
            "de": "EU KI Gesetz CRA Verordnung Elektronik",
            "fr": "Loi IA UE CRA règlement électronique",
            "es": "Ley IA UE CRA reglamento electrónico",
            "it": "Legge IA UE CRA regolamento elettronico",
            "pl": "Ustawa AI UE CRA regulacja elektronika",
            "nl": "EU AI wet CRA regelgeving elektronica",
            "da": "EU AI lov CRA regulering elektronik",
            "no": "EU AI lov CRA regulering elektronikk",
            "sv": "EU AI lag CRA regulering elektronik"
        },
    },
    "혁신 및 생태계": {
        "emoji": "🚀",
        "queries": {
            "en": "European startups 6G robotics AI innovation 2024",
            "de": "Europäische Startups 6G Robotik AI Innovation",
            "fr": "startups européens 6G robotique IA innovation",
            "es": "startups europeos 6G robótica IA innovación",
            "it": "startup europei 6G robotica IA innovazione",
            "pl": "startupy europejskie 6G robotyka AI innowacja",
            "nl": "Europese startups 6G robotica AI innovatie",
            "da": "Europæiske startups 6G robotik AI innovation",
            "no": "Europeiske startups 6G robotikk AI innovasjon",
            "sv": "Europeiska startups 6G robotik AI innovation"
        },
    },
    "Samsung 포트폴리오": {
        "emoji": "📱",
        "queries": {
            "en": "Samsung Europe technology innovation 2024 2025",
            "de": "Samsung Europa Technologie Innovation",
            "fr": "Samsung Europe technologie innovation",
            "es": "Samsung Europa tecnología innovación",
            "it": "Samsung Europa tecnologia innovazione",
            "pl": "Samsung Europa technologia innowacja",
            "nl": "Samsung Europa technologie innovatie",
            "da": "Samsung Europa teknologi innovation",
            "no": "Samsung Europa teknologi innovasjon",
            "sv": "Samsung Europa teknik innovation"
        },
    }
}

MAX_ARTICLE_AGE_DAYS = 7
MAX_SEARCH_AGE_DAYS = 30
MAX_TOTAL_ARTICLES = 10
MAX_PER_CATEGORY = 2

# ===== FILE MANAGEMENT =====
HISTORY_FILE = "article_history.json"

def load_history():
    """Load article history with metadata"""
    if not os.path.exists(HISTORY_FILE):
        return {
            "articles": {},
            "content_hashes": set(),
            "last_updated": None
        }
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["content_hashes"] = set(data.get("content_hashes", []))
            return data
    except:
        return {"articles": {}, "content_hashes": set(), "last_updated": None}

def save_history(history):
    """Save article history with metadata"""
    save_data = history.copy()
    save_data["content_hashes"] = list(history["content_hashes"])
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

def get_content_hash(title, content):
    """Generate hash of article content for deduplication"""
    text = f"{title}{content}".lower()
    text = re.sub(r'\s+', ' ', text)
    return hashlib.md5(text.encode()).hexdigest()

def is_duplicate(title, content, history):
    """Check if article is duplicate based on content hash"""
    content_hash = get_content_hash(title, content)
    return content_hash in history["content_hashes"]

def add_to_history(url, title, content, category, language):
    """Add article to history"""
    history = load_history()
    content_hash = get_content_hash(title, content)
    
    history["articles"][url] = {
        "title": title,
        "category": category,
        "language": language,
        "date_added": datetime.now().isoformat(),
        "content_preview": content[:300]
    }
    history["content_hashes"].add(content_hash)
    history["last_updated"] = datetime.now().isoformat()
    
    save_history(history)

# ===== FREE TRANSLATION USING GOOGLE TRANSLATE =====
@st.cache_data
def translate_to_korean_cached(text):
    """Translate text to Korean with caching"""
    try:
        from google_trans_new import google_translator
        translator = google_translator()
        result = translator.translate(text, lang_src='en', lang_tgt='ko')
        return result
    except Exception as e:
        return text

# ===== SMART CONTENT SUMMARIZATION =====
def smart_summarize_content(title, content):
    """
    Intelligently summarize content by:
    1. Cleaning and processing text
    2. Finding main sentences with important information
    3. Extracting exactly 3 meaningful summary points
    """
    
    # Clean content
    content = content.replace('\n', ' ').replace('\r', ' ')
    content = re.sub(r'\s+', ' ', content).strip()
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15 and len(s.strip()) < 300]
    
    if not sentences:
        return [
            "기사 내용을 상세히 읽기 위해 전체 기사 링크를 참고하세요.",
            "주요 정보 및 통계는 원문에서 확인할 수 있습니다.",
            "더 자세한 내용은 출처 기사를 통해 확인하시기 바랍니다."
        ]
    
    # Score sentences based on keywords
    def score_sentence(sent):
        score = 0
        # Prefer sentences with numbers
        if re.search(r'\d+', sent):
            score += 3
        # Prefer longer sentences with more info
        if len(sent.split()) > 8:
            score += 2
        # Prefer sentences with important keywords
        keywords = ['growth', 'increase', 'decrease', 'change', 'innovation', 'technology', 'market', 'price', 'supply', 'demand', 'new', 'launch', 'partnership', 'agreement']
        for keyword in keywords:
            if keyword.lower() in sent.lower():
                score += 1
        return score
    
    # Score all sentences
    scored_sentences = [(sent, score_sentence(sent)) for sent in sentences]
    scored_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)
    
    # Get top 3 unique sentences, maintain order from original
    top_3 = scored_sentences[:3]
    
    # Sort back to original order
    top_3_dict = {sent: idx for idx, (sent, _) in enumerate(scored_sentences[:3])}
    final_sentences = []
    for idx, sent in enumerate(sentences):
        if sent in top_3_dict:
            final_sentences.append(sent)
        if len(final_sentences) == 3:
            break
    
    # Fallback if we couldn't get 3
    if len(final_sentences) < 3:
        final_sentences = [sent for sent, _ in top_3[:3]]
    
    return final_sentences[:3]

# ===== MULTI-LANGUAGE SEARCH =====
def perform_multilingual_search(category_config, category_name, tavily_client, history, max_results=3, debug_info=None):
    """Perform searches across multiple languages"""
    
    all_results = []
    seen_urls = set()
    search_attempts = []
    
    for lang_name, lang_code in LANGUAGES.items():
        if len(all_results) >= MAX_PER_CATEGORY:
            break
            
        query = category_config["queries"].get(lang_code, category_config["queries"]["en"])
        
        try:
            results = tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_raw_content=True
            )
            
            search_attempts.append({
                "language": lang_name,
                "query": query,
                "results_count": len(results.get('results', []))
            })
            
            for res in results.get('results', []):
                if len(all_results) >= MAX_PER_CATEGORY:
                    break
                    
                url = res.get('url')
                title = res.get('title', 'No title')
                content = res.get('content', '')
                
                if url in seen_urls or url in history["articles"]:
                    continue
                
                if len(content) < 50:
                    continue
                
                if is_duplicate(title, content, history):
                    continue
                
                seen_urls.add(url)
                
                all_results.append({
                    "url": url,
                    "title": title,
                    "content": content,
                    "language": lang_name,
                    "lang_code": lang_code,
                    "raw_content": res.get('raw_content', content)[:500]
                })
        
        except Exception as e:
            search_attempts.append({
                "language": lang_name,
                "query": query,
                "error": str(e)
            })
    
    if debug_info is not None:
        debug_info.append({
            "category": category_name,
            "total_results": len(all_results),
            "search_attempts": search_attempts
        })
    
    return all_results

# ===== MAIN UI =====
st.markdown("""
<div class="header-container">
    <h1>🛡️ Samsung 유럽 조달 센터 전략 인텔리전스</h1>
    <p>전략 정보 대시보드 • 일일 자동화 리포트</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("⚙️ 설정")
tavily_key = st.sidebar.text_input("Tavily API Key", type="password", help="Tavily API 키 입력")

# 디버그 모드
debug_mode = st.sidebar.checkbox("🐛 디버그 모드", value=False)

# History stats
history = load_history()
st.sidebar.markdown("---")
st.sidebar.subheader("📊 히스토리 상태")

col1, col2 = st.sidebar.columns(2)
col1.metric("추적된 기사", len(history["articles"]))
col2.metric("고유 콘텐츠", len(history["content_hashes"]))

if history.get("last_updated"):
    last_update = datetime.fromisoformat(history["last_updated"])
    st.sidebar.caption(f"마지막 업데이트: {last_update.strftime('%Y-%m-%d %H:%M')}")

if st.sidebar.button("🗑️ 히스토리 초기화", use_container_width=True):
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    st.rerun()

# ===== MAIN REPORT BUTTON =====
st.markdown("---")

col_button1, col_button2 = st.columns([2, 1])
with col_button1:
    run_report = st.button("🚀 전략 인텔리전스 리포트 생성", use_container_width=True, key="run_report")

with col_button2:
    if st.button("ℹ️ 소개", use_container_width=True):
        st.info("""
        **Samsung 전략 조달 에이전트**
        
        이 자동화 시스템은 유럽 뉴스를 10개 언어로 매일 스캔하여 다음을 식별합니다:
        • 가격 변동성 & 공급 위험
        • 물류 중단
        • EU 규제 업데이트
        • 혁신 기회
        • Samsung 포트폴리오 개발
        """)

# ===== RUN REPORT LOGIC =====
if run_report:
    if not tavily_key:
        st.error("❌ 사이드바에 Tavily API 키를 입력하세요.")
    else:
        client = TavilyClient(api_key=tavily_key)
        history = load_history()
        
        # Progress tracking
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        all_articles = []
        articles_by_category = {}
        debug_info = [] if debug_mode else None
        
        # Search all categories
        for idx, (cat_name, cat_config) in enumerate(CATEGORIES.items()):
            status_text.text(f"🔍 {cat_name} 검색 중...")
            
            results = perform_multilingual_search(
                cat_config, 
                cat_name, 
                client, 
                history,
                max_results=2,
                debug_info=debug_info
            )
            
            if results:
                articles_by_category[cat_name] = results
                all_articles.extend(results)
            
            progress_bar.progress((idx + 1) / len(CATEGORIES))
        
        # Limit to max 10 articles
        all_articles = all_articles[:MAX_TOTAL_ARTICLES]
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Debug info
        if debug_mode and debug_info:
            st.markdown("### 🐛 디버그 정보")
            for info in debug_info:
                with st.expander(f"{info['category']} - {info['total_results']}개 기사 발견"):
                    for attempt in info['search_attempts']:
                        st.write(f"**{attempt['language']}**: {attempt.get('results_count', 0)} 결과")
                        st.code(attempt['query'])
                        if 'error' in attempt:
                            st.error(f"Error: {attempt['error']}")
        
        # Summary stats
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔍 새 기사 발견", len(all_articles))
        col2.metric("📂 검색된 카테고리", len(articles_by_category))
        col3.metric("💾 총 추적된 기사", len(history["articles"]))
        col4.metric("🌍 검색한 언어", len(LANGUAGES))
        
        st.markdown("---")
        
        # Display articles by category
        if all_articles:
            article_count = 0
            
            for cat_name, articles in articles_by_category.items():
                if article_count >= MAX_TOTAL_ARTICLES:
                    break
                
                cat_emoji = CATEGORIES[cat_name]["emoji"]
                
                # Category header
                st.markdown(f"### {cat_emoji} {cat_name}")
                st.markdown(f"*{len(articles)}개의 새로운 기사*")
                
                # Articles in this category
                for article in articles:
                    if article_count >= MAX_TOTAL_ARTICLES:
                        break
                    
                    article_count += 1
                    
                    # Smart summarize content
                    with st.spinner(f"📝 기사 {article_count} 분석 중..."):
                        summary_points = smart_summarize_content(article['title'], article['content'])
                        
                        # Translate title to Korean
                        try:
                            title_kr = translate_to_korean_cached(article['title'])
                        except Exception as e:
                            title_kr = article['title']
                    
                    # Article display
                    st.markdown(f"#### 📰 {article_count}. {title_kr}")
                    col_lang, col_cat = st.columns([1, 1])
                    with col_lang:
                        st.caption(f"🌐 {article['language']}")
                    with col_cat:
                        st.caption(f"📂 {cat_name}")
                    
                    # Summary with 3 key points from article
                    st.markdown("**□**")
                    st.markdown(f"- {summary_points[0]}")
                    st.markdown(f"- {summary_points[1]}")
                    st.markdown(f"- {summary_points[2]}")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"[📖 전체 기사 읽기]({article['url']})")
                    
                    with col2:
                        if st.button("✅ 읽음 표시", key=f"read_{article['url']}", use_container_width=True):
                            add_to_history(
                                article['url'],
                                article['title'],
                                article['content'],
                                cat_name,
                                article['language']
                            )
                            st.success("히스토리에 추가!")
                    
                    with col3:
                        if st.button("🔗 URL 복사", key=f"copy_{article['url']}", use_container_width=True):
                            st.code(article['url'], language="text")
                    
                    st.divider()
            
            # Final stats
            st.markdown("### 📊 리포트 요약")
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            
            with summary_col1:
                st.metric("✅ 완료", "리포트 생성 완료")
            
            with summary_col2:
                st.metric("🆕 새 기사", len(all_articles))
            
            with summary_col3:
                st.metric("📈 데이터베이스", len(history["articles"]))
        
        else:
            st.warning("⚠️ 검색 결과가 없습니다. 몇 가지 확인사항:")
            st.markdown("""
            1. **Tavily API 키 확인**: API 키가 유효한지 확인하세요.
            2. **검색 쿼리**: 더 간단한 검색어로 변경되었습니다.
            3. **데이터 가용성**: Tavily에 해당 지역의 기사가 없을 수 있습니다.
            4. **디버그 모드**: 사이드바에서 "디버그 모드"를 켜고 다시 시도하세요.
            """)
            
            if debug_mode:
                st.info("💡 디버그 정보는 위의 '디버그 정보' 섹션에서 확인할 수 있습니다.")
