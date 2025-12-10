-- Migration 070: Cleanup Old Garbage Suggestions
-- Removes obsolete suggestion types that are no longer used
-- PRESERVES: email_learned_patterns (121 patterns), email_link suggestions
-- Part of Phase 2.0: Context-Aware Multi-Tag System

-- Count before cleanup (for verification)
-- SELECT suggestion_type, status, COUNT(*) FROM ai_suggestions GROUP BY suggestion_type, status;

-- Delete old garbage suggestion types that are pending
-- These types are no longer used in the new system:
-- - action_required: Replaced by smarter suggestion system
-- - follow_up_needed: Now handled by conversation state tracking
-- - email_review: Replaced by multi-tag categorization
-- - link_review: Replaced by multi-tag categorization

DELETE FROM ai_suggestions
WHERE suggestion_type IN ('action_required', 'follow_up_needed', 'email_review', 'link_review')
  AND status = 'pending';

-- Also clean up very old rejected/applied suggestions (keep last 30 days)
DELETE FROM ai_suggestions
WHERE suggestion_type IN ('action_required', 'follow_up_needed', 'email_review', 'link_review')
  AND status IN ('rejected', 'applied')
  AND created_at < datetime('now', '-30 days');

-- Keep approved suggestions for audit trail but mark as archived
-- (SQLite doesn't have UPDATE with WHERE on same table in subquery easily,
--  so we'll leave approved ones alone for now)

-- Clean up orphaned suggestion_feedback entries (if table exists)
-- DELETE FROM suggestion_feedback
-- WHERE suggestion_id NOT IN (SELECT suggestion_id FROM ai_suggestions);

-- Vacuum to reclaim space (should be run separately)
-- VACUUM;

-- Migration complete marker
INSERT OR IGNORE INTO schema_migrations (version, name, description, applied_at)
VALUES (70, '070_cleanup_old_suggestions', 'Cleanup old garbage suggestions', datetime('now'));
