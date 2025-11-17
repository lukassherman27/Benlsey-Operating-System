-- ========================================
-- Migration 015: Merge Proposals into Projects Table
-- ========================================
-- Purpose: Consolidate proposals and projects into single unified table
-- The projects table already has status/is_active_project fields
-- This migration imports all proposals that don't exist in projects
-- ========================================

-- Step 1: Add any missing fields from proposals table to projects table
-- Note: Using Python script approach since SQLite doesn't support IF NOT EXISTS for ALTER TABLE

-- Step 2: Update existing duplicates in projects table with data from proposals
UPDATE projects
SET
    project_name = COALESCE(project_name, (SELECT project_title FROM proposals WHERE proposals.project_code = projects.project_code)),
    project_type = (SELECT project_type FROM proposals WHERE proposals.project_code = projects.project_code),
    country = (SELECT country FROM proposals WHERE proposals.project_code = projects.project_code),
    city = (SELECT city FROM proposals WHERE proposals.project_code = projects.project_code),
    total_fee_usd = COALESCE(total_fee_usd, (SELECT total_fee_usd FROM proposals WHERE proposals.project_code = projects.project_code)),
    contract_term_months = COALESCE(contract_term_months, (SELECT contract_term_months FROM proposals WHERE proposals.project_code = projects.project_code)),
    contract_expiry_date = COALESCE(contract_expiry_date, (SELECT contract_expiry_date FROM proposals WHERE proposals.project_code = projects.project_code)),
    folder_path = (SELECT folder_path FROM proposals WHERE proposals.project_code = projects.project_code),
    source_db = (SELECT source_db FROM proposals WHERE proposals.project_code = projects.project_code),
    source_ref = (SELECT source_ref FROM proposals WHERE proposals.project_code = projects.project_code),
    updated_at = CURRENT_TIMESTAMP
WHERE project_code IN (SELECT project_code FROM proposals);

-- Step 3: Insert proposals that DON'T exist in projects table
-- These are pure proposals (89 records) that haven't been converted to projects yet
INSERT INTO projects (
    project_code,
    project_name,
    project_type,
    country,
    city,
    total_fee_usd,
    contract_term_months,
    contract_expiry_date,
    folder_path,
    source_db,
    source_ref,
    status,
    is_active_project,
    created_at,
    updated_at
)
SELECT
    pr.project_code,
    pr.project_title,
    pr.project_type,
    pr.country,
    pr.city,
    pr.total_fee_usd,
    pr.contract_term_months,
    pr.contract_expiry_date,
    pr.folder_path,
    pr.source_db,
    pr.source_ref,
    COALESCE(pr.status, 'proposal'),  -- Set status from proposals or default to 'proposal'
    CASE
        WHEN pr.status IN ('Active', 'Completed') THEN 1
        ELSE 0
    END,  -- Set is_active_project based on status
    pr.date_created,
    CURRENT_TIMESTAMP
FROM proposals pr
WHERE pr.project_code NOT IN (SELECT project_code FROM projects);

-- Step 4: Standardize status values across all projects
-- Map proposals status values to consistent values
UPDATE projects
SET status = CASE
    WHEN status IN ('Active', 'active') THEN 'active'
    WHEN status IN ('Proposal', 'proposal') THEN 'proposal'
    WHEN status IN ('Completed', 'completed') THEN 'completed'
    WHEN status IN ('On-Hold', 'on_hold', 'on-hold') THEN 'on_hold'
    WHEN status = 'archived' THEN 'archived'
    WHEN status = 'lost' THEN 'lost'
    ELSE 'proposal'  -- Default unknown statuses to proposal
END,
is_active_project = CASE
    WHEN status IN ('Active', 'active') THEN 1
    WHEN is_active_project = 1 THEN 1
    ELSE 0
END,
updated_at = CURRENT_TIMESTAMP;

-- Step 5: Create backup of proposals table (in case we need to rollback)
DROP TABLE IF EXISTS proposals_backup;
CREATE TABLE proposals_backup AS SELECT * FROM proposals;

-- Step 6: Add index on status for better query performance
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_is_active ON projects(is_active_project);
CREATE INDEX IF NOT EXISTS idx_projects_status_active ON projects(status, is_active_project);

-- Migration tracking
INSERT INTO schema_migrations (version, name, description, applied_at)
VALUES (15, '015_merge_proposals_into_projects', 'Merge proposals table into unified projects table with lifecycle status', CURRENT_TIMESTAMP);

-- Summary of changes:
-- Projects table now contains:
--   - All 39 original projects (updated with proposals data where it existed)
--   - All 89 pure proposals (newly inserted)
--   - Total: 128 records in projects table (39 + 89)
--   - Standardized status values: 'proposal', 'active', 'completed', 'on_hold', 'archived', 'lost'
--
-- proposals table:
--   - Backed up to proposals_backup
--   - Can be deprecated (all services should use projects table)
--   - Keep for now for backwards compatibility, can drop later
