-- Email Intelligence Migration
-- Adds category tracking and proposal linking for emails

-- Add category column to emails
ALTER TABLE emails ADD COLUMN category TEXT;
ALTER TABLE emails ADD COLUMN ai_confidence REAL;
ALTER TABLE emails ADD COLUMN ai_extracted_data TEXT; -- JSON blob for structured data

-- Create email-proposal link table
CREATE TABLE IF NOT EXISTS email_proposal_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,
    proposal_id INTEGER NOT NULL,
    confidence REAL DEFAULT 0.0,
    link_type TEXT, -- 'auto', 'manual', 'ai_suggested'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    FOREIGN KEY (email_id) REFERENCES emails(email_id),
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    UNIQUE(email_id, proposal_id)
);

CREATE INDEX IF NOT EXISTS idx_email_proposal_email ON email_proposal_links(email_id);
CREATE INDEX IF NOT EXISTS idx_email_proposal_proposal ON email_proposal_links(proposal_id);
CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category);
CREATE INDEX IF NOT EXISTS idx_emails_processed ON emails(processed);
CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date);

-- AI suggestions queue table already exists, skip
