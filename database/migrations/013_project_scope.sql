-- Migration 013: Project Scope & Disciplines
-- Created: 2025-11-23
-- Description: Track project scope of work, disciplines involved, and fee allocation
--              This enables detailed financial analysis and workload distribution tracking

-- ============================================================================
-- Project Disciplines Table
-- Tracks which disciplines (Architecture, MEP, Interior Design, etc.) are included
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_disciplines (
    discipline_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id              INTEGER NOT NULL,
    discipline_name         TEXT NOT NULL,                      -- 'Architecture', 'MEP', 'Interior Design', 'Landscape', 'Structural', 'FF&E'
    scope_description       TEXT,                               -- Detailed description of what's included
    allocated_fee_usd       REAL,                               -- Fee allocated to this discipline
    allocated_percentage    REAL,                               -- Percentage of total project fee
    responsible_person      TEXT,                               -- Lead for this discipline
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    UNIQUE(project_id, discipline_name)
);

-- ============================================================================
-- Project Scope of Work
-- Tracks deliverables, exclusions, and scope changes
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_scope (
    scope_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id              INTEGER NOT NULL,
    scope_type              TEXT NOT NULL,                      -- 'deliverable', 'exclusion', 'assumption', 'change_order'
    item_description        TEXT NOT NULL,                      -- What's included/excluded
    category                TEXT,                               -- 'Design Phases', 'Documentation', 'Coordination', 'Site Visits', 'Meetings'
    quantity                INTEGER,                            -- Number of iterations, visits, meetings, etc.
    unit_description        TEXT,                               -- 'visits', 'meetings', 'revisions', 'sets'
    impact_on_fee           REAL,                               -- Fee impact if scope_type = 'change_order'
    impact_on_timeline_days INTEGER,                            -- Timeline impact
    status                  TEXT DEFAULT 'active',              -- 'active', 'removed', 'superseded'
    effective_date          DATE,                               -- When this scope item became effective
    source_document         TEXT,                               -- Reference to contract/proposal/change order
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_project_disciplines_project
    ON project_disciplines(project_id);

CREATE INDEX IF NOT EXISTS idx_project_disciplines_name
    ON project_disciplines(discipline_name);

CREATE INDEX IF NOT EXISTS idx_project_scope_project
    ON project_scope(project_id);

CREATE INDEX IF NOT EXISTS idx_project_scope_type
    ON project_scope(scope_type, status);

CREATE INDEX IF NOT EXISTS idx_project_scope_category
    ON project_scope(category);

-- ============================================================================
-- Triggers for auto-updating timestamps
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_project_disciplines_timestamp
    AFTER UPDATE ON project_disciplines
BEGIN
    UPDATE project_disciplines SET updated_at = CURRENT_TIMESTAMP
    WHERE discipline_id = NEW.discipline_id;
END;

CREATE TRIGGER IF NOT EXISTS update_project_scope_timestamp
    AFTER UPDATE ON project_scope
BEGIN
    UPDATE project_scope SET updated_at = CURRENT_TIMESTAMP
    WHERE scope_id = NEW.scope_id;
END;
