-- Add normalized date column to emails table
-- This ensures date queries work correctly without datetime() conversion

-- Add the column (as TEXT to maintain compatibility)
ALTER TABLE emails ADD COLUMN date_normalized DATETIME;

-- Populate it from existing dates using datetime() function
UPDATE emails SET date_normalized = datetime(date);

-- Create index for fast date-based queries
CREATE INDEX IF NOT EXISTS idx_emails_date_normalized ON emails(date_normalized);

-- Now all date queries should use date_normalized instead of date
-- Example: SELECT MAX(date_normalized) FROM emails
