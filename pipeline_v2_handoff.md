# AI Eco Monitor - Pipeline v2 재설계 핸드오프

## 1. 변경 개요

### 현재 MVP (Pipeline v1)

```
뉴스 입력 → Stage 1 (관련성 yes/no) → Stage 2 (event_type 분류) → Stage 3 (impact_score 1-10)
```

문제: impact_score가 블랙박스. 경영진이 "왜 이 점수인가"를 추적할 수 없음.

### 개편 (Pipeline v2)

```
뉴스 입력
  → Stage 1: 사실 추출 + 기업/카테고리 매핑 (Free model)
  → Stage 2: 측정변수 매핑 + 시그널 방향/강도 판정 (Free model)
  → Stage 3: 메모리 전이 경로 분석 + 수요 시사점 도출 (Paid model)
```

핵심 변경: "이 뉴스가 중요한가?"에서 "이 뉴스가 어떤 수요 변수를 어떤 방향으로 움직이는가?"로 전환.

---

## 2. DB 스키마 변경

### analysis_results 테이블 v2

기존 컬럼은 유지하되 신규 컬럼 추가. 기존 데이터 호환성 보장.

```sql
-- 기존 테이블에 ALTER로 추가 (기존 MVP 데이터 보존)
ALTER TABLE analysis_results
  ADD COLUMN IF NOT EXISTS stage1_facts JSONB,
  ADD COLUMN IF NOT EXISTS stage2_variable_id TEXT,
  ADD COLUMN IF NOT EXISTS stage2_variable_name TEXT,
  ADD COLUMN IF NOT EXISTS stage2_direction TEXT,          -- bullish, bearish, structural
  ADD COLUMN IF NOT EXISTS stage2_strength TEXT,           -- strong, moderate, weak
  ADD COLUMN IF NOT EXISTS stage2_confidence TEXT,         -- high, medium, low
  ADD COLUMN IF NOT EXISTS stage2_affected_memory TEXT[],  -- {'HBM','DRAM','NAND','LPDDR'}
  ADD COLUMN IF NOT EXISTS stage3_transmission_path TEXT,
  ADD COLUMN IF NOT EXISTS stage3_demand_formula_tier TEXT, -- tier1, tier2, tier3
  ADD COLUMN IF NOT EXISTS stage3_lag TEXT,                 -- immediate, short, mid, long
  ADD COLUMN IF NOT EXISTS pipeline_version SMALLINT DEFAULT 1;

CREATE INDEX IF NOT EXISTS idx_analysis_variable ON analysis_results(stage2_variable_id);
CREATE INDEX IF NOT EXISTS idx_analysis_direction ON analysis_results(stage2_direction);
CREATE INDEX IF NOT EXISTS idx_analysis_tier ON analysis_results(stage3_demand_formula_tier);
```

### stage1_facts JSONB 구조

```json
{
  "who": "Microsoft",
  "what": "FY26 capex guidance 상향",
  "how": "$80B → $95B (+19%)",
  "when": "2026 Q1 실적발표",
  "source_type": "earnings",
  "is_quantitative": true
}
```

---

## 3. Stage 1 프롬프트 (사실 추출 + 매핑)

### 모델: MODEL_FREE (Gemma 2 9B / 무료)

### System Prompt

