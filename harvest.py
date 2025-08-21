import requests
from bs4 import BeautifulSoup
from db import insert_news, news_exists
from deep_translator import GoogleTranslator
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

# --------------------------
# 免费改写函数（Google 翻译）
# --------------------------
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
        resp = requests.get(link, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        if "udn.com" in link:
            div = soup.select_one("div.article-content")
        elif "ltn.com" in link:
            div = soup.select_one("div.text")
        elif "yahoo.com" in link:
            div = soup.select_one("div[class*='caas-body']")
        else:
            div = None

        if div:
            paragraphs = div.find_all("p")
            content = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            return content
    except Exception as e:
        print(f"抓文章内容失败 {link}: {e}")
    return ""

# --------------------------
# 抓网站标题 + 链接
# --------------------------
def fetch_site_news(url, title_selector, limit=20):
    news_items = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(title_selector)
        for item in items[:limit]:
            title = item.get_text(strip=True)
            link_tag = item.find("a")
            if link_tag and link_tag.get("href"):
                link = urljoin(url, link_tag.get("href"))
            else:
                link = None
            news_items.append((title, link))
    except Exception as e:
        print(f"抓 {url} 出错: {e}")
    return news_items

# --------------------------
# 抓所有新闻
# --------------------------
def fetch_news():
    all_news = []

    sites = [
        ("https://udn.com/news/index", ".story-list__text"),
        ("https://www.ltn.com.tw", ".title"),
        ("https://tw.news.yahoo.com/", "h3")
    ]

    for url, selector in sites:
        for title, link in fetch_site_news(url, selector, limit=20):
            if not link or news_exists(link):
                continue

            title_rw = rewrite_text(title)
            content_rw = rewrite_text(fetch_article_content(link))
            if content_rw:  # 内容不为空才插入
                insert_news(title_rw, content_rw, link)
                all_news.append({"title": title_rw, "content": content_rw, "link": link})

    return all_news
