import streamlit as st
import time
import logging
from config import WEBSITES, CATEGORIES
from crawler import WebCrawler
from deduplicator import Deduplicator
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 페이지 설정
st.set_page_config(page_title="Samsung 뉴스", page_icon="📰", layout="wide")

# 세션 상태 초기화
if "articles" not in st.session_state:
    st.session_state.articles = []
if "deduplicator" not in st.session_state:
    st.session_state.deduplicator = Deduplicator()

# 제목
st.title("📰 Samsung 국제 조달센터")
st.markdown("유럽 기술 뉴스 - 자동 한국어 요약")
st.markdown("---")

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    
    # Gemini API 키
    api_key = st.text_input(
        "🔑 Gemini API 키",
        type="password",
        help="https://aistudio.google.com/app/apikey에서 발급"
    )
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            st.session_state.gemini_key = api_key
            st.success("✅ API 연결 완료")
        except Exception as e:
            st.error(f"❌ API 오류: {str(e)[:50]}")
    
    st.markdown("---")
    
    # 카테고리 선택
    st.header("📂 카테고리 선택")
    selected_categories = []
    
    for category in CATEGORIES:
        if st.checkbox(category, value=True):
            selected_categories.append(category)
    
    st.session_state.selected_categories = selected_categories

# 메인 콘텐츠
st.header("🔄 뉴스 수집")

# REFRESH 버튼
if st.button("🔄 새로운 기사 로드", use_container_width=True, type="primary"):
    
    # API 키 확인
    if "gemini_key" not in st.session_state:
        st.error("❌ API 키를 먼저 입력하세요")
    elif not st.session_state.selected_categories:
        st.error("❌ 카테고리를 선택하세요")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 1단계: 웹 크롤링
            status_text.text("🔗 웹사이트 크롤링 중...")
            logger.info("크롤링 시작")
            
            crawler = WebCrawler()
            all_articles = []
            
            for idx, website in enumerate(WEBSITES):
                progress = (idx + 1) / len(WEBSITES)
                progress_bar.progress(min(progress, 0.99))
                status_text.text(f"크롤링 중: {website['name']} ({idx + 1}/{len(WEBSITES)})")
                
                articles = crawler.crawl_website(website)
                all_articles.extend(articles)
                time.sleep(0.5)  # 서버 부하 방지
            
            logger.info(f"총 {len(all_articles)}개 기사 수집")
            status_text.text(f"✅ {len(all_articles)}개 기사 수집 완료")
            
            # 2단계: 카테고리 필터링
            status_text.text("📂 카테고리 필터링 중...")
            filtered_articles = []
            
            for article in all_articles:
                # 선택된 카테고리와 겹치는지 확인
                if any(cat in article['categories'] for cat in st.session_state.selected_categories):
                    filtered_articles.append(article)
            
            logger.info(f"필터링 후 {len(filtered_articles)}개 기사")
            status_text.text(f"📂 {len(filtered_articles)}개 기사 필터링 완료")
            
            # 3단계: Gemini로 제목 번역 + 요약
            status_text.text("🤖 Gemini AI 처리 중...")
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            processed_articles = []
            
            for idx, article in enumerate(filtered_articles):
                progress = (idx + 1) / len(filtered_articles)
                progress_bar.progress(min(progress, 0.99))
                status_text.text(f"AI 처리: {idx + 1}/{len(filtered_articles)}")
                
                try:
                    # 중복 확인
                    if st.session_state.deduplicator.is_duplicate(article):
                        logger.info(f"중복 제외: {article['title_en'][:50]}")
                        continue
                    
                    # 기사 본문 추출 (크롤러가 이미 했으므로 링크에서 가져옴)
                    # 여기서는 제목만 사용
                    
                    # Gemini 프롬프트
                    prompt = f"""당신은 Samsung의 뉴스 번역 전문가입니다.

다음 영어 기사 제목을 한국어로 번역하고, 매우 짧은 요약을 작성하세요.

원문: {article['title_en']}

응답 형식 (반드시 이 형식 유지):
제목_한국어: [한국어 제목]
요약: [1-2줄 요약]"""

                    response = model.generate_content(prompt)
                    result_text = response.text.strip()
                    
                    # 파싱
                    lines = result_text.split('\n')
                    title_ko = "제목 없음"
                    summary = "요약 없음"
                    
                    for line in lines:
                        if "제목_한국어:" in line:
                            title_ko = line.replace("제목_한국어:", "").strip()
                        elif "요약:" in line:
                            summary = line.replace("요약:", "").strip()
                    
                    # 기사 저장
                    processed_article = {
                        'title_ko': title_ko,
                        'title_en': article['title_en'],
                        'link': article['link'],
                        'source': article['source'],
                        'categories': article['categories'],
                        'summary': summary,
                        'category': article['categories'][0] if article['categories'] else "Unknown"
                    }
                    
                    processed_articles.append(processed_article)
                    
                    # CSV에 저장
                    st.session_state.deduplicator.save_article({
                        'title_en': article['title_en'],
                        'link': article['link'],
                        'source': article['source'],
                        'categories': ','.join(article['categories'])
                    })
                    
                    logger.info(f"처리 완료: {title_ko[:50]}")
                    time.sleep(0.3)
                
                except Exception as e:
                    logger.error(f"AI 처리 오류: {str(e)[:50]}")
                    continue
            
            progress_bar.progress(1.0)
            status_text.text(f"✅ {len(processed_articles)}개 기사 준비 완료!")
            
            st.session_state.articles = processed_articles
            
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
            st.success(f"✅ {len(processed_articles)}개 기사 로드 완료!")
        
        except Exception as e:
            st.error(f"❌ 오류 발생: {str(e)}")
            logger.error(f"전체 오류: {str(e)}")

# 기사 표시
st.markdown("---")

if st.session_state.articles:
    st.header(f"📊 수집된 기사 ({len(st.session_state.articles)}개)")
    
    for idx, article in enumerate(st.session_state.articles, 1):
        with st.container():
            # 제목 (한국어 + 원문 작은 글씨)
            st.subheader(article['title_ko'])
            st.caption(f"_원제목: {article['title_en']}_")
            
            # 요약
            st.markdown(article['summary'])
            
            # 메타정보
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"📂 {article['category']}")
            with col2:
                st.caption(f"출처: {article['source']}")
            with col3:
                st.markdown(f"[🔗 원문]({article['link']})")
            
            st.divider()

else:
    st.info("🔄 '새로운 기사 로드' 버튼을 클릭하여 기사를 수집하세요")
