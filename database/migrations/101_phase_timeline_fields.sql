-- Migration 101: Add Phase Timeline Fields to Projects Table
-- Created: 2025-12-30
-- Issue: #242 - Add phase timeline fields to projects table
-- Description: Add columns to track contract duration and phase-specific timelines (SD, DD, CD, CA)
--              Enables progress tracking against contract deadlines

-- ============================================================================
-- Phase Timeline Fields
-- SD = Schematic Design
-- DD = Design Development
-- CD = Construction Documents
-- CA = Contract Administration
-- ============================================================================

-- Contract-level fields (if not already existing)
-- Note: contract_term_months and contract_start_date already exist
ALTER TABLE projects ADD COLUMN contract_duration_months INTEGER;
ALTER TABLE projects ADD COLUMN contract_end_date TEXT;

-- Schematic Design (SD) Phase
ALTER TABLE projects ADD COLUMN sd_allocated_months INTEGER;
ALTER TABLE projects ADD COLUMN sd_start_date TEXT;
ALTER TABLE projects ADD COLUMN sd_deadline TEXT;
ALTER TABLE projects ADD COLUMN sd_actual_completion TEXT;

-- Design Development (DD) Phase
ALTER TABLE projects ADD COLUMN dd_allocated_months INTEGER;
ALTER TABLE projects ADD COLUMN dd_start_date TEXT;
ALTER TABLE projects ADD COLUMN dd_deadline TEXT;
ALTER TABLE projects ADD COLUMN dd_actual_completion TEXT;

-- Construction Documents (CD) Phase
ALTER TABLE projects ADD COLUMN cd_allocated_months INTEGER;
ALTER TABLE projects ADD COLUMN cd_start_date TEXT;
ALTER TABLE projects ADD COLUMN cd_deadline TEXT;
ALTER TABLE projects ADD COLUMN cd_actual_completion TEXT;

-- Contract Administration (CA) Phase
ALTER TABLE projects ADD COLUMN ca_allocated_months INTEGER;
ALTER TABLE projects ADD COLUMN ca_start_date TEXT;
ALTER TABLE projects ADD COLUMN ca_deadline TEXT;
ALTER TABLE projects ADD COLUMN ca_actual_completion TEXT;

-- ============================================================================
-- Sync existing contract fields
-- Copy contract_term_months to contract_duration_months for consistency
-- Copy contract_expiry_date to contract_end_date for consistency
-- ============================================================================
UPDATE projects
SET contract_duration_months = contract_term_months
WHERE contract_term_months IS NOT NULL;

UPDATE projects
SET contract_end_date = contract_expiry_date
WHERE contract_expiry_date IS NOT NULL;

-- ============================================================================
-- Indexes for queries on phase timelines
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_projects_sd_deadline ON projects(sd_deadline);
CREATE INDEX IF NOT EXISTS idx_projects_dd_deadline ON projects(dd_deadline);
CREATE INDEX IF NOT EXISTS idx_projects_cd_deadline ON projects(cd_deadline);
CREATE INDEX IF NOT EXISTS idx_projects_ca_deadline ON projects(ca_deadline);
CREATE INDEX IF NOT EXISTS idx_projects_contract_end ON projects(contract_end_date);
