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
        self.processed_titles = []
        
    def fetch_rss_feed(self, search_query: str, lang: str, ceid: str) -> List[Dict]:
        """Google News RSS에서 기사 가져오기"""
        try:
            encoded_query = requests.utils.quote(search_query)
            
            # 새로운 RSS URL 형식
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&gl={ceid.split(':')[0].lower()}"
            
            print(f"📡 시도: {rss_url[:80]}...")
            
            feed = feedparser.parse(rss_url)
            articles = []
            
            if not feed.entries:
                print(f"⚠️ 결과 없음: {search_query[:50]}")
                return []
            
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                
                if not link:
                    continue
                
                # URL 중복 확인
                if link in self.processed_urls:
                    continue
                
                # 제목 유사도 확인 (85% 이상 = 중복)
                if self.is_duplicate_title(title):
                    continue
                
                article_data = {
                    "title": title,
                    "link": link,
                    "source": entry.get("source", {}).get("title", "Unknown"),
                    "published": entry.get("published", ""),
                    "language": lang,
                    "region": ceid.split(":")[0],
                }
                
                articles.append(article_data)
                self.processed_titles.append(title)
                    
            return articles
        except Exception as e:
            print(f"❌ RSS 오류: {e}")
            return []
    
    def is_duplicate_title(self, title: str, threshold: float = 0.85) -> bool:
        """제목 유사도로 중복 검사"""
        for existing_title in self.processed_titles:
            similarity = difflib.SequenceMatcher(None, title.lower(), existing_title.lower()).ratio()
            if similarity >= threshold:
                return True
        return False
    
    def scrape_article(self, url: str) -> Optional[str]:
        """웹사이트에서 기사 본문 추출"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            paragraphs = soup.find_all(['p', 'article', 'main'])
            text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            if not text:
                text = soup.get_text()
            
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            if text and len(text) > 200:
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
                    max_output_tokens=600,
                    temperature=0.2,
                    top_p=0.8,
                )
            )
            
            return message.text.strip()
            
        except Exception as e:
            return f"요약 실패"
    
    def process_article(self, article: Dict) -> Optional[Dict]:
        """기사 처리"""
        if article["link"] in self.processed_urls:
            return None
        
        article_text = self.scrape_article(article["link"])
        if not article_text:
            return None
        
        summary = self.summarize_with_gemini(article_text)
        
        if "NOT_RELEVANT_TO_PROCUREMENT" in summary or "INSUFFICIENT_DETAILS" in summary:
            return None
        
        if "요약 실패" in summary:
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
