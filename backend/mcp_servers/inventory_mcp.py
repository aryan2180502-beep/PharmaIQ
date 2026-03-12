import sqlite3
from datetime import datetime, timedelta

DB_PATH = "backend/db/pharmaiq.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def scan_for_near_expiry(days_threshold: int = 60, store_id: int = None):
    """Scans inventory for batches expiring within the threshold."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    threshold_date = (datetime.now() + timedelta(days=days_threshold)).date()
    
    if store_id:
        cursor.execute("""
            SELECT sku_id, batch_no, qty, expiry_date 
            FROM inventory 
            WHERE store_id = ? AND expiry_date <= ? AND status = 'active'
        """, (store_id, threshold_date))
    else:
        cursor.execute("""
            SELECT store_id, sku_id, batch_no, qty, expiry_date 
            FROM inventory 
            WHERE expiry_date <= ? AND status = 'active'
        """, (threshold_date,))
        
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# Inventory MCP Server (Port 8005)

def get_expiry_risk_items(days_threshold: int = 60, store_id: int = None):
    """Fetches items at risk of expiry."""
    return scan_for_near_expiry(days_threshold, store_id)

def get_slow_movers(store_id: int):
    """Identifies slow-moving SKUs."""
    # Mock data for demo
    return [{"sku_id": "SKU-003", "last_sale": "15 days ago", "stock": 400}]

def flag_markdown(batch_no: str, percentage: int):
    """Flags a batch for markdown pricing."""
    return {"status": "success", "batch_no": batch_no, "markdown": f"{percentage}%"}

# For LangChain/MCP manifest
inventory_tools = [
    {
        "name": "get_expiry_risk_items",
        "description": "Get items expiring within threshold.",
        "parameters": {"days_threshold": "int", "store_id": "int"}
    },
    {
        "name": "get_slow_movers",
        "description": "Get slow moving items for a store.",
        "parameters": {"store_id": "int"}
    },
    {
        "name": "flag_markdown",
        "description": "Trigger a markdown for a batch.",
        "parameters": {"batch_no": "str", "percentage": "int"}
    }
]

PORT = 8005
