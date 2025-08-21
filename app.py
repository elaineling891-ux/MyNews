import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from db import get_all_news, init_db
from harvest import fetch_news
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --------------------------
# 启动事件：初始化 DB + 异步定时抓新闻
# --------------------------
@app.on_event("startup")
async def startup_event():
    init_db()
    asyncio.create_task(periodic_fetch_news(1800))  # 每小时抓一次新闻

async def periodic_fetch_news(interval=1800):
    while True:
        try:
            print("⏳ 开始抓新闻...")
            await asyncio.get_event_loop().run_in_executor(None, fetch_news)
            print("✅ 抓新闻完成")
        except Exception as e:
            print("抓新闻出错:", e)
        await asyncio.sleep(interval)

# --------------------------
# 首页
# --------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    news = get_all_news()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "news": news,
        "year": datetime.now().year
    })

from db import get_all_news

@app.get("/news/{index}", response_class=HTMLResponse)
async def news_detail(request: Request, index: int):
    news_list = get_all_news()  # 按 created_at DESC 排序
    if 0 <= index < len(news_list):
        news_item = news_list[index]
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
    return {"news": get_all_news()}

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

@app.post("/manual_fetch")
async def manual_fetch():
    try:
        # 异步调用同步抓新闻函数
        import asyncio
        new_news = await asyncio.get_event_loop().run_in_executor(None, fetch_news)
        return {"status": "success", "fetched_count": len(new_news)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --------------------------
# Uvicorn 入口
# --------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
