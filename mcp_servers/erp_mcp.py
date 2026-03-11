import sqlite3

DB_PATH = "db/pharmaiq.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_inventory_levels(store_id: int, sku_id: str = None):
    """Fetches inventory levels for a specific store, optionally filtered by SKU."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if sku_id:
        cursor.execute("""
            SELECT sku_id, batch_no, qty, expiry_date, status 
            FROM inventory 
            WHERE store_id = ? AND sku_id = ?
        """, (store_id, sku_id))
    else:
        cursor.execute("""
            SELECT sku_id, batch_no, qty, expiry_date, status 
            FROM inventory 
            WHERE store_id = ?
        """, (store_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def place_purchase_order(store_id: int, sku_id: str, qty: int, trigger_agent: str = "SYSTEM"):
    """Records a purchase order for restocking in the ERP store."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO purchase_orders (store_id, sku_id, qty, trigger_agent)
        VALUES (?, ?, ?, ?)
    """, (store_id, sku_id, qty, trigger_agent))
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "message": f"Recorded PO for {qty} units of {sku_id} at Store {store_id}."
    }

def quarantine_batch(batch_no: str, reason: str):
    """Marks a specific batch as quarantined."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE inventory 
        SET status = 'quarantined' 
        WHERE batch_no = ?
    """, (batch_no,))
    conn.commit()
    conn.close()
    
    return {"status": "success", "batch_no": batch_no, "action": "quarantined", "reason": reason}

# ERP MCP Server (Port 8003)

def get_inventory(store_id: int, sku_id: str = None):
    """Fetches inventory levels."""
    return get_inventory_levels(store_id, sku_id)

def raise_po(store_id: int, sku_id: str, qty: int, agent: str = "SYSTEM"):
    """Alias for place_purchase_order."""
    return place_purchase_order(store_id, sku_id, qty, agent)

def update_batch_status(batch_no: str, status: str):
    """Updates the status of a specific batch."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE inventory SET status = ? WHERE batch_no = ?
    """, (status, batch_no))
    conn.commit()
    conn.close()
    return {"status": "updated", "batch_no": batch_no, "new_status": status}

# For LangChain/MCP manifest
erp_tools = [
    {
        "name": "get_inventory",
        "description": "Get inventory levels for a store/SKU.",
        "parameters": {"store_id": "int", "sku_id": "str"}
    },
    {
        "name": "raise_po",
        "description": "Raise a purchase order.",
        "parameters": {"store_id": "int", "sku_id": "str", "qty": "int", "agent": "str"}
    },
    {
        "name": "update_batch_status",
        "description": "Update batch status (e.g., quarantined).",
        "parameters": {"batch_no": "str", "status": "str"}
    }
]

PORT = 8003
