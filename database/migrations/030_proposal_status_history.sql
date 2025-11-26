-- Migration: Proposal Status History Tracking
-- Created: 2025-11-25
-- Purpose: Track proposal status changes over time for lifecycle management

CREATE TABLE IF NOT EXISTS proposal_status_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    project_code TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    status_date DATE NOT NULL,
    changed_by TEXT DEFAULT 'system',
    notes TEXT,
    source TEXT DEFAULT 'manual',  -- 'manual', 'email', 'import', 'api'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

CREATE INDEX IF NOT EXISTS idx_proposal_history_proposal
    ON proposal_status_history(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_history_project_code
    ON proposal_status_history(project_code);
CREATE INDEX IF NOT EXISTS idx_proposal_history_date
    ON proposal_status_history(status_date);

-- Add status tracking fields to proposals table
ALTER TABLE proposals ADD COLUMN last_status_change DATE;
ALTER TABLE proposals ADD COLUMN status_changed_by TEXT;
