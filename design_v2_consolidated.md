# AI Eco Monitor - 측정변수 & 시그널 설계서 v2 (통합 개정판)

## 프로젝트 목적

600+ AI 에코시스템 기업 모니터링을 통한 **메모리 반도체(HBM, Conventional DRAM, NAND) 수요 방향성 예측**

```
실제 메모리 수요 = Tier 1 (인프라 총량) × Tier 2 (단위당 메모리 계수) × Tier 3 (가동률/실현율)
```

---

## 개정 이력

| 버전 | 변경 사항 |
|------|----------|
| v1 | 59개 측정변수, 이벤트-시그널 매핑 규칙 초안 |
| v2 | Issue 1-3, 5-10 반영. 상위 Driver 집계 구조 신설, 변수 가중치 도입, Structural 판정 폐기, Tier 3 변수 통합, Event-driven/Periodic 분류, Jevons 프레임 교체, Decision Relevance 태그, Category Key 정규화, Expected Event Calendar 추가 |
| 향후 | Issue 4 (정량 추정) 반영 예정. HBM/DRAM/NAND별 수요 규모 추정 모델 개발 필요 |

---

## Part 1: 아키텍처 개요

### 1-1. 3-Layer 집계 구조 (Issue 1 반영)

```
Layer 3: Memory Demand Drivers (5개)     ← 경영진 소비 (30초)
  ↑ 가중 합산
Layer 2: 측정변수 (46개)                  ← 분석가 소비 (5분)
  ↑ 이벤트-시그널 변환
Layer 1: 개별 뉴스/이벤트                 ← 리서처 소비 (필요시)
```

### 1-2. Memory Demand Drivers (5개)

| Driver ID | Driver 명 | 핵심 질문 | 소속 변수 (Layer 2) | Tier |
|-----------|----------|----------|-------------------|------|
| MD1 | AI Infra 투자 강도 | DC/서버/GPU에 대한 물리적 투자가 얼마나 확대되고 있는가? | V01-V07, V20-V28 | Tier 1 |
| MD2 | 반도체 공급 역량 | 칩/패키징/장비 공급이 수요를 뒷받침할 수 있는가? 병목은 어디인가? | V08-V10, V11-V12, V15, V18-V19, V22-V23 | Tier 1 |
| MD3 | 모델/기술의 메모리 계수 변화 | 모델 스케일링과 효율화의 균형에서 단위당 메모리 소비가 어떻게 변하는가? | V14, V16-V17, V29-V37 | Tier 2 |
| MD4 | AI 서비스 추론 수요 실현 | AI 서비스가 실제로 대규모 추론 수요를 만들어내고 있는가? | V38-V45, V46-V51, V52-V53, VG_SaaS, VG_IndDef | Tier 2-3 |
| MD5 | Edge/디바이스 메모리 수요 | On-device AI, AV, 로보틱스가 Conv. DRAM(모바일)/NAND 수요를 얼마나 키우는가? | V13, V62-V63, V68-V71 | Tier 1-3 |

Driver 집계 공식:
```
Driver Score = Σ (변수별 시그널 방향 × 강도 × Confidence × Weight) / Σ Weight
```

### 1-3. 시그널 방향 체계 (Issue 3 반영)

**"Structural" 폐기.** 모든 시그널은 반드시 방향을 판정한다.

| 방향 | 정의 | 비고 |
|------|------|------|
| ▲ Bullish | 메모리 수요 증가 요인 | |
| ▲ Bullish (caveat) | 수요 증가 요인이나 반론 존재 | caveat 필드에 반론 기록 |
| ▼ Bearish | 메모리 수요 감소 요인 | |
| ▼ Bearish (caveat) | 수요 감소 요인이나 반론 존재 | caveat 필드에 반론 기록 |

기존 "Structural"로 분류되던 이벤트의 처리:
- CXL 확산 → ▲ Bullish (caveat): "메모리 풀링으로 서버당 총 DRAM 용량 증가 전망이나, 효율화에 의한 단위 수요 감소 가능성"
- 모델 효율화 → 효율화 속도 vs 채택 속도 비교로 방향 판정 (Issue 7 참조)
- AI 규제 강화 → ▼ Bearish (caveat): "단기 도입 지연이나, 중기 On-prem 전환으로 기업 전용 서버 수요 증가 가능"
- 방향 판정 불가 시: 분석가 수동 판정 큐에 적재 (Stage 2 출력에 `"needs_review": true` 플래그)

### 1-4. Jevons Paradox 대체 프레임 (Issue 7 반영)

효율화 관련 이벤트 판정 시, "Jevons Paradox로 총 수요 증가 가능"이라는 무조건적 코멘트를 폐기하고, 아래 비교 프레임을 적용:

```
효율화 이벤트 판정 = 효율화 속도 vs 채택 속도 비교

Case A: 채택 속도 > 효율화 속도 → ▲ Bullish
  예: 양자화로 메모리 75% 절감, but 사용자 10x 증가 → 순 수요 증가

Case B: 효율화 속도 > 채택 속도 → ▼ Bearish (caveat)
  예: 양자화로 메모리 75% 절감, 사용자 2x 증가 → 순 수요 감소
  caveat: "채택 가속 시 반전 가능"

Case C: 판단 불가 (초기 단계) → ▲ Bullish (caveat)
  기본값은 Bullish로 판정하되, caveat에 "효율화 영향 모니터링 필요" 기록
```

LLM Stage 3 프롬프트에서 이 프레임을 명시적으로 적용하도록 지시.

### 1-5. Decision Relevance 태그 (Issue 9 반영)

| 시간축 | Decision Relevance | 대시보드 표시 |
|--------|-------------------|-------------|
| 즉시 (0-3M) | Current Quarter | 기본 표시, 강조 |
| 단기 (3-6M) | Next Quarter | 기본 표시 |
| 중기 (6-12M) | Investment Plan | 기본 표시 |
| 장기 (12M+) | Strategic Reference | 별도 "전략 뷰"에서만 표시, 기본 필터에서 제외 |

### 1-6. 관측 유형 분류 (Issue 5 반영)

| 유형 | 정의 | 파이프라인 | 업데이트 주기 |
|------|------|----------|-------------|
| Event-driven | 뉴스/보도/공시에서 자동 관측 가능 | 자동 (LLM 파이프라인) | 일 1회+ |
| Periodic | 분기 실적, 제품 스펙, 산업 통계에서만 확인 가능 | 반자동 (실적 시즌 수동 트리거) | 분기/반기 |

---

## Part 2: 측정변수 정의 (46개, Issue 8 Tier 3 통합 반영)

### 변수 목록 컨벤션

