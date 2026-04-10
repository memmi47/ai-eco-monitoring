"""
AI Eco Monitor - Pipeline v2 Variable Definitions
Design v2 Consolidated (design_v2_consolidated.md) 기준

46개 측정변수 | 메모리 제품: HBM / Conv. DRAM / NAND
"""

import re


def extract_category_key(category: str) -> str:
    """'A1. Energy & Power' → 'A1'"""
    if not category:
        return "XX"
    m = re.match(r'^([A-Z]\d+)', category.strip())
    return m.group(1) if m else "XX"


def _get_tier(layer: str) -> str:
    """Layer 대분류 → Tier 매핑"""
    if not layer:
        return "tier3"
    prefix = layer.split(".")[0].strip()
    if prefix in ("A", "B", "C"):
        return "tier1"
    elif prefix in ("D", "E", "F"):
        return "tier2"
    elif prefix in ("G", "H", "J"):
        return "tier3"
    elif prefix == "I":
        return "cross"
    return "tier3"


# ============================================================
# TIER CONTEXT - Stage 3 프롬프트 주입용
# ============================================================

TIER_CONTEXTS = {
    "tier1": (
        "This is a Tier 1 (Infrastructure) signal. It directly indicates physical compute capacity being built. "
        "Focus on quantifying how much memory this infrastructure will require. "
        "Key question: how many servers/GPUs does this translate to, and what memory configuration per unit? "
        "Memory demand formula role: VOLUME factor."
    ),
    "tier2": (
        "This is a Tier 2 (Model/Technology) signal. It affects the per-unit memory coefficient. "
        "Focus on whether this changes how much memory each server/GPU/device needs. "
        "For efficiency events (quantization, compression, etc.), apply the efficiency frame: "
        "compare efficiency speed vs adoption speed. If adoption > efficiency → Bullish. If efficiency > adoption → Bearish (add caveat). "
        "Key question: does this increase or decrease memory per unit? "
        "Memory demand formula role: PER-UNIT COEFFICIENT factor."
    ),
    "tier3": (
        "This is a Tier 3 (Application/Demand) signal. It validates whether AI infrastructure investment "
        "is translating into actual usage. Focus on inference demand volume. "
        "Key question: is AI actually being used at scale? Which applications are driving real compute demand? "
        "Memory demand formula role: UTILIZATION/REALIZATION RATE factor."
    ),
    "cross": (
        "This is a cross-tier Security & Governance signal. It affects Tier 2 and Tier 3 only. "
        "For regulation events: short-term adoption delay (Bearish) but mid-term on-prem conversion increases enterprise server demand. "
        "For security incidents: short-term hesitation (Bearish) but mid-term security infra investment (Bullish). "
        "Always add caveat field explaining both directions."
    ),
}


# ============================================================
# VARIABLE DEFINITIONS - Stage 2 프롬프트 주입용
# Category key → 변수 목록 문자열
# 기준: design_v2_consolidated.md (파일4)
# ============================================================

