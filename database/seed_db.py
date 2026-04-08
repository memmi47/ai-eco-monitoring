import pandas as pd
import sqlite3
import os

# Define Base Directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_url = os.environ.get("DATABASE_URL", os.path.join(BASE_DIR, "database", "ai_eco_monitor.db"))

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

def main():
    try:
        print(f"Connecting to SQLite database: {db_url}...")
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_url), exist_ok=True)
        
        conn = sqlite3.connect(db_url)
        cur = conn.cursor()
        
        print("Creating schema...")
        schema_path = os.path.join(BASE_DIR, "database", "schema.sql")
        with open(schema_path, 'r') as f:
            cur.executescript(f.read())
            
        print("Loading CSV...")
        csv_path = os.path.join(BASE_DIR, 'AI_Factory_Ecosystem_Database_v2.csv')
        df = pd.read_csv(csv_path)

        inserted_count = 0
        tier_counts = {'T1': 0, 'T2': 0, 'T3': 0}

        cur.execute("DELETE FROM companies")

        for index, row in df.iterrows():
            tier = map_tier(str(row['중요도']))
            
            cur.execute("""
                INSERT INTO companies (seq_no, layer, category, sub_category, company_name, biz_type, listing_status, hq_region, company_mission, description, importance, tier)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(row['No.']) if pd.notna(row['No.']) else None,
                str(row['Layer (대분류)']) if pd.notna(row['Layer (대분류)']) else None,
                str(row['Category (중분류)']) if pd.notna(row['Category (중분류)']) else None,
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
        print(f"-> [OK] {inserted_count}건 적재 완료, Tier 1: {tier_counts['T1']}건, Tier 2: {tier_counts['T2']}건, Tier 3: {tier_counts['T3']}건 (+ 기타)")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main()
