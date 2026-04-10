# AI Eco Monitor v2

AI Eco Monitor는 600개+ AI 에코시스템 기업을 모니터링하여 **메모리 반도체(HBM, Conventional DRAM, NAND) 수요 방향성**을 예측하는 인텔리전스 플랫폼입니다.

## 주요 기능

- **46개 측정변수 기반 시그널 분석**: Tier 1(인프라) × Tier 2(모델/기술) × Tier 3(서비스 실현) 3단계 수요 공식
- **3단계 LLM 파이프라인 (Pipeline v2)**:
  - **Stage 1 (Gemma 2 9B / Free)**: 사실 추출 + 기업/카테고리 매핑
  - **Stage 2 (Gemma 2 9B / Free)**: 카테고리별 측정변수 매핑 + Bullish/Bearish 방향 판정 (caveat 포함)
  - **Stage 3 (Gemini Flash 1.5 / Paid)**: 메모리 전이 경로 분석 + 경영진 요약 (한국어)
- **5개 Memory Demand Driver (MD1-MD5)**: 가중 평균 집계로 경영진 30초 소비 뷰 제공
- **Divergence Alert**: MD 간 괴리 감지 5종 (DA1-DA5) 자동 알림
- **Expected Event Calendar**: 실적 발표·제품 출시·컨퍼런스 주차별 그룹화
- **Decision Relevance 필터**: 당분기·차분기·투자계획 (기본) / 전략참조 (별도 뷰)

## 기술 스택

- **Frontend**: Next.js 14 (App Router), Tailwind CSS, TypeScript
- **Backend**: FastAPI (Python 3.9+), LiteLLM (OpenRouter API)
- **Database**: SQLite (개발) / PostgreSQL (운영, Railway)
- **Deployment**: Railway (Backend), Vercel (Frontend)

## 시작하기

### 1. 환경 변수 설정

```bash
cp backend/.env.example backend/.env
# .env에 OPENROUTER_API_KEY 입력
# 운영 환경: DATABASE_URL=postgresql://... 설정
```

### 2. 데이터베이스 초기화

```bash
cd backend
pip install -r requirements.txt
python database/seed_db.py   # 590개 기업 CSV 적재
```

### 3. 서버 구동

```bash
# Backend
python main.py               # http://localhost:8000/docs

# Frontend (별도 터미널)
cd frontend
npm install
npm run dev                  # http://localhost:3000
```

## API 엔드포인트

| Method | 경로 | 설명 |
|--------|------|------|
| POST | `/api/analyze/v2` | Pipeline v2 분석 실행 |
| GET | `/api/signals` | 시그널 피드 (direction/tier/decision_relevance 필터) |
| GET | `/api/drivers` | 5개 MD 가중 집계 점수 |
| GET | `/api/divergence-alerts` | 활성 Divergence Alert (DA1-DA5) |
| GET | `/api/expected-events` | 예정 이벤트 캘린더 |
| POST | `/api/expected-events` | 이벤트 수동 등록 |
| GET | `/api/companies` | 기업 목록 (tier/layer/q 필터) |
| GET | `/api/stats` | 대시보드 요약 통계 |

## 연락처

Created by [memmi47](https://github.com/memmi47)
