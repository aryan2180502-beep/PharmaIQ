import sqlite3

DB_PATH = "db/pharmaiq.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_epidemic_signals(district: str = None):
    """Fetches high-level epidemic signals from the SQLite store."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if district:
        cursor.execute("SELECT * FROM epidemic_signals WHERE district LIKE ?", (f"%{district}%",))
    else:
        cursor.execute("SELECT * FROM epidemic_signals")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def check_for_outbreak(district: str):
    """Specific check to see if an outbreak in a district exceeds a threshold."""
    signals = get_epidemic_signals(district)
    # Simple threshold logic: cases > 30 is an outbreak for demo
    outbreaks = [s for s in signals if s.get("case_count", 0) > 30]
# IDSP MCP Server (Port 8004)

def get_disease_signals(district: str = None):
    """Fetches high-level disease signals."""
    return get_epidemic_signals(district)

def get_district_trend(district: str):
    """Analyzes recent trends for a district."""
    signals = get_epidemic_signals(district)
    # Mock trend analysis
    return {"district": district, "trend": "Increasing", "wow_growth": 25.5}

# For LangChain/MCP manifest
idsp_tools = [
    {
        "name": "get_disease_signals",
        "description": "Get current disease signals for a district.",
        "parameters": {"district": "str"}
    },
    {
        "name": "get_district_trend",
        "description": "Get growth trend for a district.",
        "parameters": {"district": "str"}
    }
]

PORT = 8004

# For standalone tool mapping in LangChain
idsp_tools = [
    {
        "name": "get_epidemic_signals",
        "description": "Get current disease surveillance and epidemic signals.",
        "func": get_epidemic_signals
    },
    {
        "name": "check_for_outbreak",
        "description": "Check if there is a pending or active outbreak in a specific region.",
        "func": check_for_outbreak
    }
]
