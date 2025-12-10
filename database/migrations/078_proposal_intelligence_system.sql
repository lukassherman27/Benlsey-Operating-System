-- Migration 078: Proposal Intelligence System
-- Purpose: Add comprehensive proposal tracking for events, follow-ups, documents, and decision intelligence
-- Date: 2024-12-10

-- ============================================================================
-- 1. PROPOSAL EVENTS (meetings, calls, deadlines, site visits, presentations)
-- ============================================================================
CREATE TABLE IF NOT EXISTS proposal_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER,
    project_code TEXT NOT NULL,

    event_type TEXT NOT NULL CHECK(event_type IN (
        'meeting', 'call', 'deadline', 'site_visit', 'presentation',
        'decision_date', 'kickoff', 'review', 'workshop', 'other'
    )),
    event_date DATE NOT NULL,
    event_time TEXT,  -- '10:00 AM Bangkok'

    title TEXT NOT NULL,
    description TEXT,
    location TEXT,  -- 'Zoom', 'Bangkok office', 'Site'

    attendees TEXT,  -- JSON array of names
    is_confirmed INTEGER DEFAULT 1,

    -- For recurring/follow-up
    creates_follow_up INTEGER DEFAULT 0,
    follow_up_days INTEGER,  -- Days after to follow up

    completed INTEGER DEFAULT 0,
    outcome TEXT,
    next_steps TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    updated_at DATETIME,

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

CREATE INDEX idx_proposal_events_project ON proposal_events(project_code);
CREATE INDEX idx_proposal_events_date ON proposal_events(event_date);
CREATE INDEX idx_proposal_events_type ON proposal_events(event_type);
CREATE INDEX idx_proposal_events_pending ON proposal_events(completed, event_date);

