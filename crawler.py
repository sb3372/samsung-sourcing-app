"""
웹 크롤러 - RSS 우선, 1주일 이내 기사만 수집
"""
import requests
import feedparser
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _parse_date(entry) -> Optional[datetime]:
    """feedparser entry에서 published 날짜 추출"""
    for attr in ('published_parsed', 'updated_parsed'):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


class WebCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.timeout = 15
        self.processed_urls = set()
        self.url_lock = threading.Lock()

    def _crawl_rss(self, website_config: Dict) -> List[Dict]:
        """RSS 피드에서 1주일 이내 기사 추출"""
        articles = []
        try:
            feed = feedparser.parse(website_config['news_page'])
            one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            for entry in feed.entries:
                pub_date = _parse_date(entry)
                # If we can't determine the date, include it (be inclusive)
                if pub_date and pub_date < one_week_ago:
                    continue

                title = getattr(entry, 'title', '').strip()
                link = getattr(entry, 'link', '').strip()
                if not title or len(title) < 5 or not link:
                    continue

                with self.url_lock:
                    if link in self.processed_urls:
                        continue
                    self.processed_urls.add(link)

                # Use RSS summary as content — no extra HTTP request needed
                content = ''
                for attr in ('summary', 'description', 'content'):
                    val = getattr(entry, attr, None)
                    if val:
                        if isinstance(val, list):
                            val = val[0].get('value', '')
                        content = BeautifulSoup(str(val), 'html.parser').get_text(strip=True)[:1000]
                        break

                articles.append({
                    'title': title,
                    'link': link,
                    'source': website_config['name'],
                    'content': content,
                    'crawled_at': datetime.now(timezone.utc).isoformat(),
                    'published_at': pub_date.isoformat() if pub_date else '',
                })

        except Exception as e:
            logger.error(f"❌ RSS 오류 [{website_config['name']}]: {str(e)[:100]}")
        return articles

    def _crawl_html(self, website_config: Dict) -> List[Dict]:
        """HTML 스크래핑으로 기사 추출 (RSS 없는 사이트용)"""
        articles = []
        try:
            response = requests.get(
                website_config['news_page'],
                headers=self.headers,
                timeout=self.timeout
            )
            response.encoding = 'utf-8'
            if response.status_code != 200:
                logger.warning(f"❌ {website_config['name']}: HTTP {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            article_elements = soup.select(website_config.get('article_selector', 'article'))

            if not article_elements:
                for sel in ["article", "div[class*='article']", "div[class*='news']", "li.news"]:
                    article_elements = soup.select(sel)
                    if len(article_elements) > 3:
                        break

            for elem in article_elements[:50]:
                try:
                    title_elem = elem.select_one(website_config.get('title_selector', 'h2 a'))
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    if not title or len(title) < 5:
                        continue

                    link_elem = elem.select_one(website_config.get('link_selector', 'a'))
                    link = link_elem.get('href', '') if link_elem else ''
                    if not link:
                        continue

                    if link.startswith('/'):
                        link = website_config['url'].rstrip('/') + link
                    elif not link.startswith('http'):
                        link = website_config['url'].rstrip('/') + '/' + link

                    with self.url_lock:
                        if link in self.processed_urls:
                            continue
                        self.processed_urls.add(link)

                    articles.append({
                        'title': title,
                        'link': link,
                        'source': website_config['name'],
                        'content': '',
                        'crawled_at': datetime.now(timezone.utc).isoformat(),
                        'published_at': '',
                    })
                except Exception:
                    continue

        except Exception as e:
            logger.error(f"❌ HTML 오류 [{website_config['name']}]: {str(e)[:100]}")
        return articles

    def crawl_website(self, website_config: Dict) -> List[Dict]:
        """사이트 크롤링 (RSS 우선)"""
        logger.info(f"🔗 크롤링: {website_config['name']}")
        if website_config.get('use_rss', False):
            return self._crawl_rss(website_config)
        return self._crawl_html(website_config)

    def crawl_all_websites(self, websites: List[Dict], max_workers: int = 20) -> List[Dict]:
        return self.crawl_all_websites_optimized(websites, max_workers=max_workers)

    def crawl_all_websites_optimized(self, websites: List[Dict], max_workers: int = 20) -> List[Dict]:
        """모든 웹사이트 병렬 크롤링 (RSS 기반, 1주일 이내 기사만)"""
        all_articles = []
        logger.info(f"🚀 {len(websites)}개 사이트 병렬 크롤링 시작")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_site = {
                executor.submit(self.crawl_website, site): site
                for site in websites
            }
            for future in as_completed(future_to_site):
                site = future_to_site[future]
                try:
                    articles = future.result(timeout=30)
                    all_articles.extend(articles)
                    logger.info(f"✅ {site['name']}: {len(articles)}개")
                except Exception as e:
                    logger.error(f"❌ {site['name']}: {str(e)[:80]}")

        logger.info(f"🎉 총 {len(all_articles)}개 기사 수집 완료")
        return all_articles
