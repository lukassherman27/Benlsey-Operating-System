-- Migration 017: User Context & Audit Feedback
-- Created: 2025-11-23
-- Description: Track user Q&A interactions, feedback, and context building
--              Enables continuous learning and AI model improvement through human feedback

-- ============================================================================
-- Audit Questions
-- Stores questions asked by the system during audit/review process
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_questions (
    question_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id              INTEGER NOT NULL,
    question_category       TEXT NOT NULL,                      -- 'scope_verification', 'fee_breakdown', 'timeline_validation', 'payment_terms', 'contract_clause', 'deliverable_confirmation'
    question_type           TEXT NOT NULL,                      -- 'yes_no', 'multiple_choice', 'numeric', 'date', 'text', 'selection', 'verification'
    question_text           TEXT NOT NULL,                      -- The actual question
    question_context        TEXT,                               -- Why this question is being asked
    data_field              TEXT,                               -- Which database field this populates
    table_name              TEXT,                               -- Which table this data goes into
    suggested_answer        TEXT,                               -- AI's suggested/default answer
    suggested_confidence    REAL,                               -- Confidence in suggestion (0-1)
    suggestion_source       TEXT,                               -- 'ai_extraction', 'rule_based', 'pattern_match', 'historical_data'
    answer_options          TEXT,                               -- JSON array of options for multiple choice
    validation_rules        TEXT,                               -- JSON with validation criteria
    priority                INTEGER DEFAULT 1,                  -- Question priority (1=high, 5=low)
    is_required             INTEGER DEFAULT 0,                  -- Must this be answered?
    skip_logic              TEXT,                               -- JSON defining when to skip this question
    status                  TEXT DEFAULT 'pending',             -- 'pending', 'answered', 'skipped', 'deferred'
    asked_at                DATETIME,                           -- When question was presented to user
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

-- ============================================================================
-- Audit Answers
-- Stores user responses to audit questions
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_answers (
    answer_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id             INTEGER NOT NULL,
    project_id              INTEGER NOT NULL,
    answer_value            TEXT,                               -- The actual answer
    answer_type             TEXT,                               -- Type of answer provided
    answered_by             TEXT,                               -- User who provided answer
    answered_at             DATETIME NOT NULL,
    confidence_level        TEXT,                               -- 'certain', 'likely', 'unsure', 'guess'
    source_reference        TEXT,                               -- Reference to source document/email if applicable
    verification_status     TEXT DEFAULT 'pending',             -- 'pending', 'verified', 'needs_review', 'disputed'
    verified_by             TEXT,                               -- Who verified this answer
    verified_at             DATETIME,
    previous_answer         TEXT,                               -- If answer was changed, store previous value
    change_reason           TEXT,                               -- Why answer was changed
    applied_to_database     INTEGER DEFAULT 0,                  -- Has this been written to the database?
    applied_at              DATETIME,                           -- When it was applied
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (question_id) REFERENCES audit_questions(question_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

-- ============================================================================
-- User Feedback
-- Track user feedback on AI suggestions and system behavior
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_feedback (
    feedback_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    feedback_type           TEXT NOT NULL,                      -- 'suggestion_rating', 'error_report', 'feature_request', 'data_correction', 'ai_performance'
    feedback_category       TEXT,                               -- 'ai_accuracy', 'ui_ux', 'performance', 'data_quality', 'feature_gap'
    context_type            TEXT,                               -- 'email_categorization', 'proposal_matching', 'scope_extraction', 'fee_breakdown', 'timeline_prediction'
    context_id              TEXT,                               -- ID of related entity (email_id, project_id, etc.)
    ai_suggestion           TEXT,                               -- What AI suggested
    user_correction         TEXT,                               -- What user said is correct
    feedback_score          INTEGER,                            -- Rating (1-5 stars, thumbs up/down, etc.)
    feedback_text           TEXT,                               -- Detailed feedback from user
    impact_level            TEXT,                               -- 'critical', 'important', 'minor', 'enhancement'
    status                  TEXT DEFAULT 'new',                 -- 'new', 'reviewed', 'in_progress', 'implemented', 'wont_fix', 'duplicate'
    reviewed_by             TEXT,                               -- Who reviewed this feedback
    reviewed_at             DATETIME,
    resolution_notes        TEXT,                               -- How this was resolved
    led_to_improvement      INTEGER DEFAULT 0,                  -- Did this lead to system improvement?
    improvement_description TEXT,                               -- What improvement was made
    submitted_by            TEXT,
    submitted_at            DATETIME NOT NULL,
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Project Context Notes
-- Free-form contextual information about projects
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_context_notes (
    note_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id              INTEGER NOT NULL,
    note_type               TEXT NOT NULL,                      -- 'background', 'challenge', 'special_requirement', 'client_preference', 'constraint', 'opportunity', 'risk', 'assumption'
    note_category           TEXT,                               -- 'technical', 'financial', 'legal', 'operational', 'relationship', 'strategic'
    note_title              TEXT,
    note_content            TEXT NOT NULL,
    importance              INTEGER DEFAULT 3,                  -- 1=critical, 5=informational
    visibility              TEXT DEFAULT 'internal',            -- 'internal', 'team', 'client_shared'
    source                  TEXT,                               -- Where this information came from
    source_date             DATE,                               -- When this information was obtained
    is_verified             INTEGER DEFAULT 0,                  -- Has this been verified?
    verified_by             TEXT,
    verified_at             DATETIME,
    is_active               INTEGER DEFAULT 1,                  -- Is this note still relevant?
    superseded_by           INTEGER,                            -- Reference to note that replaces this one
    related_notes           TEXT,                               -- JSON array of related note_ids
    tags                    TEXT,                               -- JSON array of tags
    created_by              TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (superseded_by) REFERENCES project_context_notes(note_id) ON DELETE SET NULL
);

-- ============================================================================
-- Learning Events
-- Track significant learning events for continuous improvement
-- ============================================================================
CREATE TABLE IF NOT EXISTS learning_events (
    event_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type              TEXT NOT NULL,                      -- 'pattern_discovered', 'error_corrected', 'new_rule_created', 'model_retrained', 'accuracy_improved', 'user_taught_system'
    event_category          TEXT,                               -- 'email_processing', 'document_extraction', 'project_matching', 'financial_analysis', 'schedule_tracking'
    description             TEXT NOT NULL,                      -- What was learned
    trigger_source          TEXT,                               -- What triggered this learning: 'user_feedback', 'audit_answer', 'error_correction', 'pattern_analysis'
    trigger_id              TEXT,                               -- ID of triggering entity
    before_state            TEXT,                               -- State before learning (JSON)
    after_state             TEXT,                               -- State after learning (JSON)
    accuracy_before         REAL,                               -- Accuracy metric before learning
    accuracy_after          REAL,                               -- Accuracy metric after learning
    improvement_percentage  REAL,                               -- Percentage improvement
    affected_records        INTEGER,                            -- How many records were affected
    rule_or_pattern         TEXT,                               -- New rule or pattern discovered (JSON)
    confidence_score        REAL,                               -- Confidence in this learning (0-1)
    requires_review         INTEGER DEFAULT 0,                  -- Does this need human review?
    reviewed_by             TEXT,
    reviewed_at             DATETIME,
    approval_status         TEXT DEFAULT 'pending',             -- 'pending', 'approved', 'rejected', 'modified'
    applied_at              DATETIME,                           -- When this learning was applied
    event_date              DATETIME NOT NULL,
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_audit_questions_project
    ON audit_questions(project_id);

CREATE INDEX IF NOT EXISTS idx_audit_questions_status
    ON audit_questions(status, priority);

CREATE INDEX IF NOT EXISTS idx_audit_questions_category
    ON audit_questions(question_category);

CREATE INDEX IF NOT EXISTS idx_audit_answers_question
    ON audit_answers(question_id);

CREATE INDEX IF NOT EXISTS idx_audit_answers_project
    ON audit_answers(project_id);

CREATE INDEX IF NOT EXISTS idx_audit_answers_status
    ON audit_answers(verification_status);

CREATE INDEX IF NOT EXISTS idx_user_feedback_type
    ON user_feedback(feedback_type, status);

CREATE INDEX IF NOT EXISTS idx_user_feedback_context
    ON user_feedback(context_type, context_id);

CREATE INDEX IF NOT EXISTS idx_user_feedback_submitted
    ON user_feedback(submitted_at DESC);

CREATE INDEX IF NOT EXISTS idx_project_context_notes_project
    ON project_context_notes(project_id, is_active);

CREATE INDEX IF NOT EXISTS idx_project_context_notes_type
    ON project_context_notes(note_type, importance);

CREATE INDEX IF NOT EXISTS idx_learning_events_type
    ON learning_events(event_type, event_category);

CREATE INDEX IF NOT EXISTS idx_learning_events_date
    ON learning_events(event_date DESC);

CREATE INDEX IF NOT EXISTS idx_learning_events_approval
    ON learning_events(approval_status, requires_review);

-- ============================================================================
-- Triggers for auto-updating timestamps
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_audit_answers_timestamp
    AFTER UPDATE ON audit_answers
BEGIN
    UPDATE audit_answers SET updated_at = CURRENT_TIMESTAMP
    WHERE answer_id = NEW.answer_id;
END;

CREATE TRIGGER IF NOT EXISTS update_user_feedback_timestamp
    AFTER UPDATE ON user_feedback
BEGIN
    UPDATE user_feedback SET updated_at = CURRENT_TIMESTAMP
    WHERE feedback_id = NEW.feedback_id;
END;

CREATE TRIGGER IF NOT EXISTS update_project_context_notes_timestamp
    AFTER UPDATE ON project_context_notes
BEGIN
    UPDATE project_context_notes SET updated_at = CURRENT_TIMESTAMP
    WHERE note_id = NEW.note_id;
END;

-- ============================================================================
-- Trigger to mark question as answered when answer is provided
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS mark_question_answered
    AFTER INSERT ON audit_answers
BEGIN
    UPDATE audit_questions
    SET status = 'answered'
    WHERE question_id = NEW.question_id AND status = 'pending';
END;

-- ============================================================================
-- Trigger to calculate improvement percentage
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS calculate_improvement_percentage
    AFTER INSERT ON learning_events
    WHEN NEW.accuracy_before IS NOT NULL AND NEW.accuracy_after IS NOT NULL
BEGIN
    UPDATE learning_events
    SET improvement_percentage = ((NEW.accuracy_after - NEW.accuracy_before) / NEW.accuracy_before) * 100
    WHERE event_id = NEW.event_id;
END;
