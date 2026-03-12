import sys
import os
import json
import time
import random

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("PHARMAIQ: Initializing Simulation...")

# Ensure project root is in path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.agents.orchestrator import Orchestrator
from backend.tools.llm_utils import get_gemini_response
from backend.dashboard_api import sync_dashboard

def generate_live_signal():
    """Uses Gemini to generate a random live signal for any of the 10 stores."""
    store_id = random.randint(1, 10)
    prompt_path = "backend/prompts/daily_signal_gen.txt"
    with open(prompt_path, "r") as f:
        template = f.read()
    
    prompt = template.replace("{{STORE_ID}}", str(store_id))
    response = get_gemini_response(prompt)
    
    try:
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        print(f"LIVE_MODE: Error parsing signal: {str(e)}")
        return None

def start_live_mode():
    print("=== PHARMAIQ LIVE OPERATIONS MODE ===")
    print("Generating AI-driven signals every 10-15 seconds...")
    orchestrator = Orchestrator()
    
    try:
        while True:
            signal = generate_live_signal()
            if signal:
                print(f"[{time.strftime('%H:%M:%S')}] New Signal: {signal.get('type')} at Store {signal.get('store_id')}")
                orchestrator.process_signal(signal)
                sync_dashboard()
            
            # Wait for next wave
            delay = random.randint(40, 45)
            time.sleep(delay)
    except KeyboardInterrupt:
        print("\nStopping Live Mode.")

print("LIVE_MODE: Script loaded.")

if __name__ == "__main__":
    print("LIVE_MODE: Starting execution...")
    try:
        start_live_mode()
    except Exception as e:
        print(f"LIVE_MODE: FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
