import sqlite3
import random
from datetime import datetime

DB_PATH = "backend/db/pharmaiq.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_current_temperature(store_id: int):
    """Fetches the latest temperature reading for a specific store fridge."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT temp_c as temperature, timestamp, breach_flag as is_breach 
        FROM temperature_logs 
        WHERE store_id = ? 
        ORDER BY timestamp DESC LIMIT 1
    """, (store_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return {"error": "No temperature data found for this store."}

def check_for_breaches(store_id: int, hours: int = 24):
    """Checks for any temperature breaches in the last X hours."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as breach_count 
        FROM temperature_logs 
        WHERE store_id = ? AND breach_flag = 1 AND timestamp > datetime('now', '-' || ? || ' hours')
    """, (store_id, hours))
    count = cursor.fetchone()["breach_count"]
    conn.close()
    
    return {"store_id": store_id, "breach_count": count, "status": "critical" if count > 0 else "stable"}

def log_new_reading(store_id: int, temperature: float = None):
    """Simulates a sensor pushing a new reading."""
    if temperature is None:
        temperature = round(random.uniform(2.5, 7.5), 2)
    
    is_breach = temperature > 8.0 or temperature < 2.0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO temperature_logs (store_id, unit_id, temp_c, breach_flag)
        VALUES (?, ?, ?, ?)
    """, (store_id, "FRIDGE-01", temperature, is_breach))
    conn.commit()
    conn.close()
    
    return {"temperature": temperature, "is_breach": is_breach}

# IoT MCP Server (Port 8001)

def get_temperature(store_id: int):
    """Fetches the latest temperature reading for a specific store fridge."""
    return get_current_temperature(store_id)

def trigger_alert(store_id: int, message: str, severity: str = "warning"):
    """Manually triggers a temperature alert for a store."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alerts (agent, store_id, type, severity, action_taken)
        VALUES (?, ?, ?, ?, ?)
    """, ("SOMA", store_id, "cold_chain", severity, message))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Alert triggered for store {store_id}"}

# For LangChain/MCP manifest
iot_tools = [
    {
        "name": "get_temperature",
        "description": "Get current fridge temperature for a store.",
        "parameters": {"store_id": "int"}
    },
    {
        "name": "trigger_alert",
        "description": "Trigger a cold chain alert.",
        "parameters": {"store_id": "int", "message": "str", "severity": "str"}
    },
    {
        "name": "quarantine_batch",
        "description": "Quarantine a specific drug batch.",
        "parameters": {"batch_no": "str", "reason": "str"}
    }
]

PORT = 8001
