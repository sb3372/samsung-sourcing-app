import feedparser
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime
import time
from typing import List, Dict, Optional

class NewsScraper:
    def __init__(self, gemini_api_key: str, system_prompt: str):
        self.gemini_api_key = gemini_api_key
        self.system_prompt = system_prompt
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.processed_urls = set()
        
    def fetch_rss_feed(self, search_query: str, lang: str, region: str) -> List[Dict]:
        """Google News RSS에서 기사 가져오기"""
        try:
            encoded_query = requests.utils.quote(search_query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&ceid={region}:kr"
            
            feed = feedparser.parse(rss_url)
            articles = []
            
            for entry in feed.entries[:5]:
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
            print(f"RSS 오류: {e}")
            return []
    
    def scrape_article(self, url: str) -> Optional[str]:
        """웹사이트에서 기사 본문 추출"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            if text:
                return text[:2000]
            return None
        except Exception as e:
            print(f"스크래핑 오류: {e}")
            return None
    
    def summarize_with_gemini(self, article_text: str) -> str:
        """Gemini로 요약"""
        try:
            message = self.model.generate_content(
                [self.system_prompt, "\n\n기사:\n\n" + article_text],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.3,
                )
            )
            return message.text.strip()
        except Exception as e:
            return f"오류: {str(e)}"
    
    def process_article(self, article: Dict) -> Optional[Dict]:
        """기사 처리"""
        if article["link"] in self.processed_urls:
            return None
        
        article_text = self.scrape_article(article["link"])
        if not article_text:
            return None
        
        summary = self.summarize_with_gemini(article_text)
        
        if "NOT_RELEVANT" in summary:
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
        }
