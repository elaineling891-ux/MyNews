import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from harvest import fetch_news, init_db
from db import get_all_news
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

news_cache = []

# --------------------------
# 启动事件：初始化 DB + 异步抓新闻
# --------------------------
@app.on_event("startup")
async def startup_event():
    init_db()  # 初始化表
    asyncio.create_task(load_news())  # 异步抓新闻

async def load_news():
    global news_cache
    loop = asyncio.get_event_loop()
    news_cache = await loop.run_in_executor(None, fetch_news)  # 异步调用同步抓新闻函数

# --------------------------
# 首页
# --------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    if not news_cache:
        news_cache[:] = get_all_news()  # 如果缓存为空，从数据库拉取
    return templates.TemplateResponse("index.html", {
        "request": request,
        "news": news_cache,
        "year": datetime.now().year
    })

# --------------------------
# 新闻详情页
# --------------------------
@app.get("/news/{news_id}", response_class=HTMLResponse)
async def news_detail(request: Request, news_id: int):
    if 0 <= news_id < len(news_cache):
        news_item = news_cache[news_id]
        return templates.TemplateResponse("detail.html", {
            "request": request,
            "news_item": news_item,
            "year": datetime.now().year
        })
    return HTMLResponse(content="新闻不存在", status_code=404)

# --------------------------
# JSON API
# --------------------------
@app.get("/api/news", response_class=JSONResponse)
async def api_news():
    if not news_cache:
        news_cache[:] = get_all_news()
    return {"news": news_cache}

# --------------------------
# 测试数据库连接
# --------------------------
@app.get("/check_db")
async def check_db():
    try:
        news = get_all_news()
        return {"tables_exist": True, "news_count": len(news)}
    except Exception as e:
        return {"tables_exist": False, "error": str(e)}

# --------------------------
# Uvicorn 入口
# --------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
