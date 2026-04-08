# AI Eco Monitor 🚀

AI Eco Monitor는 AI 반도체 생태계를 모니터링하고, 특히 **메모리 반도체(HBM, DDR5 등)**에 미치는 영향을 3단계 LLM 파이프라인을 통해 정밀 분석하는 대시보드 시스템입니다.

## 🌟 주요 기능

- **생태계 대시보드**: 600여 개 글로벌 AI 관련 기업의 계층별(Infrastructure ~ App) 분류 및 중요도 관리.
- **3단계 LLM 분석 파이프라인**:
  - **Stage 1 (Gemma 2 9B)**: 메모리 반도체 관련성 필터링 (비용 최적화).
  - **Stage 2 (Gemma 2 9B)**: 이벤트 유형 및 메모리 시그널(수요 상향/하향 등) 태깅.
  - **Stage 3 (Gemini 1.5 Flash)**: 임팩트 스코어 산출 및 타임라인 분석.
- **활동 지수(Activity Index)**: 개별 기업의 활동이 메모리 시장에 미치는 파급력을 지수화하여 시각화.

## 🏗️ 기술 스택

- **Frontend**: Next.js 14 (App Router), Tailwind CSS, TypeScript
- **Backend**: FastAPI (Python 3.9+), LiteLLM (OpenRouter API 통합)
- **Database**: SQLite (개발/배포 편의성을 위해 SQLAlchemy/SQLite 전환 완료)
- **Deployment**: Railway (Backend/DB), Vercel (Frontend)

## 🚀 시작하기

### 1. 환경 변수 설정
`backend/.env` 파일을 만들고 아래 내용을 입력하세요 (보안을 위해 직접 입력 권장):
```env
OPENROUTER_API_KEY=your_key_here
DATABASE_URL=sqlite:///../database/ai_eco_monitor.db
```

### 2. 데이터베이스 초기화
```bash
cd database
python seed_db.py
```

### 3. 서버 구동
- **Backend (FastAPI)**:
  ```bash
  cd backend
  pip install -r requirements.txt
  python main.py
  ```
- **Frontend (Next.js)**:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```

## 📬 Contact
Created by [memmi47](https://github.com/memmi47)
