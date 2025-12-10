-- Migration 064: Delete old garbage suggestions
-- The AI was hallucinating and auto-linking garbage. Clean slate for review-first approach.

-- Delete all pending suggestions of these types (they're unreliable)
DELETE FROM ai_suggestions
WHERE suggestion_type IN ('action_required', 'follow_up_needed', 'email_review', 'link_review')
AND status = 'pending';

-- Delete old pending email_link suggestions (>30 days old, likely stale)
DELETE FROM ai_suggestions
WHERE suggestion_type = 'email_link'
AND status = 'pending'
AND created_at < datetime('now', '-30 days');

-- Also clean up info suggestions that were never actionable
DELETE FROM ai_suggestions
WHERE suggestion_type = 'info'
AND status = 'pending';
