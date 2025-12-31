-- Migration 104: Sync category -> primary_category
-- Issue #100: Legacy 'category' column out of sync with 'primary_category'
-- Created: 2025-12-31
--
-- PROBLEM:
-- The emails table has TWO category columns:
--   - category: Old/legacy (78% NULL, inconsistent formats)
--   - primary_category: New unified system (100% populated)
--
-- One API endpoint (suggestions.py) was still writing to 'category'
-- instead of 'primary_category', causing 816 mismatched records.
--
-- FIX:
-- 1. Copy any category values to primary_category where primary_category is missing
-- 2. Clear category column to prevent future confusion
-- 3. Backend code fixed to use primary_category exclusively

-- ============================================
-- STEP 1: Sync any stray category values to primary_category
-- (Only where primary_category is somehow NULL/empty)
-- ============================================

-- Map legacy format values first
UPDATE emails
SET primary_category =
    CASE
        WHEN category LIKE 'internal:%' THEN 'INTERNAL'
        WHEN category LIKE 'project:%' THEN 'PROJECT'
        WHEN category LIKE 'proposal:%' THEN 'PROPOSAL'
        WHEN category = 'internal' THEN 'INTERNAL'
        WHEN category = 'project' THEN 'PROJECT'
        WHEN category = 'proposal' THEN 'PROPOSAL'
        WHEN category = 'PERS-INVEST' THEN 'PERSONAL'
        WHEN category = 'BDS-GENERAL' THEN 'PROPOSAL'
        WHEN category = 'internal_scheduling' THEN 'SCHEDULING'
        ELSE UPPER(category)  -- Fallback: uppercase the value
    END
WHERE category IS NOT NULL
  AND (primary_category IS NULL OR primary_category = '');

-- ============================================
-- STEP 2: Clear legacy category column
-- This prevents future confusion and ensures primary_category is the only source
-- ============================================

UPDATE emails SET category = NULL WHERE category IS NOT NULL;

-- ============================================
-- VERIFICATION QUERY (run after migration):
-- SELECT 'After sync', COUNT(*) FROM emails WHERE category IS NOT NULL;
-- Expected: 0 (all values cleared)
-- SELECT 'primary_category coverage', COUNT(*) FROM emails WHERE primary_category IS NOT NULL;
-- Expected: Total email count (100% populated)
-- ============================================