```
You are a structured fact extractor for the AI and semiconductor industry.

Your task:
1. Extract structured facts from the news article
2. Determine if this news has ANY relevance to AI infrastructure, AI models, AI applications, or the semiconductor supply chain
3. Identify which company and industry category this relates to

IMPORTANT: Be inclusive at this stage. Even indirect relevance (e.g., an AI app growing rapidly = inference demand signal) should pass through. Only filter out completely unrelated news (sports, entertainment, politics unrelated to tech).

Respond in JSON only. No markdown, no explanation.

{
  "relevant": true/false,
  "facts": {
    "who": "company or entity name",
    "what": "action or event (be specific)",
    "how": "quantitative detail if available (numbers, percentages, dollar amounts)",
    "when": "date or time context",
    "source_type": "earnings|press_release|news|blog|sec_filing|research|rumor"
  },
  "company_match": {
    "company_name": "matched company from our database, or null",
    "category": "best matching Category from: A1.Energy&Power, A2.Thermal, A3.DC_EPC, B1.SemiEquip, B2.Compute, B3.Memory, B4.Network, B5.Server, B6.Packaging, C1.DC_Operator, C2.Hyperscaler, D1.DataInfra, D2.VectorDB, D3.DataLabeling, D4.LLM_Middleware, E1.FoundationModel, E2.VideoCreative, E3.VoiceAudio, F1.CodingAI, F2.AgentInfra, G1.EnterpriseAI, G2.ConversationalAI, G3.Productivity, G4.AISearch, G5.IndustrialAI, H1.Healthcare, H2.Legal, H3.Finance, H4.Defense, H5.SupplyChain, H6.Marketing, H7.HR, H8.Climate, H9.Education, H10.AV, H11.AgriGeo, I1.AISecurity, I2.Governance, I3.Observability, I4.EdgeAI, J1.Robotics",
    "tier": "tier1|tier2|tier3"
  },
  "is_quantitative": true/false
}
```

### User Prompt Template

```
Company context: {company_name} | Category: {category} | Tier: {tier}

Article:
Title: {title}
Content: {snippet}
```

### 판정 로직 (코드 레벨)

```python
s1 = json.loads(stage1_response)
if not s1["relevant"]:
    return {"stage1_relevant": False, "skipped": True}
# Stage 2로 전달: s1["facts"], s1["company_match"], s1["is_quantitative"]
```

---

## 4. Stage 2 프롬프트 (측정변수 매핑 + 시그널 판정)

### 모델: MODEL_FREE (Gemma 2 9B / 무료)

### System Prompt

Stage 2의 시스템 프롬프트는 카테고리별로 **다른 측정변수 목록**을 주입한다. 이것이 핵심 설계 변경.

```
You are a memory semiconductor demand signal analyst.

Given the extracted facts from a news article, your task is:
1. Map this event to the most relevant measurement variable for this category
2. Determine the signal direction, strength, and confidence
3. Identify which memory products are affected

CATEGORY: {category}
TIER: {tier}

MEASUREMENT VARIABLES FOR THIS CATEGORY:
{variable_definitions}

SIGNAL RULES:
- Direction: "bullish" (memory demand increases), "bearish" (demand decreases), "structural" (demand pattern changes, direction ambiguous)
- Strength: "strong" (official disclosure, quantitative data), "moderate" (credible report, qualitative), "weak" (rumor, speculation)
- Confidence: "high" (company filing, official announcement), "medium" (credible media), "low" (industry rumor, estimation)
- Affected memory: one or more of ["HBM", "DRAM", "NAND", "LPDDR"]

Respond in JSON only. No markdown, no explanation.

{
  "variable_id": "the variable ID from the list above",
  "variable_name": "human-readable variable name",
  "direction": "bullish|bearish|structural",
  "strength": "strong|moderate|weak",
  "confidence": "high|medium|low",
  "affected_memory": ["HBM", "DRAM"],
  "reasoning": "one sentence: why this direction and strength"
}
```

### 카테고리별 변수 정의 주입 (variable_definitions)

아래는 각 카테고리에 주입할 변수 목록. 코드에서 category를 키로 딕셔너리 조회하여 프롬프트에 삽입한다.

