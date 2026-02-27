import requests
from bs4 import BeautifulSoup
import time
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
        
        # 제외할 키워드 (AI/LLM/일반 기술)
        self.exclude_keywords = [
            'ai', 'artificial intelligence', 'llm', 'chatgpt', 'openai',
            'machine learning', 'deep learning', 'neural', 'algorithm',
            'software', 'cloud', 'data center', 'server',
            'cryptocurrency', 'blockchain', 'crypto',
            'startup', 'investment', 'funding', 'venture',
        ]
        
        # 포함할 키워드 (10개 카테고리 관련)
        self.include_keywords = [
            # Semiconductors
            'semiconductor', 'chip', 'processor', 'fab', 'foundry', 'tsmc', 'samsung', 'intel',
            'processor', 'cpu', 'gpu', 'asic', '5nm', '3nm',
            # Components
            'sensor', 'display', 'lcd', 'oled', 'capacitor', 'resistor',
            # Consumer Electronics
            'smartphone', 'iphone', 'android', 'tablet', 'smartwatch', 'wearable',
            # Energy/Power
            'battery', 'power', 'energy', 'charging', 'electric vehicle', 'ev',
            # Connectivity
            '5g', '6g', 'network', 'wifi', 'broadband', 'telecom',
            # Robotics
            'robot', 'automation', 'manufacturing',
            # Photonics
            'photon', 'quantum', 'laser', 'optical',
            # Materials
            'graphene', 'nanotechnology', 'material',
            # Raw Materials
            'rare earth', 'lithium', 'cobalt', 'mineral',
            # Sustainable
            'recycling', 'e-waste', 'circular economy', 'sustainability',
        ]
    
    def is_valid_article(self, title: str) -> bool:
        """
        유효한 기사인지 확인
        1. AI/LLM 키워드 제외
        2. 10개 카테고리 관련 키워드 포함
        """
        text = title.lower()
        
        # 1. 제외 키워드 확인
        for keyword in self.exclude_keywords:
            if keyword in text:
                logger.info(f"⏭️ 제외: {title[:50]}... (키워드: {keyword})")
                return False
        
        # 2. 포함 키워드 확인
        for keyword in self.include_keywords:
            if keyword in text:
                logger.info(f"✅ 포함: {title[:50]}... (키워드: {keyword})")
                return True
        
        logger.info(f"⏭️ 제외: {title[:50]}... (관련 키워드 없음)")
        return False
    
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
            logger.info(f"📰 '{website_config['article_selector']}': {len(article_elements)}개")
            
            if not article_elements:
                fallback_selectors = [
                    "div.news-item", "div.story", "li.news", "div.article",
                    "article", "div[class*='article']", "div[class*='news']"
                ]
                
                for selector in fallback_selectors:
                    article_elements = soup.select(selector)
                    if len(article_elements) > 3:
                        logger.info(f"📰 대체 selector '{selector}': {len(article_elements)}개")
                        break
            
            if not article_elements:
                logger.warning(f"⚠️ {website_config['name']}: 기사 요소 없음")
                return []
            
            # 각 기사 추출
            for article_elem in article_elements[:100]:
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
                    
                    # 🔒 유효한 기사인지 확인 (AI/LLM 제외, 10개 카테고리만)
                    if not self.is_valid_article(title):
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
                    
                    # 저장 (categories는 config에서 가져옴)
                    article_data = {
                        'title_en': title,
                        'link': link,
                        'source': website_config['name'],
                        'categories': website_config['categories'],
                        'crawled_at': datetime.now().isoformat(),
                    }
                    
                    articles.append(article_data)
                
                except Exception as e:
                    logger.debug(f"⚠️ 오류: {str(e)[:50]}")
                    continue
            
            logger.info(f"✅ {website_config['name']}: {len(articles)}개\n")
            return articles
        
        except Exception as e:
            logger.error(f"❌ {website_config['name']}: {str(e)[:100]}")
            return []
    
    def crawl_all_websites(self, websites: List[Dict], max_workers: int = 10) -> List[Dict]:
        """모든 웹사이트에서 기사 수집"""
        all_articles = []
        
        logger.info(f"🚀 총 {len(websites)}개 웹사이트 병렬 크롤링\n")
        
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
        
        logger.info(f"📊 총 {len(all_articles)}개 기사 수집\n")
        return all_articles
