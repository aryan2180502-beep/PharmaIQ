import os
from backend.tools.llm_utils import get_gemini_response

class CritiqueAgent:
    """Critique Agent that evaluates other agents' outputs."""
    
    def __init__(self):
        self.name = "CRITIQUE"
        # Use robust absolute path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_dir, "prompts", "critique_system.txt")
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read()

    def review(self, agent_name: str, signal: dict, action: str):
        """Reviews an agent's output and provides feedback or approval."""
        prompt = f"""
{self.system_prompt}

### Agent: {agent_name}
### Signal: {signal}
### Action Taken: {action}

Review the action above:
"""
        response = get_gemini_response(prompt).strip()
        
        if response.startswith("PASSED"):
            return True, None
        elif response.startswith("RETRY"):
            feedback = response.replace("RETRY:", "").strip()
            return False, feedback
        else:
            # Default to pass if the LLM output is not in the expected format
            return True, None
