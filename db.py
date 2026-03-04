"""
SQLite 데이터베이스 관리
"""
import sqlite3
import json
import hashlib
import os
import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

DB_FILE = "samsung_news.db"


def _connect():
    return sqlite3.connect(DB_FILE)


def init_db():
    """데이터베이스 초기화"""
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            summary TEXT,
            source TEXT,
            companies TEXT,
            categories TEXT,
            published_at TEXT,
            crawled_at TEXT,
            week_offset INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS read_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key_hash TEXT NOT NULL,
            article_link TEXT NOT NULL,
            read_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(api_key_hash, article_link)
        )
    """)

    conn.commit()
    conn.close()
    logger.info("✅ DB 초기화 완료")


def insert_articles(articles: List[Dict], week_offset: int):
    """기사 목록을 DB에 저장 (중복 무시)"""
    if not articles:
        return
    conn = _connect()
    cursor = conn.cursor()
    for article in articles:
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO articles
                    (link, title, content, summary, source, companies, categories,
                     published_at, crawled_at, week_offset)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article.get("link", ""),
                    article.get("title", ""),
                    article.get("content", ""),
                    article.get("summary", ""),
                    article.get("source", ""),
                    json.dumps(article.get("companies", []), ensure_ascii=False),
                    json.dumps(article.get("categories", []), ensure_ascii=False),
                    article.get("published_at", ""),
                    article.get("crawled_at", ""),
                    week_offset,
                ),
            )
        except Exception as e:
            logger.debug(f"⚠️ insert 오류: {e}")
    conn.commit()
    conn.close()
    logger.info(f"✅ {len(articles)}개 기사 저장 (week_offset={week_offset})")


def get_articles(week_offset: int) -> List[Dict]:
    """주어진 week_offset의 기사 목록 반환"""
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT link, title, content, summary, source, companies, categories, "
        "published_at, crawled_at, week_offset FROM articles WHERE week_offset = ?",
        (week_offset,),
    )
    rows = cursor.fetchall()
    conn.close()
    articles = []
    for row in rows:
        articles.append({
            "link": row[0],
            "title": row[1],
            "content": row[2],
            "summary": row[3],
            "source": row[4],
            "companies": json.loads(row[5]) if row[5] else [],
            "categories": json.loads(row[6]) if row[6] else [],
            "published_at": row[7],
            "crawled_at": row[8],
            "week_offset": row[9],
        })
    return articles


def get_max_week_offset() -> int:
    """현재 DB에 저장된 최대 week_offset 반환"""
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(week_offset) FROM articles")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] is not None else 0
    except Exception:
        return 0


def mark_read(api_key_hash: str, link: str):
    """기사를 읽음으로 표시"""
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO read_history (api_key_hash, article_link) VALUES (?, ?)",
            (api_key_hash, link),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.debug(f"⚠️ mark_read 오류: {e}")


def is_read(api_key_hash: str, link: str) -> bool:
    """기사가 읽혔는지 확인"""
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM read_history WHERE api_key_hash = ? AND article_link = ?",
            (api_key_hash, link),
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception:
        return False


def get_read_links(api_key_hash: str) -> Set[str]:
    """해당 API key hash의 모든 읽은 기사 링크 반환"""
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT article_link FROM read_history WHERE api_key_hash = ?",
            (api_key_hash,),
        )
        rows = cursor.fetchall()
        conn.close()
        return {row[0] for row in rows}
    except Exception:
        return set()


def clear_articles():
    """articles 테이블 초기화"""
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM articles")
        conn.commit()
        conn.close()
        logger.info("✅ articles 테이블 초기화")
    except Exception as e:
        logger.error(f"❌ clear_articles 오류: {e}")


def article_count() -> int:
    """저장된 기사 수 반환"""
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception:
        return 0


def has_properly_categorized_articles() -> bool:
    """반도체 단독이 아닌 카테고리로 분류된 기사가 있는지 확인"""
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute("SELECT categories FROM articles")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            cats = json.loads(row[0]) if row[0] else []
            if cats and cats != ["반도체"]:
                return True
        return False
    except Exception:
        return False


# DB 초기화 (파일 없으면 자동 생성)
if not os.path.exists(DB_FILE):
    init_db()
