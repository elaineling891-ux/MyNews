import requests
from bs4 import BeautifulSoup
from db import insert_news
from deep_translator import GoogleTranslator

def rewrite_text(text):
    if not text:
        return ""
    try:
        # 英文 -> 中文 -> 英文，起到免费“改写”效果
        en = GoogleTranslator(source="auto", target="en").translate(text)
        zh = GoogleTranslator(source="en", target="zh-CN").translate(en)
        return zh
    except:
        return text

def fetch_article_content(link, selector):
    if not link:
        return ""
    try:
        resp = requests.get(link, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        content_tag = soup.select_one(selector)
        if content_tag:
            return content_tag.get_text(strip=True)
    except:
        pass
    return ""

def fetch_site_news(url, title_selector, content_selector, limit=20):
    news_items = []
    try:
        resp = requests.get(url, timeout=40)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(title_selector)
        for item in items[:limit]:
            title = item.get_text(strip=True)
            link_tag = item.find("a")
            link = link_tag["href"] if link_tag else None
            news_items.append((title, link, content_selector))
    except:
        pass
    return news_items

def fetch_news():
    all_news = []

    sites = [
        ("https://udn.com/news/index", ".story-list__text", ".article-content p"),
        ("https://www.ltn.com.tw", ".title", ".text"),
        ("https://tw.news.yahoo.com/", "h3", "p")
    ]

    for url, title_sel, content_sel in sites:
        for title, link, sel in fetch_site_news(url, title_sel, content_sel):
            title_rw = rewrite_text(title)
            content_rw = rewrite_text(fetch_article_content(link, sel))
            insert_news(title_rw, content_rw)
            all_news.append({"title": title_rw, "content": content_rw})

    return all_news
