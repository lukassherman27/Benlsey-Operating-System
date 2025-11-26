-- Migration 015: AI Observations Table (Staging Area for AI Suggestions)
-- Purpose: AI suggestions go here instead of directly modifying locked data

CREATE TABLE IF NOT EXISTS ai_observations (
    observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('project', 'invoice', 'email', 'document', 'milestone')),
    entity_id INTEGER NOT NULL,
    proposed_field TEXT NOT NULL,        -- Field name AI wants to change
    current_value TEXT,                  -- Current value in database
    proposed_value TEXT,                 -- AI's suggested value
    confidence REAL CHECK(confidence >= 0 AND confidence <= 1),
    source_type TEXT CHECK(source_type IN ('email_parser', 'pdf_extraction', 'ai_inference', 'data_enrichment')),
    source_reference TEXT,               -- Email ID, PDF path, etc.
    reasoning TEXT,                      -- Why AI made this suggestion
    observed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('pending', 'approved', 'rejected', 'expired', 'superseded')) DEFAULT 'pending',
    reviewed_by TEXT,                    -- Who approved/rejected
    reviewed_at DATETIME,
    review_notes TEXT,
    expires_at DATETIME,                 -- Auto-expire stale suggestions
    metadata TEXT                        -- JSON for additional context
);

CREATE INDEX idx_ai_observations_entity ON ai_observations(entity_type, entity_id);
CREATE INDEX idx_ai_observations_status ON ai_observations(status);
CREATE INDEX idx_ai_observations_date ON ai_observations(observed_at);
CREATE INDEX idx_ai_observations_expires ON ai_observations(expires_at);
