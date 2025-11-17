-- Migration 017: Payment Milestones Table
-- Creates normalized payment tracking and improves ID management

-- Create payment_milestones table for normalized payment schedule tracking
CREATE TABLE IF NOT EXISTS payment_milestones (
    milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id TEXT NOT NULL,
    project_code TEXT NOT NULL,
    phase TEXT NOT NULL,  -- mobilization, concept, dd, cd, ca
    amount_usd REAL NOT NULL CHECK(amount_usd > 0),
    percentage REAL,  -- Percentage of total contract fee
    due_date TEXT,  -- Calculated based on contract terms or manual entry
    payment_status TEXT DEFAULT 'pending',  -- pending, invoiced, paid, overdue, cancelled
    invoice_id TEXT,  -- Link to invoice when created
    paid_date TEXT,
    paid_amount_usd REAL,  -- Actual amount paid (may differ from invoiced)
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);

-- Add fee_rollup_behavior field to projects table
ALTER TABLE projects ADD COLUMN fee_rollup_behavior TEXT DEFAULT 'separate';
  -- Values: 'separate' (fees don't roll up to parent) or 'rollup' (fees included in parent total)

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_milestones_contract ON payment_milestones(contract_id);
CREATE INDEX IF NOT EXISTS idx_milestones_project ON payment_milestones(project_code);
CREATE INDEX IF NOT EXISTS idx_milestones_status ON payment_milestones(payment_status);
CREATE INDEX IF NOT EXISTS idx_milestones_due_date ON payment_milestones(due_date);
CREATE INDEX IF NOT EXISTS idx_projects_rollup ON projects(fee_rollup_behavior);

-- Update migration ledger
INSERT INTO schema_migrations (version, name, description, applied_at)
VALUES (17, '017_payment_milestones',
       'Create payment_milestones table for normalized payment tracking and add fee_rollup_behavior to projects',
       datetime('now'));
