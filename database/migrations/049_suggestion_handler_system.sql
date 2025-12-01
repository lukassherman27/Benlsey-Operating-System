-- Migration 049: Suggestion Handler System
-- Created: 2025-12-01
-- Description: Add tasks table, suggestion_changes audit trail, and rollback columns to ai_suggestions

-- =============================================================================
-- 1. TASKS TABLE (for follow_up_needed suggestions)
-- =============================================================================
CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    task_type TEXT CHECK(task_type IN ('follow_up', 'action_item', 'deadline', 'reminder')),
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    due_date DATE,
    project_code TEXT,
    proposal_id INTEGER,
    source_suggestion_id INTEGER,
    source_email_id INTEGER,
    created_at DATETIME DEFAULT (datetime('now')),
    completed_at DATETIME,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    FOREIGN KEY (source_suggestion_id) REFERENCES ai_suggestions(suggestion_id)
);

-- =============================================================================
-- 2. SUGGESTION_CHANGES TABLE (audit trail for rollback)
-- =============================================================================
CREATE TABLE IF NOT EXISTS suggestion_changes (
    change_id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id INTEGER NOT NULL,
    table_name TEXT NOT NULL,
    record_id INTEGER,
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    change_type TEXT NOT NULL CHECK(change_type IN ('insert', 'update', 'delete')),
    changed_at DATETIME DEFAULT (datetime('now')),
    rolled_back INTEGER DEFAULT 0,
    rolled_back_at DATETIME,
    FOREIGN KEY (suggestion_id) REFERENCES ai_suggestions(suggestion_id)
);

-- =============================================================================
-- 3. ALTER AI_SUGGESTIONS: Add rollback_data and is_actionable columns
-- =============================================================================
ALTER TABLE ai_suggestions ADD COLUMN rollback_data TEXT;

ALTER TABLE ai_suggestions ADD COLUMN is_actionable INTEGER DEFAULT 1;

-- =============================================================================
-- 4. INDEXES FOR TASKS TABLE
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_code);

CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);

CREATE INDEX IF NOT EXISTS idx_tasks_proposal ON tasks(proposal_id);

CREATE INDEX IF NOT EXISTS idx_tasks_source_suggestion ON tasks(source_suggestion_id);

-- =============================================================================
-- 5. INDEXES FOR SUGGESTION_CHANGES TABLE
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_suggestion_changes_suggestion ON suggestion_changes(suggestion_id);

CREATE INDEX IF NOT EXISTS idx_suggestion_changes_table ON suggestion_changes(table_name, record_id);
