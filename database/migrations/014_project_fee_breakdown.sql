-- Migration 014: Project Fee Breakdown & Payment Tracking
-- Created: 2025-11-23
-- Description: Track project phases, fee allocation per phase, and payment status
--              Enables detailed financial tracking and cash flow forecasting

-- ============================================================================
-- Project Phases
-- Tracks design phases (Concept, SD, DD, CD, CA) and their fee allocation
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_phases (
    phase_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id              INTEGER NOT NULL,
    phase_name              TEXT NOT NULL,                      -- 'Concept Design', 'Schematic Design', 'Design Development', 'Construction Documents', 'Contract Administration'
    phase_code              TEXT,                               -- 'CD', 'SD', 'DD', 'CD', 'CA'
    sequence_order          INTEGER,                            -- 1, 2, 3, 4, 5 for sorting
    allocated_fee_usd       REAL,                               -- Fee allocated to this phase
    allocated_percentage    REAL,                               -- Percentage of total project fee
    expected_hours          REAL,                               -- Planned hours for this phase
    actual_hours            REAL DEFAULT 0,                     -- Tracked hours (if time tracking exists)
    status                  TEXT DEFAULT 'not_started',         -- 'not_started', 'in_progress', 'completed', 'on_hold', 'cancelled'
    start_date              DATE,                               -- When phase actually started
    target_completion_date  DATE,                               -- Planned completion
    actual_completion_date  DATE,                               -- Actual completion
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    UNIQUE(project_id, phase_name)
);

-- ============================================================================
-- Payment Milestones
-- Tracks payment schedule and actual payments received
-- ============================================================================
CREATE TABLE IF NOT EXISTS payment_milestones (
    milestone_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id              INTEGER NOT NULL,
    phase_id                INTEGER,                            -- Link to phase if payment is phase-based
    milestone_name          TEXT NOT NULL,                      -- 'Initial Payment', 'CD Completion', 'DD Approval', 'Monthly Retainer - Jan 2025'
    milestone_type          TEXT,                               -- 'upfront', 'phase_completion', 'monthly_retainer', 'deliverable_based', 'progress_based'
    sequence_order          INTEGER,                            -- Order of payment
    expected_amount_usd     REAL NOT NULL,                      -- Amount expected
    expected_percentage     REAL,                               -- Percentage of total fee
    expected_date           DATE,                               -- When payment is expected
    invoice_id              INTEGER,                            -- Link to invoice if created
    actual_amount_usd       REAL,                               -- Actual amount received
    actual_date             DATE,                               -- When payment was received
    payment_status          TEXT DEFAULT 'pending',             -- 'pending', 'invoiced', 'partially_paid', 'paid', 'overdue', 'waived'
    days_overdue            INTEGER,                            -- Calculated field for overdue payments
    trigger_condition       TEXT,                               -- What triggers this payment: 'Contract Signing', 'Phase Approval', 'Monthly', 'Deliverable Submission'
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (phase_id) REFERENCES project_phases(phase_id) ON DELETE SET NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id) ON DELETE SET NULL
);

-- ============================================================================
-- Fee Adjustments
-- Tracks changes to project fee (change orders, scope changes, amendments)
-- ============================================================================
CREATE TABLE IF NOT EXISTS fee_adjustments (
    adjustment_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id              INTEGER NOT NULL,
    adjustment_type         TEXT NOT NULL,                      -- 'change_order', 'scope_addition', 'scope_reduction', 'contract_amendment', 'discount', 'bonus'
    description             TEXT NOT NULL,
    adjustment_amount_usd   REAL NOT NULL,                      -- Positive for increase, negative for decrease
    adjustment_percentage   REAL,                               -- Percentage change to original fee
    effective_date          DATE,                               -- When this adjustment takes effect
    approval_status         TEXT DEFAULT 'pending',             -- 'pending', 'approved', 'rejected', 'implemented'
    approved_by             TEXT,                               -- Who approved this adjustment
    approval_date           DATE,
    source_document         TEXT,                               -- Reference to change order document
    impact_on_timeline_days INTEGER,                            -- Timeline impact if any
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_project_phases_project
    ON project_phases(project_id);

CREATE INDEX IF NOT EXISTS idx_project_phases_status
    ON project_phases(status, project_id);

CREATE INDEX IF NOT EXISTS idx_payment_milestones_project
    ON payment_milestones(project_id);

CREATE INDEX IF NOT EXISTS idx_payment_milestones_status
    ON payment_milestones(payment_status, expected_date);

CREATE INDEX IF NOT EXISTS idx_payment_milestones_phase
    ON payment_milestones(phase_id);

CREATE INDEX IF NOT EXISTS idx_fee_adjustments_project
    ON fee_adjustments(project_id);

CREATE INDEX IF NOT EXISTS idx_fee_adjustments_status
    ON fee_adjustments(approval_status);

-- ============================================================================
-- Triggers for auto-updating timestamps
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_project_phases_timestamp
    AFTER UPDATE ON project_phases
BEGIN
    UPDATE project_phases SET updated_at = CURRENT_TIMESTAMP
    WHERE phase_id = NEW.phase_id;
END;

CREATE TRIGGER IF NOT EXISTS update_payment_milestones_timestamp
    AFTER UPDATE ON payment_milestones
BEGIN
    UPDATE payment_milestones SET updated_at = CURRENT_TIMESTAMP
    WHERE milestone_id = NEW.milestone_id;
END;

CREATE TRIGGER IF NOT EXISTS update_fee_adjustments_timestamp
    AFTER UPDATE ON fee_adjustments
BEGIN
    UPDATE fee_adjustments SET updated_at = CURRENT_TIMESTAMP
    WHERE adjustment_id = NEW.adjustment_id;
END;

-- ============================================================================
-- Trigger to calculate days_overdue automatically
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS calculate_days_overdue
    AFTER UPDATE ON payment_milestones
    WHEN NEW.payment_status IN ('invoiced', 'overdue') AND NEW.actual_date IS NULL
BEGIN
    UPDATE payment_milestones
    SET days_overdue = CAST((julianday('now') - julianday(NEW.expected_date)) AS INTEGER)
    WHERE milestone_id = NEW.milestone_id AND days_overdue IS NULL;
END;
