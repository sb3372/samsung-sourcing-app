"""
백그라운드 스케줄러
- 매일 자동으로 크롤링 + AI 분류
- 데이터베이스에 저장
- 앱에서는 캐시된 데이터만 로드
"""
import schedule
import time
import logging
from datetime import datetime
from config import WEBSITES
from crawler import WebCrawler
from ai import AIProcessor
import db
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScheduler:
    def __init__(self):
        self.crawler = WebCrawler()
        self.is_running = False
    
    def crawl_and_cache(self):
        """
        1. 크롤링
        2. AI 분류
        3. DB 저장
        """
        try:
            logger.info("🚀 백그라운드 크롤링 시작")
            start_time = time.time()
            
            # 1단계: 제목 크롤링
            logger.info("🔗 단계 1: 제목 크롤링 (50개 사이트)")
            titles = self.crawler.crawl_all_websites_optimized(WEBSITES, max_workers=10)
            logger.info(f"✅ {len(titles)}개 제목 추출 ({time.time() - start_time:.1f}초)")
            
            # 2단계: 본문 크롤링 (필터된 것만)
            logger.info(f"🔗 단계 2: 본문 크롤링 ({len(titles)}개)")
            articles_with_content = self.crawler.crawl_article_content_batch(titles, max_workers=10)
            logger.info(f"✅ 본문 크롤링 완료 ({time.time() - start_time:.1f}초)")
            
            # 3단계: AI 분류 (API Key는 기본값 사용)
            # ⚠️ 주의: 이 부분은 별도의 마스터 API KEY 필요
            logger.info(f"🤖 단계 3: AI 분류 ({len(articles_with_content)}개)")
            # API KEY는 환경변수에서 가져오기
            import os
            api_key = os.getenv('GEMINI_API_KEY')
            
            if api_key:
                ai_processor = AIProcessor(api_key)
                processed = ai_processor.process_articles_parallel(articles_with_content, max_workers=5)
                logger.info(f"✅ AI 분류 완료 ({time.time() - start_time:.1f}초)")
                
                # 4단계: DB 저장
                logger.info("💾 데이터베이스 저장 중...")
                db.batch_insert_articles(processed, week_range=1)
                logger.info(f"✅ 저장 완료 ({time.time() - start_time:.1f}초)")
            else:
                logger.warning("⚠️ GEMINI_API_KEY 환경변수 없음 - 저장 스킵")
            
            elapsed = time.time() - start_time
            logger.info(f"✅ 크롤링 완료: {elapsed:.1f}초 ({elapsed/60:.1f}분)")
        
        except Exception as e:
            logger.error(f"❌ 크롤링 오류: {str(e)}", exc_info=True)
    
    def start(self):
        """스케줄러 시작"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 매일 밤 2시에 실행
        schedule.every().day.at("02:00").do(self.crawl_and_cache)
        
        # 스케줄러를 별도 스레드에서 실행
        def run_scheduler():
            logger.info("📅 스케줄러 시작")
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("✅ 백그라운드 스케줄러 활성화")
    
    def stop(self):
        """스케줄러 중지"""
        self.is_running = False
        logger.info("⏹️ 스케줄러 중지")

# 글로벌 스케줄러
scheduler = NewsScheduler()
scheduler.start()
