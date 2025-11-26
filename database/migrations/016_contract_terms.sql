-- Migration 016: Contract Terms & Conditions
-- Created: 2025-11-23
-- Description: Track contract terms, special conditions, payment terms, and legal clauses
--              Enables contract compliance monitoring and risk management

-- ============================================================================
-- Contract Details
-- Stores core contract information and terms
-- ============================================================================
CREATE TABLE IF NOT EXISTS contract_details (
    contract_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id              INTEGER NOT NULL,
    contract_number         TEXT,                               -- Official contract reference number
    contract_type           TEXT,                               -- 'Lump Sum', 'Time & Materials', 'Percentage of Construction Cost', 'Monthly Retainer', 'Hybrid'
    contract_date           DATE,                               -- Date contract was signed
    effective_date          DATE,                               -- When contract becomes effective
    expiry_date             DATE,                               -- Contract expiration
    auto_renewal            INTEGER DEFAULT 0,                  -- Does contract auto-renew?
    renewal_notice_days     INTEGER,                            -- Days notice required to cancel before renewal
    contract_value_usd      REAL,                               -- Total contract value
    contract_currency       TEXT DEFAULT 'USD',
    payment_currency        TEXT DEFAULT 'USD',
    exchange_rate           REAL,                               -- If currencies differ
    governing_law           TEXT,                               -- 'Thailand', 'Singapore', 'UAE', etc.
    dispute_resolution      TEXT,                               -- 'Arbitration', 'Litigation', 'Mediation'
    arbitration_location    TEXT,                               -- Location for arbitration if applicable
    liability_cap_usd       REAL,                               -- Professional liability cap
    insurance_required      INTEGER DEFAULT 0,                  -- Is PI insurance required?
    insurance_amount_usd    REAL,                               -- Required insurance coverage
    contract_status         TEXT DEFAULT 'draft',               -- 'draft', 'pending_signature', 'active', 'completed', 'terminated', 'expired'
    signed_by_bensley       DATE,                               -- When Bensley signed
    signed_by_client        DATE,                               -- When client signed
    contract_file_path      TEXT,                               -- Path to signed contract PDF
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    UNIQUE(project_id, contract_number)
);

-- ============================================================================
-- Contract Clauses
-- Track important contract clauses and special conditions
-- ============================================================================
CREATE TABLE IF NOT EXISTS contract_clauses (
    clause_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id             INTEGER NOT NULL,
    clause_type             TEXT NOT NULL,                      -- 'payment_terms', 'scope_limitation', 'warranty', 'indemnity', 'confidentiality', 'termination', 'ip_rights', 'force_majeure', 'penalties', 'bonuses'
    clause_category         TEXT,                               -- 'financial', 'legal', 'operational', 'risk', 'quality'
    clause_title            TEXT NOT NULL,
    clause_description      TEXT NOT NULL,                      -- Full text or summary of clause
    clause_reference        TEXT,                               -- Section number in contract (e.g., "Section 5.3")
    risk_level              TEXT,                               -- 'low', 'medium', 'high', 'critical'
    risk_assessment         TEXT,                               -- Why this clause is flagged as risky
    requires_monitoring     INTEGER DEFAULT 0,                  -- Does this need ongoing monitoring?
    monitoring_frequency    TEXT,                               -- 'weekly', 'monthly', 'quarterly', 'per_milestone'
    responsible_party       TEXT,                               -- Who ensures compliance
    compliance_status       TEXT DEFAULT 'compliant',           -- 'compliant', 'at_risk', 'non_compliant', 'waived'
    compliance_notes        TEXT,
    next_review_date        DATE,                               -- When to review compliance
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contract_id) REFERENCES contract_details(contract_id) ON DELETE CASCADE
);

-- ============================================================================
-- Payment Terms
-- Detailed payment terms and conditions
-- ============================================================================
CREATE TABLE IF NOT EXISTS payment_terms (
    term_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id             INTEGER NOT NULL,
    term_type               TEXT NOT NULL,                      -- 'payment_schedule', 'late_penalty', 'early_discount', 'retention', 'withholding_tax', 'currency_fluctuation'
    description             TEXT NOT NULL,
    payment_method          TEXT,                               -- 'Wire Transfer', 'Check', 'ACH', 'International Transfer'
    payment_due_days        INTEGER,                            -- Days from invoice to payment
    late_payment_penalty    REAL,                               -- Penalty rate per day/month
    early_payment_discount  REAL,                               -- Discount for early payment
    retention_percentage    REAL,                               -- Percentage retained until completion
    retention_release_terms TEXT,                               -- When retention is released
    withholding_tax_rate    REAL,                               -- Tax withholding percentage
    tax_responsibility      TEXT,                               -- Who pays: 'client', 'bensley', 'shared'
    invoicing_frequency     TEXT,                               -- 'monthly', 'per_milestone', 'percentage_completion', 'lump_sum'
    invoice_requirements    TEXT,                               -- Special requirements for invoices
    bank_details            TEXT,                               -- JSON with bank info
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contract_id) REFERENCES contract_details(contract_id) ON DELETE CASCADE
);

