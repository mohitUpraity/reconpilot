
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS merchants (
    merchant_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS financial_records (
    record_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    source TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    record_type TEXT NOT NULL,
    event_date TEXT,
    amount INTEGER,
    currency TEXT,
    direction TEXT,
    customer_name TEXT,
    reference TEXT,
    description TEXT,
    raw_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (merchant_id, source, source_record_id),
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
);

CREATE TABLE IF NOT EXISTS reconciliation_cases (
    case_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    case_type TEXT NOT NULL,
    status TEXT NOT NULL,
    confidence REAL,
    primary_record_id TEXT,
    matched_record_id TEXT,
    decision_source TEXT,
    reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
);

CREATE TABLE IF NOT EXISTS reconciliation_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL,
    from_record_id TEXT NOT NULL,
    to_record_id TEXT NOT NULL,
    link_type TEXT NOT NULL,
    confidence REAL,
    decision_source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(case_id, from_record_id, to_record_id, link_type),
    FOREIGN KEY (case_id) REFERENCES reconciliation_cases(case_id),
    FOREIGN KEY (from_record_id) REFERENCES financial_records(record_id),
    FOREIGN KEY (to_record_id) REFERENCES financial_records(record_id)
);

CREATE TABLE IF NOT EXISTS exceptions (
    exception_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL,
    assigned_to TEXT,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    FOREIGN KEY (case_id) REFERENCES reconciliation_cases(case_id)
);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id TEXT NOT NULL,
    case_id TEXT,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
);

CREATE TABLE IF NOT EXISTS webhook_events (
    event_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    event_type TEXT NOT NULL,
    signature_valid INTEGER NOT NULL,
    processed INTEGER NOT NULL DEFAULT 0,
    payload_json TEXT NOT NULL,
    received_at TEXT NOT NULL,
    processed_at TEXT,
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
);

CREATE INDEX IF NOT EXISTS idx_financial_records_source
    ON financial_records(merchant_id, source, record_type);

CREATE INDEX IF NOT EXISTS idx_cases_status
    ON reconciliation_cases(merchant_id, status);

CREATE INDEX IF NOT EXISTS idx_audit_case
    ON audit_events(case_id);
