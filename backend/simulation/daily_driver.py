import sys
import os
import json
import time
sys.path.append(os.getcwd())

from backend.agents.orchestrator import Orchestrator
from backend.tools.llm_utils import get_gemini_response
from backend.dashboard_api import sync_dashboard

def generate_daily_signal(store_id):
    """Uses Gemini to generate a daily signal for a specific store."""
    prompt_path = "backend/prompts/daily_signal_gen.txt"
    with open(prompt_path, "r") as f:
        template = f.read()
    
    prompt = template.replace("{{STORE_ID}}", str(store_id))
    response = get_gemini_response(prompt)
    
    try:
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        print(f"DAILY_SIM: Error parsing signal for Store {store_id}: {str(e)}")
        return {"store_id": store_id, "type": "cold_chain", "temp": 5.0}

def run_daily_simulation():
    print("=== PHARMAIQ DAILY STORE SIMULATION (10 STORES) ===")
    orchestrator = Orchestrator()
    
    for store_id in range(1, 11):
        print(f"\n--- Store {store_id}: Generating Daily Telemetry ---")
        signal = generate_daily_signal(store_id)
        print(f"Signal Type: {signal.get('type')}")
        
        # Process through Orchestrator
        orchestrator.process_signal(signal)
        
        # Artificial delay to mimic real-time processing
        time.sleep(1)

    print("\n--- All stores processed. Syncing to Dashboard... ---")
    sync_dashboard()
    print("DAILY_SIM: Simulation complete. Results available in dashboard.")

if __name__ == "__main__":
    run_daily_simulation()
