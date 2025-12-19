-- Migration 086: Comprehensive Schema Enhancement
-- Purpose: Task hierarchy, deliverables, vector embeddings, attachment organization, calendar, commitments
-- Date: 2025-12-12

-- ============================================================================
-- SECTION 1: TASK SYSTEM ENHANCEMENT
-- ============================================================================

-- 1.1 Add parent_task_id for task hierarchy (parent-child relationships)
ALTER TABLE tasks ADD COLUMN parent_task_id INTEGER REFERENCES tasks(task_id);

-- 1.2 Add task category (10 categories as agreed)
ALTER TABLE tasks ADD COLUMN category TEXT DEFAULT 'Other';

-- 1.3 Add staff_id FK for proper assignment (keep assignee TEXT for backward compatibility)
ALTER TABLE tasks ADD COLUMN assigned_staff_id INTEGER REFERENCES staff(staff_id);

-- 1.4 Add deliverable link
ALTER TABLE tasks ADD COLUMN deliverable_id INTEGER;

-- 1.5 Indexes for task hierarchy and filtering
CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category);
CREATE INDEX IF NOT EXISTS idx_tasks_staff ON tasks(assigned_staff_id);
CREATE INDEX IF NOT EXISTS idx_tasks_deliverable ON tasks(deliverable_id);
CREATE INDEX IF NOT EXISTS idx_tasks_hierarchy ON tasks(parent_task_id, status);

-- ============================================================================
-- SECTION 2: DELIVERABLES TABLE (NEW - Was Missing!)
-- ============================================================================

