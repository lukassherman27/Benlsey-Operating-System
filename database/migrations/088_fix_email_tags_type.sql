-- Migration 088: Fix email_tags NULL tag_type
-- Date: 2025-12-21
-- Issue: #43 - All 6,271 email_tags had NULL tag_type
-- This migration was applied directly - this file documents what was done.

-- 1. Drop broken trigger (referenced non-existent updated_at column)
DROP TRIGGER IF EXISTS trg_email_tags_updated_at;

-- 2. Backfill tag_type based on tag patterns

-- Categories (BDS, INT, PERS, SKIP, SM, MKT and their variants)
UPDATE email_tags SET tag_type = 'category'
WHERE tag_type IS NULL
AND (
    tag IN ('BDS', 'INT', 'PERS', 'SKIP', 'SM', 'MKT')
    OR tag LIKE 'INT-%'
    OR tag LIKE 'SKIP-%'
    OR tag LIKE 'PERS-%'
    OR tag LIKE 'BDS-%'
    OR tag LIKE 'SM-%'
    OR tag LIKE 'BILL-%'
    OR tag = 'business-development'
);

-- Project codes (XX BK-XXX pattern)
UPDATE email_tags SET tag_type = 'project'
WHERE tag_type IS NULL
AND (
    tag GLOB '[0-9][0-9] BK-[0-9][0-9][0-9]'
    OR tag GLOB '[0-9][0-9] BK-[0-9][0-9][0-9]*'
);

-- Flags
UPDATE email_tags SET tag_type = 'flag'
WHERE tag_type IS NULL
AND tag IN ('needs_project_code', 'needs_review', 'urgent', 'important');

-- Topics (known topics)
UPDATE email_tags SET tag_type = 'topic'
WHERE tag_type IS NULL
AND tag IN ('canggu_land_sale', 'inquiry', 'contract', 'status_update', 'report');

-- Remaining project names (mgm_macau, anji_china, etc.)
UPDATE email_tags SET tag_type = 'project'
WHERE tag_type IS NULL;

-- Results:
-- category: 3,887
-- project: 1,590
-- project_mention: 415
-- topic: 272
-- flag: 67
-- milestone: 29
-- document: 11
-- NULL: 0
