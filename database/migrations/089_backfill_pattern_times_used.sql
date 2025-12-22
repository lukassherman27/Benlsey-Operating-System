-- Migration 089: Backfill pattern times_used from existing links
-- Date: 2025-12-22
-- Issue: #16 - 150/152 patterns have times_used = 0 despite emails being linked
--
-- Root cause: Most emails were linked by other methods (tag_based, thread_inheritance)
-- before patterns were created. Pattern system works but times_used wasn't backfilled.
--
-- This migration counts actual matches and updates times_used accordingly.

-- 1. Backfill sender_to_proposal patterns
-- Count emails where: sender matches pattern AND email is linked to pattern's target
UPDATE email_learned_patterns
SET times_used = (
    SELECT COUNT(*)
    FROM emails e
    JOIN email_proposal_links epl ON e.email_id = epl.email_id
    WHERE LOWER(e.sender_email) LIKE '%' || LOWER(email_learned_patterns.pattern_key) || '%'
    AND epl.proposal_id = email_learned_patterns.target_id
),
updated_at = datetime('now')
WHERE pattern_type = 'sender_to_proposal';

-- 2. Backfill domain_to_proposal patterns
UPDATE email_learned_patterns
SET times_used = (
    SELECT COUNT(*)
    FROM emails e
    JOIN email_proposal_links epl ON e.email_id = epl.email_id
    WHERE LOWER(e.sender_email) LIKE '%@' || LOWER(email_learned_patterns.pattern_key)
    AND epl.proposal_id = email_learned_patterns.target_id
),
updated_at = datetime('now')
WHERE pattern_type = 'domain_to_proposal';

-- 3. Backfill sender_to_project patterns
UPDATE email_learned_patterns
SET times_used = (
    SELECT COUNT(*)
    FROM emails e
    JOIN email_project_links eprl ON e.email_id = eprl.email_id
    WHERE LOWER(e.sender_email) LIKE '%' || LOWER(email_learned_patterns.pattern_key) || '%'
    AND eprl.project_id = email_learned_patterns.target_id
),
updated_at = datetime('now')
WHERE pattern_type = 'sender_to_project';

-- 4. Backfill domain_to_project patterns
UPDATE email_learned_patterns
SET times_used = (
    SELECT COUNT(*)
    FROM emails e
    JOIN email_project_links eprl ON e.email_id = eprl.email_id
    WHERE LOWER(e.sender_email) LIKE '%@' || LOWER(email_learned_patterns.pattern_key)
    AND eprl.project_id = email_learned_patterns.target_id
),
updated_at = datetime('now')
WHERE pattern_type = 'domain_to_project';

-- 5. Update last_used_at for patterns that have been used
UPDATE email_learned_patterns
SET last_used_at = (
    SELECT MAX(epl.created_at)
    FROM emails e
    JOIN email_proposal_links epl ON e.email_id = epl.email_id
    WHERE LOWER(e.sender_email) LIKE '%' || LOWER(email_learned_patterns.pattern_key) || '%'
    AND epl.proposal_id = email_learned_patterns.target_id
)
WHERE pattern_type IN ('sender_to_proposal', 'domain_to_proposal')
AND times_used > 0;

UPDATE email_learned_patterns
SET last_used_at = (
    SELECT MAX(eprl.created_at)
    FROM emails e
    JOIN email_project_links eprl ON e.email_id = eprl.email_id
    WHERE LOWER(e.sender_email) LIKE '%' || LOWER(email_learned_patterns.pattern_key) || '%'
    AND eprl.project_id = email_learned_patterns.target_id
)
WHERE pattern_type IN ('sender_to_project', 'domain_to_project')
AND times_used > 0;
