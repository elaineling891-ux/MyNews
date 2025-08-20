import requests
from bs4 import BeautifulSoup
from db import insert_news
from transformers import pipeline
from googletrans import Translator

# 初始化 Hugging Face 改写模型
paraphrase = pipeline("text2text-generation", model="Vamsi/T5_Paraphrase_Paws")

# 初始化翻译器
translator = Translator()

def rewrite_and_translate(text):
    # 改写
    try:
        result = paraphrase(text, max_length=256, do_sample=True, top_k=50)
        rewritten = result[0]['generated_text']
    except Exception as e:
        print("改写失败:", e)
        rewritten = text

    # 翻译成简体中文
    try:
        simplified = translator.translate(rewritten, dest='zh-CN').text
    except Exception as e:
        print("翻译失败:", e)
        simplified = rewritten

    return simplified

def fetch_news():
    news_list = []

    # ===== 联合新闻网 =====
    try:
        url_udn = "https://udn.com/news/index"
        resp = requests.get(url_udn, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(".story-list__text")  # 联合新闻网新闻列表选择器
        for item in items[:5]:
            title = item.get_text(strip=True)
            link_tag = item.find("a")
            link = link_tag["href"] if link_tag else None
            content = ""
            if link:
                try:
                    art_resp = requests.get(link, timeout=10)
                    art_soup = BeautifulSoup(art_resp.text, "html.parser")
                    content_tag = art_soup.select_one(".article-content p")  # 内容选择器
                    if content_tag:
                        content = content_tag.get_text(strip=True)
                except:
                    pass

            title_rw = rewrite_and_translate(title)
            content_rw = rewrite_and_translate(content)

            insert_news(title_rw, content_rw)
            news_list.append({"title": title_rw, "content": content_rw})
    except Exception as e:
        print("抓联合新闻网出错:", e)

    # ===== 自由时报 =====
    try:
        url_ltn = "https://www.ltn.com.tw"
        resp = requests.get(url_ltn, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(".title")  # 自由时报标题选择器
        for item in items[:5]:
            title = item.get_text(strip=True)
            link_tag = item.find("a")
            link = link_tag["href"] if link_tag else None
            content = ""
            if link:
                try:
                    art_resp = requests.get(link, timeout=10)
                    art_soup = BeautifulSoup(art_resp.text, "html.parser")
                    content_tag = art_soup.select_one(".text")  # 内容选择器
                    if content_tag:
                        content = content_tag.get_text(strip=True)
                except:
                    pass

            title_rw = rewrite_and_translate(title)
            content_rw = rewrite_and_translate(content)

            insert_news(title_rw, content_rw)
            news_list.append({"title": title_rw, "content": content_rw})
    except Exception as e:
        print("抓自由时报出错:", e)

    # ===== Yahoo 新闻华语 =====
    try:
        url_yahoo = "https://tw.news.yahoo.com/"
        resp = requests.get(url_yahoo, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("h3")  # Yahoo 新闻标题选择器
        for item in items[:5]:
            title = item.get_text(strip=True)
            link_tag = item.find("a")
            link = link_tag["href"] if link_tag else None
            content = ""
            if link:
                try:
                    art_resp = requests.get(link, timeout=10)
                    art_soup = BeautifulSoup(art_resp.text, "html.parser")
                    content_tag = art_soup.select_one("p")  # 内容选择器
                    if content_tag:
                        content = content_tag.get_text(strip=True)
                except:
                    pass

            title_rw = rewrite_and_translate(title)
            content_rw = rewrite_and_translate(content)

            insert_news(title_rw, content_rw)
            news_list.append({"title": title_rw, "content": content_rw})
    except Exception as e:
        print("抓 Yahoo 新闻出错:", e)

    return news_list

def init_db():
    from db import init_db
    init_db()