각 변수에 아래 속성을 명시:
- **Weight**: Memory Impact Weight (1-10). 집계 시 가중치 (Issue 2)
- **관측 유형**: Event-driven / Periodic (Issue 5)
- **Decision Relevance**: Current/Next/Investment/Strategic (Issue 9)
- **소속 Driver**: MD1-MD5

---

### Tier 1: 인프라 투자 규모 기반 수요 추정 (A+B+C)

#### A1. Energy & Power

**V01: AI DC 전용 전력 프로젝트 규모** | Weight: 5 | Event-driven | Investment-Strategic | MD1

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| SMR/원자력 PPA 체결 | ▲ | Strong: 100MW+, Mod: 50-100MW, Weak: MOU | High: PPA 공시 | 복합 | 장기 |
| DC 전용 발전소 가동 승인 | ▲ | Strong: 가동 승인, Mod: 착공, Weak: 인허가 | High: 정부 발표 | 복합 | 장기 |
| 전력 프로젝트 취소/지연 | ▼ | Strong: 대형 취소, Mod: 일정 지연 | High: 공시 | 복합 | 장기 |

**V02: 전력 공급 병목 시그널** | Weight: 4 | Event-driven | Investment | MD1

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 전력망 연결 대기 증가 | ▼ Bearish (caveat) | Strong: 24M+ 대기, Mod: 12-24M | Medium: 보도 | 복합 | 중기 |
| DC 프로젝트 전력 미확보 지연 | ▼ | Strong: Hyperscaler 프로젝트 | High: 공시 | 복합 | 중기 |
| 정부 DC 전력 우선 배분 정책 | ▲ | Strong: 법안 통과, Mod: 행정명령 | High: 정부 | 복합 | 장기 |
| 정부 DC 전력 제한 정책 | ▼ | Strong: 법안 통과, Mod: 규제 검토 | High: 정부 | 복합 | 장기 |

> caveat (V02 전력 병목): "단기적으로 메모리 수요 이연이나, 병목 해소 시 지연된 수요 일시 반영 가능"

#### A2. Thermal Management

**V03: 액냉/고밀도 냉각 수주 추이** | Weight: 4 | Event-driven | Investment | MD1

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 액냉 장비 수주 증가 | ▲ | Strong: YoY +100%+, Mod: +30-100% | High: 실적 공시 | HBM | 중기 |
| 고밀도 랙 표준 변경 (100kW+) | ▲ | Strong: Hyperscaler 채택, Mod: OCP 스펙 | Medium: 기술 발표 | HBM, Conv. DRAM | 중기 |
| GPU 서버 TDP 세대별 증가 | ▲ | Strong: TDP 2x+ | High: 칩 발표 | HBM | 중기 |

#### A3. DC Design & EPC

**V04: 신규 DC 착공 규모** | Weight: 6 | Event-driven | Investment-Strategic | MD1

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| DC 착공/설계 수주 발표 | ▲ | Strong: 100MW+, Mod: 30-100MW | High: 공시 | 복합 | 장기 |
| DC 프로젝트 취소/보류 | ▼ | Strong: Hyperscaler, Mod: Neocloud | High: 공시 | 복합 | 중기 |
| DC 건설 단가 급등 | ▼ Bearish (caveat) | Strong: +30%+, Mod: +10-30% | Medium: 보도 | 복합 | 장기 |

> caveat (건설 단가): "비용 상승이 투자 축소로 이어질지, 비용 전가로 흡수될지 모니터링 필요"

---

#### B1. Semiconductor Equipment & EDA

**V08: HBM/첨단 패키징 장비 수주** | Weight: 8 | Event-driven + Periodic | Current-Next | MD2

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| HBM TSV/본딩 장비 수주 증가 | ▲ | Strong: +50%+, Mod: +20-50% | High: 실적 공시 | HBM | 중기 |
| HBM 테스터 출하 증가 | ▲ | Strong: 신세대 전용, Mod: 기존 세대 | High: 공시 | HBM | 단기 |
| 메모리 장비 발주 감소/이연 | ▼ | Strong: 대형 업체 감축, Mod: 일부 이연 | High: 공시 | HBM, Conv. DRAM | 단기 |

**V09: EUV/첨단 공정 장비 출하** | Weight: 5 | Periodic | Investment | MD2

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| ASML EUV/High-NA 출하 실적 | ▲ | Strong: 가이던스 초과, Mod: 부합 | High: 실적 | HBM (간접) | 장기 |
| 로직 파운드리 첨단 공정 양산 | ▲ | Strong: 3nm 이하, Mod: 가동 시작 | High: 발표 | HBM (간접) | 장기 |

**V10: EDA/IP 라이선스 트렌드** | Weight: 3 | Periodic | Strategic | MD2

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| AI 칩 EDA 매출 증가 | ▲ | Strong: +30%+, Mod: +15-30% | High: 실적 | 복합 | 장기 |
| 신규 AI ASIC 설계 발표 | ▲ | Strong: Hyperscaler 자체칩, Mod: Fabless | Medium: 보도 | 복합 | 장기 |

#### B2. Compute & Silicon

**V11: GPU/AI 가속기 스펙 및 출하** | Weight: 10 | Event-driven | Current-Next | MD2

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 차세대 GPU 발표 (HBM 세대/용량 변화) | ▲ | Strong: HBM 세대 전환, Mod: 동일 세대 용량 증가 | High: 공식 발표 | HBM | 중기 |
| GPU 양산 앞당김 | ▲ | Strong: 분기 이상, Mod: 수 주 | High: 공식 발표 | HBM | 단기 |
| GPU 양산 지연 | ▼ | Strong: 분기 이상, Mod: 수 주 | High: 공식 발표 | HBM | 단기 |
| GPU 출하량 가이던스 상향 | ▲ | Strong: +30%+, Mod: +15-30% | High: 실적 | HBM | 단기 |

**V12: Custom ASIC 프로젝트 동향** | Weight: 7 | Event-driven | Next-Investment | MD2

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| ASIC 고객 수 증가 | ▲ | Strong: 신규 Hyperscaler 고객, Mod: 기존 확장 | High: 실적 | HBM, Conv. DRAM | 장기 |
| 자체칩 양산 확정 | ▲ | Strong: 양산 확정, Mod: 테이프아웃 | High: 공식 발표 | HBM, Conv. DRAM | 장기 |
| ASIC의 GPU 대체 비율 변화 | ▲ Bullish (caveat) | 강도: ASIC 출하 규모 기준 | Medium: 분석 보고서 | HBM, Conv. DRAM | 장기 |

