
import os
from flask import Flask, render_template, jsonify
import psycopg2
import harvest

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    if not DATABASE_URL:
        raise RuntimeError("环境变量 DATABASE_URL 未设置")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            content TEXT,
            source TEXT,
            image_url TEXT,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def get_latest(limit=60):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT title, url, source, image_url, published_at
        FROM news
        ORDER BY published_at DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@app.route("/", methods=["GET"])
def index():
    try:
        news = get_latest(60)
    except Exception as e:
        news = []
        print("读取数据库失败：", e)
    return render_template("index.html", news=news)

@app.route("/fetch", methods=["GET", "POST"])
def fetch():
    try:
        inserted = harvest.fetch_all()
        return jsonify({"status":"ok","inserted":inserted})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
