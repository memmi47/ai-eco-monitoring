import os
import sys
import json
import logging
import sqlite3
import threading
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import litellm

logger = logging.getLogger("main")

load_dotenv()

# ============================================================
# PATH & CONFIG
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'database'))

try:
    import importlib.util as _ilu
    _seed_spec = _ilu.spec_from_file_location(
        "seed_db",
        os.path.join(BASE_DIR, "database", "seed_db.py")
    )
    seed_db = _ilu.module_from_spec(_seed_spec)
    _seed_spec.loader.exec_module(seed_db)
except Exception:
    seed_db = None

try:
    from variable_definitions import (
        VARIABLE_DEFINITIONS, TIER_CONTEXTS,
        _get_tier, extract_category_key,
        VARIABLE_DRIVER_MAP, DRIVER_NAMES, DIVERGENCE_ALERT_RULES,
        VARIABLE_WEIGHTS
    )
except ImportError:
    VARIABLE_DEFINITIONS = {}
    TIER_CONTEXTS = {}
    VARIABLE_DRIVER_MAP = {}
    DRIVER_NAMES = {}
    DIVERGENCE_ALERT_RULES = []
    VARIABLE_WEIGHTS = {}
    def _get_tier(layer): return "tier3"
    def extract_category_key(cat): return "XX"

DEFAULT_DB_PATH = os.path.join(BASE_DIR, "database", "ai_eco_monitor.db")
db_url = os.environ.get("DATABASE_URL", DEFAULT_DB_PATH)
_IS_PG = db_url.startswith(("postgresql://", "postgres://"))
MODEL_FREE = "openrouter/google/gemma-2-9b-it:free"
MODEL_PAID = "openrouter/google/gemini-flash-1.5"

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(title="AI Eco Monitor API v2")

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "AI Eco Monitor Backend", "version": "2.0"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# STARTUP
# ============================================================

_scheduler = None

@app.on_event("startup")
def startup_event():
    global _scheduler

    # ---- DB 초기화 (SQLite / PostgreSQL 공통) ----
    if _IS_PG:
        print(f"Connecting to PostgreSQL: {db_url.split('@')[-1]}")
        # PostgreSQL: 테이블 존재 여부 확인 후 시딩
        try:
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_name = 'companies'"
            )
            table_exists = cursor.fetchone()
            if not table_exists:
                print("Initializing DB schema & seeding...")
                if seed_db:
                    seed_db.main()
            else:
                cursor.execute("SELECT COUNT(*) as cnt FROM companies")
                row = cursor.fetchone()
                cnt = row.get("cnt", 0) if row else 0
                if cnt == 0:
                    print("Seeding companies table...")
                    if seed_db:
                        seed_db.main()
                else:
                    print(f"DB ready: {cnt} companies loaded")
            conn.close()
        except Exception as e:
            print(f"PostgreSQL 초기화 오류: {e}")
    else:
        # SQLite: 기존 로직 유지
        db_dir = os.path.dirname(db_url)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
        if not cursor.fetchone():
            print("Initializing DB...")
            if seed_db:
                seed_db.main()
        else:
            cursor.execute("SELECT COUNT(*) FROM companies")
            if cursor.fetchone()[0] == 0:
                if seed_db:
                    seed_db.main()
        conn.close()

    # ---- 뉴스 수집 스케줄러 시작 (SQLite/PostgreSQL 공통) ----
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from collector import run_collection_job

        db_path_for_collector = db_url  # PostgreSQL이면 URL 그대로, SQLite면 파일 경로
        _scheduler = BackgroundScheduler(timezone="UTC")
        # T1 핵심기업: 6시간마다
        _scheduler.add_job(
            run_collection_job, "interval", hours=6,
            args=[db_path_for_collector, "T1"],
            id="news_collector_t1", replace_existing=True,
        )
        # 전체 기업: 24시간마다
        _scheduler.add_job(
            run_collection_job, "interval", hours=24,
            args=[db_path_for_collector, None],
            id="news_collector_all", replace_existing=True,
        )
        _scheduler.start()
        logger.info("뉴스 수집 스케줄러 시작 (T1: 6h, 전체: 24h)")
    except ImportError as e:
        logger.warning(f"스케줄러 초기화 실패 (의존성 확인 필요): {e}")