```python
VARIABLE_DEFINITIONS = {

    # ===== TIER 1: 인프라 투자 규모 기반 수요 추정 =====

    "A1": """
V01: AI DC 전용 전력 프로젝트 규모 (MW)
  - Bullish: SMR/PPA 체결, 발전소 착공/가동 승인, 전력 구매 규모 확대
  - Bearish: 전력 프로젝트 취소/지연
  - Affected: 복합 (전 메모리 제품)

V02: 전력 인프라 투자 금액
  - Bullish: ESS/배터리/재생에너지 대규모 투자, 전력 관련 M&A
  - Affected: 복합

V03: 전력 공급 병목 시그널
  - Bearish: 전력망 연결 대기 증가, DC 프로젝트 전력 미확보 지연
  - Structural: 정부 전력 배분 정책 변화 (DC 우선=bullish, DC 제한=bearish)
  - Affected: 복합
""",

    "A2": """
V04: 액냉(Liquid Cooling) 수주/출하 추이
  - Bullish: 액냉 장비 수주 증가, 신규 액냉 기술 표준화, 액냉 공급 부족(수요 초과 확인)
  - Affected: HBM

V05: Rack 전력밀도 변화 (kW/Rack)
  - Bullish: 고밀도 랙 표준 변경 (100kW+), GPU 서버 TDP 세대별 증가
  - Affected: HBM, DRAM
""",

    "A3": """
V06: 신규 DC 착공/설계 건수 및 규모
  - Bullish: DC 착공 발표 (100MW+ = strong), DC 설계 수주
  - Bearish: DC 프로젝트 취소/보류
  - Affected: 복합

V07: DC 건설 비용 변화
  - Bearish: 건설 단가 상승 (+30%+ = strong), 자재/인력 부족
  - Affected: 복합
""",

    "B1": """
V08: HBM/첨단 패키징 관련 장비 수주
  - Bullish: HBM TSV/본딩 장비 수주 증가, HBM 테스터 출하 증가
  - Bearish: 메모리 장비 발주 감소/이연
  - Affected: HBM

V09: EUV/첨단 공정 장비 출하
  - Bullish: ASML EUV/High-NA 출하 실적, 로직 파운드리 첨단 공정 가동
  - Affected: HBM (간접, 로직칩 → GPU → HBM)

V10: EDA/IP 라이선스 트렌드
  - Bullish: AI 칩 설계 관련 EDA 매출 증가, 신규 AI ASIC 설계 발표
  - Affected: 복합 (장기)
""",

    "B2": """
V11: GPU/AI 가속기 신제품 스펙 변화
  - Bullish: 차세대 GPU HBM 세대/용량 변화, 양산 앞당김, 출하량 가이던스 상향
  - Bearish: 양산 지연, 출하 가이던스 하향
  - Affected: HBM

V12: Custom ASIC 설계 프로젝트 수
  - Bullish: ASIC 고객 수 증가, 자체칩 프로젝트 양산 확정
  - Structural: ASIC이 GPU 대체 시 메모리 인터페이스 다변화
  - Affected: HBM, DRAM, LPDDR

V13: Edge/NPU 칩 출시 및 스펙
  - Bullish: 모바일 AP NPU TOPS 증가, 기기당 LPDDR/UFS 탑재량 증가, Edge AI 전용칩 양산
  - Affected: LPDDR, NAND

V14: 신규 아키텍처 동향
  - Structural: CXL 상용 제품 (메모리 풀링 → DRAM 총량 변화), PIM/CIM 양산 (대체 vs 신규 카테고리)
  - Bullish: 광 인터커넥트 양산 (클러스터 확대 → HBM)
  - Affected: DRAM, HBM
""",

    "B3": """
V15: HBM 공급 동향 및 경쟁 구도
  - Structural: 경쟁사 HBM 증설 (공급↑ = 가격 하방, 시장 성장 확인), HBM 세대 전환 일정
  - Bullish (자사 관점): 경쟁사 수율 이슈, 기술 지연
  - Affected: HBM

V16: CXL/메모리 패브릭 채택
  - Structural: CXL 메모리 모듈 상용 배치, 메모리 디사그리게이션 도입
  - Affected: DRAM

V17: 스토리지 아키텍처 변화
  - Bullish: KV Cache용 eSSD 채택, AI 전용 스토리지 매출 증가, 체크포인팅 수요
  - Affected: NAND
""",

    "B4": """
V18: AI 네트워크 대역폭 세대 전환
  - Bullish: 차세대 InfiniBand/Ethernet 출시, AI 클러스터 네트워크 규모 확대
  - Affected: HBM (간접: 네트워크 → 클러스터 확대 → HBM)

V19: 광 인터커넥트 상용화 진행
  - Bullish: 광 모듈 출하 급증, 광 I/O 칩 서버 탑재 확정
  - Affected: HBM (간접)
""",

    "B5": """
V20: AI 서버 출하량/수주 전망
  - Bullish: AI 서버 수주잔고 증가, 매출/출하 실적 증가, ODM 가이던스 상향
  - Bearish: 수주잔고 감소, 가이던스 하향
  - Affected: HBM, DRAM (가장 직접적 선행 지표)

V21: 서버 아키텍처 구성 변화
  - Bullish: 서버당 GPU/HBM 탑재량 증가, 서버당 DRAM 용량 증가, 랙 스케일 아키텍처 확산
  - Affected: HBM, DRAM
""",

    "B6": """
V22: 첨단 패키징 Capa 증설
  - Bullish: CoWoS/FOPLP Capa 증설, 패키징 병목 보도(수요 초과 확인), OSAT AI 매출 비중 증가
  - Affected: HBM (패키징 Capa = HBM 병목)

V23: ABF/기판 수급 동향
  - Bullish: ABF 증산 투자, 기판 수급 타이트(수요 초과)
  - Affected: HBM (간접)
""",

    "C1": """
V24: DC 가용 용량 확장률
  - Bullish: Colo 신규 용량 확장 (100MW+ = strong), AI 전용 DC존 신설
  - Affected: 복합

V25: 입주율/가동률 변화
  - Bullish: 입주율 90%+, 대기 리스트 증가
  - Bearish: 입주율 하락
  - Affected: 복합
""",

    "C2": """
V26: Hyperscaler Capex 규모 및 가이던스 변화
  - Bullish: 연간/분기 Capex 가이던스 상향, AI 인프라 비중 증가, 실적 콜 AI 투자 가속 발언
  - Bearish: Capex 가이던스 하향/동결, 신중 발언
  - Affected: HBM, DRAM, NAND (가장 강력한 단일 선행 변수)

V27: Neocloud/GPU Cloud 자금 조달 및 확장
  - Bullish: 대규모 자금 조달 ($1B+ = strong), GPU 클러스터 확장, 높은 가동률
  - Bearish: 가동률 하락, 자금 조달 실패
  - Affected: HBM, DRAM

V28: 추론 서비스 인프라 투자
  - Bullish: 추론 전용 인프라 구축, 추론 칩 대량 배치
  - Structural: 추론 비용 인하 (효율화 vs Jevons Paradox)
  - Affected: DRAM, NAND
""",

    # ===== TIER 2: 모델/기술 트렌드 기반 단위당 메모리 계수 변화 =====

    "D1": """
V29: 데이터 파이프라인 처리량 증가율
  - Bullish: 데이터 플랫폼 매출/처리량 급증, 대규모 데이터 인프라 계약
  - Affected: DRAM

V30: ML 모델 배포 빈도
  - Bullish: 모델 허브 다운로드 급증 (월 10B+ = strong), 엔터프라이즈 모델 서빙 확대
  - Affected: DRAM
""",

    "D2": """
V31: Vector DB 도입 기업 수 및 데이터 규모
  - Bullish: Vector DB 매출/고객 성장 (+100%+ = strong), 임베딩 인덱스 규모 성장 (1B+ 벡터 = strong)
  - Affected: DRAM (임베딩 캐싱)
""",

    "D3": """
V32: 학습 데이터 생산량 및 투자 규모
  - Bullish: 데이터 라벨링 매출 증가, 합성 데이터 주요 LLM 기업 채택
  - Affected: HBM (간접: 데이터 → 학습 규모 → GPU/HBM)
""",

    "D4": """
V33: RAG/Agent 프레임워크 채택률
  - Bullish: RAG 프레임워크 다운로드 급증, 엔터프라이즈 RAG 도입 사례
  - Affected: DRAM, NAND (RAG → 컨텍스트 확대 → KV Cache 증가)
""",

    "E1": """
V34: 모델 파라미터/컨텍스트 윈도우 스케일링
  - Bullish: 차세대 모델 파라미터 규모 증가 (5x+ = strong), 컨텍스트 윈도우 확장 (1M+ 토큰 = strong)
  - Structural: 모델 효율화/경량화 (단위 수요 ↓ but 접근성 ↑ → Jevons Paradox로 총 수요 ▲ 가능)
  - Affected: HBM, DRAM, NAND

V35: 학습 클러스터 규모 발표
  - Bullish: GPU 클러스터 규모 공개 (100K+ GPU = strong), 학습 비용 $100M+ 공개
  - Affected: HBM (직접 정량화 가능: GPU수 × HBM/GPU)

V36: 오픈소스 모델 릴리스 빈도
  - Bullish: 주요 오픈소스 모델 출시 (70B+ = strong), 소버린 AI 국가 프로젝트 ($1B+ = strong)
  - Affected: HBM (학습 복제 수요 분산)

V37: 학습-추론 Compute 비율 변화
  - Structural: 추론 비중 ↑ → HBM 대비 서버 DRAM 수요 비중 변화
  - Bullish: Test-time compute 확대 → 추론 시 메모리 수요 증가
  - Affected: DRAM (비중 변화), NAND (KV Cache)
""",

    "E2": """
V38: 비디오/이미지 생성 서비스 사용량
  - Bullish: 생성형 AI MAU/생성 건수 (100M+ = strong), 비디오 생성 상용화
  - Affected: DRAM, HBM (비디오 = 텍스트 대비 10x+ compute)

V39: 멀티모달 모델 스펙 변화
  - Bullish: 해상도/길이 증가 (4K = strong), 실시간 멀티모달 처리
  - Affected: HBM, DRAM
""",

    "E3": """
V40: 음성 AI API 호출량/매출 성장률
  - Bullish: 음성 AI ARR $100M+ 또는 YoY +200%+, TTS/STT API 호출 월 1B+
  - Affected: DRAM (실시간 추론 → 고대역 DRAM)

V41: Voice Agent 상용 배치 건수
  - Bullish: 대규모 배치 계약 (100+ 엔터프라이즈 = strong), 대규모 자금 조달
  - Affected: DRAM (항시 가동 추론 서버)
""",

    "F1": """
V42: AI 코딩 도구 사용자 수/ARR
  - Bullish: 코딩 AI DAU 1M+, ARR $500M+
  - Affected: DRAM (추론 API 호출)

V43: 코딩 AI 모델 전용 학습 투자
  - Bullish: 코드 특화 모델 자금 조달 $500M+, 학습 클러스터 10K+ GPU
  - Affected: HBM (전용 학습)
""",

    "F2": """
V44: Agent 플랫폼 기업 수/사용자 성장
  - Bullish: Agent 플랫폼 ARR $100M+, Agent 호출 체인 복잡도 증가 (10+ LLM 호출/태스크)
  - Affected: DRAM (다중 LLM 호출 → 추론 승수 효과)

V45: Agent 실행 환경 인프라 투자
  - Bullish: Agent 인프라 기업 자금 조달 $100M+, 샌드박스 사용량 월 1M+
  - Affected: DRAM (상시 가동 + 상태 관리)
""",

    # ===== TIER 3: 실제 활용 기반 수요 실현 검증 =====

    "G1": """
V46: 엔터프라이즈 AI 도입률/계약 규모
  - Bullish: 대형 AI 계약 ACV $100M+, Fortune500 도입률 50%+
  - Affected: DRAM
""",

    "G2": """
V47: 컨택센터 AI 전환율
  - Bullish: 글로벌 기업 전면 전환, 시장 규모 +30%+
  - Affected: DRAM
""",

    "G3": """
V48: AI Productivity 도구 MAU 성장률
  - Bullish: MAU 100M+
  - Affected: DRAM
""",

    "G4": """
V49: AI 검색 쿼리 볼륨
  - Bullish: AI 검색 MAU 100M+, 기존 검색 대비 AI 비중 30%+
  - Affected: DRAM (검색당 추론 compute 10x)
""",

    "G5": """
V50: 제조/산업 AI 도입 규모
  - Bullish: 글로벌 제조사 전면 도입
  - Affected: DRAM, NAND

V51: Digital Twin 활용 확대
  - Bullish: Digital Twin 플랫폼 매출 +50%+
  - Affected: DRAM, HBM
""",

    "H1": """
V52: AI 신약개발 파이프라인 수
  - Bullish: AI 신약 Phase 3+ 다수 진입, Bio AI 대규모 컴퓨트 투자
  - Affected: HBM (분자 시뮬레이션/단백질 접힘)

V53: 의료 AI FDA/CE 승인 건수
  - Bullish: 월 10건+ 승인
  - Affected: DRAM (Edge 추론)
""",

    "H2": "V54: 법률 AI 로펌 도입 확대. Bullish: Top100 로펌 50%+. Affected: DRAM",
    "H3": "V55: 금융 AI 거래량/처리량 변화. Bullish: 실시간 처리 10B+건. Affected: DRAM",
    "H4": "V56: 국방 AI 예산/계약 규모. Bullish: $1B+ 계약. Affected: DRAM, NAND",
    "H5": "V57: 공급망 AI 도입 기업 수. Bullish: Fortune500 30%+. Affected: DRAM",
    "H6": "V58: Marketing/Sales AI ARR. Bullish: +50%+. Affected: DRAM",
    "H7": "V59: HR AI 플랫폼 사용 규모. Bullish: 대기업 200+. Affected: DRAM",
    "H8": "V60: 기후 AI 규제 의무화. Bullish: 주요국 의무화. Affected: DRAM",
    "H9": "V61: 교육 AI 사용자 수. Bullish: 100M+. Affected: DRAM",

    "H10": """
V62: AV 학습 클러스터 규모
  - Bullish: AV 학습 인프라 10K+ GPU, PB급 비디오 학습 데이터
  - Affected: HBM, NAND

V63: 자율주행 차량 출하/배치 수
  - Bullish: Robotaxi/AV 트럭 10K대+, 차량당 LPDDR5X 32GB+
  - Affected: LPDDR, NAND
""",

    "H11": "V64: 위성/농업 AI 데이터 처리량. Bullish: +100%+. Affected: DRAM",

    "I1": """
V65: AI 보안 솔루션 매출/도입 확대
  - Bullish: +50%+ 매출 성장
  - Structural: AI 보안 사고 발생 → 단기 도입 지연 but 중기 보안 인프라 투자 증가
  - Affected: DRAM
""",
    "I2": """
V66: AI 규제 강화
  - Structural: On-prem 전환 (기업 전용 서버 수요 ▲) vs 도입 지연 (총 수요 ▼)
  - Affected: DRAM
""",
    "I3": "V67: AI 인프라 관리 도구 확산. Bullish: GPU 활용률 최적화 → 가동률 상승. Affected: DRAM",
    "I4": "V68: Edge AI 디바이스 출하. Bullish: 100만개+ 출하. Affected: LPDDR, NAND",

    "J1": """
V69: 로봇 출하량 전망
  - Bullish: 산업/서비스 로봇 출하 전년비 +30%+, 물류 로봇 10K대+ 배치
  - Affected: LPDDR, NAND

V70: 로봇 Foundation Model 학습 투자
  - Bullish: 로봇 파운데이션 모델 자금 조달 $500M+, 월드 모델 전용 클러스터
  - Affected: HBM (비디오+물리 시뮬레이션 = 매우 메모리 집약)

V71: 휴머노이드 상용화 타임라인
  - Bullish: 1,000대+ 양산 확정, 대규모 자금 조달 $1B+
  - Affected: LPDDR (대당 16-32GB)
"""
}
```

