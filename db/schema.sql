-- SQLite Schema for PharmaIQ (Refined)

-- Drug Catalog
CREATE TABLE IF NOT EXISTS drug_catalog (
    sku_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    schedule_class TEXT, -- H1, X, etc.
    cold_chain_req BOOLEAN DEFAULT FALSE,
    reorder_lead_days INTEGER DEFAULT 7
);

-- Stores Table
CREATE TABLE IF NOT EXISTS stores (
    store_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    tier TEXT, -- Tier 1, 2, 3
    zone TEXT, -- North, South, East, West
    manager_name TEXT,
    email TEXT,
    phone TEXT
);

-- Inventory Table
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id TEXT,
    store_id INTEGER,
    qty INTEGER DEFAULT 0,
    expiry_date DATE NOT NULL,
    batch_no TEXT NOT NULL,
    cost_price DECIMAL(10, 2),
    status TEXT DEFAULT 'active', -- active, quarantined, near-expiry, stock-out
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (sku_id) REFERENCES drug_catalog(sku_id)
);

-- Temperature Logs
CREATE TABLE IF NOT EXISTS temperature_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER,
    unit_id TEXT NOT NULL, -- e.g., FRIDGE-01
    temp_c DECIMAL(5, 2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    breach_flag BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- Staff Schedules
CREATE TABLE IF NOT EXISTS staff_schedules (
    shift_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER,
    staff_id TEXT NOT NULL,
    role TEXT NOT NULL,
    start_dt DATETIME NOT NULL,
    end_dt DATETIME NOT NULL,
    pharmacist_flag BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL, -- SOMA, PULSE
    store_id INTEGER,
    type TEXT NOT NULL, -- cold_chain, expiry, demand, scheduling
    severity TEXT NOT NULL, -- info, warning, critical
    action_taken TEXT,
    human_needed BOOLEAN DEFAULT FALSE,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- Epidemic Signals (IDSP)
CREATE TABLE IF NOT EXISTS epidemic_signals (
    signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    district TEXT NOT NULL,
    disease TEXT NOT NULL,
    case_count INTEGER,
    source TEXT,
    date DATE DEFAULT (DATE('now'))
);

-- Purchase Orders (ERP)
CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER,
    sku_id TEXT,
    qty INTEGER,
    trigger_agent TEXT, -- SOMA, PULSE
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (sku_id) REFERENCES drug_catalog(sku_id)
);

-- Keep forecasts for PULSE output flexibility
CREATE TABLE IF NOT EXISTS forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER,
    sku_id TEXT,
    predicted_demand INTEGER,
    confidence_score DECIMAL(3, 2),
    signals TEXT,
    forecast_date DATE DEFAULT (DATE('now')),
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (sku_id) REFERENCES drug_catalog(sku_id)
);
