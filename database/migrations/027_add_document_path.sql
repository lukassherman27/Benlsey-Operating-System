-- Add document_path column to proposals table
-- This links the original proposal .docx file to the database record

ALTER TABLE proposals ADD COLUMN document_path TEXT;

-- Add index for quick lookups
CREATE INDEX IF NOT EXISTS idx_proposals_document_path ON proposals(document_path);

-- Also add columns for richer proposal data from documents
ALTER TABLE proposals ADD COLUMN location TEXT;
ALTER TABLE proposals ADD COLUMN currency TEXT DEFAULT 'USD';
ALTER TABLE proposals ADD COLUMN proposal_sent_date TEXT;
ALTER TABLE proposals ADD COLUMN payment_terms TEXT;
ALTER TABLE proposals ADD COLUMN scope_summary TEXT;

-- Create index on location for geographic queries
CREATE INDEX IF NOT EXISTS idx_proposals_location ON proposals(location);
