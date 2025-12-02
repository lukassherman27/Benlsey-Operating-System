-- Migration 031: Proposal Lifecycle Triggers
-- Created: 2025-11-26
-- Purpose: Add auto-logging triggers for proposal status changes
-- Note: proposal_status_history table already exists from migration 030

-- Trigger: Auto-log status changes on proposals table
-- Note: The column is 'status' (not 'proposal_status')
CREATE TRIGGER IF NOT EXISTS trg_proposals_status_change
AFTER UPDATE OF status ON proposals
FOR EACH ROW
WHEN OLD.status IS NOT NEW.status
BEGIN
    INSERT INTO proposal_status_history (
        proposal_id,
        project_code,
        old_status,
        new_status,
        status_date,
        changed_by,
        notes,
        source
    ) VALUES (
        NEW.proposal_id,
        NEW.project_code,
        OLD.status,
        NEW.status,
        DATE('now'),
        'system',
        'Auto-logged: Status changed from "' || COALESCE(OLD.status, 'NULL') || '" to "' || NEW.status || '"',
        'trigger'
    );
END;

-- View for proposal lifecycle analysis
CREATE VIEW IF NOT EXISTS v_proposal_lifecycle AS
SELECT
    p.proposal_id,
    p.project_code,
    p.project_name,
    p.status,
    p.last_contact_date,
    psh.old_status AS previous_status,
    psh.status_date AS last_change_date,
    psh.source AS change_source,
    julianday('now') - julianday(COALESCE(p.last_contact_date, p.created_at)) AS days_in_current_status,
    (SELECT COUNT(*) FROM proposal_status_history WHERE proposal_id = p.proposal_id) AS total_status_changes
FROM proposals p
LEFT JOIN proposal_status_history psh ON p.proposal_id = psh.proposal_id
    AND psh.status_date = (
        SELECT MAX(status_date)
        FROM proposal_status_history
        WHERE proposal_id = p.proposal_id
    )
ORDER BY p.project_code;
