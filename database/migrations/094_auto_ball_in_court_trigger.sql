-- Migration 094: Auto-update ball_in_court when emails are linked
-- Created: 2024-12-25
-- Issue: #94 - Auto-update ball_in_court based on email direction
-- Depends on: Migration 093 (sender_category column)

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS trg_auto_ball_in_court;

-- Create trigger to auto-update ball_in_court when email is linked
CREATE TRIGGER trg_auto_ball_in_court
AFTER INSERT ON email_proposal_links
FOR EACH ROW
BEGIN
    UPDATE proposals
    SET
        ball_in_court = CASE
            -- If client sent the email, ball is with US
            WHEN (SELECT sender_category FROM emails WHERE email_id = NEW.email_id) = 'client'
            THEN 'us'
            -- If Bensley person sent external email, ball is with THEM
            WHEN (SELECT sender_category FROM emails WHERE email_id = NEW.email_id) IN ('bill', 'brian', 'lukas', 'mink')
                AND (SELECT email_direction FROM emails WHERE email_id = NEW.email_id) IN ('internal_to_external', 'OUTBOUND', 'sent')
            THEN 'them'
            -- Otherwise keep current value
            ELSE ball_in_court
        END,
        -- Also update last_contact_date if this email is more recent
        last_contact_date = MAX(
            COALESCE(last_contact_date, '1900-01-01'),
            (SELECT date(date) FROM emails WHERE email_id = NEW.email_id)
        )
    WHERE proposal_id = NEW.proposal_id
      AND status NOT IN ('Dormant', 'Lost', 'Declined', 'Contract Signed');
END;
