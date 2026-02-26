import streamlit as st
from tavily import TavilyClient
from datetime import datetime, timedelta
import os
import json
import hashlib
from collections import defaultdict
import re
import requests

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

MAX_TOTAL_ARTICLES = 10
MAX_PER_CATEGORY = 2
HISTORY_FILE = "article_history.json"

# ===== FILE MANAGEMENT =====
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"articles": {}, "content_hashes": set(), "last_updated": None}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["content_hashes"] = set(data.get("content_hashes", []))
            return data
    except:
        return {"articles": {}, "content_hashes": set(), "last_updated": None}

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
    content_hash = get_content_hash(title, content)
    return content_hash in history["content_hashes"]

def add_to_history(url, title, content, category, language):
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

# ===== TRANSLATION =====
@st.cache_data
def translate_to_korean_cached(text):
    try:
        from google_trans_new import google_translator
        translator = google_translator()
        result = translator.translate(text, lang_src='en', lang_tgt='ko')
        return result
    except:
        return text

# ===== SMART SUMMARIZATION WITH LLM =====
def summarize_with_groq(title, content, cohere_api_key):
    """
    Use Cohere API to generate proper Korean summary
    Format: □ 제목
            - 핵심포인트1
            ·세부사항
            - 핵심포인트2
            ·세부사항
    """
    try:
        headers = {
            "Authorization": f"Bearer {cohere_api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""기사 제목: {title}

기사 내용: {content[:2000]}

위 기사를 다음 한국어 포맷으로 요약해주세요. 기사 내용만 요약하고, 전략적 분석은 하지 마세요.

포맷:
□ [기사 제목을 한국어로 번역]1)
- [핵심 포인트 1 (구체적인 숫자나 사실)]
·[핵심 포인트 1의 세부 설명 (한 문장)]
- [핵심 포인트 2 (다른 관점의 사실)]
·[핵심 포인트 2의 세부 설명 (한 문장)]
- [핵심 포인트 3 (영향 또는 결과)]
·[핵심 포인트 3의 세부 설명 (한 문장)]

예시:
□ ASML, EUV 광원 출격 1,000W 돌파... 반도체 생산성 50% 향상 예고1)
- 기존 600W 수준 EUV 광원 출력을 1,000W까지 끌어올리는 데 성공
·액체 주석(Molten Tin) 방울 투사 속도 2배로 향상
- 출력 강화로, 현재 시간당 220장 '30년 330장 수준으로 확대 전망
·레이저 펄스를 이중으로 구성하여 고출력 플라즈마 생성"""

        data = {
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.cohere.ai/v1/generate",
            headers=headers,
            json=data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result.get('generations', [{}])[0].get('text', '').strip()
            return summary
        else:
            return None
    except:
        return None

# ===== MULTI-LANGUAGE SEARCH =====
def perform_multilingual_search(category_config, category_name, tavily_client, history, max_results=3):
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
                max_results=max_results,
                include_raw_content=True
            )
            
            for res in results.get('results', []):
                if len(all_results) >= MAX_PER_CATEGORY:
                    break
                    
                url = res.get('url')
                title = res.get('title', 'No title')
                content = res.get('content', '')
                
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
                    "raw_content": res.get('raw_content', content)[:1000]
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
tavily_key = st.sidebar.text_input("Tavily API Key", type="password", help="Tavily API 키 입력")
cohere_key = st.sidebar.text_input("Cohere API Key", type="password", help="Cohere API 키 입력 (요약용)")

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

# ===== MAIN BUTTON =====
st.markdown("---")

col_button1, col_button2 = st.columns([2, 1])
with col_button1:
    run_report = st.button("🚀 전략 인텔리전스 리포트 생성", use_container_width=True, key="run_report")

with col_button2:
    if st.button("ℹ️ 소개", use_container_width=True):
        st.info("Samsung 전략 조달 에이전트 - 유럽 뉴스를 10개 언어로 스캔합니다.")

# ===== RUN REPORT =====
if run_report:
    if not tavily_key:
        st.error("❌ Tavily API 키를 입력하세요.")
    elif not cohere_key:
        st.error("❌ Cohere API 키를 입력하세요.")
    else:
        client = TavilyClient(api_key=tavily_key)
        history = load_history()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_articles = []
        articles_by_category = {}
        
        for idx, (cat_name, cat_config) in enumerate(CATEGORIES.items()):
            status_text.text(f"🔍 {cat_name} 검색 중...")
            
            results = perform_multilingual_search(cat_config, cat_name, client, history, max_results=2)
            
            if results:
                articles_by_category[cat_name] = results
                all_articles.extend(results)
            
            progress_bar.progress((idx + 1) / len(CATEGORIES))
        
        all_articles = all_articles[:MAX_TOTAL_ARTICLES]
        
        progress_bar.empty()
        status_text.empty()
        
        # Stats
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔍 새 기사", len(all_articles))
        col2.metric("📂 카테고리", len(articles_by_category))
        col3.metric("💾 총 기사", len(history["articles"]))
        col4.metric("🌍 언어", len(LANGUAGES))
        
        st.markdown("---")
        
        if all_articles:
            article_count = 0
            
            for cat_name, articles in articles_by_category.items():
                if article_count >= MAX_TOTAL_ARTICLES:
                    break
                
                cat_emoji = CATEGORIES[cat_name]["emoji"]
                st.markdown(f"### {cat_emoji} {cat_name}")
                st.markdown(f"*{len(articles)}개의 새로운 기사*")
                
                for article in articles:
                    if article_count >= MAX_TOTAL_ARTICLES:
                        break
                    
                    article_count += 1
                    
                    with st.spinner(f"📝 기사 {article_count} 요약 중..."):
                        summary = summarize_with_groq(article['title'], article['content'], cohere_key)
                        
                        try:
                            title_kr = translate_to_korean_cached(article['title'])
                        except:
                            title_kr = article['title']
                    
                    # Display
                    st.markdown(f"#### 📰 {article_count}. {title_kr}")
                    col_lang, col_cat = st.columns([1, 1])
                    with col_lang:
                        st.caption(f"🌐 {article['language']}")
                    with col_cat:
                        st.caption(f"📂 {cat_name}")
                    
                    # Summary
                    if summary:
                        st.markdown(summary)
                    else:
                        st.warning("요약 생성 실패")
                    
                    # Buttons
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"[📖 전체 기사 읽기]({article['url']})")
                    with col2:
                        if st.button("✅ 읽음", key=f"read_{article['url']}", use_container_width=True):
                            add_to_history(article['url'], article['title'], article['content'], cat_name, article['language'])
                            st.success("완료!")
                    with col3:
                        if st.button("🔗 링크", key=f"copy_{article['url']}", use_container_width=True):
                            st.code(article['url'])
                    
                    st.divider()
            
            st.markdown("### 📊 리포트 완료")
            col1, col2, col3 = st.columns(3)
            col1.metric("✅ 상태", "완료")
            col2.metric("🆕 기사", len(all_articles))
            col3.metric("📈 DB", len(history["articles"]))
        else:
            st.warning("검색 결과가 없습니다.")
