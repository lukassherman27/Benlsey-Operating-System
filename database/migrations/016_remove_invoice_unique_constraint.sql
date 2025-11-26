-- Migration 016: Remove UNIQUE constraint from invoice_number
-- Purpose: Allow same invoice to span multiple projects/phases/disciplines

-- Step 1: Create new invoices table without UNIQUE constraint
CREATE TABLE invoices_new (
  invoice_id              INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id              INTEGER,
  invoice_number          TEXT,  -- UNIQUE constraint removed
  description             TEXT,
  invoice_date            DATE,
  due_date                DATE,
  invoice_amount          REAL,
  payment_amount          REAL,
  payment_date            DATE,
  status                  TEXT,
  notes                   TEXT,
  source_ref              TEXT,
  source_type             TEXT CHECK(source_type IN ('manual', 'import', 'ai', 'email_parser')),
  source_reference        TEXT,
  locked_fields           TEXT,
  locked_by               TEXT,
  locked_at               DATETIME,
  created_by              TEXT DEFAULT 'system',
  updated_by              TEXT,
  FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- Step 2: Copy all existing data
INSERT INTO invoices_new SELECT * FROM invoices;

-- Step 3: Drop old table
DROP TABLE invoices;

-- Step 4: Rename new table
ALTER TABLE invoices_new RENAME TO invoices;

-- Step 5: Recreate indexes
CREATE INDEX idx_invoices_project ON invoices(project_id);
CREATE INDEX idx_invoices_number ON invoices(invoice_number);
CREATE INDEX idx_invoices_status ON invoices(status);
