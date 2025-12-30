-- Migration 103: Delete Unused Tables
-- Date: 2025-12-30
-- Issue: #61
--
-- AUDIT EVIDENCE:
-- These tables have:
--   1. Zero (0) records
--   2. No code references in backend/, frontend/, or scripts/
--   3. Only referenced in migration files or documentation
--
-- Tables deleted:
--   - calendar_blocks: Never implemented, 0 records
--   - project_pm_history: Never implemented, 0 records
--   - project_financials: Never implemented, 0 records
--
-- Tables NOT deleted (have active code waiting for features):
--   - commitments: Used by backend/api/routers/my_day.py
--   - contract_terms: Used by backend/services/contract_service.py
--   - learned_user_patterns: Used by backend/services/user_learning_service.py
--   - project_status_tracking: Used by backend/core/project_reports.py
--   - project_outreach: Used by backend/services/outreach_service.py
--   - project_files: Used by backend/services/file_service.py
--   - project_documents: Used by backend/services/proposal_query_service.py
--   - project_context: Used by backend/services/context_service.py
--   - project_contacts: Used by backend/api/routers/projects.py
--   - project_contact_links: Used by multiple services
--   - project_colors: Used by backend/services/schedule_pdf_generator.py

-- Verify tables are empty before dropping (safety check)
-- SELECT 'calendar_blocks' as tbl, COUNT(*) FROM calendar_blocks;
-- SELECT 'project_pm_history' as tbl, COUNT(*) FROM project_pm_history;
-- SELECT 'project_financials' as tbl, COUNT(*) FROM project_financials;

-- Drop unused tables
DROP TABLE IF EXISTS calendar_blocks;
DROP TABLE IF EXISTS project_pm_history;
DROP TABLE IF EXISTS project_financials;
