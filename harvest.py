import requests
from bs4 import BeautifulSoup
from db import insert_news
from openai import OpenAI
import os

# 初始化 OpenAI 客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ===== 改写函数（调用 OpenAI API） =====
def rewrite_text(text):
    if not text:
        return ""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 可以换成 gpt-4o / gpt-4o-mini
            messages=[
                {"role": "system", "content": "你是一个新闻改写助手，请把输入的文字改写成简洁流畅的中文，避免重复。"},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("改写失败:", e)
        return text


# ===== 抓取新闻 =====
def fetch_news():
    news_list = []

    # ===== 联合新闻网 =====
    try:
        url_udn = "https://udn.com/news/index"
        resp = requests.get(url_udn, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(".story-list__text")
        for item in items[:5]:
            title = item.get_text(strip=True)
            link_tag = item.find("a")
            link = link_tag["href"] if link_tag else None
            content = ""
            if link:
                try:
                    art_resp = requests.get(link, timeout=10)
                    art_soup = BeautifulSoup(art_resp.text, "html.parser")
                    content_tag = art_soup.select_one(".article-content p")
                    if content_tag:
                        content = content_tag.get_text(strip=True)
                except:
                    pass

            title_rw = rewrite_text(title)
            content_rw = rewrite_text(content)

            insert_news(title_rw, content_rw)
            news_list.append({"title": title_rw, "content": content_rw})
    except Exception as e:
        print("抓联合新闻网出错:", e)

    # ===== 自由时报 =====
    try:
        url_ltn = "https://www.ltn.com.tw"
        resp = requests.get(url_ltn, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(".title")
        for item in items[:5]:
            title = item.get_text(strip=True)
            link_tag = item.find("a")
            link = link_tag["href"] if link_tag else None
            content = ""
            if link:
                try:
                    art_resp = requests.get(link, timeout=10)
                    art_soup = BeautifulSoup(art_resp.text, "html.parser")
                    content_tag = art_soup.select_one(".text")
                    if content_tag:
                        content = content_tag.get_text(strip=True)
                except:
                    pass

            title_rw = rewrite_text(title)
            content_rw = rewrite_text(content)

            insert_news(title_rw, content_rw)
            news_list.append({"title": title_rw, "content": content_rw})
    except Exception as e:
        print("抓自由时报出错:", e)

    # ===== Yahoo 新闻 =====
    try:
        url_yahoo = "https://tw.news.yahoo.com/"
        resp = requests.get(url_yahoo, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("h3")
        for item in items[:5]:
            title = item.get_text(strip=True)
            link_tag = item.find("a")
            link = link_tag["href"] if link_tag else None
            content = ""
            if link:
                try:
                    art_resp = requests.get(link, timeout=10)
                    art_soup = BeautifulSoup(art_resp.text, "html.parser")
                    content_tag = art_soup.select_one("p")
                    if content_tag:
                        content = content_tag.get_text(strip=True)
                except:
                    pass

            title_rw = rewrite_text(title)
            content_rw = rewrite_text(content)

            insert_news(title_rw, content_rw)
            news_list.append({"title": title_rw, "content": content_rw})
    except Exception as e:
        print("抓 Yahoo 新闻出错:", e)

    return news_list


def init_db():
    from db import init_db
    init_db()
