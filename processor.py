"""
데이터 처리 - 필터링, 분류, 중복 제거
"""
import logging
from typing import List, Dict
from datetime import datetime, timedelta
import difflib
from ai import AIProcessor
import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, api_key: str):
        self.ai = AIProcessor(api_key)
    
    def process_articles(self, raw_articles: List[Dict], user_id: str, week_range: int) -> List[Dict]:
        """
        기사 처리:
        1. 유럽 회사 필터링
        2. AI 분류
        3. 중복 제거
        4. 사용자 이력 제외
        """
        logger.info(f"📋 {len(raw_articles)}개 기사 처리 시작\n")
        
        processed_articles = []
        
        for idx, article in enumerate(raw_articles, 1):
            logger.info(f"처리 중: {idx}/{len(raw_articles)}")
            
            # 1단계: AI 분류 & 요약
            ai_result = self.ai.categorize_and_summarize(
                article['title'],
                article['content']
            )
            
            # 2단계: 유럽 관련성 확인
            if not ai_result['is_europe_relevant']:
                logger.info(f"⏭️ 제외: 유럽 무관 - {article['title'][:50]}")
                continue
            
            # 3단계: 카테고리 확인
            if not ai_result['categories']:
                logger.info(f"⏭️ 제외: 카테고리 없음 - {article['title'][:50]}")
                continue
            
            # 4단계: 사용자 읽음 이력 확인
            if db.is_read_article(user_id, article['link']):
                logger.info(f"⏭️ 제외: 이미 읽은 기사 - {article['title'][:50]}")
                continue
            
            # 5단계: 중복 확인 (현재 세션 내)
            is_duplicate = False
            for existing in processed_articles:
                similarity = self._calculate_similarity(
                    ai_result['summary'],
                    existing.get('summary', '')
                )
                if similarity > 0.5:  # 50% 이상 유사
                    logger.info(f"⏭️ 제외: 중복 기사 ({similarity:.0%}) - {article['title'][:50]}")
                    is_duplicate = True
                    break
            
            if is_duplicate:
                continue
            
            # 최종 기사 구성
            final_article = {
                'title': article['title'],
                'link': article['link'],
                'source': article['source'],
                'summary': ai_result['summary'],
                'companies': ai_result['companies'],
                'categories': ai_result['categories'],
                'content': article['content'],
                'crawled_at': article['crawled_at'],
            }
            
            processed_articles.append(final_article)
            
            # DB에 캐시 저장
            db.cache_article(final_article, week_range)
            
            logger.info(f"✅ 처리 완료: {article['title'][:50]}...")
        
        logger.info(f"\n📊 처리 완료: {len(processed_articles)}개 기사 남음\n")
        return processed_articles
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트의 유사도 계산 (0~1)"""
        if not text1 or not text2:
            return 0
        
        similarity = difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        return similarity
