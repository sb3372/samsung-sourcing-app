import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.timeout = 10
        self.processed_urls = set()
    
    def crawl_website(self, website_config: Dict) -> List[Dict]:
        """
        웹사이트에서 기사 추출
        """
        try:
            logger.info(f"🔗 크롤링 시작: {website_config['name']}")
            
            # 웹사이트 접근
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
            
            # 기사 컨테이너 찾기
            article_elements = soup.select(website_config['article_selector'])
            logger.info(f"📰 {len(article_elements)}개 기사 요소 발견")
            
            if not article_elements:
                logger.warning(f"⚠️ {website_config['name']}: 기사 요소를 찾을 수 없음")
                return []
            
            # 각 기사 추출
            for idx, article_elem in enumerate(article_elements[:20]):
                try:
                    # 제목 추출
                    title_elem = article_elem.select_one(website_config['title_selector'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 10:
                        continue
                    
                    # 링크 추출
                    link_elem = article_elem.select_one(website_config['link_selector'])
                    if not link_elem:
                        continue
                    
                    link = link_elem.get('href', '')
                    if not link:
                        continue
                    
                    # 상대 URL 처리
                    if link.startswith('/'):
                        base_url = website_config['url'].rstrip('/')
                        link = base_url + link
                    elif not link.startswith('http'):
                        base_url = website_config['url'].rstrip('/')
                        link = base_url + '/' + link
                    
                    # 중복 확인
                    if link in self.processed_urls:
                        continue
                    
                    self.processed_urls.add(link)
                    
                    # 기사 정보 저장
                    article_data = {
                        'title_en': title,
                        'link': link,
                        'source': website_config['name'],
                        'categories': website_config['categories'],
                        'crawled_at': datetime.now().isoformat(),
                    }
                    
                    articles.append(article_data)
                    logger.info(f"✅ 기사 추출: {title[:60]}...")
                
                except Exception as e:
                    logger.warning(f"⚠️ 기사 처리 오류: {str(e)[:50]}")
                    continue
            
            logger.info(f"✅ {website_config['name']}: {len(articles)}개 기사 추출 완료\n")
            return articles
        
        except requests.Timeout:
            logger.error(f"⏱️ {website_config['name']}: 타임아웃")
            return []
        except Exception as e:
            logger.error(f"❌ {website_config['name']}: {str(e)[:100]}")
            return []
    
    def crawl_all_websites(self, websites: List[Dict], max_workers: int = 10) -> List[Dict]:
        """
        모든 웹사이트에서 기사 크롤링 (병렬 처리)
        
        Args:
            websites: config.py의 WEBSITES 리스트
            max_workers: 동시에 처리할 웹사이트 개수 (기본 10개)
            
        Returns:
            모든 기사 통합 리스트
        """
        all_articles = []
        
        logger.info(f"🚀 총 {len(websites)}개 웹사이트 병렬 크롤링 시작 (동시 {max_workers}개)\n")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 모든 웹사이트 작업 제출
            future_to_website = {
                executor.submit(self.crawl_website, website): website 
                for website in websites
            }
            
            # 완료된 작업부터 처리
            for future in as_completed(future_to_website):
                website = future_to_website[future]
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                except Exception as e:
                    logger.error(f"❌ {website['name']}: {str(e)}")
        
        logger.info(f"📊 총 {len(all_articles)}개 기사 수집 완료\n")
        return all_articles
