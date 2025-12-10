-- Migration 062: Add link_review suggestion type
-- Date: 2025-12-02
-- Purpose: Add 'link_review' to allowed suggestion_type values

-- SQLite doesn't support modifying CHECK constraints directly.
-- We need to recreate the table or drop the constraint.
-- Since the table has data, we'll use a workaround by creating a new table.

-- First, let's see if we can just drop and recreate the constraint
-- SQLite 3.35+ supports ALTER TABLE DROP COLUMN, but not constraint modification.

-- The safest approach is to:
-- 1. Create a new table with the updated constraint
-- 2. Copy data
-- 3. Drop old table
-- 4. Rename new table

-- Step 1: Create new table with updated CHECK constraint
CREATE TABLE ai_suggestions_new (
    suggestion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_type TEXT NOT NULL CHECK(suggestion_type IN (
        'new_contact',
        'update_contact',
        'fee_change',
        'status_change',
        'new_proposal',
        'follow_up_needed',
        'missing_data',
        'document_found',
        'meeting_detected',
        'deadline_detected',
        'action_item',
        'data_correction',
        'email_link',
        'contact_link',
        'transcript_link',
        'action_required',
        'proposal_status_update',
        'info',
        'relationship_insight',
        'link_review'  -- NEW: Review existing auto-created links
    )),
    priority TEXT DEFAULT 'medium',
    confidence_score REAL DEFAULT 0.5,
    source_type TEXT NOT NULL,
    source_id INTEGER,
    source_reference TEXT,
    title TEXT NOT NULL,
    description TEXT,
    suggested_action TEXT,
    suggested_data TEXT,
    target_table TEXT,
    target_id INTEGER,
    project_code TEXT,
    proposal_id INTEGER,
    status TEXT DEFAULT 'pending',
    reviewed_by TEXT,
    reviewed_at DATETIME,
    review_notes TEXT,
    correction_data TEXT,
    created_at DATETIME DEFAULT (datetime('now')),
    expires_at DATETIME,
    rollback_data TEXT,
    is_actionable INTEGER DEFAULT 1,
    detected_entities TEXT,
    suggested_actions TEXT,
    user_feedback_id INTEGER
);

-- Step 2: Copy all existing data
INSERT INTO ai_suggestions_new SELECT * FROM ai_suggestions;

-- Step 3: Drop old table
DROP TABLE ai_suggestions;

-- Step 4: Rename new table
ALTER TABLE ai_suggestions_new RENAME TO ai_suggestions;

-- Step 5: Recreate indexes
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_status ON ai_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_type ON ai_suggestions(suggestion_type);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_created ON ai_suggestions(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_project_code ON ai_suggestions(project_code);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_proposal_id ON ai_suggestions(proposal_id);
