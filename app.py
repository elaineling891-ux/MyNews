import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from db import get_all_news, init_db  # 从数据库读取新闻
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --------------------------
# 启动事件：初始化数据库
# --------------------------
@app.on_event("startup")
async def startup_event():
    init_db()  # 初始化表（建表，如果不存在）
    # ⚠️ 这里可以选择不抓新闻，只显示已有数据库内容
    # 如果需要后台抓新闻可再加 asyncio.create_task(fetch_news())

# --------------------------
# 首页：从数据库读取新闻
# --------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    news = get_all_news()  # 直接从数据库拉取
    return templates.TemplateResponse("index.html", {
        "request": request,
        "news": news,
        "year": datetime.now().year
    })

# --------------------------
# 新闻详情页
# --------------------------
@app.get("/news/{news_id}", response_class=HTMLResponse)
async def news_detail(request: Request, news_id: int):
    news_list = get_all_news()  # 从数据库读取
    for item in news_list:
        if item["id"] == news_id:
            return templates.TemplateResponse("detail.html", {
                "request": request,
                "news_item": item,
                "year": datetime.now().year
            })
    return HTMLResponse(content="新闻不存在", status_code=404)

# --------------------------
# JSON API：从数据库读取新闻
# --------------------------
@app.get("/api/news", response_class=JSONResponse)
async def api_news():
    news = get_all_news()
    return {"news": news}

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
