-- Migration 020: Add source document tracking to invoices
-- Allows each invoice to reference the finance report PDF it came from

-- Add source_document_id to track which finance report each invoice was imported from
ALTER TABLE invoices ADD COLUMN source_document_id INTEGER;

-- Add index for quick lookups
CREATE INDEX IF NOT EXISTS idx_invoices_source_document ON invoices(source_document_id);

-- Add foreign key constraint (if documents table exists)
-- Note: SQLite doesn't enforce foreign keys by default, but this documents the relationship
-- FOREIGN KEY (source_document_id) REFERENCES documents(document_id)

-- Update migration ledger
INSERT INTO schema_migrations (version, name, description, applied_at)
VALUES (20, '020_add_invoice_source_tracking',
       'Add source_document_id to invoices table for audit trail',
       datetime('now'));
