-- Migration 013: Pending Contracts Review Queue
-- Creates a queue for contracts detected in emails that need AI extraction

CREATE TABLE IF NOT EXISTS pending_contract_reviews (
    review_id TEXT PRIMARY KEY,
    email_id INTEGER,
    project_code TEXT,
    contract_file_path TEXT,
    detected_date TEXT,
    status TEXT DEFAULT 'pending', -- pending, in_progress, completed, skipped
    contract_type TEXT, -- new, extension, addendum
    client_name TEXT,
    detected_keywords TEXT, -- JSON array of keywords that triggered detection
    priority INTEGER DEFAULT 0, -- Higher = more urgent
    notes TEXT,
    reviewed_by TEXT,
    reviewed_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (email_id) REFERENCES emails(email_id)
);

CREATE INDEX IF NOT EXISTS idx_pending_contracts_status
ON pending_contract_reviews(status);

CREATE INDEX IF NOT EXISTS idx_pending_contracts_detected_date
ON pending_contract_reviews(detected_date);

CREATE INDEX IF NOT EXISTS idx_pending_contracts_priority
ON pending_contract_reviews(priority DESC, detected_date DESC);
