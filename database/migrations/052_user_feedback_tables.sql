-- Migration 052: User Feedback Tables for Enhanced Review UI
-- Purpose: Store user notes, tags, contact roles, and action tracking for suggestions
-- Created: 2025-12-02
-- Applied: 2025-12-02 (manually)

-- ============================================================================
-- 1. SUGGESTION USER FEEDBACK TABLE
-- Stores user-provided context when reviewing suggestions
-- Named "suggestion_user_feedback" to avoid conflict with existing "user_feedback"
-- ============================================================================

CREATE TABLE IF NOT EXISTS suggestion_user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id INTEGER NOT NULL,

    -- User-provided context
    context_notes TEXT,              -- Free-form notes about this suggestion
    tags TEXT,                       -- JSON array of tags e.g., ["urgent", "client-contact"]
    contact_role TEXT,               -- For contact suggestions: Client, PM, Architect, etc.
    priority TEXT,                   -- User-assigned priority: high, medium, low

    -- Metadata
    created_by TEXT DEFAULT 'user',  -- Who created this feedback
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (suggestion_id) REFERENCES ai_suggestions(suggestion_id)
        ON DELETE CASCADE
);

-- Index for fast lookup by suggestion
CREATE INDEX IF NOT EXISTS idx_suggestion_user_feedback_suggestion
    ON suggestion_user_feedback(suggestion_id);


-- ============================================================================
-- 2. SUGGESTION ACTIONS TABLE
-- Tracks what actions were taken when approving a suggestion
-- (used for multi-action approvals)
-- ============================================================================

CREATE TABLE IF NOT EXISTS suggestion_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id INTEGER NOT NULL,

    -- Action details
    action_type TEXT NOT NULL,       -- 'link_email', 'update_fee', 'link_contact', 'learn_pattern'
    action_data TEXT,                -- JSON: specific data for this action
    action_status TEXT DEFAULT 'applied',  -- 'applied', 'skipped', 'failed'
    error_message TEXT,              -- If action failed, the reason

    -- Rollback support
    rollback_data TEXT,              -- JSON: data needed to undo this action
    rolled_back_at TEXT,             -- If rolled back, when

    -- Metadata
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
    applied_by TEXT DEFAULT 'user',

    FOREIGN KEY (suggestion_id) REFERENCES ai_suggestions(suggestion_id)
        ON DELETE CASCADE
);

-- Indexes for suggestion_actions
CREATE INDEX IF NOT EXISTS idx_suggestion_actions_suggestion
    ON suggestion_actions(suggestion_id);
CREATE INDEX IF NOT EXISTS idx_suggestion_actions_type
    ON suggestion_actions(action_type);


-- ============================================================================
-- 3. COMMON TAGS TABLE (for autocomplete)
-- ============================================================================

CREATE TABLE IF NOT EXISTS suggestion_tags (
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT UNIQUE NOT NULL,
    tag_category TEXT,               -- 'project', 'contact', 'action', 'priority'
    usage_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Insert common tags
INSERT OR IGNORE INTO suggestion_tags (tag_name, tag_category) VALUES
    ('urgent', 'priority'),
    ('follow-up', 'action'),
    ('client-contact', 'contact'),
    ('vendor-contact', 'contact'),
    ('architect', 'contact'),
    ('consultant', 'contact'),
    ('fee-discussion', 'project'),
    ('scope-change', 'project'),
    ('schedule-update', 'project'),
    ('payment-related', 'project'),
    ('rfi', 'project'),
    ('meeting-notes', 'project'),
    ('needs-review', 'action'),
    ('auto-link', 'action'),
    ('manual-link', 'action');


-- ============================================================================
-- 4. ADD COLUMNS TO AI_SUGGESTIONS FOR ENHANCED TRACKING
-- ============================================================================

-- Note: Run these only if columns don't exist (will error if they do, that's OK)
-- ALTER TABLE ai_suggestions ADD COLUMN detected_entities TEXT;
-- ALTER TABLE ai_suggestions ADD COLUMN suggested_actions TEXT;
