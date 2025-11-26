-- Migration 029: Email Category Approval System
-- Adds human_approved field and approval tracking for RLHF

-- Add human_approved column to email_content if not exists
ALTER TABLE email_content ADD COLUMN human_approved INTEGER DEFAULT 0;

-- Add approved_by and approved_at columns
ALTER TABLE email_content ADD COLUMN approved_by TEXT;
ALTER TABLE email_content ADD COLUMN approved_at DATETIME;

-- Create index for finding unapproved categorizations
CREATE INDEX IF NOT EXISTS idx_email_content_human_approved
    ON email_content(human_approved);

-- Create index for finding unapproved high-importance emails
CREATE INDEX IF NOT EXISTS idx_email_content_pending_approval
    ON email_content(human_approved, importance_score DESC)
    WHERE human_approved = 0;