CREATE TABLE IF NOT EXISTS deliverables (
    deliverable_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Project linkage
    project_id INTEGER,
    project_code TEXT,
    phase_id INTEGER REFERENCES contract_phases(phase_id),

    -- Core fields
    name TEXT NOT NULL,
    description TEXT,
    deliverable_type TEXT CHECK(deliverable_type IN (
        'drawing', 'presentation', 'document', 'model',
        'specification', 'report', 'review', 'other'
    )),

    -- Timeline
    due_date DATE,
    start_date DATE,
    actual_completion_date DATE,

    -- Status tracking
    status TEXT DEFAULT 'pending' CHECK(status IN (
        'pending', 'in_progress', 'submitted', 'revision',
        'approved', 'rejected', 'cancelled'
    )),
    priority TEXT DEFAULT 'normal' CHECK(priority IN ('low', 'normal', 'high', 'critical')),

    -- Ownership
    owner_staff_id INTEGER REFERENCES staff(staff_id),
    assigned_pm TEXT,

    -- Version tracking
    revision_number INTEGER DEFAULT 1,
    supersedes_deliverable_id INTEGER REFERENCES deliverables(deliverable_id),

    -- Attachments (JSON array of attachment_ids)
    attachments TEXT,

    -- Feedback
    client_feedback TEXT,
    internal_notes TEXT,

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',

    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- Deliverable indexes
CREATE INDEX IF NOT EXISTS idx_deliverables_project ON deliverables(project_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_project_code ON deliverables(project_code);
CREATE INDEX IF NOT EXISTS idx_deliverables_phase ON deliverables(phase_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_status ON deliverables(status);
CREATE INDEX IF NOT EXISTS idx_deliverables_due ON deliverables(due_date);
CREATE INDEX IF NOT EXISTS idx_deliverables_owner ON deliverables(owner_staff_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_priority_status ON deliverables(priority, status);

-- ============================================================================
-- SECTION 3: VECTOR EMBEDDINGS TABLES
-- ============================================================================

-- 3.1 Email embeddings table
CREATE TABLE IF NOT EXISTS email_embeddings (
    embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL UNIQUE,

    -- Embedding data
    embedding BLOB NOT NULL,
    embedding_dimensions INTEGER NOT NULL,

    -- Model tracking
    model_name TEXT NOT NULL,
    model_version TEXT,

    -- Content hash for cache invalidation
    content_hash TEXT,

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,

    FOREIGN KEY (email_id) REFERENCES emails(email_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_email_embeddings_email ON email_embeddings(email_id);
CREATE INDEX IF NOT EXISTS idx_email_embeddings_model ON email_embeddings(model_name);

-- 3.2 Document/Attachment embeddings table
CREATE TABLE IF NOT EXISTS document_embeddings (
    embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    attachment_id INTEGER NOT NULL UNIQUE,

    -- Embedding data
    embedding BLOB NOT NULL,
    embedding_dimensions INTEGER NOT NULL,

    -- Model tracking
    model_name TEXT NOT NULL,
    model_version TEXT,

    -- Processing info
    extracted_text_length INTEGER,
    content_hash TEXT,

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,

    FOREIGN KEY (attachment_id) REFERENCES email_attachments(attachment_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_doc_embeddings_attachment ON document_embeddings(attachment_id);
CREATE INDEX IF NOT EXISTS idx_doc_embeddings_model ON document_embeddings(model_name);

-- 3.3 Proposal embeddings (for semantic proposal search)
CREATE TABLE IF NOT EXISTS proposal_embeddings (
    embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL UNIQUE,

    -- Embedding data (combined from name, description, scope, notes)
    embedding BLOB NOT NULL,
    embedding_dimensions INTEGER NOT NULL,

    -- Model tracking
    model_name TEXT NOT NULL,
    model_version TEXT,

    -- What was embedded
    embedded_fields TEXT,
    content_hash TEXT,

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_proposal_embeddings_proposal ON proposal_embeddings(proposal_id);

-- 3.4 Contact embeddings (for finding similar contacts)
CREATE TABLE IF NOT EXISTS contact_embeddings (
    embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL UNIQUE,

    embedding BLOB NOT NULL,
    embedding_dimensions INTEGER NOT NULL,

    model_name TEXT NOT NULL,
    model_version TEXT,
    content_hash TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,

    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_contact_embeddings_contact ON contact_embeddings(contact_id);

-- ============================================================================
-- SECTION 4: ATTACHMENT ORGANIZATION
-- ============================================================================

-- 4.1 Add organized_path for folder structure
-- Structure: /attachments/{year}/{project_code}/{document_type}/{filename}
ALTER TABLE email_attachments ADD COLUMN organized_path TEXT;

-- 4.2 Add deliverable link for attachments
ALTER TABLE email_attachments ADD COLUMN deliverable_id INTEGER REFERENCES deliverables(deliverable_id);

-- 4.3 Add project_code for easier filtering (denormalized for performance)
ALTER TABLE email_attachments ADD COLUMN project_code TEXT;

-- 4.4 Add organization metadata
ALTER TABLE email_attachments ADD COLUMN organized_at DATETIME;
ALTER TABLE email_attachments ADD COLUMN organized_by TEXT;

-- 4.5 Indexes for organization
CREATE INDEX IF NOT EXISTS idx_attachments_organized ON email_attachments(organized_path);
CREATE INDEX IF NOT EXISTS idx_attachments_deliverable ON email_attachments(deliverable_id);
CREATE INDEX IF NOT EXISTS idx_attachments_project ON email_attachments(project_code);

-- ============================================================================
-- SECTION 5: CALENDAR/SCHEDULING ENHANCEMENT
-- ============================================================================

-- 5.1 Add recurring meeting support
ALTER TABLE meetings ADD COLUMN is_recurring INTEGER DEFAULT 0;
ALTER TABLE meetings ADD COLUMN recurrence_pattern TEXT;
ALTER TABLE meetings ADD COLUMN recurrence_end_date DATE;
ALTER TABLE meetings ADD COLUMN parent_meeting_id INTEGER REFERENCES meetings(meeting_id);
ALTER TABLE meetings ADD COLUMN occurrence_number INTEGER;

-- 5.2 Create time blocks table for calendar blocking
CREATE TABLE IF NOT EXISTS calendar_blocks (
    block_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Who and when
    staff_id INTEGER REFERENCES staff(staff_id),
    block_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    is_all_day INTEGER DEFAULT 0,

    -- What kind of block
    block_type TEXT CHECK(block_type IN (
        'focus_time', 'travel', 'vacation', 'sick', 'training',
        'client_visit', 'site_visit', 'admin', 'other'
    )) NOT NULL,

    title TEXT,
    description TEXT,

    -- Linkage (optional)
    project_code TEXT,
    meeting_id INTEGER REFERENCES meetings(meeting_id),

    -- Recurrence
    is_recurring INTEGER DEFAULT 0,
    recurrence_pattern TEXT,
    parent_block_id INTEGER REFERENCES calendar_blocks(block_id),

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_calendar_blocks_staff_date ON calendar_blocks(staff_id, block_date);
CREATE INDEX IF NOT EXISTS idx_calendar_blocks_type ON calendar_blocks(block_type);
CREATE INDEX IF NOT EXISTS idx_calendar_blocks_project ON calendar_blocks(project_code);

-- 5.3 Index for recurring meetings
CREATE INDEX IF NOT EXISTS idx_meetings_recurring ON meetings(is_recurring, parent_meeting_id);

-- ============================================================================
-- SECTION 6: COMMITMENTS TABLE (Tracking Promises)
-- ============================================================================

CREATE TABLE IF NOT EXISTS commitments (
    commitment_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Type: our promise vs their promise
    commitment_type TEXT CHECK(commitment_type IN ('our_commitment', 'their_commitment')),

    -- Details
    description TEXT NOT NULL,
    committed_by TEXT,

    -- Timeline
    due_date DATE,
    fulfillment_status TEXT DEFAULT 'pending' CHECK(fulfillment_status IN (
        'pending', 'fulfilled', 'overdue', 'waived'
    )),

    -- Linkage
    project_code TEXT,
    proposal_id INTEGER,
    source_email_id INTEGER,
    source_suggestion_id INTEGER,
    related_task_id INTEGER,

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    fulfilled_at DATETIME,

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    FOREIGN KEY (source_email_id) REFERENCES emails(email_id),
    FOREIGN KEY (source_suggestion_id) REFERENCES ai_suggestions(suggestion_id),
    FOREIGN KEY (related_task_id) REFERENCES tasks(task_id)
);

CREATE INDEX IF NOT EXISTS idx_commitments_status ON commitments(fulfillment_status);
CREATE INDEX IF NOT EXISTS idx_commitments_due ON commitments(due_date);
CREATE INDEX IF NOT EXISTS idx_commitments_project ON commitments(project_code);
CREATE INDEX IF NOT EXISTS idx_commitments_type ON commitments(commitment_type);

-- ============================================================================
-- SECTION 7: AI SUGGESTIONS ENHANCEMENT
-- ============================================================================

-- 7.1 Add auto-approval tracking
ALTER TABLE ai_suggestions ADD COLUMN auto_approved INTEGER DEFAULT 0;
ALTER TABLE ai_suggestions ADD COLUMN auto_approved_reason TEXT;
ALTER TABLE ai_suggestions ADD COLUMN auto_approved_at DATETIME;

-- ============================================================================
-- SECTION 8: HELPER VIEWS
-- ============================================================================

-- 8.1 Task hierarchy view with depth (recursive CTE)
CREATE VIEW IF NOT EXISTS v_task_hierarchy AS
WITH RECURSIVE task_tree AS (
    -- Root tasks (no parent)
    SELECT
        task_id, title, parent_task_id, status, category,
        assignee, due_date, project_code, proposal_id,
        0 AS depth,
        CAST(task_id AS TEXT) AS path
    FROM tasks
    WHERE parent_task_id IS NULL

    UNION ALL

    -- Child tasks
    SELECT
        t.task_id, t.title, t.parent_task_id, t.status, t.category,
        t.assignee, t.due_date, t.project_code, t.proposal_id,
        tt.depth + 1,
        tt.path || '/' || CAST(t.task_id AS TEXT)
    FROM tasks t
    JOIN task_tree tt ON t.parent_task_id = tt.task_id
    WHERE tt.depth < 10
)
SELECT * FROM task_tree;

-- 8.2 Deliverable progress view
CREATE VIEW IF NOT EXISTS v_deliverable_progress AS
SELECT
    d.deliverable_id,
    d.project_code,
    d.name,
    d.status,
    d.due_date,
    d.owner_staff_id,
    s.first_name AS owner_first_name,
    s.last_name AS owner_last_name,
    COUNT(t.task_id) AS total_tasks,
    SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) AS completed_tasks,
    ROUND(100.0 * SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) /
        NULLIF(COUNT(t.task_id), 0), 1) AS completion_percentage
FROM deliverables d
LEFT JOIN tasks t ON t.deliverable_id = d.deliverable_id
LEFT JOIN staff s ON d.owner_staff_id = s.staff_id
GROUP BY d.deliverable_id;

-- 8.3 Staff workload view
CREATE VIEW IF NOT EXISTS v_staff_workload AS
SELECT
    s.staff_id,
    s.first_name,
    s.last_name,
    s.email,
    COUNT(DISTINCT t.task_id) AS active_tasks,
    COUNT(DISTINCT CASE WHEN t.due_date < DATE('now') AND t.status NOT IN ('completed', 'cancelled') THEN t.task_id END) AS overdue_tasks,
    COUNT(DISTINCT d.deliverable_id) AS active_deliverables,
    COUNT(DISTINCT CASE WHEN m.meeting_date >= DATE('now') AND m.status IN ('scheduled', 'confirmed') THEN m.meeting_id END) AS upcoming_meetings
FROM staff s
LEFT JOIN tasks t ON t.assigned_staff_id = s.staff_id AND t.status NOT IN ('completed', 'cancelled')
LEFT JOIN deliverables d ON d.owner_staff_id = s.staff_id AND d.status NOT IN ('approved', 'cancelled')
LEFT JOIN meetings m ON m.participants LIKE '%' || s.email || '%'
WHERE s.is_active = 1
GROUP BY s.staff_id;

-- 8.4 Commitment summary view
CREATE VIEW IF NOT EXISTS v_commitment_summary AS
SELECT
    c.*,
    p.project_name,
    e.subject AS source_email_subject,
    t.title AS related_task_title,
    CASE
        WHEN c.due_date < DATE('now') AND c.fulfillment_status = 'pending' THEN 'overdue'
        WHEN c.due_date = DATE('now') THEN 'due_today'
        WHEN c.due_date <= DATE('now', '+7 days') THEN 'due_soon'
        ELSE 'on_track'
    END AS urgency
FROM commitments c
LEFT JOIN proposals p ON c.proposal_id = p.proposal_id
LEFT JOIN emails e ON c.source_email_id = e.email_id
LEFT JOIN tasks t ON c.related_task_id = t.task_id;

-- ============================================================================
-- SECTION 9: DATA BACKFILL
-- ============================================================================

-- 9.1 Backfill staff_id from TEXT assignee where possible
UPDATE tasks
SET assigned_staff_id = (
    SELECT s.staff_id
    FROM staff s
    WHERE LOWER(s.first_name) = LOWER(tasks.assignee)
    OR LOWER(s.nickname) = LOWER(tasks.assignee)
    LIMIT 1
)
WHERE assigned_staff_id IS NULL
AND assignee IS NOT NULL
AND assignee NOT IN ('us', 'them', 'Team', 'mutual');

-- 9.2 Set default category based on context
UPDATE tasks
SET category = CASE
    WHEN project_code IS NOT NULL AND project_code LIKE '%BK%' THEN 'Project'
    WHEN proposal_id IS NOT NULL THEN 'Proposal'
    ELSE 'Other'
END
WHERE category IS NULL OR category = 'Other';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Summary of changes:
-- 1. Tasks: parent_task_id, category, assigned_staff_id, deliverable_id + indexes
-- 2. Deliverables: NEW table with full lifecycle tracking
-- 3. Embeddings: 4 tables (email, document, proposal, contact)
-- 4. Attachments: organized_path, deliverable_id, project_code
-- 5. Meetings: recurring support, calendar_blocks table
-- 6. Commitments: NEW table for tracking promises
-- 7. AI Suggestions: auto_approved columns
-- 8. Views: v_task_hierarchy, v_deliverable_progress, v_staff_workload, v_commitment_summary
