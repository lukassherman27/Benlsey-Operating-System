-- Migration 054: Contact Context Learning System
-- Stores rich context about contacts learned from user feedback
-- This enables intelligent email handling based on contact role/relationship

-- ============================================================================
-- CONTACT CONTEXT TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS contact_context (
    context_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Link to contact (can be by email or contact_id)
    contact_id INTEGER,
    email TEXT NOT NULL,

    -- Extracted role information
    role TEXT,                    -- e.g., 'kitchen consultant', 'project manager', 'IT support'
    role_confidence REAL DEFAULT 0.8,

    -- Relationship classification
    relationship_type TEXT CHECK(relationship_type IN (
        'client',           -- Client contact, primary stakeholder
        'client_team',      -- Client's team member
        'vendor',           -- External vendor/supplier
        'contractor',       -- Consultant/contractor
        'internal',         -- Internal team member
        'external',         -- External but not client/vendor
        'unknown'           -- Not yet classified
    )) DEFAULT 'unknown',

    -- Contact behavior flags
    is_client BOOLEAN DEFAULT NULL,           -- Explicitly: is this a client contact?
    is_multi_project BOOLEAN DEFAULT NULL,    -- Works across multiple projects?
    is_decision_maker BOOLEAN DEFAULT NULL,   -- Can approve/sign-off?

    -- Email handling preferences
    email_handling_preference TEXT CHECK(email_handling_preference IN (
        'link_to_project',      -- Always try to link to specific project
        'categorize_only',      -- Just categorize, don't link
        'suggest_multiple',     -- May relate to multiple projects
        'ignore',               -- Don't process (spam, automated, etc.)
        'default'               -- Use default handling
    )) DEFAULT 'default',

    -- Default category for this contact's emails
    default_category TEXT,        -- e.g., 'External', 'Internal', 'Vendor'
    default_subcategory TEXT,     -- e.g., 'IT', 'Kitchen', 'Landscape'

    -- Company/Organization context
    company TEXT,
    company_type TEXT,            -- e.g., 'design firm', 'hotel chain', 'supplier'

    -- Free-form context notes
    context_notes TEXT,           -- User's original notes
    structured_notes TEXT,        -- AI-structured version of notes

    -- Provenance: where did this context come from?
    learned_from TEXT CHECK(learned_from IN (
        'user_correction',        -- User corrected a suggestion with notes
        'user_approval',          -- User approved with context
        'email_analysis',         -- Extracted from email content
        'transcript_mention',     -- Mentioned in meeting transcript
        'manual_entry',           -- Manually entered by user
        'inferred'                -- System inferred from patterns
    )),
    learned_from_suggestion_id INTEGER,   -- Suggestion that triggered learning
    learned_from_email_id INTEGER,        -- Email that provided context

    -- Confidence and usage tracking
    confidence REAL DEFAULT 0.7 CHECK(confidence >= 0 AND confidence <= 1),
    times_validated INTEGER DEFAULT 0,    -- How many times context was confirmed
    times_contradicted INTEGER DEFAULT 0, -- How many times context was wrong

    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    last_used_at TEXT,

    -- Constraints
    UNIQUE(email),
    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id),
    FOREIGN KEY (learned_from_suggestion_id) REFERENCES ai_suggestions(suggestion_id)
);

-- Index for lookups
CREATE INDEX IF NOT EXISTS idx_contact_context_email ON contact_context(email);
CREATE INDEX IF NOT EXISTS idx_contact_context_contact_id ON contact_context(contact_id);
CREATE INDEX IF NOT EXISTS idx_contact_context_relationship ON contact_context(relationship_type);
CREATE INDEX IF NOT EXISTS idx_contact_context_multi_project ON contact_context(is_multi_project);

-- Update trigger
CREATE TRIGGER IF NOT EXISTS trg_contact_context_updated_at
AFTER UPDATE ON contact_context
FOR EACH ROW
BEGIN
    UPDATE contact_context
    SET updated_at = datetime('now')
    WHERE context_id = NEW.context_id;
END;


-- ============================================================================
-- CONTACT CONTEXT HISTORY TABLE
-- Track how context evolves over time
-- ============================================================================

CREATE TABLE IF NOT EXISTS contact_context_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    context_id INTEGER NOT NULL,
    email TEXT NOT NULL,

    -- What changed
    change_type TEXT NOT NULL CHECK(change_type IN (
        'created', 'updated', 'role_changed', 'relationship_changed',
        'flags_changed', 'confidence_adjusted'
    )),

    -- Previous values (JSON)
    previous_values TEXT,

    -- New values (JSON)
    new_values TEXT,

    -- Why the change happened
    change_reason TEXT,
    changed_by TEXT,

    -- Source of change
    source_suggestion_id INTEGER,
    source_email_id INTEGER,

    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (context_id) REFERENCES contact_context(context_id)
);