---

## 5. Stage 3 프롬프트 (메모리 전이 경로 분석)

### 모델: MODEL_PAID (Gemini Flash 1.5 / 유료 저가)

### System Prompt

```
You are a senior memory semiconductor demand strategist at a major memory company.

Your task: Given the structured facts and signal classification from previous stages, provide:
1. The specific transmission path from this event to memory semiconductor demand
2. The demand impact on each affected memory product
3. The time lag before demand impact materializes
4. A concise executive summary

CONTEXT:
- This project aims to forecast memory demand direction by monitoring 600+ AI ecosystem companies
- Memory demand = Tier1 (infra volume) × Tier2 (per-unit memory coefficient) × Tier3 (utilization/realization rate)
- Your analysis must trace HOW the event transmits to memory demand, not just WHETHER it does

TIER CONTEXT:
{tier_context}

Respond in JSON only. No markdown, no explanation.

{
  "transmission_path": "A → B → C chain showing how event reaches memory demand. Be specific. Example: 'MS capex +19% → GPU server orders increase → HBM demand +15-20% in 6-9 months'",
  "memory_impact": {
    "HBM": {"direction": "bullish|bearish|neutral", "magnitude": "high|medium|low|none", "detail": "specific impact"},
    "DRAM": {"direction": "...", "magnitude": "...", "detail": "..."},
    "NAND": {"direction": "...", "magnitude": "...", "detail": "..."},
    "LPDDR": {"direction": "...", "magnitude": "...", "detail": "..."}
  },
  "time_lag": "immediate|short_3-6m|mid_6-12m|long_12m+",
  "demand_formula_tier": "tier1|tier2|tier3",
  "demand_formula_role": "Explain which part of the demand formula this affects: volume (tier1), per-unit coefficient (tier2), or utilization rate (tier3)",
  "counterargument": "What could make this signal wrong or overstated? One sentence.",
  "executive_summary": "2-3 sentences for C-level. State the event, the memory demand impact, and the confidence level. In Korean."
}
```

