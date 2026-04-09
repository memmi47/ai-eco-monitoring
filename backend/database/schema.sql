-- ============================================================
-- AI Eco Monitor - Database Schema (v2)
-- SQLite compatible
-- ============================================================

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seq_no INTEGER,
    layer VARCHAR(255),
    category VARCHAR(255),
    category_key VARCHAR(10),      -- e.g. "A1", "B2" (v2 신규)
    sub_category VARCHAR(255),
    company_name VARCHAR(255),
    biz_type VARCHAR(255),
    listing_status VARCHAR(255),
    hq_region VARCHAR(255),
    company_mission TEXT,
    description TEXT,
    importance VARCHAR(50),
    tier VARCHAR(10)
);

CREATE INDEX IF NOT EXISTS idx_companies_catkey ON companies(category_key);
CREATE INDEX IF NOT EXISTS idx_companies_tier ON companies(tier);

-- ============================================================

CREATE TABLE IF NOT EXISTS crawl_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    title TEXT,
    source_url TEXT,
    published_date TIMESTAMP,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content TEXT
);

-- ============================================================

CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER REFERENCES crawl_history(id),
    company_id INTEGER REFERENCES companies(id),

    -- v1 컬럼 (하위 호환 보존)
    is_memory_related INTEGER,
    event_type VARCHAR(255),
    memory_signal VARCHAR(255),
    impact_score FLOAT,
    implications TEXT,
    timeframe VARCHAR(255),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- v2 Stage 1
    stage1_relevant INTEGER,
    stage1_facts TEXT,             -- JSON: {who, what, how, when, source_type, is_quantitative}

    -- v2 Stage 2: 변수 매핑 + 시그널 판정
    stage2_variable_id TEXT,       -- e.g. "V26"
    stage2_variable_name TEXT,
    stage2_direction TEXT,         -- "bullish" | "bearish"
    stage2_caveat TEXT,            -- null 또는 반론 문자열
    stage2_needs_review INTEGER DEFAULT 0,  -- 1 = 분석가 수동 판정 필요
    stage2_strength TEXT,          -- "strong" | "moderate" | "weak"
    stage2_confidence TEXT,        -- "high" | "medium" | "low"
    stage2_affected_memory TEXT,   -- JSON array: ["HBM","Conv. DRAM","NAND"]
    stage2_reasoning TEXT,

    -- v2 Stage 3: 메모리 전이 경로 분석
    stage3_transmission_path TEXT,
    stage3_memory_impact TEXT,     -- JSON: {HBM:{direction,magnitude,detail}, ...}
    stage3_time_lag TEXT,          -- "immediate"|"short_3-6m"|"mid_6-12m"|"long_12m+"
    stage3_demand_formula_tier TEXT, -- "tier1"|"tier2"|"tier3"
    stage3_demand_formula_role TEXT,
    stage3_decision_relevance TEXT,  -- "current_quarter"|"next_quarter"|"investment_plan"|"strategic_reference"
    stage3_counterargument TEXT,
    stage3_executive_summary TEXT,

    -- 버전 관리
    model_used TEXT,
    pipeline_version INTEGER DEFAULT 1  -- 1=v1, 2=v2
);

CREATE INDEX IF NOT EXISTS idx_analysis_variable ON analysis_results(stage2_variable_id);
CREATE INDEX IF NOT EXISTS idx_analysis_direction ON analysis_results(stage2_direction);
CREATE INDEX IF NOT EXISTS idx_analysis_tier ON analysis_results(stage3_demand_formula_tier);
CREATE INDEX IF NOT EXISTS idx_analysis_version ON analysis_results(pipeline_version);

-- ============================================================

CREATE TABLE IF NOT EXISTS activity_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    calculation_date DATE,
    index_value FLOAT,
    news_count INTEGER,
    avg_impact_score FLOAT
);

-- ============================================================
-- v2 신규: Expected Event Calendar (Part 5)
-- ============================================================

CREATE TABLE IF NOT EXISTS expected_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    event_type TEXT NOT NULL,      -- "earnings"|"product_launch"|"conference"|"regulatory"|"industry_data"
    expected_date DATE NOT NULL,
    description TEXT,
    variable_ids TEXT,             -- JSON array: ["V11","V20","V22"]
    source TEXT,                   -- 일정 출처
    is_confirmed INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_expected_date ON expected_events(expected_date);
