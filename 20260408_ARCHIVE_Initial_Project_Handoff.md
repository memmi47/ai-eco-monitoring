# AI Eco Monitor - Handoff Document

## 1. 프로젝트 구조

```
ai-eco-monitor/
  database/
    schema.sql              # PostgreSQL DDL (companies, crawl_history, analysis_results, activity_index)
    seed_db.py              # AI_Factory_Ecosystem_Database_v2.csv -> PostgreSQL
  backend/
    main.py                 # FastAPI + 3단계 LLM 파이프라인 (6 endpoints)
    requirements.txt
    .env.example
  frontend/
    src/app/                # Next.js App Router
    src/components/         # NewsFeed, ActivityChart, TaxonomyPanel
    package.json
    next.config.js          # /api/* -> backend:8000 proxy
  AI_Factory_Ecosystem_Database_v2.csv   # 원본 CSV (590 companies, 루트에 배치)
  README_Handoff.md
```

## 2. 데이터 구조

### 원본 CSV 컬럼 -> DB 매핑

| CSV 헤더 | DB 컬럼 | 비고 |
|----------|---------|------|
| No. | seq_no | 원본 순번 |
| Layer (대분류) | layer | A~G (Physical Infra ~ Application) |
| Category (중분류) | category | 약 30개 분류 |
| Sub-category (소분류) | sub_category | |
| 회사명 | company_name | |
| 구분 | biz_type | GPU, LLM, Foundry 등 세부 유형 |
| 상장여부 | listing_status | 상장/비상장/인수/오픈소스 등 |
| HQ지역 | hq_region | |
| Company Mission | company_mission | |
| 한줄 설명 (비고) | description | |
| 중요도 | importance + tier | High->T1, Medium->T2, Low->T3 |

### 추가 참조 자료
- `compass_artifact_...md`: 463개 DB 대비 12개 누락 섹터, 350+ 추가 기업 식별 문서
- 후속 Phase에서 이 기업들을 companies 테이블에 추가 적재 가능

## 3. 로컬 테스트 순서

### 3-1. DB 준비

```bash
createdb ai_eco_monitor
cd database
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/ai_eco_monitor"
python seed_db.py
# -> [OK] 590건 적재 완료, Tier 1: 97건, Tier 2: 149건, Tier 3: 73건 (+ 기타)
```

### 3-2. Backend

```bash
cd backend
cp .env.example .env
# .env에 OPENROUTER_API_KEY 입력
pip install -r requirements.txt
python main.py
# -> http://localhost:8000/docs (Swagger UI)
```

### 3-3. Frontend

```bash
cd frontend
npm install
npm run dev
# -> http://localhost:3000
```

## 4. 핵심 로직

### 4-1. 3단계 LLM 파이프라인 (POST /api/analyze)

Stage 1 -> Gemma 2 9B (free): 메모리 반도체 관련성 yes/no 필터
Stage 2 -> Gemma 2 9B (free): event_type + memory_signal 태깅
Stage 3 -> Gemini Flash 1.5 (paid): impact_score(1-10), 시사점, 시간축 분석

- Stage 1 "no" 시 2,3단계 스킵 -> 비용 최적화
- model 변경: main.py 상단 MODEL_FREE / MODEL_PAID 변수만 수정
- LiteLLM이 OpenRouter API 호출 통합 처리

### 4-2. API 엔드포인트

- GET /api/companies - 기업 목록 (tier/layer/category/importance/q 필터)
- GET /api/companies/{id} - 기업 상세
- GET /api/stats - 대시보드 요약 통계
- GET /api/feed - 메모리 임팩트 뉴스 피드
- GET /api/activity - 업체 활동 지수
- GET /api/taxonomy - Layer/Category 분류 체계
- POST /api/analyze - 뉴스 1건 분석 실행

## 5. 후속 작업 (Antigravity TODO)

1. CSV 파일을 프로젝트 루트에 배치 후 seed_db.py 실행, 적재 건수 확인
2. 뉴스 크롤러 구현: 현재 /api/analyze는 수동 입력만 지원. APScheduler 또는 Celery로 자동 수집 추가
3. activity_index 갱신: 일별 배치로 analysis_results 집계 SQL 작성
4. compass 문서의 350+ 추가 기업 적재 (별도 seed 스크립트 또는 CSV 병합)
5. 인증: 내부 사용 시 API key 미들웨어 추가
6. 배포: Docker Compose (postgres + backend + frontend) 구성
