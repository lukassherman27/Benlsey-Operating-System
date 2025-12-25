-- Migration 093: Auto-update ball_in_court based on email direction
-- Issue #94: When emails are linked to proposals, update ball_in_court automatically
-- Created: 2025-12-25

-- Drop trigger if exists (for idempotency)
DROP TRIGGER IF EXISTS trg_auto_ball_in_court;

-- Create trigger to auto-update ball_in_court when email is linked to proposal
-- Logic:
--   - If client emails us -> ball is with "us" (we need to respond)
--   - If Bensley emails client -> ball is with "them" (waiting for response)
CREATE TRIGGER trg_auto_ball_in_court
AFTER INSERT ON email_proposal_links
FOR EACH ROW
BEGIN
    UPDATE proposals
    SET ball_in_court = CASE
        WHEN (SELECT sender_category FROM emails WHERE email_id = NEW.email_id) = 'client'
        THEN 'us'
        WHEN (SELECT sender_category FROM emails WHERE email_id = NEW.email_id) IN ('bill', 'brian', 'lukas', 'mink', 'bensley_other')
        THEN 'them'
        ELSE ball_in_court  -- Keep current value if unknown
    END,
    last_contact_date = COALESCE(
        (SELECT normalized_date FROM emails WHERE email_id = NEW.email_id),
        last_contact_date
    )
    WHERE proposal_id = NEW.proposal_id;
END;

-- Record migration
INSERT OR IGNORE INTO schema_migrations (version, name, applied_at)
VALUES (93, '093_auto_ball_in_court_trigger', datetime('now'));
