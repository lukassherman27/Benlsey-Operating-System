-- Migration 021: Add phase and discipline columns to invoices table
-- These columns track which contract phase and discipline each invoice belongs to

-- Add phase column (mobilization, concept, dd, cd, ca, etc.)
ALTER TABLE invoices ADD COLUMN phase TEXT;

-- Add discipline column (Landscape, Architectural, Interior)
ALTER TABLE invoices ADD COLUMN discipline TEXT;

-- Add created_at timestamp if not exists
ALTER TABLE invoices ADD COLUMN created_at DATETIME DEFAULT (datetime('now'));

-- Record migration
INSERT INTO schema_migrations (version, name, description, applied_at)
VALUES (21, '021_add_invoice_phase_discipline',
       'Add phase, discipline, and created_at columns to invoices table',
       datetime('now'));
