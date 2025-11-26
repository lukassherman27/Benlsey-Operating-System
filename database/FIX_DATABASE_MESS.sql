-- ============================================================================
-- DATABASE CLEANUP SCRIPT - Fix the Proposal/Project Mess
-- Date: 2025-11-24
-- Purpose: Clean up duplicate and conflicting data between proposals/projects
-- ============================================================================

-- BACKUP FIRST!
-- Run: sqlite3 database/bensley_master.db ".backup database/bensley_master_BACKUP_2025-11-24.db"

BEGIN TRANSACTION;

-- ============================================================================
-- STEP 1: Understand what we have
-- ============================================================================

-- proposals table (87 records) - 2025 SALES PIPELINE
--   53 lost
--   33 active proposals
--    1 won (BK-033)
-- THIS IS CORRECT - keep as-is

-- projects table (110 records) - MIXED MESS
--   64 from source_db='proposals' (WRONG! These shouldn't be in projects)
--   42 from source_db='contracts' (CORRECT - these are signed contracts)
--    4 from source_db=NULL (unknown)

-- proposal_tracker table (33 records) - DUPLICATE GARBAGE
-- DELETE THIS TABLE ENTIRELY

-- ============================================================================
-- STEP 2: Delete the garbage proposal_tracker table
-- ============================================================================

DROP TABLE IF EXISTS proposal_tracker;
DROP TABLE IF EXISTS proposal_tracker_audit_log;
DROP TABLE IF EXISTS proposal_tracker_status_history;

SELECT 'Step 2 Complete: Deleted proposal_tracker tables';

-- ============================================================================
-- STEP 3: Remove PROPOSALS from projects table
-- ============================================================================

-- Projects table should ONLY have SIGNED CONTRACTS
-- Remove anything with source_db='proposals' (these are not contracts yet)

DELETE FROM projects WHERE source_db = 'proposals';

SELECT 'Step 3 Complete: Removed ' || changes() || ' proposals from projects table';

-- ============================================================================
-- STEP 4: Verify projects table now only has CONTRACTS
-- ============================================================================

-- After Step 3, projects table should have:
--   42 from source_db='contracts' (signed contracts)
--    4 from source_db=NULL (we'll investigate these)
-- Total: 46 projects (all signed contracts)

SELECT 'Projects remaining: ' || COUNT(*) FROM projects;
SELECT 'Contracts: ' || COUNT(*) FROM projects WHERE source_db = 'contracts';
SELECT 'Unknown: ' || COUNT(*) FROM projects WHERE source_db IS NULL;

-- ============================================================================
-- STEP 5: Add the WON proposal to projects table
-- ============================================================================

-- BK-033 (Ritz Carlton) is marked as won in proposals
-- It should ALSO be in projects table as an active contract

INSERT OR IGNORE INTO projects (
    project_code,
    project_title,
    client_id,
    source_db,
    status,
    project_type,
    country,
    total_fee_usd,
    date_created,
    notes,
    source_type,
    created_by
)
SELECT
    p.project_code,
    p.project_name as project_title,
    NULL as client_id, -- TODO: link to clients table
    'proposals' as source_db,
    'Active' as status, -- Won proposal = Active project
    CASE
        WHEN p.is_landscape = 1 THEN 'Landscape'
        WHEN p.is_architect = 1 THEN 'Architecture'
        WHEN p.is_interior = 1 THEN 'Interior'
        ELSE 'Mixed'
    END as project_type,
    NULL as country, -- proposals table doesn't have country
    p.project_value as total_fee_usd,
    p.contract_signed_date as date_created,
    'Migrated from won proposal' as notes,
    'proposals_migration' as source_type,
    'database_cleanup_script' as created_by
FROM proposals p
WHERE p.status = 'won'
  AND p.is_active_project = 1
  AND NOT EXISTS (
      SELECT 1 FROM projects pr WHERE pr.project_code = p.project_code
  );

SELECT 'Step 5 Complete: Added ' || changes() || ' won proposals to projects';

-- ============================================================================
-- STEP 6: Create summary report
-- ============================================================================

CREATE TEMP TABLE cleanup_summary AS
SELECT
    'proposals' as table_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN status = 'proposal' THEN 1 ELSE 0 END) as active_proposals,
    SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as won_proposals,
    SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as lost_proposals
FROM proposals
UNION ALL
SELECT
    'projects' as table_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_projects,
    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled
FROM projects;

SELECT '=== CLEANUP SUMMARY ===';
SELECT * FROM cleanup_summary;

-- ============================================================================
-- STEP 7: Verify data quality
-- ============================================================================

-- Check for orphaned data
SELECT 'Checking for orphaned email_proposal_links...';
SELECT COUNT(*) as orphaned_email_links
FROM email_proposal_links epl
WHERE NOT EXISTS (SELECT 1 FROM proposals p WHERE p.project_code = epl.project_code);

SELECT 'Checking for orphaned proposal_timeline...';
SELECT COUNT(*) as orphaned_timeline
FROM proposal_timeline pt
WHERE NOT EXISTS (SELECT 1 FROM proposals p WHERE p.project_code = pt.project_code);

-- ============================================================================
-- STEP 8: Final verification
-- ============================================================================

SELECT '=== FINAL STATE ===';
SELECT 'proposals table:' as description, COUNT(*) as count FROM proposals
UNION ALL
SELECT 'projects table:', COUNT(*) FROM projects
UNION ALL
SELECT 'proposal_tracker (should be 0):', COUNT(*) FROM sqlite_master WHERE type='table' AND name='proposal_tracker';

COMMIT;

SELECT '=== DATABASE CLEANUP COMPLETE ===';
SELECT 'proposals table: Sales pipeline (87 records: 33 active, 53 lost, 1 won)';
SELECT 'projects table: Signed contracts ONLY (~47 records)';
SELECT 'proposal_tracker: DELETED';
