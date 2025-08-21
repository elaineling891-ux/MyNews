import asyncio
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from harvest import fetch_news, init_db
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

news_cache = []

@app.on_event("startup")
async def startup_event():
    global news_cache
    init_db()
    # 🚀 不要阻塞启动，丢给后台跑
    asyncio.create_task(load_news())

async def load_news():
    global news_cache
    news_cache = fetch_news()   # 抓新闻逻辑保持不变

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "news": news_cache,
        "year": datetime.now().year
    })

@app.get("/news/{news_id}", response_class=HTMLResponse)
def news_detail(request: Request, news_id: int):
    if 0 <= news_id < len(news_cache):
        news_item = news_cache[news_id]
        return templates.TemplateResponse("detail.html", {
            "request": request,
            "news_item": news_item,
            "year": datetime.now().year
        })
    return HTMLResponse(content="新闻不存在", status_code=404)
