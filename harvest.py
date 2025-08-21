import requests
from bs4 import BeautifulSoup
from db import insert_news, news_exists
from deep_translator import GoogleTranslator

# --------------------------
# 免费改写函数（Google 翻译）
# --------------------------
def rewrite_text(text):
    if not text:
        return ""
    try:
        # 英文 -> 中文 -> 英文 反复翻译，达到改写效果
        en = GoogleTranslator(source="auto", target="en").translate(text)
        zh = GoogleTranslator(source="en", target="zh-CN").translate(en)
        return zh
    except:
        return text

# --------------------------
# 抓文章内容，按网站选择 selector
# --------------------------
def fetch_article_content(link, site="udn"):
    if not link:
        return ""
    try:
        resp = requests.get(link, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        if "udn.com" in site:
            div = soup.select_one("div.article-content")
        elif "ltn.com" in site:
            div = soup.select_one("div.text")
        elif "yahoo.com" in site:
            div = soup.select_one("div[class*='caas-body']")
        else:
            div = None

        if div:
            paragraphs = div.find_all("p")
            return "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    except Exception as e:
        print(f"抓文章内容失败: {e}")
    return ""

# --------------------------
# 抓网站新闻标题和链接
# --------------------------
def fetch_site_news(url, title_selector, limit=20):
    news_items = []
    try:
        resp = requests.get(url, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(title_selector)
        for item in items[:limit]:
            title = item.get_text(strip=True)
            link_tag = item.find("a")
            link = link_tag["href"] if link_tag else None
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
        ("https://udn.com/news/index", ".story-list__text"),
        ("https://www.ltn.com.tw", ".title"),
        ("https://tw.news.yahoo.com/", "h3")
    ]

    for url, title_sel in sites:
        for title, link in fetch_site_news(url, title_sel, limit=20):
            # 避免重复抓取
            if news_exists(link):
                continue

            # 改写标题和内容
            title_rw = rewrite_text(title)
            content_rw = rewrite_text(fetch_article_content(link, url))

            # 插入数据库
            insert_news(title_rw, content_rw, link)
            all_news.append({"title": title_rw, "content": content_rw, "link": link})

    return all_news
