-- Migration 015: Project Phase Timeline & Schedule Tracking
-- Created: 2025-11-23
-- Description: Track expected vs actual timeline for project phases and key milestones
--              Enables schedule analysis, delay tracking, and project health scoring

-- ============================================================================
-- Project Timeline
-- Tracks key dates and milestones for project execution
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_timeline (
    timeline_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id              INTEGER NOT NULL,
    milestone_name          TEXT NOT NULL,                      -- 'Contract Signing', 'Project Kickoff', 'First Submission', 'Client Approval', 'Final Handover'
    milestone_type          TEXT,                               -- 'contract', 'kickoff', 'submission', 'approval', 'delivery', 'meeting', 'site_visit', 'deadline'
    milestone_category      TEXT,                               -- 'internal', 'client', 'authority', 'contractor'
    phase_id                INTEGER,                            -- Link to specific phase if applicable
    planned_date            DATE,                               -- Originally planned date
    baseline_date           DATE,                               -- Baseline after first revision
    current_forecast_date   DATE,                               -- Current forecast/expected date
    actual_date             DATE,                               -- When it actually happened
    status                  TEXT DEFAULT 'planned',             -- 'planned', 'upcoming', 'in_progress', 'completed', 'missed', 'cancelled'
    days_variance           INTEGER,                            -- Difference between planned and actual (negative = early, positive = delayed)
    is_critical_path        INTEGER DEFAULT 0,                  -- Is this milestone on the critical path?
    dependencies            TEXT,                               -- JSON array of milestone_ids this depends on
    responsible_party       TEXT,                               -- Who is responsible: 'Bensley', 'Client', 'Consultant', 'Contractor'
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (phase_id) REFERENCES project_phases(phase_id) ON DELETE SET NULL
);

-- ============================================================================
-- Schedule Updates
-- Track changes to schedule over time (schedule revisions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS schedule_updates (
    update_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id              INTEGER NOT NULL,
    timeline_id             INTEGER,                            -- Which milestone was updated
    update_type             TEXT NOT NULL,                      -- 'initial_baseline', 'client_delay', 'scope_change', 'resource_issue', 'external_factor', 'acceleration'
    previous_date           DATE,                               -- Previous planned/forecast date
    new_date                DATE,                               -- New planned/forecast date
    days_shift              INTEGER,                            -- How many days the date shifted
    reason                  TEXT NOT NULL,                      -- Why the schedule changed
    impact_assessment       TEXT,                               -- Assessment of impact on project
    responsible_party       TEXT,                               -- Who caused this schedule change
    requires_client_notice  INTEGER DEFAULT 0,                  -- Does client need to be notified?
    notified_on             DATE,                               -- When client was notified
    update_date             DATE NOT NULL,                      -- When this update was made
    updated_by              TEXT,                               -- Who made this update
    source_document         TEXT,                               -- Reference to email/meeting notes/memo
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (timeline_id) REFERENCES project_timeline(timeline_id) ON DELETE CASCADE
);

-- ============================================================================
-- Project Delays
-- Track and categorize project delays for analysis
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_delays (
    delay_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id              INTEGER NOT NULL,
    timeline_id             INTEGER,                            -- Which milestone was delayed
    phase_id                INTEGER,                            -- Which phase was delayed
    delay_type              TEXT NOT NULL,                      -- 'client_feedback', 'client_approval', 'scope_change', 'information_pending', 'resource_unavailable', 'external_authority', 'weather', 'site_access'
    delay_category          TEXT,                               -- 'client_caused', 'bensley_caused', 'third_party', 'force_majeure'
    description             TEXT NOT NULL,
    impact_days             INTEGER NOT NULL,                   -- Number of days delayed
    impact_cost_usd         REAL,                               -- Financial impact if any
    start_date              DATE,                               -- When delay started
    resolution_date         DATE,                               -- When delay was resolved
    status                  TEXT DEFAULT 'active',              -- 'active', 'resolved', 'mitigated', 'accepted'
    mitigation_actions      TEXT,                               -- Actions taken to mitigate
    responsible_party       TEXT,                               -- Who is responsible for the delay
    is_recoverable          INTEGER DEFAULT 1,                  -- Can this delay be recovered?
    recovery_plan           TEXT,                               -- How we plan to recover the time
    requires_eot            INTEGER DEFAULT 0,                  -- Does this require Extension of Time claim?
    eot_submitted           INTEGER DEFAULT 0,                  -- Has EOT claim been submitted?
    eot_approved            INTEGER DEFAULT 0,                  -- Has EOT been approved?
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (timeline_id) REFERENCES project_timeline(timeline_id) ON DELETE SET NULL,
    FOREIGN KEY (phase_id) REFERENCES project_phases(phase_id) ON DELETE SET NULL
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_project_timeline_project
    ON project_timeline(project_id);

CREATE INDEX IF NOT EXISTS idx_project_timeline_status
    ON project_timeline(status, planned_date);

CREATE INDEX IF NOT EXISTS idx_project_timeline_phase
    ON project_timeline(phase_id);

CREATE INDEX IF NOT EXISTS idx_project_timeline_critical
    ON project_timeline(is_critical_path, status);

CREATE INDEX IF NOT EXISTS idx_schedule_updates_project
    ON schedule_updates(project_id, update_date DESC);

CREATE INDEX IF NOT EXISTS idx_schedule_updates_timeline
    ON schedule_updates(timeline_id);

CREATE INDEX IF NOT EXISTS idx_project_delays_project
    ON project_delays(project_id);

CREATE INDEX IF NOT EXISTS idx_project_delays_status
    ON project_delays(status, delay_category);

CREATE INDEX IF NOT EXISTS idx_project_delays_type
    ON project_delays(delay_type);

-- ============================================================================
-- Triggers for auto-updating timestamps and calculations
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_project_timeline_timestamp
    AFTER UPDATE ON project_timeline
BEGIN
    UPDATE project_timeline SET updated_at = CURRENT_TIMESTAMP
    WHERE timeline_id = NEW.timeline_id;
END;

CREATE TRIGGER IF NOT EXISTS update_project_delays_timestamp
    AFTER UPDATE ON project_delays
BEGIN
    UPDATE project_delays SET updated_at = CURRENT_TIMESTAMP
    WHERE delay_id = NEW.delay_id;
END;

-- Calculate days variance when actual_date is set
CREATE TRIGGER IF NOT EXISTS calculate_timeline_variance
    AFTER UPDATE ON project_timeline
    WHEN NEW.actual_date IS NOT NULL AND OLD.actual_date IS NULL
BEGIN
    UPDATE project_timeline
    SET days_variance = CAST((julianday(NEW.actual_date) - julianday(NEW.planned_date)) AS INTEGER)
    WHERE timeline_id = NEW.timeline_id;
END;

-- Calculate days_shift when schedule is updated
CREATE TRIGGER IF NOT EXISTS calculate_schedule_shift
    AFTER INSERT ON schedule_updates
    WHEN NEW.previous_date IS NOT NULL AND NEW.new_date IS NOT NULL
BEGIN
    UPDATE schedule_updates
    SET days_shift = CAST((julianday(NEW.new_date) - julianday(NEW.previous_date)) AS INTEGER)
    WHERE update_id = NEW.update_id;
END;
