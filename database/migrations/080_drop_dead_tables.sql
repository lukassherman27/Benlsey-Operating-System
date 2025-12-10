-- Migration 080: Drop Dead Tables
-- Date: 2025-12-10
-- Purpose: Remove 5 unused/archived tables that are no longer needed
-- Total rows being removed: 741 rows across 5 tables

-- 1. contacts_only_archive (205 rows)
-- Backup table - data already migrated to contacts table
DROP TABLE IF EXISTS contacts_only_archive;

-- 2. project_contacts_archive (6 rows)
-- Old system - replaced by contact_context table
DROP TABLE IF EXISTS project_contacts_archive;

-- 3. contact_metadata_archive (183 rows)
-- Backup table - data already migrated to contacts table
DROP TABLE IF EXISTS contact_metadata_archive;

-- 4. learned_patterns (341 rows)
-- Abandoned feature - never read by any code in the system
DROP TABLE IF EXISTS learned_patterns;

-- 5. learning_patterns (6 rows)
-- Abandoned feature - superseded by other learning systems
DROP TABLE IF EXISTS learning_patterns;