VARIABLE_DEFINITIONS = {

    # ========== TIER 1: 인프라 투자 규모 기반 수요 추정 ==========

    "A1": """
V01: AI DC 전용 전력 프로젝트 규모 [Weight:5 | Investment-Strategic | MD1]
  Bullish: SMR/원자력 PPA 체결(Strong:100MW+, Mod:50-100MW), DC 전용 발전소 가동 승인, 전력 구매 규모 확대
  Bearish: 전력 프로젝트 취소(Strong)/일정 지연(Mod)
  Affected memory: HBM, Conv. DRAM, NAND (복합)

V02: 전력 공급 병목 시그널 [Weight:4 | Investment | MD1]
  Bearish(caveat): 전력망 연결 대기 증가(Strong:24M+ 대기), DC 프로젝트 전력 미확보 지연
  Bullish: 정부 DC 전력 우선 배분 정책 통과
  Bearish: 정부 DC 전력 제한 정책
  caveat: "단기 메모리 수요 이연이나, 병목 해소 시 지연된 수요 일시 반영 가능"
  Affected memory: HBM, Conv. DRAM, NAND (복합)
""",

    "A2": """
V03: 액냉/고밀도 냉각 수주 추이 [Weight:4 | Investment | MD1]
  Bullish: 액냉 장비 수주 증가(Strong:YoY +100%+, Mod:+30-100%), 고밀도 랙 표준 변경(100kW+=Strong), GPU 서버 TDP 세대별 증가(Strong:2x+)
  Affected memory: HBM, Conv. DRAM
""",

    "A3": """
V04: 신규 DC 착공 규모 [Weight:6 | Investment-Strategic | MD1]
  Bullish: DC 착공/설계 수주 발표(Strong:100MW+, Mod:30-100MW)
  Bearish: DC 프로젝트 취소/보류(Strong:Hyperscaler, Mod:Neocloud)
  Bearish(caveat): DC 건설 단가 급등(Strong:+30%+)
  caveat(건설단가): "비용 상승이 투자 축소로 이어질지, 비용 전가로 흡수될지 모니터링 필요"
  Affected memory: HBM, Conv. DRAM, NAND (복합)
""",

    "B1": """
V08: HBM/첨단 패키징 장비 수주 [Weight:8 | Current-Next | MD2]
  Bullish: HBM TSV/본딩 장비 수주 증가(Strong:+50%+, Mod:+20-50%), HBM 테스터 출하 증가(Strong:신세대 전용)
  Bearish: 메모리 장비 발주 감소/이연(Strong:대형 업체 감축)
  Affected memory: HBM

V09: EUV/첨단 공정 장비 출하 [Weight:5 | Investment | MD2]
  Bullish: ASML EUV/High-NA 출하 실적(Strong:가이던스 초과), 로직 파운드리 첨단 공정 양산(Strong:3nm 이하)
  Affected memory: HBM (간접: 로직칩→GPU→HBM)

V10: EDA/IP 라이선스 트렌드 [Weight:3 | Strategic | MD2]
  Bullish: AI 칩 EDA 매출 증가(Strong:+30%+), 신규 AI ASIC 설계 발표(Strong:Hyperscaler 자체칩)
  Affected memory: HBM, Conv. DRAM (간접, 장기)
""",

    "B2": """
V11: GPU/AI 가속기 스펙 및 출하 [Weight:10 | Current-Next | MD2]
  Bullish: 차세대 GPU 발표(Strong:HBM 세대 전환, Mod:동일 세대 용량 증가), GPU 양산 앞당김(Strong:분기 이상), GPU 출하량 가이던스 상향(Strong:+30%+)
  Bearish: GPU 양산 지연(Strong:분기 이상), 출하 가이던스 하향
  Affected memory: HBM

V12: Custom ASIC 프로젝트 동향 [Weight:7 | Next-Investment | MD2]
  Bullish: ASIC 고객 수 증가(Strong:신규 Hyperscaler 고객), 자체칩 양산 확정
  Bullish(caveat): ASIC의 GPU 대체 비율 변화
  caveat: "GPU 대비 ASIC은 메모리 인터페이스 다양화. HBM 일변도에서 Conv. DRAM/CXL로 분산 가능"
  Affected memory: HBM, Conv. DRAM

V13: Edge/NPU 칩 스펙 [Weight:5 | Investment | MD5]
  Bullish: 모바일 AP NPU TOPS 증가(Strong:2x+), 기기당 모바일 DRAM/UFS 탑재량 증가(Strong:세대 전환+용량 증가)
  Bullish: Edge AI 전용칩 양산(Strong:100만대+)
  Affected memory: Conv. DRAM, NAND

V14: CXL/차세대 메모리 인터페이스 [Weight:4 | Strategic | MD3]
  Bullish(caveat): CXL 상용 제품 출시/배치(Strong:Hyperscaler 도입)
  Bullish: 광 인터커넥트 칩 서버 탑재 확정(Strong:양산 채택)
  caveat(CXL): "메모리 풀링은 서버당 DRAM 슬롯 확대(▲)와 활용률 개선에 의한 총량 절감(▼) 양면 효과. 현 시점 DRAM 총 수요 확대 방향 판정"
  Affected memory: Conv. DRAM, HBM (간접)
""",

    "B3": """
V15: HBM 공급 경쟁 구도 [Weight:6 | Current-Next | MD2]
  Bearish(caveat): 경쟁사 HBM 증설 발표(Strong:대규모)
  Bullish: 경쟁사 수율/기술 이슈(Strong:양산 지연)
  caveat(경쟁사 증설): "공급 증가로 가격 하방 압력이나, 시장 성장 확인. 자사 점유율/기술 우위 관점 별도 분석 필요"
  Affected memory: HBM

V16: 스토리지 아키텍처 변화(AI 워크로드) [Weight:5 | Next-Investment | MD3]
  Bullish: KV Cache용 eSSD 채택(Strong:Hyperscaler 표준), AI 전용 스토리지 매출 증가(Strong:+50%+), 체크포인팅/학습 스토리지 수요(Strong:PB급)
  Affected memory: NAND
""",

    "B4": """
V18: AI 네트워크 대역폭/광 인터커넥트 [Weight:5 | Investment | MD2]
  Bullish: 차세대 InfiniBand/Ethernet 출시(Strong:세대 전환 400G→800G), AI 클러스터 규모 발표(Strong:100K+ GPU)
  Bullish: 광 모듈/트랜시버 출하 급증(Strong:+100%+)
  Affected memory: HBM (간접: 네트워크→클러스터 확대→HBM)
""",

    "B5": """
V20: AI 서버 출하/수주/재고 [Weight:10 | Current-Next | MD1]
  Bullish: AI 서버 수주잔고 증가(Strong:+$1B+), 매출/출하 실적 증가(Strong:YoY+50%+), ODM 가이던스 상향(Strong:연간 변경)
  Bullish(caveat): 서버 ODM 재고 축적 보도(Strong:대규모 선구매)
  Bearish: 수주잔고 감소, 가이던스 하향, 고객사 충분한 재고 보유 보도(Strong:복수 소스 확인)
  Bearish: 고객사 구매 decommit/발주 이연(Strong:대형 고객 decommit)
  caveat(재고 축적): "단기 출하 증가이나, 재고 소진 사이클 진입 시 발주 급감 가능. 2022-2023 DRAM 다운사이클 패턴 참고"
  Affected memory: HBM, Conv. DRAM

V21: 서버 아키텍처 구성 변화 [Weight:8 | Next-Investment | MD1]
  Bullish: 서버당 GPU/HBM 탑재량 증가(Strong:2x+), 서버당 DRAM 용량 증가(Strong:1TB+), 랙 스케일 아키텍처 확산(Strong:대량 발주)
  Affected memory: HBM, Conv. DRAM
""",

    "B6": """
V22: 첨단 패키징 Capa 및 수급 [Weight:9 | Current-Next | MD2]
  Bullish: CoWoS/FOPLP Capa 증설(Strong:2x, Mod:+30-100%), 패키징 병목/대기 보도(Strong:12M+ 대기=수요 초과 확인)
  Bullish: OSAT AI 매출 비중 증가(Strong:50%+)
  Affected memory: HBM (패키징 Capa = HBM 병목)

V23: ABF/기판 수급 [Weight:4 | Investment | MD2]
  Bullish: ABF 증산 투자(Strong:신규 라인), 기판 납기 연장/가격 상승(Strong:납기 연장=수요 초과)
  Affected memory: HBM (간접)
""",

    "C1": """
V24: DC 가용 용량 및 가동률 [Weight:6 | Next-Investment | MD1]
  Bullish: Colo 신규 용량 확장(Strong:100MW+, Mod:30-100MW), 입주율 90%+(Strong:95%+)
  Bearish: 입주율 하락(Strong:-5%p+)
  Affected memory: HBM, Conv. DRAM, NAND (복합)
""",

    "C2": """
V26: Hyperscaler Capex 가이던스 [Weight:10 | Current-Next | MD1]
  Bullish: Capex 가이던스 상향(Strong:+20%+, Mod:+10-20%), 실적 콜 AI 투자 톤 가속(Strong:CEO 직접 "가속")
  Bearish: Capex 가이던스 하향/동결(Strong:하향, Mod:동결), 실적 콜 AI 투자 톤 신중(Strong:CEO "효율화 우선")
  Affected memory: HBM, Conv. DRAM, NAND (가장 강력한 단일 선행 변수)

V27: Neocloud 자금 조달 및 확장 [Weight:7 | Next-Investment | MD1]
  Bullish: 대규모 자금 조달(Strong:$5B+, Mod:$1-5B), GPU 클러스터 확장(Strong:10K+ GPU)
  Bearish: 가동률 하락/자금 조달 실패(Strong:파산/구조조정)
  Affected memory: HBM, Conv. DRAM

V28: 추론 인프라 투자 [Weight:6 | Next-Investment | MD1]
  Bullish: 추론 전용 인프라 구축(Strong:전용 DC), 추론 칩 대량 배치(Strong:만대+)
  Efficiency frame: 추론 비용 인하 → 채택속도 vs 효율화속도 비교로 방향 판정
  Affected memory: Conv. DRAM, NAND
""",

    # ========== TIER 2: 모델/기술 트렌드 기반 단위당 메모리 계수 ==========

    "D1": """
V29: 데이터/ML 인프라 활용 규모 [Weight:4 | Investment | MD3]
  Bullish: 데이터 플랫폼 매출/처리량 급증(Strong:+50%+), 모델 허브 다운로드 급증(Strong:월10B+)
  Bullish: Vector DB 고객/규모 성장(Strong:+100%+ YoY), 학습 데이터 기업 대형 계약(Strong:$1B+)
  Bullish: RAG 프레임워크 채택 급증(Strong:월 다운로드+200%+)
  Affected memory: Conv. DRAM, HBM (간접)
""",

    "D2": """
V29: 데이터/ML 인프라 활용 규모 [Weight:4 | Investment | MD3]
  Bullish: Vector DB 매출/고객 성장(Strong:+100%+ YoY), 임베딩 인덱스 규모(Strong:1B+ 벡터)
  Affected memory: Conv. DRAM
""",

    "D3": """
V29: 데이터/ML 인프라 활용 규모 [Weight:4 | Investment | MD3]
  Bullish: 데이터 라벨링 기업 대형 계약(Strong:$1B+), 합성 데이터 주요 LLM 기업 채택(Strong)
  Affected memory: HBM (간접: 데이터→학습 규모→GPU/HBM)
""",

    "D4": """
V29: 데이터/ML 인프라 활용 규모 [Weight:4 | Investment | MD3]
  Bullish: RAG 프레임워크 채택 급증(Strong:월 다운로드+200%+), 엔터프라이즈 RAG 도입 사례
  Affected memory: Conv. DRAM, NAND (RAG→컨텍스트 확대→KV Cache 증가)
""",

    "E1": """
V34: 모델 스케일링 트렌드 [Weight:9 | Current-Investment | MD3]
  Bullish: 차세대 모델 파라미터 규모 증가(Strong:이전 5x+, Mod:2-5x)
  Bullish: 컨텍스트 윈도우 확장(Strong:1M+ 토큰, Mod:200K-1M)
  Bullish: 학습 클러스터 규모 공개(Strong:100K+ GPU), 학습 비용 공개(Strong:$100M+)
  Affected memory: HBM, Conv. DRAM, NAND

V35: 모델 효율화/경량화 트렌드 [Weight:8 | Current-Investment | MD3]
  ** EFFICIENCY FRAME 필수 적용 **
  양자화/압축 기술 상용화, KV Cache 압축/offloading, MoE 등 아키텍처 변화 이벤트에 적용:
  - 효율화 메모리 절감률 vs 서비스 채택(사용자/처리량) 성장률 비교
  - 채택속도 > 효율화속도 → Bullish (총 수요 증가)
  - 효율화속도 > 채택속도 → Bearish (caveat: "채택 가속 시 반전 가능")
  - 판단 불가 → Bullish (caveat: "효율화 영향 모니터링 필요")
  Affected memory: HBM, Conv. DRAM

V36: 오픈소스/소버린 AI 확산 [Weight:5 | Investment | MD3]
  Bullish: 주요 오픈소스 모델 출시(Strong:70B+, Mod:7-70B)
  Bullish: 소버린 AI 국가 프로젝트(Strong:$1B+)
  Affected memory: HBM (학습 복제 수요 분산)

V37: 학습-추론 Compute 비율 변화 [Weight:7 | Investment | MD3]
  Bullish(caveat): 추론 비중 증가 발언/데이터(Strong:정량 데이터 공개)
  Bullish: Test-time compute 확대(Strong:주류 서비스 적용)
  caveat(추론 비중): "HBM 대비 서버 DRAM 수요 비중 증가. HBM 총량이 줄지는 않으나 DRAM 성장 가속이 핵심"
  Affected memory: Conv. DRAM, NAND
""",

    "E2": """
V38: 생성형 AI 서비스 확산 [Weight:5 | Next-Investment | MD4]
  Bullish: 생성형 AI MAU/생성 건수(Strong:MAU 100M+), 비디오 생성 상용화(Strong:유료 매출 급증)
  Bullish: 실시간 멀티모달 서비스(Strong:4K 비디오+음성)
  Affected memory: HBM, Conv. DRAM (비디오=텍스트 대비 10x+ compute)
""",

    "E3": """
V38: 생성형 AI 서비스 확산 [Weight:5 | Next-Investment | MD4]
  Bullish: 음성 AI ARR $100M+ 또는 YoY+200%+(Strong), TTS/STT API 호출 월1B+(Strong)
  Bullish: Voice Agent 대규모 배치(Strong:100+ 엔터프라이즈)
  Affected memory: Conv. DRAM (실시간 추론 → 고대역 DRAM)
""",

    "F1": """
V42: 코딩/에이전트 AI 활용 확산 [Weight:6 | Next-Investment | MD4]
  Bullish: 코딩 AI DAU 1M+ 또는 ARR $500M+(Strong)
  Bullish: 코드 특화 모델 학습 투자(Strong:$500M+, Mod:$100-500M)
  Affected memory: Conv. DRAM (추론 API 호출), HBM (전용 학습)
""",

    "F2": """
V42: 코딩/에이전트 AI 활용 확산 [Weight:6 | Next-Investment | MD4]
  Bullish: Agent 플랫폼 ARR $100M+(Strong), Agent 호출 체인 복잡도 증가(Strong:10+ LLM 호출/태스크)
  Bullish: Agent 인프라 자금 조달(Strong:$100M+)
  Affected memory: Conv. DRAM (다중 LLM 호출 → 추론 승수 효과)
""",

    # ========== TIER 3: 실제 활용 기반 수요 실현 검증 ==========

    "G1": """
VG_SaaS: Enterprise SaaS AI 추론 수요 [Weight:4 | Investment-Strategic | MD4]
  G1(Enterprise AI)+G2(Conversational)+G3(Productivity)+G4(Search)+H2+H3+H6+H7+H8+H9 통합
  Bullish: 대형 Enterprise AI 계약(Strong:ACV $100M+), AI SaaS 도입률(Strong:Fortune500 50%+)
  Bullish: AI 검색 MAU 100M+ 또는 기존 대비 30%+ 비중(Strong)
  Bearish: AI SaaS 도입 정체/이탈 보도(Strong:다수 기업 이탈)
  Affected memory: Conv. DRAM
""",
    "G2": """
VG_SaaS: Enterprise SaaS AI 추론 수요 [Weight:4 | Investment-Strategic | MD4]
  Bullish: 컨택센터 AI 글로벌 기업 전면 전환(Strong), 시장 성장 +30%+(Strong)
  Affected memory: Conv. DRAM
""",
    "G3": """
VG_SaaS: Enterprise SaaS AI 추론 수요 [Weight:4 | Investment-Strategic | MD4]
  Bullish: 프로덕티비티 AI MAU 100M+(Strong)
  Affected memory: Conv. DRAM
""",
    "G4": """
VG_SaaS: Enterprise SaaS AI 추론 수요 [Weight:4 | Investment-Strategic | MD4]
  Bullish: AI 검색 MAU 100M+(Strong), 기존 검색 대비 30%+ 비중(Strong)
  Affected memory: Conv. DRAM (검색당 추론 compute 10x)
""",
    "G5": """
VG_IndDef: 산업/국방 AI 수요 [Weight:5 | Investment-Strategic | MD4]
  G5(Industrial)+H4(Defense)+H5(SupplyChain) 통합
  Bullish: 글로벌 제조사 AI 전면 도입(Strong), Digital Twin 플랫폼 매출+50%+(Mod)
  Bullish: 국방 AI 대형 계약(Strong:$1B+), 소버린 AI 국방 인프라
  Affected memory: Conv. DRAM, NAND
""",

    "H1": """
V52: Healthcare/Bio AI 수요 [Weight:4 | Strategic | MD4]
  Bullish: AI 신약 Phase 3+ 다수 진입(Strong), Bio AI 대규모 컴퓨트 투자(Strong:자체 GPU 클러스터)
  Bullish: 의료 AI 기기 월10건+ 승인(Mod)
  Affected memory: HBM (분자 시뮬레이션), Conv. DRAM (Edge 추론)
""",
    "H2": """
VG_SaaS: Enterprise SaaS AI 추론 수요 [Weight:4 | Investment-Strategic | MD4]
  Bullish: 법률 AI Top100 로펌 50%+ 도입(Strong)
  Affected memory: Conv. DRAM
""",
    "H3": """
VG_SaaS: Enterprise SaaS AI 추론 수요 [Weight:4 | Investment-Strategic | MD4]
  Bullish: 금융 AI 실시간 처리 10B+건(Strong), on-prem 추론 서버 투자
  Affected memory: Conv. DRAM
""",
    "H4": """
VG_IndDef: 산업/국방 AI 수요 [Weight:5 | Investment-Strategic | MD4]
  Bullish: 국방 AI 대형 계약(Strong:$1B+), 자율 무기 체계 배치
  Affected memory: Conv. DRAM, NAND
""",
    "H5": """
VG_IndDef: 산업/국방 AI 수요 [Weight:5 | Investment-Strategic | MD4]
  Bullish: Fortune500 공급망 AI 30%+ 도입(Strong)
  Affected memory: Conv. DRAM
""",
    "H6": "VG_SaaS: Enterprise SaaS AI. Bullish: Marketing/Sales AI ARR +50%+. Affected: Conv. DRAM",
    "H7": "VG_SaaS: Enterprise SaaS AI. Bullish: HR AI 대기업 200+ 도입. Affected: Conv. DRAM",
    "H8": "VG_SaaS: Enterprise SaaS AI. Bullish: 기후 AI 주요국 규제 의무화. Affected: Conv. DRAM",
    "H9": "VG_SaaS: Enterprise SaaS AI. Bullish: 교육 AI 사용자 100M+. Affected: Conv. DRAM",

    "H10": """
V62: AV/Robotics 수요 [Weight:6 | Investment-Strategic | MD5]
  H10(AV)+J1(Robotics) 통합
  Bullish: AV 학습 인프라 투자(Strong:10K+ GPU), Robotaxi/AV 트럭 10K대+ 배치(Strong)
  Bullish: 차량당 LPDDR5X 32GB+ 스펙(Strong), 산업 로봇 출하 YoY+30%+(Strong)
  Bullish: 로봇 Foundation Model 자금 조달(Strong:$500M+), 휴머노이드 1,000대+ 양산(Strong)
  Affected memory: Conv. DRAM, NAND, HBM (로봇 학습)
""",
    "H11": """
VG_IndDef: 산업/국방 AI 수요 [Weight:5 | Investment-Strategic | MD4]
  Bullish: 위성 AI 이미지 분석 처리량+100%+(Strong)
  Affected memory: Conv. DRAM
""",

    "I1": """
V65: AI 보안/규제 환경 변화 [Weight:3 | Investment | MD4]
  Bullish: AI 보안 솔루션 매출+50%+(Strong)
  Bearish(caveat): AI 규제 강화(EU AI Act 등, Strong:주요국 시행)
  Bearish(caveat): AI 보안 사고(Strong:대형 사고)
  caveat(규제): "단기 도입 지연, On-prem 전환 시 기업 전용 서버 수요 증가"
  caveat(보안 사고): "단기 도입 주저, 중기 보안 인프라 투자 확대 가능"
  Affected memory: Conv. DRAM
""",
    "I2": """
V65: AI 보안/규제 환경 변화 [Weight:3 | Investment | MD4]
  Bearish(caveat): AI 거버넌스 규제 강화 → On-prem 전환 수요
  caveat: "단기 도입 지연이나, On-prem 전환 시 기업 전용 서버 수요 증가. AI 지출 자체는 줄지 않을 전망"
  Affected memory: Conv. DRAM
""",
    "I3": """
V68: Edge AI 인프라 확산 [Weight:3 | Strategic | MD5]
  Bullish: GPU 활용률 최적화 → 동일 GPU 대비 더 많은 워크로드 → 메모리 가동률 상승
  Affected memory: Conv. DRAM
""",
    "I4": """
V68: Edge AI 인프라 확산 [Weight:3 | Strategic | MD5]
  Bullish: Edge AI 프로세서 100만대+ 출하(Strong)
  Affected memory: Conv. DRAM, NAND
""",

    "J1": """
V62: AV/Robotics 수요 [Weight:6 | Investment-Strategic | MD5]
  Bullish: 산업/서비스 로봇 출하 YoY+30%+(Strong), 물류 로봇 10K대+ 배치(Strong)
  Bullish: 로봇 Foundation Model 자금 조달(Strong:$500M+), 월드 모델 전용 클러스터 구축
  Bullish: 휴머노이드 1,000대+ 양산 확정(Strong), 대규모 자금 조달(Strong:$1B+)
  Affected memory: Conv. DRAM, NAND, HBM (비디오+물리 시뮬레이션)
""",
}

