-- Migration 007: Operations Command Center Tables
-- Creates complete database foundation for project operations dashboard
-- Date: 2025-01-15

-- ============================================================================
-- 1. PROJECT MILESTONES
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_milestones (
    milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    milestone_type TEXT NOT NULL,  -- 'presentation', 'concept_delivery', 'schematic', 'detail_design', 'final_delivery', 'contract_signing'
    milestone_name TEXT NOT NULL,
    description TEXT,
    expected_date DATE NOT NULL,
    actual_date DATE,
    status TEXT DEFAULT 'pending',  -- 'pending', 'on_track', 'delayed', 'completed', 'cancelled'
    delay_reason TEXT,  -- 'waiting_on_client', 'need_internal_work', 'budget_pending', 'scope_change', 'resource_constraints'
    delay_days INTEGER DEFAULT 0,
    responsible_party TEXT,  -- 'bensley', 'client', 'third_party'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_milestones_proposal ON project_milestones(proposal_id);
CREATE INDEX IF NOT EXISTS idx_milestones_status ON project_milestones(status);
CREATE INDEX IF NOT EXISTS idx_milestones_expected_date ON project_milestones(expected_date);

-- ============================================================================
-- 2. PROJECT RFIs (REQUESTS FOR INFORMATION)
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_rfis (
    rfi_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    email_id INTEGER,  -- Link to email that contains RFI
    rfi_number TEXT UNIQUE,  -- e.g., "BK033-RFI-001"
    question TEXT NOT NULL,
    asked_by TEXT,  -- 'bensley', 'client', 'consultant'
    asked_date DATE NOT NULL,
    response TEXT,
    responded_by TEXT,
    responded_date DATE,
    status TEXT DEFAULT 'unanswered',  -- 'unanswered', 'answered', 'pending_followup', 'closed'
    priority TEXT DEFAULT 'normal',  -- 'low', 'normal', 'high', 'critical'
    category TEXT,  -- 'technical', 'design', 'budget', 'timeline', 'scope', 'regulatory'
    days_waiting INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    FOREIGN KEY (email_id) REFERENCES emails(email_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_rfis_proposal ON project_rfis(proposal_id);
CREATE INDEX IF NOT EXISTS idx_rfis_status ON project_rfis(status);
CREATE INDEX IF NOT EXISTS idx_rfis_priority ON project_rfis(priority);

-- ============================================================================
-- 3. PROJECT FINANCIALS
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_financials (
    financial_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    payment_type TEXT NOT NULL,  -- 'initial', 'milestone', 'final', 'expense', 'retainer'
    milestone_id INTEGER,  -- Link to specific milestone
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    percentage_of_total REAL,  -- e.g., 20.0 for 20%
    due_date DATE,
    invoice_number TEXT,
    invoice_sent_date DATE,
    payment_received_date DATE,
    payment_method TEXT,  -- 'wire', 'check', 'ach', 'credit_card'
    status TEXT DEFAULT 'pending',  -- 'pending', 'invoiced', 'paid', 'overdue', 'cancelled'
    days_outstanding INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    FOREIGN KEY (milestone_id) REFERENCES project_milestones(milestone_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_financials_proposal ON project_financials(proposal_id);
CREATE INDEX IF NOT EXISTS idx_financials_status ON project_financials(status);
CREATE INDEX IF NOT EXISTS idx_financials_due_date ON project_financials(due_date);

-- ============================================================================
-- 4. PROJECT FILES METADATA
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- 'drawing', 'presentation', 'contract', 'render', 'document', 'spreadsheet', 'image'
    file_category TEXT,  -- 'concept', 'schematic', 'detail', 'final', 'reference', 'submission'
    file_path TEXT,  -- Relative path in file system
    onedrive_path TEXT,  -- Path in OneDrive
    onedrive_url TEXT,  -- Shareable link
    file_size INTEGER,  -- Bytes
    version TEXT,  -- v1.0, v2.1, etc.
    uploaded_date DATE,
    uploaded_by TEXT,
    description TEXT,
    tags TEXT,  -- JSON array of tags: ["urgent", "client-ready", "draft"]
    is_latest_version BOOLEAN DEFAULT 1,
    related_milestone_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    FOREIGN KEY (related_milestone_id) REFERENCES project_milestones(milestone_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_files_proposal ON project_files(proposal_id);
CREATE INDEX IF NOT EXISTS idx_files_type ON project_files(file_type);
CREATE INDEX IF NOT EXISTS idx_files_latest ON project_files(is_latest_version);

-- ============================================================================
-- 5. PROJECT CONTEXT & TASKS
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_context (
    context_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    context_type TEXT NOT NULL,  -- 'note', 'task', 'reminder', 'decision', 'risk', 'issue'
    context_text TEXT NOT NULL,
    priority TEXT DEFAULT 'normal',  -- 'low', 'normal', 'high', 'urgent'
    status TEXT DEFAULT 'active',  -- 'active', 'completed', 'cancelled', 'on_hold'
    due_date DATE,
    assigned_to TEXT,  -- 'bill', 'brian', 'team', 'lukas', 'client'
    created_by TEXT DEFAULT 'lukas',
    related_email_id INTEGER,
    related_milestone_id INTEGER,
    agent_action_taken TEXT,  -- What agent did: 'email_sent', 'meeting_scheduled', 'timeline_updated', 'reminder_created'
    agent_action_result TEXT,  -- Result of agent action (JSON)
    agent_action_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    FOREIGN KEY (related_email_id) REFERENCES emails(email_id) ON DELETE SET NULL,
    FOREIGN KEY (related_milestone_id) REFERENCES project_milestones(milestone_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_context_proposal ON project_context(proposal_id);
CREATE INDEX IF NOT EXISTS idx_context_type ON project_context(context_type);
CREATE INDEX IF NOT EXISTS idx_context_status ON project_context(status);
CREATE INDEX IF NOT EXISTS idx_context_assigned ON project_context(assigned_to);

-- ============================================================================
-- 6. PROJECT MEETINGS
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_meetings (
    meeting_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    meeting_type TEXT NOT NULL,  -- 'kickoff', 'design_review', 'client_presentation', 'internal', 'site_visit', 'workshop'
    meeting_title TEXT NOT NULL,
    scheduled_date DATETIME NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    location TEXT,  -- 'zoom', 'office', 'client_office', 'site', 'google_meet'
    meeting_url TEXT,  -- Zoom/Teams/Meet link
    attendees TEXT,  -- JSON array of attendees: [{"name": "Bill", "email": "bill@...", "role": "lead"}]
    agenda TEXT,
    meeting_notes TEXT,
    action_items TEXT,  -- JSON array of action items
    status TEXT DEFAULT 'scheduled',  -- 'scheduled', 'completed', 'cancelled', 'rescheduled', 'no_show'
    calendar_event_id TEXT,  -- Google Calendar/Outlook ID
    reminder_sent BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_meetings_proposal ON project_meetings(proposal_id);
CREATE INDEX IF NOT EXISTS idx_meetings_date ON project_meetings(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_meetings_status ON project_meetings(status);

-- ============================================================================
-- 7. PROJECT OUTREACH TRACKING
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_outreach (
    outreach_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    contact_date DATE NOT NULL,
    contact_type TEXT NOT NULL,  -- 'email', 'phone_call', 'video_call', 'meeting', 'site_visit', 'text_message'
    contact_person TEXT,
    contact_person_role TEXT,  -- 'client', 'consultant', 'contractor', 'authority'
    contact_method TEXT,  -- 'sent_email', 'received_email', 'phone_call_made', 'phone_call_received', 'video_call'
    subject TEXT,
    summary TEXT,
    outcome TEXT,  -- 'positive', 'neutral', 'needs_followup', 'negative'
    next_action TEXT,
    next_action_date DATE,
    related_email_id INTEGER,
    related_meeting_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    FOREIGN KEY (related_email_id) REFERENCES emails(email_id) ON DELETE SET NULL,
    FOREIGN KEY (related_meeting_id) REFERENCES project_meetings(meeting_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_outreach_proposal ON project_outreach(proposal_id);
CREATE INDEX IF NOT EXISTS idx_outreach_date ON project_outreach(contact_date);
CREATE INDEX IF NOT EXISTS idx_outreach_next_action_date ON project_outreach(next_action_date);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Milestones
CREATE TRIGGER IF NOT EXISTS update_milestone_timestamp
AFTER UPDATE ON project_milestones
BEGIN
    UPDATE project_milestones SET updated_at = CURRENT_TIMESTAMP
    WHERE milestone_id = NEW.milestone_id;
END;

-- RFIs
CREATE TRIGGER IF NOT EXISTS update_rfi_timestamp
AFTER UPDATE ON project_rfis
BEGIN
    UPDATE project_rfis SET updated_at = CURRENT_TIMESTAMP
    WHERE rfi_id = NEW.rfi_id;
END;

-- Financials
CREATE TRIGGER IF NOT EXISTS update_financial_timestamp
AFTER UPDATE ON project_financials
BEGIN
    UPDATE project_financials SET updated_at = CURRENT_TIMESTAMP
    WHERE financial_id = NEW.financial_id;
END;

-- Files
CREATE TRIGGER IF NOT EXISTS update_file_timestamp
AFTER UPDATE ON project_files
BEGIN
    UPDATE project_files SET updated_at = CURRENT_TIMESTAMP
    WHERE file_id = NEW.file_id;
END;

-- Context
CREATE TRIGGER IF NOT EXISTS update_context_timestamp
AFTER UPDATE ON project_context
BEGIN
    UPDATE project_context SET updated_at = CURRENT_TIMESTAMP
    WHERE context_id = NEW.context_id;
END;

-- Meetings
CREATE TRIGGER IF NOT EXISTS update_meeting_timestamp
AFTER UPDATE ON project_meetings
BEGIN
    UPDATE project_meetings SET updated_at = CURRENT_TIMESTAMP
    WHERE meeting_id = NEW.meeting_id;
END;

-- Outreach
CREATE TRIGGER IF NOT EXISTS update_outreach_timestamp
AFTER UPDATE ON project_outreach
BEGIN
    UPDATE project_outreach SET updated_at = CURRENT_TIMESTAMP
    WHERE outreach_id = NEW.outreach_id;
END;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Version: 007
-- Description: Operations Command Center foundation tables
-- Tables created: 7
-- Indexes created: 21
-- Triggers created: 7
