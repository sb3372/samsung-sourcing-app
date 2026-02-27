import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict
import difflib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Deduplicator:
    def __init__(self, csv_file: str = "seen_articles.csv"):
        self.csv_file = csv_file
        self.seen_articles = self._load_seen_articles()
    
    def _load_seen_articles(self) -> List[Dict]:
        """저장된 기사 로드"""
        if not os.path.exists(self.csv_file):
            return []
        
        articles = []
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                articles = list(reader)
            logger.info(f"✅ {len(articles)}개 기존 기사 로드됨")
        except Exception as e:
            logger.error(f"❌ CSV 로드 오류: {e}")
        
        return articles
    
    def _title_similarity(self, title1: str, title2: str, threshold: float = 0.5) -> bool:
        """
        제목 유사도 비교 (50% 이상 같으면 중복)
        
        Args:
            title1: 제목 1
            title2: 제목 2
            threshold: 유사도 임계값 (기본 50%)
            
        Returns:
            유사하면 True, 아니면 False
        """
        similarity = difflib.SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
        return similarity >= threshold
    
    def is_duplicate(self, article: Dict) -> bool:
        """
        기사가 중복인지 확인
        
        1. URL 기반 중복
        2. 제목 50% 유사도 기반 중복
        3. 7일 이내 같은 제목
        """
        article_link = article['link']
        article_title = article['title_en']
        
        # 1. URL 중복 확인
        for seen in self.seen_articles:
            if seen['link'] == article_link:
                logger.info(f"↺ URL 중복: {article_title[:50]}...")
                return True
        
        # 2. 제목 유사도 확인 (50% 이상)
        for seen in self.seen_articles:
            if self._title_similarity(article_title, seen['title_en'], threshold=0.50):
                logger.info(f"↺ 제목 유사 (50%+): {article_title[:50]}...")
                return True
        
        return False
    
    def save_article(self, article: Dict) -> None:
        """기사를 CSV에 저장"""
        try:
            # 새 기사인지 확인
            if self.is_duplicate(article):
                return
            
            # CSV에 추가
            article['saved_at'] = datetime.now().isoformat()
            
            # 파일이 없으면 생성
            if not os.path.exists(self.csv_file):
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=article.keys())
                    writer.writeheader()
                    writer.writerow(article)
            else:
                with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=article.keys())
                    writer.writerow(article)
            
            logger.info(f"💾 저장됨: {article['title_en'][:50]}...")
        
        except Exception as e:
            logger.error(f"❌ 저장 오류: {e}")
    
    def save_articles(self, articles: List[Dict]) -> int:
        """여러 기사 저장"""
        saved_count = 0
        for article in articles:
            if not self.is_duplicate(article):
                self.save_article(article)
                saved_count += 1
                self.seen_articles.append(article)
        
        logger.info(f"✅ {saved_count}개 새 기사 저장됨")
        return saved_count
    
    def cleanup_old_articles(self, days: int = 30) -> None:
        """30일 이상 된 기사 삭제"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            remaining = []
            for article in self.seen_articles:
                saved_at = datetime.fromisoformat(article.get('saved_at', datetime.now().isoformat()))
                if saved_at > cutoff_date:
                    remaining.append(article)
            
            if len(remaining) < len(self.seen_articles):
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=remaining[0].keys() if remaining else [])
                    writer.writeheader()
                    writer.writerows(remaining)
                
                logger.info(f"🧹 {len(self.seen_articles) - len(remaining)}개 오래된 기사 삭제됨")
                self.seen_articles = remaining
        
        except Exception as e:
            logger.error(f"❌ 정리 오류: {e}")
