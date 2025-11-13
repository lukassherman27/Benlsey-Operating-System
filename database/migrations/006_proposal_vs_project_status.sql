-- Migration 006: Distinguish between proposals and active projects
-- This is CRITICAL for proper email categorization

-- Add status field to proposals table if not exists
-- Status values:
--   'prospect'     - Initial contact, exploring
--   'proposal'     - Proposal drafted/sent, awaiting decision
--   'negotiating'  - Back and forth on terms/scope/fee
--   'won'          - Contract signed, now ACTIVE PROJECT
--   'lost'         - Client went with someone else or passed
--   'on_hold'      - Temporarily paused

-- Check if status column exists, if not add it
-- SQLite doesn't have IF NOT EXISTS for ALTER COLUMN, so we check first

-- Add contract_signed_date to track when it became active project
ALTER TABLE proposals ADD COLUMN contract_signed_date TEXT;

-- Add is_active_project flag (1 = signed contract, 0 = still proposal)
ALTER TABLE proposals ADD COLUMN is_active_project INTEGER DEFAULT 0;

-- Update existing proposals based on status
-- If status = 'won' or contains 'active', mark as active project
UPDATE proposals
SET is_active_project = 1
WHERE status LIKE '%won%'
   OR status LIKE '%active%'
   OR status LIKE '%signed%';

-- Add project_phase for active projects
-- Values: concept, schematic, DD, CD, CA, closeout
ALTER TABLE proposals ADD COLUMN project_phase TEXT;

-- Add notes field for context
ALTER TABLE proposals ADD COLUMN status_notes TEXT;
