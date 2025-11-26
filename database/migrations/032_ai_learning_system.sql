-- Migration 032: AI Learning System
-- Foundation for human feedback loop and continuous learning

-- ============================================================================
-- AI SUGGESTIONS - What the AI proposes
-- ============================================================================

DROP TABLE IF EXISTS ai_suggestions;
CREATE TABLE ai_suggestions (
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
        'data_correction'        -- AI thinks existing data is wrong
    )),

    -- Priority/confidence
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),
    confidence_score REAL DEFAULT 0.5,  -- 0-1, how sure is AI

    -- Context: where did this come from?
    source_type TEXT NOT NULL CHECK(source_type IN ('email', 'attachment', 'contract', 'pattern')),
    source_id INTEGER,          -- email_id, attachment_id, etc.
    source_reference TEXT,      -- Human readable: "Email from John Smith, Nov 25"

    -- The suggestion itself
    title TEXT NOT NULL,        -- Short: "New contact: John Smith"
    description TEXT,           -- Detailed explanation
    suggested_action TEXT,      -- What should happen: "Add to contacts table"

    -- The data to add/change (JSON)
    suggested_data TEXT,        -- JSON: {"name": "John Smith", "email": "john@client.com", "company": "Ritz Carlton"}
    target_table TEXT,          -- Which table: "contacts", "proposals", etc.
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

-- Indexes for fast queries
CREATE INDEX idx_suggestions_status ON ai_suggestions(status);
CREATE INDEX idx_suggestions_type ON ai_suggestions(suggestion_type);
CREATE INDEX idx_suggestions_priority ON ai_suggestions(priority, status);
CREATE INDEX idx_suggestions_project ON ai_suggestions(project_code);
CREATE INDEX idx_suggestions_pending ON ai_suggestions(status, priority DESC, created_at DESC)
    WHERE status = 'pending';


-- ============================================================================
-- TRAINING FEEDBACK - What AI learns from human corrections
-- ============================================================================

DROP TABLE IF EXISTS training_feedback;
CREATE TABLE training_feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Link to original suggestion (if applicable)
    suggestion_id INTEGER,

    -- The learning context
    feedback_type TEXT NOT NULL CHECK(feedback_type IN (
        'suggestion_correction',  -- Human corrected AI suggestion
        'category_correction',    -- Wrong email category
        'entity_correction',      -- Wrong entity extraction
        'link_correction',        -- Wrong project link
        'tone_preference',        -- "Use more formal tone for this client"
        'business_rule',          -- "We never do X for Y type projects"
        'pattern_teaching',       -- "When you see X, it means Y"
        'explicit_instruction'    -- Direct teaching from user
    )),

    -- What was wrong
    original_value TEXT,        -- What AI said/did
    corrected_value TEXT,       -- What human corrected to

    -- Context for learning
    context_type TEXT,          -- 'email', 'proposal', 'contract', etc.
    context_id INTEGER,         -- ID of the source
    context_text TEXT,          -- The relevant text for training

    -- The lesson
    lesson TEXT,                -- Human-readable: "For luxury clients, always use formal tone"
    applies_to TEXT,            -- JSON: conditions when this applies

    -- Metadata
    project_code TEXT,
    client_company TEXT,

    -- Who taught
    taught_by TEXT NOT NULL,    -- 'bill', 'brian', 'lukas'
    taught_at DATETIME DEFAULT (datetime('now')),

    -- Learning status
    incorporated INTEGER DEFAULT 0,  -- Has this been used to improve?
    incorporated_at DATETIME,

    -- Quality tracking
    times_applied INTEGER DEFAULT 0,  -- How often has this lesson been used
    success_rate REAL,               -- When applied, was it correct?

    FOREIGN KEY (suggestion_id) REFERENCES ai_suggestions(suggestion_id)
);

CREATE INDEX idx_feedback_type ON training_feedback(feedback_type);
CREATE INDEX idx_feedback_context ON training_feedback(context_type, context_id);
CREATE INDEX idx_feedback_unincorporated ON training_feedback(incorporated) WHERE incorporated = 0;


