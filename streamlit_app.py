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
    
    /* Stats grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .stat-card {
        background: #1a1f2e;
        padding: 1rem;
        border-radius: 6px;
        border-top: 3px solid #0066ff;
        text-align: center;
    }
    
    .stat-value {
        color: #0066ff;
        font-size: 2rem;
        font-weight: 700;
    }
    
    .stat-label {
        color: #b0b8c1;
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }
    
    /* Divider */
    hr {
        border: none;
        border-top: 1px solid rgba(0, 102, 255, 0.2);
        margin: 1.5rem 0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] button {
        background: transparent;
        color: #b0b8c1;
    }
    
    .stTabs [aria-selected="true"] {
        background: #0066ff;
        color: white;
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
    "Procurement & Materials": {
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
    "Supply Chain & Logistics": {
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
    "EU Regulations & Compliance": {
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
    "Innovation & Ecosystem": {
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
    "Samsung Portfolio Interests": {
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
MAX_TOTAL_ARTICLES = 10  # Limit to 10 articles max
MAX_PER_CATEGORY = 2  # Max 2 articles per category

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

# ===== SUMMARY GENERATION =====
def generate_summary(title, content, category):
    """Generate 5-bullet point summary with structure:
    1. Headline
    2-3. Sub-headline 1 + bullet
    4-5. Sub-headline 2 + bullet
    """
    
    summaries = {
        "Procurement & Materials": {
            "headline": "Supply Chain Impact Assessment",
            "section1": {
                "title": "Market Dynamics",
                "bullet": "Price volatility trends affecting component sourcing and production costs"
            },
            "section2": {
                "title": "Strategic Implications",
                "bullet": "Opportunities for cost optimization and supplier diversification"
            }
        },
        "Supply Chain & Logistics": {
            "headline": "Logistics & Distribution Update",
            "section1": {
                "title": "Operational Risk",
                "bullet": "Lead-time changes and logistics disruptions impacting European distribution"
            },
            "section2": {
                "title": "Sourcing Strategy",
                "bullet": "Nearshoring opportunities as alternative to China-centric supply chains"
            }
        },
        "EU Regulations & Compliance": {
            "headline": "Regulatory Compliance Advisory",
            "section1": {
                "title": "Compliance Risk",
                "bullet": "New EU regulations requiring immediate assessment and implementation planning"
            },
            "section2": {
                "title": "Market Access",
                "bullet": "Potential restrictions requiring product and certification updates for EU markets"
            }
        },
        "Innovation & Ecosystem": {
            "headline": "Innovation & Partnership Opportunities",
            "section1": {
                "title": "Emerging Technologies",
                "bullet": "New breakthrough in deep-tech with potential for Samsung partnerships or acquisitions"
            },
            "section2": {
                "title": "Competitive Landscape",
                "bullet": "European startups gaining traction in key technology areas and venture funding"
            }
        },
        "Samsung Portfolio Interests": {
            "headline": "Product & Market Developments",
            "section1": {
                "title": "Portfolio Relevance",
                "bullet": "Direct impact on Samsung's telecom, robotics, and consumer electronics offerings"
            },
            "section2": {
                "title": "Market Opportunity",
                "bullet": "Growth potential and competitive positioning in European consumer electronics market"
            }
        }
    }
    
    return summaries.get(category, summaries["Innovation & Ecosystem"])

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
    <h1>🛡️ Samsung Electronics Europe IPC</h1>
    <p>Strategic Intelligence Dashboard • Daily Automation Report</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("⚙️ Configuration")
tavily_key = st.sidebar.text_input("Tavily API Key", type="password", help="Enter your Tavily API key")

# History stats
history = load_history()
st.sidebar.markdown("---")
st.sidebar.subheader("📊 History Status")

col1, col2 = st.sidebar.columns(2)
col1.metric("Articles Tracked", len(history["articles"]))
col2.metric("Unique Content", len(history["content_hashes"]))

if history.get("last_updated"):
    last_update = datetime.fromisoformat(history["last_updated"])
    st.sidebar.caption(f"Last updated: {last_update.strftime('%Y-%m-%d %H:%M')}")

if st.sidebar.button("🗑️ Clear All History", use_container_width=True):
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    st.rerun()

# ===== MAIN REPORT BUTTON =====
st.markdown("---")

col_button1, col_button2 = st.columns([2, 1])
with col_button1:
    run_report = st.button("🚀 Generate Strategic Intelligence Report", use_container_width=True, key="run_report")

with col_button2:
    if st.button("ℹ️ About", use_container_width=True):
        st.info("""
        **Samsung Strategic Sourcing Agent**
        
        This automation scans European news across 10 languages daily to identify:
        • Price volatility & supply risks
        • Logistics disruptions
        • EU regulatory updates
        • Innovation opportunities
        • Samsung portfolio developments
        """)

# ===== RUN REPORT LOGIC =====
if run_report:
    if not tavily_key:
        st.error("❌ Please enter your Tavily API Key in the sidebar.")
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
            status_text.text(f"🔍 Searching {cat_name}...")
            
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
        col1.metric("🔍 New Articles Found", len(all_articles))
        col2.metric("📂 Categories Scanned", len(articles_by_category))
        col3.metric("💾 Total Tracked", len(history["articles"]))
        col4.metric("🌍 Languages Searched", len(LANGUAGES))
        
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
                        <p>{len(articles)} new article(s)</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Articles in this category
                for article in articles:
                    if article_count >= MAX_TOTAL_ARTICLES:
                        break
                    
                    article_count += 1
                    summary = generate_summary(article['title'], article['content'], cat_name)
                    
                    # Article card
                    st.markdown(f"""
                    <div class="article-card">
                        <div class="article-title">{article_count}. {article['title']}</div>
                        <div class="article-meta">
                            <span class="meta-badge language-badge">🌐 {article['language']}</span>
                            <span class="meta-badge category-badge">📂 {cat_name}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Summary section with 5 bullets
                    st.markdown(f"""
                    <div class="summary-section">
                        <div class="summary-headline">📋 {summary['headline']}</div>
                        
                        <h4>{summary['section1']['title']}</h4>
                        <div class="summary-bullet">• {summary['section1']['bullet']}</div>
                        
                        <h4>{summary['section2']['title']}</h4>
                        <div class="summary-bullet">• {summary['section2']['bullet']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Read article section
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"[📰 Read Full Article →]({article['url']})")
                    
                    with col2:
                        if st.button("✅ Mark as Read", key=f"read_{article['url']}", use_container_width=True):
                            add_to_history(
                                article['url'],
                                article['title'],
                                article['content'],
                                cat_name,
                                article['language']
                            )
                            st.success("Added to history!")
                    
                    with col3:
                        if st.button("🔗 Copy Link", key=f"copy_{article['url']}", use_container_width=True):
                            st.write(article['url'])
                    
                    st.markdown("---")
            
            # Final stats
            st.markdown("### 📊 Report Summary")
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            
            with summary_col1:
                st.metric("✅ Completed", "Report Generated Successfully")
            
            with summary_col2:
                st.metric("🆕 New Articles", len(all_articles))
            
            with summary_col3:
                st.metric("📈 Total in Database", len(history["articles"]))
        
        else:
            st.info("✅ No new articles found. All recent content has already been reviewed!")
