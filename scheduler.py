"""
백그라운드 스케줄러
- 첫 실행: 즉시 크롤링
- 이후: 매일 밤 2시 자동 크롤링
"""
import schedule
import time
import logging
import os
from datetime import datetime
from config import WEBSITES
from crawler import WebCrawler
from ai import AIProcessor
import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScheduler:
    def __init__(self):
        self.crawler = WebCrawler()
        self.is_first_run = not self._has_articles()
    
    def _has_articles(self):
        """DB에 기사가 있는지 확인"""
        try:
            import sqlite3
            conn = sqlite3.connect("samsung_news.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cached_articles")
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except:
            return False
    
    def run_crawl_job(self):
        """크롤링 작업 실행"""
        try:
            logger.info("=" * 60)
            logger.info(f"🚀 크롤링 시작: {datetime.now()}")
            logger.info("=" * 60)
            
            start_time = time.time()
            
            # 1단계: 크롤링
            logger.info("\n📖 단계 1: 50개 사이트에서 기사 크롤링")
            articles = self.crawler.crawl_all_websites_optimized(WEBSITES, max_workers=10)
            logger.info(f"✅ {len(articles)}개 기사 수집\n")
            
            if not articles:
                logger.warning("⚠️ 크롤링 실패 - 기사 없음")
                return
            
            # 2단계: AI 분류
            api_key = os.getenv('GEMINI_API_KEY')
            
            if not api_key:
                logger.warning("⚠️ GEMINI_API_KEY 없음 - 기본값으로 저장")
                for article in articles:
                    article['categories'] = ['반도체']
                    article['summary'] = article.get('content', '')[:200]
                    article['companies'] = []
                    article['is_europe_relevant'] = True
                
                db.batch_insert_articles(articles, week_range=1)
            else:
                logger.info("📖 단계 2: AI로 기사 분류 (병렬 처리)")
                ai = AIProcessor(api_key)
                processed = ai.process_articles_parallel(articles, max_workers=5)
                
                valid_articles = [a for a in processed if a.get('is_europe_relevant')]
                logger.info(f"✅ {len(valid_articles)}개 기사 분류 완료\n")
                
                logger.info("📖 단계 3: DB에 저장")
                db.batch_insert_articles(valid_articles, week_range=1)
            
            elapsed = time.time() - start_time
            logger.info(f"\n✅ 완료: {elapsed:.1f}초 ({elapsed/60:.1f}분)")
            logger.info("=" * 60 + "\n")
        
        except Exception as e:
            logger.error(f"❌ 크롤링 오류: {str(e)}", exc_info=True)
    
    def start(self):
        """스케줄러 시작"""
        logger.info("📅 스케줄러 시작\n")
        
        # 첫 실행: 즉시 크롤링
        if self.is_first_run:
            logger.info("🔴 첫 실행 감지 - 즉시 크롤링 시작!\n")
            self.run_crawl_job()
        
        # 매일 밤 2시에 실행
        schedule.every().day.at("02:00").do(self.run_crawl_job)
        logger.info("✅ 매일 밤 2시에 자동 크롤링 예약됨\n")
        
        # 스케줄러 루프
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except Exception as e:
                logger.error(f"❌ 스케줄러 오류: {str(e)}")
                time.sleep(60)

if __name__ == "__main__":
    scheduler = NewsScheduler()
    scheduler.start()
