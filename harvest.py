import requests
from bs4 import BeautifulSoup
from db import insert_news
from concurrent.futures import ThreadPoolExecutor, as_completed
from transformers import pipeline

# 初始化改写模型
paraphrase = pipeline("text2text-generation", model="Vamsi/T5_Paraphrase_Paws")

def rewrite_text(text):
    if not text:
        return ""
    try:
        result = paraphrase(text, max_length=300, do_sample=True, top_p=0.9, temperature=0.7)
        return result[0]['generated_text'].strip()
    except Exception as e:
        print("改写失败:", e)
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

def fetch_site_news(url, title_selector, content_selector, limit=5):
    news_items = []
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(title_selector)
        for item in items[:limit]:
            title = item.get_text(strip=True)
            link_tag = item.find("a")
            link = link_tag["href"] if link_tag else None
            news_items.append((title, link, content_selector))
    except Exception as e:
        print(f"抓取 {url} 出错:", e)
    return news_items

def fetch_news():
    all_news = []

    sites = [
        ("https://udn.com/news/index", ".story-list__text", ".article-content p"),
        ("https://www.ltn.com.tw", ".title", ".text"),
        ("https://tw.news.yahoo.com/", "h3", "p")
    ]

    # 先抓标题和链接
    news_tasks = []
    for url, title_sel, content_sel in sites:
        news_tasks.extend(fetch_site_news(url, title_sel, content_sel))

    # 并行抓内容 + 改写
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_news = {
            executor.submit(
                lambda t: (rewrite_text(t[0]), rewrite_text(fetch_article_content(t[1], t[2]))),
                news
            ): news for news in news_tasks
        }
        for future in as_completed(future_to_news):
            try:
                title_rw, content_rw = future.result()
                insert_news(title_rw, content_rw)
                all_news.append({"title": title_rw, "content": content_rw})
            except Exception as e:
                print("处理新闻出错:", e)

    return all_news

def init_db():
    from db import init_db
    init_db()
