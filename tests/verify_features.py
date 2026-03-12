import sys
import os
import sqlite3
import time

sys.path.append(os.getcwd())
from backend.agents.orchestrator import Orchestrator
from backend.dashboard_api import sync_dashboard

def test_critique_and_resolution():
    print("--- Starting Verification Test ---")
    orchestrator = Orchestrator()
    
    # 1. Test Critique Loop (SOMA)
    print("\n[1] Testing Critique Loop with SOMA signal...")
    # This signal might trigger a retry if the LLM thinks it's ambiguous
    orchestrator.process_signal({"type": "cold_chain", "store_id": 3, "temp": 14.5, "duration_mins": 20})
    
    # 2. Test Human Escalation
    print("\n[2] Testing Human Escalation...")
    orchestrator.process_signal({"type": "unknown_signal", "data": "Something weird happened"})
    sync_dashboard()
    
    # 3. Check DB for pending escalation
    conn = sqlite3.connect("backend/db/pharmaiq.db")
    cursor = conn.cursor()
    cursor.execute("SELECT alert_id FROM alerts WHERE human_needed = 1 AND status = 'pending' ORDER BY ts DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        alert_id = row[0]
        print(f"Found pending escalation alert: {alert_id}")
        
        # 4. Test Manual Resolution (via API call simulation)
        print(f"\n[3] Testing Manual Resolution for alert {alert_id}...")
        from backend.dashboard_api import resolve_alert
        resolve_alert(alert_id)
        
        # Verify resolution
        cursor.execute("SELECT status FROM alerts WHERE alert_id = ?", (alert_id,))
        new_status = cursor.fetchone()[0]
        print(f"New status for alert {alert_id}: {new_status}")
        if new_status == 'resolved':
            print("SUCCESS: Manual resolution verified.")
        else:
            print("FAILURE: Manual resolution failed.")
    else:
        print("FAILURE: No pending escalation alert found to resolve.")
    
    conn.close()
    print("\n--- Verification Test Complete ---")

if __name__ == "__main__":
    test_critique_and_resolution()
