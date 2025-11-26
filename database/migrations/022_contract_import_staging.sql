-- Migration 022: Contract Import Staging and Approval System
-- Date: 2025-11-20
-- Purpose: Add staging tables for contract import approval workflow

-- ============================================================================
-- contract_imports_staging: Holds pending contract imports for review
-- ============================================================================

CREATE TABLE IF NOT EXISTS contract_imports_staging (
    import_id TEXT PRIMARY KEY,                    -- Unique import ID (e.g., "IMP-20251120-001")
    project_code TEXT NOT NULL,                    -- Project code being imported
    import_type TEXT NOT NULL,                     -- 'new', 'update', 'addendum'
    status TEXT DEFAULT 'pending',                 -- 'pending', 'approved', 'rejected', 'edited'

    -- Contract metadata (staged values)
    client_name TEXT,
    total_fee_usd REAL,
    contract_duration_months INTEGER,
    contract_date TEXT,
    payment_terms_days INTEGER,
    late_payment_interest_rate REAL,
    stop_work_days_threshold INTEGER,
    restart_fee_percentage REAL,

    -- Additional context
    contract_notes TEXT,                           -- Special notes from import
    pdf_source_path TEXT,                          -- Source PDF path if applicable
    imported_by TEXT,                              -- Who initiated the import

    -- Fee breakdown (JSON array of phase entries)
    fee_breakdown_json TEXT,                       -- JSON: [{"discipline": "Landscape", "phase": "Mobilization", "fee": 50000, "pct": 20.0}, ...]

    -- Diff information (JSON)
    changes_preview_json TEXT,                     -- JSON showing what will change

    -- Review and approval
    reviewed_by TEXT,                              -- Who reviewed
    review_notes TEXT,                             -- Notes from reviewer
    approved_at TEXT,                              -- When approved
    rejected_at TEXT,                              -- When rejected
    rejection_reason TEXT,                         -- Why rejected

    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_staging_project_code ON contract_imports_staging(project_code);
CREATE INDEX IF NOT EXISTS idx_staging_status ON contract_imports_staging(status);
CREATE INDEX IF NOT EXISTS idx_staging_created ON contract_imports_staging(created_at);

-- ============================================================================
-- contract_import_audit: Complete audit trail of all import actions
-- ============================================================================

CREATE TABLE IF NOT EXISTS contract_import_audit (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_id TEXT NOT NULL,                       -- Links to contract_imports_staging
    project_code TEXT NOT NULL,
    action TEXT NOT NULL,                          -- 'staged', 'approved', 'rejected', 'edited', 'committed'

    -- Action details
    performed_by TEXT,                             -- Who performed the action
    action_notes TEXT,                             -- Notes about the action

    -- Snapshot of data at time of action (JSON)
    data_snapshot_json TEXT,                       -- Full snapshot of import data

    -- Changes made (for edit actions)
    field_changes_json TEXT,                       -- JSON: {"field": {"old": value, "new": value}}

    -- Timestamp
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (import_id) REFERENCES contract_imports_staging(import_id)
);

CREATE INDEX IF NOT EXISTS idx_audit_import_id ON contract_import_audit(import_id);
CREATE INDEX IF NOT EXISTS idx_audit_project_code ON contract_import_audit(project_code);
CREATE INDEX IF NOT EXISTS idx_audit_action ON contract_import_audit(action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON contract_import_audit(created_at);

-- ============================================================================
-- Migration tracking
-- ============================================================================

INSERT INTO schema_migrations (version, name, description, applied_at)
VALUES (22, '022_contract_import_staging', 'Contract import staging and approval system', datetime('now'));
