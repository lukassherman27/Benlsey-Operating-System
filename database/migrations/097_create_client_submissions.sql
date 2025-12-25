-- Migration 097: Create client_submissions table for tracking deliveries to clients
-- Created: 2025-12-26
-- Issue: #107 - Project management redesign
--
-- This table tracks what we send to clients and their feedback.
-- Links to phases, invoices, and emails for full traceability.

CREATE TABLE IF NOT EXISTS client_submissions (
    submission_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Project linkage
    project_id INTEGER REFERENCES projects(project_id),
    project_code TEXT NOT NULL,

    -- Phase linkage
    phase_id INTEGER REFERENCES contract_phases(phase_id),
    discipline TEXT CHECK(discipline IN ('Architecture', 'Interior', 'Landscape', 'Artwork', 'Branding')),
    phase_name TEXT,  -- 'Concept', 'Schematic', 'DD', 'CD', etc.

    -- Submission details
    submission_type TEXT NOT NULL CHECK(submission_type IN (
        'drawing_set',
        'presentation',
        'report',
        'specifications',
        'model',
        'renderings',
        'samples',
        'other'
    )),
    title TEXT NOT NULL,
    description TEXT,
    revision_number INTEGER DEFAULT 1,

    -- When and how
    submitted_date DATE NOT NULL,
    submitted_by INTEGER REFERENCES staff(staff_id),
    delivery_method TEXT CHECK(delivery_method IN ('email', 'portal', 'wetransfer', 'dropbox', 'physical', 'other')),

    -- Files (JSON array)
    -- [{filename: "DD-Set-Rev3.pdf", path: "/path/to/file", size_mb: 45.2}]
    files TEXT,

    -- Client response
    status TEXT DEFAULT 'sent' CHECK(status IN (
        'sent',           -- Just sent, waiting
        'received',       -- Client acknowledged receipt
        'under_review',   -- Client is reviewing
        'approved',       -- Client approved
        'revision_requested',  -- Client wants changes
        'superseded'      -- Replaced by newer revision
    )),
    client_feedback TEXT,
    feedback_date DATE,
    feedback_received_by INTEGER REFERENCES staff(staff_id),

    -- Linkages
    linked_invoice_id INTEGER REFERENCES invoices(invoice_id),
    source_email_id INTEGER REFERENCES emails(email_id),
    supersedes_submission_id INTEGER REFERENCES client_submissions(submission_id),

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_submissions_project ON client_submissions(project_code);
CREATE INDEX IF NOT EXISTS idx_submissions_phase ON client_submissions(phase_id);
CREATE INDEX IF NOT EXISTS idx_submissions_date ON client_submissions(submitted_date);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON client_submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_discipline ON client_submissions(discipline);

-- Trigger to update updated_at
CREATE TRIGGER IF NOT EXISTS trg_submissions_updated
AFTER UPDATE ON client_submissions
FOR EACH ROW
BEGIN
    UPDATE client_submissions SET updated_at = CURRENT_TIMESTAMP WHERE submission_id = NEW.submission_id;
END;
