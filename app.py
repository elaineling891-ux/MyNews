from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from harvest import fetch_news, init_db
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

news_cache = []

@app.on_event("startup")
def startup_event():
    global news_cache
    init_db()
    news_cache = fetch_news()

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

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
