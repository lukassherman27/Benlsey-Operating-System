-- Migration 081: Fix last_contact_date to use actual email data
-- Date: 2025-12-11
-- Problem: last_contact_date is static and never updates when emails are linked
-- Solution:
--   1. Update view to calculate from actual emails
--   2. Add trigger to update on new email links
--   3. Backfill all existing proposals

-- ============================================
-- STEP 1: Backfill all proposals with actual email dates
-- ============================================

UPDATE proposals
SET last_contact_date = (
    SELECT MAX(date(e.date))
    FROM emails e
    JOIN email_proposal_links epl ON e.email_id = epl.email_id
    WHERE epl.proposal_id = proposals.proposal_id
)
WHERE proposal_id IN (
    SELECT DISTINCT proposal_id FROM email_proposal_links
);

-- ============================================
-- STEP 2: Create trigger to update last_contact_date when email is linked
-- ============================================

DROP TRIGGER IF EXISTS trg_update_last_contact_on_email_link;

CREATE TRIGGER trg_update_last_contact_on_email_link
AFTER INSERT ON email_proposal_links
FOR EACH ROW
BEGIN
    UPDATE proposals
    SET last_contact_date = (
        SELECT MAX(date(e.date))
        FROM emails e
        JOIN email_proposal_links epl ON e.email_id = epl.email_id
        WHERE epl.proposal_id = NEW.proposal_id
    )
    WHERE proposal_id = NEW.proposal_id;
END;

-- ============================================
-- STEP 3: Drop and recreate the priority view with better logic
-- ============================================

DROP VIEW IF EXISTS v_proposal_priorities;

CREATE VIEW v_proposal_priorities AS
SELECT
    p.proposal_id,
    p.project_code,
    p.project_name,
    p.current_status as status,
    p.project_value,
    p.contact_person,

    -- Calculate ACTUAL last contact from emails (not the static field)
    COALESCE(
        (SELECT MAX(date(e.date)) FROM emails e
         JOIN email_proposal_links epl ON e.email_id = epl.email_id
         WHERE epl.proposal_id = p.proposal_id),
        p.last_contact_date,
        date(p.created_at)
    ) as actual_last_contact,

    -- Days since ACTUAL last contact
    CAST(julianday('now') - julianday(
        COALESCE(
            (SELECT MAX(date(e.date)) FROM emails e
             JOIN email_proposal_links epl ON e.email_id = epl.email_id
             WHERE epl.proposal_id = p.proposal_id),
            p.last_contact_date,
            p.created_at
        )
    ) AS INTEGER) as days_silent,

    -- Check if silence is expected
    sr.reason_type as silence_reason,
    sr.valid_until as silence_ok_until,
    sr.reason_detail as silence_detail,

    -- Next scheduled event
    (SELECT MIN(event_date) FROM proposal_events pe
     WHERE pe.project_code = p.project_code AND pe.completed = 0) as next_event,
    (SELECT title FROM proposal_events pe
     WHERE pe.project_code = p.project_code AND pe.completed = 0
     ORDER BY event_date LIMIT 1) as next_event_title,

    -- Follow-up count
    (SELECT COUNT(*) FROM proposal_follow_ups pf
     WHERE pf.project_code = p.project_code) as follow_up_count,

    -- Last follow-up date
    (SELECT MAX(sent_date) FROM proposal_follow_ups pf
     WHERE pf.project_code = p.project_code) as last_follow_up_date,

    -- Last proposal sent
    (SELECT MAX(sent_date) FROM proposal_documents pd
     WHERE pd.project_code = p.project_code AND pd.doc_type = 'proposal') as proposal_sent_date,

    -- Decision info
    di.expected_decision_date,
    di.our_position,

    -- Priority calculation based on ACTUAL email dates
    CASE
        WHEN sr.valid_until > date('now') THEN 'OK - ' || sr.reason_type
        WHEN p.current_status = 'Negotiation' AND CAST(julianday('now') - julianday(
            COALESCE(
                (SELECT MAX(date(e.date)) FROM emails e
                 JOIN email_proposal_links epl ON e.email_id = epl.email_id
                 WHERE epl.proposal_id = p.proposal_id),
                p.last_contact_date,
                p.created_at
            )
        ) AS INTEGER) > 14 THEN 'URGENT'
        WHEN p.current_status = 'Proposal Sent' AND CAST(julianday('now') - julianday(
            COALESCE(
                (SELECT MAX(date(e.date)) FROM emails e
                 JOIN email_proposal_links epl ON e.email_id = epl.email_id
                 WHERE epl.proposal_id = p.proposal_id),
                p.last_contact_date,
                p.created_at
            )
        ) AS INTEGER) > 21 THEN 'FOLLOW UP'
        WHEN p.current_status = 'First Contact' AND CAST(julianday('now') - julianday(
            COALESCE(
                (SELECT MAX(date(e.date)) FROM emails e
                 JOIN email_proposal_links epl ON e.email_id = epl.email_id
                 WHERE epl.proposal_id = p.proposal_id),
                p.last_contact_date,
                p.created_at
            )
        ) AS INTEGER) > 7 THEN 'RESPOND'
        WHEN p.current_status IN ('Proposal Prep', 'Drafting') AND CAST(julianday('now') - julianday(
            COALESCE(
                (SELECT MAX(date(e.date)) FROM emails e
                 JOIN email_proposal_links epl ON e.email_id = epl.email_id
                 WHERE epl.proposal_id = p.proposal_id),
                p.last_contact_date,
                p.created_at
            )
        ) AS INTEGER) > 14 THEN 'CHECK IN'
        ELSE 'MONITOR'
    END as priority_status

FROM proposals p
LEFT JOIN proposal_silence_reasons sr
    ON p.project_code = sr.project_code AND sr.resolved = 0
LEFT JOIN proposal_decision_info di
    ON p.project_code = di.project_code
WHERE p.current_status NOT IN ('Lost', 'Declined', 'Contract Signed', 'Dormant', 'Archived', 'Contract signed')
ORDER BY
    CASE
        WHEN p.current_status = 'Negotiation' THEN 1
        WHEN p.current_status = 'Proposal Sent' THEN 2
        WHEN p.current_status = 'First Contact' THEN 3
        ELSE 4
    END,
    CAST(julianday('now') - julianday(
        COALESCE(
            (SELECT MAX(date(e.date)) FROM emails e
             JOIN email_proposal_links epl ON e.email_id = epl.email_id
             WHERE epl.proposal_id = p.proposal_id),
            p.last_contact_date,
            p.created_at
        )
    ) AS INTEGER) DESC;
