import json
from typing import TypedDict, List, Annotated
import operator
# Note: In a production environment, we would use:
# from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    """Shared state for the PharmaIQ orchestration."""
    signals: List[dict]
    history: List[str]
    current_agent: str
    decision_threshold_exceeded: bool
    escalation_required: bool

from tools.llm_utils import get_gemini_response
import os

def route_signal_with_gemini(signal: dict):
    """Uses Gemini to intelligently route signals to the correct agent."""
    try:
        # Load prompts
        prompt_dir = "prompts"
        with open(os.path.join(prompt_dir, "routing_system.txt"), "r") as f:
            system_prompt = f.read()
        with open(os.path.join(prompt_dir, "routing_user.txt"), "r") as f:
            user_template = f.read()
        
        user_prompt = user_template.replace("{{SIGNAL_JSON}}", json.dumps(signal, indent=2))
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = get_gemini_response(full_prompt)
        
        target = response.strip().upper()
        if target in ["SOMA", "PULSE", "HUMAN_ESCALATION"]:
            return target
        return "HUMAN_ESCALATION" # Fallback for unexpected response
    except Exception as e:
        print(f"ROUTER_ERROR: {str(e)}. Falling back to static logic.")
        return route_signal_static(signal)

def route_signal_static(signal: dict):
    """Fallback static routing logic."""
    sig_type = signal.get("type")
    if sig_type in ["cold_chain", "scheduling"]:
        return "SOMA"
    elif sig_type in ["epidemic", "expiry"]:
        return "PULSE"
    else:
        return "HUMAN_ESCALATION"

def route_signal(state: AgentState):
    """Router function that prefers Gemini for intelligence."""
    last_signal = state["signals"][-1] if state["signals"] else None
    if not last_signal:
        return "END"
    
    return route_signal_with_gemini(last_signal)

class Orchestrator:
    """Mock implementation of the LangGraph Orchestrator logic for demo."""
    
    def __init__(self):
        self.state = {
            "signals": [],
            "history": [],
            "current_agent": None,
            "decision_threshold_exceeded": False,
            "escalation_required": False
        }

    def process_signal(self, signal: dict):
        print(f"\n--- Processing Signal: {signal.get('type', 'Natural Language')} ---")
        self.state["signals"].append(signal)
        
        target = route_signal(self.state)
        self.state["current_agent"] = target
        
        if target == "SOMA":
            from agents.soma import SOMA
            agent = SOMA()
            result = agent.run(signal)
            self.state["history"].append(f"SOMA: {result}")
        elif target == "PULSE":
            from agents.pulse import PULSE
            agent = PULSE()
            result = agent.run(signal)
            self.state["history"].append(f"PULSE: {result}")
        else:
            self.state["escalation_required"] = True
            msg = f"ESCALATED: Signal requires human review."
            self.state["history"].append(msg)
            print(f"CRITICAL: {msg} for {signal}")
        
        return self.state

if __name__ == "__main__":
    # Test routing
    orchestrator = Orchestrator()
    orchestrator.process_signal({"type": "cold_chain", "store_id": 1, "temp": 9.5})
    orchestrator.process_signal({"type": "epidemic", "region": "Mumbai", "disease": "Dengue"})
