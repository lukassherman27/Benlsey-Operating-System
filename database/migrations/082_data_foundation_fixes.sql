-- Migration 082: Data Foundation Fixes
-- Date: 2025-12-10
-- Purpose: Fix critical data issues identified in architecture audit
--
-- Issues Fixed:
-- 1. Backfill NULL due_date for 420 invoices (due_date = invoice_date + 30 days)
-- 2. Set is_active_project flag for proposals that became projects
-- 3. Create learning_events table (referenced by code but missing)
-- 4. Create proposal_status_history table for tracking changes over time

-- ============================================================================
-- 1. BACKFILL INVOICE DUE DATES
-- ============================================================================
-- Standard payment terms: Net 30 days

UPDATE invoices
SET due_date = date(invoice_date, '+30 days')
WHERE due_date IS NULL
  AND invoice_date IS NOT NULL;

-- Verify: SELECT COUNT(*) FROM invoices WHERE due_date IS NULL; -- Should be 0

-- ============================================================================
-- 2. SET is_active_project FLAG FOR CONVERTED PROPOSALS
-- ============================================================================
-- Mark proposals that have been converted to projects

UPDATE proposals
SET is_active_project = 1
WHERE project_code IN (SELECT project_code FROM projects WHERE project_code IS NOT NULL);

-- Verify: SELECT COUNT(*) FROM proposals WHERE is_active_project = 1; -- Should match project count

-- ============================================================================
-- 3. CREATE learning_events TABLE
-- ============================================================================
-- This table is referenced by learning_service.py but was never created

CREATE TABLE IF NOT EXISTS learning_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,  -- 'email_link_approved', 'email_link_rejected', 'pattern_created', etc.
    email_id INTEGER,
    sender_email TEXT,
    sender_domain TEXT,
    project_code TEXT,
    proposal_id INTEGER,
    project_id INTEGER,
    pattern_type TEXT,
    pattern_key TEXT,
    confidence_before REAL,
    confidence_after REAL,
    confidence_delta REAL,
    user_notes TEXT,
    gpt_reasoning TEXT,
    correct_project_code TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails(email_id),
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX IF NOT EXISTS idx_learning_events_type ON learning_events(event_type);
CREATE INDEX IF NOT EXISTS idx_learning_events_email ON learning_events(email_id);
CREATE INDEX IF NOT EXISTS idx_learning_events_project ON learning_events(project_code);
CREATE INDEX IF NOT EXISTS idx_learning_events_created ON learning_events(created_at);

-- ============================================================================
-- 4. CREATE proposal_status_history TABLE
-- ============================================================================
-- Track proposal status changes over time for analytics

CREATE TABLE IF NOT EXISTS proposal_status_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    project_code TEXT,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT DEFAULT 'system',
    notes TEXT,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

CREATE INDEX IF NOT EXISTS idx_proposal_status_history_proposal ON proposal_status_history(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_status_history_code ON proposal_status_history(project_code);
CREATE INDEX IF NOT EXISTS idx_proposal_status_history_date ON proposal_status_history(changed_at);

-- ============================================================================
-- 5. CREATE project_phase_history TABLE
-- ============================================================================
-- Track project phase changes over time

CREATE TABLE IF NOT EXISTS project_phase_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    project_code TEXT,
    old_phase TEXT,
    new_phase TEXT NOT NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    changed_by TEXT DEFAULT 'system',
    notes TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX IF NOT EXISTS idx_project_phase_history_project ON project_phase_history(project_id);
CREATE INDEX IF NOT EXISTS idx_project_phase_history_code ON project_phase_history(project_code);
CREATE INDEX IF NOT EXISTS idx_project_phase_history_date ON project_phase_history(started_at);

-- ============================================================================
-- 6. SEED INITIAL STATUS HISTORY FROM CURRENT DATA
-- ============================================================================
-- Capture current state as starting point for tracking

INSERT INTO proposal_status_history (proposal_id, project_code, old_status, new_status, changed_at, changed_by, notes)
SELECT
    proposal_id,
    project_code,
    NULL,
    current_status,
    COALESCE(created_at, datetime('now')),
    'migration_082',
    'Initial status from migration 082 - capturing current state'
FROM proposals
WHERE current_status IS NOT NULL;

-- ============================================================================
-- VERIFICATION QUERIES (run manually after migration)
-- ============================================================================
-- SELECT 'Invoices with due_date' as metric, COUNT(*) FROM invoices WHERE due_date IS NOT NULL;
-- SELECT 'Proposals marked as active_project' as metric, COUNT(*) FROM proposals WHERE is_active_project = 1;
-- SELECT 'Learning events table exists' as metric, COUNT(*) FROM sqlite_master WHERE name='learning_events';
-- SELECT 'Status history records' as metric, COUNT(*) FROM proposal_status_history;
