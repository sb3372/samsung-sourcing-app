import streamlit as st
from tavily import TavilyClient
from datetime import datetime, timedelta
import os
import json
import hashlib
import re

# ===== PAGE CONFIGURATION =====
st.set_page_config(
    page_title="Samsung Strategic Sourcing Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CUSTOM CSS =====
st.markdown("""
<style>
    :root {
        --samsung-blue: #1428a0;
        --samsung-accent: #0066ff;
        --dark-bg: #0f1419;
        --card-bg: #1a1f2e;
        --text-primary: #ffffff;
        --text-secondary: #b0b8c1;
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
    }
</style>
""", unsafe_allow_html=True)

# ===== CONFIGURATION =====
LANGUAGES = {
    "English": "en",
    "German": "de",
    "French": "fr",
    "Spanish": "es",
}

CATEGORIES = {
    "조달 및 소재": {
        "emoji": "💰",
        "queries": {
            "en": "semiconductor price volatility Europe 2024 2025",
            "de": "Halbleiter Preise Europa",
            "fr": "prix semiconducteur Europe",
            "es": "precios semiconductores Europa",
        },
    },
    "공급망 및 물류": {
        "emoji": "🚢",
        "queries": {
            "en": "logistics disruption Europe port strikes 2024",
            "de": "Logistik Störungen Europa",
            "fr": "perturbations logistiques Europe",
            "es": "disrupciones logísticas Europa",
        },
    },
    "EU 규제 및 준수": {
        "emoji": "⚖️",
        "queries": {
            "en": "EU AI Act CRA regulation electronics 2024",
            "de": "EU KI Gesetz CRA",
            "fr": "Loi IA UE CRA",
            "es": "Ley IA UE CRA",
        },
    },
    "혁신 및 생태계": {
        "emoji": "🚀",
        "queries": {
            "en": "European startups 6G robotics AI innovation 2024",
            "de": "Europäische Startups 6G Robotik",
            "fr": "startups européens 6G robotique",
            "es": "startups europeos 6G robótica",
        },
    },
    "Samsung 포트폴리오": {
        "emoji": "📱",
        "queries": {
            "en": "Samsung Europe technology innovation 2024",
            "de": "Samsung Europa Technologie",
            "fr": "Samsung Europe technologie",
            "es": "Samsung Europa tecnología",
        },
    }
}

MAX_TOTAL_ARTICLES = 10
MAX_PER_CATEGORY = 2
HISTORY_FILE = "article_history.json"

# ===== HISTORY MANAGEMENT =====
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"articles": {}, "content_hashes": set()}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["content_hashes"] = set(data.get("content_hashes", []))
            return data
    except:
        return {"articles": {}, "content_hashes": set()}

def save_history(history):
    save_data = history.copy()
    save_data["content_hashes"] = list(history["content_hashes"])
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

def get_content_hash(title, content):
    text = f"{title}{content}".lower()
    text = re.sub(r'\s+', ' ', text)
    return hashlib.md5(text.encode()).hexdigest()

def is_duplicate(title, content, history):
    return get_content_hash(title, content) in history["content_hashes"]

def add_to_history(url, title, content, category):
    history = load_history()
    hash_val = get_content_hash(title, content)
    history["articles"][url] = {
        "title": title,
        "category": category,
        "date": datetime.now().isoformat()
    }
    history["content_hashes"].add(hash_val)
    save_history(history)

# ===== TRANSLATION =====
@st.cache_data
def translate_to_korean(text):
    try:
        from google_trans_new import google_translator
        translator = google_translator()
        return translator.translate(text, lang_src='en', lang_tgt='ko')
    except:
        return text

