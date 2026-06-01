"""메인 FastAPI 앱 — 네이버 쇼핑 검색 (루트 제공)."""
import re

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.models import mongodb
from app.models.shopping import ShoppingModel
from app.shopping_scraper import NaverShoppingScraper

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ──────────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────────

def _to_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _strip_tags(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text)


def _normalize_item(keyword: str, item: dict) -> dict:
    return {
        "keyword": keyword,
        "title": _strip_tags(item.get("title", "")),
        "link": item.get("link", ""),
        "image": item.get("image", ""),
        "lprice": _to_int(item.get("lprice", 0)),
        "hprice": _to_int(item.get("hprice", 0)),
        "mall_name": item.get("mallName", ""),
        "product_id": str(item.get("productId", "")),
        "brand": item.get("brand", ""),
        "maker": item.get("maker", ""),
        "category1": item.get("category1", ""),
        "category2": item.get("category2", ""),
        "category3": item.get("category3", ""),
        "category4": item.get("category4", ""),
    }


# ──────────────────────────────────────────────
# 페이지 라우터
# ──────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "쇼핑 검색"},
    )


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = "", sort: str = "date"):
    keyword = q.strip()

    if not keyword:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"title": "쇼핑 검색", "message": "검색어를 입력해주세요"},
        )

    if sort not in ("date", "asc", "dsc", "sim"):
        sort = "date"

    scraper = NaverShoppingScraper()
    items_raw = await scraper.search(keyword, sort=sort)
    items = [_normalize_item(keyword, item) for item in items_raw]

    shop_models = [ShoppingModel(**i) for i in items]
    if shop_models:
        await mongodb.engine.save_all(shop_models)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": f"{keyword} 검색결과",
            "keyword": keyword,
            "sort": sort,
            "items": items,
        },
    )


# ──────────────────────────────────────────────
# JSON API (AJAX 정렬용)
# ──────────────────────────────────────────────

@app.get("/api/shop")
async def api_shop(q: str = "", sort: str = "date"):
    keyword = q.strip()
    if not keyword:
        return JSONResponse({"items": []})

    if sort not in ("date", "asc", "dsc", "sim"):
        sort = "date"

    scraper = NaverShoppingScraper()
    items_raw = await scraper.search(keyword, sort=sort)
    items = [_normalize_item(keyword, item) for item in items_raw]
    return JSONResponse({"items": items})


# ──────────────────────────────────────────────
# 수명주기
# ──────────────────────────────────────────────

@app.on_event("startup")
async def on_app_start():
    print("hello server")
    mongodb.connect()


@app.on_event("shutdown")
async def on_app_shutdown():
    print("goodbye server")
    mongodb.close()
