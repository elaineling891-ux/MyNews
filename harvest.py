import requests
from bs4 import BeautifulSoup 
from db import insert_news, get_db
import random

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
        items = soup.select(".story-list__text h2 a")
        for item in items[:5]:
            title = item.get_text(strip=True)
            link = "https://udn.com" + item["href"]

            content = ""
            try:
                art_resp = requests.get(link, timeout=10)
                art_soup = BeautifulSoup(art_resp.text, "html.parser")
                paragraphs = art_soup.select(".article-content__paragraph")
                content = " ".join(p.get_text(strip=True) for p in paragraphs)
            except:
                pass

            # 改写
            title_rw = simple_rewrite(title)
            content_rw = simple_rewrite(content)
            insert_news(title_rw, content_rw)
            news_list.append({"title": title_rw, "content": content_rw})
    except Exception as e:
        print("抓联合新闻网出错:", e)

    # ===== 自由时报 =====
    try:
        url_ltn = "https://news.ltn.com.tw/list/breakingnews"
        resp = requests.get(url_ltn, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("ul.list > li > a")
        for item in items[:5]:
            title = item.get_text(strip=True)
            link = item["href"]

            content = ""
            try:
                art_resp = requests.get(link, timeout=10)
                art_soup = BeautifulSoup(art_resp.text, "html.parser")
                paragraphs = art_soup.select("div.text p")
                content = " ".join(p.get_text(strip=True) for p in paragraphs)
            except:
                pass

            # 改写
            title_rw = simple_rewrite(title)
            content_rw = simple_rewrite(content)
            insert_news(title_rw, content_rw)
            news_list.append({"title": title_rw, "content": content_rw})
    except Exception as e:
        print("抓自由时报出错:", e)

    # ===== Yahoo 新闻华语 =====
    try:
        url_yahoo = "https://tw.news.yahoo.com/"
        resp = requests.get(url_yahoo, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("h3 a")
        for item in items[:5]:
            title = item.get_text(strip=True)
            link = item["href"]

            # Yahoo 链接有可能是相对路径，补全
            if link.startswith("/"):
                link = "https://tw.news.yahoo.com" + link

            content = ""
            try:
                art_resp = requests.get(link, timeout=10)
                art_soup = BeautifulSoup(art_resp.text, "html.parser")
                paragraphs = art_soup.select("div.caas-body p")
                content = " ".join(p.get_text(strip=True) for p in paragraphs)
            except:
                pass

            # 改写
            title_rw = simple_rewrite(title)
            content_rw = simple_rewrite(content)
            insert_news(title_rw, content_rw)
            news_list.append({"title": title_rw, "content": content_rw})
    except Exception as e:
        print("抓 Yahoo 新闻出错:", e)

    return news_list
    
def init_db():
    from db import init_db
    init_db()
