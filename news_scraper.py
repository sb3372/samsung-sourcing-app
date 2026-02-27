import feedparser
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime
import time
from typing import List, Dict, Optional
import difflib

class NewsScraper:
    def __init__(self, gemini_api_key: str, system_prompt: str):
        self.gemini_api_key = gemini_api_key
        self.system_prompt = system_prompt
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-pro")
        self.processed_urls = set()
        
    def fetch_rss_feed(self, search_query: str) -> List[Dict]:
        """Google News RSS에서 기사 가져오기 - 다언어 지원"""
        try:
            encoded_query = requests.utils.quote(search_query)
            
            # 간단한 RSS URL (언어 자동 감지)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}"
            
            feed = feedparser.parse(rss_url)
            articles = []
            
            if not feed.entries:
                return []
            
            for entry in feed.entries[:5]:  # 각 쿼리당 5개만
                title = entry.get("title", "")
                link = entry.get("link", "")
                
                if not link or link in self.processed_urls:
                    continue
                
                article_data = {
                    "title": title,
                    "link": link,
                    "source": entry.get("source", {}).get("title", "Unknown"),
                    "published": entry.get("published", ""),
                }
                
                articles.append(article_data)
                self.processed_urls.add(link)
                    
            return articles
        except Exception as e:
            print(f"RSS 오류: {e}")
            return []
    
    def scrape_article(self, url: str) -> Optional[str]:
        """웹사이트에서 텍스트 추출"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 불필요 요소 제거
            for element in soup(["script", "style", "nav", "footer"]):
                element.decompose()
            
            # 텍스트 추출
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            text = ' '.join(line for line in lines if line)
            
            if len(text) > 150:
                return text[:3000]
            return None
            
        except Exception as e:
            print(f"스크래핑 오류: {e}")
            return None
    
    def summarize_with_gemini(self, article_text: str) -> str:
        """Gemini로 한국어 요약"""
        try:
            message = self.model.generate_content(
                [self.system_prompt, "\n\n【기사 내용】\n\n" + article_text],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=400,
                    temperature=0.3,
                )
            )
            
            return message.text.strip()
            
        except Exception as e:
            print(f"Gemini 오류: {e}")
            return None
    
    def process_article(self, article: Dict) -> Optional[Dict]:
        """기사 처리"""
        article_text = self.scrape_article(article["link"])
        if not article_text:
            return None
        
        summary = self.summarize_with_gemini(article_text)
        if not summary or "NOT_RELEVANT" in summary:
            return None
        
        return {
            "title": article["title"],
            "link": article["link"],
            "source": article["source"],
            "published": article["published"],
            "summary": summary,
        }
