"""
Samsung 국제 조달센터 전문 뉴스 수집기 설정
기술 매트릭스 기반 고급 검색 쿼리
"""

SEARCH_QUERIES = {
    "조달 & 자재": {
        "description": "반도체, 디스플레이, 그래핀, 희토류 원자재 가격 변동성",
        "queries": {
            "en_US": [
                "intitle:OLED OR intitle:AMOLED OR intitle:MicroLED price volatility shortage",
                "intitle:Graphene OR intitle:Perovskite semiconductor production cost",
                "intitle:Rare-earth materials price shortage Europe",
            ],
            "de_DE": [
                "intitle:OLED OR intitle:Halbleiter Preis Knappheit Produktion",
                "intitle:Seltene Erden Rohstoffe Lieferkettengesetz",
            ],
            "fr_FR": [
                "intitle:OLED OR intitle:Semiconusductor prix volatilité",
                "intitle:Terres rares souveraineté numérique production",
            ],
            "es_ES": [
                "intitle:OLED OR intitle:Semiconductores precio escasez",
                "intitle:Minerales raros cadena suministro",
            ],
            "nl_NL": [
                "intitle:OLED OR intitle:Halfgeleider prijs tekort",
                "intitle:Zeldzame aardmetalen toeleveringsketen",
            ],
            "pl_PL": [
                "intitle:OLED OR intitle:Półprzewodnik cena niedobór",
                "intitle:Rzadkie ziemie łańcuch dostaw",
            ]
        }
    },
    
    "공급망 & 물류": {
        "description": "유럽 항만, 운송, nearshoring, 납기 변화",
        "queries": {
            "en_US": [
                "intitle:Logistics OR intitle:Shipping Strike Rotterdam Hamburg Antwerp",
                "intitle:Freight Disruption Delay Lead time Europe",
                "intitle:Nearshoring Sourcing Poland Europe",
            ],
            "de_DE": [
                "intitle:Logistik OR intitle:Schifffahrt Streik Störung Rotterdam Hamburg",
                "intitle:Lieferkettengesetz Nearshoring Lieferkette",
            ],
            "fr_FR": [
                "intitle:Logistique OR intitle:Transport Grève Perturbation Rotterdam Anvers",
                "intitle:Souveraineté industrielle Relocalisation Europe",
            ],
            "es_ES": [
                "intitle:Logística OR intitle:Envío Huelga Perturbación Rotterdam",
                "intitle:Nearshoring Localización Europa",
            ],
            "nl_NL": [
                "intitle:Logistiek OR intitle:Verzending Staking verstoring Rotterdam",
                "intitle:Toeleveringsketen Europa verstoring",
            ],
            "pl_PL": [
                "intitle:Logistyka OR intitle:Transport Strajk Zakłócenia",
                "intitle:Łańcuch dostaw Europa Polska",
            ]
        }
    },
    
    "EU 규제 & 준수": {
        "description": "ESPR, 디지털 제품 여권, AI법, 사이버 복원력법",
        "queries": {
            "en_US": [
                "intitle:ESPR OR intitle:Ecodesign Directive EU Regulation",
                "intitle:Digital Product Passport compliance mandate",
                "intitle:AI Act OR intitle:Cyber Resilience Act Right to Repair",
            ],
            "de_DE": [
                "intitle:ESPR OR intitle:Ökodesign-Richtlinie EU Verordnung",
                "intitle:Digitale Produktausweis Konformität",
                "intitle:AI-Verordnung Recht auf Reparatur",
            ],
            "fr_FR": [
                "intitle:ESPR OR intitle:Écoconception Directive UE",
                "intitle:Passeport Numérique Produit conformité",
                "intitle:Loi IA OR intitle:Droit à la réparation",
            ],
            "es_ES": [
                "intitle:ESPR OR intitle:Ecodiseño Regulación UE",
                "intitle:Pasaporte Digital Producto cumplimiento",
                "intitle:Ley IA Derecho a la reparación",
            ],
            "nl_NL": [
                "intitle:ESPR OR intitle:Ecodesign EU Regulering",
                "intitle:Digitaal Productpaspoort naleving",
                "intitle:AI-wet Recht op reparatie",
            ],
            "pl_PL": [
                "intitle:ESPR OR intitle:Dyrektywa ekoproject UE",
                "intitle:Paszport produktu cyfrowego",
                "intitle:Ustawa o sztucznej inteligencji",
            ]
        }
    },
    
    "혁신 & 기술": {
        "description": "6G, 양자, 포토닉스, 휴머노이드 로봇",
        "queries": {
            "en_US": [
                "intitle:6G OR intitle:TeraHertz Breakthrough Startup Europe",
                "intitle:Quantum OR intitle:Photonics R&D Grant Horizon Europe",
                "intitle:Humanoid OR intitle:Solid-state VC funding European",
                "intitle:RIS OR intitle:Exoskeleton Innovation breakthrough",
            ],
            "de_DE": [
                "intitle:6G OR intitle:Terahertz Durchbruch Europa",
                "intitle:Quantencomputer OR intitle:Photonik Forschung",
                "intitle:Humanoid Roboter Finanzierung Europa",
            ],
            "fr_FR": [
                "intitle:6G OR intitle:Térahertz Percée Europe",
                "intitle:Quantique OR intitle:Photonique Recherche",
                "intitle:Robot Humanoïde Financement Européen",
            ],
            "es_ES": [
                "intitle:6G OR intitle:Terahertz Avance Europa",
                "intitle:Cuántico OR intitle:Fotónica Investigación",
                "intitle:Robot Humanoide Financiación Europea",
            ],
            "nl_NL": [
                "intitle:6G OR intitle:Terahertz Doorbraak Europa",
                "intitle:Kwantum OR intitle:Fotonics Onderzoek",
                "intitle:Humanoïde robot financiering",
            ],
            "pl_PL": [
                "intitle:6G OR intitle:Terahertz Przełom Europa",
                "intitle:Kwantowy OR intitle:Fotonika Badania",
                "intitle:Robot humanoidalny finansowanie",
            ]
        }
    },
    
    "Samsung 관심사": {
        "description": "스마트홈, 웨어러블, XR, IoT, 폴더블",
        "queries": {
            "en_US": [
                "intitle:Smart-home OR intitle:IoT Innovation Trends Europe",
                "intitle:Wearable OR intitle:Smartwatch Launch Analysis",
                "intitle:XR OR intitle:AR Metaverse Consumer Tech",
                "intitle:Foldable Display Innovation Samsung competitor",
            ],
            "de_DE": [
                "intitle:Smart-Home OR intitle:IoT Innovation Europa",
                "intitle:Wearable OR intitle:Smartwatch Trend",
                "intitle:XR OR intitle:AR Metaverse",
            ],
            "fr_FR": [
                "intitle:Maison intelligente OR intitle:IoT Innovation",
                "intitle:Portable OR intitle:Montre Trend",
                "intitle:XR OR intitle:AR Métavers",
            ],
            "es_ES": [
                "intitle:Casa inteligente OR intitle:IoT Innovación",
                "intitle:Wearable OR intitle:Reloj Tendencia",
                "intitle:XR OR intitle:AR Metaverso",
            ],
            "nl_NL": [
                "intitle:Slim huis OR intitle:IoT Innovatie",
                "intitle:Draagbaar OR intitle:Smartwatch Trend",
                "intitle:XR OR intitle:AR Metaverse",
            ],
            "pl_PL": [
                "intitle:Inteligentny dom OR intitle:IoT Innowacja",
                "intitle:Urządzenie noszone OR intitle:Smartwatch Trend",
                "intitle:XR OR intitle:AR Metawersum",
            ]
        }
    }
}

