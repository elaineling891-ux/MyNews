from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from harvest import fetch_news, init_db

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    news = fetch_news()
    return templates.TemplateResponse("index.html", {"request": request, "news": news})