> caveat (ASIC 대체): "GPU 대비 ASIC은 메모리 인터페이스가 다양화됨. HBM 일변도에서 Conv. DRAM/CXL 등으로 분산 가능. 총 수요는 증가하나 HBM 비중 변화 모니터링 필요"

**V13: Edge/NPU 칩 스펙** | Weight: 5 | Event-driven | Investment | MD5

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 모바일 AP NPU TOPS 증가 | ▲ | Strong: 2x+, Mod: 1.5x | High: 칩 발표 | Conv. DRAM | 중기 |
| 기기당 모바일 DRAM/UFS 탑재량 증가 | ▲ | Strong: 세대 전환 + 용량 증가, Mod: 용량만 | High: 제품 스펙 | Conv. DRAM, NAND | 단기 |
| Edge AI 전용칩 양산 | ▲ | Strong: 100만대+, Mod: 10만대+ | Medium: 발표 | Conv. DRAM | 중기 |

**V14: CXL/차세대 메모리 인터페이스** | Weight: 4 | Event-driven | Strategic | MD3

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| CXL 상용 제품 출시/배치 | ▲ Bullish (caveat) | Strong: Hyperscaler 도입, Mod: 1사 도입 | High: 사례 발표 | Conv. DRAM | 장기 |
| 광 인터커넥트 칩 서버 탑재 확정 | ▲ | Strong: 양산 채택, Mod: 파일럿 | Medium: 발표 | HBM (간접) | 장기 |

> caveat (CXL): "메모리 풀링은 서버당 DRAM 슬롯 확대(▲)와 활용률 개선에 의한 총량 절감(▼) 양면 효과. 현 시점에서는 DRAM 총 수요 확대 방향으로 판정하되, 실제 배치 사례의 총량 데이터 모니터링"

#### B3. Memory & Storage

**V15: HBM 공급 경쟁 구도** | Weight: 6 | Event-driven + Periodic | Current-Next | MD2

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 경쟁사 HBM 증설 발표 | ▼ Bearish (caveat) | Strong: 대규모 증설, Mod: 점진적 | High: 공시 | HBM | 중기 |
| 경쟁사 수율/기술 이슈 | ▲ | Strong: 양산 지연, Mod: 수율 하락 보도 | Medium: 보도, Low: 루머 | HBM | 단기 |
| HBM 세대 전환 일정 변화 | ▲/▼ | 앞당김 = ▲ (선도 업체 유리), 지연 = ▼ (기존 세대 연장) | High: 공식 발표 | HBM | 중기 |

> caveat (경쟁사 증설): "공급 증가로 가격 하방 압력이나, 시장 성장 확인이자 생태계 확대 의미. 자사 점유율/기술 우위 관점에서 별도 분석 필요"

**V16: 스토리지 아키텍처 변화 (AI 워크로드)** | Weight: 5 | Event-driven | Next-Investment | MD3

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| KV Cache용 eSSD 채택 사례 | ▲ | Strong: Hyperscaler 표준, Mod: 1사 도입 | High: 기술 발표 | NAND | 중기 |
| AI 전용 스토리지 매출 증가 | ▲ | Strong: +50%+, Mod: +20-50% | High: 실적 | NAND | 단기 |
| 체크포인팅/학습 스토리지 수요 | ▲ | Strong: PB급 사례, Mod: 증가 보도 | Medium: 기술 보고서 | NAND | 중기 |

#### B4. Networking & Interconnect

**V18: AI 네트워크 대역폭/광 인터커넥트** | Weight: 5 | Event-driven | Investment | MD2

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 차세대 InfiniBand/Ethernet 출시 | ▲ | Strong: 세대 전환(400G→800G), Mod: 출하 증가 | High: 제품 발표 | HBM (간접) | 중기 |
| AI 클러스터 네트워크 규모 발표 | ▲ | Strong: 100K+ GPU, Mod: 10K+ | High: 기업 발표 | HBM | 단기 |
| 광 모듈/트랜시버 출하 급증 | ▲ | Strong: +100%+, Mod: +30-100% | High: 실적 | HBM (간접) | 중기 |

#### B5. Server & System Integration

**V20: AI 서버 출하/수주/재고** | Weight: 10 | Event-driven + Periodic | Current-Next | MD1

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| AI 서버 수주잔고 증가 | ▲ | Strong: +$1B+, Mod: +$500M+ | High: 실적 | HBM, Conv. DRAM | 단기 |
| AI 서버 매출/출하 실적 | ▲/▼ | Strong: YoY +50%+, Mod: +20-50% | High: 실적 | HBM, Conv. DRAM | 즉시 |
| 서버 ODM 가이던스 변경 | ▲/▼ | Strong: 연간 변경, Mod: 분기 변경 | High: 실적 | HBM, Conv. DRAM | 단기 |
| 고객사 충분한 재고 보유 보도/루머 | ▼ | Strong: 복수 소스 확인, Mod: 단일 보도, Weak: 루머 | Medium: 보도, Low: 루머 | HBM, Conv. DRAM | 단기 |
| 고객사 구매 decommit/발주 이연 | ▼ | Strong: 대형 고객 decommit, Mod: 일부 이연 | High: 직접 확인, Medium: 보도 | HBM, Conv. DRAM | 즉시 |
| 서버 ODM 재고 축적 보도 | ▲ Bullish (caveat) | Strong: 대규모 선구매, Mod: 소규모 | Medium: 보도 | HBM, Conv. DRAM | 단기 |

> caveat (ODM 재고 축적): "단기 출하 증가이나, 재고 소진 사이클 진입 시 발주 급감 가능. 재고 축적 기간과 규모를 추적하여 소진 시점 추정 필요"

> 재고 시그널 해석 원칙: 재고 축적 초기는 수요 강세 확인(▲)이나, 재고 수준이 비정상적으로 높아지면 향후 발주 급감의 선행 지표(▼). 과거 2022-2023 DRAM 다운사이클이 이 패턴이었음을 상기.

**V21: 서버 아키텍처 구성 변화** | Weight: 8 | Event-driven | Next-Investment | MD1

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 서버당 GPU/HBM 탑재량 증가 | ▲ | Strong: 2x+, Mod: 1.5x | High: 제품 스펙 | HBM | 중기 |
| 서버당 DRAM 용량 증가 | ▲ | Strong: 1TB+, Mod: 512GB-1TB | High: 제품 스펙 | Conv. DRAM | 중기 |
| 랙 스케일 아키텍처 확산 | ▲ | Strong: 대량 발주, Mod: 파일럿 | High: 발표 | HBM, Conv. DRAM | 단기 |

#### B6. Advanced Packaging & Components

