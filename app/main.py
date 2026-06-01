from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import re

from app.models import mongodb
from app.models.book import BookModel
from app.book_scraper import NaverBookScraper

app = FastAPI()


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _to_int(value) -> int:
    """네이버 응답의 가격 필드처럼 빈 문자열/None/숫자 문자열을 안전하게 int로."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _strip_tags(text: str) -> str:
    """네이버 title 등에 섞여오는 <b> 같은 태그 제거."""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "북북"},
    )


@app.get("/search", response_class=HTMLResponse)
async def read_item(request: Request, q: str = ""):
    keyword = q.strip()

    if not keyword:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"title": "북북", "message": "검색어를 입력해주세요"},
        )

    naver_book_scraper = NaverBookScraper()
    books = await naver_book_scraper.search(keyword, 10)

    book_models = []
    for book in books:
        book_model = BookModel(
            keyword=keyword,
            title=_strip_tags(book.get("title", "")),
            author=_strip_tags(book.get("author", "")).replace("^", ", "),
            publisher=book.get("publisher", ""),
            price=_to_int(book.get("discount")),
            image=book.get("image", ""),
        )
        book_models.append(book_model)

    if book_models:
        await mongodb.engine.save_all(book_models)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "북북", "keyword": keyword, "books": book_models},
    )


@app.on_event("startup")
async def on_app_start():
    print("hello server")
    mongodb.connect()


@app.on_event("shutdown")
async def on_app_shutdown():
    print("goodbye server")
    mongodb.close()
