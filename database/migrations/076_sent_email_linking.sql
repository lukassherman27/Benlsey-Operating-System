-- Migration 076: Sent Email Linking Infrastructure
-- Enables linking outbound @bensley.com emails to proposals via recipients

-- Index for faster contact_email lookups
CREATE INDEX IF NOT EXISTS idx_proposals_contact_email
ON proposals(contact_email) WHERE contact_email IS NOT NULL;

-- Index for email direction queries
CREATE INDEX IF NOT EXISTS idx_emails_direction
ON emails(email_direction) WHERE email_direction IS NOT NULL;

-- Backfill email_direction for existing emails
UPDATE emails
SET email_direction = 'sent'
WHERE (sender_email LIKE '%@bensley.com%' OR sender_email LIKE '%@bensley.co.id%')
AND (email_direction IS NULL OR email_direction = '');

UPDATE emails
SET email_direction = 'received'
WHERE sender_email NOT LIKE '%@bensley.com%'
AND sender_email NOT LIKE '%@bensley.co.id%'
AND (email_direction IS NULL OR email_direction = '');

-- View to consolidate all recipient-to-proposal mappings
CREATE VIEW IF NOT EXISTS v_recipient_proposal_map AS
-- From proposals.contact_email (highest confidence)
SELECT
    LOWER(TRIM(p.contact_email)) as recipient_email,
    p.proposal_id,
    p.project_code,
    p.project_name,
    'proposals.contact_email' as source,
    0.95 as confidence
FROM proposals p
WHERE p.contact_email IS NOT NULL
AND LENGTH(TRIM(p.contact_email)) > 5
AND p.contact_email LIKE '%@%'

UNION ALL

-- From contacts table via project_contact_links
SELECT
    LOWER(TRIM(c.email)) as recipient_email,
    pcl.proposal_id,
    p.project_code,
    p.project_name,
    'contacts.project_contact_links' as source,
    0.85 as confidence
FROM contacts c
JOIN project_contact_links pcl ON c.contact_id = pcl.contact_id
JOIN proposals p ON pcl.proposal_id = p.proposal_id
WHERE c.email IS NOT NULL
AND LENGTH(TRIM(c.email)) > 5
AND pcl.proposal_id IS NOT NULL;
