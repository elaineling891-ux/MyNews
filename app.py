from fastapi import FastAPI
from harvest import fetch_news, init_db

app = FastAPI()

# 启动事件，初始化数据库
@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def home():
    news = fetch_news()
    return {"news": news}
