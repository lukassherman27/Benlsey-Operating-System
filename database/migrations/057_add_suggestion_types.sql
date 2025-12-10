-- Migration 057: Add new suggestion types
-- Date: 2025-12-02
-- Purpose: Add action_required, proposal_status_update, info, relationship_insight to suggestion_type CHECK constraint

-- SQLite doesn't support modifying CHECK constraints, so we need to recreate the table

-- Step 1: Create new table with updated constraint
CREATE TABLE ai_suggestions_new (
    suggestion_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- What type of suggestion (UPDATED with new types)
    suggestion_type TEXT NOT NULL CHECK(suggestion_type IN (
        'new_contact',           -- Found new person in email
        'update_contact',        -- Contact info changed
        'fee_change',            -- Fee/payment amount detected
        'status_change',         -- Project status should change
        'new_proposal',          -- New proposal opportunity detected
        'follow_up_needed',      -- Should follow up with client
        'missing_data',          -- Data gap detected
        'document_found',        -- Important document in attachment
        'meeting_detected',      -- Meeting mentioned, should schedule
        'deadline_detected',     -- Deadline mentioned
        'action_item',           -- Action item extracted
        'data_correction',       -- AI thinks existing data is wrong
        'email_link',            -- Suggest linking email to project
        'contact_link',          -- Suggest linking contact to project
        'transcript_link',       -- Suggest linking transcript to proposal
        'action_required',       -- NEW: We need to take action
        'proposal_status_update', -- NEW: Proposal status should change
        'info',                  -- NEW: Informational insight
        'relationship_insight'   -- NEW: Contact relationship detected
    )),

    -- Priority/confidence
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),
    confidence_score REAL DEFAULT 0.5,

    -- Context: where did this come from?
    source_type TEXT NOT NULL CHECK(source_type IN ('email', 'attachment', 'contract', 'pattern', 'transcript')),
    source_id INTEGER,
    source_reference TEXT,

    -- The suggestion itself
    title TEXT NOT NULL,
    description TEXT,
    suggested_action TEXT,

    -- The data to add/change (JSON)
    suggested_data TEXT,
    target_table TEXT,
    target_id INTEGER,

    -- Related entities
    project_code TEXT,
    proposal_id INTEGER,

    -- Status
    status TEXT DEFAULT 'pending' CHECK(status IN (
        'pending',
        'approved',
        'rejected',
        'modified',
        'auto_applied',
        'expired'
    )),

    -- Review tracking
    reviewed_by TEXT,
    reviewed_at DATETIME,
    review_notes TEXT,

    -- If modified, what was the correction?
    correction_data TEXT,

    -- Timestamps
    created_at DATETIME DEFAULT (datetime('now')),
    expires_at DATETIME,
    rollback_data TEXT,
    is_actionable INTEGER DEFAULT 1,
    detected_entities TEXT,
    suggested_actions TEXT,
    user_feedback_id INTEGER,

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

-- Step 2: Copy data from old table
INSERT INTO ai_suggestions_new (
    suggestion_id, suggestion_type, priority, confidence_score,
    source_type, source_id, source_reference,
    title, description, suggested_action,
    suggested_data, target_table, target_id,
    project_code, proposal_id,
    status, reviewed_by, reviewed_at, review_notes,
    correction_data, created_at, expires_at,
    rollback_data, is_actionable, detected_entities,
    suggested_actions, user_feedback_id
)
SELECT
    suggestion_id, suggestion_type, priority, confidence_score,
    source_type, source_id, source_reference,
    title, description, suggested_action,
    suggested_data, target_table, target_id,
    project_code, proposal_id,
    status, reviewed_by, reviewed_at, review_notes,
    correction_data, created_at, expires_at,
    rollback_data, is_actionable, detected_entities,
    suggested_actions, user_feedback_id
FROM ai_suggestions;

-- Step 3: Drop old table
DROP TABLE ai_suggestions;

-- Step 4: Rename new table
ALTER TABLE ai_suggestions_new RENAME TO ai_suggestions;

-- Step 5: Recreate indexes
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_type ON ai_suggestions(suggestion_type);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_status ON ai_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_project ON ai_suggestions(project_code);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_source ON ai_suggestions(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_created ON ai_suggestions(created_at);

-- Done