# ===== INTELLIGENT SUMMARIZATION =====
def extract_smart_summary(title, content):
    """
    Extract 3 key points from article content
    Format: - Point (with numbers/facts)
            · Detail explanation
    """
    
    # Clean content
    content = content.replace('\n', ' ').replace('\r', ' ')
    content = re.sub(r'\s+', ' ', content).strip()
    
    # Split by sentences
    sentences = re.split(r'(?<=[.!?])\s+', content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    # Score sentences
    def score_sentence(sent):
        score = 0
        # Prefer sentences with numbers/percentages
        if re.search(r'\d+[%]?', sent):
            score += 5
        # Prefer sentences about growth/change
        keywords = ['grow', 'increase', 'rise', 'jump', 'expand', 'reach', 'launch', 'announce', 'strike', 'disruption', 'regulation', 'innovation', 'market', 'chip', 'semiconductor']
        for kw in keywords:
            if kw.lower() in sent.lower():
                score += 3
        # Prefer longer sentences with more info
        if len(sent.split()) > 8:
            score += 2
        return score
    
    # Score and sort
    scored = [(sent, score_sentence(sent)) for sent in sentences]
    scored = sorted(scored, key=lambda x: x[1], reverse=True)
    
    # Get top 3
    top_3 = [sent for sent, _ in scored[:3]]
    
    # Return top 3 or default
    if len(top_3) < 3:
        top_3.extend([
            "기사에서 추출한 주요 정보입니다.",
            "시장 동향 및 변화를 반영하고 있습니다.",
            "더 자세한 내용은 전체 기사에서 확인할 수 있습니다."
        ])
    
    return top_3[:3]

# ===== SEARCH =====
def perform_search(category_config, category_name, tavily_client, history):
    all_results = []
    seen_urls = set()
    
    for lang_name, lang_code in LANGUAGES.items():
        if len(all_results) >= MAX_PER_CATEGORY:
            break
        
        query = category_config["queries"].get(lang_code, category_config["queries"]["en"])
        
        try:
            results = tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=3,
                include_raw_content=True
            )
            
            for res in results.get('results', []):
                if len(all_results) >= MAX_PER_CATEGORY:
                    break
                
                url = res.get('url')
                title = res.get('title', '')
                content = res.get('content', '')
                
                if not url or not content:
                    continue
                
                if url in seen_urls or url in history["articles"]:
                    continue
                
                if len(content) < 100:
                    continue
                
                if is_duplicate(title, content, history):
                    continue
                
                seen_urls.add(url)
                all_results.append({
                    "url": url,
                    "title": title,
                    "content": content,
                    "language": lang_name,
                })
        except:
            pass
    
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
tavily_key = st.sidebar.text_input("Tavily API Key", type="password")

history = load_history()
st.sidebar.markdown("---")
st.sidebar.subheader("📊 히스토리")
col1, col2 = st.sidebar.columns(2)
col1.metric("추적 기사", len(history["articles"]))
col2.metric("고유 콘텐츠", len(history["content_hashes"]))

if st.sidebar.button("🗑️ 초기화", use_container_width=True):
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    st.rerun()

# Main
st.markdown("---")
run_report = st.button("🚀 리포트 생성", use_container_width=True)

st.markdown("---")

if run_report:
    if not tavily_key:
        st.error("❌ Tavily API 키를 입력하세요.")
    else:
        client = TavilyClient(api_key=tavily_key)
        history = load_history()
        
        pbar = st.progress(0)
        status = st.empty()
        
        all_articles = []
        by_category = {}
        
        for idx, (cat_name, cat_config) in enumerate(CATEGORIES.items()):
            status.text(f"🔍 {cat_name} 검색 중...")
            
            results = perform_search(cat_config, cat_name, client, history)
            
            if results:
                by_category[cat_name] = results
                all_articles.extend(results)
            
            pbar.progress((idx + 1) / len(CATEGORIES))
        
        all_articles = all_articles[:MAX_TOTAL_ARTICLES]
        pbar.empty()
        status.empty()
        
        # Stats
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("새 기사", len(all_articles))
        col2.metric("카테고리", len(by_category))
        col3.metric("총 기사", len(history["articles"]))
        
        st.markdown("---")
        
        if all_articles:
            article_num = 0
            
            for cat_name, articles in by_category.items():
                if article_num >= MAX_TOTAL_ARTICLES:
                    break
                
                emoji = CATEGORIES[cat_name]["emoji"]
                st.markdown(f"### {emoji} {cat_name}")
                st.markdown(f"*{len(articles)}개의 새로운 기사*")
                
                for article in articles:
                    if article_num >= MAX_TOTAL_ARTICLES:
                        break
                    
                    article_num += 1
                    
                    # Extract summary
                    with st.spinner(f"📝 기사 {article_num} 분석 중..."):
                        summary_points = extract_smart_summary(article['title'], article['content'])
                        
                        try:
                            title_kr = translate_to_korean(article['title'])
                        except:
                            title_kr = article['title']
                    
                    # Display article
                    st.markdown(f"#### 📰 {article_num}. {title_kr}")
                    col_a, col_b = st.columns([2, 1])
                    with col_a:
                        st.caption(f"🌐 {article['language']}")
                    with col_b:
                        st.caption(f"📂 {cat_name}")
                    
                    # Display summary
                    st.markdown("**□**")
                    st.markdown(f"- {summary_points[0]}")
                    st.markdown(f"  · 주요 내용")
                    st.markdown(f"- {summary_points[1]}")
                    st.markdown(f"  · 추가 정보")
                    st.markdown(f"- {summary_points[2]}")
                    st.markdown(f"  · 상세 내용")
                    
                    # Buttons
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"[📖 전체 기사]({article['url']})")
                    with col2:
                        if st.button("✅ 읽음", key=f"r_{article_num}", use_container_width=True):
                            add_to_history(article['url'], article['title'], article['content'], cat_name)
                            st.success("완료!")
                    with col3:
                        if st.button("🔗 링크", key=f"l_{article_num}", use_container_width=True):
                            st.code(article['url'])
                    
                    st.divider()
        
        else:
            st.warning("⚠️ 검색 결과가 없습니다.")