**V22: 첨단 패키징 Capa 및 수급** | Weight: 9 | Event-driven + Periodic | Current-Next | MD2

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| CoWoS/FOPLP Capa 증설 | ▲ | Strong: 2x, Mod: +30-100% | High: 공시 | HBM | 중기 |
| 패키징 병목/대기 보도 | ▲ (수요 초과 확인) | Strong: 12M+ 대기, Mod: 6-12M | Medium: 보도 | HBM | 단기 |
| OSAT AI 매출 비중 증가 | ▲ | Strong: 50%+, Mod: 30-50% | High: 실적 | HBM | 중기 |

**V23: ABF/기판 수급** | Weight: 4 | Event-driven | Investment | MD2

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| ABF 증산 투자 | ▲ | Strong: 신규 라인, Mod: 기존 확장 | High: 공시 | HBM (간접) | 장기 |
| 기판 납기 연장/가격 상승 | ▲ (수요 초과) | Strong: 납기 연장, Mod: 가격 상승 | Medium: 보도 | HBM (간접) | 단기 |

---

#### C1. DC Operator & Colocation

**V24: DC 가용 용량 및 가동률** | Weight: 6 | Event-driven + Periodic | Next-Investment | MD1

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| Colo 신규 용량 확장 | ▲ | Strong: 100MW+, Mod: 30-100MW | High: 공시 | 복합 | 중기 |
| 입주율 90%+ | ▲ | Strong: 95%+, Mod: 90-95% | High: 실적 | 복합 | 단기 |
| 입주율 하락 | ▼ | Strong: -5%p+, Mod: -2-5%p | High: 실적 | 복합 | 단기 |

#### C2. Hyperscaler & GPU Cloud

**V26: Hyperscaler Capex 가이던스** | Weight: 10 | Event-driven + Periodic | Current-Next | MD1

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| Capex 가이던스 상향 | ▲ | Strong: +20%+, Mod: +10-20%, Weak: +10% 미만 | High: 실적 공시 | HBM, Conv. DRAM, NAND | 단기 |
| Capex 가이던스 하향/동결 | ▼ | Strong: 하향, Mod: 동결 | High: 실적 공시 | HBM, Conv. DRAM, NAND | 단기 |
| 실적 콜 AI 투자 톤 가속 | ▲ | Strong: CEO 직접 "가속", Mod: "지속" | High: 실적 콜 | 복합 | 단기 |
| 실적 콜 AI 투자 톤 신중 | ▼ | Strong: CEO "효율화 우선", Mod: "신중" | High: 실적 콜 | 복합 | 단기 |

**V27: Neocloud 자금 조달 및 확장** | Weight: 7 | Event-driven | Next-Investment | MD1

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 대규모 자금 조달 | ▲ | Strong: $5B+, Mod: $1-5B, Weak: $500M-1B | High: 공시 | HBM, Conv. DRAM | 중기 |
| GPU 클러스터 확장 | ▲ | Strong: 10K+ GPU, Mod: 1-10K | Medium: 발표 | HBM | 단기 |
| 가동률 하락/자금 조달 실패 | ▼ | Strong: 파산/구조조정, Mod: 가동률 하락 | High: 공시 | HBM, Conv. DRAM | 단기 |

**V28: 추론 인프라 투자** | Weight: 6 | Event-driven | Next-Investment | MD1

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 추론 전용 인프라 구축 | ▲ | Strong: 전용 DC, Mod: 전용 클러스터 | Medium: 발표 | Conv. DRAM, NAND | 중기 |
| 추론 칩 대량 배치 | ▲ | Strong: 만대+, Mod: 천대+ | Medium: 발표 | Conv. DRAM | 중기 |
| 추론 비용 인하 발표 | 효율화 프레임 적용 | 채택 속도 > 효율화 → ▲, 반대 → ▼ (caveat) | Medium: 가격 발표 | Conv. DRAM | 중기 |

---

### Tier 2: 모델/기술 트렌드 기반 단위당 메모리 계수 변화 (D→E→F)

#### D1-D4. AI Platform & Data Infra (통합)

**V29: 데이터/ML 인프라 활용 규모** | Weight: 4 | Event-driven + Periodic | Investment | MD3

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 데이터 플랫폼 매출/처리량 급증 | ▲ | Strong: +50%+, Mod: +20-50% | High: 실적 | Conv. DRAM | 중기 |
| 모델 허브 다운로드 급증 | ▲ | Strong: 월 10B+, Mod: 전월비 +30%+ | Medium: 발표 | Conv. DRAM | 중기 |
| Vector DB 고객/규모 성장 | ▲ | Strong: +100%+ YoY, Mod: +50-100% | High: 공시 | Conv. DRAM | 중기 |
| 학습 데이터 기업 대형 계약 | ▲ | Strong: $1B+, Mod: $100M+ | High: 공시 | HBM (간접) | 중기 |
| RAG 프레임워크 채택 급증 | ▲ | Strong: 월 다운로드 +200%+, Mod: +50-200% | Medium: 통계 | Conv. DRAM, NAND | 중기 |

#### E1. Foundation Models & LLM

**V34: 모델 스케일링 트렌드** | Weight: 9 | Event-driven | Current-Investment | MD3

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 차세대 모델 파라미터 규모 증가 | ▲ | Strong: 이전 5x+, Mod: 2-5x | High: 발표/논문 | HBM | 중기 |
| 컨텍스트 윈도우 확장 | ▲ | Strong: 1M+ 토큰, Mod: 200K-1M | High: 발표 | Conv. DRAM, NAND | 중기 |
| 학습 클러스터 규모 공개 | ▲ | Strong: 100K+ GPU, Mod: 10-100K | High: 발표 | HBM | 즉시 |
| 학습 비용 공개 | ▲ | Strong: $100M+, Mod: $10-100M | Medium: 보도 | HBM | 단기 |

**V35: 모델 효율화/경량화 트렌드** | Weight: 8 | Event-driven | Current-Investment | MD3

| 이벤트 유형 | 방향 | 판정 방법 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 양자화/압축 기술 상용화 | **효율화 프레임 적용** | 채택 속도 > 효율화 속도 → ▲, 반대 → ▼ (caveat) | High: 제품 적용 | HBM, Conv. DRAM | 중기 |
| KV Cache 압축/offloading 기술 | **효율화 프레임 적용** | 동일 | Medium: 논문/발표 | Conv. DRAM, NAND | 중기 |
| Mixture of Experts 등 아키텍처 변화 | **효율화 프레임 적용** | 동일 | Medium: 논문 | HBM, Conv. DRAM | 장기 |