### Tier Context 주입

```python
TIER_CONTEXTS = {
    "tier1": "This is a Tier 1 (Infrastructure) signal. It directly indicates physical compute capacity being built. Focus on quantifying how much memory this infrastructure will require. Key question: how many servers/GPUs does this translate to, and what memory configuration per unit?",

    "tier2": "This is a Tier 2 (Model/Technology) signal. It affects the per-unit memory coefficient. Focus on whether this changes how much memory each server/GPU/device needs. Key question: does this increase or decrease memory per unit? Consider efficiency trade-offs (quantization, compression, offloading vs. parameter growth, context window expansion).",

    "tier3": "This is a Tier 3 (Application/Demand) signal. It validates whether AI infrastructure investment is translating into actual usage. Focus on inference demand volume. Key question: is AI actually being used at scale? Which applications are driving real compute demand?"
}
```

---

## 6. 코드 변경 가이드 (Antigravity 작업 지시)

### 6-1. main.py 변경 사항

```python
# 1. 신규 import
from variable_definitions import VARIABLE_DEFINITIONS, TIER_CONTEXTS

# 2. Stage 2에서 company의 category를 기반으로 variable_definitions 주입
async def analyze_news(inp: AnalysisInput):
    # company의 category 조회
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT category, layer FROM companies WHERE id=%s", (inp.company_id,))
    company = cur.fetchone()
    conn.close()

    cat_key = company["category"].split(".")[0].strip()  # "A1" 추출
    tier = _get_tier(company["layer"])  # layer → tier 매핑

    # Stage 1: 사실 추출 (기존과 동일 구조, 프롬프트만 변경)
    s1 = await _llm(MODEL_FREE, STAGE1_SYSTEM_PROMPT,
        f"Company: {inp.company_name} | Category: {company['category']}\n\nTitle: {inp.title}\nContent: {inp.snippet}")

    # Stage 2: 변수 매핑 (카테고리별 다른 프롬프트)
    var_defs = VARIABLE_DEFINITIONS.get(cat_key, "No specific variables defined. Use general assessment.")
    s2_system = STAGE2_SYSTEM_PROMPT.format(
        category=company["category"],
        tier=tier,
        variable_definitions=var_defs
    )
    s2 = await _llm(MODEL_FREE, s2_system, json.dumps(s1_data["facts"]))

    # Stage 3: 전이 경로 분석 (tier context 주입)
    s3_system = STAGE3_SYSTEM_PROMPT.format(
        tier_context=TIER_CONTEXTS.get(tier, "")
    )
    s3_input = json.dumps({"facts": s1_data["facts"], "signal": s2_data})
    s3 = await _llm(MODEL_PAID, s3_system, s3_input)
```

