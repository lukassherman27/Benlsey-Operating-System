-- Migration 018: Add proposal tracking date columns
-- Purpose: Track proposal lifecycle dates (first contact, drafting, proposal sent)
-- Data source: Historical data from Proposals.xlsx calendar tracking

-- Add first_contact_date column
ALTER TABLE projects ADD COLUMN first_contact_date DATE;

-- Add drafting_date column
ALTER TABLE projects ADD COLUMN drafting_date DATE;

-- Add proposal_sent_date column
ALTER TABLE projects ADD COLUMN proposal_sent_date DATE;

-- Add contract_signed_date column
ALTER TABLE projects ADD COLUMN contract_signed_date DATE;

-- Add last_proposal_activity_date column (for tracking most recent activity)
ALTER TABLE projects ADD COLUMN last_proposal_activity_date DATE;

-- Create indexes for performance
CREATE INDEX idx_projects_first_contact ON projects(first_contact_date);
CREATE INDEX idx_projects_proposal_sent ON projects(proposal_sent_date);
CREATE INDEX idx_projects_last_activity ON projects(last_proposal_activity_date);
