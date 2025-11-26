-- Migration 024: Add Provenance Tracking to proposal_tracker
-- Date: 2025-11-24
-- Purpose: Enable data source tracking, field locking, and audit trails for proposal tracker

-- Add provenance columns to proposal_tracker table
ALTER TABLE proposal_tracker ADD COLUMN source_type TEXT
    CHECK(source_type IN ('manual', 'import', 'ai', 'email_parser', NULL));

ALTER TABLE proposal_tracker ADD COLUMN source_reference TEXT;

ALTER TABLE proposal_tracker ADD COLUMN created_by TEXT DEFAULT 'system';

ALTER TABLE proposal_tracker ADD COLUMN updated_by TEXT;

ALTER TABLE proposal_tracker ADD COLUMN locked_fields TEXT;  -- JSON array: ["project_value", "current_status"]

ALTER TABLE proposal_tracker ADD COLUMN locked_by TEXT;

ALTER TABLE proposal_tracker ADD COLUMN locked_at DATETIME;

-- Create audit log table for proposal_tracker changes
CREATE TABLE IF NOT EXISTS proposal_tracker_audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_tracker_id INTEGER NOT NULL,
    project_code TEXT NOT NULL,

    -- What changed
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,

    -- Who and when
    changed_by TEXT NOT NULL,
    changed_at DATETIME DEFAULT (datetime('now')),

    -- Why (optional)
    change_reason TEXT,

    -- Provenance
    change_source TEXT CHECK(change_source IN ('manual', 'import', 'ai', 'email_parser', 'system')),

    FOREIGN KEY (proposal_tracker_id) REFERENCES proposal_tracker(id) ON DELETE CASCADE
);

-- Index for performance
CREATE INDEX idx_audit_log_proposal_id ON proposal_tracker_audit_log(proposal_tracker_id);
CREATE INDEX idx_audit_log_project_code ON proposal_tracker_audit_log(project_code);
CREATE INDEX idx_audit_log_changed_at ON proposal_tracker_audit_log(changed_at);
CREATE INDEX idx_audit_log_field_name ON proposal_tracker_audit_log(field_name);

-- Create trigger to log all changes to proposal_tracker
CREATE TRIGGER log_proposal_tracker_changes
AFTER UPDATE ON proposal_tracker
FOR EACH ROW
BEGIN
    -- Log project_value changes
    INSERT INTO proposal_tracker_audit_log (
        proposal_tracker_id, project_code, field_name, old_value, new_value,
        changed_by, change_source
    )
    SELECT
        NEW.id,
        NEW.project_code,
        'project_value',
        CAST(OLD.project_value AS TEXT),
        CAST(NEW.project_value AS TEXT),
        COALESCE(NEW.updated_by, 'system'),
        COALESCE(NEW.source_type, 'system')
    WHERE OLD.project_value != NEW.project_value OR (OLD.project_value IS NULL AND NEW.project_value IS NOT NULL);

    -- Log status changes
    INSERT INTO proposal_tracker_audit_log (
        proposal_tracker_id, project_code, field_name, old_value, new_value,
        changed_by, change_source
    )
    SELECT
        NEW.id,
        NEW.project_code,
        'current_status',
        OLD.current_status,
        NEW.current_status,
        COALESCE(NEW.updated_by, 'system'),
        COALESCE(NEW.source_type, 'system')
    WHERE OLD.current_status != NEW.current_status;

    -- Log project_name changes
    INSERT INTO proposal_tracker_audit_log (
        proposal_tracker_id, project_code, field_name, old_value, new_value,
        changed_by, change_source
    )
    SELECT
        NEW.id,
        NEW.project_code,
        'project_name',
        OLD.project_name,
        NEW.project_name,
        COALESCE(NEW.updated_by, 'system'),
        COALESCE(NEW.source_type, 'system')
    WHERE OLD.project_name != NEW.project_name;

    -- Log country changes
    INSERT INTO proposal_tracker_audit_log (
        proposal_tracker_id, project_code, field_name, old_value, new_value,
        changed_by, change_source
    )
    SELECT
        NEW.id,
        NEW.project_code,
        'country',
        OLD.country,
        NEW.country,
        COALESCE(NEW.updated_by, 'system'),
        COALESCE(NEW.source_type, 'system')
    WHERE (OLD.country != NEW.country) OR (OLD.country IS NULL AND NEW.country IS NOT NULL) OR (OLD.country IS NOT NULL AND NEW.country IS NULL);
END;

-- Record this migration
INSERT INTO schema_migrations (version, name, description)
VALUES (24, '024_proposal_tracker_provenance', 'Add provenance tracking and audit log to proposal_tracker table');
