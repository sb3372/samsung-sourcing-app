"""
Samsung 국제 조달센터 뉴스 수집기 설정
"""

SEARCH_CATEGORIES = {
    "조달 & 자재": {
        "description": "센서, 배터리, 디스플레이, 부품 가격 변동성",
        "keywords": [
            "European sensor manufacturing",
            "European battery supply chain",
            "Europe display panel production",
            "Europe component shortage",
        ]
    },
    "공급망 & 물류": {
        "description": "유럽 물류 중단, 항만 파업, 납기 변화",
        "keywords": [
            "Europe port strike",
            "European supply chain disruption",
            "Europe semiconductor lead time",
            "European logistics delay",
        ]
    },
    "EU 규제 & 준수": {
        "description": "ESPR, 디지털 제품 여권, EU AI 법",
        "keywords": [
            "EU ESPR ecodesign directive",
            "EU Digital Product Passport",
            "European AI Act compliance",
            "EU Right to Repair",
        ]
    },
    "혁신 & 에코시스템": {
        "description": "유럽 스타트업, 6G R&D, 로봇공학",
        "keywords": [
            "European tech startup investment",
            "Europe 6G research development",
            "European robotics innovation",
            "Europe AI hardware manufacturing",
        ]
    },
    "Samsung 관심사": {
        "description": "Samsung 제품 발표, 경쟁사 동향",
        "keywords": [
            "Samsung Europe announcement",
            "Samsung European competitor",
            "Samsung Europe factory",
            "Samsung Europe market",
        ]
    }
}

REGIONS = {
    "Germany": {"lang": "de", "region": "DE"},
    "France": {"lang": "fr", "region": "FR"},
    "Spain": {"lang": "es", "region": "ES"},
}

SYSTEM_PROMPT = """You are a professional business analyst for Samsung Electronics.

YOUR TASK:
1. Check if this article is relevant to consumer electronics procurement.
2. If NOT relevant, respond with: "NOT_RELEVANT"
3. If relevant, summarize in Korean with this EXACT format:

□ [헤드라인: 핵심 한 줄]
- [주요 내용 1]
  · [세부 1-1]
  · [세부 1-2]
- [주요 내용 2]
  · [세부 2-1]
  · [세부 2-2]

IMPORTANT: Only use facts from the article. No speculation."""

LANGUAGE_NAMES = {
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
}
