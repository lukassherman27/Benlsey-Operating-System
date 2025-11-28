-- Migration 011: Improved Email Categories
-- Based on critical audit feedback: current categories miss key proposal intelligence

-- Add new columns to email_content for enhanced categorization
ALTER TABLE email_content ADD COLUMN subcategory TEXT;
ALTER TABLE email_content ADD COLUMN urgency_level TEXT CHECK(urgency_level IN ('low', 'medium', 'high', 'critical'));
ALTER TABLE email_content ADD COLUMN client_sentiment TEXT CHECK(client_sentiment IN ('positive', 'neutral', 'negative', 'frustrated'));
ALTER TABLE email_content ADD COLUMN action_required INTEGER DEFAULT 0;
ALTER TABLE email_content ADD COLUMN follow_up_date DATE;

-- Create index on new fields
CREATE INDEX IF NOT EXISTS idx_email_content_subcategory ON email_content(subcategory);
CREATE INDEX IF NOT EXISTS idx_email_content_urgency ON email_content(urgency_level);
CREATE INDEX IF NOT EXISTS idx_email_content_action ON email_content(action_required);

-- NEW CATEGORY SYSTEM (keeping existing categories for backwards compatibility)
-- But adding subcategories for more granular intelligence
--
-- FOR PROPOSALS (pre-contract):
--   category: general
--   subcategory options:
--     - fee_discussion (client discussing budget/pricing/value)
--     - scope_discussion (what's included, deliverables)
--     - timeline_discussion (when work starts, project duration)
--     - client_decision (yes/no, go ahead, approval)
--     - competitor_mentioned (talking to other firms)
--     - follow_up_needed (ball in our court)
--     - objection (concerns, hesitation)
--     - introduction (first contact)
--     - update (general status update)
--
-- FOR ACTIVE PROJECTS:
--   category: design/rfi/schedule/etc (existing)
--   subcategory options:
--     - approval_needed
--     - revision_requested
--     - milestone_complete
--     - issue_raised
--     - clarification
--     - update
