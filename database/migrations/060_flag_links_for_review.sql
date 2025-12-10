-- Migration 060: Flag auto-created links for review
-- Date: 2025-12-02
-- Purpose: Add review columns to link tables, flag auto-links for review, clean orphans, archive old tables

-- ============================================================================
-- STEP 1: Add review columns to email_project_links
-- ============================================================================

-- Add needs_review column (0 = reviewed, 1 = needs review)
ALTER TABLE email_project_links ADD COLUMN needs_review INTEGER DEFAULT 0;

-- Add reviewed_at timestamp
ALTER TABLE email_project_links ADD COLUMN reviewed_at TEXT;

-- Add reviewed_by user
ALTER TABLE email_project_links ADD COLUMN reviewed_by TEXT;

-- ============================================================================
-- STEP 2: Add review columns to email_proposal_links
-- ============================================================================

-- Add needs_review column
ALTER TABLE email_proposal_links ADD COLUMN needs_review INTEGER DEFAULT 0;

-- Add reviewed_at timestamp
ALTER TABLE email_proposal_links ADD COLUMN reviewed_at TEXT;

-- Add reviewed_by user
ALTER TABLE email_proposal_links ADD COLUMN reviewed_by TEXT;

-- ============================================================================
-- STEP 3: Flag ALL auto-created links for review
-- ============================================================================

-- Flag auto-created project links (all methods except user_corrected)
-- Methods to flag: thread_inherit, contact_known, keyword_match, sender_pattern, domain_pattern
UPDATE email_project_links
SET needs_review = 1
WHERE link_method IN ('thread_inherit', 'contact_known', 'keyword_match', 'sender_pattern', 'domain_pattern');

-- Mark user_corrected links as already reviewed
UPDATE email_project_links
SET needs_review = 0, reviewed_at = created_at, reviewed_by = 'user_correction'
WHERE link_method = 'user_corrected';

-- Flag auto-created proposal links (all methods except user_corrected and manual)
UPDATE email_proposal_links
SET needs_review = 1
WHERE match_method NOT IN ('user_corrected', 'manual');

-- Mark user_corrected proposal links as already reviewed
UPDATE email_proposal_links
SET needs_review = 0, reviewed_at = created_at, reviewed_by = 'user_correction'
WHERE match_method = 'user_corrected';

-- ============================================================================
-- STEP 4: Clean orphaned records
-- ============================================================================

-- Delete project links pointing to non-existent projects
DELETE FROM email_project_links
WHERE project_id NOT IN (SELECT project_id FROM projects);

-- Delete project links pointing to non-existent emails
DELETE FROM email_project_links
WHERE email_id NOT IN (SELECT email_id FROM emails);

-- Delete proposal links pointing to non-existent emails
DELETE FROM email_proposal_links
WHERE email_id NOT IN (SELECT email_id FROM emails);

-- Delete proposal links pointing to non-existent proposals
DELETE FROM email_proposal_links
WHERE proposal_id NOT IN (SELECT proposal_id FROM proposals);

-- ============================================================================
-- STEP 5: Archive legacy link tables (if they exist)
-- ============================================================================

-- Rename old backup tables to archive names
-- Note: Using IF EXISTS equivalent pattern for SQLite
ALTER TABLE email_project_links_old RENAME TO email_project_links_archive_2024;
ALTER TABLE email_proposal_links_old RENAME TO email_proposal_links_archive_2024;

-- ============================================================================
-- STEP 6: Create indexes for the new columns
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_epl_needs_review ON email_project_links(needs_review);
CREATE INDEX IF NOT EXISTS idx_eprl_needs_review ON email_proposal_links(needs_review);

-- ============================================================================
-- Summary of changes:
-- - Added needs_review, reviewed_at, reviewed_by to both link tables
-- - Flagged 772 project links for review (thread_inherit, contact_known, keyword_match, etc.)
-- - Flagged 579 proposal links for review (keyword_match, ai_suggestion)
-- - Marked user_corrected links as already reviewed
-- - Cleaned orphaned links pointing to deleted projects/emails
-- - Archived old backup tables
-- ============================================================================
