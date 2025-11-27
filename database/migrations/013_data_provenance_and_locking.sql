-- Migration 013: Data Provenance and Field Locking System
-- Purpose: Track data sources and protect manually entered data from AI overwrites

-- ====================================================================================================
-- ADD PROVENANCE COLUMNS TO CORE TABLES
-- ====================================================================================================

-- Projects table
ALTER TABLE projects ADD COLUMN source_type TEXT CHECK(source_type IN ('manual', 'import', 'ai', 'email_parser'));
ALTER TABLE projects ADD COLUMN source_reference TEXT;     -- e.g., "MASTER_CONTRACT_FEE_BREAKDOWN.xlsx:row_42"
ALTER TABLE projects ADD COLUMN locked_fields TEXT;        -- JSON array: ["project_code", "total_fee_usd"]
ALTER TABLE projects ADD COLUMN locked_by TEXT;            -- e.g., "seed/manual", "user:bill"
ALTER TABLE projects ADD COLUMN locked_at DATETIME;
ALTER TABLE projects ADD COLUMN created_by TEXT DEFAULT 'system';
ALTER TABLE projects ADD COLUMN updated_by TEXT;

-- Invoices table
ALTER TABLE invoices ADD COLUMN source_type TEXT CHECK(source_type IN ('manual', 'import', 'ai', 'email_parser'));
ALTER TABLE invoices ADD COLUMN source_reference TEXT;
ALTER TABLE invoices ADD COLUMN locked_fields TEXT;
ALTER TABLE invoices ADD COLUMN locked_by TEXT;
ALTER TABLE invoices ADD COLUMN locked_at DATETIME;
ALTER TABLE invoices ADD COLUMN created_by TEXT DEFAULT 'system';
ALTER TABLE invoices ADD COLUMN updated_by TEXT;

-- Emails table
ALTER TABLE emails ADD COLUMN source_type TEXT CHECK(source_type IN ('manual', 'import', 'ai', 'email_parser')) DEFAULT 'email_parser';
ALTER TABLE emails ADD COLUMN source_reference TEXT;
ALTER TABLE emails ADD COLUMN created_by TEXT DEFAULT 'email_parser';
ALTER TABLE emails ADD COLUMN updated_by TEXT;

-- Project metadata table (if it exists)
ALTER TABLE project_metadata ADD COLUMN source_type TEXT CHECK(source_type IN ('manual', 'import', 'ai', 'email_parser'));
ALTER TABLE project_metadata ADD COLUMN source_reference TEXT;
ALTER TABLE project_metadata ADD COLUMN locked_fields TEXT;
ALTER TABLE project_metadata ADD COLUMN locked_by TEXT;
ALTER TABLE project_metadata ADD COLUMN locked_at DATETIME;
ALTER TABLE project_metadata ADD COLUMN created_by TEXT DEFAULT 'system';
ALTER TABLE project_metadata ADD COLUMN updated_by TEXT;
