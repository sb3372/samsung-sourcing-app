"""
Samsung 뉴스 수집 및 요약 엔진
"""

import feedparser
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime
import difflib
from typing import List, Dict, Optional
import time

class NewsScraper:
    def __init__(self, gemini_api_key: str, system_prompt: str):
        """
        뉴스 스크래퍼 초기화
        """
        self.gemini_api_key = gemini_api_key
        self.system_prompt = system_prompt
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.processed_urls = set()
        
    def fetch_rss_feed(self, search_query: str, lang: str, region: str) -> List[Dict]:
        """
        Google News RSS 피드에서 기사 가져오기
        """
        try:
            encoded_query = requests.utils.quote(search_query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&ceid={region}:kr"
            
            feed = feedparser.parse(rss_url)
            articles = []
            
            for entry in feed.entries[:10]:
                article_data = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "source": entry.get("source", {}).get("title", "Unknown"),
                    "published": entry.get("published", ""),
                    "language": lang,
                    "region": region,
                }
                
                if article_data["link"] not in self.processed_urls:
                    articles.append(article_data)
                    
            return articles
            
        except Exception as e:
            print(f"RSS 피드 파싱 오류: {e}")
            return []
    
    def is_duplicate_by_title(self, title: str, existing_titles: List[str], threshold: float = 0.8) -> bool:
        """
        제목 유사도로 중복 검사
        """
        for existing_title in existing_titles:
            similarity = difflib.SequenceMatcher(None, title.lower(), existing_title.lower()).ratio()
            if similarity >= threshold:
                return True
        return False
    
    def scrape_article(self, url: str) -> Optional[str]:
        """
        웹사이트에서 기사 본문 추출
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 불필요한 요소 제거
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            
            # 기사 본문 추출 (주요 텍스트 태그)
            paragraphs = soup.find_all(['p', 'article', 'main'])
            text = ' '.join([p.get_text() for p in paragraphs])
            
            if text:
                return text[:3000]
            return None
            
        except Exception as e:
            print(f"기사 추출 오류 ({url}): {e}")
            return None
    
    def summarize_with_gemini(self, article_text: str) -> str:
        """
        Gemini API를 사용하여 기사 요약
        """
        try:
            message = self.model.generate_content(
                [self.system_prompt, "\n\n기사 내용:\n\n" + article_text],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.3,
                )
            )
            
            return message.text.strip()
            
        except Exception as e:
            print(f"Gemini 요약 오류: {e}")
            return "요약 실패"
    
    def process_article(self, article: Dict) -> Optional[Dict]:
        """
        단일 기사 처리
        """
        if article["link"] in self.processed_urls:
            return None
        
        article_text = self.scrape_article(article["link"])
        if not article_text:
            return None
        
        summary = self.summarize_with_gemini(article_text)
        
        if "NOT_RELEVANT_TO_PROCUREMENT" in summary or "INSUFFICIENT_DETAILS" in summary:
            return None
        
        self.processed_urls.add(article["link"])
        
        return {
            "title": article["title"],
            "link": article["link"],
            "source": article["source"],
            "published": article["published"],
            "language": article["language"],
            "region": article["region"],
            "summary": summary,
            "processed_at": datetime.now().isoformat(),
        }
    
    def process_articles_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        여러 기사를 배치로 처리
        """
        processed = []
        
        for i, article in enumerate(articles):
            result = self.process_article(article)
            
            if result:
                processed.append(result)
            
            time.sleep(0.5)
        
        return processed
