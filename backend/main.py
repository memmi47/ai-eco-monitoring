import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import sqlite3
import litellm

load_dotenv()

app = FastAPI(title="AI Eco Monitor API")
# Point to SQLite db file in database dir
db_url = os.environ.get("DATABASE_URL", "../database/ai_eco_monitor.db")

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
    return {"layers": [], "categories": []}

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
