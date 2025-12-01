-- Migration 047: Add transcript_link suggestion type
-- Date: 2025-12-01
-- Purpose: Enable transcript linking via suggestions workflow

-- SQLite doesn't allow ALTER TABLE to modify CHECK constraints
-- We need to recreate the table with the expanded constraint

-- Step 1: Create new table with updated constraint
CREATE TABLE ai_suggestions_new (
    suggestion_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- What type of suggestion
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
        'transcript_link'        -- NEW: Suggest linking transcript to proposal
    )),

    -- Priority/confidence
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),
    confidence_score REAL DEFAULT 0.5,  -- 0-1, how sure is AI

    -- Context: where did this come from?
    source_type TEXT NOT NULL CHECK(source_type IN ('email', 'attachment', 'contract', 'pattern', 'transcript')),
    source_id INTEGER,          -- email_id, attachment_id, transcript_id, etc.
    source_reference TEXT,      -- Human readable: "Meeting transcript from Nov 25"

    -- The suggestion itself
    title TEXT NOT NULL,        -- Short: "Link transcript to BK-070"
    description TEXT,           -- Detailed explanation
    suggested_action TEXT,      -- What should happen: "Update meeting_transcripts.proposal_id"

    -- The data to add/change (JSON)
    suggested_data TEXT,        -- JSON: {"transcript_id": 3, "proposal_id": 45, "project_code": "25 BK-070"}
    target_table TEXT,          -- Which table: "meeting_transcripts"
    target_id INTEGER,          -- If updating existing record

    -- Related entities
    project_code TEXT,
    proposal_id INTEGER,

    -- Status
    status TEXT DEFAULT 'pending' CHECK(status IN (
        'pending',      -- Awaiting review
        'approved',     -- Human approved, applied
        'rejected',     -- Human rejected
        'modified',     -- Human approved with changes
        'auto_applied', -- Applied automatically (high confidence)
        'expired'       -- Too old, no longer relevant
    )),

    -- Review tracking
    reviewed_by TEXT,
    reviewed_at DATETIME,
    review_notes TEXT,

    -- If modified, what was the correction?
    correction_data TEXT,       -- JSON: what human changed

    -- Timestamps
    created_at DATETIME DEFAULT (datetime('now')),
    expires_at DATETIME,        -- Some suggestions expire

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

-- Step 2: Copy data from old table
INSERT INTO ai_suggestions_new SELECT * FROM ai_suggestions;

-- Step 3: Drop old table
DROP TABLE ai_suggestions;

-- Step 4: Rename new table
ALTER TABLE ai_suggestions_new RENAME TO ai_suggestions;

-- Step 5: Recreate indexes
CREATE INDEX idx_suggestions_status ON ai_suggestions(status);
CREATE INDEX idx_suggestions_type ON ai_suggestions(suggestion_type);
CREATE INDEX idx_suggestions_priority ON ai_suggestions(priority, status);
CREATE INDEX idx_suggestions_project ON ai_suggestions(project_code);
CREATE INDEX idx_suggestions_pending ON ai_suggestions(status, priority DESC, created_at DESC)
    WHERE status = 'pending';

-- Verify migration
SELECT 'Migration 047 complete. New suggestion type: transcript_link' as result;
