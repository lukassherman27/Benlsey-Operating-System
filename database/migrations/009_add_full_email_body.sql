-- Migration 009: Add full email body storage
-- Store complete email bodies, not just 200 char previews

ALTER TABLE emails ADD COLUMN body_full TEXT;

-- Update body_preview to be just first 500 chars (for quick display)
-- body_full will have complete content