@app.on_event("shutdown")
def shutdown_event():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("스케줄러 종료")

# ============================================================
# DB HELPER
# ============================================================

def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


class _PGCursorAdapter:
    """psycopg2 커서를 sqlite3 호환 인터페이스로 래핑.
    - ? → %s 플레이스홀더 자동 변환
    - INSERT 시 RETURNING id로 lastrowid 에뮬레이션
    """
    def __init__(self, cursor):
        self._cur = cursor
        self.lastrowid = None
        self.description = None

    @staticmethod
    def _to_pg_sql(query: str) -> str:
        """SQLite 전용 SQL 구문을 PostgreSQL 호환으로 변환."""
        import re
        q = query.replace("?", "%s")
        # datetime('now', '-30 days') → NOW() - INTERVAL '30 days'
        q = re.sub(
            r"datetime\('now',\s*'-(\d+)\s*days'\)",
            r"NOW() - INTERVAL '\1 days'",
            q,
        )
        # date('now', %s || ' days') → CURRENT_DATE + (%s * INTERVAL '1 day')
        q = re.sub(
            r"date\('now',\s*%s\s*\|\|\s*'[^']*days[^']*'\)",
            r"CURRENT_DATE + (%s * INTERVAL '1 day')",
            q,
        )
        # date('now') → CURRENT_DATE
        q = re.sub(r"date\('now'\)", "CURRENT_DATE", q)
        # sqlite_master → information_schema.tables (스타트업 체크용)
        q = q.replace("sqlite_master", "information_schema.tables")
        return q

    def execute(self, query: str, params=None):
        pg_query = self._to_pg_sql(query)
        is_insert = pg_query.strip().upper().startswith("INSERT")
        if is_insert and "RETURNING" not in pg_query.upper():
            pg_query = pg_query.rstrip(";").rstrip() + " RETURNING id"
        self._cur.execute(pg_query, params or ())
        self.description = self._cur.description
        if is_insert:
            row = self._cur.fetchone()
            self.lastrowid = row["id"] if row else None

    def fetchone(self):
        row = self._cur.fetchone()
        return dict(row) if row else None

    def fetchall(self):
        return [dict(r) for r in self._cur.fetchall()]

    @property
    def rowcount(self):
        return self._cur.rowcount


class _PGConnAdapter:
    """psycopg2 연결을 sqlite3 호환 인터페이스로 래핑"""
    def __init__(self):
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            raise RuntimeError(
                "psycopg2가 설치되지 않았습니다. pip install psycopg2-binary"
            )
        self._conn = psycopg2.connect(db_url)
        self._RDC = psycopg2.extras.RealDictCursor

    def cursor(self):
        return _PGCursorAdapter(self._conn.cursor(cursor_factory=self._RDC))

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def get_conn():
    if _IS_PG:
        return _PGConnAdapter()
    conn = sqlite3.connect(db_url)
    conn.row_factory = dict_factory
    return conn

# ============================================================
# PROMPTS v2
# ============================================================

STAGE1_SYSTEM = """You are a structured fact extractor for the AI and semiconductor industry.

Your task:
1. Extract structured facts from the news article
2. Determine if this news has ANY relevance to AI infrastructure, AI models, AI applications, or the semiconductor supply chain
3. Identify which company and industry category this relates to

IMPORTANT: Be inclusive. Even indirect relevance should pass. Only filter out completely unrelated news (sports, entertainment, unrelated politics).

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
    "company_name": "matched company or null",
    "category": "best matching Category (e.g. C2.Hyperscaler, B5.Server)",
    "tier": "tier1|tier2|tier3"
  },
  "is_quantitative": true/false
}"""

