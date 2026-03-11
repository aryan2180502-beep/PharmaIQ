import sys
import os
import json
sys.path.append(os.getcwd())

from agents.orchestrator import Orchestrator
from tests.generate_test_data import generate_signals

def run_stress_test():
    print("=== PHARMAIQ AI-DRIVEN STRESS TEST ===")
    print("Initializing Orchestrator and generating dynamic signals...")
    
    orchestrator = Orchestrator()
    signals = generate_signals()
    
    results = []
    
    for i, signal in enumerate(signals):
        print(f"\n[{i+1}/{len(signals)}] Processing Signal...")
        try:
            state = orchestrator.process_signal(signal)
            last_action = state["history"][-1] if state["history"] else "NO_ACTION_RECORDED (Escalated)"
            results.append({
                "signal": signal,
                "agent": state["current_agent"],
                "action": last_action
            })
        except Exception as e:
            print(f"ERROR: Failed to process signal: {str(e)}")
            results.append({
                "signal": signal,
                "agent": "ERROR",
                "action": str(e)
            })

    print("\n" + "="*50)
    print("FINAL TEST SUMMARY")
    print("="*50)
    for r in results:
        print(f"[{r['agent']}] -> {r['action'][:100]}...")
    
    # Save results for audit
    with open("tests/test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to tests/test_results.json")

if __name__ == "__main__":
    run_stress_test()
