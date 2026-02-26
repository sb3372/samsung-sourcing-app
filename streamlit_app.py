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
st.title("🛡️ Samsung Electronics Europe IPC: Strategic Intelligence")

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
        "keywords": ["price", "cost", "supply", "component", "semiconductor"]
    },
    "Supply Chain & Logistics": {
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
        "keywords": ["port", "logistics", "disruption", "China", "nearshoring", "lead time"]
    },
    "EU Regulations & Compliance": {
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
        "keywords": ["regulation", "compliance", "EU", "AI Act", "ESPR", "CRA", "energy"]
    },
    "Innovation & Ecosystem": {
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
        "keywords": ["6G", "robotics", "AI", "startup", "innovation", "deep-tech"]
    },
    "Samsung Portfolio Interests": {
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
        "keywords": ["Samsung", "telecommunication", "wearable", "appliance", "consumer electronics"]
    }
}

# ===== FILE MANAGEMENT =====
HISTORY_FILE = "article_history.json"
MAX_ARTICLE_AGE_DAYS = 7  # Articles older than 7 days are considered "old"
MAX_SEARCH_AGE_DAYS = 30  # Only search for articles from last 30 days

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
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    return hashlib.md5(text.encode()).hexdigest()

def is_article_fresh(article_date_str):
    """Check if article is within the 'fresh' threshold (7 days)"""
    try:
        article_date = datetime.fromisoformat(article_date_str.replace('Z', '+00:00'))
        age_days = (datetime.now(article_date.tzinfo) - article_date).days
        return age_days <= MAX_ARTICLE_AGE_DAYS
    except:
        return False

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

# ===== INTELLIGENT ANALYSIS =====
def analyze_article_impact(title, content, category, tavily_client=None):
    """Generate AI-powered impact analysis for Samsung operations"""
    
    impact_framework = {
        "Procurement & Materials": {
            "supply_risk": "Analyze price trends and supply chain vulnerabilities",
            "cost_implication": "Quantify potential cost impact on Samsung's production",
            "strategic_action": "Recommend hedging or diversification strategies",
            "timeline": "Estimate impact timeline for Samsung operations"
        },
        "Supply Chain & Logistics": {
            "supply_risk": "Assess logistics disruption risk and severity",
            "lead_time_impact": "Estimate lead-time changes for European distribution",
            "nearshoring_opportunity": "Identify nearshoring opportunities vs China sourcing",
            "timeline": "Project recovery/mitigation timeline"
        },
        "EU Regulations & Compliance": {
            "compliance_risk": "Assess regulatory compliance impact on Samsung products",
            "market_access": "Evaluate potential market access barriers",
            "implementation_cost": "Estimate compliance implementation costs",
            "timeline": "Deadline for compliance implementation"
        },
        "Innovation & Ecosystem": {
            "competitive_threat": "Identify emerging competitive threats",
            "partnership_opportunity": "Assess partnership/acquisition opportunities",
            "strategic_advantage": "Evaluate potential strategic advantages",
            "timeline": "Time-to-market for emerging technologies"
        },
        "Samsung Portfolio Interests": {
            "product_relevance": "Relevance to Samsung's current portfolio",
            "market_opportunity": "Market size and growth potential",
            "competitive_positioning": "Samsung's competitive position",
            "innovation_gap": "Identify innovation gaps for Samsung"
        }
    }
    
    framework = impact_framework.get(category, {})
    return framework

