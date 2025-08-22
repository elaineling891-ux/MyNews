import requests
from bs4 import BeautifulSoup
from db import insert_news
from deep_translator import GoogleTranslator
import os

# 从环境变量获取 DeepAI API Key
DEEPAI_API_KEY = os.getenv("DEEPAI_API_KEY")

# 改写函数：调用 DeepAI Text Paraphrasing API
def paraphrase_text(text):
    if not DEEPAI_API_KEY:
        print("❌ DeepAI API key not found. Returning original text.")
        return text

    try:
        response = requests.post(
            "https://api.deepai.org/api/text-paraphraser",
            data={'text': text},
            headers={'api-key': DEEPAI_API_KEY}
        )
        response.raise_for_status()
        result = response.json()
        return result.get("output", text)  # DeepAI 返回 "output" 字段
    except Exception as e:
        print(f"⚠️ DeepAI 改写失败: {e}, 使用原始文本")
        return text

# 爬取新闻并保存
def harvest_news(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')

    title = soup.select_one("h1").get_text(strip=True)
    paragraphs = [p.get_text(strip=True) for p in soup.select("p")]
    content = "\n\n".join(paragraphs)  # 保持分段

    # 改写内容
    rewritten = paraphrase_text(content)

    # 翻译成中文
    translated = GoogleTranslator(source='en', target='zh-cn').translate(rewritten)

    # 图片
    img_tag = soup.select_one("img")
    image_url = img_tag["src"] if img_tag else None

    # 存入数据库
    insert_news(title, translated, image_url)

    print(f"✅ 已抓取并改写: {title}")

if __name__ == "__main__":
    test_url = "https://example.com/news/test"  # 你换成目标新闻网址
    harvest_news(test_url)
