-- Migration 020: Add Provenance Tracking to Contract Tables
-- Purpose: Track data sources for contract_metadata and contract_phases

-- Add provenance columns to contract_metadata
ALTER TABLE contract_metadata ADD COLUMN source_type TEXT CHECK(source_type IN ('manual', 'import', 'ai', 'email_parser'));
ALTER TABLE contract_metadata ADD COLUMN source_reference TEXT;
ALTER TABLE contract_metadata ADD COLUMN locked_fields TEXT;
ALTER TABLE contract_metadata ADD COLUMN locked_by TEXT;
ALTER TABLE contract_metadata ADD COLUMN locked_at DATETIME;
ALTER TABLE contract_metadata ADD COLUMN created_by TEXT DEFAULT 'system';
ALTER TABLE contract_metadata ADD COLUMN updated_by TEXT;

-- Add provenance columns to contract_phases
ALTER TABLE contract_phases ADD COLUMN source_type TEXT CHECK(source_type IN ('manual', 'import', 'ai', 'email_parser'));
ALTER TABLE contract_phases ADD COLUMN source_reference TEXT;
ALTER TABLE contract_phases ADD COLUMN locked_fields TEXT;
ALTER TABLE contract_phases ADD COLUMN locked_by TEXT;
ALTER TABLE contract_phases ADD COLUMN locked_at DATETIME;
ALTER TABLE contract_phases ADD COLUMN created_by TEXT DEFAULT 'system';
ALTER TABLE contract_phases ADD COLUMN updated_by TEXT;
