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
            api_key TEXT NOT NULL,
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
    
    # 크롤링된 기사 캐시 테이블
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
    logger.info("✅ 데이터베이스 초기화 완료")

def get_or_create_user(user_id: str, api_key: str):
    """사용자 생성 또는 조회"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute('''
            INSERT INTO users (user_id, api_key)
            VALUES (?, ?)
        ''', (user_id, api_key))
        conn.commit()
        logger.info(f"✅ 새 사용자 생성: {user_id}")
    else:
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
    
    conn.close()
    return user_id

def is_read_article(user_id: str, article_link: str) -> bool:
    """사용자가 이 기사를 읽었는지 확인"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 1 FROM read_articles
        WHERE user_id = ? AND article_link = ?
    ''', (user_id, article_link))
    
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

def mark_article_read(user_id: str, article_link: str):
    """기사를 읽음으로 표시"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO read_articles (user_id, article_link)
            VALUES (?, ?)
        ''', (user_id, article_link))
        conn.commit()
        logger.info(f"✅ 기사 읽음 표시: {article_link[:50]}")
    except sqlite3.IntegrityError:
        pass  # 이미 읽음
    
    conn.close()

def cache_article(article: dict, week_range: int):
    """기사를 캐시에 저장"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO cached_articles 
            (article_link, title, content, summary, source, companies, categories, week_range)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            article['link'],
            article['title'],
            article.get('content', ''),
            article.get('summary', ''),
            article.get('source', ''),
            ','.join(article.get('companies', [])),
            ','.join(article.get('categories', [])),
            week_range
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # 이미 캐시됨
    
    conn.close()

def get_cached_articles(week_range: int):
    """캐시된 기사 조회"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM cached_articles WHERE week_range = ?
        ORDER BY crawled_at DESC
    ''', (week_range,))
    
    articles = cursor.fetchall()
    conn.close()
    
    return articles

# 초기화
if not os.path.exists(DB_FILE):
    init_db()
