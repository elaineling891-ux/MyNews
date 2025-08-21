import requests
from bs4 import BeautifulSoup
from db import insert_news, news_exists
from deep_translator import GoogleTranslator
import time

# --------------------------
# 免费改写函数（Google 翻译）
# --------------------------
def rewrite_text(text):
    if not text:
        return ""
    try:
        # 英文 -> 中文 -> 英文，达到改写效果
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

        # 根据网站选择 selector
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
        print(f"抓文章内容失败 ({link}): {e}")
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
            if link and link.startswith("/"):
                # 补全相对链接
                from urllib.parse import urljoin
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
        ("https://udn.com/news/index", ".story-list__text"),
        ("https://www.ltn.com.tw", ".title"),
        ("https://tw.news.yahoo.com/", "h3")
    ]

    for url, title_sel in sites:
        site_name = url.split("//")[1].split("/")[0]
        for title, link in fetch_site_news(url, title_sel, limit=20):
            if not link:
                continue
            # 避免重复抓取
            if news_exists(link):
                print(f"已存在，跳过: {link}")
                continue

            # 抓文章内容
            content = fetch_article_content(link)
            if not content:
                print(f"内容为空，跳过: {link}")
                continue

            # 改写标题和内容
            title_rw = rewrite_text(title)
            content_rw = rewrite_text(content)

            try:
                insert_news(title_rw, content_rw, link)
                all_news.append({"title": title_rw, "content": content_rw, "link": link})
                print(f"插入成功: {title_rw[:30]}...")
            except Exception as e:
                print(f"插入失败: {e}")

            # 避免频繁请求，可加小延迟
            time.sleep(1)

    print(f"抓取完成，总共 {len(all_news)} 条新新闻")
    return all_news
