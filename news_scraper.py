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
        """제목 유사도로 중복 검사 (85% 이상 = 중복)"""
        for existing_title in self.processed_titles:
            similarity = difflib.SequenceMatcher(None, title.lower(), existing_title.lower()).ratio()
            if similarity >= threshold:
                return True
        return False
    
    def scrape_article(self, url: str) -> Optional[str]:
        """웹사이트에서 기사 본문 추출 - 5가지 방법 사용"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 불필요한 요소 제거
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "meta"]):
                element.decompose()
            
            text = ""
            
            # 방법 1: article 태그
            article = soup.find('article')
            if article:
                text = article.get_text()
                if len(text) > 200:
                    pass  # 성공
                else:
                    text = ""
            
            # 방법 2: main 태그
            if not text or len(text) < 200:
                main = soup.find('main')
                if main:
                    text = main.get_text()
                    if len(text) > 200:
                        pass  # 성공
                    else:
                        text = ""
            
            # 방법 3: div class에서 content 찾기
            if not text or len(text) < 200:
                for div in soup.find_all('div', class_=lambda x: x and any(keyword in x.lower() for keyword in ['content', 'article', 'post', 'entry', 'body'])):
                    candidate_text = div.get_text()
                    if len(candidate_text) > 200:
                        text = candidate_text
                        break
            
            # 방법 4: 모든 p 태그 수집
            if not text or len(text) < 200:
                paragraphs = soup.find_all('p')
                if paragraphs:
                    text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            # 방법 5: 전체 body에서 추출
            if not text or len(text) < 200:
                body = soup.find('body')
                if body:
                    text = body.get_text()
                else:
                    text = soup.get_text()
            
            # 텍스트 정제
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # 최소 길이 체크
            if len(text) > 150:
                print(f"✅ 스크래핑 성공: {len(text)} 글자")
                return text[:3000]
            else:
                print(f"❌ 텍스트 부족: {len(text)} 글자")
                return None
            
        except requests.Timeout:
            print(f"⏱️ 타임아웃: {url[:50]}...")
            return None
        except Exception as e:
            print(f"❌ 스크래핑 오류: {e}")
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
            
            result = message.text.strip()
            return result
            
        except Exception as e:
            print(f"❌ Gemini 오류: {e}")
            return f"요약_실패"
    
    def process_article(self, article: Dict) -> Optional[Dict]:
        """기사 처리 - 스크래핑 + Gemini 요약"""
        # URL 중복 확인
        if article["link"] in self.processed_urls:
            print(f"↺ 이미 처리됨: {article['title'][:50]}")
            return None
        
        # 기사 추출
        print(f"🔗 추출 시작: {article['title'][:60]}...")
        article_text = self.scrape_article(article["link"])
        if not article_text:
            print(f"❌ 추출 실패: {article['title'][:50]}")
            return None
        
        # Gemini 요약
        print(f"📝 Gemini 요약 중...")
        summary = self.summarize_with_gemini(article_text)
        print(f"📄 요약 결과: {summary[:100]}...")
        
        # 필터링 (더 관대하게)
        if len(summary) < 50:
            print(f"❌ 요약이 너무 짧음 ({len(summary)} 글자): {summary}")
            return None
        
        if "요약_실패" in summary:
            print(f"❌ Gemini 요약 실패")
            return None
        
        if "NOT_RELEVANT_TO_PROCUREMENT" in summary:
            print(f"ⓘ 관련성 없음 (조달과 무관): {article['title'][:50]}")
            return None
        
        if "INSUFFICIENT_DETAILS" in summary:
            print(f"ⓘ 상세 정보 부족: {article['title'][:50]}")
            return None
        
        # 성공!
        self.processed_urls.add(article["link"])
        print(f"✓ 기사 추가 완료!")
        
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
