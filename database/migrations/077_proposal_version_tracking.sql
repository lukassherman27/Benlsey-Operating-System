-- Migration 077: Proposal Version Tracking
-- Enables tracking multiple proposal versions with fees and documents

-- Index for faster version lookups
CREATE INDEX IF NOT EXISTS idx_ea_proposal_version
ON email_attachments(proposal_id, version_number, created_at)
WHERE proposal_id IS NOT NULL;

-- Backfill num_proposals_sent from email_attachments
UPDATE proposals
SET num_proposals_sent = (
    SELECT COUNT(DISTINCT ea.attachment_id)
    FROM email_attachments ea
    WHERE ea.proposal_id = proposals.proposal_id
    AND ea.document_type = 'proposal'
    AND COALESCE(ea.is_junk, 0) = 0
)
WHERE (num_proposals_sent IS NULL OR num_proposals_sent = 0)
AND proposal_id IN (
    SELECT DISTINCT proposal_id FROM email_attachments
    WHERE document_type = 'proposal' AND proposal_id IS NOT NULL
);

-- View combining proposal documents with fee history
CREATE VIEW IF NOT EXISTS v_proposal_versions AS
WITH proposal_docs AS (
    SELECT
        ea.proposal_id,
        ea.attachment_id,
        ea.filename,
        ea.filepath,
        ea.version_number,
        ea.key_terms,
        ea.created_at as doc_created_at,
        e.date as email_date,
        e.email_id,
        e.subject as email_subject,
        e.recipient_emails
    FROM email_attachments ea
    LEFT JOIN emails e ON ea.email_id = e.email_id
    WHERE ea.document_type = 'proposal'
    AND ea.proposal_id IS NOT NULL
    AND COALESCE(ea.is_junk, 0) = 0
),
fee_history AS (
    SELECT
        proposal_id,
        project_code,
        old_value as previous_fee,
        new_value as new_fee,
        changed_at as fee_changed_at,
        changed_by,
        change_source
    FROM proposals_audit_log
    WHERE field_name = 'project_value'
)
SELECT
    p.proposal_id,
    p.project_code,
    p.project_name,
    p.client_company,
    p.contact_person,
    p.num_proposals_sent,
    p.project_value as current_fee,
    p.status,
    pd.attachment_id,
    pd.filename as proposal_document,
    pd.filepath,
    pd.version_number,
    pd.key_terms,
    pd.email_subject,
    pd.recipient_emails,
    DATE(COALESCE(pd.email_date, pd.doc_created_at)) as version_date,
    fh.previous_fee,
    fh.new_fee,
    fh.fee_changed_at,
    fh.changed_by as fee_changed_by
FROM proposals p
LEFT JOIN proposal_docs pd ON p.proposal_id = pd.proposal_id
LEFT JOIN fee_history fh ON p.proposal_id = fh.proposal_id
ORDER BY p.project_code, COALESCE(pd.version_number, 0), pd.email_date;
