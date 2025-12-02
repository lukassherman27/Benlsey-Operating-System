-- ========================================
-- Migration 014: Comprehensive Audit System (Phase 2)
-- ========================================
-- Purpose: Add tables for comprehensive project auditing including:
--   - Project scope tracking (landscape/interiors/architecture)
--   - Fee breakdown by phase
--   - Phase timeline tracking
--   - Contract terms
--   - User feedback and continuous learning
--   - Audit rules engine
-- ========================================

-- Table 1: Project Scope
-- Tracks what disciplines are included in each project
CREATE TABLE IF NOT EXISTS project_scope (
    scope_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    discipline TEXT NOT NULL,  -- 'landscape', 'interiors', 'architecture'
    fee_usd REAL,
    percentage_of_total REAL,
    scope_description TEXT,
    confirmed_by_user INTEGER DEFAULT 0,
    confidence REAL,  -- AI confidence in this classification
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);

CREATE INDEX IF NOT EXISTS idx_project_scope_code ON project_scope(project_code);
CREATE INDEX IF NOT EXISTS idx_project_scope_discipline ON project_scope(discipline);
CREATE INDEX IF NOT EXISTS idx_project_scope_confirmed ON project_scope(confirmed_by_user);

-- Table 2: Project Fee Breakdown
-- Tracks fee allocation by project phase
CREATE TABLE IF NOT EXISTS project_fee_breakdown (
    breakdown_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    phase TEXT NOT NULL,  -- 'mobilization', 'concept', 'schematic', 'dd', 'cd', 'ca'
    phase_fee_usd REAL,
    percentage_of_total REAL,
    payment_status TEXT DEFAULT 'pending',  -- 'pending', 'invoiced', 'paid', 'waived'
    invoice_id TEXT,  -- Link to specific invoice if paid
    expected_payment_date DATE,
    actual_payment_date DATE,
    confirmed_by_user INTEGER DEFAULT 0,
    confidence REAL,  -- AI confidence in this breakdown
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);

CREATE INDEX IF NOT EXISTS idx_fee_breakdown_code ON project_fee_breakdown(project_code);
CREATE INDEX IF NOT EXISTS idx_fee_breakdown_phase ON project_fee_breakdown(phase);
CREATE INDEX IF NOT EXISTS idx_fee_breakdown_status ON project_fee_breakdown(payment_status);
CREATE INDEX IF NOT EXISTS idx_fee_breakdown_confirmed ON project_fee_breakdown(confirmed_by_user);

-- Table 3: Project Phase Timeline
-- Tracks timeline for each project phase
CREATE TABLE IF NOT EXISTS project_phase_timeline (
    timeline_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    phase TEXT NOT NULL,  -- 'mobilization', 'concept', 'schematic', 'dd', 'cd', 'ca'
    expected_duration_months REAL,  -- Can be fractional (e.g., 3.5 months)
    start_date DATE,
    expected_end_date DATE,
    actual_end_date DATE,
    presentation_date DATE,
    presentation_type TEXT,  -- 'client', 'internal', 'review', etc.
    status TEXT DEFAULT 'not_started',  -- 'not_started', 'in_progress', 'completed', 'delayed', 'on_hold'
    delay_days INTEGER,  -- Days behind schedule (if negative, ahead of schedule)
    notes TEXT,
    confirmed_by_user INTEGER DEFAULT 0,
    confidence REAL,  -- AI confidence in this timeline
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);

CREATE INDEX IF NOT EXISTS idx_timeline_code ON project_phase_timeline(project_code);
CREATE INDEX IF NOT EXISTS idx_timeline_phase ON project_phase_timeline(phase);
CREATE INDEX IF NOT EXISTS idx_timeline_status ON project_phase_timeline(status);
CREATE INDEX IF NOT EXISTS idx_timeline_dates ON project_phase_timeline(start_date, expected_end_date);

-- Table 4: Contract Terms
-- Stores contract metadata and terms
CREATE TABLE IF NOT EXISTS contract_terms (
    contract_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    contract_signed_date DATE,
    contract_start_date DATE,
    total_contract_term_months INTEGER,
    contract_end_date DATE,
    total_fee_usd REAL,
    payment_schedule TEXT,  -- JSON: detailed payment schedule
    contract_type TEXT,  -- 'fixed_fee', 'hourly', 'percentage', 'hybrid'
    retainer_amount_usd REAL,
    final_payment_amount_usd REAL,
    early_termination_terms TEXT,
    amendment_count INTEGER DEFAULT 0,
    original_contract_id TEXT,  -- If this is an amendment, link to original
    contract_document_path TEXT,  -- Path to PDF or scanned contract
    confirmed_by_user INTEGER DEFAULT 0,
    confidence REAL,  -- AI confidence in extracted data
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (project_code) REFERENCES projects(project_code),
    FOREIGN KEY (original_contract_id) REFERENCES contract_terms(contract_id)
);

