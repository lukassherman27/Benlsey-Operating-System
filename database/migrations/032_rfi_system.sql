-- Migration 032: RFI System Enhancement
-- Created: 2025-11-26
-- Purpose: Add rfi_responses table and enhance existing rfis table
-- Note: rfis table already exists - only adding missing columns

-- Add missing columns to rfis table (using ALTER TABLE for SQLite compatibility)
-- Note: SQLite doesn't allow CURRENT_TIMESTAMP as default in ALTER TABLE
ALTER TABLE rfis ADD COLUMN category TEXT;
ALTER TABLE rfis ADD COLUMN assigned_to TEXT;
ALTER TABLE rfis ADD COLUMN updated_at DATETIME;

-- Create rfi_responses table for tracking all responses to an RFI
CREATE TABLE IF NOT EXISTS rfi_responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfi_id INTEGER NOT NULL,
    email_id INTEGER,
    response_text TEXT,
    response_date DATETIME NOT NULL,
    responder_name TEXT,
    responder_email TEXT,
    is_final_response BOOLEAN DEFAULT 0,
    attachments_count INTEGER DEFAULT 0,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (rfi_id) REFERENCES rfis(rfi_id) ON DELETE CASCADE,
    FOREIGN KEY (email_id) REFERENCES emails(id)
);

-- Indexes for rfi_responses
CREATE INDEX IF NOT EXISTS idx_rfi_responses_rfi ON rfi_responses(rfi_id);
CREATE INDEX IF NOT EXISTS idx_rfi_responses_email ON rfi_responses(email_id);
CREATE INDEX IF NOT EXISTS idx_rfi_responses_date ON rfi_responses(response_date);

-- Index on new rfis columns
CREATE INDEX IF NOT EXISTS idx_rfi_category ON rfis(category);
CREATE INDEX IF NOT EXISTS idx_rfi_assigned ON rfis(assigned_to);

-- Trigger to update rfis when a response is added
CREATE TRIGGER IF NOT EXISTS trg_rfi_response_update
AFTER INSERT ON rfi_responses
FOR EACH ROW
WHEN NEW.is_final_response = 1
BEGIN
    UPDATE rfis
    SET status = 'closed',
        date_responded = NEW.response_date,
        response_email_id = NEW.email_id,
        updated_at = CURRENT_TIMESTAMP
    WHERE rfi_id = NEW.rfi_id;
END;

-- View for RFI summary with response counts
CREATE VIEW IF NOT EXISTS v_rfi_summary AS
SELECT
    r.rfi_id,
    r.project_code,
    r.rfi_number,
    r.subject,
    r.category,
    r.status,
    r.priority,
    r.date_sent,
    r.date_due,
    r.date_responded,
    r.assigned_to,
    CASE
        WHEN r.status = 'open' AND r.date_due < DATE('now') THEN 'overdue'
        WHEN r.status = 'open' AND r.date_due <= DATE('now', '+3 days') THEN 'due_soon'
        ELSE r.status
    END AS urgency,
    (SELECT COUNT(*) FROM rfi_responses WHERE rfi_id = r.rfi_id) AS response_count,
    julianday(COALESCE(r.date_responded, 'now')) - julianday(r.date_sent) AS days_to_respond
FROM rfis r
ORDER BY
    CASE r.status WHEN 'open' THEN 0 ELSE 1 END,
    r.date_due;
