"""메인 FastAPI 앱 — 네이버 쇼핑 검색 (루트 제공)."""
import re

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.models import mongodb
from app.models.shopping import ShoppingModel
from app.models.favorite import FavoriteModel
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
        await mongodb.get_engine().save_all(shop_models)

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
# 즐겨찾기 API
# ──────────────────────────────────────────────

@app.get("/api/favorites")
async def get_favorites():
    """저장된 즐겨찾기 전체 반환."""
    engine = mongodb.get_engine()
    favs = await engine.find(FavoriteModel)
    return JSONResponse({"items": [dict(f) for f in favs]})


@app.post("/api/favorites")
async def add_favorite(request: Request):
    """즐겨찾기 추가 (중복이면 무시)."""
    data = await request.json()
    pid = str(data.get("product_id", "")).strip()
    if not pid:
        return JSONResponse({"ok": False, "error": "product_id 없음"}, status_code=400)

    engine = mongodb.get_engine()
    existing = await engine.find_one(FavoriteModel, FavoriteModel.product_id == pid)
    if existing:
        return JSONResponse({"ok": True, "created": False})

    fav = FavoriteModel(
        product_id=pid,
        title=data.get("title", ""),
        link=data.get("link", ""),
        image=data.get("image", ""),
        lprice=int(data.get("lprice", 0)),
        hprice=int(data.get("hprice", 0)),
        mall_name=data.get("mall_name", ""),
        brand=data.get("brand", ""),
        maker=data.get("maker", ""),
        category1=data.get("category1", ""),
        category2=data.get("category2", ""),
        category3=data.get("category3", ""),
        category4=data.get("category4", ""),
    )
    await engine.save(fav)
    return JSONResponse({"ok": True, "created": True})


@app.delete("/api/favorites/{product_id}")
async def remove_favorite(product_id: str):
    """즐겨찾기 삭제."""
    engine = mongodb.get_engine()
    fav = await engine.find_one(FavoriteModel, FavoriteModel.product_id == product_id)
    if fav:
        await engine.delete(fav)
    return JSONResponse({"ok": True})


# ──────────────────────────────────────────────
# 수명주기
# ──────────────────────────────────────────────

@app.on_event("startup")
async def on_app_start():
    # 로컬 실행 시 미리 연결; Vercel 서버리스는 get_engine()이 대신 처리
    print("hello server")
    mongodb.connect()


@app.on_event("shutdown")
async def on_app_shutdown():
    print("goodbye server")
    mongodb.close()
