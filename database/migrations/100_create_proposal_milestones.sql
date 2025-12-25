-- Migration 100: Create proposal_milestones table
-- Issue #140: Activity Tracking Database - Foundation for Business Intelligence
--
-- This table stores key milestones in the proposal journey.
-- Used for timeline visualization and analytics.

CREATE TABLE IF NOT EXISTS proposal_milestones (
    milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL REFERENCES proposals(proposal_id),

    -- Milestone details
    milestone_type TEXT NOT NULL,  -- See types below
    milestone_date DATE NOT NULL,
    description TEXT,

    -- Link to the activity that created this milestone
    source_activity_id INTEGER REFERENCES proposal_activities(activity_id),

    -- Value at this point (for tracking changes)
    proposal_value_at_milestone REAL,
    status_at_milestone TEXT,

    -- Metadata
    created_by TEXT,              -- 'system', 'bill', 'lukas', etc.
    notes TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Milestone types:
-- 'first_contact'      - Initial contact with client
-- 'meeting_scheduled'  - First meeting scheduled
-- 'meeting_held'       - Meeting occurred
-- 'proposal_requested' - Client requested proposal
-- 'proposal_sent'      - We sent the proposal
-- 'proposal_revised'   - Revised proposal sent
-- 'negotiation_started'- Entered negotiation phase
-- 'terms_agreed'       - Terms agreed upon
-- 'contract_sent'      - Contract sent for signature
-- 'contract_signed'    - Deal won!
-- 'lost'               - Deal lost
-- 'declined'           - We declined
-- 'on_hold'            - Put on hold
-- 'reactivated'        - Came back from hold
-- 'scope_change'       - Significant scope change
-- 'key_decision'       - Important decision made

CREATE INDEX IF NOT EXISTS idx_milestones_proposal ON proposal_milestones(proposal_id);
CREATE INDEX IF NOT EXISTS idx_milestones_type ON proposal_milestones(milestone_type);
CREATE INDEX IF NOT EXISTS idx_milestones_date ON proposal_milestones(milestone_date);


-- Also create a view for easy proposal timeline queries
CREATE VIEW IF NOT EXISTS v_proposal_timeline AS
SELECT
    p.proposal_id,
    p.project_code,
    p.project_name,
    pa.activity_id,
    pa.activity_type,
    pa.activity_date,
    pa.title,
    pa.summary,
    pa.actor,
    pa.sentiment,
    pa.is_significant,
    pm.milestone_id,
    pm.milestone_type
FROM proposals p
LEFT JOIN proposal_activities pa ON p.proposal_id = pa.proposal_id
LEFT JOIN proposal_milestones pm ON pa.activity_id = pm.source_activity_id
ORDER BY p.proposal_id, pa.activity_date DESC;