-- ============================================================================
-- LEARNED PATTERNS - Accumulated knowledge
-- ============================================================================

DROP TABLE IF EXISTS learned_patterns;
CREATE TABLE learned_patterns (
    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Pattern definition
    pattern_name TEXT NOT NULL,          -- "luxury_client_tone"
    pattern_type TEXT NOT NULL CHECK(pattern_type IN (
        'client_preference',     -- How to handle specific clients
        'document_structure',    -- Where to find data in documents
        'communication_style',   -- Tone, format preferences
        'business_rule',         -- "Never quote less than $X for Y"
        'entity_pattern',        -- How to extract specific entities
        'workflow_pattern'       -- "After X, always do Y"
    )),

    -- The pattern rule
    condition TEXT NOT NULL,     -- JSON: when to apply {"client_type": "luxury", "project_type": "hotel"}
    action TEXT NOT NULL,        -- JSON: what to do {"tone": "formal", "sign_off": "Warm regards"}

    -- Evidence
    learned_from INTEGER,        -- feedback_id that created this
    evidence_count INTEGER DEFAULT 1,  -- How many feedbacks support this

    -- Confidence
    confidence_score REAL DEFAULT 0.5,
    last_validated DATETIME,
    validation_count INTEGER DEFAULT 0,

    -- Status
    is_active INTEGER DEFAULT 1,

    -- Timestamps
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

CREATE INDEX idx_patterns_type ON learned_patterns(pattern_type);
CREATE INDEX idx_patterns_active ON learned_patterns(is_active, pattern_type);


-- ============================================================================
-- ACTION QUEUE - Things AI should do automatically
-- ============================================================================

DROP TABLE IF EXISTS ai_action_queue;
CREATE TABLE ai_action_queue (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- What to do
    action_type TEXT NOT NULL CHECK(action_type IN (
        'send_email',           -- Draft and send (with approval)
        'schedule_followup',    -- Set reminder
        'update_record',        -- Update database
        'create_record',        -- Add to database
        'notify_user',          -- Alert Bill/Brian
        'generate_document',    -- Create proposal/report
        'parse_attachment'      -- Extract data from document
    )),

    -- Action details
    action_data TEXT NOT NULL,  -- JSON: all parameters needed

    -- Scheduling
    scheduled_for DATETIME,     -- When to execute
    requires_approval INTEGER DEFAULT 1,  -- Need human OK?

    -- Context
    triggered_by TEXT,          -- What triggered this: 'email_123', 'schedule', 'pattern_5'
    project_code TEXT,

    -- Status
    status TEXT DEFAULT 'pending' CHECK(status IN (
        'pending',
        'approved',
        'executing',
        'completed',
        'failed',
        'cancelled'
    )),

    -- Execution tracking
    approved_by TEXT,
    approved_at DATETIME,
    executed_at DATETIME,
    result TEXT,                -- JSON: what happened
    error_message TEXT,

    -- Timestamps
    created_at DATETIME DEFAULT (datetime('now'))
);

CREATE INDEX idx_actions_status ON ai_action_queue(status, scheduled_for);
CREATE INDEX idx_actions_project ON ai_action_queue(project_code);


-- ============================================================================
-- HELPER VIEW: Pending suggestions for review
-- ============================================================================

DROP VIEW IF EXISTS pending_suggestions_view;
CREATE VIEW pending_suggestions_view AS
SELECT
    s.suggestion_id,
    s.suggestion_type,
    s.priority,
    s.confidence_score,
    s.title,
    s.description,
    s.suggested_action,
    s.suggested_data,
    s.source_reference,
    s.project_code,
    p.project_name,
    s.created_at,
    CASE
        WHEN s.priority = 'critical' THEN 1
        WHEN s.priority = 'high' THEN 2
        WHEN s.priority = 'medium' THEN 3
        ELSE 4
    END as priority_order
FROM ai_suggestions s
LEFT JOIN proposals p ON s.project_code = p.project_code
WHERE s.status = 'pending'
ORDER BY priority_order, s.confidence_score DESC, s.created_at DESC;
