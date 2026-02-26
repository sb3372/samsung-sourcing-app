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

# ===== CUSTOM CSS FOR BETTER DESIGN =====
st.markdown("""
<style>
    /* Main theme colors */
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
    
    /* Main container */
    .main {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%);
    }
    
    /* Header styling */
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
    
    /* Article card */
    .article-card {
        background: #1a1f2e;
        border-left: 4px solid #0066ff;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    
    .article-card:hover {
        box-shadow: 0 4px 16px rgba(0, 102, 255, 0.2);
        transform: translateX(4px);
    }
    
    /* Article title */
    .article-title {
        color: #0066ff;
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    /* Meta info */
    .article-meta {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
        font-size: 0.85rem;
    }
    
    .meta-badge {
        background: rgba(0, 102, 255, 0.2);
        color: #0066ff;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        display: inline-block;
    }
    
    .language-badge {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    
    .category-badge {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
    }
    
    /* Summary section */
    .summary-section {
        background: rgba(0, 102, 255, 0.05);
        padding: 1.2rem;
        border-radius: 6px;
        margin: 1rem 0;
        border-left: 3px solid #0066ff;
    }
    
    .summary-headline {
        color: #0066ff;
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 0.8rem;
    }
    
    .summary-section h4 {
        color: #ffffff;
        font-size: 0.95rem;
        margin-top: 0.8rem;
        margin-bottom: 0.4rem;
        font-weight: 600;
    }
    
    .summary-bullet {
        color: #b0b8c1;
        margin-left: 1.5rem;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    /* Category section */
    .category-section {
        margin-bottom: 2rem;
    }
    
    .category-header {
        background: linear-gradient(90deg, rgba(20, 40, 160, 0.3), rgba(0, 102, 255, 0.2));
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #1428a0;
    }
    
    .category-header h2 {
        color: #0066ff;
        margin: 0;
        font-size: 1.5rem;
    }
    
    .category-header p {
        color: #b0b8c1;
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
    }
    
    /* Buttons */
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
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #1a1f2e;
    }
    
    /* Metrics */
    [data-testid="metric-container"] {
        background: #1a1f2e;
        border-left: 3px solid #0066ff;
    }
    
    /* Link styling */
    a {
        color: #0066ff !important;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    /* Divider */
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
            "en": "price volatility semiconductor electronic components smartphones raw materials Europe supply cost",
            "de": "Preisvolatilität Halbleiter elektronische Komponenten Smartphones Rohstoffe Europa Lieferkosten",
            "fr": "volatilité des prix composants électroniques smartphones matières premières Europe approvisionnement",
            "es": "volatilidad de precios componentes electrónicos semiconductores smartphones materias primas Europa",
            "it": "volatilità dei prezzi componenti elettronici smartphone materie prime Europa approvvigionamento",
            "pl": "zmienność cen komponenty elektroniczne półprzewodniki smartfony surowce Europa",
            "nl": "prijsvolatiliteit elektronische componenten smartphones grondstoffen Europa leveringen",
            "da": "prisvolatilitet elektroniske komponenter smartphones råmaterialer Europa forsyning",
            "no": "prisvolatilitet elektroniske komponenter smarttelefoner råvarer Europa forsyninger",
            "sv": "prisvolatilitet elektroniska komponenter smartphones råvaror Europa försörjning"
        },
    },
    "공급망 및 물류": {
        "emoji": "🚢",
        "queries": {
            "en": "port strikes logistics disruptions China sourcing nearshoring Europe lead time semiconductor",
            "de": "Hafenstreiks Logistikstörungen China Beschaffung Nearshoring Europa Lieferzeit",
            "fr": "grèves portuaires perturbations logistiques sourcing Chine nearshoring Europe délai de livraison",
            "es": "huelgas portuarias disrupciones logísticas sourcing China nearshoring Europa tiempo de entrega",
            "it": "scioperi portuali interruzioni logistiche sourcing Cina nearshoring Europa tempo di consegna",
            "pl": "strajki portowe zakłócenia logistyczne sourcing Chiny nearshoring Europa czas dostawy",
            "nl": "havenstakingen logistieke verstoringen China sourcing nearshoring Europa levertijd",
            "da": "havnestrejker logistiske forstyrrelser China sourcing nearshoring Europa leveringstid",
            "no": "havnestreiker logistiske forstyrrelser China sourcing nearshoring Europa leveringstid",
            "sv": "hamnstrejker logistiska störningar Kina sourcing nearshoring Europa leveranstid"
        },
    },
    "EU 규제 및 준수": {
        "emoji": "⚖️",
        "queries": {
            "en": "EU AI Act ESPR Digital Product Passport Cyber Resilience Act CRA energy labeling regulation compliance electronics",
            "de": "EU-KI-Gesetz ESPR Digital Product Passport Cyber-Resilienz-Gesetz CRA Energiekennzeichnung Regelkonformität",
            "fr": "Loi IA UE ESPR Passeport Numérique Produit Loi Résilience Cyber CRA étiquetage énergétique conformité",
            "es": "Ley de IA de la UE ESPR Pasaporte Digital de Producto Ley de Resiliencia Cibernética CRA etiquetado energético",
            "it": "Legge AI UE ESPR Passaporto Digitale Prodotto Legge Resilienza Cibernetica CRA etichettatura energetica",
            "pl": "Ustawa AI UE ESPR Paszport Cyfrowy Produktu Ustawa Odporności Cybernetycznej CRA etykietowanie energetyczne",
            "nl": "EU AI-wet ESPR Digitaal Productpaspoort Cyberveiligheidswet CRA energielabeling conformiteit",
            "da": "EU AI-lov ESPR Digitalt produktpas Cybersikkerhedslov CRA energimærkning compliance",
            "no": "EU AI-lov ESPR Digitalt produktpass Cybersikkerhetsloven CRA energimerking compliance",
            "sv": "EU AI-lag ESPR Digitalt produktpass Cybersäkerhetslag CRA energimärkning regelefterlevnad"
        },
    },
    "혁신 및 생태계": {
        "emoji": "🚀",
        "queries": {
            "en": "European 6G robotics AI-native hardware sustainable materials startups venture capital grants deep-tech innovation",
            "de": "Europäische 6G Robotik KI-Hardware nachhaltige Materialien Startups Risikokapital Zuschüsse Deep-Tech",
            "fr": "6G européen robotique matériel IA matériaux durables startups capital-risque subventions innovation deep-tech",
            "es": "6G europeo robótica hardware nativo de IA materiales sostenibles startups capital de riesgo subvenciones",
            "it": "6G europeo robotica hardware nativo IA materiali sostenibili startup capitale di rischio sovvenzioni",
            "pl": "Europejskie 6G robotyka sprzęt AI-native materiały zrównoważone startupy kapitał wysokiego ryzyka dotacje",
            "nl": "Europese 6G robotica AI-native hardware duurzame materialen startups durfkapitaal subsidies",
            "da": "Europæisk 6G robotik AI-hardware bæredygtige materialer startups venturekapital tilskud deep-tech",
            "no": "Europeisk 6G robotikk AI-innfødt maskinvare bærekraftige materialer startups venturekapital stipend",
            "sv": "Europeisk 6G robotteknik AI-ursprunglig hårdvara hållbara material startups riskkapital bidrag"
        },
    },
    "Samsung 포트폴리오": {
        "emoji": "📱",
        "queries": {
            "en": "Samsung telecommunication devices wearables home appliances consumer electronics innovation Europe technology",
            "de": "Samsung Telekommunikationsgeräte Wearables Haushaltsgeräte Unterhaltungselektronik Innovation Europa",
            "fr": "Samsung appareils de télécommunication wearables appareils ménagers électronique grand public innovation",
            "es": "Samsung dispositivos de telecomunicaciones wearables electrodomésticos electrónica de consumo innovación",
            "it": "Samsung dispositivi telecomunicazioni wearables elettrodomestici elettronica di consumo innovazione",
            "pl": "Samsung urządzenia telekomunikacyjne wearables urządzenia domowe elektronika konsumencka innowacja",
            "nl": "Samsung telecommunicatieapparaten wearables huishoudelijke apparaten consumentenelektronica innovatie",
            "da": "Samsung telekommunikationsudstyr wearables husholdningsapparater forbrugerelektronik innovation",
            "no": "Samsung telekommunikasjonsutstyr wearables husholdningsapparater forbrukerelektronikk innovasjon",
            "sv": "Samsung telekommunikationsenheter wearables hushållsapparater konsumentelektronik innovation"
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

# ===== TRANSLATION AND SUMMARY GENERATION =====
def translate_and_summarize(title, content, category, openai_api_key):
    """
    Translate article to Korean and generate 5-bullet summary using OpenAI API.
    Returns: {
        'title_kr': Korean title,
        'headline': 메인 헤드라인,
        'section1_title': 소제목 1,
        'section1_bullet': 소제목 1 설명,
        'section2_title': 소제목 2,
        'section2_bullet': 소제목 2 설명
    }
    """
    try:
        headers = {
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""당신은 Samsung 조달 전문가입니다. 다음 기사를 한국어로 번역하고 요약해주세요.

기사 제목: {title}

기사 내용: {content[:1200]}

카테고리: {category}

한국어로 다음 JSON 형식으로만 응답해주세요 (다른 텍스트 없이):
{{
  "title_kr": "한국어 제목 (10-20 글자)",
  "headline": "Samsung 운영에 미치는 영향 (한 줄 요약, 15-20 글자)",
  "section1_title": "첫 번째 소제목 (3-4 단어)",
  "section1_bullet": "첫 번째 상세 설명 (20-30 글자 한 문장)",
  "section2_title": "두 번째 소제목 (3-4 단어)",
  "section2_bullet": "두 번째 상세 설명 (20-30 글자 한 문장)"
}}"""
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code != 200:
            st.warning(f"OpenAI API 오류: {response.status_code}")
            return get_default_summary(title, category)
        
        response_json = response.json()
        response_text = response_json["choices"][0]["message"]["content"]
        
        # Parse JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            summary_data = json.loads(response_text.strip())
        except json.JSONDecodeError:
            st.warning("JSON 파싱 오류, 기본 요약 사용")
            return get_default_summary(title, category)
        
        return summary_data
    
    except Exception as e:
        st.warning(f"번역 오류: {str(e)}, 기본 요약 사용")
        return get_default_summary(title, category)

def get_default_summary(title, category):
    """Return a default summary when API fails"""
    return {
        'title_kr': title,
        'headline': f'{category} 관련 중요 소식',
        'section1_title': '시장 영향',
        'section1_bullet': 'Samsung의 운영에 영향을 미치는 주요 사항입니다.',
        'section2_title': '전략적 중요성',
        'section2_bullet': '향후 조달 전략 수립 시 검토 필요합니다.'
    }

# ===== MULTI-LANGUAGE SEARCH =====
def perform_multilingual_search(category_config, category_name, tavily_client, history, max_results=3):
    """Perform searches across multiple languages"""
    
    all_results = []
    seen_urls = set()
    
    for lang_name, lang_code in LANGUAGES.items():
        if len(all_results) >= MAX_PER_CATEGORY:
            break
            
        query = category_config["queries"].get(lang_code, category_config["queries"]["en"])
        search_query = f"{query} (published after {(datetime.now() - timedelta(days=MAX_SEARCH_AGE_DAYS)).strftime('%Y-%m-%d')})"
        
        try:
            results = tavily_client.search(
                query=search_query,
                search_depth="advanced",
                max_results=max_results,
                include_raw_content=True
            )
            
            for res in results.get('results', []):
                if len(all_results) >= MAX_PER_CATEGORY:
                    break
                    
                url = res.get('url')
                
                if url in seen_urls or url in history["articles"]:
                    continue
                
                if is_duplicate(res.get('title', ''), res.get('content', ''), history):
                    continue
                
                seen_urls.add(url)
                
                all_results.append({
                    "url": url,
                    "title": res.get('title', 'No title'),
                    "content": res.get('content', ''),
                    "language": lang_name,
                    "lang_code": lang_code,
                    "raw_content": res.get('raw_content', res.get('content', ''))[:500]
                })
        
        except Exception as e:
            pass
    
    return all_results

# ===== MAIN UI =====
# Header
st.markdown("""
<div class="header-container">
    <h1>🛡️ Samsung 유럽 조달 센터 전략 인텔리전스</h1>
    <p>전략 정보 대시보드 • 일일 자동화 리포트</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("⚙️ 설정")

tavily_key = st.sidebar.text_input("Tavily API Key", type="password", help="Tavily API 키 입력")
openai_key = st.sidebar.text_input("OpenAI API Key", type="password", help="OpenAI API 키 입력 (번역용)")

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
    elif not openai_key:
        st.error("❌ 사이드바에 OpenAI API 키를 입력하세요.")
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
        
        # Search all categories
        for idx, (cat_name, cat_config) in enumerate(CATEGORIES.items()):
            status_text.text(f"🔍 {cat_name} 검색 중...")
            
            results = perform_multilingual_search(
                cat_config, 
                cat_name, 
                client, 
                history,
                max_results=2
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
                st.markdown(f"""
                <div class="category-section">
                    <div class="category-header">
                        <h2>{cat_emoji} {cat_name}</h2>
                        <p>{len(articles)}개의 새로운 기사</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Articles in this category
                for article in articles:
                    if article_count >= MAX_TOTAL_ARTICLES:
                        break
                    
                    article_count += 1
                    
                    # Generate summary with translation
                    with st.spinner(f"📝 기사 {article_count} 번역 및 분석 중..."):
                        summary = translate_and_summarize(
                            article['title'],
                            article['content'],
                            cat_name,
                            openai_key
                        )
                    
                    # Article card
                    st.markdown(f"""
                    <div class="article-card">
                        <div class="article-title">{article_count}. {summary.get('title_kr', article['title'])}</div>
                        <div class="article-meta">
                            <span class="meta-badge language-badge">🌐 {article['language']}</span>
                            <span class="meta-badge category-badge">📂 {cat_name}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Summary section with 5 structured bullets
                    st.markdown(f"""
                    <div class="summary-section">
                        <div class="summary-headline">📋 {summary.get('headline', 'Samsung 운영에 미치는 영향')}</div>
                        
                        <h4>🔹 {summary.get('section1_title', '섹션 1')}</h4>
                        <div class="summary-bullet">• {summary.get('section1_bullet', '내용')}</div>
                        
                        <h4>🔹 {summary.get('section2_title', '섹션 2')}</h4>
                        <div class="summary-bullet">• {summary.get('section2_bullet', '내용')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Read article section
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"[📰 전체 기사 읽기 →]({article['url']})")
                    
                    with col2:
                        if st.button("✅ 읽음으로 표시", key=f"read_{article['url']}", use_container_width=True):
                            add_to_history(
                                article['url'],
                                article['title'],
                                article['content'],
                                cat_name,
                                article['language']
                            )
                            st.success("히스토리에 추가되었습니다!")
                    
                    with col3:
                        if st.button("🔗 링크 복사", key=f"copy_{article['url']}", use_container_width=True):
                            st.code(article['url'])
                    
                    st.markdown("---")
            
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
            st.info("✅ 새로운 기사가 없습니다. 최근 모든 콘텐츠는 이미 검토되었습니다!")
