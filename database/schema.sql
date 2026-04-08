CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seq_no INTEGER,
    layer VARCHAR(255),
    category VARCHAR(255),
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

CREATE TABLE IF NOT EXISTS crawl_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    title TEXT,
    source_url TEXT,
    published_date TIMESTAMP,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content TEXT
);

CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER REFERENCES crawl_history(id),
    is_memory_related INTEGER,
    event_type VARCHAR(255),
    memory_signal VARCHAR(255),
    impact_score FLOAT,
    implications TEXT,
    timeframe VARCHAR(255),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    calculation_date DATE,
    index_value FLOAT,
    news_count INTEGER,
    avg_impact_score FLOAT
);