# ===== SEARCH WITH MULTI-LANGUAGE SUPPORT =====
def perform_multilingual_search(category_config, category_name, tavily_client, history):
    """Perform searches across multiple languages"""
    
    all_results = []
    seen_urls = set()
    
    for lang_name, lang_code in LANGUAGES.items():
        query = category_config["queries"].get(lang_code, category_config["queries"]["en"])
        
        # Add date filter and language hint
        search_query = f"{query} (published after {(datetime.now() - timedelta(days=MAX_SEARCH_AGE_DAYS)).strftime('%Y-%m-%d')})"
        
        try:
            results = tavily_client.search(
                query=search_query,
                search_depth="advanced",
                max_results=5,
                include_raw_content=True
            )
            
            for res in results.get('results', []):
                url = res.get('url')
                
                # Skip if URL already seen in this batch
                if url in seen_urls or url in history["articles"]:
                    continue
                
                # Skip if duplicate content
                if is_duplicate(res.get('title', ''), res.get('content', ''), history):
                    continue
                
                seen_urls.add(url)
                
                all_results.append({
                    "url": url,
                    "title": res.get('title', 'No title'),
                    "content": res.get('content', ''),
                    "language": lang_name,
                    "lang_code": lang_code,
                    "raw_content": res.get('raw_content', res.get('content', ''))[:1000]
                })
        
        except Exception as e:
            st.warning(f"Search error for {lang_name} in {category_name}: {str(e)}")
    
    return all_results

# ===== MAIN APP =====
st.sidebar.header("⚙️ Configuration")
tavily_key = st.sidebar.text_input("Tavily API Key", type="password", help="Enter your Tavily API key")

# Display search history stats
history = load_history()
st.sidebar.markdown("---")
st.sidebar.subheader("📊 History Status")
st.sidebar.metric("Total Articles Tracked", len(history["articles"]))
st.sidebar.metric("Unique Content Hashes", len(history["content_hashes"]))

if history.get("last_updated"):
    last_update = datetime.fromisoformat(history["last_updated"])
    st.sidebar.caption(f"Last updated: {last_update.strftime('%Y-%m-%d %H:%M')}")

# Clear history button
if st.sidebar.button("🗑️ Clear History", help="Reset all tracked articles"):
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    st.sidebar.success("History cleared!")
    st.rerun()

# ===== RUN REPORT =====
if st.button("🚀 Run Strategic Intelligence Report", use_container_width=True):
    if not tavily_key:
        st.error("❌ Please enter your Tavily API Key in the sidebar.")
    else:
        client = TavilyClient(api_key=tavily_key)
        history = load_history()
        
        total_new_articles = 0
        articles_by_category = defaultdict(list)
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Process each category
        for idx, (cat_name, cat_config) in enumerate(CATEGORIES.items()):
            status_text.text(f"Searching {cat_name}...")
            
            # Multi-language search
            results = perform_multilingual_search(cat_config, cat_name, client, history)
            
            if results:
                articles_by_category[cat_name] = results
                total_new_articles += len(results)
            
            progress_bar.progress((idx + 1) / len(CATEGORIES))
        
        status_text.text("Generating analysis...")
        
        # Display results by category
        for cat_name, articles in articles_by_category.items():
            st.header(f"📂 {cat_name}")
            st.markdown(f"**Found {len(articles)} new articles**")
            
            for article in articles:
                # Visual indicator for language
                lang_flag = f"🌐 {article['language']}"
                
                with st.expander(f"📰 {article['title'][:80]}... {lang_flag}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**[Read Full Article →]({article['url']})")
                    
                    with col2:
                        if st.button("✅ Mark as Read", key=article['url']):
                            add_to_history(
                                article['url'],
                                article['title'],
                                article['content'],
                                cat_name,
                                article['language']
                            )
                            st.success("Added to history")
                    
                    # Impact Analysis
                    st.markdown("### 🎯 Impact on Samsung Operations")
                    
                    framework = analyze_article_impact(article['title'], article['content'], cat_name, client)
                    
                    for key, description in framework.items():
                        st.markdown(f"**{key.replace('_', ' ').title()}:**")
                        st.caption(description)
                    
                    # Content Preview
                    st.markdown("### 📄 Article Summary")
                    st.write(article['raw_content'])
                    
                    st.divider()
        
        # Final summary
        st.success(f"✅ Report Complete")
        col1, col2, col3 = st.columns(3)
        col1.metric("New Articles Found", total_new_articles)
        col2.metric("Articles in History", len(history["articles"]))
        col3.metric("Categories Scanned", len(CATEGORIES))
        
        status_text.empty()
        progress_bar.empty()
