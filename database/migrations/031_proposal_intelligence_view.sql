-- Migration 031: Proposal Intelligence View
-- Combines proposal, email, and attachment data for rich context

-- Drop if exists
DROP VIEW IF EXISTS proposal_intelligence;

-- Create comprehensive intelligence view
CREATE VIEW proposal_intelligence AS
SELECT
    p.proposal_id,
    p.project_code,
    p.project_name,
    p.client_company,
    p.contact_person,
    p.contact_email,
    p.project_value,
    p.current_status,
    p.status,
    p.days_in_current_status,
    p.first_contact_date,
    p.proposal_sent_date,
    p.contract_signed_date,
    p.last_contact_date,
    p.days_since_contact,
    p.health_score,
    p.win_probability,
    p.last_sentiment,
    p.next_action,
    p.next_action_date,
    p.location,
    p.country,
    p.scope_summary,

    -- Email statistics
    COALESCE(email_stats.email_count, 0) as email_count,
    COALESCE(email_stats.inbound_count, 0) as inbound_email_count,
    COALESCE(email_stats.outbound_count, 0) as outbound_email_count,
    email_stats.latest_email_date,
    email_stats.latest_email_subject,
    email_stats.latest_email_summary,

    -- Email category breakdown
    COALESCE(email_stats.contract_emails, 0) as contract_emails,
    COALESCE(email_stats.invoice_emails, 0) as invoice_emails,
    COALESCE(email_stats.design_emails, 0) as design_emails,
    COALESCE(email_stats.meeting_emails, 0) as meeting_emails,
    COALESCE(email_stats.general_emails, 0) as general_emails,

    -- Urgency and action
    COALESCE(email_stats.action_required_count, 0) as emails_needing_action,
    COALESCE(email_stats.urgent_count, 0) as urgent_emails,

    -- Sentiment analysis
    email_stats.dominant_sentiment,
    email_stats.positive_ratio,

    -- Attachment statistics
    COALESCE(attach_stats.attachment_count, 0) as attachment_count,
    COALESCE(attach_stats.contract_docs, 0) as contract_documents,
    COALESCE(attach_stats.proposal_docs, 0) as proposal_documents,
    COALESCE(attach_stats.design_docs, 0) as design_documents,

    -- Status history
    COALESCE(status_history.status_change_count, 0) as status_changes,
    status_history.first_status,
    status_history.last_status_change_date,

    -- Calculated fields
    CASE
        WHEN p.days_since_contact > 30 THEN 'stale'
        WHEN p.days_since_contact > 14 THEN 'cooling'
        WHEN p.days_since_contact > 7 THEN 'active'
        ELSE 'hot'
    END as engagement_level,

    CASE
        WHEN COALESCE(email_stats.urgent_count, 0) > 0 THEN 'urgent'
        WHEN COALESCE(email_stats.action_required_count, 0) > 0 THEN 'action_needed'
        WHEN p.days_since_contact > 14 THEN 'follow_up_needed'
        ELSE 'on_track'
    END as attention_status

FROM proposals p

