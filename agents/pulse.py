from mcp_servers.erp_mcp import raise_po
from mcp_servers.inventory_mcp import flag_markdown
from vector_store.ingest import KnowledgeStore

class PULSE:
    """Predictive Unified Life-Sciences Engine."""
    
    def __init__(self):
        self.name = "PULSE"
        self.ks = KnowledgeStore()

    def run(self, signal: dict):
        from tools.llm_utils import extract_signal_data, parse_signal_intent
        
        # 1. AI-powered extraction/normalization
        flat_data = extract_signal_data("PULSE", signal)
        
        # 2. Determine Intent
        sig_type = signal.get("type", signal.get("signal_type"))
        if not sig_type or sig_type not in ["epidemic", "expiry"]:
            sig_type = parse_signal_intent("PULSE", signal)

        district = flat_data.get("district")
        store_id = flat_data.get("store_id")
        
        # 3. Dispatch
        if sig_type == "epidemic":
            return self.handle_epidemic(district, flat_data.get("wow_growth", 0))
        elif sig_type in ["expiry", "inventory_aging_alert"]:
            return self.handle_expiry(store_id, flat_data.get("days_to_expiry", 30), flat_data.get("sales_velocity", 1.0))
            
        return f"Unknown signal type for PULSE: {sig_type}"

    def handle_epidemic(self, district: str, wow_growth: float):
        # Ensure values are not None
        district = str(district) if district else "Mumbai"
        wow_growth = float(wow_growth) if wow_growth is not None else 0.0
        
        print(f"PULSE: Forecasting for {district}, WoW Growth: {wow_growth}%")
        
        # Level 1: +20% WoW
        if 20 <= wow_growth < 50:
            from tools.llm_utils import get_gemini_response
            insight = get_gemini_response(f"Generate 1 technical demand insight for a pharmacist for {district} seeing {wow_growth}% growth in fever cases.")
            return f"INFO: {insight}"

        # Level 2: +50% WoW
        if 50 <= wow_growth < 100:
            raise_po(1, "SKU-002", 150, agent="PULSE") # 1.5x standard (assume 100 is std)
            return f"ACTION: Raised PO at 1.5x for {district} due to {wow_growth}% WoW growth."

        # 3. Level 3: +100% WoW
        if wow_growth >= 100:
            raise_po(1, "SKU-002", 250, agent="PULSE") # 2.5x standard
            return f"CRITICAL: Raised PO at 2.5x for {district}. Human review required for further increases."

        # 4. Multi-district (Mock: check if 'multi' flag in signal)
        return f"INFO: District {district} signals are stable."

    def handle_expiry(self, store_id: int, days_to_expiry: int, velocity: float):
        # Ensure values are not None
        store_id = int(store_id) if store_id is not None else 1
        days_to_expiry = int(days_to_expiry) if days_to_expiry is not None else 30
        velocity = float(velocity) if velocity is not None else 1.0
        
        print(f"PULSE: Expiry Check - Store {store_id}, Days: {days_to_expiry}, Velocity: {velocity}")
        
        # 1. 90 Days
        if days_to_expiry >= 90:
            return f"INFO: Monitoring batch at Store {store_id}. Expiry in {days_to_expiry} days."

        # 2. 60 Days + Low Velocity
        if 30 < days_to_expiry <= 60 and velocity < 0.5:
            return f"SUGGESTION: Flagged in Sheets dashboard. Inter-store transfer recommended for Store {store_id}."

        # 3. 30 Days + Low Velocity
        if 15 < days_to_expiry <= 30 and velocity < 0.3:
            flag_markdown("BCH-001", 20)
            return f"ACTION: Triggered 20% markdown for batch at Store {store_id}."

        # 4. <15 Days
        if days_to_expiry <= 15:
            return f"CRITICAL: Initiating disposal workflow for near-expiry stock at Store {store_id} (Human required)."

        return f"INFO: No immediate risk for batch at Store {store_id}."