CREATE INDEX IF NOT EXISTS idx_contract_code ON contract_terms(project_code);
CREATE INDEX IF NOT EXISTS idx_contract_dates ON contract_terms(contract_start_date, contract_end_date);
CREATE INDEX IF NOT EXISTS idx_contract_confirmed ON contract_terms(confirmed_by_user);

-- Table 5: User Context
-- Stores user feedback and corrections for continuous learning
CREATE TABLE IF NOT EXISTS user_context (
    context_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    question_type TEXT,  -- 'scope', 'fee_breakdown', 'timeline', 'classification', 'contract_terms'
    ai_suggestion TEXT,  -- What AI thought (JSON)
    user_correction TEXT,  -- What user said (JSON)
    context_provided TEXT,  -- User's explanation/reasoning
    confidence_before REAL,  -- AI confidence before correction
    confidence_after REAL,  -- Updated confidence after learning
    applied_to_project INTEGER DEFAULT 1,  -- Whether correction was applied
    pattern_extracted INTEGER DEFAULT 0,  -- Whether a reusable pattern was created
    times_pattern_reused INTEGER DEFAULT 0,  -- How many times this pattern has been applied
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'user',  -- Who provided the context
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);

CREATE INDEX IF NOT EXISTS idx_user_context_code ON user_context(project_code);
CREATE INDEX IF NOT EXISTS idx_user_context_type ON user_context(question_type);
CREATE INDEX IF NOT EXISTS idx_user_context_pattern ON user_context(pattern_extracted);
CREATE INDEX IF NOT EXISTS idx_user_context_date ON user_context(created_at);

-- Table 6: Audit Rules
-- Stores learned audit rules with accuracy tracking
CREATE TABLE IF NOT EXISTS audit_rules (
    rule_id TEXT PRIMARY KEY,
    rule_type TEXT NOT NULL,  -- 'scope_detection', 'fee_validation', 'timeline_validation', 'classification'
    rule_category TEXT,  -- 'financial', 'timeline', 'scope', 'status'
    rule_label TEXT NOT NULL,  -- Human-readable name
    rule_logic TEXT NOT NULL,  -- Description of the rule logic
    rule_pattern TEXT,  -- JSON: pattern matching criteria
    confidence_threshold REAL DEFAULT 0.75,  -- Minimum confidence to suggest
    auto_apply_threshold REAL DEFAULT 0.95,  -- Minimum confidence to auto-apply
    times_suggested INTEGER DEFAULT 0,  -- How many times rule has generated suggestions
    times_confirmed INTEGER DEFAULT 0,  -- How many times user approved
    times_rejected INTEGER DEFAULT 0,  -- How many times user rejected
    accuracy_rate REAL DEFAULT 0.0,  -- Calculated: confirmed / (confirmed + rejected)
    auto_apply_enabled INTEGER DEFAULT 0,  -- Whether to auto-apply this rule
    enabled INTEGER DEFAULT 1,  -- Whether rule is active
    priority INTEGER DEFAULT 5,  -- 1 (highest) to 10 (lowest)
    created_from_context_id TEXT,  -- If learned from user feedback
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    last_used_at DATETIME,
    FOREIGN KEY (created_from_context_id) REFERENCES user_context(context_id)
);

CREATE INDEX IF NOT EXISTS idx_audit_rules_type ON audit_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_audit_rules_enabled ON audit_rules(enabled);
CREATE INDEX IF NOT EXISTS idx_audit_rules_auto_apply ON audit_rules(auto_apply_enabled);
CREATE INDEX IF NOT EXISTS idx_audit_rules_accuracy ON audit_rules(accuracy_rate);

-- Migration tracking
INSERT INTO schema_migrations (version, name, description, applied_at)
VALUES (14, '014_comprehensive_audit_system', 'Comprehensive Audit System - Scope, Fee Breakdown, Timeline, Contract Terms, Learning', CURRENT_TIMESTAMP);