# ============================================================
# DRIVER MAPPING - 각 변수가 속한 Memory Demand Driver
# ============================================================

VARIABLE_DRIVER_MAP = {
    "V01": "MD1", "V02": "MD1", "V03": "MD1", "V04": "MD1",
    "V08": "MD2", "V09": "MD2", "V10": "MD2",
    "V11": "MD2", "V12": "MD2", "V13": "MD5", "V14": "MD3",
    "V15": "MD2", "V16": "MD3",
    "V18": "MD2",
    "V20": "MD1", "V21": "MD1", "V22": "MD2", "V23": "MD2",
    "V24": "MD1",
    "V26": "MD1", "V27": "MD1", "V28": "MD1",
    "V29": "MD3",
    "V34": "MD3", "V35": "MD3", "V36": "MD3", "V37": "MD3",
    "V38": "MD4", "V42": "MD4",
    "VG_SaaS": "MD4", "VG_IndDef": "MD4",
    "V52": "MD4", "V62": "MD5",
    "V65": "MD4", "V68": "MD5",
}

DRIVER_NAMES = {
    "MD1": "AI Infra 투자 강도",
    "MD2": "반도체 공급 역량",
    "MD3": "모델/기술의 메모리 계수 변화",
    "MD4": "AI 서비스 추론 수요 실현",
    "MD5": "Edge/디바이스 메모리 수요",
}