CREATE INDEX IF NOT EXISTS idx_contact_context_history_context ON contact_context_history(context_id);
CREATE INDEX IF NOT EXISTS idx_contact_context_history_email ON contact_context_history(email);


-- ============================================================================
-- EXTEND EMAIL_LEARNED_PATTERNS FOR RICH CONTEXT
-- ============================================================================

-- Add columns to track context-based patterns
ALTER TABLE email_learned_patterns ADD COLUMN contact_context_id INTEGER REFERENCES contact_context(context_id);
ALTER TABLE email_learned_patterns ADD COLUMN uses_contact_context BOOLEAN DEFAULT 0;
ALTER TABLE email_learned_patterns ADD COLUMN context_role TEXT;
ALTER TABLE email_learned_patterns ADD COLUMN context_relationship TEXT;


-- ============================================================================
-- VIEW: Contact Context Summary
-- ============================================================================

CREATE VIEW IF NOT EXISTS v_contact_context_summary AS
SELECT
    cc.context_id,
    cc.email,
    cc.contact_id,
    c.name as contact_name,
    cc.role,
    cc.relationship_type,
    cc.is_client,
    cc.is_multi_project,
    cc.email_handling_preference,
    cc.default_category,
    cc.company,
    cc.confidence,
    cc.times_validated,
    cc.context_notes,
    cc.learned_from,
    cc.created_at,
    cc.updated_at,
    -- Calculate effective confidence
    CASE
        WHEN cc.times_validated + cc.times_contradicted = 0 THEN cc.confidence
        ELSE cc.confidence * (1.0 * cc.times_validated / (cc.times_validated + cc.times_contradicted + 1))
    END as effective_confidence
FROM contact_context cc
LEFT JOIN contacts c ON cc.contact_id = c.contact_id;


-- ============================================================================
-- VIEW: Multi-project contacts (for special handling)
-- ============================================================================

CREATE VIEW IF NOT EXISTS v_multi_project_contacts AS
SELECT
    cc.email,
    cc.contact_id,
    c.name as contact_name,
    cc.role,
    cc.company,
    cc.context_notes,
    cc.confidence,
    COUNT(DISTINCT epl.project_id) as project_count,
    GROUP_CONCAT(DISTINCT p.project_code) as linked_projects
FROM contact_context cc
LEFT JOIN contacts c ON cc.contact_id = c.contact_id
LEFT JOIN emails e ON LOWER(e.sender_email) LIKE '%' || LOWER(cc.email) || '%'
LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
LEFT JOIN projects p ON epl.project_id = p.project_id
WHERE cc.is_multi_project = 1
GROUP BY cc.email;


-- ============================================================================
-- SEED: Context extraction prompts for common patterns
-- ============================================================================

-- Store prompts/patterns for extracting context
CREATE TABLE IF NOT EXISTS context_extraction_patterns (
    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name TEXT NOT NULL UNIQUE,
    pattern_regex TEXT,                    -- Regex to match user input
    extraction_template TEXT,              -- Template for AI extraction
    example_input TEXT,                    -- Example user input
    example_output TEXT,                   -- Expected structured output
    is_active BOOLEAN DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Seed common patterns
INSERT OR IGNORE INTO context_extraction_patterns (pattern_name, pattern_regex, example_input, example_output) VALUES
('consultant_role',
 '(?i)(consultant|specialist|advisor|expert)\s+(for|on|in)\s+(.+)',
 'Suresh is a kitchen consultant who works on many projects',
 '{"role": "kitchen consultant", "relationship_type": "contractor", "is_multi_project": true, "is_client": false}'),

('internal_role',
 '(?i)(our|internal|in-house)\s+(.+)',
 'John is our internal IT guy',
 '{"role": "IT", "relationship_type": "internal", "is_client": false}'),

('client_contact',
 '(?i)(client|client''?s?)\s+(contact|representative|person)',
 'Maria is the client contact for the Dubai project',
 '{"role": "client contact", "relationship_type": "client", "is_client": true, "is_multi_project": false}'),

('vendor_role',
 '(?i)(vendor|supplier|from)\s+(.+)',
 'James is from the furniture supplier',
 '{"role": "furniture supplier contact", "relationship_type": "vendor", "is_client": false}'),

('multi_project',
 '(?i)(many|multiple|several|various)\s+project',
 'She works on many projects, not just one',
 '{"is_multi_project": true}'),

('not_client',
 '(?i)(not|isn''t|isn''t a|not a)\s+client',
 'They are not a client, just a supplier',
 '{"is_client": false}');


-- ============================================================================
-- RECORD MIGRATION
-- ============================================================================

INSERT OR IGNORE INTO schema_migrations (version, name, description)
VALUES (54, '054_contact_context', 'Contact context learning system for rich contact understanding');