> 효율화 이벤트 판정 기준: Stage 3 프롬프트에서 "이 효율화 기술의 메모리 절감률은 몇 %인가? 해당 서비스의 사용자/처리량 성장률은 몇 %인가? 절감률 < 성장률이면 ▲ Bullish, 절감률 > 성장률이면 ▼ Bearish (caveat: 채택 가속 시 반전 가능)"으로 판정 유도

**V36: 오픈소스/소버린 AI 확산** | Weight: 5 | Event-driven | Investment | MD3

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 주요 오픈소스 모델 출시 (70B+) | ▲ | Strong: 70B+, Mod: 7-70B | High: 릴리스 | HBM | 중기 |
| 소버린 AI 국가 프로젝트 | ▲ | Strong: $1B+, Mod: $100M+ | High: 정부 발표 | HBM, Conv. DRAM | 장기 |

**V37: 학습-추론 Compute 비율 변화** | Weight: 7 | Event-driven | Investment | MD3

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 추론 비중 증가 발언/데이터 | ▲ Bullish (caveat) | Strong: 정량 데이터 공개, Mod: 발언 | Medium: 실적 콜 | Conv. DRAM | 중기 |
| Test-time compute 확대 | ▲ | Strong: 주류 서비스 적용, Mod: 일부 적용 | Medium: 제품 | Conv. DRAM, NAND | 중기 |

> caveat (추론 비중): "HBM 대비 서버 DRAM 수요 비중 증가. HBM 총량이 줄지는 않으나, DRAM 성장 가속이 핵심 시사점"

#### E2-E3. AI 생성/음성 서비스

**V38: 생성형 AI 서비스 확산** | Weight: 5 | Event-driven | Next-Investment | MD4

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 생성형 AI MAU/생성 건수 | ▲ | Strong: MAU 100M+, Mod: 10-100M | Medium: 발표 | HBM, Conv. DRAM | 중기 |
| 비디오 생성 상용화 | ▲ | Strong: 유료 매출 급증, Mod: 베타 출시 | Medium: 발표 | HBM | 중기 |
| 음성 AI ARR/호출량 | ▲ | Strong: ARR $100M+ 또는 YoY +200%+ | High: 공시 | Conv. DRAM | 중기 |
| Voice Agent 대규모 배치 | ▲ | Strong: 100+ 엔터프라이즈, Mod: 10-100 | Medium: 보도 | Conv. DRAM | 중기 |
| 실시간 멀티모달 서비스 | ▲ | Strong: 4K 비디오+음성, Mod: 단일 모달리티 | Medium: 제품 | Conv. DRAM | 단기 |

#### F1-F2. AI 개발도구 & Agent

**V42: 코딩/에이전트 AI 활용 확산** | Weight: 6 | Event-driven | Next-Investment | MD4

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 코딩 AI DAU/ARR 이정표 | ▲ | Strong: DAU 1M+ 또는 ARR $500M+, Mod: 급성장 보도 | Medium: 발표 | Conv. DRAM | 중기 |
| 코드 특화 모델 학습 투자 | ▲ | Strong: $500M+, Mod: $100-500M | High: 공시 | HBM | 중기 |
| Agent 플랫폼 ARR/고객 성장 | ▲ | Strong: ARR $100M+, Mod: $10-100M | Medium: 보도 | Conv. DRAM | 중기 |
| Agent 인프라 자금 조달 | ▲ | Strong: $100M+, Mod: $10-100M | High: 공시 | Conv. DRAM | 장기 |
| Agent 호출 체인 복잡도 증가 | ▲ | Strong: 10+ LLM 호출/태스크, Mod: 3-10 | Low: 기술 블로그 | Conv. DRAM | 장기 |

---

### Tier 3: 실제 활용 기반 수요 실현 검증 (G+H+J) — Issue 8 통합 적용

기존 15개 변수 → **4개 그룹 변수**로 통합

**VG_SaaS: Enterprise SaaS AI 추론 수요** | Weight: 4 | Event-driven | Investment-Strategic | MD4

G1(Enterprise AI) + G2(Conversational) + G3(Productivity) + G4(Search) + H2(Legal) + H3(Finance) + H6(Marketing) + H7(HR) + H8(Climate) + H9(Education) 통합

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 대형 Enterprise AI 계약 (ACV $100M+) | ▲ | Strong | High: 공시 | Conv. DRAM | 장기 |
| AI SaaS 도입률 서베이 (Fortune500 50%+) | ▲ | Strong | Medium: 리서치 | Conv. DRAM | 장기 |
| AI 검색 MAU 100M+ 또는 기존 대비 30%+ 비중 | ▲ | Strong | Medium: 발표 | Conv. DRAM | 중기 |
| Conversational/Productivity AI MAU 급증 | ▲ | Mod | Medium: 발표 | Conv. DRAM | 장기 |
| Vertical AI(법률/금융/HR/교육 등) 대형 계약 | ▲ | Mod | Medium: 보도 | Conv. DRAM | 장기 |
| AI SaaS 도입 정체/이탈 보도 | ▼ | Strong: 다수 기업 이탈, Mod: 성장 둔화 | Medium: 보도 | Conv. DRAM | 장기 |

**VG_IndDef: 산업/국방 AI 수요** | Weight: 5 | Event-driven | Investment-Strategic | MD4

G5(Industrial) + H4(Defense) + H5(Supply Chain) 통합

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| 국방 AI 대형 계약 ($1B+) | ▲ | Strong | High: 정부 공시 | Conv. DRAM, NAND | 장기 |
| 산업 AI 글로벌 제조사 전면 도입 | ▲ | Strong | Medium: 보도 | Conv. DRAM, NAND | 장기 |
| Digital Twin 플랫폼 매출 +50%+ | ▲ | Mod | High: 실적 | HBM, Conv. DRAM | 장기 |
| 소버린 AI 국방 인프라 구축 | ▲ | Strong | High: 정부 발표 | Conv. DRAM | 장기 |

**V52: Healthcare/Bio AI 수요** | Weight: 4 | Event-driven | Strategic | MD4

H1 단독 (Bio AI는 compute 집약도가 다른 버티컬 대비 현저히 높아 별도 유지)

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| AI 신약 Phase 3+ 다수 진입 | ▲ | Strong | High: FDA/EMA | HBM | 장기 |
| Bio AI 대규모 컴퓨트 투자 | ▲ | Strong: 자체 GPU 클러스터 | Medium: 발표 | HBM | 중기 |
| 의료 AI 기기 월 10건+ 승인 | ▲ | Mod | High: FDA 데이터 | DRAM (Edge) | 장기 |

