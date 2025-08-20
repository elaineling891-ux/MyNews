import sqlite3

DB_FILE = "news.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_news(title, content):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO news (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    conn.close()
