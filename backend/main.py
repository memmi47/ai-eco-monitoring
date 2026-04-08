import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import sqlite3
import litellm
import sys

# Add database directory to path to import seed_db
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))
try:
    import seed_db
except ImportError:
    seed_db = None

load_dotenv()

# Base directory is now the backend folder itself
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="AI Eco Monitor API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite DB is now in backend/database/
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "database", "ai_eco_monitor.db")
db_url = os.environ.get("DATABASE_URL", DEFAULT_DB_PATH)

# Import seed_db from the local database folder
import sys
sys.path.append(os.path.join(BASE_DIR, 'database'))
try:
    import seed_db
except ImportError:
    seed_db = None

# Startup check
@app.on_event("startup")
def startup_event():
    db_dir = os.path.dirname(db_url)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_url)
    cursor = conn.cursor()
    # If the provided DATABASE_URL is postgres, we skip the sqlite check/seed
    if db_url.startswith("postgresql"):
        print(f"Connecting to external PostgreSQL: {db_url}")
        conn.close()
        return

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print(f"Initializing SQLite database at {db_url}...")
        if seed_db:
            seed_db.main()
    else:
        cursor.execute("SELECT COUNT(*) FROM companies")
        if cursor.fetchone()[0] == 0:
            if seed_db:
                seed_db.main()
    conn.close()

MODEL_FREE = "openrouter/google/gemma-2-9b-it:free"
MODEL_PAID = "openrouter/google/gemini-flash-1.5"

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# GET /api/companies
@app.get("/api/companies")
def get_companies(layer: str = None, tier: str = None, q: str = None):
    query = "SELECT * FROM companies WHERE 1=1"
    params = []
    if layer:
        query += " AND layer = ?"
        params.append(layer)
    if tier:
        query += " AND tier = ?"
        params.append(tier)
    if q:
        query += " AND company_name LIKE ?"
        params.append(f"%{q}%")
        
    conn = sqlite3.connect(db_url)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()
    return data

@app.get("/api/companies/{company_id}")
def get_company(company_id: int):
    conn = sqlite3.connect(db_url)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
    data = cursor.fetchone()
    conn.close()
    if not data:
        raise HTTPException(status_code=404, detail="Company not found")
    return data

@app.get("/api/stats")
def get_stats():
    conn = sqlite3.connect(db_url)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM companies")
    total = cursor.fetchone()['total']
    cursor.execute("SELECT tier, COUNT(*) as count FROM companies GROUP BY tier")
    tiers = {row['tier'] if row['tier'] else 'other': row['count'] for row in cursor.fetchall()}
    conn.close()
    return {"total_companies": total, "tier1": tiers.get('T1', 0), "tier2": tiers.get('T2', 0), "tier3": tiers.get('T3', 0)}

@app.get("/api/feed")
def get_feed():
    return []

@app.get("/api/activity")
def get_activity():
    return []

@app.get("/api/taxonomy")
def get_taxonomy():
    conn = sqlite3.connect(db_url)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT layer FROM companies ORDER BY layer")
    layers = [row['layer'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT category FROM companies ORDER BY category")
    categories = [row['category'] for row in cursor.fetchall()]
    
    conn.close()
    return {"layers": layers, "categories": categories}

class AnalyzeRequest(BaseModel):
    news_content: str

@app.post("/api/analyze")
def analyze_news(request: AnalyzeRequest):
    content = request.news_content
    try:
        # Stage 1
        response1 = litellm.completion(
            model=MODEL_FREE,
            messages=[{"role": "user", "content": f"Is this news related to memory semiconductors? Reply with 'yes' or 'no' only.\n\n{content}"}]
        )
        is_related = response1.choices[0].message.content.strip().lower()
        
        if "no" in is_related:
            return {"is_memory_related": False, "reason": "Not related to memory semiconductor."}
            
        # Stage 2
        response2 = litellm.completion(
            model=MODEL_FREE,
            messages=[{"role": "user", "content": f"Tag the event_type and memory_signal for this news.\n\n{content}"}]
        )
        tagging = response2.choices[0].message.content
        
        # Stage 3
        response3 = litellm.completion(
            model=MODEL_PAID,
            messages=[{"role": "user", "content": f"Analyze impact_score (1-10), implications, and timeframe based on tags: {tagging}\n\n{content}"}]
        )
        impact = response3.choices[0].message.content
        
        return {
            "is_memory_related": True,
            "tagging": tagging,
            "impact_analysis": impact
        }
    except Exception as e:
        print(f"LLM API Error: {e}")
        # Graceful degradation for testing
        return {
            "is_memory_related": True,
            "tagging": "[Mock] Event: New Product, Signal: High Bandwidth Requirement",
            "impact_analysis": f"[Mock] Impact Score: 8/10. Error encountered: {str(e)}",
            "is_mock": True
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
