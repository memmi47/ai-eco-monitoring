import pandas as pd
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_url = os.environ.get("DATABASE_URL", os.path.join(BASE_DIR, "database", "ai_eco_monitor.db"))
_IS_PG = db_url.startswith(("postgresql://", "postgres://"))


def extract_category_key(category: str) -> str:
    """'A1. Energy & Power' → 'A1'"""
    if not category or category == 'None':
        return "XX"
    m = re.match(r'^([A-Z]\d+)', category.strip())
    return m.group(1) if m else "XX"


def map_tier(importance):
    if not isinstance(importance, str):
        return None
    val = importance.strip().lower()
    if val == 'high':
        return 'T1'
    elif val == 'medium':
        return 'T2'
    elif val == 'low':
        return 'T3'
    return None


def _pg_schema() -> str:
    """PostgreSQL용 스키마 (AUTOINCREMENT → SERIAL)."""
    return """
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    seq_no INTEGER,
    layer VARCHAR(255),
    category VARCHAR(255),
    category_key VARCHAR(10),
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

CREATE TABLE IF NOT EXISTS crawl_history (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    title TEXT,
    source_url TEXT,
    published_date TIMESTAMP,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content TEXT
);

CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    crawl_id INTEGER REFERENCES crawl_history(id),
    company_id INTEGER REFERENCES companies(id),
    is_memory_related INTEGER,
    event_type VARCHAR(255),
    memory_signal VARCHAR(255),
    impact_score FLOAT,
    implications TEXT,
    timeframe VARCHAR(255),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stage1_relevant INTEGER,
    stage1_facts TEXT,
    stage2_variable_id TEXT,
    stage2_variable_name TEXT,
    stage2_direction TEXT,
    stage2_caveat TEXT,
    stage2_needs_review INTEGER DEFAULT 0,
    stage2_strength TEXT,
    stage2_confidence TEXT,
    stage2_affected_memory TEXT,
    stage2_reasoning TEXT,
    stage3_transmission_path TEXT,
    stage3_memory_impact TEXT,
    stage3_time_lag TEXT,
    stage3_demand_formula_tier TEXT,
    stage3_demand_formula_role TEXT,
    stage3_decision_relevance TEXT,
    stage3_counterargument TEXT,
    stage3_executive_summary TEXT,
    model_used TEXT,
    pipeline_version INTEGER DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_analysis_variable ON analysis_results(stage2_variable_id);
CREATE INDEX IF NOT EXISTS idx_analysis_direction ON analysis_results(stage2_direction);
CREATE INDEX IF NOT EXISTS idx_analysis_tier ON analysis_results(stage3_demand_formula_tier);
CREATE INDEX IF NOT EXISTS idx_analysis_version ON analysis_results(pipeline_version);

CREATE TABLE IF NOT EXISTS activity_index (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    calculation_date DATE,
    index_value FLOAT,
    news_count INTEGER,
    avg_impact_score FLOAT
);

CREATE TABLE IF NOT EXISTS expected_events (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    event_type TEXT NOT NULL,
    expected_date DATE NOT NULL,
    description TEXT,
    variable_ids TEXT,
    source TEXT,
    is_confirmed INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_expected_date ON expected_events(expected_date);
"""


def main():
    csv_path = os.path.join(BASE_DIR, 'AI_Factory_Ecosystem_Database_v2.csv')

    if _IS_PG:
        _seed_postgres(csv_path)
    else:
        _seed_sqlite(csv_path)


