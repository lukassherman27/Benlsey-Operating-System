-- Migration 025: Add Provenance Tracking to CORRECT proposals table
-- Fixes the mistake of using proposal_tracker instead of proposals
-- Date: 2025-11-24

-- =============================================================================
-- STEP 1: Add provenance columns to proposals table
-- =============================================================================

-- Add source tracking
ALTER TABLE proposals ADD COLUMN source_type TEXT DEFAULT 'manual';
ALTER TABLE proposals ADD COLUMN source_reference TEXT;
ALTER TABLE proposals ADD COLUMN created_by TEXT DEFAULT 'system';
ALTER TABLE proposals ADD COLUMN updated_by TEXT;

-- Add field locking capability
ALTER TABLE proposals ADD COLUMN locked_fields TEXT; -- JSON array of protected fields
ALTER TABLE proposals ADD COLUMN locked_by TEXT;
ALTER TABLE proposals ADD COLUMN locked_at DATETIME;

-- =============================================================================
-- STEP 2: Create audit log table for proposals
-- =============================================================================

CREATE TABLE IF NOT EXISTS proposals_audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    project_code TEXT NOT NULL,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT NOT NULL,
    changed_at DATETIME DEFAULT (datetime('now')),
    change_reason TEXT,
    change_source TEXT, -- 'manual', 'ai', 'email_parser', 'import'

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE CASCADE
);

-- =============================================================================
-- STEP 3: Create indexes for query performance
-- =============================================================================

CREATE INDEX idx_proposals_audit_proposal_id ON proposals_audit_log(proposal_id);
CREATE INDEX idx_proposals_audit_project_code ON proposals_audit_log(project_code);
CREATE INDEX idx_proposals_audit_changed_at ON proposals_audit_log(changed_at);
CREATE INDEX idx_proposals_audit_field_name ON proposals_audit_log(field_name);
CREATE INDEX idx_proposals_audit_changed_by ON proposals_audit_log(changed_by);

-- =============================================================================
-- STEP 4: Create trigger for automatic audit logging
-- =============================================================================

CREATE TRIGGER IF NOT EXISTS log_proposals_changes
AFTER UPDATE ON proposals
FOR EACH ROW
BEGIN
    -- Log project_value changes
    INSERT INTO proposals_audit_log (
        proposal_id, project_code, field_name, old_value, new_value,
        changed_by, change_reason, change_source
    )
    SELECT NEW.proposal_id, NEW.project_code, 'project_value',
           CAST(OLD.project_value AS TEXT), CAST(NEW.project_value AS TEXT),
           COALESCE(NEW.updated_by, 'system'),
           NULL, -- change_reason captured separately
           COALESCE(NEW.source_type, 'manual')
    WHERE OLD.project_value != NEW.project_value OR (OLD.project_value IS NULL AND NEW.project_value IS NOT NULL);

    -- Log status changes
    INSERT INTO proposals_audit_log (
        proposal_id, project_code, field_name, old_value, new_value,
        changed_by, change_reason, change_source
    )
    SELECT NEW.proposal_id, NEW.project_code, 'status',
           OLD.status, NEW.status,
           COALESCE(NEW.updated_by, 'system'),
           NULL,
           COALESCE(NEW.source_type, 'manual')
    WHERE OLD.status != NEW.status OR (OLD.status IS NULL AND NEW.status IS NOT NULL);

    -- Log project_name changes
    INSERT INTO proposals_audit_log (
        proposal_id, project_code, field_name, old_value, new_value,
        changed_by, change_reason, change_source
    )
    SELECT NEW.proposal_id, NEW.project_code, 'project_name',
           OLD.project_name, NEW.project_name,
           COALESCE(NEW.updated_by, 'system'),
           NULL,
           COALESCE(NEW.source_type, 'manual')
    WHERE OLD.project_name != NEW.project_name OR (OLD.project_name IS NULL AND NEW.project_name IS NOT NULL);

    -- Log client_company changes
    INSERT INTO proposals_audit_log (
        proposal_id, project_code, field_name, old_value, new_value,
        changed_by, change_reason, change_source
    )
    SELECT NEW.proposal_id, NEW.project_code, 'client_company',
           OLD.client_company, NEW.client_company,
           COALESCE(NEW.updated_by, 'system'),
           NULL,
           COALESCE(NEW.source_type, 'manual')
    WHERE OLD.client_company != NEW.client_company OR (OLD.client_company IS NULL AND NEW.client_company IS NOT NULL);

    -- Log is_active_project changes (proposal became active project)
    INSERT INTO proposals_audit_log (
        proposal_id, project_code, field_name, old_value, new_value,
        changed_by, change_reason, change_source
    )
    SELECT NEW.proposal_id, NEW.project_code, 'is_active_project',
           CAST(OLD.is_active_project AS TEXT), CAST(NEW.is_active_project AS TEXT),
           COALESCE(NEW.updated_by, 'system'),
           'Proposal signed - became active project',
           COALESCE(NEW.source_type, 'manual')
    WHERE OLD.is_active_project != NEW.is_active_project;

    -- Log contract_signed_date changes
    INSERT INTO proposals_audit_log (
        proposal_id, project_code, field_name, old_value, new_value,
        changed_by, change_reason, change_source
    )
    SELECT NEW.proposal_id, NEW.project_code, 'contract_signed_date',
           OLD.contract_signed_date, NEW.contract_signed_date,
           COALESCE(NEW.updated_by, 'system'),
           NULL,
           COALESCE(NEW.source_type, 'manual')
    WHERE OLD.contract_signed_date != NEW.contract_signed_date OR (OLD.contract_signed_date IS NULL AND NEW.contract_signed_date IS NOT NULL);
END;

-- =============================================================================
-- STEP 5: Mark migration as complete
-- =============================================================================

INSERT INTO schema_migrations (migration_file, applied_at)
VALUES ('025_proposals_provenance_correct.sql', datetime('now'));
