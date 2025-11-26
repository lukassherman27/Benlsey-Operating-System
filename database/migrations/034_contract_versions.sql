-- Migration 034: Contract Versions Tracking
-- Created: 2025-11-26
-- Purpose: Track contract document versions and amendments

CREATE TABLE IF NOT EXISTS contract_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    project_code TEXT NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    version_type TEXT CHECK(version_type IN (
        'original',
        'amendment',
        'addendum',
        'change_order',
        'supplemental'
    )) DEFAULT 'original',

    -- Document details
    file_path TEXT,
    file_name TEXT,
    document_date DATE,
    effective_date DATE,

    -- Change tracking
    changes_summary TEXT,
    scope_changes TEXT,
    fee_changes TEXT,
    schedule_changes TEXT,

    -- Financial impact
    original_contract_value REAL,
    new_contract_value REAL,
    value_change REAL,

    -- Approval tracking
    status TEXT CHECK(status IN (
        'draft',
        'pending_review',
        'approved',
        'executed',
        'superseded'
    )) DEFAULT 'draft',
    approved_by TEXT,
    approved_date DATE,

    -- Provenance
    source_type TEXT DEFAULT 'manual',
    source_reference TEXT,
    created_by TEXT DEFAULT 'system',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- Indexes for contract_versions
CREATE INDEX IF NOT EXISTS idx_contract_version_project ON contract_versions(project_id);
CREATE INDEX IF NOT EXISTS idx_contract_version_code ON contract_versions(project_code);
CREATE INDEX IF NOT EXISTS idx_contract_version_number ON contract_versions(project_code, version_number);
CREATE INDEX IF NOT EXISTS idx_contract_version_status ON contract_versions(status);
CREATE INDEX IF NOT EXISTS idx_contract_version_date ON contract_versions(effective_date);

-- Unique constraint: one version number per project
CREATE UNIQUE INDEX IF NOT EXISTS idx_contract_version_unique
    ON contract_versions(project_code, version_number);

-- Trigger to update updated_at
CREATE TRIGGER IF NOT EXISTS trg_contract_version_updated
AFTER UPDATE ON contract_versions
FOR EACH ROW
BEGIN
    UPDATE contract_versions
    SET updated_at = CURRENT_TIMESTAMP
    WHERE version_id = NEW.version_id
    AND updated_at != CURRENT_TIMESTAMP;
END;

-- Trigger to mark previous version as superseded when new one is approved
CREATE TRIGGER IF NOT EXISTS trg_contract_version_supersede
AFTER UPDATE OF status ON contract_versions
FOR EACH ROW
WHEN NEW.status = 'executed' AND OLD.status != 'executed'
BEGIN
    UPDATE contract_versions
    SET status = 'superseded'
    WHERE project_code = NEW.project_code
    AND version_number < NEW.version_number
    AND status = 'executed';
END;

-- Calculate value_change automatically
CREATE TRIGGER IF NOT EXISTS trg_contract_version_value_calc
AFTER INSERT ON contract_versions
FOR EACH ROW
WHEN NEW.original_contract_value IS NOT NULL AND NEW.new_contract_value IS NOT NULL
BEGIN
    UPDATE contract_versions
    SET value_change = NEW.new_contract_value - NEW.original_contract_value
    WHERE version_id = NEW.version_id;
END;

-- View for current contract versions
CREATE VIEW IF NOT EXISTS v_current_contracts AS
SELECT
    cv.version_id,
    cv.project_code,
    p.project_name,
    cv.version_number,
    cv.version_type,
    cv.document_date,
    cv.effective_date,
    cv.new_contract_value AS current_value,
    cv.status,
    cv.changes_summary,
    cv.file_path
FROM contract_versions cv
JOIN projects p ON cv.project_id = p.project_id
WHERE cv.version_number = (
    SELECT MAX(version_number)
    FROM contract_versions
    WHERE project_code = cv.project_code
)
ORDER BY cv.project_code;

-- View for contract amendment history
CREATE VIEW IF NOT EXISTS v_contract_history AS
SELECT
    project_code,
    version_number,
    version_type,
    effective_date,
    changes_summary,
    COALESCE(value_change, 0) AS value_change,
    new_contract_value,
    status,
    approved_by,
    approved_date
FROM contract_versions
ORDER BY project_code, version_number;
