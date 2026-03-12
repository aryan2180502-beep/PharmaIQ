import sqlite3
import json
import os

DB_PATH = "backend/db/pharmaiq.db"
DATA_JSON_PATH = "frontend/data.json"

def sync_dashboard():
    """Syncs data from SQLite to a JSON file for the live frontend."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Fetch recent alerts (last 20 for history) and ALL pending escalations
    # We want to make sure any 'ghost' escalations are visible so they can be resolved.
    cursor.execute("SELECT * FROM alerts WHERE status = 'pending' AND human_needed = 1")
    pending_escalations = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM alerts ORDER BY ts DESC LIMIT 30")
    recent_alerts = [dict(row) for row in cursor.fetchall()]
    
    # Merge and deduplicate by alert_id
    alerts_map = {a['alert_id']: a for a in pending_escalations}
    for a in recent_alerts:
        if a['alert_id'] not in alerts_map:
            alerts_map[a['alert_id']] = a
            
    # Sort merged list by ts DESC
    alerts = sorted(alerts_map.values(), key=lambda x: x['ts'], reverse=True)
    
    # 2. Fetch quarantined items
    cursor.execute("""
        SELECT c.name as drug_name, i.batch_no, i.status, i.store_id 
        FROM inventory i
        JOIN drug_catalog c ON i.sku_id = c.sku_id
        WHERE i.status != 'active'
    """)
    quarantined = [dict(row) for row in cursor.fetchall()]
    
    # 3. Aggregate Per-Store Status
    # Priority: escalated > critical > warning > stable
    store_status = {}
    for i in range(1, 11):
        # Default stable
        store_status[i] = "stable"
        
        # Check for human escalation (Highest Priority)
        cursor.execute("SELECT 1 FROM alerts WHERE store_id = ? AND human_needed = 1 AND status = 'pending' LIMIT 1", (i,))
        if cursor.fetchone():
            store_status[i] = "escalated"
            continue

        # Check for critical alerts in last 24h
        cursor.execute("SELECT severity FROM alerts WHERE store_id = ? AND severity = 'critical' AND status = 'pending'", (i,))
        if cursor.fetchone():
            store_status[i] = "critical"
            continue
            
        # Check for quarantined items
        cursor.execute("SELECT 1 FROM inventory WHERE store_id = ? AND status = 'quarantined'", (i,))
        if cursor.fetchone():
            store_status[i] = "warning"

    # 4. Global Stats & Forecast
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE status = 'pending'")
    pending_alerts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM inventory WHERE status = 'quarantined'")
    quarantined_count = cursor.fetchone()[0]
    
    # 5. Extract Escalations (EXCLUSIVELY pending human review)
    # This prevents them from being buried in the general history
    cursor.execute("SELECT * FROM alerts WHERE human_needed = 1 AND status = 'pending' ORDER BY ts DESC")
    escalations = [dict(row) for row in cursor.fetchall()]
    
    # 6. Generate Dynamic Forecast Data (PULSE Simulation)
    # We'll base this on a small variation around baseline numbers
    import random
    # Cities: Mumbai, Delhi, Bengaluru, Chennai, Hyderabad, Pune, Kolkata
    baselines = [40, 60, 95, 75, 50, 45, 30]
    forecast_data = [min(100, max(10, b + random.randint(-15, 15))) for b in baselines]
    
    conn.close()
    
    # 7. Compile State
    state = {
        "last_sync": os.popen("date '+%H:%M:%S'").read().strip(),
        "alerts": alerts,
        "escalations": escalations,
        "quarantined": quarantined,
        "store_status": store_status,
        "forecast_data": forecast_data,
        "stats": {
            "pending_alerts": pending_alerts,
            "quarantined_items": quarantined_count,
            "coverage": "100%"
        }
    }
    
    with open(DATA_JSON_PATH, "w") as f:
        json.dump(state, f, indent=2)
    
    # print(f"DASHBOARD_SYNC: State saved to {DATA_JSON_PATH}")

def resolve_alert(alert_id: int):
    """Marks an alert as resolved and logs the resolution action in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Fetch the original alert so we know which store it belongs to
    cursor.execute("SELECT store_id, type, agent FROM alerts WHERE alert_id = ?", (alert_id,))
    row = cursor.fetchone()
    
    if row:
        store_id, sig_type, agent = row
        
        # 2. Mark the original alert as resolved
        cursor.execute(
            "UPDATE alerts SET status = 'resolved' WHERE alert_id = ?",
            (alert_id,)
        )
        
        # 3. Log the resolution as a new audit entry in the alerts table
        resolution_action = f"Orchestrator ---> HUMAN | Human operator resolved alert #{alert_id}. Store status reset to stable."
        cursor.execute("""
            INSERT INTO alerts (agent, store_id, type, severity, action_taken, human_needed, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("HUMAN_RESOLVED", store_id, sig_type, "info", resolution_action, 0, "resolved"))
        
        conn.commit()
        conn.close()
        sync_dashboard()
        print(f"DASHBOARD_API: Alert {alert_id} resolved. Store {store_id} status reset. Resolution logged.")
    else:
        conn.close()
        print(f"DASHBOARD_API: Alert {alert_id} not found.")


if __name__ == "__main__":
    sync_dashboard()