REGIONS = {
    "DE": {"lang": "de", "ceid": "DE:de"},
    "FR": {"lang": "fr", "ceid": "FR:fr"},
    "ES": {"lang": "es", "ceid": "ES:es"},
    "NL": {"lang": "nl", "ceid": "NL:nl"},
    "PL": {"lang": "pl", "ceid": "PL:pl"},
}

SYSTEM_PROMPT = """You are a professional supply chain analyst for Samsung Electronics International Procurement Center.

CRITICAL TASK:
1. FIRST evaluate if article is relevant to consumer electronics components procurement
2. If NOT relevant → respond ONLY: "NOT_RELEVANT_TO_PROCUREMENT"
3. If relevant → summarize ONLY with FACTS from article in Korean, using EXACT format:

□ [헤드라인: 1-2줄 핵심 요약]
- [주요내용 1: 데이터/수치/사건]
  · [세부 1-1: 기술 근거 또는 구체적 수치]
  · [세부 1-2: 이해관계자 또는 비즈니스 임팩트]
- [주요내용 2: 다른 관점 또는 연쇄 효과]
  · [세부 2-1: 구체적 데이터/지표]
  · [세부 2-2: 조달/공급망 영향도]

RULES:
- NEVER add information not in article
- ONLY factual content with numbers/dates/companies
- Focus on Samsung procurement impact
- No speculation or assumptions
- If insufficient details → respond: "INSUFFICIENT_DETAILS"
"""

LANGUAGE_NAMES = {
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "nl": "Nederlands",
    "pl": "Polski",
}