STAGE2_SYSTEM = """You are a memory semiconductor demand signal analyst.

Given the extracted facts from a news article, your task is:
1. Map this event to the most relevant measurement variable for this category
2. Determine the signal direction (ONLY bullish or bearish — never structural)
3. Add a caveat field if the direction has important counterarguments
4. Identify which memory products are affected (HBM / Conv. DRAM / NAND)

CATEGORY: {category}
TIER: {tier}

MEASUREMENT VARIABLES FOR THIS CATEGORY:
{variable_definitions}

SIGNAL RULES:
- Direction: ONLY "bullish" (memory demand increases) or "bearish" (demand decreases)
- If previously classified as "structural", choose the primary direction and add caveat
- Strength: "strong" (official disclosure, quantitative), "moderate" (credible report), "weak" (rumor)
- Confidence: "high" (company filing/official), "medium" (credible media), "low" (rumor/estimation)
- Affected memory: subset of ["HBM", "Conv. DRAM", "NAND"]
- needs_review: true if direction is genuinely ambiguous and requires human analyst review

Respond in JSON only. No markdown, no explanation.

{{
  "variable_id": "the variable ID (e.g. V26)",
  "variable_name": "human-readable variable name",
  "direction": "bullish|bearish",
  "caveat": "null or one sentence counterargument",
  "needs_review": false,
  "strength": "strong|moderate|weak",
  "confidence": "high|medium|low",
  "affected_memory": ["HBM", "Conv. DRAM"],
  "reasoning": "one sentence: why this direction and strength"
}}"""

STAGE3_SYSTEM = """You are a senior memory semiconductor demand strategist at a major memory company.

Given the structured facts and signal classification from previous stages, provide:
1. The specific transmission path from this event to memory semiconductor demand (A → B → C chain)
2. The demand impact on each memory product (HBM, Conv. DRAM, NAND)
3. The time lag before demand impact materializes
4. A concise executive summary in Korean (2-3 sentences)

CONTEXT:
- Memory demand = Tier1 (infra volume) × Tier2 (per-unit memory coefficient) × Tier3 (utilization rate)
- For efficiency events: compare efficiency speed vs adoption speed
  * If adoption speed > efficiency speed → bullish (total demand still grows)
  * If efficiency speed > adoption speed → bearish (add caveat: "채택 가속 시 반전 가능")
  * If unclear → bullish with caveat "효율화 영향 모니터링 필요"
- Do NOT say "Jevons Paradox" blindly — apply the speed comparison frame above

TIER CONTEXT:
{tier_context}

Respond in JSON only. No markdown, no explanation.

{{
  "transmission_path": "Specific A→B→C chain. Example: 'MS capex +19% → GPU server orders increase → HBM demand +15-20% in 6-9M'",
  "memory_impact": {{
    "HBM": {{"direction": "bullish|bearish|neutral", "magnitude": "high|medium|low|none", "detail": "specific impact"}},
    "Conv. DRAM": {{"direction": "...", "magnitude": "...", "detail": "..."}},
    "NAND": {{"direction": "...", "magnitude": "...", "detail": "..."}}
  }},
  "time_lag": "immediate|short_3-6m|mid_6-12m|long_12m+",
  "demand_formula_tier": "tier1|tier2|tier3",
  "demand_formula_role": "Which part of the formula: volume (tier1), per-unit coefficient (tier2), or utilization rate (tier3)",
  "decision_relevance": "current_quarter|next_quarter|investment_plan|strategic_reference",
  "counterargument": "What could make this signal wrong? One sentence.",
  "executive_summary": "2-3 sentences in Korean for C-level. State event, memory demand impact, confidence level."
}}"""

# ============================================================
# LLM HELPER
# ============================================================

def _call_llm(model: str, system_prompt: str, user_content: str) -> dict:
    """LLM 호출 + JSON 파싱. 실패 시 에러 dict 반환."""
    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        raw = response.choices[0].message.content.strip()
        # JSON 블록 추출
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        return {"_error": str(e)}

# ============================================================
# EXISTING v1 ENDPOINTS (하위 호환)
# ============================================================

@app.get("/api/companies")
def get_companies(layer: str = None, tier: str = None, q: str = None):
    query = "SELECT * FROM companies WHERE 1=1"
    params = []
    if layer:
        query += " AND layer = ?"; params.append(layer)
    if tier:
        query += " AND tier = ?"; params.append(tier)
    if q:
        query += " AND company_name LIKE ?"; params.append(f"%{q}%")
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()
    return data

