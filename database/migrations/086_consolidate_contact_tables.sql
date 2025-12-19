-- Migration 086: Consolidate Contact Tables
-- Reduces 26 contact-related tables down to core set
-- Run: sqlite3 database/bensley_master.db < database/migrations/086_consolidate_contact_tables.sql

-- ============================================================================
-- STEP 1: Merge proposal_stakeholders into contacts (110 records)
-- ============================================================================

-- Add any stakeholders not already in contacts
INSERT OR IGNORE INTO contacts (email, name, company, role, contact_type, context_notes, source)
SELECT
    ps.email,
    ps.name,
    ps.company,
    ps.role,
    'client',
    'From proposal ' || ps.project_code || '. Role: ' || COALESCE(ps.role, 'unknown'),
    'proposal_stakeholders'
FROM proposal_stakeholders ps
WHERE ps.email IS NOT NULL
AND ps.email != ''
AND NOT EXISTS (
    SELECT 1 FROM contacts c
    WHERE LOWER(REPLACE(REPLACE(c.email, '<', ''), '>', '')) = LOWER(ps.email)
);

-- ============================================================================
-- STEP 2: Remove BENSLEY staff from contacts (they belong in staff table)
-- ============================================================================

-- First, verify they exist in staff
-- Then delete from contacts
DELETE FROM contacts
WHERE (email LIKE '%@bensley.com%' OR email LIKE '%@bensley.co.id%')
AND EXISTS (
    SELECT 1 FROM staff s
    WHERE LOWER(s.email) = LOWER(REPLACE(REPLACE(contacts.email, '<', ''), '>', ''))
       OR LOWER(s.email) LIKE '%' || LOWER(REPLACE(REPLACE(REPLACE(REPLACE(contacts.email, '<', ''), '>', ''), '"', ''), ' ', '')) || '%'
);

-- ============================================================================
-- STEP 3: Merge contact_project_mappings data into project_team
-- ============================================================================

-- Insert contact-project links that don't already exist
INSERT OR IGNORE INTO project_team (project_code, contact_id, company, notes, is_active)
SELECT
    cpm.project_code,
    c.contact_id,
    cpm.contact_name,
    'Linked via ' || cpm.email_count || ' emails. First: ' || cpm.first_email_date || ', Last: ' || cpm.last_email_date,
    1
FROM contact_project_mappings cpm
JOIN contacts c ON LOWER(REPLACE(REPLACE(c.email, '<', ''), '>', '')) LIKE '%' || LOWER(cpm.contact_email) || '%'
WHERE NOT EXISTS (
    SELECT 1 FROM project_team pt
    WHERE pt.project_code = cpm.project_code
    AND pt.contact_id = c.contact_id
);

-- ============================================================================
-- STEP 4: Build clients table from contact companies
-- ============================================================================

-- Extract unique companies from contacts
INSERT OR IGNORE INTO clients (company_name, country)
SELECT DISTINCT
    company,
    NULL
FROM contacts
WHERE company IS NOT NULL
AND company != ''
AND company NOT LIKE '%@%'
AND LENGTH(company) > 2
AND company NOT IN ('client', 'unknown', 'Unknown', 'N/A', 'na', 'NA');

-- ============================================================================
-- STEP 5: Drop duplicate/obsolete tables
-- ============================================================================

-- team_members is duplicate of staff (98% overlap)
DROP TABLE IF EXISTS team_members;
DROP TABLE IF EXISTS team_member_specialties;

-- These are superseded by project_team
DROP TABLE IF EXISTS contact_project_history;  -- empty, I created today
DROP TABLE IF EXISTS project_contact_links;    -- superseded by project_team

-- Raw extraction tables (already processed)
DROP TABLE IF EXISTS email_extracted_contacts;

-- Context history not needed
DROP TABLE IF EXISTS contact_context_history;

-- ============================================================================
-- STEP 6: Keep but rename contact_project_mappings for reference
-- Then drop after verifying project_team has the data
-- ============================================================================

-- We'll keep contact_project_mappings as read-only reference for now
-- Can drop later: DROP TABLE IF EXISTS contact_project_mappings;

-- ============================================================================
-- FINAL: Verify counts
-- ============================================================================

-- This will show counts after migration
SELECT 'contacts' as tbl, COUNT(*) as cnt FROM contacts
UNION ALL SELECT 'staff', COUNT(*) FROM staff
UNION ALL SELECT 'clients', COUNT(*) FROM clients
UNION ALL SELECT 'project_team', COUNT(*) FROM project_team;