-- ============================================================================
-- 2. FOLLOW-UP TRACKING
-- ============================================================================
CREATE TABLE IF NOT EXISTS proposal_follow_ups (
    follow_up_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER,
    project_code TEXT NOT NULL,

    follow_up_number INTEGER,  -- 1st, 2nd, 3rd follow-up
    sent_date DATE NOT NULL,
    sent_via TEXT CHECK(sent_via IN ('email', 'whatsapp', 'call', 'in_person', 'other')),
    sent_by TEXT,  -- 'lukas', 'bill', 'brian'

    message_summary TEXT,  -- What we said

    response_received INTEGER DEFAULT 0,
    response_date DATE,
    response_summary TEXT,  -- What they said
    response_sentiment TEXT CHECK(response_sentiment IN ('positive', 'neutral', 'negative', 'delayed', NULL)),

    next_follow_up_date DATE,
    notes TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

CREATE INDEX idx_proposal_followups_project ON proposal_follow_ups(project_code);
CREATE INDEX idx_proposal_followups_date ON proposal_follow_ups(sent_date);
CREATE INDEX idx_proposal_followups_pending ON proposal_follow_ups(response_received, next_follow_up_date);

-- ============================================================================
-- 3. SILENCE CONTEXT (why we're not worried about no response)
-- ============================================================================
CREATE TABLE IF NOT EXISTS proposal_silence_reasons (
    silence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER,
    project_code TEXT NOT NULL,

    reason_type TEXT NOT NULL CHECK(reason_type IN (
        'scheduled_meeting', 'waiting_on_client_process', 'holiday',
        'budget_cycle', 'government', 'internal_review', 'client_requested',
        'seasonal', 'ghosted', 'other'
    )),

    reason_detail TEXT,  -- 'Meeting scheduled Jan 15', 'Waiting on government approval by Dec 7'
    valid_until DATE,  -- Don't flag as stale until after this date

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',

    resolved INTEGER DEFAULT 0,
    resolved_date DATE,
    resolution_notes TEXT,

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

CREATE INDEX idx_proposal_silence_project ON proposal_silence_reasons(project_code);
CREATE INDEX idx_proposal_silence_active ON proposal_silence_reasons(resolved, valid_until);

-- ============================================================================
-- 4. PROPOSAL DOCUMENTS SENT
-- ============================================================================
CREATE TABLE IF NOT EXISTS proposal_documents (
    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER,
    project_code TEXT NOT NULL,

    doc_type TEXT NOT NULL CHECK(doc_type IN (
        'proposal', 'contract', 'portfolio', 'nda', 'addendum',
        'revised_proposal', 'fee_letter', 'scope', 'presentation', 'other'
    )),
    version INTEGER DEFAULT 1,

    sent_date DATE NOT NULL,
    sent_to TEXT,  -- Email addresses or names
    sent_via TEXT CHECK(sent_via IN ('email', 'wetransfer', 'google_drive', 'dropbox', 'physical', 'motorcycle', 'other')),
    sent_by TEXT,

    file_path TEXT,
    external_link TEXT,  -- WeTransfer, Google Drive link
    link_expires DATE,

    delivery_confirmed INTEGER DEFAULT 0,
    delivery_failed INTEGER DEFAULT 0,
    failure_reason TEXT,

    fee_amount REAL,
    fee_currency TEXT DEFAULT 'USD',

    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

CREATE INDEX idx_proposal_docs_project ON proposal_documents(project_code);
CREATE INDEX idx_proposal_docs_type ON proposal_documents(doc_type);
CREATE INDEX idx_proposal_docs_sent ON proposal_documents(sent_date);

-- ============================================================================
-- 5. CLIENT DECISION TIMELINE
-- ============================================================================
CREATE TABLE IF NOT EXISTS proposal_decision_info (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER,
    project_code TEXT NOT NULL UNIQUE,  -- One per proposal

    expected_decision_date DATE,
    budget_approval_date DATE,
    board_meeting_date DATE,

    decision_maker TEXT,  -- Who makes final call
    influencers TEXT,  -- JSON array of people who influence

    competing_firms TEXT,  -- JSON array if known
    our_position TEXT CHECK(our_position IN ('front_runner', 'shortlisted', 'long_shot', 'unknown', NULL)),

    budget_range_low REAL,
    budget_range_high REAL,
    budget_currency TEXT DEFAULT 'USD',
    budget_confirmed INTEGER DEFAULT 0,

    blockers TEXT,  -- What's preventing decision

    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

CREATE INDEX idx_proposal_decision_project ON proposal_decision_info(project_code);
CREATE INDEX idx_proposal_decision_date ON proposal_decision_info(expected_decision_date);

-- ============================================================================
-- 6. PROPOSAL CONTACTS (multiple stakeholders per project)
-- ============================================================================
CREATE TABLE IF NOT EXISTS proposal_stakeholders (
    stakeholder_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER,
    project_code TEXT NOT NULL,
    contact_id INTEGER,  -- Link to contacts table if exists

    name TEXT NOT NULL,
    role TEXT CHECK(role IN (
        'decision_maker', 'influencer', 'coordinator',
        'technical', 'finance', 'end_user', 'champion', 'other'
    )),
    company TEXT,
    email TEXT,
    phone TEXT,
    whatsapp TEXT,

    is_primary INTEGER DEFAULT 0,
    relationship_strength TEXT CHECK(relationship_strength IN ('strong', 'medium', 'weak', 'new', NULL)),

    communication_preference TEXT CHECK(communication_preference IN ('email', 'whatsapp', 'call', 'in_person', NULL)),
    timezone TEXT,

    notes TEXT,
    last_contact_date DATE,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
);

CREATE INDEX idx_proposal_stakeholders_project ON proposal_stakeholders(project_code);
CREATE INDEX idx_proposal_stakeholders_role ON proposal_stakeholders(role);
CREATE INDEX idx_proposal_stakeholders_primary ON proposal_stakeholders(is_primary);

-- ============================================================================
-- SMART VIEWS FOR DAILY INTELLIGENCE
-- ============================================================================

-- Priority Dashboard View
CREATE VIEW IF NOT EXISTS v_proposal_priorities AS
SELECT
    p.proposal_id,
    p.project_code,
    p.project_name,
    p.current_status as status,
    p.project_value,
    p.contact_person,

    -- Days since last contact
    CAST(julianday('now') - julianday(COALESCE(p.last_contact_date, p.created_at)) AS INTEGER) as days_silent,

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

    -- Priority calculation
    CASE
        WHEN sr.valid_until > date('now') THEN 'OK - ' || sr.reason_type
        WHEN p.current_status = 'Negotiation' AND days_silent > 14 THEN 'URGENT'
        WHEN p.current_status = 'Proposal Sent' AND days_silent > 21 THEN 'FOLLOW UP'
        WHEN p.current_status = 'First Contact' AND days_silent > 7 THEN 'RESPOND'
        WHEN p.current_status = 'Drafting' AND days_silent > 14 THEN 'CHECK IN'
        ELSE 'MONITOR'
    END as priority_status

FROM proposals p
LEFT JOIN proposal_silence_reasons sr
    ON p.project_code = sr.project_code AND sr.resolved = 0
LEFT JOIN proposal_decision_info di
    ON p.project_code = di.project_code
WHERE p.current_status NOT IN ('Lost', 'Declined', 'Contract Signed', 'Dormant', 'Archived')
ORDER BY
    CASE
        WHEN priority_status LIKE 'URGENT%' THEN 1
        WHEN priority_status LIKE 'FOLLOW UP%' THEN 2
        WHEN priority_status LIKE 'RESPOND%' THEN 3
        WHEN priority_status LIKE 'CHECK IN%' THEN 4
        ELSE 5
    END,
    days_silent DESC;

-- Upcoming Events View
CREATE VIEW IF NOT EXISTS v_upcoming_proposal_events AS
SELECT
    pe.*,
    p.project_name,
    p.contact_person,
    p.current_status,
    julianday(pe.event_date) - julianday('now') as days_until
FROM proposal_events pe
JOIN proposals p ON pe.project_code = p.project_code
WHERE pe.completed = 0
  AND pe.event_date >= date('now')
ORDER BY pe.event_date ASC;

-- Document Status View
CREATE VIEW IF NOT EXISTS v_proposal_document_status AS
SELECT
    p.project_code,
    p.project_name,
    pd.doc_type,
    pd.version,
    pd.sent_date,
    pd.sent_to,
    pd.delivery_confirmed,
    pd.fee_amount,
    julianday('now') - julianday(pd.sent_date) as days_since_sent
FROM proposals p
LEFT JOIN proposal_documents pd ON p.project_code = pd.project_code
WHERE p.current_status NOT IN ('Lost', 'Declined', 'Contract Signed', 'Dormant')
ORDER BY pd.sent_date DESC;