@app.get("/api/companies/{company_id}")
def get_company(company_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
    data = cursor.fetchone()
    conn.close()
    if not data:
        raise HTTPException(status_code=404, detail="Company not found")
    return data

@app.get("/api/stats")
def get_stats():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM companies")
    total = cursor.fetchone()['total']
    cursor.execute("SELECT tier, COUNT(*) as count FROM companies GROUP BY tier")
    tiers = {row['tier'] if row['tier'] else 'other': row['count'] for row in cursor.fetchall()}
    conn.close()
    return {
        "total_companies": total,
        "tier1": tiers.get('T1', 0),
        "tier2": tiers.get('T2', 0),
        "tier3": tiers.get('T3', 0)
    }

@app.get("/api/taxonomy")
def get_taxonomy():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT layer FROM companies WHERE layer IS NOT NULL ORDER BY layer")
    layers = [row['layer'] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT category FROM companies WHERE category IS NOT NULL ORDER BY category")
    categories = [row['category'] for row in cursor.fetchall()]
    conn.close()
    return {"layers": layers, "categories": categories}

@app.get("/api/feed")
def get_feed():
    return []

@app.get("/api/activity")
def get_activity():
    return []

# ============================================================
# COLLECTOR ENDPOINTS
# ============================================================

class CollectRequest(BaseModel):
    tier_filter: Optional[str] = None  # "T1" | "T2" | "T3" | None (전체)

@app.post("/api/collect")
def manual_collect(req: CollectRequest = CollectRequest()):
    """수동 뉴스 수집 트리거 (백그라운드 실행)."""
    try:
        from collector import run_collection_job
    except ImportError:
        raise HTTPException(status_code=500, detail="collector 모듈을 로드할 수 없습니다. requirements.txt를 확인하세요.")

    t = threading.Thread(
        target=run_collection_job,
        args=[DEFAULT_DB_PATH, req.tier_filter],
        daemon=True,
    )
    t.start()
    label = req.tier_filter or "전체"
    return {"status": "started", "message": f"뉴스 수집 작업 시작됨 (대상: {label} 기업)"}

# ============================================================
# v2 ENDPOINTS
# ============================================================

class AnalyzeV2Request(BaseModel):
    company_id: int
    title: str
    snippet: str

@app.post("/api/analyze/v2")
def analyze_v2(req: AnalyzeV2Request):
    """Pipeline v2: 사실추출 → 변수매핑 → 메모리전이경로 분석"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM companies WHERE id = ?", (req.company_id,))
    company = cursor.fetchone()
    conn.close()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    category = company.get('category') or ''
    cat_key = company.get('category_key') or extract_category_key(category)
    layer = company.get('layer') or ''
    tier = _get_tier(layer)

    # ---- Stage 1: 사실 추출 ----
    s1_input = f"Company: {company.get('company_name')} | Category: {category}\n\nTitle: {req.title}\nContent: {req.snippet}"
    s1 = _call_llm(MODEL_FREE, STAGE1_SYSTEM, s1_input)

    if s1.get("_error"):
        # Mock fallback
        s1 = {
            "relevant": True,
            "facts": {"who": company.get('company_name'), "what": req.title, "how": "N/A", "when": "Recent", "source_type": "news"},
            "company_match": {"company_name": company.get('company_name'), "category": category, "tier": tier},
            "is_quantitative": False,
            "_mock": True
        }

    if not s1.get("relevant", True):
        return {"pipeline_version": 2, "stage1_relevant": False, "skipped": True, "company": company.get('company_name')}

    # ---- Stage 2: 변수 매핑 ----
    var_defs = VARIABLE_DEFINITIONS.get(cat_key, f"Category: {category}. Use general assessment for memory semiconductor demand impact.")
    s2_system = STAGE2_SYSTEM.format(
        category=category,
        tier=tier,
        variable_definitions=var_defs
    )
    s2_input = json.dumps(s1.get("facts", {}))
    s2 = _call_llm(MODEL_FREE, s2_system, s2_input)

    if s2.get("_error"):
        s2 = {
            "variable_id": "V26" if "capex" in req.title.lower() else "V20",
            "variable_name": "General Signal",
            "direction": "bullish",
            "caveat": None,
            "needs_review": True,
            "strength": "moderate",
            "confidence": "medium",
            "affected_memory": ["HBM", "Conv. DRAM"],
            "reasoning": f"Mock analysis for {req.title}",
            "_mock": True
        }

    # ---- Stage 3: 전이 경로 분석 ----
    tier_ctx = TIER_CONTEXTS.get(tier, TIER_CONTEXTS.get("tier3", ""))
    s3_system = STAGE3_SYSTEM.format(tier_context=tier_ctx)
    s3_input = json.dumps({"facts": s1.get("facts", {}), "signal": s2})
    s3 = _call_llm(MODEL_PAID, s3_system, s3_input)

    if s3.get("_error"):
        s3 = {
            "transmission_path": f"{company.get('company_name')} 관련 이벤트 → 메모리 수요 변화 (Mock)",
            "memory_impact": {
                "HBM": {"direction": s2.get("direction","bullish"), "magnitude": "medium", "detail": "Mock analysis"},
                "Conv. DRAM": {"direction": s2.get("direction","bullish"), "magnitude": "low", "detail": "Mock"},
                "NAND": {"direction": "neutral", "magnitude": "none", "detail": "Mock"}
            },
            "time_lag": "mid_6-12m",
            "demand_formula_tier": tier,
            "demand_formula_role": "Mock role",
            "decision_relevance": "investment_plan",
            "counterargument": "Mock counterargument",
            "executive_summary": f"[Mock] {req.title} 관련 분석입니다. API 키를 Railway에 등록하면 실제 분석이 작동합니다.",
            "_mock": True
        }

    # ---- DB 저장 ----
    result = {
        "pipeline_version": 2,
        "company": company.get('company_name'),
        "category": category,
        "category_key": cat_key,
        "tier": tier,
        "stage1": s1,
        "stage2": s2,
        "stage3": s3,
    }

    try:
        conn2 = get_conn()
        cur2 = conn2.cursor()
        cur2.execute("""
            INSERT INTO analysis_results (
                company_id, stage1_relevant, stage1_facts,
                stage2_variable_id, stage2_variable_name,
                stage2_direction, stage2_caveat, stage2_needs_review,
                stage2_strength, stage2_confidence, stage2_affected_memory,
                stage2_reasoning,
                stage3_transmission_path, stage3_memory_impact,
                stage3_time_lag, stage3_demand_formula_tier,
                stage3_demand_formula_role, stage3_decision_relevance,
                stage3_counterargument, stage3_executive_summary,
                pipeline_version
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            req.company_id,
            1 if s1.get("relevant") else 0,
            json.dumps(s1.get("facts", {})),
            s2.get("variable_id"),
            s2.get("variable_name"),
            s2.get("direction"),
            s2.get("caveat"),
            1 if s2.get("needs_review") else 0,
            s2.get("strength"),
            s2.get("confidence"),
            json.dumps(s2.get("affected_memory", [])),
            s2.get("reasoning"),
            s3.get("transmission_path"),
            json.dumps(s3.get("memory_impact", {})),
            s3.get("time_lag"),
            s3.get("demand_formula_tier"),
            s3.get("demand_formula_role"),
            s3.get("decision_relevance"),
            s3.get("counterargument"),
            s3.get("executive_summary"),
            2
        ))
        conn2.commit()
        result["saved_id"] = cur2.lastrowid
        conn2.close()
    except Exception as e:
        result["db_error"] = str(e)

    return result


@app.get("/api/signals")
def get_signals(
    limit: int = 20,
    direction: str = None,
    tier: str = None,
    variable_id: str = None,
    decision_relevance: str = None,
    exclude_strategic: bool = False,
):
    """v2 분석 결과 시그널 목록 조회.

    decision_relevance: current_quarter|next_quarter|investment_plan|strategic_reference
    exclude_strategic: True이면 strategic_reference 제외 (기본 뷰용)
    """
    query = """
        SELECT ar.*, c.company_name, c.category, c.layer, c.tier as company_tier
        FROM analysis_results ar
        LEFT JOIN companies c ON ar.company_id = c.id
        WHERE ar.pipeline_version = 2 AND ar.stage1_relevant = 1
    """
    params = []
    if direction:
        query += " AND ar.stage2_direction = ?"; params.append(direction)
    if tier:
        query += " AND ar.stage3_demand_formula_tier = ?"; params.append(tier)
    if variable_id:
        query += " AND ar.stage2_variable_id = ?"; params.append(variable_id)
    if decision_relevance:
        query += " AND ar.stage3_decision_relevance = ?"; params.append(decision_relevance)
    if exclude_strategic:
        query += " AND (ar.stage3_decision_relevance IS NULL OR ar.stage3_decision_relevance != 'strategic_reference')"
    query += " ORDER BY ar.analyzed_at DESC LIMIT ?"
    params.append(limit)

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    # JSON 필드 파싱
    for row in rows:
        for field in ['stage1_facts', 'stage2_affected_memory', 'stage3_memory_impact']:
            if row.get(field) and isinstance(row[field], str):
                try:
                    row[field] = json.loads(row[field])
                except:
                    pass
    return rows


@app.get("/api/drivers")
def get_drivers():
    """5개 Memory Demand Driver 집계 점수 계산"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT stage2_variable_id, stage2_direction, stage2_strength, stage2_confidence
        FROM analysis_results
        WHERE pipeline_version = 2 AND stage1_relevant = 1
        AND analyzed_at > datetime('now', '-30 days')
    """)
    rows = cursor.fetchall()
    conn.close()

    strength_map = {"strong": 3, "moderate": 2, "weak": 1}
    confidence_map = {"high": 1.0, "medium": 0.7, "low": 0.4}

    # design_v2 집계 공식: Σ(방향 × 강도 × Confidence × Weight) / Σ Weight
    driver_scores = {k: {"score": 0, "weight_sum": 0, "count": 0, "bullish": 0, "bearish": 0} for k in ["MD1","MD2","MD3","MD4","MD5"]}

    for row in rows:
        vid = row.get('stage2_variable_id') or ''
        driver = VARIABLE_DRIVER_MAP.get(vid)
        if not driver or driver not in driver_scores:
            continue
        direction = row.get('stage2_direction', 'bullish')
        strength = strength_map.get(row.get('stage2_strength', 'moderate'), 2)
        confidence = confidence_map.get(row.get('stage2_confidence', 'medium'), 0.7)
        weight = VARIABLE_WEIGHTS.get(vid, 1)
        sign = 1 if direction == 'bullish' else -1
        driver_scores[driver]["score"] += strength * confidence * weight * sign
        driver_scores[driver]["weight_sum"] += weight
        driver_scores[driver]["count"] += 1
        if direction == 'bullish':
            driver_scores[driver]["bullish"] += 1
        else:
            driver_scores[driver]["bearish"] += 1

    result = []
    for driver_id, data in driver_scores.items():
        # 가중 평균 정규화 (weight_sum이 0이면 neutral)
        normalized = data["score"] / data["weight_sum"] if data["weight_sum"] > 0 else 0
        result.append({
            "driver_id": driver_id,
            "driver_name": DRIVER_NAMES.get(driver_id, driver_id),
            "score": round(normalized, 2),
            "count": data["count"],
            "bullish": data["bullish"],
            "bearish": data["bearish"],
            "direction": "bullish" if normalized > 0 else ("bearish" if normalized < 0 else "neutral")
        })
    return result