### 6-2. 신규 파일: variable_definitions.py

위 Section 4의 VARIABLE_DEFINITIONS 딕셔너리와 TIER_CONTEXTS를 별도 파일로 분리.

### 6-3. Category → Tier 매핑 함수

```python
def _get_tier(layer: str) -> str:
    """Layer 대분류 → Tier 매핑"""
    prefix = layer.split(".")[0].strip()  # "A", "B", "C" 등
    if prefix in ("A", "B", "C"):
        return "tier1"
    elif prefix in ("D", "E", "F"):
        return "tier2"
    elif prefix in ("G", "H", "J"):
        return "tier3"
    elif prefix == "I":
        return "cross"  # 횡단
    return "tier3"  # fallback
```

### 6-4. DB INSERT 변경

```python
cur.execute("""
    INSERT INTO analysis_results (
        crawl_id, company_id, stage1_relevant, stage1_facts,
        stage2_event_type, stage2_memory_signal,
        stage2_variable_id, stage2_variable_name,
        stage2_direction, stage2_strength, stage2_confidence, stage2_affected_memory,
        stage3_summary, stage3_impact_score, stage3_memory_implication, stage3_time_horizon,
        stage3_transmission_path, stage3_demand_formula_tier, stage3_lag,
        model_used, pipeline_version
    ) VALUES (%s,%s,TRUE,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,2)
""", (...))
```