**V62: AV/Robotics 수요** | Weight: 6 | Event-driven | Investment-Strategic | MD5

H10(AV) + J1(Robotics) 통합

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| AV 학습 인프라 투자 (10K+ GPU) | ▲ | Strong | High: 발표 | HBM, NAND | 중기 |
| Robotaxi/AV 트럭 10K대+ 배치 | ▲ | Strong | High: 발표 | Conv. DRAM, NAND | 중기 |
| 차량당 모바일 DRAM(LPDDR5X) 32GB+ 스펙 | ▲ | Strong | High: 제품 스펙 | Conv. DRAM | 중기 |
| 산업/서비스 로봇 출하 YoY +30%+ | ▲ | Strong | High: IFR 통계 | Conv. DRAM, NAND | 중기 |
| 로봇 Foundation Model 자금 조달 $500M+ | ▲ | Strong | High: 공시 | HBM | 장기 |
| 휴머노이드 1,000대+ 양산 확정 | ▲ | Strong | Medium: 발표 | Conv. DRAM | 장기 |

---

### 횡단: I (Security & Governance) — Tier 2-3에만 영향

**V65: AI 보안/규제 환경 변화** | Weight: 3 | Event-driven | Investment | MD4

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| AI 보안 솔루션 매출 +50%+ | ▲ | Strong | High: 실적 | Conv. DRAM | 장기 |
| AI 규제 강화 (EU AI Act 등) | ▼ Bearish (caveat) | Strong: 주요국 시행, Mod: 가이드라인 | High: 정부 | Conv. DRAM | 장기 |
| AI 보안 사고 (모델 탈취 등) | ▼ Bearish (caveat) | Strong: 대형 사고, Mod: 중소 사고 | High: 보도 | Conv. DRAM | 중기 |

> caveat (규제): "단기 도입 지연이나, On-prem 전환 시 기업 전용 서버 수요 증가. AI 관련 지출 자체가 줄지는 않을 전망"
> caveat (보안 사고): "단기 도입 주저이나, 중기 보안 인프라 투자 확대로 이어질 가능성"

**V68: Edge AI 인프라 확산** | Weight: 3 | Event-driven | Strategic | MD5

| 이벤트 유형 | 방향 | 강도 기준 | Confidence | 메모리 | 시간축 |
|------------|------|----------|-----------|--------|--------|
| Edge AI 프로세서 100만대+ 출하 | ▲ | Strong | Medium: 발표 | Conv. DRAM, NAND | 중기 |
| Edge AI 최적화 도구 확산 | ▲ | Mod | Medium: 보도 | Conv. DRAM | 장기 |

---

## Part 3: 변수 요약 및 가중치 테이블

### 전체 변수 목록 (46개, v1 대비 25개 감축)

| ID | 변수명 | Weight | Tier | Driver | 관측 유형 | Decision Relevance |
|----|--------|--------|------|--------|----------|-------------------|
| V01 | AI DC 전력 프로젝트 | 5 | T1 | MD1 | Event | Investment-Strategic |
| V02 | 전력 병목 시그널 | 4 | T1 | MD1 | Event | Investment |
| V03 | 액냉/고밀도 냉각 수주 | 4 | T1 | MD1 | Event | Investment |
| V04 | 신규 DC 착공 규모 | 6 | T1 | MD1 | Event | Investment-Strategic |
| V08 | HBM/패키징 장비 수주 | 8 | T1 | MD2 | Event+Periodic | Current-Next |
| V09 | EUV/첨단 공정 장비 | 5 | T1 | MD2 | Periodic | Investment |
| V10 | EDA/IP 라이선스 | 3 | T1 | MD2 | Periodic | Strategic |
| V11 | GPU/가속기 스펙/출하 | **10** | T1 | MD2 | Event | Current-Next |
| V12 | Custom ASIC 동향 | 7 | T1 | MD2 | Event | Next-Investment |
| V13 | Edge/NPU 칩 스펙 | 5 | T1 | MD5 | Event | Investment |
| V14 | CXL/차세대 인터페이스 | 4 | T1 | MD3 | Event | Strategic |
| V15 | HBM 공급 경쟁 구도 | 6 | T1 | MD2 | Event+Periodic | Current-Next |
| V16 | 스토리지 아키텍처 (AI) | 5 | T1 | MD3 | Event | Next-Investment |
| V18 | 네트워크/광 인터커넥트 | 5 | T1 | MD2 | Event | Investment |
| V20 | AI 서버 출하/수주 | **10** | T1 | MD1 | Event+Periodic | Current-Next |
| V21 | 서버 아키텍처 변화 | 8 | T1 | MD1 | Event | Next-Investment |
| V22 | 패키징 Capa/수급 | 9 | T1 | MD2 | Event+Periodic | Current-Next |
| V23 | ABF/기판 수급 | 4 | T1 | MD2 | Event | Investment |
| V24 | DC 가용 용량/가동률 | 6 | T1 | MD1 | Event+Periodic | Next-Investment |
| V26 | Hyperscaler Capex | **10** | T1 | MD1 | Event+Periodic | Current-Next |
| V27 | Neocloud 자금/확장 | 7 | T1 | MD1 | Event | Next-Investment |
| V28 | 추론 인프라 투자 | 6 | T1 | MD1 | Event | Next-Investment |
| V29 | 데이터/ML 인프라 규모 | 4 | T2 | MD3 | Event+Periodic | Investment |
| V34 | 모델 스케일링 트렌드 | 9 | T2 | MD3 | Event | Current-Investment |
| V35 | 모델 효율화/경량화 | 8 | T2 | MD3 | Event | Current-Investment |
| V36 | 오픈소스/소버린 AI | 5 | T2 | MD3 | Event | Investment |
| V37 | 학습-추론 비율 변화 | 7 | T2 | MD3 | Event | Investment |
| V38 | 생성형 AI 서비스 확산 | 5 | T2 | MD4 | Event | Next-Investment |
| V42 | 코딩/에이전트 AI 확산 | 6 | T2 | MD4 | Event | Next-Investment |
| VG_SaaS | Enterprise SaaS AI | 4 | T3 | MD4 | Event | Investment-Strategic |
| VG_IndDef | 산업/국방 AI | 5 | T3 | MD4 | Event | Investment-Strategic |
| V52 | Healthcare/Bio AI | 4 | T3 | MD4 | Event | Strategic |
| V62 | AV/Robotics | 6 | T3 | MD5 | Event | Investment-Strategic |
| V65 | AI 보안/규제 | 3 | 횡단 | MD4 | Event | Investment |
| V68 | Edge AI 인프라 | 3 | 횡단 | MD5 | Event | Strategic |

