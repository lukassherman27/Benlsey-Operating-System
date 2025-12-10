-- Migration 063: Extend email_learned_patterns with new pattern types
--
-- Adds support for:
-- - Internal category patterns (domain_to_internal, sender_to_internal)
-- - Skip patterns (domain_to_skip, sender_to_skip)
-- - Project redirects (project_redirect)
-- - Thread patterns (thread_to_project, thread_to_proposal)
--
-- Also extends target_type to support 'internal' and 'skip'

-- Step 1: Create new table with extended constraints
CREATE TABLE email_learned_patterns_new (
    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Pattern definition - EXTENDED with new types
    pattern_type TEXT NOT NULL CHECK(pattern_type IN (
        -- Original types
        'sender_to_project',      -- "emails from X@company.com -> project Y"
        'sender_to_proposal',     -- "emails from X@company.com -> proposal Y"
        'domain_to_project',      -- "emails from @rosewood.com -> Rosewood project"
        'domain_to_proposal',     -- "emails from @domain.com -> proposal Y"
        'keyword_to_project',     -- "emails mentioning 'Dubai villa' -> Dubai project"
        'keyword_to_proposal',    -- "emails mentioning 'Qatar eco' -> Qatar proposal"
        'contact_to_project',     -- "contact X is associated with project Y"
        'sender_name_to_project', -- "emails from 'John Smith' -> project Y"
        'sender_name_to_proposal',-- "emails from 'John Smith' -> proposal Y"
        -- NEW: Internal category patterns
        'sender_to_internal',     -- "emails from X -> internal category (INT-OPS, etc)"
        'domain_to_internal',     -- "emails from @naviworld.com -> INT-OPS"
        'keyword_to_internal',    -- "emails mentioning 'D365' -> INT-OPS"
        -- NEW: Skip patterns (cancelled projects, spam, etc)
        'sender_to_skip',         -- "emails from X -> skip (don't link)"
        'domain_to_skip',         -- "emails from @domain -> skip"
        'keyword_to_skip',        -- "emails mentioning 'unsubscribe' -> skip"
        -- NEW: Project redirect patterns
        'project_redirect',       -- "project X is merged into project Y"
        -- NEW: Thread-based patterns
        'thread_to_project',      -- "thread with ID X -> project Y"
        'thread_to_proposal'      -- "thread with ID X -> proposal Y"
    )),

    -- The pattern key (what we match against)
    pattern_key TEXT NOT NULL,
    pattern_key_normalized TEXT,

    -- What this pattern links to - EXTENDED
    target_type TEXT NOT NULL CHECK(target_type IN (
        'project',
        'proposal',
        'internal',  -- NEW: links to internal_categories
        'skip'       -- NEW: marks as skip/ignore
    )),
    target_id INTEGER NOT NULL,   -- project_id, proposal_id, or category_id
    target_code TEXT,             -- 'BK-070', 'INT-OPS', etc
    target_name TEXT,             -- Name for display

    -- Confidence tracking
    confidence REAL DEFAULT 0.7 CHECK(confidence >= 0 AND confidence <= 1),
    times_used INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    times_rejected INTEGER DEFAULT 0,

    -- Provenance
    created_from_suggestion_id INTEGER,
    created_from_email_id INTEGER,

    -- Metadata
    is_active INTEGER DEFAULT 1,
    notes TEXT,

    -- Contact context (existing fields)
    contact_context_id INTEGER,
    uses_contact_context BOOLEAN DEFAULT 0,
    context_role TEXT,
    context_relationship TEXT,

    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    last_used_at TEXT,

    -- Constraints
    UNIQUE(pattern_type, pattern_key_normalized, target_type, target_id),
    FOREIGN KEY (created_from_suggestion_id) REFERENCES ai_suggestions(suggestion_id),
    FOREIGN KEY (contact_context_id) REFERENCES contact_context(context_id)
);

-- Step 2: Copy existing data
INSERT INTO email_learned_patterns_new (
    pattern_id, pattern_type, pattern_key, pattern_key_normalized,
    target_type, target_id, target_code, target_name,
    confidence, times_used, times_correct, times_rejected,
    created_from_suggestion_id, created_from_email_id,
    is_active, notes,
    contact_context_id, uses_contact_context, context_role, context_relationship,
    created_at, updated_at, last_used_at
)
SELECT
    pattern_id, pattern_type, pattern_key, pattern_key_normalized,
    target_type, target_id, target_code, target_name,
    confidence, times_used, times_correct, times_rejected,
    created_from_suggestion_id, created_from_email_id,
    is_active, notes,
    contact_context_id, uses_contact_context, context_role, context_relationship,
    created_at, updated_at, last_used_at
FROM email_learned_patterns;

-- Step 3: Drop old table and rename new
DROP TABLE email_learned_patterns;
ALTER TABLE email_learned_patterns_new RENAME TO email_learned_patterns;

-- Step 4: Recreate indexes
CREATE INDEX idx_email_patterns_key ON email_learned_patterns(pattern_key_normalized);
CREATE INDEX idx_email_patterns_type ON email_learned_patterns(pattern_type);
CREATE INDEX idx_email_patterns_target ON email_learned_patterns(target_type, target_id);
CREATE INDEX idx_email_patterns_active_confidence ON email_learned_patterns(is_active, confidence DESC);

-- Step 5: Recreate trigger for updated_at
CREATE TRIGGER IF NOT EXISTS trg_email_patterns_updated_at
AFTER UPDATE ON email_learned_patterns
BEGIN
    UPDATE email_learned_patterns SET updated_at = datetime('now') WHERE pattern_id = NEW.pattern_id;
END;

-- Log migration (schema_version table may not exist in all environments)
-- INSERT INTO schema_version (version, description, applied_at)
-- VALUES (63, 'Extend email_learned_patterns with internal, skip, redirect, and thread pattern types', datetime('now'));