### 6-5. 기존 v1 데이터 호환

- pipeline_version 컬럼으로 v1/v2 데이터 구분
- 프론트엔드에서 v2 데이터가 있으면 신규 UI 표시, v1이면 기존 UI 유지
- v1 → v2 일괄 재분석은 별도 배치 스크립트로 처리 가능 (우선순위 낮음)

---

## 7. 프론트엔드 변경 요약

### 뉴스 피드 카드 v2

기존 impact_score 중심에서 시그널 카드로 변경:

```
┌─────────────────────────────────────────────┐
│ [T1] Microsoft | C2.Hyperscaler              │
│                                              │
│ FY26 capex guidance $80B → $95B (+19%)       │
│                                              │
│ Variable: V26 Hyperscaler Capex              │
│ ▲ Bullish | Strong | High Confidence         │
│ [HBM] [DRAM] [NAND]                         │
│                                              │
│ 전이경로: Capex +19% → GPU 서버 발주 증가     │
│  → HBM 수요 +15-20% (6-9개월)               │
│                                              │
│ 경영진 요약: MS가 FY26 AI 인프라 투자를       │
│ $95B로 상향. GPU 서버 발주 증가에 따른        │
│ HBM/DRAM/NAND 전 제품군 수요 상승 예상.      │
│ Confidence: High (공시 기반)                  │
│                                              │
│ 반론: AI 투자 ROI 미입증 시 차년도 감축 가능  │
│                                              │
│ 3-6M lag | 2026.04.15                        │
└─────────────────────────────────────────────┘
```