### Weight 분포

- Weight 10 (최고): V11(GPU 스펙), V20(서버 출하), V26(Hyperscaler Capex) — 3개
- Weight 8-9: V08(HBM 장비), V21(서버 아키텍처), V22(패키징), V34(모델 스케일링), V35(효율화) — 5개
- Weight 5-7: 14개
- Weight 3-4: 13개

### Weight 보정 로드맵

현재 Weight는 전문가 판단 기반 초기 모델이다. 데이터 축적 후 아래 절차로 보정 예정:

1. 데이터 축적 (v2 운영 2-3분기): 시그널 발생 이력과 실제 메모리 출하/가격 변화 데이터 수집
2. 상관관계 분석: 각 변수의 시그널 방향과 후속 메모리 수요 변화(bit growth, ASP)의 상관계수 측정
3. Weight 보정: 상관관계가 높은 변수의 Weight 상향, 낮은 변수는 하향 또는 폐기
4. 반복: 매 반기 1회 백테스트 수행, Weight 갱신

이 과정을 통해 시스템이 시간이 갈수록 정확해지는 학습 구조를 확보한다.

---

## Part 4: Category Key 매핑 (Issue 10 반영)

### DB 스키마 변경

```sql
ALTER TABLE companies ADD COLUMN IF NOT EXISTS category_key TEXT;

UPDATE companies SET category_key = regexp_replace(category, '^([A-Z]\d+)\..*', '\1');

CREATE INDEX IF NOT EXISTS idx_companies_catkey ON companies(category_key);
```

### 코드 레벨 (seed_db.py 수정)

```python
import re

def extract_category_key(category: str) -> str:
    """'A1. Energy & Power' → 'A1'"""
    m = re.match(r'^([A-Z]\d+)', category.strip())
    return m.group(1) if m else "XX"
```

### Pipeline v2 코드에서의 사용

```python
# 기존 (취약)
cat_key = company["category"].split(".")[0].strip()

# 변경 (안정)
cat_key = company["category_key"]  # DB에서 직접 조회
```

---

## Part 5: Expected Event Calendar (Issue 6 부분 반영)

### 개요

향후 4-5주의 예정된 이벤트를 보여주는 별도 탭. "침묵 = Bearish" 해석은 적용하지 않음. 순수하게 "어떤 이벤트가 예정되어 있고, 어떤 변수에 영향을 줄 수 있는가"를 사전 안내하는 용도.

### DB 테이블

```sql
CREATE TABLE IF NOT EXISTS expected_events (
    id              SERIAL PRIMARY KEY,
    company_id      INT REFERENCES companies(id),
    event_type      TEXT NOT NULL,     -- earnings, product_launch, conference, regulatory
    expected_date   DATE NOT NULL,
    description     TEXT,
    variable_ids    TEXT[],            -- 영향받을 변수 ID 목록
    source          TEXT,              -- 일정 출처
    is_confirmed    BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_expected_date ON expected_events(expected_date);
```

### 주요 등록 대상

| 이벤트 유형 | 대상 기업 | 영향 변수 | 등록 방법 |
|------------|----------|----------|----------|
| 분기 실적 발표 | Hyperscaler 4사, NVIDIA, AMD, TSMC, 서버 ODM | V11, V20, V22, V26 | SEC 실적 캘린더 기반 자동/반자동 |
| 제품 발표/컨퍼런스 | NVIDIA(GTC), Google(I/O), Apple(WWDC) | V11, V13, V21 | 연간 컨퍼런스 일정 수동 등록 |
| 정부 정책/규제 | EU AI Act 시행일, 미국 반도체 수출 규제 | V65 | 수동 등록 |
| 산업 통계 발표 | IFR(로봇), IDC(서버), Gartner(시장 전망) | V62, V20, 다수 | 발표 일정 수동 등록 |

### 프론트엔드 표시

대시보드에 "Upcoming Events" 탭 추가. 주차별로 그룹화하여 표시:

```
이번 주 (4/7-4/11)
  4/9  TSMC Q1 실적 발표 → V22(패키징 Capa), V08(장비 수주)
  4/10 Google Cloud Next → V26(Hyperscaler), V28(추론 인프라)

다음 주 (4/14-4/18)
  4/15 NVIDIA 신제품 발표 예정 → V11(GPU 스펙), V21(서버 아키텍처)
  4/17 CoreWeave Q1 보고 → V27(Neocloud)
...
```

---

## Part 6: 향후 개선 필요 사항 (Issue 4 보류분)

### 정량 추정 모델 개발 (Priority: High, Complexity: High)

현재 시스템은 방향과 강도만 출력. 경영진의 궁극적 필요는 "HBM 수요가 몇 GB/wafer 변하는가".

**단계적 접근 제안:**

Phase 1 (v2.5): Order of Magnitude 추정
- Stage 3 프롬프트에 "이 이벤트의 HBM 수요 영향은 대략 수천/수만/수십만 단위 중 어디인가" 필드 추가
- 정확하지 않아도 크기감 제공

Phase 2 (v3): 제품별 수요 추정 모델
- Tier 1 핵심 변수(V11, V20, V26)에 대해 정량 변환 공식 개발
- 예: "Hyperscaler capex $X → GPU 서버 약 Y만대 → HBM 약 Z GB"
- 공식의 파라미터(GPU당 HBM 용량, ASP 등)는 분기별 업데이트

Phase 3 (v4): 교차 검증 메커니즘
- Tier 1(투자 기반 추정) vs Tier 3(활용 기반 역산)의 수요 추정치 비교
- 괴리가 크면 "수요 실현 갭" 또는 "과잉 투자" 경고

**HBM/DRAM/NAND별 추정의 어려움:**
- HBM: GPU 스펙에 종속. 상대적으로 정량화 용이 (GPU수 × HBM/GPU)
- DRAM: 학습/추론/엔터프라이즈 등 용도가 분산. 용도별 추정 모델 별도 필요
- NAND: KV Cache, 체크포인팅, 스토리지 등 용도 다양. 가장 추정 어려움

---

## Part 7: Pipeline v2 프롬프트 변경 요약

### Stage 1 변경 없음 (사실 추출)

v1 핸드오프 문서의 Stage 1 프롬프트 유지.

### Stage 2 변경 사항

1. `"structural"` 방향 제거. 응답 스키마에서 `"direction": "bullish|bearish"` 만 허용
2. `"caveat"` 필드 추가: `"caveat": "string or null"`
3. `"needs_review"` 필드 추가: `"needs_review": true/false` (방향 판정 불확실 시)
4. 카테고리별 variable_definitions에 Weight 정보 포함
5. 효율화 관련 이벤트 판정 시 효율화 프레임 지시 추가

