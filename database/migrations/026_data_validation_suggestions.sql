-- Migration 026: Data Validation Suggestions System
-- Date: 2025-11-24
-- Purpose: AI-powered data validation - detect inconsistencies between emails and database

-- Store suggestions from AI when it detects data inconsistencies
CREATE TABLE IF NOT EXISTS data_validation_suggestions (
    suggestion_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- What entity has the issue
    entity_type TEXT NOT NULL, -- 'proposal', 'project', 'invoice', 'contract'
    entity_id INTEGER NOT NULL,
    project_code TEXT,

    -- What's the inconsistency?
    field_name TEXT NOT NULL, -- 'status', 'project_value', 'team_size', etc.
    current_value TEXT, -- What database currently says
    suggested_value TEXT NOT NULL, -- What AI thinks it should be

    -- Evidence (why AI thinks this)
    evidence_source TEXT NOT NULL, -- 'email', 'document', 'conversation'
    evidence_id INTEGER, -- email_id or document_id
    evidence_snippet TEXT, -- Actual text from email: "5 people working on this"
    evidence_date DATETIME,

    -- AI reasoning
    confidence_score REAL CHECK(confidence_score BETWEEN 0 AND 1), -- 0.0 to 1.0
    reasoning TEXT, -- "Email from Nov 20 mentions project is active, but database shows archived"
    suggested_action TEXT, -- "Update project status from 'archived' to 'active'"

    -- Review status
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'denied', 'applied')),
    reviewed_by TEXT,
    reviewed_at DATETIME,
    review_notes TEXT,

    -- Application tracking
    applied_at DATETIME,
    applied_by TEXT,

    -- Metadata
    created_at DATETIME DEFAULT (datetime('now')),

    -- Indexes
    CHECK(entity_type IN ('proposal', 'project', 'invoice', 'contract', 'client', 'contact'))
);

-- Indexes for fast querying
CREATE INDEX idx_suggestions_status ON data_validation_suggestions(status);
CREATE INDEX idx_suggestions_entity ON data_validation_suggestions(entity_type, entity_id);
CREATE INDEX idx_suggestions_project_code ON data_validation_suggestions(project_code);
CREATE INDEX idx_suggestions_confidence ON data_validation_suggestions(confidence_score DESC);
CREATE INDEX idx_suggestions_created ON data_validation_suggestions(created_at DESC);

-- Track when suggestions are applied (for learning)
CREATE TABLE IF NOT EXISTS suggestion_application_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id INTEGER NOT NULL,

    -- What was changed
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,

    -- Who and when
    applied_by TEXT NOT NULL,
    applied_at DATETIME DEFAULT (datetime('now')),

    -- Result
    success INTEGER DEFAULT 1, -- 1 = success, 0 = failed
    error_message TEXT,

    FOREIGN KEY (suggestion_id) REFERENCES data_validation_suggestions(suggestion_id)
);

CREATE INDEX idx_application_log_suggestion ON suggestion_application_log(suggestion_id);
CREATE INDEX idx_application_log_entity ON suggestion_application_log(entity_type, entity_id);

-- Record this migration
INSERT INTO schema_migrations (version, name, description)
VALUES (26, '026_data_validation_suggestions', 'AI-powered data validation and inconsistency detection system');
