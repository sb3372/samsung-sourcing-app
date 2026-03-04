"""
웹 크롤러 - 50개 웹사이트에서 기사 수집
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.timeout = 10
        self.processed_urls = set()
        self.url_lock = threading.Lock()
    
    def crawl_website(self, website_config: Dict) -> List[Dict]:
        """웹사이트에서 기사 추출"""
        try:
            logger.info(f"🔗 크롤링 시작: {website_config['name']}")
            
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
            articles = []
            
            # 기사 요소 찾기
            article_elements = soup.select(website_config['article_selector'])
            logger.info(f"📰 {website_config['name']}: {len(article_elements)}개 기사 요소 발견")
            
            if not article_elements:
                fallback_selectors = [
                    "div.news-item", "div.story", "li.news", "div.article",
                    "article", "div[class*='article']", "div[class*='news']"
                ]
                
                for selector in fallback_selectors:
                    article_elements = soup.select(selector)
                    if len(article_elements) > 3:
                        logger.info(f"📰 대체 selector 사용: {selector} ({len(article_elements)}개)")
                        break
            
            if not article_elements:
                logger.warning(f"⚠️ {website_config['name']}: 기사 요소 없음")
                return []
            
            # 각 기사 추출
            for article_elem in article_elements[:100]:  # 최대 100개
                try:
                    # 제목
                    title = None
                    title_elem = article_elem.select_one(website_config['title_selector'])
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    else:
                        for tag in article_elem.select("a"):
                            text = tag.get_text(strip=True)
                            if len(text) > 10:
                                title = text
                                break
                        
                        if not title:
                            for tag in article_elem.select("h2, h3, h1"):
                                text = tag.get_text(strip=True)
                                if len(text) > 10:
                                    title = text
                                    break
                    
                    if not title or len(title) < 10:
                        continue
                    
                    # 링크
                    link = None
                    link_elem = article_elem.select_one(website_config['link_selector'])
                    
                    if link_elem and link_elem.get('href'):
                        link = link_elem.get('href')
                    else:
                        for tag in article_elem.select("a"):
                            if tag.get('href'):
                                link = tag.get('href')
                                break
                    
                    if not link:
                        continue
                    
                    # URL 처리
                    if link.startswith('/'):
                        base_url = website_config['url'].rstrip('/')
                        link = base_url + link
                    elif not link.startswith('http'):
                        base_url = website_config['url'].rstrip('/')
                        link = base_url + '/' + link
                    
                    # 중복 확인
                    with self.url_lock:
                        if link in self.processed_urls:
                            continue
                        self.processed_urls.add(link)
                    
                    # 기사 본문 추출
                    try:
                        content = self._extract_content(link)
                    except Exception as e:
                        logger.debug(f"⚠️ 본문 추출 실패: {str(e)[:50]}")
                        content = ""
                    
                    # 저장
                    article_data = {
                        'title': title,
                        'link': link,
                        'source': website_config['name'],
                        'content': content,
                        'crawled_at': datetime.now().isoformat(),
                    }
                    
                    articles.append(article_data)
                    logger.info(f"✅ 기사 추출: {title[:50]}...")
                
                except Exception as e:
                    logger.debug(f"⚠️ 기사 처리 오류: {str(e)[:50]}")
                    continue
            
            logger.info(f"✅ {website_config['name']}: {len(articles)}개 기사 추출 완료\n")
            return articles
        
        except Exception as e:
            logger.error(f"❌ {website_config['name']}: {str(e)[:100]}")
            return []
    
    def _extract_content(self, link: str) -> str:
        """기사 본문 추출"""
        try:
            response = requests.get(link, headers=self.headers, timeout=self.timeout)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 기사 본문 찾기 (일반적인 selector들)
            content_selectors = [
                "article",
                "div.article-content",
                "div.post-content",
                "div.content",
                "main",
                "div[class*='content']",
                "div[class*='article']",
            ]
            
            for selector in content_selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if len(text) > 100:
                        return text[:2000]  # 최대 2000글자
            
            # 실패하면 body에서 추출
            body = soup.find('body')
            if body:
                text = body.get_text(strip=True)
                return text[:2000]
            
            return ""
        
        except Exception as e:
            logger.debug(f"⚠️ 본문 추출 오류: {str(e)[:50]}")
            return ""
    
    def crawl_all_websites(self, websites: List[Dict], max_workers: int = 10) -> List[Dict]:
        """모든 웹사이트에서 기사 수집 (병렬 처리)"""
        all_articles = []
        
        logger.info(f"🚀 총 {len(websites)}개 웹사이트 병렬 크롤링 시작\n")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_website = {
                executor.submit(self.crawl_website, website): website 
                for website in websites
            }
            
            for future in as_completed(future_to_website):
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                except Exception as e:
                    logger.error(f"❌ 오류: {str(e)}")
        
        logger.info(f"📊 총 {len(all_articles)}개 기사 수집 완료\n")
        return all_articles