### 히트맵 (후속 작업)

signal_mapping_rules_v1.md의 부록 2 스펙 기반으로 구현. 이 핸드오프에서는 파이프라인 변경에 집중.

---

## 8. 테스트 시나리오

파이프라인 v2가 정상 작동하는지 아래 3건으로 검증:

### 테스트 1: Tier 1 Strong Bullish

```json
{
  "company_id": "[Microsoft ID]",
  "title": "Microsoft raises FY26 capex guidance to $95B",
  "snippet": "Microsoft announced during Q1 FY26 earnings that capital expenditure guidance has been raised from $80B to $95B, with the majority directed toward AI infrastructure including new data centers and GPU clusters."
}
```

기대 출력: V26, ▲ Bullish, Strong, High, [HBM, DRAM, NAND], 3-6M lag

### 테스트 2: Tier 2 Structural

```json
{
  "company_id": "[OpenAI ID]",
  "title": "OpenAI announces 4-bit quantization for GPT-5 inference",
  "snippet": "OpenAI released a new quantization technique reducing GPT-5 inference memory requirements by 75% while maintaining 98% accuracy. The technique is being deployed across all API endpoints."
}
```

기대 출력: V34 또는 V37, ◆ Structural, Strong, High, [HBM, DRAM], Jevons Paradox 언급 필수

### 테스트 3: Tier 3 Demand Validation

```json
{
  "company_id": "[Cursor/Anysphere ID]",
  "title": "Cursor reaches 5M daily active users, $2B ARR",
  "snippet": "Anysphere reports Cursor AI IDE has surpassed 5M daily active users and $2B in annual recurring revenue, making it one of the fastest-growing AI applications."
}
```

기대 출력: V42, ▲ Bullish, Strong, Medium, [DRAM], 추론 API 호출 → 서버 DRAM 수요
```
