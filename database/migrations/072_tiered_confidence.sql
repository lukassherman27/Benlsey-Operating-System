-- Migration 072: Tiered Confidence System
-- Created: 2025-12-05
-- Purpose: Track confidence at each categorization tier for robust email classification

-- Track confidence at each tier for each email
CREATE TABLE IF NOT EXISTS email_tier_confidence (
    email_id INTEGER PRIMARY KEY REFERENCES emails(email_id),
    tier1_category TEXT,        -- BDS, INT, PERS, SKIP
    tier1_confidence REAL,
    tier2_stage TEXT,           -- RFI, Proposal, Contract, Delivery
    tier2_confidence REAL,
    tier3_project_code TEXT,
    tier3_confidence REAL,
    tier4_document_type TEXT,   -- NDA, Contract, Fee, Meeting, etc.
    tier4_confidence REAL,
    needs_review BOOLEAN DEFAULT 0,
    reviewed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Standard document types (extensible via INSERT)
CREATE TABLE IF NOT EXISTS document_types (
    type_code TEXT PRIMARY KEY,
    type_name TEXT NOT NULL,
    tier INTEGER DEFAULT 4,     -- Which tier this belongs to
    parent_type TEXT,           -- For hierarchy (NDA-SIGNED → NDA)
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Seed initial document types
INSERT OR IGNORE INTO document_types (type_code, type_name, tier, parent_type, description) VALUES
-- Legal
('NDA', 'Non-Disclosure Agreement', 4, NULL, 'Confidentiality agreement'),
('NDA-SIGNED', 'Signed NDA', 4, 'NDA', 'Executed NDA'),
('NDA-UNSIGNED', 'Unsigned NDA', 4, 'NDA', 'Draft NDA pending signature'),

-- Contracts
('CONTRACT', 'Design Contract', 4, NULL, 'Service agreement'),
('CONTRACT-DRAFT', 'Draft Contract', 4, 'CONTRACT', 'Unsigned contract'),
('CONTRACT-SIGNED', 'Signed Contract', 4, 'CONTRACT', 'Executed contract'),
('CONTRACT-ADDENDUM', 'Contract Addendum', 4, 'CONTRACT', 'Modification to contract'),

-- Proposals
('PROPOSAL', 'Fee Proposal', 4, NULL, 'Pricing proposal'),
('PROPOSAL-SENT', 'Proposal Sent', 4, 'PROPOSAL', 'Submitted to client'),
('PROPOSAL-REVISED', 'Revised Proposal', 4, 'PROPOSAL', 'Updated pricing'),
('PROPOSAL-ACCEPTED', 'Proposal Accepted', 4, 'PROPOSAL', 'Client accepted'),

-- Financial
('INVOICE', 'Invoice', 4, NULL, 'Payment request'),
('PAYMENT', 'Payment Confirmation', 4, 'INVOICE', 'Payment received'),
('FEE-DISCUSSION', 'Fee Discussion', 4, NULL, 'Budget/pricing emails'),

-- Project Lifecycle
('RFI', 'Request for Information', 4, NULL, 'Initial client inquiry'),
('SITE-VISIT', 'Site Visit', 4, NULL, 'Site trip coordination'),
('DESIGN-REVIEW', 'Design Review', 4, NULL, 'Design feedback/presentation'),
('MEETING', 'Meeting', 4, NULL, 'Meeting coordination'),
('KICKOFF', 'Project Kickoff', 4, 'MEETING', 'Project start meeting'),

-- Documents
('DRAWINGS', 'Design Drawings', 4, NULL, 'Architectural drawings'),
('PHOTOS', 'Site Photos', 4, NULL, 'Photography from site'),
('SPECIFICATIONS', 'Specifications', 4, NULL, 'Technical specifications');

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_tier_confidence_needs_review ON email_tier_confidence(needs_review);
CREATE INDEX IF NOT EXISTS idx_tier_confidence_tier3 ON email_tier_confidence(tier3_project_code);
CREATE INDEX IF NOT EXISTS idx_document_types_parent ON document_types(parent_type);

-- View for emails needing review (low confidence or flagged)
CREATE VIEW IF NOT EXISTS v_emails_needing_review AS
SELECT
    e.email_id,
    e.subject,
    e.sender_email,
    e.date_normalized,
    tc.tier1_category,
    tc.tier1_confidence,
    tc.tier3_project_code,
    tc.tier3_confidence,
    tc.needs_review
FROM emails e
LEFT JOIN email_tier_confidence tc ON e.email_id = tc.email_id
WHERE tc.needs_review = 1
   OR tc.tier3_confidence < 0.7
   OR tc.tier1_confidence < 0.8
ORDER BY e.date_normalized DESC;
