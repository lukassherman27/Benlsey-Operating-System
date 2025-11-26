-- Migration 008: Manual Overrides Table
-- Purpose: Track Bill's manual instructions and context overrides
-- Created: 2025-01-14

CREATE TABLE IF NOT EXISTS manual_overrides (
    override_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER,  -- nullable for global overrides
    project_code TEXT,    -- denormalized for quick filtering
    scope TEXT NOT NULL,  -- 'emails', 'documents', 'billing', 'rfis', 'scheduling', 'general'
    instruction TEXT NOT NULL,  -- The actual instruction/note
    author TEXT NOT NULL DEFAULT 'bill',  -- Who provided this (bill, lukas, etc.)
    source TEXT NOT NULL DEFAULT 'dashboard_context_modal',  -- Where it came from
    urgency TEXT NOT NULL DEFAULT 'informational',  -- 'informational', 'urgent'
    status TEXT NOT NULL DEFAULT 'active',  -- 'active', 'applied', 'archived'
    applied_by TEXT,  -- Who/what applied this override
    applied_at TIMESTAMP,  -- When it was applied
    tags TEXT,  -- JSON array of keywords for search
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_manual_overrides_proposal_id ON manual_overrides(proposal_id);
CREATE INDEX IF NOT EXISTS idx_manual_overrides_project_code ON manual_overrides(project_code);
CREATE INDEX IF NOT EXISTS idx_manual_overrides_status ON manual_overrides(status);
CREATE INDEX IF NOT EXISTS idx_manual_overrides_author ON manual_overrides(author);
CREATE INDEX IF NOT EXISTS idx_manual_overrides_scope ON manual_overrides(scope);
CREATE INDEX IF NOT EXISTS idx_manual_overrides_created_at ON manual_overrides(created_at DESC);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_manual_overrides_timestamp
AFTER UPDATE ON manual_overrides
BEGIN
    UPDATE manual_overrides SET updated_at = CURRENT_TIMESTAMP
    WHERE override_id = NEW.override_id;
END;
