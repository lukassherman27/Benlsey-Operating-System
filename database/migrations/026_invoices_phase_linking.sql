-- Migration: Link invoices to specific phase/discipline breakdowns
-- This allows one invoice number to have multiple entries for different phases/disciplines
-- Example: I25-115 can have entries for Landscape Mobilization, Architecture Mobilization, etc.

-- Add breakdown_id column to invoices table
ALTER TABLE invoices ADD COLUMN breakdown_id TEXT;

-- Create foreign key relationship (SQLite doesn't enforce this retroactively, but good for documentation)
-- FOREIGN KEY (breakdown_id) REFERENCES project_fee_breakdown(breakdown_id)

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_invoices_breakdown ON invoices(breakdown_id);

-- Create index for finding all entries of same invoice number
CREATE INDEX IF NOT EXISTS idx_invoices_number_breakdown ON invoices(invoice_number, breakdown_id);

-- Update existing invoices to set breakdown_id = NULL (they're not linked to specific phases)
-- Future invoices should have breakdown_id populated

-- Note: invoice_number is already non-unique, so multiple entries per invoice number are allowed