def _get_da3_signals() -> dict:
    """DA3 판정용: 최근 30일 V35 bearish 카운트 + MD4 평균 strength 조회"""
    conn = get_conn()
    cursor = conn.cursor()
    # V35 bearish 건수
    cursor.execute("""
        SELECT COUNT(*) as cnt
        FROM analysis_results
        WHERE pipeline_version = 2 AND stage1_relevant = 1
        AND stage2_variable_id = 'V35' AND stage2_direction = 'bearish'
        AND analyzed_at > datetime('now', '-30 days')
    """)
    row = cursor.fetchone()
    v35_bearish_count = row['cnt'] if row else 0

    # MD4 소속 변수들의 최근 strength 분포 (MD4 Bullish 강도 약화 판단)
    cursor.execute("""
        SELECT stage2_strength, COUNT(*) as cnt
        FROM analysis_results
        WHERE pipeline_version = 2 AND stage1_relevant = 1
        AND stage2_variable_id IN ('V38','V42','VG_SaaS','VG_IndDef','V52')
        AND stage2_direction = 'bullish'
        AND analyzed_at > datetime('now', '-30 days')
        GROUP BY stage2_strength
    """)
    strength_rows = cursor.fetchall()
    conn.close()

    strength_map = {"strong": 3, "moderate": 2, "weak": 1}
    total_strength = 0
    total_count = 0
    for r in strength_rows:
        s = strength_map.get(r['stage2_strength'], 2)
        c = r['cnt']
        total_strength += s * c
        total_count += c

    avg_strength = total_strength / total_count if total_count > 0 else 0
    # avg_strength < 2.0 (moderate 미만)이면 "강도 약화"로 판단
    md4_weakening = avg_strength < 2.0 and total_count > 0

    return {"v35_bearish_count": v35_bearish_count, "md4_weakening": md4_weakening}


