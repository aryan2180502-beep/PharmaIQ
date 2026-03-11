import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "db/pharmaiq.db"
SCHEMA_PATH = "db/schema.sql"

DRUG_CATALOG = [
    ("SKU-001", "Insulin Glargine", "Schedule H", True, 3),
    ("SKU-002", "Amoxicillin 500mg", "Schedule H1", False, 7),
    ("SKU-003", "Paracetamol 650mg", "OTC", False, 5),
    ("SKU-004", "Dextromethorphan", "OTC", False, 5),
    ("SKU-005", "Vaxigrip Tetra", "Schedule H", True, 10),
    ("SKU-006", "Metformin 500mg", "Schedule G", False, 7),
    ("SKU-007", "Azithromycin 500mg", "Schedule H1", False, 7),
    ("SKU-008", "Pantoprazole 40mg", "Schedule H", False, 5),
]

STORES = [
    ("South Mumbai Hub", "Mumbai", "Tier 1", "South", "Dr. Rajesh"),
    ("Bandra West Clinic", "Mumbai", "Tier 1", "West", "Dr. Sneha"),
    ("Bengaluru Central", "Bengaluru", "Tier 1", "Central", "Dr. Amit"),
    ("Indiranagar Express", "Bengaluru", "Tier 2", "East", "Dr. Priya"),
    ("Delhi GK Store", "Delhi", "Tier 1", "South", "Dr. Vikram"),
    ("Gurgaon Sector 29", "Delhi NCR", "Tier 2", "North", "Dr. Ananya"),
    ("Chennai OMR Square", "Chennai", "Tier 1", "South", "Dr. Karthik"),
    ("Hyderabad Jubilee", "Hyderabad", "Tier 1", "West", "Dr. Lakshmi"),
    ("Pune Kothrud Mall", "Pune", "Tier 2", "West", "Dr. Rahul"),
    ("Kolkata Park St", "Kolkata", "Tier 1", "East", "Dr. Debraj"),
]

EPIDEMIC_SIGNALS = [
    ("Mumbai", "Dengue", 45, "IDSP-MUM-01"),
    ("Bengaluru", "Viral Infection", 120, "IDSP-BLR-04"),
    ("Delhi", "Respiratory Distress", 340, "IDSP-DEL-09"),
]

PHARMACISTS = ["STAFF-001", "STAFF-002", "STAFF-003", "STAFF-004", "STAFF-005"]

def seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Reset tables to ensure refined schema is applied
    cursor.execute("DROP TABLE IF EXISTS forecasts")
    cursor.execute("DROP TABLE IF EXISTS purchase_orders")
    cursor.execute("DROP TABLE IF EXISTS epidemic_signals")
    cursor.execute("DROP TABLE IF EXISTS alerts")
    cursor.execute("DROP TABLE IF EXISTS staff_schedules")
    cursor.execute("DROP TABLE IF EXISTS temperature_logs")
    cursor.execute("DROP TABLE IF EXISTS inventory")
    cursor.execute("DROP TABLE IF EXISTS stores")
    cursor.execute("DROP TABLE IF EXISTS drug_catalog")

    # Re-run schema
    with open(SCHEMA_PATH, 'r') as f:
        cursor.executescript(f.read())

    # 1. Seed Drug Catalog
    cursor.executemany("""
        INSERT INTO drug_catalog (sku_id, name, schedule_class, cold_chain_req, reorder_lead_days)
        VALUES (?, ?, ?, ?, ?)
    """, DRUG_CATALOG)

    # 2. Seed Stores
    for name, city, tier, zone, mgr in STORES:
        cursor.execute("""
            INSERT INTO stores (name, city, tier, zone, manager_name) 
            VALUES (?, ?, ?, ?, ?)
        """, (name, city, tier, zone, mgr))
    
    conn.commit()
    print(f"Seeded {len(STORES)} stores and {len(DRUG_CATALOG)} drugs.")

    # 3. Seed Inventory
    for store_id in range(1, 11):
        for sku_id, name, sched, is_cold, lead in DRUG_CATALOG:
            for i in range(2):
                batch_no = f"BCH-{store_id}-{sku_id[-3:]}-{i}"
                qty = random.randint(20, 200)
                price = random.uniform(50, 1500)
                
                if random.random() < 0.15:
                    expiry = datetime.now() + timedelta(days=random.randint(5, 30))
                else:
                    expiry = datetime.now() + timedelta(days=random.randint(100, 500))
                
                cursor.execute("""
                    INSERT INTO inventory (sku_id, store_id, qty, expiry_date, batch_no, cost_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (sku_id, store_id, qty, expiry.date(), batch_no, round(price, 2)))

    # 4. Seed Temperature Logs
    for store_id in range(1, 11):
        for hour in range(12):
            ts = datetime.now() - timedelta(hours=hour)
            temp = random.uniform(2.5, 7.5)
            # Add one breach for demo
            if store_id == 1 and hour == 0:
                temp = 12.8
            
            cursor.execute("""
                INSERT INTO temperature_logs (store_id, unit_id, temp_c, timestamp, breach_flag)
                VALUES (?, ?, ?, ?, ?)
            """, (store_id, "FRIDGE-01", round(temp, 2), ts, temp > 8.0))

    # 5. Seed Staff Schedules
    for store_id in range(1, 11):
        for d in range(2):
            dt = datetime.now() + timedelta(days=d)
            cursor.execute("""
                INSERT INTO staff_schedules (store_id, staff_id, role, start_dt, end_dt, pharmacist_flag)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (store_id, random.choice(PHARMACISTS), "Pharmacist", 
                  dt.replace(hour=9), dt.replace(hour=17), True))

    # 6. Seed Epidemic Signals
    cursor.executemany("""
        INSERT INTO epidemic_signals (district, disease, case_count, source)
        VALUES (?, ?, ?, ?)
    """, EPIDEMIC_SIGNALS)

    conn.commit()
    conn.close()
    print("Refined database seeding complete.")

if __name__ == "__main__":
    seed()

if __name__ == "__main__":
    seed()
