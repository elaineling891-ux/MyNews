
import os, json, time, random
import requests, psycopg2
from bs4 import BeautifulSoup

DATABASE_URL = os.getenv("DATABASE_URL")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

def _conn():
    if not DATABASE_URL:
        raise RuntimeError("环境变量 DATABASE_URL 未设置")
    return psycopg2.connect(DATABASE_URL)

def _ensure_table():
    conn = _conn(); cur = conn.cursor()
    cur.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            content TEXT,
            source TEXT,
            image_url TEXT,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    \"\"\")
    conn.commit(); cur.close(); conn.close()

def _rewrite_title(title:str)->str:
    t = " ".join(title.split())
    for a,b in {"：":" - ","，":"、","—":"-","最新":"新进","快讯":"即时报","曝":"传出","称":"表示"}.items():
        t = t.replace(a,b)
    return t[:180]

def _upsert(title, url, content, source, image_url=None):
    conn = _conn(); cur = conn.cursor()
    cur.execute(
        \"\"\"INSERT INTO news (title, url, content, source, image_url, published_at)
               VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)
               ON CONFLICT (url) DO NOTHING\"\"\" ,
        (_rewrite_title(title), url, content, source, image_url)
    )
    conn.commit(); rc = cur.rowcount; cur.close(); conn.close(); return rc

def _fetch_list(s):
    resp = requests.get(s["url"], headers=HEADERS, timeout=12)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    items = []
    for a in soup.select(s["list_selector"])[:s.get("limit", 12)]:
        title = a.get_text(strip=True)
        href = a.get(s.get("attr","href"), "")
        if not href: continue
        if not href.startswith("http"): href = s.get("prefix","") + href
        img = None
        items.append((title, href, img))
    return items

def fetch_all():
    _ensure_table()
    with open("sources.json","r",encoding="utf-8") as f:
        sources = json.load(f)
    inserted = 0
    for s in sources:
        try:
            for title, link, img in _fetch_list(s):
                inserted += _upsert(title, link, "", s["name"], img)
            time.sleep(random.uniform(1.0, 2.0))
            print("✅", s["name"], "完成")
        except Exception as e:
            print("❌", s["name"], "失败：", e)
    return inserted
