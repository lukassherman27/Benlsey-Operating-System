-- Migration 012: Critical Query Performance Indexes
-- Based on agent feedback and common query patterns

-- Composite index for finding important emails by category
-- Query pattern: "Show me all important contract emails"
CREATE INDEX IF NOT EXISTS idx_email_content_category_importance
    ON email_content(category, importance_score DESC);

-- Composite index for finding emails needing follow-up
-- Query pattern: "Show me all emails with upcoming follow-ups"
CREATE INDEX IF NOT EXISTS idx_email_content_followup
    ON email_content(follow_up_date, action_required);

-- Composite index for proposal health queries
-- Query pattern: "Show me all proposals with low health scores"
CREATE INDEX IF NOT EXISTS idx_proposals_status_health
    ON proposals(status, health_score ASC);

-- Composite index for email-proposal relationship queries by confidence
-- Query pattern: "Find all emails for proposal X ordered by confidence"
CREATE INDEX IF NOT EXISTS idx_epl_proposal_confidence
    ON email_proposal_links(proposal_id, confidence_score DESC);

-- Index for document-proposal link type queries
-- Query pattern: "Show me all documents for this proposal by type"
CREATE INDEX IF NOT EXISTS idx_dpl_proposal_type
    ON document_proposal_links(proposal_id, link_type);

-- Index for urgent/action-required emails
-- Query pattern: "Show me all urgent emails requiring action"
CREATE INDEX IF NOT EXISTS idx_email_content_urgent_action
    ON email_content(urgency_level, action_required);

-- Index for emails with full body content
-- Query pattern: "Find all emails with full body text for analysis"
CREATE INDEX IF NOT EXISTS idx_emails_body_full
    ON emails(body_full) WHERE body_full IS NOT NULL;
