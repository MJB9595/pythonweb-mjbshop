# 김재아의 웹 스크래핑 프로젝트 — 쇼핑 검색

네이버 쇼핑 Open API를 활용한 상품 검색 웹 애플리케이션입니다.  
FastAPI 기반의 비동기 백엔드와 MongoDB Atlas를 연동하여 검색 결과를 저장하고, 정렬·즐겨찾기 기능을 제공합니다.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 상품 검색 | 키워드로 네이버 쇼핑 상품 최대 100건 조회 |
| 정렬 | 최신순 / 가격 낮은순 / 가격 높은순 / 정확도순 |
| 즐겨찾기 | 카드별 ♡ 버튼으로 즐겨찾기 추가·제거, 브라우저 로컬 저장 |
| 상품 링크 | 카드 클릭 시 해당 상품 페이지로 이동 (새 탭) |
| 데이터 저장 | 검색 결과를 MongoDB Atlas에 자동 저장 |

---

## 기술 스택

- **Backend** — Python 3.12, FastAPI, Uvicorn
- **Scraping** — 네이버 검색 Open API, aiohttp (비동기 HTTP)
- **Database** — MongoDB Atlas, Motor (비동기 드라이버), ODMantic (ORM)
- **Frontend** — Jinja2 템플릿, Vanilla JS, mvp.css

---

## 프로젝트 구조

```
mjbbooks/
├── app/
│   ├── main.py               # FastAPI 라우터 (/, /search, /api/shop)
│   ├── shopping_scraper.py   # 네이버 쇼핑 API 스크래퍼
│   ├── book_scraper.py       # 네이버 책 API 스크래퍼 (기존)
│   ├── config.py             # 환경 변수 / secrets.json 로더
│   ├── models/
│   │   ├── __init__.py       # MongoDB 연결 (Motor + ODMantic)
│   │   ├── shopping.py       # 쇼핑 상품 데이터 모델
│   │   └── book.py           # 책 데이터 모델 (기존)
│   └── templates/
│       ├── index.html        # 쇼핑 검색 메인 페이지
│       └── shop.html         # (구) 쇼핑 전용 페이지
├── api/
│   └── index.py              # Vercel 배포용 진입점
├── server.py                 # Uvicorn 서버 실행 스크립트
├── vercel.json               # Vercel 배포 설정
├── requirements.txt          # 의존성 목록
└── secrets.json              # API 키 / DB URI (로컬 전용, git 제외)
```

---

## 로컬 실행

### 1. 의존성 설치

```bash
cd mjbbooks
python -m venv venv312
source venv312/bin/activate       # Windows: venv312\Scripts\activate
pip install -r requirements.txt
```

### 2. 환경 변수 설정

프로젝트 루트에 `secrets.json` 파일을 생성합니다.

```json
{
  "NAVER_API_ID": "발급받은_클라이언트_ID",
  "NAVER_API_SECRET": "발급받은_클라이언트_시크릿",
  "MONGODB_URI": "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/",
  "MONGODB_DB_NAME": "사용할_DB명"
}
```

> 네이버 Open API 키는 [네이버 개발자 센터](https://developers.naver.com/)에서 발급합니다.  
> MongoDB Atlas 무료 클러스터는 [mongodb.com/atlas](https://www.mongodb.com/atlas) 에서 생성합니다.

### 3. 서버 실행

```bash
python server.py
```

브라우저에서 `http://localhost:8000` 접속

---

## 배포

### Vercel (권장 — 빠른 공유)

```bash
npm i -g vercel
vercel
```

Vercel 대시보드 → **Settings → Environment Variables** 에 아래 4개 등록:

| 키 | 설명 |
|----|------|
| `NAVER_API_ID` | 네이버 API 클라이언트 ID |
| `NAVER_API_SECRET` | 네이버 API 클라이언트 시크릿 |
| `MONGODB_URI` | MongoDB Atlas 연결 URI |
| `MONGODB_DB_NAME` | 사용할 DB 이름 |

> `secrets.json`은 로컬 전용입니다. Vercel에서는 환경 변수를 자동으로 사용합니다.

### 홈서버 (장기 운영)

```bash
# 백그라운드 실행
nohup python server.py > server.log 2>&1 &

# 또는 systemd 서비스 등록 후 부팅 시 자동 시작
```

외부 접속이 필요한 경우 라우터에서 **8000번 포트 포워딩**을 설정합니다.

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/` | 쇼핑 검색 메인 페이지 |
| `GET` | `/search?q=검색어&sort=date` | 검색 결과 페이지 (HTML) |
| `GET` | `/api/shop?q=검색어&sort=asc` | 검색 결과 JSON (AJAX용) |

**sort 파라미터:**

| 값 | 정렬 기준 |
|----|-----------|
| `date` | 최신순 (기본값) |
| `asc` | 가격 낮은순 |
| `dsc` | 가격 높은순 |
| `sim` | 정확도순 |

---

## 주의 사항

- `secrets.json`은 반드시 `.gitignore`에 추가하여 Git에 올라가지 않도록 합니다.
- 네이버 검색 API 무료 플랜은 하루 **25,000건** 호출 제한이 있습니다.
- Vercel 서버리스 함수는 **실행 시간 10초** 제한이 있습니다 (대량 검색 시 주의).
