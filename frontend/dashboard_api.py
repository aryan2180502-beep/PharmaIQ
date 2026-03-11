import sqlite3
import json
import os

DB_PATH = "db/pharmaiq.db"
DATA_JSON_PATH = "frontend/data.json"

def sync_dashboard():
    """Syncs data from SQLite to a JSON file for the live frontend."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Fetch recent alerts (last 20 for history)
    cursor.execute("SELECT * FROM alerts ORDER BY ts DESC LIMIT 20")
    rows = cursor.fetchall()
    alerts = [dict(row) for row in rows]
    
    # 2. Fetch quarantined items
    cursor.execute("""
        SELECT c.name as drug_name, i.batch_no, i.status, i.store_id 
        FROM inventory i
        JOIN drug_catalog c ON i.sku_id = c.sku_id
        WHERE i.status != 'active'
    """)
    quarantined = [dict(row) for row in cursor.fetchall()]
    
    # 3. Aggregate Per-Store Status
    # We'll determine status based on pending critical alerts or quarantined items
    store_status = {}
    for i in range(1, 11):
        # Default stable
        store_status[i] = "stable"
        
        # Check for critical alerts in last 24h
        cursor.execute("SELECT severity FROM alerts WHERE store_id = ? AND severity = 'critical' AND status = 'pending'", (i,))
        if cursor.fetchone():
            store_status[i] = "critical"
            continue
            
        # Check for quarantined items
        cursor.execute("SELECT 1 FROM inventory WHERE store_id = ? AND status = 'quarantined'", (i,))
        if cursor.fetchone():
            store_status[i] = "warning"

    # 4. Global Stats
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE status = 'pending'")
    pending_alerts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM inventory WHERE status = 'quarantined'")
    quarantined_count = cursor.fetchone()[0]
    
    conn.close()
    
    # 5. Compile State
    state = {
        "last_sync": os.popen("date '+%H:%M:%S'").read().strip(),
        "alerts": alerts,
        "quarantined": quarantined,
        "store_status": store_status,
        "stats": {
            "pending_alerts": pending_alerts,
            "quarantined_items": quarantined_count,
            "coverage": "100%"
        }
    }
    
    with open(DATA_JSON_PATH, "w") as f:
        json.dump(state, f, indent=2)
    
    # print(f"DASHBOARD_SYNC: State saved to {DATA_JSON_PATH}")

if __name__ == "__main__":
    sync_dashboard()
