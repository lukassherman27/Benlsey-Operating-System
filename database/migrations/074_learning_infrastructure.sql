-- Migration 074: Learning Infrastructure
-- Created: 2025-12-08
-- Purpose: Track decisions, queries, and context to train future models

-- Every decision Claude helps make (for training data)
CREATE TABLE IF NOT EXISTS decision_log (
    decision_id INTEGER PRIMARY KEY,
    decision_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    decision_type TEXT,           -- 'email_link', 'status_update', 'contact_identified', 'fee_update', etc.
    entity_type TEXT,             -- 'proposal', 'project', 'contact', 'email'
    entity_id INTEGER,
    entity_code TEXT,             -- e.g., '25 BK-033' for easy reference
    old_value TEXT,
    new_value TEXT,
    confidence REAL,              -- How confident was AI? (0.0-1.0)
    source TEXT,                  -- 'ai_suggestion', 'manual', 'pattern_match', 'claude_session'
    source_id INTEGER,            -- Link to ai_suggestions if applicable
    session_id TEXT,              -- Claude session identifier
    approved_by TEXT,             -- Who approved?
    rejection_reason TEXT,        -- If rejected, why?
    notes TEXT,                   -- Any context
    outcome_verified BOOLEAN DEFAULT 0,     -- Was this decision verified as correct?
    outcome_date DATETIME,
    outcome_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_decision_log_type ON decision_log(decision_type);
CREATE INDEX IF NOT EXISTS idx_decision_log_entity ON decision_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_decision_log_date ON decision_log(decision_date);
CREATE INDEX IF NOT EXISTS idx_decision_log_session ON decision_log(session_id);

-- Every question asked (for understanding what queries matter)
CREATE TABLE IF NOT EXISTS query_log (
    query_id INTEGER PRIMARY KEY,
    query_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_email TEXT,
    session_id TEXT,
    query_text TEXT,              -- What did they ask?
    query_type TEXT,              -- 'search', 'report', 'status', 'analysis', 'enrichment'
    response_summary TEXT,        -- Brief summary of response
    response_tokens INTEGER,
    response_time_ms INTEGER,
    was_helpful BOOLEAN,          -- Did user indicate it was useful?
    feedback TEXT,
    tools_used TEXT,              -- JSON: which tools/services were called
    tables_queried TEXT,          -- JSON: which tables were accessed
    records_returned INTEGER
);

CREATE INDEX IF NOT EXISTS idx_query_log_type ON query_log(query_type);
CREATE INDEX IF NOT EXISTS idx_query_log_date ON query_log(query_date);
CREATE INDEX IF NOT EXISTS idx_query_log_user ON query_log(user_email);

-- Permanent context about entities (nicknames, preferences, warnings)
CREATE TABLE IF NOT EXISTS entity_context (
    context_id INTEGER PRIMARY KEY,
    entity_type TEXT NOT NULL,    -- 'contact', 'company', 'project', 'proposal'
    entity_id INTEGER,
    entity_identifier TEXT,       -- e.g., email address for contact, project_code for project
    context_type TEXT NOT NULL,   -- 'nickname', 'preference', 'warning', 'relationship', 'history'
    context_key TEXT NOT NULL,    -- 'called_by_bill', 'communication_preference', 'trustworthiness'
    context_value TEXT NOT NULL,  -- 'jinny', 'prefers WhatsApp', 'scammer - proceed with caution'
    source_type TEXT,             -- 'user_stated', 'inferred_from_email', 'learned_from_session'
    source_reference TEXT,        -- email_id, session_id, or other reference
    learned_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_confirmed DATETIME,
    confirmed_by TEXT,
    confidence REAL DEFAULT 1.0,
    is_active BOOLEAN DEFAULT 1,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_entity_context_entity ON entity_context(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_context_identifier ON entity_context(entity_identifier);
CREATE INDEX IF NOT EXISTS idx_entity_context_type ON entity_context(context_type);
CREATE UNIQUE INDEX IF NOT EXISTS idx_entity_context_unique ON entity_context(entity_type, entity_id, context_type, context_key);

-- Outcomes tracking - was the suggestion/decision correct?
CREATE TABLE IF NOT EXISTS suggestion_outcomes (
    outcome_id INTEGER PRIMARY KEY,
    suggestion_id INTEGER REFERENCES ai_suggestions(suggestion_id),
    decision_id INTEGER REFERENCES decision_log(decision_id),
    predicted_outcome TEXT,       -- What did we expect to happen?
    actual_outcome TEXT,          -- What actually happened?
    was_correct BOOLEAN,
    correction_applied TEXT,      -- What fix was needed?
    outcome_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    verified_by TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_suggestion_outcomes_suggestion ON suggestion_outcomes(suggestion_id);
CREATE INDEX IF NOT EXISTS idx_suggestion_outcomes_correct ON suggestion_outcomes(was_correct);

-- Session tracking - link multiple decisions to one Claude session
CREATE TABLE IF NOT EXISTS claude_sessions (
    session_id TEXT PRIMARY KEY,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    user_email TEXT,
    session_type TEXT,            -- 'enrichment', 'query', 'planning', 'audit'
    summary TEXT,                 -- What was accomplished?
    decisions_made INTEGER DEFAULT 0,
    entities_updated INTEGER DEFAULT 0,
    patterns_learned INTEGER DEFAULT 0,
    context_added INTEGER DEFAULT 0,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_claude_sessions_date ON claude_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_claude_sessions_type ON claude_sessions(session_type);

-- Insert some initial entity_context from what we've learned
-- (Nicknames discovered during enrichment sessions)
INSERT OR IGNORE INTO entity_context (entity_type, entity_identifier, context_type, context_key, context_value, source_type, notes)
VALUES
    ('contact', 'jin.young.kim@example.com', 'nickname', 'called_by_bill', 'jinny', 'user_stated', 'Bill refers to Jin Young Kim as jinny'),
    ('contact', 'sudha.reddy@example.com', 'nickname', 'called_by_bill', 'necklace', 'user_stated', 'Bill refers to Sudha Reddy as necklace (La Vie Wellness)');

-- Insert warning about Sanda Win
INSERT OR IGNORE INTO entity_context (entity_type, entity_identifier, context_type, context_key, context_value, source_type, notes)
VALUES
    ('contact', 'sanda.win@example.com', 'warning', 'trustworthiness', 'Proceed with caution - Bill warned "a bit of a scammer"', 'user_stated', 'Project Sumba (25 BK-074)');

-- Status type definitions (learned from enrichment)
INSERT OR IGNORE INTO entity_context (entity_type, entity_identifier, context_type, context_key, context_value, source_type, notes)
VALUES
    ('system', 'status_definitions', 'definition', 'dormant', 'Proposal sent, no response for months - not lost, just quiet', 'user_stated', 'Learned during enrichment'),
    ('system', 'status_definitions', 'definition', 'on_hold', 'Project paused by client - may resume', 'user_stated', 'Learned during enrichment');
