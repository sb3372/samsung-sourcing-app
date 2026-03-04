"""
SQLite 데이터베이스 관리
"""
import sqlite3
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

DB_FILE = "samsung_news.db"

def init_db():
    """데이터베이스 초기화"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 사용자 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            api_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # 읽은 기사 이력 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS read_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            article_link TEXT NOT NULL,
            read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, article_link)
        )
    ''')
    
    # 캐시 기사 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cached_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_link TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            summary TEXT,
            source TEXT,
            companies TEXT,
            categories TEXT,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            week_range INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ DB 초기화 완료")

def get_or_create_user(user_id: str, api_key: str = ""):
    """사용자 생성 또는 조회"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.execute('''
                INSERT INTO users (user_id, api_key, last_login)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, api_key))
            logger.info(f"✅ 새 사용자: {user_id}")
        else:
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            logger.info(f"✅ 기존 사용자: {user_id}")
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"❌ 사용자 생성 오류: {str(e)}")
        return False

def is_read_article(user_id: str, article_link: str) -> bool:
    """사용자가 읽은 기사 확인"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 1 FROM read_articles
            WHERE user_id = ? AND article_link = ?
        ''', (user_id, article_link))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    except Exception as e:
        logger.error(f"❌ 조회 오류: {str(e)}")
        return False

def mark_article_read(user_id: str, article_link: str):
    """기사를 읽음으로 표시"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO read_articles (user_id, article_link)
            VALUES (?, ?)
        ''', (user_id, article_link))
        
        conn.commit()
        conn.close()
    
    except Exception as e:
        logger.debug(f"⚠️ {str(e)[:50]}")

def cache_article(article: dict, week_range: int):
    """기사를 캐시에 저장"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO cached_articles 
            (article_link, title, content, summary, source, companies, categories, week_range)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            article.get('link', ''),
            article.get('title', ''),
            article.get('content', ''),
            article.get('summary', ''),
            article.get('source', ''),
            ','.join(article.get('companies', [])),
            ','.join(article.get('categories', [])),
            week_range
        ))
        
        conn.commit()
        conn.close()
    
    except Exception as e:
        logger.debug(f"⚠️ 캐시 저장 오류: {str(e)[:50]}")

def batch_insert_articles(articles: list, week_range: int):
    """여러 기사를 한 번에 저장"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        for article in articles:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO cached_articles 
                    (article_link, title, content, summary, source, companies, categories, week_range)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.get('link', ''),
                    article.get('title', ''),
                    article.get('content', ''),
                    article.get('summary', ''),
                    article.get('source', ''),
                    ','.join(article.get('companies', [])),
                    ','.join(article.get('categories', [])),
                    week_range
                ))
            except Exception as e:
                logger.debug(f"⚠️ {str(e)[:30]}")
                continue
        
        conn.commit()
        conn.close()
        logger.info(f"✅ {len(articles)}개 기사 저장")
    
    except Exception as e:
        logger.error(f"❌ 배치 저장 오류: {str(e)}")

def get_cached_articles_filtered(categories: list, limit: int = 1000) -> list:
    """카테고리로 필터링된 기사 로드"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 모든 기사 로드
        cursor.execute('SELECT * FROM cached_articles LIMIT ?', (limit,))
        all_articles = cursor.fetchall()
        conn.close()
        
        # Python에서 필터링
        filtered = []
        for article in all_articles:
            article_categories = article[7].split(',') if article[7] else []
            if any(cat.strip() in categories for cat in article_categories):
                filtered.append({
                    'id': article[0],
                    'link': article[1],
                    'title': article[2],
                    'content': article[3],
                    'summary': article[4],
                    'source': article[5],
                    'companies': article[6].split(',') if article[6] else [],
                    'categories': article_categories,
                    'crawled_at': article[8],
                })
        
        return filtered
    
    except Exception as e:
        logger.error(f"❌ 조회 오류: {str(e)}")
        return []

def get_user_api_key(user_id: str) -> str:
    """사용자의 API Key 조회"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT api_key FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else ""
    
    except Exception as e:
        logger.error(f"❌ API Key 조회 오류: {str(e)}")
        return ""

# DB 초기화
if not os.path.exists(DB_FILE):
    init_db()
