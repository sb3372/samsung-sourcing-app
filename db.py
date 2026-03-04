"""
SQLite 데이터베이스 - 배치 저장 추가
"""
import sqlite3
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

DB_FILE = "samsung_news.db"

# ... (기존 코드)

def batch_insert_articles(articles: list, week_range: int):
    """여러 기사를 한 번에 저장"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        for article in articles:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO cached_articles 
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
            except Exception as e:
                logger.debug(f"⚠️ {str(e)[:30]}")
                continue
        
        conn.commit()
        logger.info(f"✅ {len(articles)}개 기사 저장 완료")
    
    except Exception as e:
        logger.error(f"❌ 배치 저장 오류: {str(e)}")
    
    finally:
        conn.close()

def get_articles_for_user(user_id: str, categories: list = None, limit: int = 100):
    """DB에서 기사 로드 (즉시 반환)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if categories:
        # 카테고리 필터링
        placeholders = ','.join('?' * len(categories))
        cursor.execute(f'''
            SELECT * FROM cached_articles
            WHERE categories LIKE {'OR categories LIKE '.join(['?'] * len(categories))}
            LIMIT ?
        ''', [f'%{cat}%' for cat in categories] + [limit])
    else:
        cursor.execute('SELECT * FROM cached_articles LIMIT ?', (limit,))
    
    articles = cursor.fetchall()
    conn.close()
    
    return articles
