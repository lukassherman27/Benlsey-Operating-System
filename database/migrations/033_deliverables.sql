-- Migration 033: Deliverables Enhancement
-- Created: 2025-11-26
-- Purpose: Enhance deliverables table with assignment tracking
-- Note: deliverables table already exists - only adding missing columns

-- Add missing columns to deliverables table
ALTER TABLE deliverables ADD COLUMN title TEXT;
ALTER TABLE deliverables ADD COLUMN assigned_pm TEXT;
ALTER TABLE deliverables ADD COLUMN description TEXT;
ALTER TABLE deliverables ADD COLUMN priority TEXT DEFAULT 'normal';
ALTER TABLE deliverables ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Populate title from deliverable_name for existing records
UPDATE deliverables SET title = deliverable_name WHERE title IS NULL;

-- Indexes on new columns
CREATE INDEX IF NOT EXISTS idx_deliverable_assigned_pm ON deliverables(assigned_pm);
CREATE INDEX IF NOT EXISTS idx_deliverable_status_due ON deliverables(status, due_date);
CREATE INDEX IF NOT EXISTS idx_deliverable_priority ON deliverables(priority);

-- Trigger to update updated_at on changes
CREATE TRIGGER IF NOT EXISTS trg_deliverable_updated
AFTER UPDATE ON deliverables
FOR EACH ROW
BEGIN
    UPDATE deliverables
    SET updated_at = CURRENT_TIMESTAMP
    WHERE deliverable_id = NEW.deliverable_id
    AND updated_at != CURRENT_TIMESTAMP;
END;

-- View for deliverables dashboard
CREATE VIEW IF NOT EXISTS v_deliverables_dashboard AS
SELECT
    d.deliverable_id,
    d.project_code,
    p.project_name,
    COALESCE(d.title, d.deliverable_name) AS title,
    d.deliverable_type,
    d.phase,
    d.due_date,
    d.submitted_date,
    d.approved_date,
    d.status,
    d.assigned_pm,
    d.priority,
    d.revision_number,
    CASE
        WHEN d.status = 'approved' THEN 'completed'
        WHEN d.status = 'pending' AND d.due_date < DATE('now') THEN 'overdue'
        WHEN d.status = 'pending' AND d.due_date <= DATE('now', '+7 days') THEN 'due_soon'
        ELSE d.status
    END AS urgency,
    julianday(d.due_date) - julianday('now') AS days_until_due
FROM deliverables d
LEFT JOIN projects p ON d.project_id = p.project_id
ORDER BY
    CASE d.status WHEN 'pending' THEN 0 WHEN 'submitted' THEN 1 ELSE 2 END,
    d.due_date;

-- View for PM workload
CREATE VIEW IF NOT EXISTS v_pm_deliverable_workload AS
SELECT
    assigned_pm,
    COUNT(*) AS total_deliverables,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_count,
    SUM(CASE WHEN status = 'pending' AND due_date < DATE('now') THEN 1 ELSE 0 END) AS overdue_count,
    SUM(CASE WHEN status = 'pending' AND due_date <= DATE('now', '+7 days') THEN 1 ELSE 0 END) AS due_this_week
FROM deliverables
WHERE assigned_pm IS NOT NULL
GROUP BY assigned_pm
ORDER BY overdue_count DESC, due_this_week DESC;
