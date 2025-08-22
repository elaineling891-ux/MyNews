import requests
from bs4 import BeautifulSoup
from db import insert_news, news_exists
import time
from urllib.parse import urljoin
import os

AI21_API_KEY = os.getenv("AI21_API_KEY")  # AI21 Studio API Key
AI21_MODEL = "j2-large"  # 可根据需求选择 j2-large, j2-grande 等

# --------------------------
# 调用 AI21 Studio 改写
# --------------------------
def rewrite_text_jamba(text):
    if not text:
        return text
    url = "https://api.ai21.com/studio/v1/jamba-large/complete"
    headers = {
        "Authorization": f"Bearer {AI21_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"请帮我改写以下内容，保持意思不变，但用不同表达方式：\n\n{text}"
    data = {
        "prompt": prompt,
        "numResults": 1,
        "maxTokens": 800,
        "temperature": 0.7,
        "topP": 1,
        "stopSequences": []
    }
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=20)
        resp.raise_for_status()
        output = resp.json()
        if "completions" in output and len(output["completions"]) > 0:
            return output["completions"][0]["data"]["text"].strip()
        return text
    except Exception as e:
        print("Jamba 改写失败:", e)
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

def rewrite_text(text):
    rewritten = rewrite_text_jamba(text)
    return add_linebreaks(rewritten)

# --------------------------
# 以下抓取文章内容、图片、网站新闻等保持不变
# --------------------------
def fetch_article_content(link):
    if not link:
        return ""
    try:
        resp = requests.get(link, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        if "udn.com" in link:
            div = soup.select_one("div#story_body_content")
        elif "ltn.com" in link:
            div = soup.select_one("div.text")
        elif "yahoo.com" in link:
            div = soup.select_one("article")
        else:
            div = None

        if div:
            paragraphs = div.find_all("p")
            content = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            return content
    except Exception as e:
        print(f"抓文章内容失败 ({link}): {e}")
    return ""

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

        if img_url and img_url.startswith("/"):
            img_url = urljoin(link, img_url)

        return img_url
    except Exception as e:
        print(f"抓文章图片失败 ({link}): {e}")
    return None

def fetch_site_news(url, limit=20):
    news_items = []
    try:
        resp = requests.get(url, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")

        if "udn.com" in url:
            items = soup.select("div.story-list__text a")
        elif "ltn.com" in url:
            items = soup.select("div.title a")
        elif "yahoo.com" in url:
            items = soup.select("h3 a")
        else:
            items = []

        for item in items[:limit]:
            title = item.get_text(strip=True)
            link = item.get("href")
            if link and link.startswith("/"):
                link = urljoin(url, link)
            news_items.append((title, link))
    except Exception as e:
        print(f"抓 {url} 出错: {e}")
    return news_items

def fetch_news():
    all_news = []
    sites = [
        "https://udn.com/news/index",
        "https://www.ltn.com.tw",
        "https://tw.news.yahoo.com/"
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
                print(f"插入成功: {title_rw[:30]}...")
            except Exception as e:
                print(f"插入失败: {e}")
            time.sleep(1)
    print(f"抓取完成，总共 {len(all_news)} 条新新闻")
    return all_news
