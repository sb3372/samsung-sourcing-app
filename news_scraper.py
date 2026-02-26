"""
Samsung 뉴스 수집 및 요약 엔진
"""

import feedparser
import requests
from newspaper import Article
import google.generativeai as genai
from datetime import datetime
import difflib
from typing import List, Dict, Optional
import time

class NewsScraper:
    def __init__(self, gemini_api_key: str, system_prompt: str):
        """
        뉴스 스크래퍼 초기화
        
        Args:
            gemini_api_key: Google Gemini API 키
            system_prompt: Gemini 요약용 시스템 프롬프트
        """
        self.gemini_api_key = gemini_api_key
        self.system_prompt = system_prompt
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.processed_urls = set()
        
    def fetch_rss_feed(self, search_query: str, lang: str, region: str) -> List[Dict]:
        """
        Google News RSS 피드에서 기사 가져오기
        
        Args:
            search_query: 검색 쿼리
            lang: 언어 코드 (en, de, fr, es, nl, pl)
            region: 지역 코드 (US, DE, FR, ES, NL, PL)
            
        Returns:
            기사 목록
        """
        try:
            # Google News RSS URL 구성
            encoded_query = requests.utils.quote(search_query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&ceid={region}:kr"
            
            feed = feedparser.parse(rss_url)
            articles = []
            
            for entry in feed.entries[:10]:  # 상위 10개만
                article_data = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "source": entry.get("source", {}).get("title", "Unknown"),
                    "published": entry.get("published", ""),
                    "language": lang,
                    "region": region,
                }
                
                # URL 중복 확인
                if article_data["link"] not in self.processed_urls:
                    articles.append(article_data)
                    
            return articles
            
        except Exception as e:
            print(f"RSS 피드 파싱 오류: {e}")
            return []
    
    def is_duplicate_by_title(self, title: str, existing_titles: List[str], threshold: float = 0.8) -> bool:
        """
        제목 유사도로 중복 검사
        
        Args:
            title: 검사할 제목
            existing_titles: 기존 제목 목록
            threshold: 유사도 임계값 (기본값 0.8 = 80%)
            
        Returns:
            중복 여부
        """
        for existing_title in existing_titles:
            similarity = difflib.SequenceMatcher(None, title.lower(), existing_title.lower()).ratio()
            if similarity >= threshold:
                return True
        return False
    
    def scrape_article(self, url: str) -> Optional[str]:
        """
        웹사이트에서 기사 본문 추출
        
        Args:
            url: 기사 URL
            
        Returns:
            기사 본문 또는 None
        """
        try:
            article = Article(url, language="en")
            article.download()
            article.parse()
            
            if article.text:
                return article.text[:3000]  # 3000자까지만
            return None
            
        except Exception as e:
            print(f"기사 추출 오류 ({url}): {e}")
            return None
    
    def summarize_with_gemini(self, article_text: str) -> str:
        """
        Gemini API를 사용하여 기사 요약 및 한국어 번역
        
        Args:
            article_text: 기사 본문
            
        Returns:
            요약된 한국어 텍스트
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
            return f"요약 실패: {str(e)}"
    
    def process_article(self, article: Dict) -> Optional[Dict]:
        """
        단일 기사 처리 (스크래핑 + 요약)
        
        Args:
            article: 기사 데이터
            
        Returns:
            처리된 기사 또는 None
        """
        # URL 중복 확인
        if article["link"] in self.processed_urls:
            return None
        
        # 기사 본문 추출
        article_text = self.scrape_article(article["link"])
        if not article_text:
            return None
        
        # Gemini로 요약
        summary = self.summarize_with_gemini(article_text)
        
        # 관련성 없음 또는 상세 부족인 경우 필터링
        if "NOT_RELEVANT_TO_PROCUREMENT" in summary or "INSUFFICIENT_DETAILS" in summary:
            return None
        
        # 처리된 URL 기록
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
        
        Args:
            articles: 기사 목록
            
        Returns:
            처리된 기사 목록
        """
        processed = []
        
        for i, article in enumerate(articles):
            print(f"처리 중... ({i+1}/{len(articles)})")
            result = self.process_article(article)
            
            if result:
                processed.append(result)
            
            # API 속도 제한 방지
            time.sleep(1)
        
        return processed
