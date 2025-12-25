-- Migration 091: Backfill Email Categories
-- Maps old category values to new unified codes
-- Created: 2025-12-25

-- ============================================
-- STEP 1: Map email_content.category to new codes
-- ============================================

-- internal_scheduling → SCHEDULING
UPDATE emails SET primary_category = 'SCHEDULING'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'internal_scheduling');

-- project_contracts → PROJECT-CONTRACT
UPDATE emails SET primary_category = 'PROJECT-CONTRACT'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'project_contracts');

-- project_design → PROJECT-DESIGN
UPDATE emails SET primary_category = 'PROJECT-DESIGN'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'project_design');

-- project_financial → PROJECT-FINANCIAL
UPDATE emails SET primary_category = 'PROJECT-FINANCIAL'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'project_financial');

-- internal, internal_operations → INTERNAL
UPDATE emails SET primary_category = 'INTERNAL'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category IN ('internal', 'internal_operations'));

-- automated_notification → SKIP-AUTO
UPDATE emails SET primary_category = 'SKIP-AUTO'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'automated_notification');

-- client_communication → PROPOSAL (usually BD-related)
UPDATE emails SET primary_category = 'PROPOSAL'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'client_communication');

-- design → PROJECT-DESIGN
UPDATE emails SET primary_category = 'PROJECT-DESIGN'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'design');

-- vendor_supplier → INTERNAL-OPS
UPDATE emails SET primary_category = 'INTERNAL-OPS'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'vendor_supplier');

-- marketing_outreach → PR
UPDATE emails SET primary_category = 'PR'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'marketing_outreach');

-- personal → PERSONAL
UPDATE emails SET primary_category = 'PERSONAL'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'personal');

-- ============================================
-- STEP 2: Map existing primary_category codes
-- ============================================

-- BDS → PROPOSAL (clearer name)
UPDATE emails SET primary_category = 'PROPOSAL' WHERE primary_category = 'BDS';

-- INT → INTERNAL
UPDATE emails SET primary_category = 'INTERNAL' WHERE primary_category = 'INT';

-- PERS → PERSONAL
UPDATE emails SET primary_category = 'PERSONAL' WHERE primary_category = 'PERS';

-- MKT → PR
UPDATE emails SET primary_category = 'PR' WHERE primary_category = 'MKT';

-- Keep SM variants as-is (SM, SM-WILD already correct format)
-- Keep SKIP variants as-is (SKIP, SKIP-SPAM, SKIP-AUTO already correct)

-- Map email_content values that are already using new format
UPDATE emails SET primary_category = 'PERSONAL-BILL'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'PERS-BILL');

UPDATE emails SET primary_category = 'INTERNAL-OPS'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'INT-OPS');

UPDATE emails SET primary_category = 'INTERNAL'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'INT-LEGAL');

UPDATE emails SET primary_category = 'SM-WILD'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'SM-WILD');

-- ============================================
-- STEP 3: Backfill from links (emails linked to proposals/projects)
-- ============================================

-- Emails linked to proposals → PROPOSAL (unless already more specific like PROJECT-*)
UPDATE emails SET primary_category = 'PROPOSAL'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_proposal_links);

-- Emails linked to projects but not proposals → PROJECT
UPDATE emails SET primary_category = 'PROJECT'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_project_links);

-- ============================================
-- STEP 4: Backfill purely internal emails
-- ============================================

-- Purely internal emails (@bensley.com → @bensley.com only) → INTERNAL
UPDATE emails SET primary_category = 'INTERNAL'
WHERE primary_category IS NULL
AND is_purely_internal = 1;

-- ============================================
-- STEP 5: Map any remaining BDS/INT email_content categories
-- ============================================

UPDATE emails SET primary_category = 'PROPOSAL'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'BDS');

UPDATE emails SET primary_category = 'INTERNAL'
WHERE primary_category IS NULL
AND email_id IN (SELECT email_id FROM email_content WHERE category = 'INT');
