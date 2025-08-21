# db.py
import psycopg2
import os

DB_URL = os.getenv("DATABASE_URL")

def init_db():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            title TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ 数据库初始化完成")

def insert_news(title, content):
    if not title or not content:
        return
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO news (title, content) VALUES (%s, %s)",
        (title, content)
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ 已写入: {title[:20]}...")
