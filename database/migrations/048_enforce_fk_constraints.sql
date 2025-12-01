-- Migration 048: Enforce Foreign Key Constraints
-- Created: 2025-12-01
-- Author: Backend Worker
-- Status: PENDING - DO NOT RUN until Data Worker completes link rebuild
--
-- PURPOSE:
-- 1. Enable FK enforcement for all new connections
-- 2. Clean up orphaned links that violate FK constraints
-- 3. Recreate link tables with proper FK enforcement
--
-- PREREQUISITE:
-- - Data Worker must first rebuild all link tables with valid FKs
-- - Run: SELECT COUNT(*) FROM email_proposal_links WHERE proposal_id NOT IN (SELECT proposal_id FROM proposals);
-- - Result should be 0 before running this migration
--
-- CURRENT STATE (from Phase B audit):
-- - email_proposal_links: 4,872 links, 100% orphaned (proposal_ids 1-87, but proposals are 177-263)
-- - email_project_links: 918 links, 98.9% orphaned
-- - PRAGMA foreign_keys = 0 (enforcement disabled)

-- ============================================================================
-- SECTION 1: VALIDATION QUERIES (Run these first to check data state)
-- ============================================================================

-- Check orphaned email_proposal_links
-- Expected: 0 after Data Worker rebuild
-- SELECT COUNT(*) as orphaned_proposal_links
-- FROM email_proposal_links
-- WHERE proposal_id NOT IN (SELECT proposal_id FROM proposals);

-- Check orphaned email_project_links
-- Expected: 0 after Data Worker rebuild
-- SELECT COUNT(*) as orphaned_project_links
-- FROM email_project_links
-- WHERE project_id NOT IN (SELECT project_id FROM projects);

-- Check orphaned document_proposal_links
-- SELECT COUNT(*) as orphaned_doc_links
-- FROM document_proposal_links
-- WHERE proposal_id NOT IN (SELECT proposal_id FROM proposals);

-- Check orphaned project_contact_links
-- SELECT COUNT(*) as orphaned_contact_links
-- FROM project_contact_links
-- WHERE (proposal_id IS NOT NULL AND proposal_id NOT IN (SELECT proposal_id FROM proposals))
--    OR (project_id IS NOT NULL AND project_id NOT IN (SELECT project_id FROM projects))
--    OR (contact_id NOT IN (SELECT contact_id FROM contacts));

-- ============================================================================
-- SECTION 2: CLEANUP ORPHANED DATA (Only run if validation shows orphans)
-- ============================================================================

-- Delete orphaned email_proposal_links
-- DELETE FROM email_proposal_links
-- WHERE proposal_id NOT IN (SELECT proposal_id FROM proposals);

-- Delete orphaned email_project_links (by project_id)
-- DELETE FROM email_project_links
-- WHERE project_id NOT IN (SELECT project_id FROM projects);

-- Delete orphaned email_project_links (by email_id)
-- DELETE FROM email_project_links
-- WHERE email_id NOT IN (SELECT email_id FROM emails);

-- Delete orphaned document_proposal_links
-- DELETE FROM document_proposal_links
-- WHERE proposal_id NOT IN (SELECT proposal_id FROM proposals)
--    OR document_id NOT IN (SELECT document_id FROM documents);

-- Delete orphaned project_contact_links
-- DELETE FROM project_contact_links
-- WHERE (proposal_id IS NOT NULL AND proposal_id NOT IN (SELECT proposal_id FROM proposals))
--    OR (project_id IS NOT NULL AND project_id NOT IN (SELECT project_id FROM projects))
--    OR (contact_id NOT IN (SELECT contact_id FROM contacts));

-- ============================================================================
-- SECTION 3: ENABLE FK ENFORCEMENT
-- ============================================================================

-- This must be set on EVERY connection to SQLite
-- Add this to all Python database connections:
--   connection.execute("PRAGMA foreign_keys = ON")

-- For reference, the existing FK constraints defined in tables:
--
-- email_proposal_links:
--   FOREIGN KEY (email_id) REFERENCES emails(email_id)
--   FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
--
-- email_project_links:
--   FOREIGN KEY (email_id) REFERENCES emails(email_id)
--   FOREIGN KEY (project_id) REFERENCES projects(project_id)
--
-- document_proposal_links:
--   FOREIGN KEY (document_id) REFERENCES documents(document_id)
--   FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
--
-- project_contact_links:
--   FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
--   FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
--   FOREIGN KEY (project_id) REFERENCES projects(project_id)
--
-- email_client_links:
--   FOREIGN KEY (email_id) REFERENCES emails(email_id)
--   FOREIGN KEY (client_id) REFERENCES clients(client_id)

-- ============================================================================
-- SECTION 4: PYTHON CODE CHANGES REQUIRED
-- ============================================================================

-- Update backend/api/dependencies.py to add FK enforcement:
--
-- def get_db():
--     db_path = os.getenv("DATABASE_PATH", "database/bensley_master.db")
--     conn = sqlite3.connect(db_path)
--     conn.row_factory = sqlite3.Row
--     conn.execute("PRAGMA foreign_keys = ON")  -- ADD THIS LINE
--     return conn

-- Update all services that create their own connections to add:
--     conn.execute("PRAGMA foreign_keys = ON")

-- Files that need updating:
-- - backend/api/dependencies.py
-- - backend/services/base_service.py (if it has connection logic)
-- - scripts/core/email_project_linker.py
-- - scripts/core/transcript_linker.py
-- - Any service that calls sqlite3.connect() directly

-- ============================================================================
-- SECTION 5: FK ENFORCEMENT TEST
-- ============================================================================

-- After enabling PRAGMA foreign_keys = ON, test with:
-- INSERT INTO email_proposal_links (email_id, proposal_id, confidence_score)
-- VALUES (1, 999999, 0.5);
--
-- Should fail with: FOREIGN KEY constraint failed

-- ============================================================================
-- ROLLBACK PLAN
-- ============================================================================

-- If FK enforcement causes issues:
-- 1. Remove PRAGMA foreign_keys = ON from Python code
-- 2. FK constraints will be ignored again
-- 3. Investigate which data is violating constraints
