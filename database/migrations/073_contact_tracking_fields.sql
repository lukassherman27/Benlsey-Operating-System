-- Migration 073: Add contact tracking fields to proposals
-- Created: 2025-12-05
-- Purpose: Track who owes who a response and what we're waiting for

ALTER TABLE proposals ADD COLUMN last_client_contact_date DATE;
ALTER TABLE proposals ADD COLUMN last_our_contact_date DATE;
ALTER TABLE proposals ADD COLUMN waiting_for TEXT;
ALTER TABLE proposals ADD COLUMN waiting_since DATE;

-- Add index for quick queries on waiting status
CREATE INDEX idx_proposals_waiting ON proposals(waiting_for, waiting_since);
