-- Migration 087: Foundation Fixes
-- Date: 2025-12-21
-- Fixes issues #35 (broken views) and #36 (missing tables)
-- This migration was applied directly - this file documents what was done.

-- ============================================================================
-- 1. MISSING TABLES CREATED
-- ============================================================================

-- team_members (for schedule management)
CREATE TABLE IF NOT EXISTS team_members (
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    nickname TEXT,
    office TEXT CHECK(office IN ('Bali', 'Bangkok', 'Thailand')) NOT NULL,
    discipline TEXT CHECK(discipline IN ('Architecture', 'Interior', 'Landscape', 'Artwork', 'Management')) NOT NULL,
    is_active INTEGER DEFAULT 1,
    is_team_lead INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- weekly_schedules (for schedule tracking)
CREATE TABLE IF NOT EXISTS weekly_schedules (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    office TEXT CHECK(office IN ('Bali', 'Bangkok')) NOT NULL,
    week_start_date TEXT NOT NULL,
    week_end_date TEXT NOT NULL,
    source_email_id INTEGER,
    created_by TEXT,
    override_by TEXT,
    status TEXT CHECK(status IN ('draft', 'published', 'archived')) DEFAULT 'published',
    pdf_generated INTEGER DEFAULT 0,
    pdf_path TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (source_email_id) REFERENCES emails(email_id),
    UNIQUE(office, week_start_date)
);

-- project_colors (for PDF generation)
CREATE TABLE IF NOT EXISTS project_colors (
    color_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT UNIQUE NOT NULL,
    color_hex TEXT NOT NULL,
    color_name TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- schedule_processing_log
CREATE TABLE IF NOT EXISTS schedule_processing_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER,
    office TEXT,
    week_start_date TEXT,
    status TEXT CHECK(status IN ('success', 'failed', 'partial')),
    entries_created INTEGER DEFAULT 0,
    error_message TEXT,
    processed_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (email_id) REFERENCES emails(email_id)
);

-- contract_terms (for contract tracking)
CREATE TABLE IF NOT EXISTS contract_terms (
    contract_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    contract_signed_date DATE,
    contract_start_date DATE,
    total_contract_term_months INTEGER,
    contract_end_date DATE,
    total_fee_usd REAL,
    payment_schedule TEXT,
    contract_type TEXT,
    retainer_amount_usd REAL,
    final_payment_amount_usd REAL,
    early_termination_terms TEXT,
    amendment_count INTEGER DEFAULT 0,
    original_contract_id TEXT,
    contract_document_path TEXT,
    confirmed_by_user INTEGER DEFAULT 0,
    confidence REAL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);

-- user_context (for learning feedback)
CREATE TABLE IF NOT EXISTS user_context (
    context_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    question_type TEXT,
    ai_suggestion TEXT,
    user_correction TEXT,
    context_provided TEXT,
    confidence_before REAL,
    confidence_after REAL,
    applied_to_project INTEGER DEFAULT 1,
    pattern_extracted INTEGER DEFAULT 0,
    times_pattern_reused INTEGER DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'user',
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);

-- audit_rules (for business rules)
CREATE TABLE IF NOT EXISTS audit_rules (
    rule_id TEXT PRIMARY KEY,
    rule_type TEXT NOT NULL,
    rule_category TEXT,
    rule_label TEXT NOT NULL,
    rule_logic TEXT NOT NULL,
    rule_pattern TEXT,
    confidence_threshold REAL DEFAULT 0.75,
    auto_apply_threshold REAL DEFAULT 0.95,
    times_suggested INTEGER DEFAULT 0,
    times_confirmed INTEGER DEFAULT 0,
    times_rejected INTEGER DEFAULT 0,
    accuracy_rate REAL DEFAULT 0.0,
    auto_apply_enabled INTEGER DEFAULT 0,
    enabled INTEGER DEFAULT 1,
    priority INTEGER DEFAULT 5,
    created_from_context_id TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    last_used_at DATETIME,
    FOREIGN KEY (created_from_context_id) REFERENCES user_context(context_id)
);

-- project_scope (for scope tracking)
CREATE TABLE IF NOT EXISTS project_scope (
    scope_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    discipline TEXT NOT NULL,
    fee_usd REAL,
    percentage_of_total REAL,
    scope_description TEXT,
    confirmed_by_user INTEGER DEFAULT 0,
    confidence REAL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);

-- project_phase_timeline
CREATE TABLE IF NOT EXISTS project_phase_timeline (
    timeline_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    phase TEXT NOT NULL,
    expected_duration_months REAL,
    start_date DATE,
    expected_end_date DATE,
    actual_end_date DATE,
    presentation_date DATE,
    presentation_type TEXT,
    status TEXT DEFAULT 'not_started',
    delay_days INTEGER,
    notes TEXT,
    confirmed_by_user INTEGER DEFAULT 0,
    confidence REAL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);

-- ai_suggestions_queue
CREATE TABLE IF NOT EXISTS ai_suggestions_queue (
    id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    suggestion_type TEXT NOT NULL,
    proposed_fix TEXT NOT NULL,
    evidence TEXT NOT NULL,
    confidence REAL NOT NULL,
    impact_type TEXT,
    impact_value_usd REAL,
    impact_summary TEXT,
    severity TEXT NOT NULL,
    bucket TEXT NOT NULL,
    pattern_id TEXT,
    pattern_label TEXT,
    auto_apply_candidate INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    snooze_until DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- suggestion_patterns
CREATE TABLE IF NOT EXISTS suggestion_patterns (
    pattern_id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    detection_logic TEXT NOT NULL,
    confidence_threshold REAL DEFAULT 0.7,
    auto_apply_enabled INTEGER DEFAULT 0,
    approval_count INTEGER DEFAULT 0,
    rejection_count INTEGER DEFAULT 0,
    total_suggestions INTEGER DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- suggestion_decisions
CREATE TABLE IF NOT EXISTS suggestion_decisions (
    decision_id TEXT PRIMARY KEY,
    suggestion_id TEXT NOT NULL,
    project_code TEXT NOT NULL,
    suggestion_type TEXT NOT NULL,
    proposed_payload TEXT NOT NULL,
    evidence_snapshot TEXT NOT NULL,
    confidence REAL NOT NULL,
    decision TEXT NOT NULL,
    decision_by TEXT,
    decision_reason TEXT,
    applied INTEGER DEFAULT 0,
    decided_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (suggestion_id) REFERENCES ai_suggestions_queue(id) ON DELETE CASCADE
);

-- project_contact_links
CREATE TABLE IF NOT EXISTS project_contact_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code TEXT,
    contact_id INTEGER NOT NULL,
    role TEXT,
    email_count INTEGER DEFAULT 0,
    confidence_score REAL DEFAULT 0.5,
    first_linked TEXT DEFAULT (datetime('now')),
    last_activity TEXT DEFAULT (datetime('now')),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
);

-- document_proposal_links
CREATE TABLE IF NOT EXISTS document_proposal_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    proposal_id INTEGER NOT NULL,
    link_type TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    UNIQUE(document_id, proposal_id)
);

-- document_versions
CREATE TABLE IF NOT EXISTS document_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    previous_version_id INTEGER,
    version_number TEXT,
    changes_summary TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

-- project_outreach
CREATE TABLE IF NOT EXISTS project_outreach (
    outreach_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    contact_date DATE NOT NULL,
    contact_type TEXT NOT NULL,
    contact_person TEXT,
    contact_person_role TEXT,
    contact_method TEXT,
    subject TEXT,
    summary TEXT,
    outcome TEXT,
    next_action TEXT,
    next_action_date DATE,
    related_email_id INTEGER,
    related_meeting_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE CASCADE
);

-- project_contacts (contact registry)
CREATE TABLE IF NOT EXISTS project_contacts (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_address TEXT UNIQUE NOT NULL,
    full_name TEXT,
    company TEXT,
    phone TEXT,
    is_internal INTEGER DEFAULT 0,
    first_seen TEXT,
    last_contact TEXT,
    total_emails INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ============================================================================
-- 2. VIEWS FIXED
-- ============================================================================

-- Dropped views that reference unimplemented features:
-- proposal_health, recent_activity, v_contact_project_summary,
-- v_contract_history, v_current_contracts, v_current_project_pms,
-- v_pm_workload, v_rfi_summary

-- Fixed views with wrong column/table references:
-- v_pattern_effectiveness, v_patterns_by_project (learned_patterns -> email_learned_patterns)
-- v_deliverables_dashboard (project_name -> project_title, title -> name)
-- v_project_contacts (pcl.source removed)
-- v_recipient_proposal_map (proposal_id -> project_code)
-- contact_projects_view, project_contacts_view (proposal_id -> project_code)

-- ============================================================================
-- 3. INDEXES CREATED
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_team_members_office ON team_members(office);
CREATE INDEX IF NOT EXISTS idx_team_members_discipline ON team_members(discipline);
CREATE INDEX IF NOT EXISTS idx_weekly_schedules_dates ON weekly_schedules(week_start_date, week_end_date);
CREATE INDEX IF NOT EXISTS idx_project_scope_code ON project_scope(project_code);
CREATE INDEX IF NOT EXISTS idx_contract_code ON contract_terms(project_code);
CREATE INDEX IF NOT EXISTS idx_user_context_code ON user_context(project_code);
CREATE INDEX IF NOT EXISTS idx_audit_rules_type ON audit_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_suggestions_status ON ai_suggestions_queue(status);
CREATE INDEX IF NOT EXISTS idx_contact_links_project ON project_contact_links(project_code);
CREATE INDEX IF NOT EXISTS idx_doc_proposal_links ON document_proposal_links(proposal_id);
CREATE INDEX IF NOT EXISTS idx_outreach_proposal ON project_outreach(proposal_id);
CREATE INDEX IF NOT EXISTS idx_project_contacts_email ON project_contacts(email_address);

-- ============================================================================
-- 4. SEED DATA
-- ============================================================================

INSERT OR IGNORE INTO team_members (email, full_name, nickname, office, discipline, is_team_lead) VALUES
    ('bensley.bali@bensley.co.id', 'Astuti', 'Astuti', 'Bali', 'Management', 1),
    ('aood@bensley.com', 'Pakheenai Saenharn', 'Aood', 'Bangkok', 'Interior', 1),
    ('moo@bensley.com', 'Natthawat Thatpakorn', 'Moo', 'Bangkok', 'Landscape', 1),
    ('bill@bensley.com', 'Bill Bensley', 'Bill', 'Bangkok', 'Management', 1),
    ('bsherman@bensley.com', 'Brian Kent Sherman', 'Brian', 'Bangkok', 'Management', 1);
