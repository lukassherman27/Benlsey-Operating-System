-- Migration 062: Consolidate Contact Tables (Final)
-- Date: 2025-12-02
-- Purpose: Archive remaining redundant contact tables, merge useful data
-- Note: contact_metadata, project_contacts, ai_suggestions_queue were already archived by 061

-- ============================================================================
-- STEP 1: Merge data from contacts_only into contacts (if not already there)
-- ============================================================================

-- contacts_only has 205 rows, many may overlap with contacts (486 rows)
-- Only insert contacts that don't already exist in contacts table
INSERT OR IGNORE INTO contacts (email, name, notes, source)
SELECT
    email,
    name,
    notes,
    'contacts_only_migration'
FROM contacts_only
WHERE email NOT IN (SELECT email FROM contacts);

-- ============================================================================
-- STEP 2: Archive contacts_only
-- ============================================================================

ALTER TABLE contacts_only RENAME TO contacts_only_archive;

-- ============================================================================
-- Summary of contact tables after this migration:
-- ACTIVE:
--   - contacts (primary contact table, ~486+ rows)
--   - contact_context (context/classification for contacts, 36 rows)
--   - contact_context_history (history tracking, 17 rows)
--   - email_extracted_contacts (tracks which emails had contacts extracted, 100 rows)
--
-- ARCHIVED:
--   - contact_metadata_archive (merged into contacts)
--   - project_contacts_archive (superseded by contact_context)
--   - contacts_only_archive (merged into contacts)
-- ============================================================================
