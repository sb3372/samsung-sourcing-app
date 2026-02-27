"""
Samsung 국제 조달센터 뉴스 수집기
다언어 유럽 뉴스 → 한국어 요약
"""

SEARCH_QUERIES = {
    "조달 & 자재": [
        "semiconductor Europe price",
        "OLED display production Europe",
        "battery manufacturing shortage",
        "rare earth materials supply",
        "chip shortage Europe 2025",
        "Halbleiter Europa Preis",
        "Halbleiter Mangel Europa",
        "production batterie Europe",
        "semiconductor prix Europe",
        "pénurie semiconducteurs",
        "escasez semiconductor Europa",
        "fabricación batería",
        "halfgeleider Europa",
        "halfgeleider tekort",
        "półprzewodnik Europa",
        "niedobór półprzewodników",
    ],
    
    "공급망 & 물류": [
        "supply chain disruption Europe",
        "port strike Rotterdam Hamburg",
        "shipping delay Europe",
        "logistics disruption",
        "nearshoring Europe manufacturing",
        "Lieferkettengesetz Europe",
        "Streik Rotterdam Hamburg",
        "Logistik Störung",
        "grève port Rotterdam",
        "perturbation logistique",
        "huelga puerto",
        "trastorno logístico",
        "staking haven",
        "verstoring logistiek",
        "strajk port",
        "zakłócenia logistyczne",
    ],
    
    "EU 규제 & 준수": [
        "ESPR ecodesign directive",
        "EU Digital Product Passport",
        "AI Act regulation compliance",
        "right to repair Europe",
        "Cyber Resilience Act",
        "ESPR Ökodesign EU",
        "Digitale Produktausweis",
        "EU AI Verordnung",
        "Recht auf Reparatur",
        "ESPR écoconception",
        "passeport numérique produit",
        "loi IA Union Européenne",
        "ecodiseño UE directiva",
        "pasaporte digital producto",
        "derecho reparación",
        "ecodesign richtlijn",
        "digitaal productpaspoort",
    ],
    
    "혁신 & 기술": [
        "6G technology Europe",
        "quantum computing breakthrough",
        "photonics innovation Europe",
        "humanoid robotics development",
        "solid-state battery",
        "6G Technologie Europa",
        "Quantencomputer Forschung",
        "Photonik Innovation",
        "Roboter Humanoid",
        "technologie 6G Europe",
        "informatique quantique",
        "photonique innovation",
        "robot humanoïde",
        "tecnología 6G Europa",
        "informática cuántica",
        "robótica humanoide",
    ],
    
    "Samsung 관심사": [
        "smart home technology",
        "wearable devices innovation",
        "XR AR metaverse",
        "foldable smartphone",
        "IoT consumer electronics",
        "Smart-Home Technologie",
        "tragbare Geräte",
        "Faltbares Telefon",
        "maison intelligente",
        "appareil portable",
        "téléphone pliable",
        "casa inteligente",
        "dispositivo wearable",
        "teléfono plegable",
        "slim huis technologie",
        "draagbare apparaten",
    ]
}

SYSTEM_PROMPT = """You are a supply chain analyst for Samsung Electronics.

TASK: Summarize this article for procurement professionals.

FILTER:
- If completely irrelevant (sports, politics, entertainment) → respond ONLY: "NOT_RELEVANT"
- Otherwise → summarize in Korean

FORMAT (use EXACTLY this format):

□ [헤드라인: 1-2줄 핵심]
- [주요내용 1]
  · [세부 1-1]
  · [세부 1-2]
- [주요내용 2]
  · [세부 2-1]
  · [세부 2-2]

RULES:
- ALWAYS respond in Korean
- Use ONLY facts from article
- Include numbers/dates/companies
- Never speculate
- If insufficient details → still provide summary
"""