@app.get("/api/divergence-alerts")
def get_divergence_alerts():
    """활성 Divergence Alert 계산 (DA1-DA5 전체)"""
    drivers = get_drivers()
    driver_map = {d["driver_id"]: d for d in drivers}
    da3_data = _get_da3_signals()

    active_alerts = []
    for rule in DIVERGENCE_ALERT_RULES:
        triggered = False
        if rule["id"] == "DA1":
            triggered = (driver_map.get("MD1", {}).get("direction") == "bullish" and
                        driver_map.get("MD4", {}).get("direction") == "bearish")
        elif rule["id"] == "DA2":
            triggered = (driver_map.get("MD4", {}).get("direction") == "bullish" and
                        driver_map.get("MD2", {}).get("direction") == "bearish")
        elif rule["id"] == "DA3":
            # V35 Bearish 3건 이상 + MD4 Bullish 강도 약화
            triggered = (da3_data["v35_bearish_count"] >= 3 and da3_data["md4_weakening"])
        elif rule["id"] == "DA4":
            triggered = all(driver_map.get(d, {}).get("direction") == "bearish"
                          for d in ["MD1", "MD2", "MD4"])
        elif rule["id"] == "DA5":
            triggered = all(driver_map.get(d, {}).get("direction") == "bullish"
                          for d in ["MD1", "MD4", "MD5"])

        if triggered:
            active_alerts.append({**rule, "active": True})

    return {"active_alerts": active_alerts, "total": len(active_alerts)}


