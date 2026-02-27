"""
Samsung 국제 조달센터 전문 뉴스 수집기 설정
기술 매트릭스 기반 고급 검색 쿼리 - 데이터 손실 최소화
"""

SEARCH_QUERIES = {
    "조달 & 자재": {
        "description": "반도체, 디스플레이, 그래핀, 희토류 원자재 가격 변동성",
        "queries": {
            "en_US": [
                "intitle:OLED OR intitle:AMOLED OR intitle:MicroLED price volatility shortage",
                "intitle:Graphene OR intitle:Perovskite semiconductor production cost",
                "intitle:Rare-earth materials price shortage Europe",
                "semiconductor shortage Europe 2025",
                "battery production cost Europe",
                "display panel manufacturing Europe",
                "component sourcing Europe supply",
            ],
            "de_DE": [
                "intitle:OLED OR intitle:Halbleiter Preis Knappheit Produktion",
                "intitle:Seltene Erden Rohstoffe Lieferkettengesetz",
                "Halbleiter Mangel Europa Produktion",
                "Batterieproduktion Kosten Europa",
                "Displayherstellung Europa Versorgung",
            ],
            "fr_FR": [
                "intitle:OLED OR intitle:Semiconusductor prix volatilité",
                "intitle:Terres rares souveraineté numérique production",
                "pénurie de semiconducteurs Europe 2025",
                "production batterie coûts Europe",
                "fabrication écran Europe approvisionnement",
            ],
            "es_ES": [
                "intitle:OLED OR intitle:Semiconductores precio escasez",
                "intitle:Minerales raros cadena suministro",
                "escasez semiconductor Europa producción",
                "fabricación batería costos Europa",
            ],
            "nl_NL": [
                "intitle:OLED OR intitle:Halfgeleider prijs tekort",
                "intitle:Zeldzame aardmetalen toeleveringsketen",
                "halfgeleider tekort Europa productie",
                "batterijproductie kosten Europa",
            ],
            "pl_PL": [
                "intitle:OLED OR intitle:Półprzewodnik cena niedobór",
                "intitle:Rzadkie ziemie łańcuch dostaw",
                "niedobór półprzewodników Europa produkcja",
                "produkcja baterii koszty Europa",
            ]
        }
    },
    
    "공급망 & 물류": {
        "description": "유럽 항만, 운송, nearshoring, 납기 변화",
        "queries": {
            "en_US": [
                "intitle:Logistics OR intitle:Shipping Strike Rotterdam Hamburg Antwerp disruption",
                "intitle:Freight Disruption Delay Lead time Europe",
                "intitle:Nearshoring Sourcing Poland Europe manufacturing",
                "supply chain disruption Europe 2025",
                "port strike Rotterdam Hamburg Antwerp",
                "logistics delay semiconductor components",
                "manufacturing relocation Europe nearshoring",
            ],
            "de_DE": [
                "intitle:Logistik OR intitle:Schifffahrt Streik Störung Rotterdam Hamburg",
                "intitle:Lieferkettengesetz Nearshoring Lieferkette",
                "Streik Rotterdam Hamburg Antwerpen Logistik",
                "Lieferkettengesetz Nearshoring Polen",
                "Logistikstörung Europa Halbleiter",
            ],
            "fr_FR": [
                "intitle:Logistique OR intitle:Transport Grève Perturbation Rotterdam Anvers",
                "intitle:Souveraineté industrielle Relocalisation Europe",
                "grève port Rotterdam Anvers logistique",
                "délais de livraison Europe semi-conducteurs",
                "relocalisation fabrication Europe nearshoring",
            ],
            "es_ES": [
                "intitle:Logística OR intitle:Envío Huelga Perturbación Rotterdam",
                "intitle:Nearshoring Localización Europa",
                "huelga puerto Rotterdam Amberes logística",
                "retraso entrega Europa semiconductores",
            ],
            "nl_NL": [
                "intitle:Logistiek OR intitle:Verzending Staking verstoring Rotterdam",
                "intitle:Toeleveringsketen Europa verstoring",
                "staking haven Rotterdam Antwerpen logistiek",
                "leveringsvertragingen Europa halfgeleiders",
            ],
            "pl_PL": [
                "intitle:Logistyka OR intitle:Transport Strajk Zakłócenia",
                "intitle:Łańcuch dostaw Europa Polska",
                "strajk port Rotterdam Antwerpia logistyka",
                "opóźnienia dostaw Europa półprzewodniki",
            ]
        }
    },
    
    "EU 규제 & 준수": {
        "description": "ESPR, 디지털 제품 여권, AI법, 사이버 복원력법",
        "queries": {
            "en_US": [
                "intitle:ESPR OR intitle:Ecodesign Directive EU Regulation compliance",
                "intitle:Digital Product Passport mandate implementation",
                "intitle:AI Act OR intitle:Cyber Resilience Act Right to Repair regulation",
                "ESPR ecodesign directive EU manufacturers",
                "digital product passport implementation 2025",
                "EU AI Act compliance requirements",
                "right to repair regulation Europe",
            ],
            "de_DE": [
                "intitle:ESPR OR intitle:Ökodesign-Richtlinie EU Verordnung",
                "intitle:Digitale Produktausweis Konformität",
                "intitle:AI-Verordnung Recht auf Reparatur",
                "ESPR Ökodesign Hersteller Compliance",
                "Digitales Produktpflegepass Implementierung",
                "EU-AI-Verordnung Anforderungen Konformität",
            ],
            "fr_FR": [
                "intitle:ESPR OR intitle:Écoconception Directive UE",
                "intitle:Passeport Numérique Produit conformité",
                "intitle:Loi IA OR intitle:Droit à la réparation",
                "ESPR écoconception fabricants conformité",
                "passeport numérique produit mise en œuvre",
                "loi IA UE exigences conformité",
            ],
            "es_ES": [
                "intitle:ESPR OR intitle:Ecodiseño Regulación UE",
                "intitle:Pasaporte Digital Producto cumplimiento",
                "intitle:Ley IA Derecho a la reparación",
                "ESPR ecodiseño fabricantes conformidad",
                "pasaporte digital producto implementación",
            ],
            "nl_NL": [
                "intitle:ESPR OR intitle:Ecodesign EU Regulering",
                "intitle:Digitaal Productpaspoort naleving",
                "intitle:AI-wet Recht op reparatie",
                "ESPR ecodesign fabrikanten compliance",
                "digitaal productpaspoort implementatie",
            ],
            "pl_PL": [
                "intitle:ESPR OR intitle:Dyrektywa ekoproject UE",
                "intitle:Paszport produktu cyfrowego",
                "intitle:Ustawa o sztucznej inteligencji",
                "ESPR ekodesign producenci zgodność",
                "paszport produktu cyfrowego implementacja",
            ]
        }
    },
    
    "혁신 & 기술": {
        "description": "6G, 양자, 포토닉스, 휴머노이드 로봇, 고급 센서",
        "queries": {
            "en_US": [
                "intitle:6G OR intitle:TeraHertz Breakthrough Startup Europe",
                "intitle:Quantum OR intitle:Photonics R&D Grant Horizon Europe",
                "intitle:Humanoid OR intitle:Solid-state VC funding European",
                "intitle:RIS OR intitle:Exoskeleton Innovation breakthrough",
                "6G technology development Europe research",
                "quantum computing breakthrough Europe startup",
                "photonics innovation European companies",
                "humanoid robotics development Europe funding",
            ],
            "de_DE": [
                "intitle:6G OR intitle:Terahertz Durchbruch Europa",
                "intitle:Quantencomputer OR intitle:Photonik Forschung",
                "intitle:Humanoid Roboter Finanzierung Europa",
                "6G Technologie Entwicklung Europa Forschung",
                "Quantencomputer Durchbruch Europa Startup",
                "Photonik Innovation europäische Unternehmen",
            ],
            "fr_FR": [
                "intitle:6G OR intitle:Térahertz Percée Europe",
                "intitle:Quantique OR intitle:Photonique Recherche",
                "intitle:Robot Humanoïde Financement Européen",
                "technologie 6G développement Europe recherche",
                "informatique quantique percée Europe startup",
                "photonique innovation entreprises européennes",
            ],
            "es_ES": [
                "intitle:6G OR intitle:Terahertz Avance Europa",
                "intitle:Cuántico OR intitle:Fotónica Investigación",
                "intitle:Robot Humanoide Financiación Europea",
                "tecnología 6G desarrollo Europa investigación",
                "informática cuántica avance Europa startup",
            ],
            "nl_NL": [
                "intitle:6G OR intitle:Terahertz Doorbraak Europa",
                "intitle:Kwantum OR intitle:Fotonics Onderzoek",
                "intitle:Humanoïde robot financiering",
                "6G-technologie ontwikkeling Europa onderzoek",
                "kwantumcomputing doorbraak Europa startup",
            ],
            "pl_PL": [
                "intitle:6G OR intitle:Terahertz Przełom Europa",
                "intitle:Kwantowy OR intitle:Fotonika Badania",
                "intitle:Robot humanoidalny finansowanie",
                "technologia 6G rozwój Europa badania",
                "obliczenia kwantowe przełom Europa startup",
            ]
        }
    },
    
    "Samsung 관심사": {
        "description": "스마트홈, 웨어러블, XR, IoT, 폴더블, 경쟁사 동향",
        "queries": {
            "en_US": [
                "intitle:Smart-home OR intitle:IoT Innovation Trends Europe",
                "intitle:Wearable OR intitle:Smartwatch Launch Analysis market",
                "intitle:XR OR intitle:AR Metaverse Consumer Tech developments",
                "intitle:Foldable Display Innovation Samsung competitor",
                "smart home technology trend Europe 2025",
                "wearable device innovation market analysis",
                "extended reality XR AR consumer technology",
                "foldable smartphone technology Samsung Apple",
            ],
            "de_DE": [
                "intitle:Smart-Home OR intitle:IoT Innovation Europa",
                "intitle:Wearable OR intitle:Smartwatch Trend",
                "intitle:XR OR intitle:AR Metaverse",
                "intitle:Faltbar Smartphone Innovation Konkurrenz",
                "Smart-Home Technologie Trend Europa",
                "tragbares Gerät Innovation Marktanalyse",
            ],
            "fr_FR": [
                "intitle:Maison intelligente OR intitle:IoT Innovation",
                "intitle:Portable OR intitle:Montre Trend",
                "intitle:XR OR intitle:AR Métavers",
                "intitle:Téléphone Pliable Innovation Concurrence",
                "maison intelligente technologie tendance Europe",
                "appareil portable innovation analyse marché",
            ],
            "es_ES": [
                "intitle:Casa inteligente OR intitle:IoT Innovación",
                "intitle:Wearable OR intitle:Reloj Tendencia",
                "intitle:XR OR intitle:AR Metaverso",
                "intitle:Teléfono Plegable Innovación Competencia",
                "casa inteligente tecnología tendencia Europa",
            ],
            "nl_NL": [
                "intitle:Slim huis OR intitle:IoT Innovatie",
                "intitle:Draagbaar OR intitle:Smartwatch Trend",
                "intitle:XR OR intitle:AR Metaverse",
                "intitle:Opvouwbare Telefoon Innovatie Concurrentie",
                "slim huis technologie trend Europa",
            ],
            "pl_PL": [
                "intitle:Inteligentny dom OR intitle:IoT Innowacja",
                "intitle:Urządzenie noszone OR intitle:Smartwatch Trend",
                "intitle:XR OR intitle:AR Metawersum",
                "intitle:Telefon Składany Innowacja Konkurencja",
                "inteligentny dom technologia trend Europa",
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

SYSTEM_PROMPT = """당신은 Samsung Electronics 국제 조달센터의 공급망 분석가입니다.

【작업】
이 기사를 조달 전문가 관점에서 요약하세요.

【필터링】
기사가 기술/제조와 완전히 무관한 경우만 (예: 스포츠, 정치) → "NOT_RELEVANT_TO_PROCUREMENT" 응답

【그 외 모든 경우】
기사의 사실만 사용하여 아래 정확한 형식으로 한국어 요약:

□ [헤드라인: 1-2줄 핵심 요약]
- [주요내용 1: 주요 사건/수치/발전사항]
  · [세부 1-1: 기술적 근거 또는 회사명/인물명]
  · [세부 1-2: 비즈니스 임팩트 또는 구체적 수치]
- [주요내용 2: 다른 관점 또는 연쇄 효과]
  · [세부 2-1: 구체적 수치/날짜/백분율]
  · [세부 2-2: 공급망 또는 산업 영향도]

【규칙】
- 항상 한국어로 응답
- 기사에 없는 정보 추가 금지
- 구체적 수치/날짜/회사명 포함
- 정보 부족해도 요약 제공 (정보 부족은 필터링 이유 아님)
- "NOT_RELEVANT_TO_PROCUREMENT"는 완전 무관한 것만
"""

LANGUAGE_NAMES = {
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "nl": "Nederlands",
    "pl": "Polski",
}
