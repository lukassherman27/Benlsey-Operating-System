-- Category Consolidation Migration (#317)
--
-- Problem: Three overlapping category systems:
--   1. emails.primary_category (PROPOSAL, PROJECT, INTERNAL, SCHEDULING, etc.)
--   2. emails.email_type (internal, client_external, etc.)
--   3. email_content.category (internal_scheduling, project_contracts, etc.)
--
-- Solution: Consolidate to emails.primary_category as single source of truth.
--
-- Run with: sqlite3 database/bensley_master.db < scripts/migrations/consolidate_email_categories.sql

-- Step 1: Migrate email_type to primary_category where primary_category is missing
-- Map email_type values to primary_category values
UPDATE emails
SET primary_category = CASE email_type
    WHEN 'internal' THEN 'INTERNAL'
    WHEN 'client_external' THEN 'PROPOSAL'  -- Client emails usually about proposals
    WHEN 'operator_external' THEN 'PROJECT'  -- Operator emails usually about projects
    WHEN 'developer_external' THEN 'PROJECT'
    WHEN 'consultant_external' THEN 'PROJECT'
    WHEN 'vendor_external' THEN 'PROJECT'
    WHEN 'spam' THEN 'SPAM'
    WHEN 'administrative' THEN 'INTERNAL'
    ELSE 'UNCATEGORIZED'
END
WHERE primary_category IS NULL
AND email_type IS NOT NULL
AND email_type != '';

-- Step 2: Migrate email_content.category where emails.primary_category is still missing
-- This handles older emails that only have email_content categorization
UPDATE emails
SET primary_category = CASE
    WHEN ec.category LIKE '%proposal%' THEN 'PROPOSAL'
    WHEN ec.category LIKE '%project%' THEN 'PROJECT'
    WHEN ec.category = 'internal_scheduling' THEN 'SCHEDULING'
    WHEN ec.category = 'internal' THEN 'INTERNAL'
    WHEN ec.category LIKE '%contract%' THEN 'PROJECT-CONTRACT'
    WHEN ec.category LIKE '%design%' THEN 'PROJECT-DESIGN'
    WHEN ec.category LIKE '%financial%' OR ec.category LIKE '%invoice%' THEN 'INT-FIN'
    WHEN ec.category LIKE 'PERS%' THEN 'PERSONAL'
    ELSE 'UNCATEGORIZED'
END
FROM email_content ec
WHERE emails.email_id = ec.email_id
AND (emails.primary_category IS NULL OR emails.primary_category = '')
AND ec.category IS NOT NULL
AND ec.category != '';

-- Step 3: Add comment documenting deprecation (SQLite doesn't support table comments,
-- but we document it here for reference)
--
-- DEPRECATED FIELDS (do not use, will be removed in future):
--   - emails.email_type: Replaced by emails.primary_category
--   - emails.category: Replaced by emails.primary_category
--   - email_content.category: Replaced by emails.primary_category
--
-- Going forward, only use emails.primary_category for email categorization.

-- Step 4: Show migration results
SELECT 'Migration complete. Category distribution:';
SELECT primary_category, COUNT(*) as count
FROM emails
WHERE primary_category IS NOT NULL
GROUP BY primary_category
ORDER BY count DESC;

SELECT '';
SELECT 'Emails still without primary_category: ' || COUNT(*)
FROM emails
WHERE primary_category IS NULL OR primary_category = '';
