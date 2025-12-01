-- Migration 051: Email Learned Patterns - AI Learning Loop for Email Links
-- Created: 2025-12-01
-- Description: Store patterns learned from approved email->project link suggestions
--
-- This enables the system to:
-- 1. Learn from human-approved email->project links
-- 2. Suggest the same project for emails from same sender/domain
-- 3. Increase confidence with each approval
-- 4. Build institutional knowledge over time
--
-- NOTE: This is separate from the general learned_patterns table which handles
-- business rules and other learning patterns.

-- =============================================================================
-- 1. EMAIL_LEARNED_PATTERNS TABLE
-- =============================================================================
-- Stores patterns extracted from approved email link suggestions
-- Used to improve future email->project link suggestions

CREATE TABLE IF NOT EXISTS email_learned_patterns (
    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Pattern definition
    pattern_type TEXT NOT NULL CHECK(pattern_type IN (
        'sender_to_project',     -- "emails from X@company.com -> project Y"
        'sender_to_proposal',    -- "emails from X@company.com -> proposal Y"
        'domain_to_project',     -- "emails from @rosewood.com -> Rosewood project"
        'domain_to_proposal',    -- "emails from @domain.com -> proposal Y"
        'keyword_to_project',    -- "emails mentioning 'Dubai villa' -> Dubai project"
        'keyword_to_proposal',   -- "emails mentioning 'Qatar eco' -> Qatar proposal"
        'contact_to_project',    -- "contact X is associated with project Y"
        'sender_name_to_project',-- "emails from 'John Smith' -> project Y" (name-based)
        'sender_name_to_proposal'-- "emails from 'John Smith' -> proposal Y"
    )),

    -- The pattern key (what we match against)
    pattern_key TEXT NOT NULL,  -- e.g., 'nigel@rosewood.com', '@rosewood.com', 'dubai project'
    pattern_key_normalized TEXT, -- lowercase, trimmed for matching

    -- What this pattern links to
    target_type TEXT NOT NULL CHECK(target_type IN ('project', 'proposal')),
    target_id INTEGER NOT NULL,   -- project_id or proposal_id
    target_code TEXT,             -- 'BK-070' for quick reference
    target_name TEXT,             -- Project/proposal name for display

    -- Confidence tracking
    confidence REAL DEFAULT 0.7 CHECK(confidence >= 0 AND confidence <= 1),
    times_used INTEGER DEFAULT 0,       -- How often this pattern suggested a link
    times_correct INTEGER DEFAULT 0,    -- How often suggestion was approved
    times_rejected INTEGER DEFAULT 0,   -- How often suggestion was rejected

    -- Provenance: where did this pattern come from?
    created_from_suggestion_id INTEGER, -- Original suggestion that created this pattern
    created_from_email_id INTEGER,      -- Email that triggered the original suggestion

    -- Metadata
    is_active INTEGER DEFAULT 1,        -- Can be disabled without deletion
    notes TEXT,                         -- Human notes about this pattern

    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    last_used_at TEXT,                  -- Last time this pattern was used for a suggestion

    -- Constraints
    UNIQUE(pattern_type, pattern_key_normalized, target_type, target_id),
    FOREIGN KEY (created_from_suggestion_id) REFERENCES ai_suggestions(suggestion_id)
);

-- =============================================================================
-- 2. EMAIL_PATTERN_USAGE_LOG TABLE
-- =============================================================================
-- Track every time an email pattern is used to make/influence a suggestion
-- Enables analysis and debugging of the learning system