-- ============================================================================
-- Contract Amendments
-- Track all amendments and modifications to contracts
-- ============================================================================
CREATE TABLE IF NOT EXISTS contract_amendments (
    amendment_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id             INTEGER NOT NULL,
    amendment_number        TEXT,                               -- 'Amendment 1', 'Amendment 2', etc.
    amendment_type          TEXT NOT NULL,                      -- 'scope_change', 'fee_adjustment', 'timeline_extension', 'payment_terms', 'clause_modification', 'termination'
    description             TEXT NOT NULL,                      -- What changed
    effective_date          DATE,
    fee_impact_usd          REAL,                               -- Change to contract value (+ or -)
    timeline_impact_days    INTEGER,                            -- Change to timeline (+ or -)
    amendment_status        TEXT DEFAULT 'draft',               -- 'draft', 'pending_approval', 'approved', 'executed', 'rejected'
    requested_by            TEXT,                               -- 'bensley', 'client', 'mutual'
    requested_date          DATE,
    approved_date           DATE,
    signed_by_bensley       DATE,
    signed_by_client        DATE,
    amendment_file_path     TEXT,                               -- Path to amendment document
    supersedes_amendment    INTEGER,                            -- Reference to previous amendment if this replaces it
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contract_id) REFERENCES contract_details(contract_id) ON DELETE CASCADE,
    FOREIGN KEY (supersedes_amendment) REFERENCES contract_amendments(amendment_id) ON DELETE SET NULL
);

-- ============================================================================
-- Termination Clauses
-- Track termination rights and procedures
-- ============================================================================
CREATE TABLE IF NOT EXISTS termination_clauses (
    termination_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id             INTEGER NOT NULL,
    termination_type        TEXT NOT NULL,                      -- 'termination_for_convenience', 'termination_for_cause', 'termination_by_mutual_consent', 'auto_termination'
    party_with_right        TEXT,                               -- 'bensley', 'client', 'either', 'mutual_only'
    notice_period_days      INTEGER,                            -- Required notice period
    trigger_conditions      TEXT,                               -- What triggers this termination right
    payment_on_termination  TEXT,                               -- How payment is calculated upon termination
    deliverables_required   TEXT,                               -- What must be delivered upon termination
    ip_rights_disposition   TEXT,                               -- What happens to IP upon termination
    non_compete_period_days INTEGER,                            -- Non-compete duration post-termination
    confidentiality_survives INTEGER DEFAULT 1,                 -- Does confidentiality survive termination?
    notes                   TEXT,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contract_id) REFERENCES contract_details(contract_id) ON DELETE CASCADE
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_contract_details_project
    ON contract_details(project_id);

CREATE INDEX IF NOT EXISTS idx_contract_details_status
    ON contract_details(contract_status);

CREATE INDEX IF NOT EXISTS idx_contract_details_dates
    ON contract_details(contract_date, expiry_date);

CREATE INDEX IF NOT EXISTS idx_contract_clauses_contract
    ON contract_clauses(contract_id);

CREATE INDEX IF NOT EXISTS idx_contract_clauses_type
    ON contract_clauses(clause_type, risk_level);

CREATE INDEX IF NOT EXISTS idx_contract_clauses_monitoring
    ON contract_clauses(requires_monitoring, next_review_date);

CREATE INDEX IF NOT EXISTS idx_payment_terms_contract
    ON payment_terms(contract_id);

CREATE INDEX IF NOT EXISTS idx_contract_amendments_contract
    ON contract_amendments(contract_id);

CREATE INDEX IF NOT EXISTS idx_contract_amendments_status
    ON contract_amendments(amendment_status);

CREATE INDEX IF NOT EXISTS idx_termination_clauses_contract
    ON termination_clauses(contract_id);

-- ============================================================================
-- Triggers for auto-updating timestamps
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_contract_details_timestamp
    AFTER UPDATE ON contract_details
BEGIN
    UPDATE contract_details SET updated_at = CURRENT_TIMESTAMP
    WHERE contract_id = NEW.contract_id;
END;

CREATE TRIGGER IF NOT EXISTS update_contract_clauses_timestamp
    AFTER UPDATE ON contract_clauses
BEGIN
    UPDATE contract_clauses SET updated_at = CURRENT_TIMESTAMP
    WHERE clause_id = NEW.clause_id;
END;

CREATE TRIGGER IF NOT EXISTS update_payment_terms_timestamp
    AFTER UPDATE ON payment_terms
BEGIN
    UPDATE payment_terms SET updated_at = CURRENT_TIMESTAMP
    WHERE term_id = NEW.term_id;
END;

CREATE TRIGGER IF NOT EXISTS update_contract_amendments_timestamp
    AFTER UPDATE ON contract_amendments
BEGIN
    UPDATE contract_amendments SET updated_at = CURRENT_TIMESTAMP
    WHERE amendment_id = NEW.amendment_id;
END;

CREATE TRIGGER IF NOT EXISTS update_termination_clauses_timestamp
    AFTER UPDATE ON termination_clauses
BEGIN
    UPDATE termination_clauses SET updated_at = CURRENT_TIMESTAMP
    WHERE termination_id = NEW.termination_id;
END;

-- ============================================================================
-- Trigger to auto-update contract status based on dates
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS auto_update_contract_status
    AFTER UPDATE ON contract_details
    WHEN NEW.expiry_date < date('now') AND NEW.contract_status = 'active'
BEGIN
    UPDATE contract_details
    SET contract_status = 'expired'
    WHERE contract_id = NEW.contract_id;
END;
