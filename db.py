import sqlite3

DB_NAME = "news.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 增加 image_url 字段
    c.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def insert_news(title, content, image_url=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO news (title, content, image_url) VALUES (?, ?, ?)", 
              (title, content, image_url))
    conn.commit()
    conn.close()

def get_all_news():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, title, content, image_url, created_at FROM news ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [
        {"id": r[0], "title": r[1], "content": r[2], "image_url": r[3], "created_at": r[4]}
        for r in rows
    ]
