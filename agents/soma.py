from mcp_servers.iot_mcp import trigger_alert
from mcp_servers.hrms_mcp import update_shift
from mcp_servers.erp_mcp import quarantine_batch
from vector_store.ingest import KnowledgeStore
from tools.llm_utils import summarize_action

class SOMA:
    """Store Operations & Monitoring Agent."""
    
    def __init__(self):
        self.name = "SOMA"
        self.ks = KnowledgeStore()

    def run(self, signal: dict):
        from tools.llm_utils import extract_signal_data, parse_signal_intent
        
        # 1. AI-powered extraction/normalization
        flat_data = extract_signal_data("SOMA", signal)
        
        # 2. Determine Intent
        sig_type = signal.get("type", signal.get("signal_type"))
        if not sig_type or sig_type not in ["cold_chain", "scheduling"]:
            sig_type = parse_signal_intent("SOMA", signal)

        store_id = flat_data.get("store_id")
        
        # 3. Dispatch
        if sig_type == "cold_chain":
            return self.handle_cold_chain(store_id, flat_data.get("temp"), flat_data.get("duration_mins", 0))
        elif sig_type == "scheduling":
            return self.handle_scheduling(store_id, flat_data.get("hours_to_shift", 48))
            
        return f"Unknown signal type for SOMA: {sig_type}"

    def handle_cold_chain(self, store_id: int, temp: float, duration: int):
        # Ensure values are not None
        temp = float(temp) if temp is not None else 5.0
        duration = int(duration) if duration is not None else 0
        store_id = int(store_id) if store_id is not None else 1
        
        print(f"SOMA: Analyzing Cold Chain - Store {store_id}, Temp: {temp}°C, Duration: {duration} mins")
        
        # 1. Normal Range
        if 2.0 <= temp <= 8.0:
            return f"INFO: Store {store_id} temperature stable at {temp}°C."

        # 2. Level 1 Breach (8-12°C, <15 mins)
        if 8.0 < temp <= 12.0 and duration < 15:
            trigger_alert(store_id, f"Temporary excursion ({temp}°C) for {duration} mins.", severity="warning")
            return f"ALERT: Excursion detected at Store {store_id}. Manager notified via Sheets."

        # 3. Level 2 Breach (>12°C or >15 mins at >8°C)
        if temp > 12.0 or duration >= 15:
            # Check for repetition (Mock: check alerts table for last 7 days)
            # For demo, we'll simulate a 'repeated' breach if store_id is 1
            if store_id == 1:
                trigger_alert(store_id, "REPEATED BREACH: 2nd in 7 days. Escalating to CDSCO workflow.", severity="critical")
                return f"CRITICAL: Repeated breach at Store {store_id}. Human review + CDSCO workflow triggered."
            
            quarantine_batch(f"BCH-{store_id}-COLD-0", f"Quarantined due to {temp}°C breach for {duration} mins.")
            trigger_alert(store_id, f"Quarantine initiated for {temp}°C breach.", severity="critical")
            
            # Use Gemini to generate a professional summary
            summary = summarize_action("SOMA", f"Quarantined cold-chain batches at Store {store_id}", f"Temperature: {temp}, Duration: {duration}")
            return f"ACTION: {summary}"

        return f"INFO: Signal processed for Store {store_id}."

    def handle_scheduling(self, store_id: int, hours_to_shift: int):
        # Ensure values are not None
        store_id = int(store_id) if store_id is not None else 1
        hours_to_shift = int(hours_to_shift) if hours_to_shift is not None else 48
        
        print(f"SOMA: Checking Staffing - Store {store_id}, Timing: {hours_to_shift} hours ahead")
        
        # 1. Schedule H coverage gap (High Priority)
        # Mock: if store_id 2, assume Schedule H gap
        if store_id == 2:
            return f"CRITICAL: Schedule H coverage gap at Store {store_id}. Immediate escalation to Sheets row initiated."

        # 2. Immediate Gap (<24hrs)
        if hours_to_shift < 24:
            update_shift(store_id, "STAFF-999 (Relief)", "Pharmacist", "2024-03-21 09:00:00", "2024-03-21 17:00:00")
            return f"ACTION: Auto-confirmed relief pharmacist for Store {store_id} (<24hr gap)."

        # 3. Future Gap (>24hrs)
        if hours_to_shift >= 24:
            return f"SUGGESTION: Found gap at Store {store_id} (>24hrs ahead). Suggesting replacement via Sheets."

        return f"INFO: No immediate staffing actions for Store {store_id}."
