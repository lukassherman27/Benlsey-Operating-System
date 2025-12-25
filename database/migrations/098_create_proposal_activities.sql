-- Migration 098: Create proposal_activities table
-- Issue #140: Activity Tracking Database - Foundation for Business Intelligence
--
-- This table logs ALL interactions and events for proposals, enabling:
-- - AI Story Builder to piece together the narrative
-- - Weekly Reports to show "what happened this week"
-- - Analytics to track patterns and outcomes

CREATE TABLE IF NOT EXISTS proposal_activities (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER REFERENCES proposals(proposal_id),
    project_id INTEGER REFERENCES projects(project_id),  -- Some activities may be project-level

    -- What happened
    activity_type TEXT NOT NULL,  -- 'email_sent', 'email_received', 'meeting', 'status_change',
                                  -- 'follow_up_scheduled', 'action_completed', 'note_added',
                                  -- 'proposal_sent', 'contract_signed', 'call', 'decision'
    activity_date DATETIME NOT NULL,

    -- Where it came from
    source_type TEXT,             -- 'email', 'transcript', 'manual', 'system'
    source_id TEXT,               -- email_id, transcript_id, etc.

    -- Who was involved
    actor TEXT,                   -- 'bill', 'brian', 'lukas', 'mink', 'client', 'system'
    actor_email TEXT,             -- Email address if from email

    -- What was said/done
    title TEXT,                   -- Short summary (e.g., email subject)
    summary TEXT,                 -- AI-generated or manual summary
    full_content TEXT,            -- Full content if needed (email body, transcript)

    -- Extracted intelligence (populated by AI Story Builder)
    sentiment TEXT,               -- 'positive', 'neutral', 'negative', 'urgent'
    extracted_dates TEXT,         -- JSON array of dates mentioned
    extracted_actions TEXT,       -- JSON array of action items found
    extracted_decisions TEXT,     -- JSON array of decisions made

    -- Metadata
    metadata TEXT,                -- JSON for flexible additional data
    is_significant INTEGER DEFAULT 0,  -- Flag for important events (milestones)

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_activities_proposal ON proposal_activities(proposal_id);
CREATE INDEX IF NOT EXISTS idx_activities_project ON proposal_activities(project_id);
CREATE INDEX IF NOT EXISTS idx_activities_date ON proposal_activities(activity_date);
CREATE INDEX IF NOT EXISTS idx_activities_type ON proposal_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_activities_source ON proposal_activities(source_type, source_id);

-- Trigger to update updated_at
CREATE TRIGGER IF NOT EXISTS proposal_activities_updated_at
AFTER UPDATE ON proposal_activities
BEGIN
    UPDATE proposal_activities SET updated_at = CURRENT_TIMESTAMP WHERE activity_id = NEW.activity_id;
END;
