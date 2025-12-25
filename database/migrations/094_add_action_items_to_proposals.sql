-- Migration 094: Add action owner tracking to proposals
-- Issue #95: Track Bensley action items not just ball ownership
-- Created: 2025-12-25

-- NOTE: proposals table already has:
--   next_action TEXT - what needs to be done (has existing data)
--   next_action_date TEXT - when it's due (has existing data)
--
-- This migration adds:
--   action_owner - who owns the action (bill/brian/lukas/mink)
--   action_source - where the action came from (email/meeting/manual)

-- Add owner and source columns (if not exist)
ALTER TABLE proposals ADD COLUMN action_owner TEXT CHECK(action_owner IN ('bill', 'brian', 'lukas', 'mink', NULL));
ALTER TABLE proposals ADD COLUMN action_source TEXT CHECK(action_source IN ('email', 'meeting', 'manual', NULL));

-- Also added action_needed and action_due but these are redundant with next_action/next_action_date
-- Keeping for now but next_action is the canonical field
ALTER TABLE proposals ADD COLUMN action_needed TEXT;
ALTER TABLE proposals ADD COLUMN action_due DATE;

-- Create index for finding proposals by owner
CREATE INDEX IF NOT EXISTS idx_proposals_action_owner ON proposals(action_owner) WHERE action_owner IS NOT NULL;

-- Record migration
INSERT OR IGNORE INTO schema_migrations (version, name, applied_at)
VALUES (94, '094_add_action_items_to_proposals', datetime('now'));
