-- Migration 019: Flexible Contract Phases Structure
-- Purpose: Store detailed contract breakdown by discipline and phase
-- Supports: Landscape, Architecture, Interior, Branding, and any custom disciplines
-- Phases: Mobilization, Schematic (optional), Conceptual, DD, CD, CA

-- Create contract_phases table
CREATE TABLE IF NOT EXISTS contract_phases (
    phase_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,

    -- Discipline (Landscape, Architecture, Interior, Branding, etc.)
    discipline TEXT NOT NULL,

    -- Phase name (Mobilization, Schematic, Conceptual Design, Design Development, etc.)
    phase_name TEXT NOT NULL,

    -- Phase order (for sorting: 1=Mobilization, 2=Schematic, 3=Conceptual, etc.)
    phase_order INTEGER,

    -- Financial tracking
    phase_fee_usd REAL,
    invoiced_amount_usd REAL DEFAULT 0,
    paid_amount_usd REAL DEFAULT 0,

    -- Status tracking
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')),

    -- Dates
    start_date DATE,
    expected_completion_date DATE,
    actual_completion_date DATE,

    -- Notes and details
    scope_description TEXT,
    deliverables TEXT,
    notes TEXT,

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_contract_phases_project ON contract_phases(project_id);
CREATE INDEX idx_contract_phases_discipline ON contract_phases(discipline);
CREATE INDEX idx_contract_phases_status ON contract_phases(status);
CREATE INDEX idx_contract_phases_order ON contract_phases(project_id, discipline, phase_order);

-- Create contract_metadata table for overall contract info
CREATE TABLE IF NOT EXISTS contract_metadata (
    contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL UNIQUE,

    -- Contract details
    contract_date DATE,
    contract_term_months INTEGER,
    contract_file_path TEXT,

    -- Financial summary
    total_contract_value_usd REAL,
    total_landscape_fee_usd REAL,
    total_architecture_fee_usd REAL,
    total_interior_fee_usd REAL,
    total_branding_fee_usd REAL,
    total_other_fees_usd REAL,

    -- Payment terms
    payment_terms TEXT,
    payment_due_days INTEGER DEFAULT 30,
    late_payment_interest_rate REAL,

    -- Contract parties
    client_name TEXT,
    client_address TEXT,
    signing_date DATE,

    -- Metadata
    parsed_at DATETIME,
    parsed_by TEXT DEFAULT 'ai',
    verified BOOLEAN DEFAULT 0,
    notes TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE INDEX idx_contract_metadata_project ON contract_metadata(project_id);
CREATE INDEX idx_contract_metadata_date ON contract_metadata(contract_date);
