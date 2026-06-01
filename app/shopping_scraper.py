"""네이버 쇼핑 검색 API 스크래퍼."""
import asyncio
import ssl

import aiohttp
import certifi

from app.config import get_secret


class NaverShoppingScraper:
    NAVER_API_SHOP = "https://openapi.naver.com/v1/search/shop.json"
    NAVER_API_ID = get_secret("NAVER_API_ID")
    NAVER_API_SECRET = get_secret("NAVER_API_SECRET")

    @staticmethod
    async def fetch(session, url, headers):
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("items", [])
            return []

    def _build_url(self, keyword: str, start: int, sort: str = "date") -> dict:
        """
        sort 옵션:
          sim  – 정확도 (네이버 기본)
          date – 날짜 (최신)
          asc  – 가격 낮은 순
          dsc  – 가격 높은 순
        """
        return {
            "url": (
                f"{self.NAVER_API_SHOP}"
                f"?query={keyword}"
                f"&display=100"
                f"&start={start}"
                f"&sort={sort}"
            ),
            "headers": {
                "X-Naver-Client-Id": self.NAVER_API_ID,
                "X-Naver-Client-Secret": self.NAVER_API_SECRET,
            },
        }

    async def search(self, keyword: str, sort: str = "date") -> list[dict]:
        """네이버 쇼핑 API에서 최대 100개 결과를 반환한다."""
        api = self._build_url(keyword, start=1, sort=sort)

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)

        async with aiohttp.ClientSession(connector=connector) as session:
            items = await NaverShoppingScraper.fetch(
                session, api["url"], api["headers"]
            )
            return items or []

    def run(self, keyword: str, sort: str = "date") -> list[dict]:
        return asyncio.run(self.search(keyword, sort))


if __name__ == "__main__":
    scraper = NaverShoppingScraper()
    results = scraper.run("갤럭시북", "date")
    for item in results[:3]:
        print(item)
