import google.generativeai as genai
import json
from backend.config import GEMINI_API_KEY

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_gemini_response(prompt: str, model_name: str = "gemini-pro-latest"):
    """Helper to get a response from the Gemini API."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your-key-here":
        return "LLM_MOCK: Gemini API key not configured."
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"LLM_ERROR: {str(e)}"

def summarize_action(agent_name: str, action: str, context: str):
    """Generates a professional summary of an agent action."""
    prompt = f"""
    You are the {agent_name} agent in the PharmaIQ system.
    You just took the following action: {action}
    Context: {context}
    
    Provide a professional, concise 1-sentence summary of this action for a pharmacy manager's dashboard.
    """
    return get_gemini_response(prompt)

def parse_signal_intent(agent_name: str, signal: dict):
    """Uses Gemini to map an unknown signal to a known agent method/intent."""
    if agent_name == "SOMA":
        intents = "cold_chain, scheduling"
    else:
        intents = "epidemic, expiry"
        
    prompt = f"""
    You are the {agent_name} agent. You received a signal that you don't recognize.
    Signal: {json.dumps(signal)}
    
    Map this signal to one of your known intents: {intents}.
    If it doesn't fit any, return 'unknown'.
    
    Output ONLY the intent name.
    """
    return get_gemini_response(prompt).lower().strip()

def extract_signal_data(agent_name: str, signal: dict):
    """Uses Gemini to extract flat key-value pairs from a potentially nested signal."""
    if agent_name == "SOMA":
        expected = "store_id (int), temp (float), duration_mins (int), hours_to_shift (int)"
    else:
        expected = "district (str), wow_growth (float), store_id (int), days_to_expiry (int), sales_velocity (float)"
        
    prompt = f"""
    You are a data extraction specialist for the {agent_name} agent.
    Given this signal: {json.dumps(signal)}
    
    Extract the following fields if they exist (or their equivalents): {expected}.
    
    CRITICAL: 
    - Convert text ratings (like 'low', 'medium', 'high') to numbers (0.2, 0.5, 0.8) for 'sales_velocity'.
    - Ensure all numerical fields are clean floats or ints.
    
    Return ONLY a raw JSON object with these flat keys. No markdown.
    """
    response = get_gemini_response(prompt)
    try:
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return {}
