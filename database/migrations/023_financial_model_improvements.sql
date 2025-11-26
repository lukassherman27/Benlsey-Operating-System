-- Migration 023: Financial Model Improvements
-- Date: 2025-11-20
-- Purpose: Add support for partial invoicing, invoice-to-phase linking, and improved financial calculations

-- ============================================================================
-- STEP 1: Standardize invoice status values
-- ============================================================================

-- Normalize status values to lowercase
UPDATE invoices SET status = 'paid' WHERE LOWER(status) IN ('paid', 'PAID');
UPDATE invoices SET status = 'outstanding' WHERE LOWER(status) = 'outstanding';
UPDATE invoices SET status = 'sent' WHERE LOWER(status) = 'sent';

-- Mark overdue invoices (past due date and not paid)
UPDATE invoices
SET status = 'overdue'
WHERE status != 'paid'
  AND due_date IS NOT NULL
  AND due_date < date('now')
  AND (payment_amount IS NULL OR payment_amount < invoice_amount);

-- ============================================================================
-- STEP 2: Add partial invoicing support to invoices table
-- ============================================================================

-- Add column for what percentage of a phase this invoice represents
ALTER TABLE invoices ADD COLUMN phase_percentage REAL DEFAULT NULL;

-- Add days outstanding calculation helper
ALTER TABLE invoices ADD COLUMN days_outstanding INTEGER;

-- Update days_outstanding for unpaid invoices
UPDATE invoices
SET days_outstanding = CAST((julianday('now') - julianday(invoice_date)) AS INTEGER)
WHERE status IN ('outstanding', 'overdue', 'sent');

-- ============================================================================
-- STEP 3: Add invoice-to-phase linking (many-to-many relationship)
-- ============================================================================

CREATE TABLE IF NOT EXISTS invoice_phase_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,              -- FK to invoices.invoice_id
    breakdown_id TEXT NOT NULL,               -- FK to project_fee_breakdown.breakdown_id
    amount_applied REAL NOT NULL,             -- Amount of this invoice applied to this phase
    percentage_of_phase REAL,                 -- % of phase fee this amount represents
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
    FOREIGN KEY (breakdown_id) REFERENCES project_fee_breakdown(breakdown_id),

    -- Ensure unique invoice-phase combinations
    UNIQUE(invoice_id, breakdown_id)
);

