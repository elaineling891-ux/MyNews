import requests
from bs4 import BeautifulSoup
from database import insert_news, get_db

# 新闻抓取函数
def fetch_news():
    urls = [
        "https://www.udn.com/news/breaknews/1",   # 联合新闻网
        "https://www.ltn.com.tw/news",           # 自由时报
        "https://tw.news.yahoo.com/"             # Yahoo新闻华语
    ]
    news_list = []
    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # 这里根据实际网页结构写 selector
                titles = soup.select("a")[:5]  # 仅示例
                for t in titles:
                    news_item = {"title": t.get_text(), "link": t.get("href")}
                    news_list.append(news_item)
                    insert_news(news_item)
        except Exception as e:
            print("抓取出错:", e)
    return news_list

def init_db():
    from database import init_db
    init_db()
