-- Migration: Create proposal_tracker table
-- This table tracks the status of all active proposals for the Proposal Tracker Dashboard

CREATE TABLE IF NOT EXISTS proposal_tracker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code TEXT NOT NULL UNIQUE,
    project_name TEXT NOT NULL,
    project_value REAL DEFAULT 0,
    country TEXT,

    -- Status tracking
    current_status TEXT NOT NULL DEFAULT 'First Contact',
    last_week_status TEXT,
    status_changed_date TEXT,
    days_in_current_status INTEGER DEFAULT 0,

    -- Important dates
    first_contact_date TEXT,
    proposal_sent_date TEXT,

    -- Proposal flags
    proposal_sent INTEGER DEFAULT 0,

    -- Notes and context
    project_summary TEXT,
    current_remark TEXT,
    latest_email_context TEXT,
    waiting_on TEXT,
    next_steps TEXT,

    -- Email integration
    last_email_date TEXT,

    -- Audit fields
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    -- Constraints
    CHECK (current_status IN ('First Contact', 'Drafting', 'Proposal Sent', 'On Hold', 'Archived', 'Contract Signed')),
    CHECK (proposal_sent IN (0, 1)),
    CHECK (project_value >= 0)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_proposal_tracker_status ON proposal_tracker(current_status);
CREATE INDEX IF NOT EXISTS idx_proposal_tracker_country ON proposal_tracker(country);
CREATE INDEX IF NOT EXISTS idx_proposal_tracker_project_code ON proposal_tracker(project_code);
CREATE INDEX IF NOT EXISTS idx_proposal_tracker_days ON proposal_tracker(days_in_current_status);

-- Create status history table
CREATE TABLE IF NOT EXISTS proposal_tracker_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_tracker_id INTEGER NOT NULL,
    project_code TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    remark TEXT,
    changed_by TEXT,
    changed_on TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (proposal_tracker_id) REFERENCES proposal_tracker(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_status_history_project ON proposal_tracker_status_history(project_code);
CREATE INDEX IF NOT EXISTS idx_status_history_date ON proposal_tracker_status_history(changed_on);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_proposal_tracker_timestamp
AFTER UPDATE ON proposal_tracker
BEGIN
    UPDATE proposal_tracker SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Create trigger to log status changes
CREATE TRIGGER IF NOT EXISTS log_proposal_status_change
AFTER UPDATE OF current_status ON proposal_tracker
WHEN OLD.current_status != NEW.current_status
BEGIN
    INSERT INTO proposal_tracker_status_history (
        proposal_tracker_id,
        project_code,
        old_status,
        new_status,
        remark,
        changed_by
    ) VALUES (
        NEW.id,
        NEW.project_code,
        OLD.current_status,
        NEW.current_status,
        NEW.current_remark,
        'system'
    );

    UPDATE proposal_tracker
    SET status_changed_date = datetime('now'),
        days_in_current_status = 0,
        last_week_status = OLD.current_status
    WHERE id = NEW.id;
END;