CREATE TABLE IF NOT EXISTS email_pattern_usage_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,

    pattern_id INTEGER NOT NULL,
    suggestion_id INTEGER,              -- The suggestion this pattern influenced
    email_id INTEGER,                   -- The email being analyzed

    -- What happened
    action TEXT NOT NULL CHECK(action IN (
        'matched',      -- Pattern matched this email
        'suggested',    -- Pattern led to a suggestion
        'approved',     -- User approved the pattern-based suggestion
        'rejected',     -- User rejected the pattern-based suggestion
        'boosted'       -- Pattern boosted confidence of an existing suggestion
    )),

    -- Context
    match_score REAL,                   -- How well the pattern matched (0-1)
    confidence_contribution REAL,       -- How much this pattern added to confidence

    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (pattern_id) REFERENCES email_learned_patterns(pattern_id),
    FOREIGN KEY (suggestion_id) REFERENCES ai_suggestions(suggestion_id)
);

-- =============================================================================
-- 3. INDEXES FOR PERFORMANCE
-- =============================================================================

-- Fast pattern lookup by key
CREATE INDEX IF NOT EXISTS idx_email_patterns_key ON email_learned_patterns(pattern_key_normalized);

-- Find patterns by type
CREATE INDEX IF NOT EXISTS idx_email_patterns_type ON email_learned_patterns(pattern_type);

-- Find active patterns for a target
CREATE INDEX IF NOT EXISTS idx_email_patterns_target ON email_learned_patterns(target_type, target_id);

-- Find patterns by project code
CREATE INDEX IF NOT EXISTS idx_email_patterns_project_code ON email_learned_patterns(target_code);

-- Find high-confidence active patterns
CREATE INDEX IF NOT EXISTS idx_email_patterns_active_confidence ON email_learned_patterns(is_active, confidence DESC)
    WHERE is_active = 1;

-- Pattern usage log indexes
CREATE INDEX IF NOT EXISTS idx_email_pattern_usage_pattern ON email_pattern_usage_log(pattern_id);
CREATE INDEX IF NOT EXISTS idx_email_pattern_usage_suggestion ON email_pattern_usage_log(suggestion_id);
CREATE INDEX IF NOT EXISTS idx_email_pattern_usage_email ON email_pattern_usage_log(email_id);

-- =============================================================================
-- 4. TRIGGERS
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS trg_email_patterns_updated_at
AFTER UPDATE ON email_learned_patterns
FOR EACH ROW
BEGIN
    UPDATE email_learned_patterns
    SET updated_at = datetime('now')
    WHERE pattern_id = NEW.pattern_id;
END;

-- =============================================================================
-- 5. VIEWS FOR ANALYSIS
-- =============================================================================

-- View: Email pattern effectiveness summary
CREATE VIEW IF NOT EXISTS v_email_pattern_effectiveness AS
SELECT
    lp.pattern_id,
    lp.pattern_type,
    lp.pattern_key,
    lp.target_code,
    lp.target_name,
    lp.confidence,
    lp.times_used,
    lp.times_correct,
    lp.times_rejected,
    CASE
        WHEN lp.times_used > 0
        THEN ROUND(lp.times_correct * 1.0 / lp.times_used, 2)
        ELSE 0
    END as success_rate,
    lp.is_active,
    lp.created_at,
    lp.last_used_at
FROM email_learned_patterns lp
ORDER BY lp.times_used DESC, lp.confidence DESC;

-- View: Email patterns by project
CREATE VIEW IF NOT EXISTS v_email_patterns_by_project AS
SELECT
    lp.target_code as project_code,
    lp.target_name as project_name,
    COUNT(*) as pattern_count,
    SUM(CASE WHEN lp.pattern_type = 'sender_to_project' THEN 1 ELSE 0 END) as sender_patterns,
    SUM(CASE WHEN lp.pattern_type = 'domain_to_project' THEN 1 ELSE 0 END) as domain_patterns,
    SUM(CASE WHEN lp.pattern_type = 'keyword_to_project' THEN 1 ELSE 0 END) as keyword_patterns,
    AVG(lp.confidence) as avg_confidence,
    SUM(lp.times_used) as total_uses,
    SUM(lp.times_correct) as total_correct
FROM email_learned_patterns lp
WHERE lp.target_type = 'project' AND lp.is_active = 1
GROUP BY lp.target_code, lp.target_name
ORDER BY pattern_count DESC;
