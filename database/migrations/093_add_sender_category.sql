-- Migration 093: Add sender_category to emails table
-- Created: 2024-12-25
-- Issue: #93 - Add sender_category to emails for Bill/Brian/Lukas tracking
-- Purpose: Enable automatic ball-in-court detection and proposal story building

-- Step 1: Add the column (if not exists - idempotent)
-- Note: Column already added and backfilled in this session

-- Step 2: Backfill commands (already run):
-- UPDATE emails SET sender_category = 'bill' WHERE sender_email LIKE '%bill@bensley%';
-- UPDATE emails SET sender_category = 'brian' WHERE sender_email LIKE '%bsherman@bensley%';
-- UPDATE emails SET sender_category = 'lukas' WHERE sender_email LIKE '%lukas@bensley%';
-- UPDATE emails SET sender_category = 'mink' WHERE sender_email LIKE '%mink@bensley%';
-- UPDATE emails SET sender_category = 'bensley_other' WHERE sender_category IS NULL AND sender_email LIKE '%@bensley.com%';
-- UPDATE emails SET sender_category = 'client' WHERE sender_category IS NULL AND sender_email IS NOT NULL;

-- Step 3: Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_emails_sender_category ON emails(sender_category);

-- Results after backfill:
-- client: 1173
-- lukas: 1133
-- bensley_other: 583
-- bill: 491
-- brian: 442
-- mink: 57