def _seed_postgres(csv_path: str):
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        print("[seed_db Error] psycopg2가 설치되지 않았습니다.")
        return

    try:
        print(f"Connecting to PostgreSQL...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        print("Creating schema...")
        for stmt in _pg_schema().split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)
        conn.commit()

        print("Loading CSV...")
        df = pd.read_csv(csv_path)

        cur.execute("SELECT COUNT(*) as cnt FROM companies")
        row = cur.fetchone()
        if row and row["cnt"] > 0:
            print(f"-> [SKIP] companies 테이블에 이미 {row['cnt']}건 존재. 시딩 건너뜀.")
            conn.close()
            return

        inserted_count = 0
        tier_counts = {'T1': 0, 'T2': 0, 'T3': 0}

        for _, row in df.iterrows():
            tier = map_tier(str(row['중요도']))
            category_raw = str(row['Category (중분류)']) if pd.notna(row['Category (중분류)']) else None
            category_key = extract_category_key(category_raw)

            cur.execute("""
                INSERT INTO companies (
                    seq_no, layer, category, category_key, sub_category,
                    company_name, biz_type, listing_status, hq_region,
                    company_mission, description, importance, tier
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                int(row['No.']) if pd.notna(row['No.']) else None,
                str(row['Layer (대분류)']) if pd.notna(row['Layer (대분류)']) else None,
                category_raw,
                category_key,
                str(row['Sub-category (소분류)']) if pd.notna(row['Sub-category (소분류)']) else None,
                str(row['회사명']) if pd.notna(row['회사명']) else None,
                str(row['구분']) if pd.notna(row['구분']) else None,
                str(row['상장여부']) if pd.notna(row['상장여부']) else None,
                str(row['HQ지역']) if pd.notna(row['HQ지역']) else None,
                str(row['Company Mission']) if pd.notna(row['Company Mission']) else None,
                str(row['한줄 설명 (비고)']) if pd.notna(row['한줄 설명 (비고)']) else None,
                str(row['중요도']) if pd.notna(row['중요도']) else None,
                tier
            ))
            inserted_count += 1
            if tier in tier_counts:
                tier_counts[tier] += 1

        conn.commit()
        print(f"-> [OK] {inserted_count}건 적재 완료 | T1:{tier_counts['T1']} T2:{tier_counts['T2']} T3:{tier_counts['T3']}")

    except Exception as e:
        print(f"[seed_db Error] {e}")
        import traceback; traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()


def _seed_sqlite(csv_path: str):
    import sqlite3
    try:
        print(f"Connecting to SQLite...")
        os.makedirs(os.path.dirname(db_url), exist_ok=True)

        conn = sqlite3.connect(db_url)
        cur = conn.cursor()

        print("Creating schema...")
        schema_path = os.path.join(BASE_DIR, "database", "schema.sql")
        with open(schema_path, 'r') as f:
            cur.executescript(f.read())

        print("Loading CSV...")
        df = pd.read_csv(csv_path)

        cur.execute("SELECT COUNT(*) FROM companies")
        if cur.fetchone()[0] > 0:
            print("-> [SKIP] companies 테이블에 이미 데이터 존재.")
            conn.close()
            return

        inserted_count = 0
        tier_counts = {'T1': 0, 'T2': 0, 'T3': 0}

        for _, row in df.iterrows():
            tier = map_tier(str(row['중요도']))
            category_raw = str(row['Category (중분류)']) if pd.notna(row['Category (중분류)']) else None
            category_key = extract_category_key(category_raw)

            cur.execute("""
                INSERT INTO companies (
                    seq_no, layer, category, category_key, sub_category,
                    company_name, biz_type, listing_status, hq_region,
                    company_mission, description, importance, tier
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                int(row['No.']) if pd.notna(row['No.']) else None,
                str(row['Layer (대분류)']) if pd.notna(row['Layer (대분류)']) else None,
                category_raw,
                category_key,
                str(row['Sub-category (소분류)']) if pd.notna(row['Sub-category (소분류)']) else None,
                str(row['회사명']) if pd.notna(row['회사명']) else None,
                str(row['구분']) if pd.notna(row['구분']) else None,
                str(row['상장여부']) if pd.notna(row['상장여부']) else None,
                str(row['HQ지역']) if pd.notna(row['HQ지역']) else None,
                str(row['Company Mission']) if pd.notna(row['Company Mission']) else None,
                str(row['한줄 설명 (비고)']) if pd.notna(row['한줄 설명 (비고)']) else None,
                str(row['중요도']) if pd.notna(row['중요도']) else None,
                tier
            ))
            inserted_count += 1
            if tier in tier_counts:
                tier_counts[tier] += 1

        conn.commit()
        print(f"-> [OK] {inserted_count}건 적재 완료 | T1:{tier_counts['T1']} T2:{tier_counts['T2']} T3:{tier_counts['T3']}")

    except Exception as e:
        print(f"[seed_db Error] {e}")
        import traceback; traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == '__main__':
    main()
