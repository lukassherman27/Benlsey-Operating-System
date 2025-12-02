-- Migration 013: Automated Proposal Tracker System
-- Tracks proposal status, emails, context for automated weekly reports

-- Enhanced proposal tracking table
CREATE TABLE IF NOT EXISTS proposal_tracker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code TEXT UNIQUE NOT NULL,
    project_name TEXT NOT NULL,
    project_value REAL DEFAULT 0,
    country TEXT,

    -- Status tracking
    current_status TEXT CHECK(current_status IN (
        'First Contact',
        'Drafting',
        'Proposal Sent',
        'On Hold',
        'Archived',
        'Contract Signed'
    )) DEFAULT 'First Contact',
    last_week_status TEXT,
    status_changed_date TEXT,
    days_in_current_status INTEGER DEFAULT 0,

    -- Key dates
    first_contact_date TEXT,
    proposal_sent_date TEXT,
    proposal_sent BOOLEAN DEFAULT 0,

    -- Context and notes (auto-populated from emails)
    current_remark TEXT,
    project_summary TEXT,
    latest_email_context TEXT,
    waiting_on TEXT,
    next_steps TEXT,

    -- Tracking
    last_email_date TEXT,
    last_email_id INTEGER,
    is_active BOOLEAN DEFAULT 1,

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    last_synced_at TEXT,

    FOREIGN KEY (project_code) REFERENCES projects(project_code),
    FOREIGN KEY (last_email_id) REFERENCES emails(id)
);

-- Email-to-proposal intelligence mapping
CREATE TABLE IF NOT EXISTS proposal_email_intelligence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,
    project_code TEXT NOT NULL,

    -- Extracted intelligence
    status_update TEXT,  -- Did this email change status?
    key_information TEXT,  -- Important info extracted
    action_items TEXT,  -- Action items mentioned
    client_sentiment TEXT,  -- Positive/Negative/Neutral
    confidence_score REAL DEFAULT 0.0,

    -- Context
    email_subject TEXT,
    email_date TEXT,
    email_from TEXT,
    email_to TEXT,
    email_snippet TEXT,

    -- Processing
    processed_at TEXT DEFAULT (datetime('now')),
    ai_model_used TEXT DEFAULT 'claude-3-5-sonnet-20241022',

    FOREIGN KEY (email_id) REFERENCES emails(id),
    FOREIGN KEY (project_code) REFERENCES proposal_tracker(project_code)
);

-- Status history for tracking changes over time
CREATE TABLE IF NOT EXISTS proposal_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_date TEXT DEFAULT (datetime('now')),
    changed_by TEXT,  -- 'system' or 'manual'
    source_email_id INTEGER,
    notes TEXT,

    FOREIGN KEY (project_code) REFERENCES proposal_tracker(project_code),
    FOREIGN KEY (source_email_id) REFERENCES emails(id)
);

-- Weekly report generation log
CREATE TABLE IF NOT EXISTS weekly_proposal_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date TEXT NOT NULL,
    week_ending TEXT NOT NULL,
    pdf_path TEXT,
    proposals_count INTEGER,
    total_pipeline_value REAL,
    sent_to TEXT,  -- Email addresses
    sent_at TEXT,
    generation_notes TEXT,

    created_at TEXT DEFAULT (datetime('now'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_proposal_tracker_status ON proposal_tracker(current_status, is_active);
CREATE INDEX IF NOT EXISTS idx_proposal_tracker_code ON proposal_tracker(project_code);
CREATE INDEX IF NOT EXISTS idx_proposal_tracker_active ON proposal_tracker(is_active, status_changed_date);

CREATE INDEX IF NOT EXISTS idx_proposal_email_intel_project ON proposal_email_intelligence(project_code, email_date DESC);
CREATE INDEX IF NOT EXISTS idx_proposal_email_intel_email ON proposal_email_intelligence(email_id);

CREATE INDEX IF NOT EXISTS idx_proposal_status_history_project ON proposal_status_history(project_code, changed_date DESC);

-- Trigger to update days_in_current_status automatically
CREATE TRIGGER IF NOT EXISTS update_proposal_days_in_status
AFTER UPDATE ON proposal_tracker
FOR EACH ROW
WHEN NEW.status_changed_date IS NOT NULL
BEGIN
    UPDATE proposal_tracker
    SET days_in_current_status = CAST(
        (julianday('now') - julianday(NEW.status_changed_date)) AS INTEGER
    ),
    updated_at = datetime('now')
    WHERE id = NEW.id;
END;

-- Trigger to log status changes
CREATE TRIGGER IF NOT EXISTS log_proposal_status_change
AFTER UPDATE OF current_status ON proposal_tracker
FOR EACH ROW
WHEN OLD.current_status != NEW.current_status
BEGIN
    INSERT INTO proposal_status_history (project_code, old_status, new_status, changed_by, notes)
    VALUES (NEW.project_code, OLD.current_status, NEW.current_status, 'system',
            'Auto-updated from ' || OLD.current_status || ' to ' || NEW.current_status);
END;

-- View for easy querying
CREATE VIEW IF NOT EXISTS active_proposals_summary AS
SELECT
    pt.project_code,
    pt.project_name,
    pt.project_value,
    pt.country,
    pt.current_status,
    pt.last_week_status,
    pt.days_in_current_status,
    pt.proposal_sent,
    pt.first_contact_date,
    pt.proposal_sent_date,
    pt.current_remark,
    pt.latest_email_context,
    pt.last_email_date,
    COUNT(DISTINCT pei.email_id) as related_emails_count
FROM proposal_tracker pt
LEFT JOIN proposal_email_intelligence pei ON pt.project_code = pei.project_code
WHERE pt.is_active = 1
GROUP BY pt.project_code
ORDER BY pt.project_code;
