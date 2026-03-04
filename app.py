"""
Streamlit 웹 앱 - Samsung Electronics Europe IPC
"""
import streamlit as st
import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from config import CATEGORIES, WEBSITES
import crawler
from ai import AIProcessor, _jaccard_similarity
import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Samsung Electronics Europe IPC",
    page_icon="📱",
    layout="wide",
)

st.markdown("""
<style>
.article-title { font-size: 1.2rem; font-weight: 600; color: #1e88e5; margin-bottom: 0.3rem; }
.article-summary { font-size: 0.95rem; color: #333; line-height: 1.5; margin-bottom: 0.5rem; }
.badge-source { background: #e3f2fd; padding: 0.2rem 0.6rem; border-radius: 4px;
                display: inline-block; margin-right: 0.4rem; font-size: 0.8rem; }
.badge-cat { background: #1e88e5; color: white; padding: 0.2rem 0.6rem; border-radius: 4px;
             display: inline-block; margin-right: 0.4rem; font-size: 0.8rem; }
.divider { margin: 1rem 0; border-top: 1px solid #eee; }
</style>
""", unsafe_allow_html=True)

# ── DB 초기화 ──────────────────────────────────────────────────────────────
db.init_db()

# ── 세션 상태 기본값 ────────────────────────────────────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "current_week" not in st.session_state:
    st.session_state.current_week = 0
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "전체"
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
if "crawled_weeks" not in st.session_state:
    st.session_state.crawled_weeks = set()


# ── 사이드바 ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ 설정")

    env_key = os.environ.get("GEMINI_API_KEY", "")
    try:
        env_key = env_key or st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        pass

    if env_key:
        st.session_state.api_key = env_key
        st.success("✅ API 키 설정됨")
    else:
        raw = st.text_input(
            "🔑 Gemini API Key 입력",
            type="password",
            value=st.session_state.api_key,
            placeholder="AIza...",
        )
        if raw:
            st.session_state.api_key = raw

    st.divider()
    if st.button("🗑️ DB 초기화"):
        db.clear_articles()
        st.session_state.current_week = 0
        st.session_state.selected_category = "전체"
        st.session_state.current_page = 0
        st.session_state.crawled_weeks = set()
        st.rerun()


# ── 메인 헤더 ────────────────────────────────────────────────────────────────
st.title("📱 Samsung Electronics Europe IPC")
st.markdown("유럽 기술 뉴스 - AI 기반 분류")

api_key = st.session_state.api_key
if not api_key:
    st.warning("API 키를 사이드바에 입력하세요")
    st.stop()

# API key hash (SHA-256)
api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()


# ── 유틸: 중복 제거 ──────────────────────────────────────────────────────────
def deduplicate(new_articles: List[Dict], existing_articles: List[Dict]) -> List[Dict]:
    final = []
    all_existing = list(existing_articles)
    for article in new_articles:
        is_dup = False
        for other in all_existing:
            if _jaccard_similarity(
                f"{article.get('title','')} {article.get('content','')}",
                f"{other.get('title','')} {other.get('content','')}",
            ) >= 0.5:
                is_dup = True
                break
        if not is_dup:
            final.append(article)
            all_existing.append(article)
    return final


# ── 크롤 함수 ────────────────────────────────────────────────────────────────
def run_crawl(week_offset: int):
    now = datetime.now(timezone.utc)
    until_date = now - timedelta(days=7 * week_offset)
    since_date = now - timedelta(days=7 * (week_offset + 1))

    with st.spinner(f"⏳ 기사 크롤링 중... (최근 {week_offset + 1}주차)"): 
        articles = crawler.crawl_all(WEBSITES, since_date, until_date)

    st.info(f"📰 {len(articles)}개 기사 수집됨")

    if not articles:
        st.warning("수집된 기사가 없습니다.")
        st.session_state.crawled_weeks.add(week_offset)
        return

    with st.spinner("🤖 AI 분류 중... (수 분 소요될 수 있습니다)"): 
        ai = AIProcessor(api_key)
        processed = ai.process_articles_parallel(articles, max_workers=5)

    europe_articles = [a for a in processed if a.get("is_europe_relevant")]
    existing = db.get_articles(week_offset)
    final = deduplicate(europe_articles, existing)
    db.insert_articles(final, week_offset)
    st.session_state.crawled_weeks.add(week_offset)
    st.success(f"✅ {len(final)}개 유럽 관련 기사 저장됨")


