-- Migration 058: Fix suggestion_user_feedback unique constraint
-- Issue: ON CONFLICT clause in save-feedback endpoint was failing because
-- suggestion_id had only an INDEX, not a UNIQUE constraint
-- Date: 2025-12-02

-- Add unique index to enable ON CONFLICT upsert behavior
CREATE UNIQUE INDEX IF NOT EXISTS idx_suggestion_user_feedback_unique
    ON suggestion_user_feedback(suggestion_id);
