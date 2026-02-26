"""
Samsung 국제 조달센터 뉴스 수집기 설정
"""

SEARCH_CATEGORIES = {
    "조달 & 자재": {
        "description": "반도체, 디스플레이, 배터리, 센서 등 가격 변동성과 공급 가능성",
        "keywords": [
            "sensor pricing OR sensor shortage",
            "battery supply chain OR battery shortage",
            "display panel price OR display component",
            "component shortage OR component pricing",
            "semiconductor supply OR chip shortage",
            "connector pricing OR connector shortage",
            "camera module price OR optical sensor",
            "wireless module 5G OR 6G component",
            "mechanical component manufacturing",
            "raw material price index",
        ]
    },
    "공급망 & 물류": {
        "description": "유럽 물류 중단, 항만 파업, 납기 변화, 중국 소싱 변화",
        "keywords": [
            "port strike Europe OR logistics disruption",
            "supply chain disruption consumer electronics",
            "lead time semiconductor OR component",
            "nearshoring Europe manufacturing",
            "China sourcing alternative OR reshoring",
            "European logistics delay",
            "customs clearance delay",
            "transportation cost increase",
            "inventory shortage consumer tech",
            "shipping port congestion",
        ]
    },
    "EU 규제 & 준수": {
        "description": "ESPR, 디지털 제품 여권, EU AI 법, 사이버 복원력 법",
        "keywords": [
            "ESPR ecodesign OR Digital Product Passport",
            "EU AI Act consumer electronics",
            "Cyber Resilience Act CRA compliance",
            "EU energy labeling consumer appliances",
            "Right to Repair EU OR repairability requirement",
            "Extended Producer Responsibility EPR",
            "EU compliance consumer electronics",
            "GDPR data privacy wearable",
            "EU battery regulation OR battery directive",
            "sustainability regulation consumer tech",
        ]
    },
    "혁신 & 에코시스템": {
        "description": "유럽 스타트업, 6G R&D, 로봇공학, AI 하드웨어, VC 투자",
        "keywords": [
            "European tech startup funding OR AI startup",
            "6G research development breakthrough",
            "robotics breakthrough OR robot innovation",
            "AI-native hardware OR edge AI device",
            "sustainable materials electronics OR bio-materials",
            "venture capital investment consumer tech",
            "deep-tech government grant Europe",
            "quantum computing sensor OR quantum device",
            "smart home innovation OR IoT breakthrough",
            "augmented reality hardware OR mixed reality device",
        ]
    },
    "Samsung 관심사": {
        "description": "Samsung 제품 발표, 경쟁사 동향, 신흥 카테고리",
        "keywords": [
            "Samsung announcement OR Samsung product launch",
            "Samsung competitor smartphone OR wearable",
            "Samsung robotics OR service robot",
            "Samsung display technology OR display innovation",
            "Samsung battery technology OR energy storage",
            "Samsung sensor technology breakthrough",
            "Samsung 5G OR 6G development",
            "Samsung supply chain management",
            "Samsung sustainability initiative",
            "Samsung emerging market strategy",
        ]
    }
}

REGIONS = {
    "US": {"lang": "en", "region": "US"},
    "Germany": {"lang": "de", "region": "DE"},
    "France": {"lang": "fr", "region": "FR"},
    "Spain": {"lang": "es", "region": "ES"},
    "Netherlands": {"lang": "nl", "region": "NL"},
    "Poland": {"lang": "pl", "region": "PL"},
}

SYSTEM_PROMPT = """You are a professional business analyst for Samsung Electronics International Procurement Center.

YOUR CRITICAL TASK:
1. FIRST, evaluate if this article is RELEVANT to consumer electronics components procurement (sensors, batteries, displays, connectivity modules, cameras, audio components, mechanical parts for smartphones, tablets, wearables, home appliances, IoT devices, etc.)
2. If NOT relevant to procurement, respond with EXACTLY: "NOT_RELEVANT_TO_PROCUREMENT"
3. If relevant, translate and summarize ONLY using facts from the article into Korean following this EXACT format:

□ [헤드라인: 핵심을 한 줄로 - 3-5단어]
- [주요 내용 1: 데이터/사건/돌파구]
  · [세부 1-1: 기술 근거 또는 구체적 수치]
  · [세부 1-2: 이해관계자 또는 인과관계]
- [주요 내용 2: 다른 관점의 주요 사항]
  · [세부 2-1: 기술 근거 또는 구체적 수치]
  · [세부 2-2: 이해관계자 또는 인과관계]

CRITICAL RULES:
- NEVER add information not in the article
- ONLY use facts and data explicitly mentioned in the article
- If article lacks enough detail for 2 main points with details, respond: "INSUFFICIENT_DETAILS"
- Use bullet points exactly as shown
- Write in professional Korean for procurement professionals
- Focus on impact to Samsung procurement and supply chain decisions
- Do NOT include speculation or assumptions
- Do NOT add strategic impact section"""

LANGUAGE_NAMES = {
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "nl": "Nederlands",
    "pl": "Polski",
}
