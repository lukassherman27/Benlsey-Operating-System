-- Migration 065: Add email direction and sender classification fields
-- This allows us to persist the direction of each email (internal vs external)
-- and classify the sender type for better filtering.

-- Add email_direction column
-- Values: internal_to_internal, internal_to_external, external_to_internal, external_to_external
ALTER TABLE emails ADD COLUMN email_direction TEXT;

-- Add sender_type column
-- Values: bensley_staff, client, vendor, consultant, operator, developer, unknown
ALTER TABLE emails ADD COLUMN sender_type TEXT;

-- Add flag for purely internal emails (all recipients are internal)
-- These should NOT trigger project link suggestions
ALTER TABLE emails ADD COLUMN is_purely_internal INTEGER DEFAULT 0;

-- Create index on email_direction for filtering
CREATE INDEX IF NOT EXISTS idx_emails_direction ON emails(email_direction);

-- Create index on is_purely_internal for quick filtering
CREATE INDEX IF NOT EXISTS idx_emails_internal ON emails(is_purely_internal);

-- Create composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_emails_direction_date ON emails(email_direction, date);