CREATE INDEX IF NOT EXISTS idx_invoice_phase_links_invoice ON invoice_phase_links(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_phase_links_breakdown ON invoice_phase_links(breakdown_id);

-- ============================================================================
-- STEP 4: Enhance project_fee_breakdown table for partial invoicing tracking
-- ============================================================================

-- Add fields to track invoicing progress per phase
ALTER TABLE project_fee_breakdown ADD COLUMN total_invoiced REAL DEFAULT 0;
ALTER TABLE project_fee_breakdown ADD COLUMN percentage_invoiced REAL DEFAULT 0;
ALTER TABLE project_fee_breakdown ADD COLUMN total_paid REAL DEFAULT 0;
ALTER TABLE project_fee_breakdown ADD COLUMN percentage_paid REAL DEFAULT 0;

-- Update total_invoiced from existing invoices (where discipline and phase match)
UPDATE project_fee_breakdown
SET total_invoiced = (
    SELECT COALESCE(SUM(i.invoice_amount), 0)
    FROM invoices i
    WHERE i.project_code = project_fee_breakdown.project_code
      AND i.discipline = project_fee_breakdown.discipline
      AND i.phase = project_fee_breakdown.phase
);

-- Update percentage_invoiced
UPDATE project_fee_breakdown
SET percentage_invoiced =
    CASE
        WHEN phase_fee_usd > 0 THEN (total_invoiced * 100.0 / phase_fee_usd)
        ELSE 0
    END;

-- Update total_paid from existing paid invoices
UPDATE project_fee_breakdown
SET total_paid = (
    SELECT COALESCE(SUM(i.payment_amount), 0)
    FROM invoices i
    WHERE i.project_code = project_fee_breakdown.project_code
      AND i.discipline = project_fee_breakdown.discipline
      AND i.phase = project_fee_breakdown.phase
      AND i.status = 'paid'
);

-- Update percentage_paid
UPDATE project_fee_breakdown
SET percentage_paid =
    CASE
        WHEN phase_fee_usd > 0 THEN (total_paid * 100.0 / phase_fee_usd)
        ELSE 0
    END;

-- ============================================================================
-- STEP 5: Add calculated financial fields to projects table
-- ============================================================================

-- Add cached financial summary fields
ALTER TABLE projects ADD COLUMN total_invoiced_usd REAL DEFAULT 0;
ALTER TABLE projects ADD COLUMN total_remaining_usd REAL DEFAULT 0;

-- Update total_invoiced_usd from invoices
UPDATE projects
SET total_invoiced_usd = (
    SELECT COALESCE(SUM(invoice_amount), 0)
    FROM invoices
    WHERE invoices.project_code = projects.project_code
);

-- Update total_remaining_usd (contract value - invoiced)
UPDATE projects
SET total_remaining_usd = COALESCE(total_fee_usd, 0) - COALESCE(total_invoiced_usd, 0);

-- Update existing paid_to_date_usd from payments
UPDATE projects
SET paid_to_date_usd = (
    SELECT COALESCE(SUM(payment_amount), 0)
    FROM invoices
    WHERE invoices.project_code = projects.project_code
      AND status = 'paid'
);

-- Update outstanding_usd (invoiced but not paid)
UPDATE projects
SET outstanding_usd = COALESCE(total_invoiced_usd, 0) - COALESCE(paid_to_date_usd, 0);

-- ============================================================================
-- STEP 6: Create views for common financial queries
-- ============================================================================

-- View: Project financial summary with all key metrics
CREATE VIEW IF NOT EXISTS v_project_financial_summary AS
SELECT
    p.project_code,
    p.project_name,
    p.client_company,
    p.status,
    p.is_active_project,

    -- Contract
    p.total_fee_usd AS contract_value,
    p.contract_date,
    p.contract_duration_months,

    -- Invoicing
    p.total_invoiced_usd,
    p.paid_to_date_usd,
    p.outstanding_usd,
    p.total_remaining_usd,

    -- Calculated percentages
    CASE WHEN p.total_fee_usd > 0
         THEN (p.total_invoiced_usd * 100.0 / p.total_fee_usd)
         ELSE 0
    END AS percent_invoiced,

    CASE WHEN p.total_fee_usd > 0
         THEN (p.paid_to_date_usd * 100.0 / p.total_fee_usd)
         ELSE 0
    END AS percent_paid,

    -- Invoice counts
    (SELECT COUNT(*) FROM invoices WHERE project_code = p.project_code) AS invoice_count,
    (SELECT COUNT(*) FROM invoices WHERE project_code = p.project_code AND status = 'paid') AS paid_invoice_count,
    (SELECT COUNT(*) FROM invoices WHERE project_code = p.project_code AND status = 'overdue') AS overdue_invoice_count,

    -- Outstanding breakdown
    (SELECT COALESCE(SUM(invoice_amount - COALESCE(payment_amount, 0)), 0)
     FROM invoices
     WHERE project_code = p.project_code AND status = 'outstanding') AS outstanding_not_due,

    (SELECT COALESCE(SUM(invoice_amount - COALESCE(payment_amount, 0)), 0)
     FROM invoices
     WHERE project_code = p.project_code AND status = 'overdue') AS overdue_amount,

    p.updated_at

FROM projects p
WHERE p.is_active_project = 1;

-- View: Invoice aging report
CREATE VIEW IF NOT EXISTS v_invoice_aging AS
SELECT
    i.invoice_id,
    i.project_code,
    i.invoice_number,
    i.invoice_date,
    i.due_date,
    i.invoice_amount,
    i.payment_amount,
    i.invoice_amount - COALESCE(i.payment_amount, 0) AS amount_outstanding,
    i.status,
    i.discipline,
    i.phase,
    i.days_outstanding,

    -- Days overdue (if past due date)
    CASE
        WHEN i.due_date IS NOT NULL AND i.due_date < date('now') AND i.status != 'paid'
        THEN CAST((julianday('now') - julianday(i.due_date)) AS INTEGER)
        ELSE 0
    END AS days_overdue,

    -- Aging category
    CASE
        WHEN i.status = 'paid' THEN 'Paid'
        WHEN i.due_date >= date('now') THEN 'Current'
        WHEN julianday('now') - julianday(i.due_date) <= 30 THEN '1-30 days'
        WHEN julianday('now') - julianday(i.due_date) <= 60 THEN '31-60 days'
        WHEN julianday('now') - julianday(i.due_date) <= 90 THEN '61-90 days'
        ELSE '90+ days'
    END AS aging_bucket,

    p.project_name,
    p.client_company

FROM invoices i
LEFT JOIN projects p ON i.project_code = p.project_code
WHERE i.status != 'paid'
ORDER BY i.days_outstanding DESC;

-- ============================================================================
-- STEP 7: Create triggers to maintain calculated fields
-- ============================================================================

-- Trigger: Update project financials when invoice is inserted/updated
CREATE TRIGGER IF NOT EXISTS update_project_financials_on_invoice_change
AFTER INSERT ON invoices
FOR EACH ROW
BEGIN
    UPDATE projects
    SET
        total_invoiced_usd = (
            SELECT COALESCE(SUM(invoice_amount), 0)
            FROM invoices
            WHERE project_code = NEW.project_code
        ),
        paid_to_date_usd = (
            SELECT COALESCE(SUM(payment_amount), 0)
            FROM invoices
            WHERE project_code = NEW.project_code AND status = 'paid'
        ),
        updated_at = datetime('now')
    WHERE project_code = NEW.project_code;

    UPDATE projects
    SET
        outstanding_usd = total_invoiced_usd - paid_to_date_usd,
        total_remaining_usd = COALESCE(total_fee_usd, 0) - total_invoiced_usd
    WHERE project_code = NEW.project_code;
END;

-- Trigger: Update project financials when invoice is updated
CREATE TRIGGER IF NOT EXISTS update_project_financials_on_invoice_update
AFTER UPDATE ON invoices
FOR EACH ROW
BEGIN
    UPDATE projects
    SET
        total_invoiced_usd = (
            SELECT COALESCE(SUM(invoice_amount), 0)
            FROM invoices
            WHERE project_code = NEW.project_code
        ),
        paid_to_date_usd = (
            SELECT COALESCE(SUM(payment_amount), 0)
            FROM invoices
            WHERE project_code = NEW.project_code AND status = 'paid'
        ),
        updated_at = datetime('now')
    WHERE project_code = NEW.project_code;

    UPDATE projects
    SET
        outstanding_usd = total_invoiced_usd - paid_to_date_usd,
        total_remaining_usd = COALESCE(total_fee_usd, 0) - total_invoiced_usd
    WHERE project_code = NEW.project_code;
END;

-- ============================================================================
-- Migration tracking
-- ============================================================================

INSERT INTO schema_migrations (version, name, description, applied_at)
VALUES (23, '023_financial_model_improvements', 'Add partial invoicing, invoice-phase linking, and improved financial calculations', datetime('now'));