@app.get("/api/expected-events")
def get_expected_events(weeks: int = 4):
    """Expected Event Calendar 조회"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ee.*, c.company_name
        FROM expected_events ee
        LEFT JOIN companies c ON ee.company_id = c.id
        WHERE ee.expected_date >= date('now')
        AND ee.expected_date <= date('now', ? || ' days')
        ORDER BY ee.expected_date ASC
    """, (weeks * 7,))
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        if row.get('variable_ids') and isinstance(row['variable_ids'], str):
            try:
                row['variable_ids'] = json.loads(row['variable_ids'])
            except:
                pass
    return rows


class ExpectedEventRequest(BaseModel):
    company_id: int = None
    event_type: str
    expected_date: str
    description: str
    variable_ids: list = []
    source: str = None
    is_confirmed: bool = True

@app.post("/api/expected-events")
def create_expected_event(req: ExpectedEventRequest):
    """Expected Event 수동 등록"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expected_events (company_id, event_type, expected_date, description, variable_ids, source, is_confirmed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        req.company_id, req.event_type, req.expected_date,
        req.description, json.dumps(req.variable_ids),
        req.source, 1 if req.is_confirmed else 0
    ))
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    return {"id": event_id, "message": "Event created"}


# ============================================================
# v1 호환 analyze endpoint (기존 프론트엔드용)
# ============================================================

class AnalyzeRequest(BaseModel):
    news_content: str

@app.post("/api/analyze")
def analyze_news(request: AnalyzeRequest):
    """v1 호환 엔드포인트 (기존 UI용)"""
    content = request.news_content
    try:
        response1 = litellm.completion(
            model=MODEL_FREE,
            messages=[{"role": "user", "content": f"Is this news related to memory semiconductors? Reply 'yes' or 'no' only.\n\n{content}"}]
        )
        is_related = response1.choices[0].message.content.strip().lower()
        if "no" in is_related:
            return {"is_memory_related": False}
        response2 = litellm.completion(
            model=MODEL_FREE,
            messages=[{"role": "user", "content": f"Tag event_type and memory_signal.\n\n{content}"}]
        )
        tagging = response2.choices[0].message.content
        response3 = litellm.completion(
            model=MODEL_PAID,
            messages=[{"role": "user", "content": f"Analyze impact_score(1-10), implications, timeframe. Tags: {tagging}\n\n{content}"}]
        )
        return {"is_memory_related": True, "tagging": tagging, "impact_analysis": response3.choices[0].message.content}
    except Exception as e:
        return {"is_memory_related": True, "tagging": "[Mock]", "impact_analysis": f"[Mock] Error: {str(e)}", "is_mock": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
