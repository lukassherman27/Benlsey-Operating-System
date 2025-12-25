-- Migration 099: Create proposal_action_items table
-- Issue #140: Activity Tracking Database - Foundation for Business Intelligence
--
-- This table stores action items extracted from emails, meetings, and manual entry.
-- AI Story Builder populates this by parsing text like "follow up in January"

CREATE TABLE IF NOT EXISTS proposal_action_items (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER REFERENCES proposals(proposal_id),
    project_id INTEGER REFERENCES projects(project_id),

    -- Source of the action item
    source_activity_id INTEGER REFERENCES proposal_activities(activity_id),
    source_type TEXT,             -- 'email', 'transcript', 'manual', 'system'

    -- The action itself
    action_text TEXT NOT NULL,    -- "Follow up in January", "Send revised proposal"
    action_category TEXT,         -- 'follow_up', 'send_document', 'schedule_meeting',
                                  -- 'provide_info', 'review', 'decision_needed', 'other'

    -- Timing
    due_date DATE,                -- When it's due (extracted or calculated)
    due_date_source TEXT,         -- 'extracted' (from text), 'calculated' (7 days from now), 'manual'
    reminder_date DATE,           -- When to remind (typically 1-2 days before due)

    -- Assignment
    assigned_to TEXT,             -- 'bill', 'brian', 'lukas', 'mink', 'client'
    assigned_by TEXT,             -- Who assigned it

    -- Status tracking
    status TEXT DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'cancelled', 'overdue'
    priority TEXT DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'
    completed_at DATETIME,
    completed_by TEXT,
    completion_notes TEXT,

    -- AI metadata
    extraction_confidence REAL,   -- 0.0-1.0 confidence score from AI
    original_text TEXT,           -- The exact text the action was extracted from

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_action_items_proposal ON proposal_action_items(proposal_id);
CREATE INDEX IF NOT EXISTS idx_action_items_project ON proposal_action_items(project_id);
CREATE INDEX IF NOT EXISTS idx_action_items_status ON proposal_action_items(status);
CREATE INDEX IF NOT EXISTS idx_action_items_due ON proposal_action_items(due_date);
CREATE INDEX IF NOT EXISTS idx_action_items_assigned ON proposal_action_items(assigned_to);
CREATE INDEX IF NOT EXISTS idx_action_items_source ON proposal_action_items(source_activity_id);

-- Trigger to update updated_at
CREATE TRIGGER IF NOT EXISTS action_items_updated_at
AFTER UPDATE ON proposal_action_items
BEGIN
    UPDATE proposal_action_items SET updated_at = CURRENT_TIMESTAMP WHERE action_id = NEW.action_id;
END;

-- Trigger to mark overdue items
-- (This would be run by a scheduled job, but we can also check on query)