Stage 2 응답 스키마 (수정):
```json
{
  "variable_id": "V26",
  "variable_name": "Hyperscaler Capex 가이던스",
  "direction": "bullish",
  "caveat": null,
  "needs_review": false,
  "strength": "strong",
  "confidence": "high",
  "affected_memory": ["HBM", "Conv. DRAM", "NAND"],
  "reasoning": "MS FY26 capex +19% 상향은 GPU 서버 발주 증가 직결"
}
```

### Stage 3 변경 사항

1. `"demand_formula_role"` 필드: 수요 공식에서의 역할 명시
2. `"counterargument"` 필드 유지
3. Jevons Paradox 대신 효율화 프레임 적용 지시
4. `"decision_relevance"` 필드 추가: `"current_quarter|next_quarter|investment_plan|strategic_reference"`

Stage 3 응답 스키마 (수정):
```json
{
  "transmission_path": "MS capex $80B→$95B (+19%) → GPU 서버 발주 증가 → HBM 수요 +15-20% (6-9M)",
  "memory_impact": {
    "HBM": {"direction": "bullish", "magnitude": "high", "detail": "GPU 서버 증가에 따른 직접 수요"},
    "Conv_DRAM": {"direction": "bullish", "magnitude": "medium", "detail": "서버 DRAM 동반 수요"},
    "NAND": {"direction": "bullish", "magnitude": "low", "detail": "스토리지 간접 수요"}
  },
  "time_lag": "short_3-6m",
  "demand_formula_tier": "tier1",
  "demand_formula_role": "인프라 투자 총량(Tier 1) 증가. 물리적 서버 발주 수 증가로 메모리 수요 총량 확대.",
  "decision_relevance": "current_quarter",
  "counterargument": "AI 투자 ROI 미입증 시 차년도 capex 감축 가능. 추론 수요 실현 여부 모니터링 필요.",
  "executive_summary": "MS가 FY26 AI 인프라 투자를 $95B로 19% 상향 발표. GPU 서버 발주 증가에 따라 HBM/DRAM/NAND 전 제품군 수요 상승 예상. Confidence: High (실적 공시 기반)."
}
```
---

## Part 8: Divergence Alert 규칙

### 개요

5개 Driver 또는 3개 Tier의 시그널 방향이 엇갈릴 때, 자동으로 경고를 생성한다. 이것이 메모리 사이클 전환점을 조기에 포착하는 핵심 메커니즘이다.

### Alert 유형

**Alert 1: 투자-실현 괴리 (Overinvestment Risk)**

- 조건: MD1(인프라 투자) Bullish + MD4(추론 수요 실현) Bearish, 2주 이상 지속
- 의미: 인프라는 확장되나 실제 AI 활용이 뒤따르지 않음. 과잉 투자 초기 징후
- 경영진 메시지: "인프라 투자 대비 추론 수요 실현이 지연되고 있음. 수요 실현 추이 주시 필요"
- 정교화 필요 사항: MD1 내에서도 Hyperscaler capex(V26) vs Neocloud(V27)를 구분하여 판단해야 함. Hyperscaler는 자체 서비스 기반이므로 외부 수요 실현과 무관하게 투자 지속 가능. Neocloud의 가동률 하락이 동반되면 Alert 강도 상향

**Alert 2: 공급 병목 (Supply Bottleneck)**

- 조건: MD4(추론 수요) Bullish + MD2(반도체 공급) Bearish, 2주 이상 지속
- 의미: 수요는 강하나 칩/패키징/장비 공급이 제약. 메모리 가격 상승 가능
- 경영진 메시지: "수요 강세 대비 공급 제약 감지. 단기 가격 상승 및 할당 우선순위 검토 필요"
- 정교화 필요 사항: 병목 지점 특정 필요. V22(패키징) Bearish vs V11(GPU 지연) Bearish는 대응이 다름

**Alert 3: 효율화 가속 (Efficiency Acceleration)**

- 조건: MD3(메모리 계수) 내 V35(효율화)에서 Bearish 시그널 3건 이상 누적, 동시에 MD4(추론 수요) Bullish 강도 약화
- 의미: 모델 효율화 속도가 채택 속도를 초과하기 시작. 단위당 메모리 수요 순감소 가능
- 경영진 메시지: "모델 효율화 기술의 상용화가 가속되고 있음. 단위당 메모리 소비 변화 추이 주시 필요"
- 정교화 필요 사항: 제품별 영향이 다름. 양자화는 HBM 영향, KV Cache 압축은 NAND 영향. 제품별 세분화 Alert 추가 검토

**Alert 4: Tier 전면 동조 하락 (Cycle Downturn Signal)**

- 조건: MD1 + MD2 + MD4 모두 Bearish, 1주 이상 지속
- 의미: 인프라, 공급, 수요 전 영역 위축. 다운사이클 진입 가능성
- 경영진 메시지: "전 계층 하향 시그널 감지. 사이클 전환 가능성 검토 필요"
- 정교화 필요 사항: 단기 노이즈와 실제 사이클 전환 구분이 핵심. 1주는 너무 짧을 수 있으며, Bearish 강도(Strong 비율)와 V26(Hyperscaler capex) 방향을 추가 확인

**Alert 5: Tier 전면 동조 상승 (Cycle Upturn Confirmation)**

- 조건: MD1 + MD4 + MD5 모두 Bullish, 2주 이상 지속
- 의미: 인프라 투자 + 추론 수요 + Edge 수요 동시 성장 확인
- 경영진 메시지: "전 계층 상승 시그널. 수요 확장 사이클 확인"
- 정교화 필요 사항: "이미 가격에 반영되었는가"를 함께 판단해야 의미 있음. 향후 priced_in_risk 도입 시 연계

### Alert 운영 규칙

- Alert는 대시보드 최상단에 배너 형태로 표시
- 발생 조건 충족 시 자동 생성, 조건 해소 시 자동 해제
- Alert 이력은 별도 로그로 보관 (과거 Alert와 실제 시장 변화 대조용, Weight 백테스트에 활용)
- 초기 운영에서는 Alert 임계값(지속 기간, 시그널 건수)을 보수적으로 설정하고, 오탐/미탐 비율을 보며 조정

### 향후 정교화 방향

- 현재는 Driver 단위 방향 비교로 단순 구현. 향후 변수 단위 가중 합산 점수의 시계열 변화를 기반으로 통계적 이상 탐지(z-score 등) 적용 가능
- Alert와 실제 메모리 가격/출하 변화의 상관관계 백테스트를 통해 Alert 신뢰도 보정
