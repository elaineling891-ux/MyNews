import requests
from bs4 import BeautifulSoup
from db import insert_news, news_exists
from deep_translator import GoogleTranslator
import time
from urllib.parse import urljoin

def rewrite_text(text):
    if not text:
        return ""
    try:
        en = GoogleTranslator(source="auto", target="en").translate(text)
        zh = GoogleTranslator(source="en", target="zh-CN").translate(en)
        return zh
    except:
        return text

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
            # UDN 内容在 div#story_body_content
            div = soup.select_one("div#story_body_content")
        elif "ltn.com" in link:
            # LTN 内容在 div.text p
            div = soup.select_one("div.text")
        elif "yahoo.com" in link:
            # Yahoo 内容在 article p
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
    """抓文章正文里的第一张图片"""
    if not link:
        return None
    try:
        resp = requests.get(link, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        # 默认没有图片
        img_url = None

        if "udn.com" in link:
            div = soup.select_one("div#story_body_content")
        elif "ltn.com" in link:
            div = soup.select_one("div.text")
        elif "yahoo.com" in link:
            div = soup.select_one("article")
        else:
            div = None

        if div:
            img = div.find("img")
            if img:
                img_url = img.get("data-src") or img.get("src")
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
            if not link:
                continue
            if news_exists(link):
                continue
            content = fetch_article_content(link)
            if not content:
                continue
            image_url = fetch_article_image(link)
            title_rw = rewrite_text(title)
            content_rw = rewrite_text(content)
            try:
                insert_news(title_rw, content_rw, link, image_url)
                all_news.append({"title": title_rw, "content": content_rw, "link": link})
                print(f"插入成功: {title_rw[:30]}...")
            except Exception as e:
                print(f"插入失败: {e}")
            time.sleep(1)
    print(f"抓取完成，总共 {len(all_news)} 条新新闻")
    return all_news
