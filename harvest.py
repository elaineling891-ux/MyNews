import requests
from bs4 import BeautifulSoup
from db import insert_news, news_exists
import time
from urllib.parse import urljoin
from deep_translator import GoogleTranslator
from playwright.sync_api import sync_playwright

# --------------------------
# 初始化 Cohere 改写 API
# --------------------------
COHERE_API_KEY = "W2pkO3EABJq0LyPyCZ6I1yYwBsLuuiiHDG45qmO5"
COHERE_URL = "https://api.cohere.ai/v1/chat"

def rewrite_text_cohere(text: str) -> str:
    headers = {
        "Authorization": f"Bearer {COHERE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "command-r",  # ✅ 最新模型
        "message": f"请用中文改写以下文本，保持原意但用不同的措辞：\n\n{text}",
        "temperature": 0.7
    }

    resp = requests.post(COHERE_URL, headers=headers, json=payload)
    if resp.status_code != 200:
        print("Cohere 改写失败:", resp.status_code, resp.text)
        return text

    data = resp.json()
    try:
        return data["text"]  # chat 接口会直接给一个 text 字段
    except KeyError:
        return text

# --------------------------
# 后处理：添加换行，每3句换一次行
# --------------------------
def add_linebreaks(text, n_sentences=3):
    import re
    sentences = re.split(r'(?<=[。！？.!?])', text)
    lines = []
    for i in range(0, len(sentences), n_sentences):
        lines.append("".join(sentences[i:i+n_sentences]))
    return "\n\n".join(lines)

# --------------------------
# 翻译成简体中文
# --------------------------
def translate_to_simplified(text: str) -> str:
    try:
        return GoogleTranslator(source="auto", target="zh-CN").translate(text)
    except Exception as e:
        print("翻译失败:", e)
        return text

def rewrite_text(text):
    rewritten = rewrite_text_cohere(text)
    rewritten = add_linebreaks(rewritten)
    return translate_to_simplified(rewritten)  # ✅ 最后翻译成简体

# --------------------------
# 抓取文章内容
# --------------------------
def fetch_article_content(link):
    try:
        resp = requests.get(link, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        div = soup.select_one("div.entry-content") or soup.select_one("div.article-content")
        if div:
            paragraphs = div.find_all("p")
            return "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    except Exception as e:
        print(f"抓文章内容失败 ({link}): {e}")
    return ""

if __name__ == "__main__":
    url = "https://www.sinchew.com.my/latest"
    news_list = fetch_site_news(url)
    for title, link in news_list:
        content = fetch_article_content(link)
        print(f"标题: {title}\n链接: {link}\n内容预览: {content[:100]}...\n")

# --------------------------
# 抓取文章图片
# --------------------------
def fetch_article_image(link):
    if not link:
        return None
    try:
        resp = requests.get(link, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        img_url = None

        if "udn.com" in link:
            div = soup.select_one("div#story_body_content")
            if div:
                img = div.find("img")
                if img:
                    img_url = img.get("data-src") or img.get("src")
        elif "ltn.com" in link:
            div = soup.select_one("div.text")
            if div:
                img = div.find("img")
                if img:
                    img_url = img.get("src")
        elif "yahoo.com" in link:
            meta = soup.select_one('meta[property="og:image"]')
            if meta:
                img_url = meta.get("content")
        elif "sinchew.com.my" in link:
            meta = soup.select_one('meta[property="og:image"]')
            if meta:
                img_url = meta.get("content")

        if img_url and img_url.startswith("/"):
            img_url = urljoin(link, img_url)

        return img_url
    except Exception as e:
        print(f"抓文章图片失败 ({link}): {e}")
    return None

# --------------------------
# 抓取站点新闻列表
# --------------------------
def fetch_site_news(url, limit=20):
    news_items = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=30000)
        page.wait_for_timeout(3000)  # 等 JS 加载

        anchors = page.query_selector_all("h2.post-title.entry-title a")[:limit]
        for a in anchors:
            title = a.inner_text().strip()
            link = a.get_attribute("href")
            if link and link.startswith("/"):
                link = urljoin(url, link)
            news_items.append((title, link))
        browser.close()
    return news_items


# --------------------------
# 主流程
# --------------------------
def fetch_news():
    all_news = []
    sites = [
      #  "https://udn.com/news/index",
      #  "https://www.ltn.com.tw",
       # "https://tw.news.yahoo.com/",
        "https://www.sinchew.com.my/latest"
    ]

    for url in sites:
        for title, link in fetch_site_news(url, limit=20):
            if not link or news_exists(link):
                continue
            content = fetch_article_content(link)
            if not content:
                continue
            image_url = fetch_article_image(link)
            title_rw = rewrite_text(title)
            content_rw = rewrite_text(content)
            try:
                insert_news(title_rw, content_rw, link, image_url)
                all_news.append({
                    "title": title_rw,
                    "content": content_rw,
                    "link": link,
                    "image_url": image_url
                })
                print(f"✅ 改写成功并保存: {title_rw[:30]}...")
            except Exception as e:
                print(f"插入失败: {e}")
