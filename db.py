import psycopg2
import os

DB_URL = os.getenv("DATABASE_URL")

def init_db():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT,
        link TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(title),
        UNIQUE(link)
    )
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ 数据库初始化完成")

def insert_news(title, content, link=None):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO news (title, content, link)
        VALUES (%s, %s, %s)
        ON CONFLICT (link) DO NOTHING
    """, (title, content, link))
    conn.commit()
    cur.close()
    conn.close()

def get_all_news(limit=20):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT id, title, content, created_at FROM news ORDER BY created_at DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "title": r[1], "content": r[2]} for r in rows]
