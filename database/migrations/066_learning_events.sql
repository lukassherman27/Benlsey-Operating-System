-- Migration 066: Create learning_events table for tracking all learning activities
-- Every approve/reject/correction is logged here for analysis and debugging.

CREATE TABLE IF NOT EXISTS learning_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Event identification
    event_type TEXT NOT NULL,  -- 'email_link_approved', 'email_link_rejected', 'pattern_created', 'pattern_boosted', 'skip_pattern_created'

    -- Source information
    email_id INTEGER,
    sender_email TEXT,
    sender_domain TEXT,

    -- Target information
    project_code TEXT,
    proposal_id INTEGER,
    project_id INTEGER,

    -- Pattern information
    pattern_type TEXT,  -- 'sender_to_proposal', 'domain_to_project', 'domain_to_skip', etc.
    pattern_key TEXT,   -- The actual pattern value (email, domain, keyword)

    -- Confidence tracking
    confidence_before REAL,
    confidence_after REAL,
    confidence_delta REAL,  -- How much confidence changed

    -- User feedback
    user_notes TEXT,        -- User's explanation for the decision
    gpt_reasoning TEXT,     -- GPT's original reasoning (for analysis)
    correct_project_code TEXT,  -- If user provided a correction

    -- Metadata
    created_at DATETIME DEFAULT (datetime('now')),
    created_by TEXT DEFAULT 'system'
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_learning_events_type ON learning_events(event_type);
CREATE INDEX IF NOT EXISTS idx_learning_events_email ON learning_events(email_id);
CREATE INDEX IF NOT EXISTS idx_learning_events_project ON learning_events(project_code);
CREATE INDEX IF NOT EXISTS idx_learning_events_sender ON learning_events(sender_email);
CREATE INDEX IF NOT EXISTS idx_learning_events_pattern ON learning_events(pattern_type, pattern_key);
CREATE INDEX IF NOT EXISTS idx_learning_events_created ON learning_events(created_at);
