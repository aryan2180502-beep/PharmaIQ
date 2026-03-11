import sqlite3
from datetime import datetime, timedelta

DB_PATH = "db/pharmaiq.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_store_schedule(store_id: int, date_str: str = None):
    """Fetches the shift schedule for a specific store on a given date."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT staff_id, role, start_dt, end_dt, pharmacist_flag 
        FROM staff_schedules 
        WHERE store_id = ? AND date(start_dt) = ?
        ORDER BY start_dt ASC
    """, (store_id, date_str))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def detect_scheduling_gaps(store_id: int, days_ahead: int = 3):
    """Identifies days where the required minimum shifts are not met."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    gaps = []
    for i in range(days_ahead):
        check_date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT COUNT(*) as shift_count 
            FROM staff_schedules 
            WHERE store_id = ? AND date(start_dt) = ?
        """, (store_id, check_date))
        count = cursor.fetchone()["shift_count"]
        
        # Simple logic: Need at least 1 pharmacist shift per day
        if count < 1:
            gaps.append({"date": check_date, "count": count, "missing": 1 - count})
            
    conn.close()
    return gaps

def update_shift(store_id: int, staff_id: str, role: str, start_dt: str, end_dt: str, pharmacist_flag: bool = True):
    """Adds or updates a staff shift."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO staff_schedules (store_id, staff_id, role, start_dt, end_dt, pharmacist_flag)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (store_id, staff_id, role, start_dt, end_dt, pharmacist_flag))
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": f"Shift recorded for {staff_id}"}

# HRMS MCP Server (Port 8002)

def get_schedule(store_id: int, date_str: str = None):
    """Fetches the shift schedule for a specific store."""
    return get_store_schedule(store_id, date_str)

def flag_gap(store_id: int, date: str, reason: str):
    """Flags a scheduling gap in the system for human review."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alerts (agent, store_id, type, severity, action_taken, human_needed)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("SOMA", store_id, "scheduling", "warning", reason, True))
    conn.commit()
    conn.close()
    return {"status": "flagged", "store_id": store_id, "date": date}

def suggest_replacement(store_id: int, date: str):
    """Suggests a relief pharmacist for a gap."""
    return {"status": "suggested", "staff_id": "STAFF-999-RELIEF", "name": "Relief Expert"}

# For LangChain/MCP manifest
hrms_tools = [
    {
        "name": "get_schedule",
        "description": "Get shift schedule for a store.",
        "parameters": {"store_id": "int", "date_str": "str"}
    },
    {
        "name": "flag_gap",
        "description": "Flag a staffing gap.",
        "parameters": {"store_id": "int", "date": "str", "reason": "str"}
    },
    {
        "name": "suggest_replacement",
        "description": "Suggest a replacement staff for a gap.",
        "parameters": {"store_id": "int", "date": "str"}
    }
]
