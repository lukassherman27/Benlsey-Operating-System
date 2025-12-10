-- Migration 056: Add email classification columns
-- Date: 2025-12-02
-- Purpose: Store email type (internal/external/client/consultant/vendor) on email records

-- Add classification columns to emails table
ALTER TABLE emails ADD COLUMN email_type TEXT DEFAULT NULL;
-- Valid values: internal, client_external, operator_external, developer_external, consultant_external, vendor_external, spam, administrative

ALTER TABLE emails ADD COLUMN is_project_related INTEGER DEFAULT NULL;
-- 1 = yes, 0 = no, NULL = not yet classified

ALTER TABLE emails ADD COLUMN classification_confidence REAL DEFAULT NULL;
-- 0.0 to 1.0 confidence score from GPT

ALTER TABLE emails ADD COLUMN classification_reasoning TEXT DEFAULT NULL;
-- Brief explanation of why this classification was assigned

ALTER TABLE emails ADD COLUMN classified_at TEXT DEFAULT NULL;
-- Timestamp when classification was applied

-- Create index for efficient filtering by email type
CREATE INDEX IF NOT EXISTS idx_emails_email_type ON emails(email_type);
CREATE INDEX IF NOT EXISTS idx_emails_is_project_related ON emails(is_project_related);

-- Create view for email classification summary
CREATE VIEW IF NOT EXISTS email_classification_summary AS
SELECT
    email_type,
    is_project_related,
    COUNT(*) as email_count,
    AVG(classification_confidence) as avg_confidence
FROM emails
WHERE email_type IS NOT NULL
GROUP BY email_type, is_project_related
ORDER BY email_count DESC;

-- Done
