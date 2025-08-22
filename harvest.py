import requests
from bs4 import BeautifulSoup
from db import insert_news, news_exists
import time
from urllib.parse import urljoin
import os

HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # Hugging Face Token

# --------------------------
# 调用 Hugging Face 公共模型改写
# --------------------------
def rewrite_text_hf(text):
    """使用公开模型 tuner007/pegasus_paraphrase 改写文本"""
    if not text:
        return ""
    API_URL = "https://api-inference.huggingface.co/models/tuner007/pegasus_paraphrase"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": text,
        "parameters": {"max_length": 512, "do_sample": False}
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]
        return text
    except Exception as e:
        print("Hugging Face 改写失败:", e)
        return text

# --------------------------
# 后处理：添加换行，每3句换一次行
# --------------------------
def add_linebreaks(text, n_sentences=3):
    import re
    sentences = re.split(r'(?<=[。！？])', text)
    lines = []
    for i in range(0, len(sentences), n_sentences):
        lines.append("".join(sentences[i:i+n_sentences]))
    return "\n\n".join(lines)

def rewrite_text(text):
    rewritten = rewrite_text_hf(text)
    return add_linebreaks(rewritten)

# --------------------------
# 抓文章内容
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

# --------------------------
# 抓文章主图
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

        if img_url and img_url.startswith("/"):
            img_url = urljoin(link, img_url)

        return img_url
    except Exception as e:
        print(f"抓文章图片失败 ({link}): {e}")
    return None

# --------------------------
# 抓网站新闻标题和链接
# --------------------------
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

# --------------------------
# 抓所有新闻，改写并插入数据库
# --------------------------
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
