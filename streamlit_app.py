import streamlit as st
from tavily import TavilyClient
from datetime import datetime, timedelta
import os
import json
import hashlib
import re

st.set_page_config(page_title="Samsung Strategic Sourcing Agent", layout="wide")

st.markdown("""
<style>
    .header-container {
        background: linear-gradient(90deg, #1428a0 0%, #0066ff 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .header-container h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
</style>
<div class="header-container">
    <h1>🛡️ Samsung 유럽 조달 센터 전략 인텔리전스</h1>
</div>
""", unsafe_allow_html=True)

HISTORY_FILE = "article_history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"urls": set(), "hashes": set()}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {"urls": set(data.get("urls", [])), "hashes": set(data.get("hashes", []))}
    except:
        return {"urls": set(), "hashes": set()}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "urls": list(history["urls"]),
            "hashes": list(history["hashes"])
        }, f, ensure_ascii=False, indent=2)

def get_hash(content):
    content = re.sub(r'\s+', ' ', content.lower())
    return hashlib.md5(content.encode()).hexdigest()

@st.cache_data
def translate_kr(text):
    try:
        from google_trans_new import google_translator
        return google_translator().translate(text, lang_src='en', lang_tgt='ko')
    except:
        return text

# ===== 핵심: 스마트 기사 필터링 =====
def is_high_quality_article(title, content, category_name):
    """
    기사 품질 평가 (0-100)
    - 높을수록 좋은 기사
    """
    score = 0
    
    # 1. 콘텐츠 길이 (최소 500자)
    if len(content) < 500:
        return -1
    if len(content) > 300:
        score += 10
    
    # 2. 구체적인 숫자/통계 포함 (매우 중요!)
    numbers = re.findall(r'\b\d+(?:\.\d+)?[%M B billion million thousand]?\b', content)
    if len(numbers) >= 3:
        score += 30
    elif len(numbers) >= 1:
        score += 15
    
    # 3. 날짜 정보 포함
    dates = re.findall(r'\b(202[4-6]|Q[1-4]|January|February|March|April|May|June|July|August|September|October|November|December)\b', content, re.IGNORECASE)
    if len(dates) > 0:
        score += 10
    
    # 4. 기업/기관명 포함 (신뢰성)
    company_names = ['Samsung', 'ASML', 'TSMC', 'Intel', 'Qualcomm', 'Apple', 'EU', 'European', 'Germany', 'Netherlands', 'France']
    for company in company_names:
        if company.lower() in content.lower():
            score += 5
    
    # 5. 카테고리별 키워드 매칭
    category_keywords = {
        "조달 및 소재": ["semiconductor", "chip", "price", "cost", "supply", "component", "memory", "processor"],
        "공급망 및 물류": ["port", "logistics", "disruption", "strike", "shipping", "lead time", "delivery"],
        "EU 규제 및 준수": ["regulation", "compliance", "CRA", "AI Act", "ESPR", "Digital Product Passport", "cybersecurity"],
        "혁신 및 생태계": ["startup", "innovation", "6G", "robotics", "AI", "venture", "funding", "technology"],
        "Samsung 포트폴리오": ["Samsung", "telecommunication", "wearable", "consumer electronics", "device"]
    }
    
    keywords = category_keywords.get(category_name, [])
    keyword_count = sum(1 for kw in keywords if kw.lower() in content.lower())
    score += min(keyword_count * 5, 25)
    
    # 6. 중요 동사/액션 포함
    action_verbs = ['announce', 'launch', 'introduce', 'achieve', 'reach', 'surge', 'jump', 'grow', 'expand', 'partnership', 'strike', 'disrupt']
    action_count = sum(1 for verb in action_verbs if verb.lower() in content.lower())
    score += min(action_count * 3, 15)
    
    # 7. 제목과 내용의 연관성
    title_words = set(title.lower().split())
    content_first_300 = content[:300].lower()
    matching_words = sum(1 for word in title_words if word in content_first_300)
    if matching_words > len(title_words) * 0.3:
        score += 10
    
    return score

# ===== 핵심: 정교한 기사 요약 =====
def summarize_article_korean(title, content):
    """
    기사를 3개의 핵심 포인트로 정리
    포맷:
    □ 제목
    - 포인트1 (구체적인 수치 포함)
    · 설명1
    - 포인트2
    · 설명2
    - 포인트3
    · 설명3
    """
    
    # 단계 1: 핵심 정보 추출
    # 1) 숫자와 함께 나오는 문장 찾기
    sentences = re.split(r'(?<=[.!?])\s+', content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    # 각 문장 점수 계산
    def score_sentence(sent):
        score = 0
        
        # 숫자 포함 (매우 중요)
        numbers = re.findall(r'\d+\.?\d*[%M B]?', sent)
        if numbers:
            score += 50
        
        # 문장 길이 (너무 짧으면 안됨)
        if 20 < len(sent) < 200:
            score += 10
        
        # 중요 키워드
        important_words = ['increase', 'growth', 'rise', 'jump', 'surge', 'reach', 'announce', 'launch', 'expand', 'partnership', 'challenge', 'threat', 'opportunity', 'market', 'new', 'first', 'breakthrough']
        for word in important_words:
            if word.lower() in sent.lower():
                score += 3
        
        # 주어-동사-목적어 구조 (완전한 문장)
        if re.search(r'\b[A-Z][a-z]+\s+(?:has|is|are|was|were|announced|said|reported)\b', sent):
            score += 5
        
        return score
    
    scored_sentences = [(sent, score_sentence(sent)) for sent in sentences]
    scored_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)
    
    # 상위 3개 선택
    top_3 = [sent for sent, _ in scored_sentences[:3]]
    
    # 단계 2: 한국어로 번역 및 정리
    try:
        from google_trans_new import google_translator
        translator = google_translator()
        
        title_kr = translator.translate(title, lang_src='en', lang_tgt='ko')
        points_kr = [translator.translate(point, lang_src='en', lang_tgt='ko') for point in top_3]
    except:
        title_kr = title
        points_kr = top_3
    
    # 단계 3: 세부 설명 생성
    details = [
        "주요 내용 및 수치를 반영한 내용입니다.",
        "시장 변화 및 영향을 나타냅니다.",
        "향후 전망 및 의미를 담고 있습니다."
    ]
    
    # 포맷 생성
    summary = f"□ {title_kr}\n"
    for i, (point, detail) in enumerate(zip(points_kr, details)):
        # 불릿 포인트 정리
        point_clean = re.sub(r'^[-•*]\s*', '', point).strip()
        summary += f"- {point_clean}\n"
        summary += f"  · {detail}\n"
    
    return summary

