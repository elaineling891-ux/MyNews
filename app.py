import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from db import init_db, get_all_news
from harvest import fetch_news  # 你之前写好的抓新闻函数

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 缓存新闻
news_cache = []

# --------------------------
# 启动事件：初始化数据库 + 定时抓新闻
# --------------------------
@app.on_event("startup")
async def startup_event():
    init_db()
    # 启动后台定时抓新闻任务
    asyncio.create_task(periodic_fetch_news(1800))  # 默认每 1800 秒 = 30 分钟

async def periodic_fetch_news(interval: int = 1800):
    global news_cache
    while True:
        try:
            print(f"⏳ [{datetime.now()}] 开始抓新闻...")
            await asyncio.get_event_loop().run_in_executor(None, fetch_news)
            news_cache = get_all_news()  # 更新缓存
            print(f"✅ [{datetime.now()}] 抓新闻完成，当前新闻条数: {len(news_cache)}")
        except Exception as e:
            print(f"❌ 抓新闻出错: {e}")
        await asyncio.sleep(interval)

# --------------------------
# 首页
# --------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    global news_cache
    if not news_cache:
        news_cache = get_all_news()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "news": news_cache,
        "year": datetime.now().year
    })

# --------------------------
# 新闻详情页（按数据库 id）
# --------------------------
@app.get("/news/{news_id}", response_class=HTMLResponse)
async def news_detail(request: Request, news_id: int):
    global news_cache
    if not news_cache:
        news_cache = get_all_news()
    for item in news_cache:
        if item["id"] == news_id:
            return templates.TemplateResponse("detail.html", {
                "request": request,
                "news_item": item,
                "year": datetime.now().year
            })
    return HTMLResponse(content="新闻不存在", status_code=404)

# --------------------------
# JSON API
# --------------------------
@app.get("/api/news", response_class=JSONResponse)
async def api_news():
    global news_cache
    if not news_cache:
        news_cache = get_all_news()
    return {"news": news_cache}

# --------------------------
# 手动抓新闻接口
# --------------------------
@app.post("/manual_fetch")
async def manual_fetch():
    global news_cache
    try:
        new_news = await asyncio.get_event_loop().run_in_executor(None, fetch_news)
        news_cache = get_all_news()  # 更新缓存
        return {"status": "success", "fetched_count": len(new_news)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
