"""
웹 크롤러 - RSS 피드 기반 기사 수집
"""
import feedparser
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime, timezone
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FETCH_TIMEOUT = 15


def _parse_published(entry) -> datetime:
    """RSS entry에서 published datetime 추출 (UTC-aware)"""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def _strip_html(html: str) -> str:
    """HTML 태그 제거 후 텍스트 반환"""
    if not html:
        return ""
    try:
        return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)
    except Exception:
        return html


def _ensure_utc(dt: datetime) -> datetime:
    """datetime을 UTC-aware로 변환"""
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _fetch_feed(website: Dict, since_date: datetime, until_date: datetime) -> List[Dict]:
    """단일 RSS 피드에서 기사 수집"""
    name = website["name"]
    rss_url = website["rss"]
    articles = []
    since = _ensure_utc(since_date)
    until = _ensure_utc(until_date)
    try:
        feed = feedparser.parse(rss_url, agent="Mozilla/5.0", request_headers={"Connection": "close"})
        if feed.get("bozo") and not feed.get("entries"):
            logger.warning(f"⚠️ {name}: RSS 파싱 오류 (bozo={feed.bozo_exception})")
            return []
        for entry in feed.entries:
            try:
                pub_dt = _parse_published(entry)
                if not (since <= pub_dt < until):
                    continue
                title = _strip_html(getattr(entry, "title", "")).strip()
                if not title:
                    continue
                link = getattr(entry, "link", "").strip()
                if not link:
                    continue
                # content: summary 또는 description
                raw_content = (
                    getattr(entry, "summary", "")
                    or getattr(entry, "description", "")
                    or ""
                )
                content = _strip_html(raw_content)[:2000]
                articles.append({
                    "title": title,
                    "link": link,
                    "source": name,
                    "content": content,
                    "published_at": pub_dt.isoformat(),
                    "crawled_at": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as e:
                logger.debug(f"⚠️ {name} entry 오류: {e}")
                continue
        logger.info(f"✅ {name}: {len(articles)}개 기사 수집")
    except Exception as e:
        logger.warning(f"⚠️ {name}: 피드 수집 실패 - {str(e)[:80]}")
    return articles


def crawl_all(websites: List[Dict], since_date: datetime, until_date: datetime) -> List[Dict]:
    """모든 RSS 피드에서 기사 병렬 수집 후 URL 중복 제거"""
    all_articles: List[Dict] = []
    seen_links: set = set()

    logger.info(f"🚀 {len(websites)}개 사이트 RSS 크롤링 시작 ({since_date.date()} ~ {until_date.date()})")

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(_fetch_feed, site, since_date, until_date): site
            for site in websites
        }
        for future in as_completed(futures, timeout=FETCH_TIMEOUT * 2):
            site = futures[future]
            try:
                articles = future.result(timeout=FETCH_TIMEOUT)
                for a in articles:
                    if a["link"] not in seen_links:
                        seen_links.add(a["link"])
                        all_articles.append(a)
            except Exception as e:
                logger.warning(f"⚠️ {site['name']}: {str(e)[:60]}")

    logger.info(f"📊 총 {len(all_articles)}개 기사 수집 완료")
    return all_articles
