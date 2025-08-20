import requests
from bs4 import BeautifulSoup
import random，insert_news, get_db

def simple_rewrite(text):
    """
    简单改写文本，避免直接原文
    """
    words = text.split()
    random.shuffle(words)
    return " ".join(words)

def fetch_news():
    news_list = []

    # ===== 联合新闻网 =====
    try:
        url_udn = "https://udn.com/news/index"
        resp = requests.get(url_udn, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(".story-list__text")  # 示例 selector，需确认
        for item in items[:5]:  # 只取前5条
            title = simple_rewrite(item.get_text(strip=True))
            link_tag = item.find("a")
            link = link_tag["href"] if link_tag else url_udn
            news_list.append({"title": title, "link": link})
    except Exception as e:
        print("抓联合新闻网出错:", e)

    # ===== 自由时报 =====
    try:
        url_ltn = "https://www.ltn.com.tw"
        resp = requests.get(url_ltn, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(".title")  # 示例 selector
        for item in items[:5]:
            title = simple_rewrite(item.get_text(strip=True))
            link_tag = item.find("a")
            link = link_tag["href"] if link_tag else url_ltn
            news_list.append({"title": title, "link": link})
    except Exception as e:
        print("抓自由时报出错:", e)

    # ===== Yahoo 新闻华语 =====
    try:
        url_yahoo = "https://tw.news.yahoo.com/"
        resp = requests.get(url_yahoo, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("h3")  # 示例 selector
        for item in items[:5]:
            title = simple_rewrite(item.get_text(strip=True))
            link_tag = item.find("a")
            link = link_tag["href"] if link_tag else url_yahoo
            news_list.append({"title": title, "link": link})
    except Exception as e:
        print("抓 Yahoo 新闻出错:", e)

    return news_list

def init_db():
    from database import init_db
    init_db()