# ============================================================
# DIVERGENCE ALERT RULES
# ============================================================

# ============================================================
# VARIABLE WEIGHTS - design_v2_consolidated.md 기준 Memory Impact Weight (1-10)
# get_drivers() 집계 공식에서 사용: Σ(방향×강도×Confidence×Weight) / Σ Weight
# ============================================================

VARIABLE_WEIGHTS = {
    # Tier 1 - A/B/C
    "V01": 5,  "V02": 4,  "V03": 4,  "V04": 6,
    "V08": 8,  "V09": 5,  "V10": 3,
    "V11": 10, "V12": 7,  "V13": 5,  "V14": 4,
    "V15": 6,  "V16": 5,
    "V18": 5,
    "V20": 10, "V21": 8,  "V22": 9,  "V23": 4,
    "V24": 6,
    "V26": 10, "V27": 7,  "V28": 6,
    # Tier 2 - D/E/F
    "V29": 4,
    "V34": 9,  "V35": 8,  "V36": 5,  "V37": 7,
    "V38": 5,
    "V42": 6,
    # Tier 3 - G/H/I/J (통합 변수)
    "VG_SaaS": 4,  "VG_IndDef": 5,
    "V52": 4,
    "V62": 6,
    "V65": 3,  "V68": 3,
}