-- Email statistics subquery
LEFT JOIN (
    SELECT
        ec.linked_project_code,
        COUNT(*) as email_count,
        SUM(CASE WHEN e.folder IN ('INBOX', 'Inbox') THEN 1 ELSE 0 END) as inbound_count,
        SUM(CASE WHEN e.folder IN ('Sent', 'SENT') THEN 1 ELSE 0 END) as outbound_count,
        MAX(e.date) as latest_email_date,
        (SELECT e2.subject FROM emails e2
         JOIN email_content ec2 ON e2.email_id = ec2.email_id
         WHERE ec2.linked_project_code = ec.linked_project_code
         ORDER BY e2.date DESC LIMIT 1) as latest_email_subject,
        (SELECT ec2.ai_summary FROM email_content ec2
         WHERE ec2.linked_project_code = ec.linked_project_code
         AND ec2.ai_summary IS NOT NULL
         ORDER BY ec2.content_id DESC LIMIT 1) as latest_email_summary,

        -- Category counts
        SUM(CASE WHEN ec.category = 'contract' THEN 1 ELSE 0 END) as contract_emails,
        SUM(CASE WHEN ec.category = 'invoice' THEN 1 ELSE 0 END) as invoice_emails,
        SUM(CASE WHEN ec.category = 'design' THEN 1 ELSE 0 END) as design_emails,
        SUM(CASE WHEN ec.category = 'meeting' THEN 1 ELSE 0 END) as meeting_emails,
        SUM(CASE WHEN ec.category = 'general' THEN 1 ELSE 0 END) as general_emails,

        -- Action/urgency counts
        SUM(CASE WHEN ec.action_required = 1 THEN 1 ELSE 0 END) as action_required_count,
        SUM(CASE WHEN ec.urgency_level IN ('high', 'critical') THEN 1 ELSE 0 END) as urgent_count,

        -- Sentiment analysis
        (SELECT ec3.client_sentiment
         FROM email_content ec3
         WHERE ec3.linked_project_code = ec.linked_project_code
         GROUP BY ec3.client_sentiment
         ORDER BY COUNT(*) DESC LIMIT 1) as dominant_sentiment,
        CAST(SUM(CASE WHEN ec.client_sentiment = 'positive' THEN 1 ELSE 0 END) AS REAL) /
            NULLIF(COUNT(*), 0) as positive_ratio

    FROM email_content ec
    JOIN emails e ON ec.email_id = e.email_id
    WHERE ec.linked_project_code IS NOT NULL
    GROUP BY ec.linked_project_code
) email_stats ON p.project_code = email_stats.linked_project_code

-- Attachment statistics
LEFT JOIN (
    SELECT
        ec.linked_project_code,
        COUNT(a.attachment_id) as attachment_count,
        SUM(CASE WHEN a.category = 'external_contract' THEN 1 ELSE 0 END) as contract_docs,
        SUM(CASE WHEN a.category = 'proposal' THEN 1 ELSE 0 END) as proposal_docs,
        SUM(CASE WHEN a.category = 'design_document' THEN 1 ELSE 0 END) as design_docs
    FROM email_content ec
    JOIN attachments a ON ec.email_id = a.email_id
    WHERE ec.linked_project_code IS NOT NULL
    GROUP BY ec.linked_project_code
) attach_stats ON p.project_code = attach_stats.linked_project_code

-- Status history summary
LEFT JOIN (
    SELECT
        psh.project_code,
        COUNT(*) as status_change_count,
        (SELECT psh2.new_status FROM proposal_status_history psh2
         WHERE psh2.project_code = psh.project_code
         ORDER BY psh2.status_date ASC LIMIT 1) as first_status,
        MAX(psh.status_date) as last_status_change_date
    FROM proposal_status_history psh
    GROUP BY psh.project_code
) status_history ON p.project_code = status_history.project_code

ORDER BY
    CASE WHEN COALESCE(email_stats.urgent_count, 0) > 0 THEN 0 ELSE 1 END,
    COALESCE(email_stats.action_required_count, 0) DESC,
    p.days_since_contact DESC;

-- Create index helper table for faster queries
DROP TABLE IF EXISTS proposal_intelligence_cache;
CREATE TABLE proposal_intelligence_cache (
    project_code TEXT PRIMARY KEY,
    email_count INTEGER,
    urgent_emails INTEGER,
    action_needed INTEGER,
    attention_status TEXT,
    engagement_level TEXT,
    last_updated DATETIME DEFAULT (datetime('now'))
);

-- Populate cache
INSERT INTO proposal_intelligence_cache (project_code, email_count, urgent_emails, action_needed, attention_status, engagement_level)
SELECT
    project_code,
    email_count,
    urgent_emails,
    emails_needing_action,
    attention_status,
    engagement_level
FROM proposal_intelligence;

-- Create useful indexes
CREATE INDEX IF NOT EXISTS idx_pic_attention ON proposal_intelligence_cache(attention_status);
CREATE INDEX IF NOT EXISTS idx_pic_urgent ON proposal_intelligence_cache(urgent_emails DESC);