# ===== 기사 검색 및 필터링 =====
def search_and_filter_articles(category_name, query, tavily_client, history, max_try=5):
    """
    1. Tavily로 검색
    2. 고품질 기사만 필터링
    3. 중복 제거
    """
    
    try:
        results = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=max_try,
            include_raw_content=True
        )
    except:
        return []
    
    filtered = []
    
    for res in results.get('results', []):
        url = res.get('url')
        title = res.get('title', '')
        content = res.get('content', '')
        
        # 기본 검증
        if not url or not content or len(content) < 200:
            continue
        
        # 중복 확인
        if url in history["urls"]:
            continue
        
        content_hash = get_hash(content)
        if content_hash in history["hashes"]:
            continue
        
        # 품질 평가
        quality_score = is_high_quality_article(title, content, category_name)
        
        if quality_score < 40:  # 최소 40점 이상
            continue
        
        filtered.append({
            "url": url,
            "title": title,
            "content": content,
            "quality": quality_score
        })
    
    # 품질순 정렬
    filtered = sorted(filtered, key=lambda x: x['quality'], reverse=True)
    
    return filtered[:2]  # 상위 2개만

# ===== UI =====
st.sidebar.header("⚙️ 설정")
tavily_key = st.sidebar.text_input("Tavily API Key", type="password")

history = load_history()
st.sidebar.markdown("---")
st.sidebar.metric("추적된 기사", len(history["urls"]))

if st.sidebar.button("🗑️ 히스토리 초기화"):
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    st.rerun()

st.markdown("---")

SEARCH_QUERIES = {
    "조달 및 소재": "Samsung Europe semiconductor chips supply price 2024 2025",
    "공급망 및 물류": "Europe port logistics disruption shipping 2024 2025",
    "EU 규제 및 준수": "EU CRA AI Act regulation compliance 2024 2025",
    "혁신 및 생태계": "Europe 6G robotics startup innovation 2024 2025",
    "Samsung 포트폴리오": "Samsung Europe semiconductor innovation announcement 2024 2025"
}

if st.button("🚀 고품질 기사 검색 시작", use_container_width=True):
    if not tavily_key:
        st.error("❌ Tavily API 키를 입력하세요.")
    else:
        client = TavilyClient(api_key=tavily_key)
        history = load_history()
        
        pbar = st.progress(0)
        status = st.empty()
        
        all_articles = []
        category_results = {}
        
        for idx, (cat_name, query) in enumerate(SEARCH_QUERIES.items()):
            status.text(f"🔍 {cat_name} 검색 중... (고품질 기사만 필터링)")
            
            # 기사 검색 및 필터링
            articles = search_and_filter_articles(cat_name, query, client, history, max_try=10)
            
            if articles:
                category_results[cat_name] = articles
                all_articles.extend(articles)
            
            pbar.progress((idx + 1) / len(SEARCH_QUERIES))
        
        pbar.empty()
        status.empty()
        
        # 통계
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("🔍 발견된 기사", len(all_articles))
        col2.metric("📂 카테고리", len(category_results))
        col3.metric("💾 총 추적", len(history["urls"]))
        
        st.markdown("---")
        
        if all_articles:
            article_num = 0
            
            for cat_name, articles in category_results.items():
                st.markdown(f"### 📂 {cat_name}")
                
                for article in articles:
                    article_num += 1
                    
                    if article_num > 10:
                        break
                    
                    # 요약 생성
                    with st.spinner(f"📝 기사 {article_num} 요약 중..."):
                        summary = summarize_article_korean(article['title'], article['content'])
                        
                        try:
                            title_kr = translate_kr(article['title'])
                        except:
                            title_kr = article['title']
                    
                    # 품질 점수 표시
                    st.markdown(f"#### 📰 {article_num}. {title_kr}")
                    st.caption(f"⭐ 품질점수: {article['quality']}/100 | 원문: {len(article['content'])}자")
                    
                    # 요약 표시
                    st.markdown(summary)
                    
                    # 버튼
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"[📖 전체 기사 읽기]({article['url']})")
                    with col2:
                        if st.button("✅ 읽음", key=f"btn_{article_num}"):
                            history["urls"].add(article['url'])
                            history["hashes"].add(get_hash(article['content']))
                            save_history(history)
                            st.success("완료!")
                    
                    st.divider()
        else:
            st.warning("⚠️ 고품질 기사를 찾을 수 없습니다. Tavily API 키를 확인하세요.")