DIVERGENCE_ALERT_RULES = [
    {
        "id": "DA1",
        "name": "투자-실현 괴리 (Overinvestment Risk)",
        "condition": "MD1 Bullish + MD4 Bearish, 2주 이상",
        "message": "인프라 투자 대비 추론 수요 실현이 지연되고 있음. 수요 실현 추이 주시 필요",
    },
    {
        "id": "DA2",
        "name": "공급 병목 (Supply Bottleneck)",
        "condition": "MD4 Bullish + MD2 Bearish, 2주 이상",
        "message": "수요 강세 대비 공급 제약 감지. 단기 가격 상승 및 할당 우선순위 검토 필요",
    },
    {
        "id": "DA3",
        "name": "효율화 가속 (Efficiency Acceleration)",
        "condition": "V35 Bearish 3건 이상 + MD4 Bullish 강도 약화",
        "message": "모델 효율화 기술의 상용화 가속. 단위당 메모리 소비 변화 추이 주시 필요",
    },
    {
        "id": "DA4",
        "name": "Tier 전면 동조 하락 (Cycle Downturn Signal)",
        "condition": "MD1 + MD2 + MD4 모두 Bearish, 1주 이상",
        "message": "전 계층 하향 시그널 감지. 사이클 전환 가능성 검토 필요",
    },
    {
        "id": "DA5",
        "name": "Tier 전면 동조 상승 (Cycle Upturn Confirmation)",
        "condition": "MD1 + MD4 + MD5 모두 Bullish, 2주 이상",
        "message": "전 계층 상승 시그널. 수요 확장 사이클 확인",
    },
]
