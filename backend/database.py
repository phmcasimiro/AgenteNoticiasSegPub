import sqlite3
import os
from typing import List
from .models import NewsItem
from .logging_config import setup_logging

logger = setup_logging()

# Using absolute path relative to project root or configured via env
# For now, placing it in data/ folder similar to previous db
DB_PATH = os.path.join("data", "historico_noticias.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS noticias (
            id TEXT PRIMARY KEY,
            title TEXT,
            url TEXT,
            publishedAt TEXT,
            source TEXT,
            snippet TEXT,
            language TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            level TEXT,
            message TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized/checked.")

def insert_log(level: str, message: str):
    """Inserts a log entry into the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        from datetime import datetime
        cursor.execute("INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)", 
                      (datetime.now().isoformat(), level, message))
        conn.commit()
        conn.close()
    except Exception:
        # Avoid recursion or crashes in logging
        pass

def save_to_db(items: List[NewsItem]):
    conn = get_connection()
    cursor = conn.cursor()
    count = 0
    for item in items:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO noticias (id, title, url, publishedAt, source, snippet, language)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (item.id, item.title, item.url, item.publishedAt.isoformat(), item.source, item.snippet, item.language))
            if cursor.rowcount > 0: count += 1
        except Exception as e:
            logger.error(f"Error saving item {item.id}: {e}")
            
    conn.commit()
    conn.close()
    if count > 0:
        logger.info(f"Saved {count} new items to DB.")

def search_db(q: str) -> List[NewsItem]:
    conn = get_connection()
    cursor = conn.cursor()
    query = f"%{q}%"
    cursor.execute("SELECT * FROM noticias WHERE title LIKE ? OR snippet LIKE ? ORDER BY publishedAt DESC", (query, query))
    rows = cursor.fetchall()
    conn.close()
    return [NewsItem(**dict(r)) for r in rows]

def get_recent_news_db(limit: int = 50) -> List[NewsItem]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM noticias ORDER BY publishedAt DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [NewsItem(**dict(r)) for r in rows]