# ── 최초 실행: DB에 기사가 없으면 버튼으로 크롤 시작 ──────────────────────────
if not db.has_properly_categorized_articles() and 0 not in st.session_state.crawled_weeks:
    st.info("📭 아직 수집된 기사가 없습니다. 아래 버튼을 눌러 최근 1주일 기사를 불러오세요.")
    if st.button("🚀 기사 불러오기 (최근 1주일)", type="primary", use_container_width=True):
        run_crawl(0)
        st.rerun()
    st.stop()


# ── 기사 로드 및 필터 ────────────────────────────────────────────────────────
max_week = st.session_state.current_week
all_articles: List[Dict] = []
for w in range(max_week + 1):
    all_articles.extend(db.get_articles(w))

# 읽은 기사 제외
read_links = db.get_read_links(api_key_hash)
all_articles = [a for a in all_articles if a["link"] not in read_links]

# 카테고리 필터 버튼
col_buttons = st.columns([1] + [2] * len(CATEGORIES))
with col_buttons[0]:
    if st.button("전체", use_container_width=True,
                 type="primary" if st.session_state.selected_category == "전체" else "secondary"):
        st.session_state.selected_category = "전체"
        st.session_state.current_page = 0
        st.rerun()

for i, cat in enumerate(CATEGORIES):
    with col_buttons[i + 1]:
        btn_type = "primary" if st.session_state.selected_category == cat else "secondary"
        if st.button(cat, use_container_width=True, type=btn_type):
            st.session_state.selected_category = cat
            st.session_state.current_page = 0
            st.rerun()

# 카테고리 필터 적용
selected = st.session_state.selected_category
if selected != "전체":
    filtered_articles = [a for a in all_articles if selected in a.get("categories", [])]
else:
    filtered_articles = all_articles

# ── 페이지네이션 ─────────────────────────────────────────────────────────────
PAGE_SIZE = 10
total = len(filtered_articles)
total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
current_page = min(st.session_state.current_page, total_pages - 1)

st.markdown(f"**총 {total}개 기사** · 페이지 {current_page + 1}/{total_pages}")

start = current_page * PAGE_SIZE
page_articles = filtered_articles[start: start + PAGE_SIZE]

if not page_articles:
    st.info("📥 표시할 기사가 없습니다.")
else:
    for article in page_articles:
        link = article.get("link", "#")
        title = article.get("title", "제목 없음")
        source = article.get("source", "")

        st.markdown(
            f"<div class='article-title'><a href='{link}' target='_blank'>{title}</a></div>",
            unsafe_allow_html=True,
        )

        meta = f"<span class='badge-source'>📰 {source}</span>"
        for cat in article.get("categories", []):
            meta += f"<span class='badge-cat'>📁 {cat}</span>"
        pub = article.get("published_at", "")[:10]
        if pub:
            meta += f"<span style='color:#888;font-size:0.8rem;margin-left:0.5rem'>{pub}</span>"
        st.markdown(meta, unsafe_allow_html=True)

        # 기사 읽음 처리
        db.mark_read(api_key_hash, link)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ── 페이지 이동 버튼 ──────────────────────────────────────────────────────────
col_prev, col_next = st.columns(2)
with col_prev:
    if current_page > 0:
        if st.button("⬅️ 이전"):
            st.session_state.current_page = current_page - 1
            st.rerun()

with col_next:
    if current_page < total_pages - 1:
        if st.button("다음 ➡️"):
            st.session_state.current_page = current_page + 1
            st.rerun()

# ── 마지막 페이지에 "1주일 더 로딩" 버튼 ────────────────────────────────────
is_last_page = current_page == total_pages - 1
is_last_week = max_week == db.get_max_week_offset()

if is_last_page and is_last_week:
    st.divider()
    if st.button("📅 1주일 더 로딩"):
        next_week = max_week + 1
        st.session_state.current_week = next_week
        run_crawl(next_week)
        st.session_state.current_page = 0
        st.rerun()