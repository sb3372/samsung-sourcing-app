"""
Samsung 국제 조달센터 뉴스 수집기 설정
"""

SEARCH_CATEGORIES = {
    "조달 & 자재": {
        "description": "센서, 배터리, 디스플레이, 부품 가격 변동성",
        "keywords": [
            "sensor pricing",
            "battery supply chain",
            "display panel price",
            "component shortage",
        ]
    },
    "공급망 & 물류": {
        "description": "유럽 물류 중단, 항만 파업, 납기 변화",
        "keywords": [
            "port strike Europe",
            "supply chain disruption",
            "lead time semiconductor",
            "logistics delay",
        ]
    },
    "EU 규제 & 준수": {
        "description": "ESPR, 디지털 제품 여권, EU AI 법",
        "keywords": [
            "ESPR ecodesign",
            "Digital Product Passport",
            "EU AI Act",
            "Right to Repair",
        ]
    },
    "혁신 & 에코시스템": {
        "description": "유럽 스타트업, 6G R&D, 로봇공학",
        "keywords": [
            "European tech startup",
            "6G research",
            "robotics breakthrough",
            "AI hardware",
        ]
    },
    "Samsung 관심사": {
        "description": "Samsung 제품 발표, 경쟁사 동향",
        "keywords": [
            "Samsung announcement",
            "Samsung competitor",
            "Samsung robotics",
            "Samsung 5G",
        ]
    }
}

REGIONS = {
    "US": {"lang": "en", "region": "US"},
    "Germany": {"lang": "de", "region": "DE"},
    "France": {"lang": "fr", "region": "FR"},
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
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
}
