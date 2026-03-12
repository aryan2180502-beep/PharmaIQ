import json
import os
from backend.tools.llm_utils import get_gemini_response

def generate_signals():
    """Generates dynamic test signals using Gemini."""
    print("AI_TEST_GEN: Requesting diverse operational signals from Gemini...")
    
    prompt_path = "prompts/test_data_gen.txt"
    with open(prompt_path, "r") as f:
        prompt = f.read()
    
    response = get_gemini_response(prompt)
    
    # Try to parse the response as JSON
    try:
        # Strip potential markdown backticks if Gemini ignored the 'raw' instruction
        clean_response = response.strip().replace("```json", "").replace("```", "").strip()
        signals = json.loads(clean_response)
        print(f"AI_TEST_GEN: Successfully generated {len(signals)} signals.")
        return signals
    except Exception as e:
        print(f"AI_TEST_GEN: Error parsing Gemini response: {str(e)}")
        print(f"AI_TEST_GEN: Raw response: {response}")
        # Fallback to a single dummy signal if AI fails
        return [{"type": "cold_chain", "store_id": 1, "temp": 5.0}]

if __name__ == "__main__":
    signals = generate_signals()
    print(json.dumps(signals, indent=2))
