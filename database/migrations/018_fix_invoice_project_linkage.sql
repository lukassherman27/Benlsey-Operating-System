-- Migration 018: Fix Invoice-Project Linkage
-- Links invoices to projects table via project_code

-- Add project_code column to invoices table
ALTER TABLE invoices ADD COLUMN project_code TEXT;

-- Populate project_code by joining invoices.project_id with projects.proposal_id
UPDATE invoices
SET project_code = (
    SELECT p.project_code
    FROM projects p
    WHERE p.proposal_id = invoices.project_id
);

-- Create index for project_code lookups
CREATE INDEX IF NOT EXISTS idx_invoices_project_code ON invoices(project_code);

-- Verify the linkage
-- SELECT
--     COUNT(*) as total_invoices,
--     COUNT(project_code) as linked_invoices,
--     COUNT(*) - COUNT(project_code) as orphaned_invoices
-- FROM invoices;

-- Update migration ledger
INSERT INTO schema_migrations (version, name, description, applied_at)
VALUES (18, '018_fix_invoice_project_linkage',
       'Add project_code to invoices table and link to projects via proposal_id',
       datetime('now'));
