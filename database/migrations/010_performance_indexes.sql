-- Migration 010: Performance Indexes
-- Add indexes to speed up common queries

-- Email indexes for timeline and search
CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date);
CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender_email);
CREATE INDEX IF NOT EXISTS idx_emails_folder ON emails(folder);

-- Full-text search on email bodies
-- (SQLite FTS5 for fast text search)
CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
    email_id UNINDEXED,
    subject,
    body_full,
    content='emails',
    content_rowid='email_id'
);

-- Populate FTS index
INSERT INTO emails_fts(email_id, subject, body_full)
SELECT email_id, subject, body_full FROM emails;

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS emails_ai AFTER INSERT ON emails BEGIN
  INSERT INTO emails_fts(email_id, subject, body_full)
  VALUES (new.email_id, new.subject, new.body_full);
END;

CREATE TRIGGER IF NOT EXISTS emails_ad AFTER DELETE ON emails BEGIN
  DELETE FROM emails_fts WHERE email_id = old.email_id;
END;

CREATE TRIGGER IF NOT EXISTS emails_au AFTER UPDATE ON emails BEGIN
  UPDATE emails_fts SET subject = new.subject, body_full = new.body_full
  WHERE email_id = new.email_id;
END;

-- Document indexes
CREATE INDEX IF NOT EXISTS idx_documents_project_code ON documents(project_code);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_modified ON documents(modified_date);

-- Proposal health and status indexes
CREATE INDEX IF NOT EXISTS idx_proposals_health ON proposals(health_score);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
CREATE INDEX IF NOT EXISTS idx_proposals_active ON proposals(is_active_project);
CREATE INDEX IF NOT EXISTS idx_proposals_days_contact ON proposals(days_since_contact);

-- Email content category index
CREATE INDEX IF NOT EXISTS idx_email_content_category ON email_content(category);
CREATE INDEX IF NOT EXISTS idx_email_content_importance ON email_content(importance_score);

-- Link table indexes for joins
CREATE INDEX IF NOT EXISTS idx_epl_proposal ON email_proposal_links(proposal_id);
CREATE INDEX IF NOT EXISTS idx_epl_email ON email_proposal_links(email_id);
CREATE INDEX IF NOT EXISTS idx_dpl_proposal ON document_proposal_links(proposal_id);
CREATE INDEX IF NOT EXISTS idx_dpl_document ON document_proposal_links(document_id);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_proposals_active_health
    ON proposals(is_active_project, health_score, days_since_contact);

CREATE INDEX IF NOT EXISTS idx_emails_date_folder
    ON emails(date, folder);
