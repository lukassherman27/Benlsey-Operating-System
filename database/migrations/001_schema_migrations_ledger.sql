-- Migration 001: Create Schema Migrations Ledger
-- Purpose: Track which migrations have been applied to the database
-- Date: 2025-11-14
--
-- This migration creates the infrastructure to track database schema versions.
-- All future migrations will be recorded here automatically.

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    applied_by TEXT DEFAULT 'system',
    checksum TEXT,  -- MD5 hash of migration file for validation
    execution_time_ms INTEGER
);

-- Create index for quick lookups
CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at
    ON schema_migrations(applied_at DESC);

-- Record this migration
INSERT OR IGNORE INTO schema_migrations (version, name, description, applied_by)
VALUES (1, '001_schema_migrations_ledger', 'Create migration tracking table', 'manual_backfill');

-- Record all previously applied migrations (backfill)
-- These were applied before the migration ledger existed

INSERT OR IGNORE INTO schema_migrations (version, name, description, applied_by, applied_at)
VALUES
    (2, '002_business_structure', 'Business structure tables', 'manual_backfill', '2025-11-13 00:00:00'),
    (3, '003_daily_work_tracking', 'Daily work tracking', 'manual_backfill', '2025-11-13 00:00:00'),
    (4, '004_smart_contact_learning', 'Smart contact learning', 'manual_backfill', '2025-11-13 00:00:00'),
    (5, '005_brain_intelligence', 'Brain intelligence tables', 'manual_backfill', '2025-11-13 00:00:00'),
    (6, '006_proposal_vs_project_status', 'Distinguish proposals vs projects', 'manual_backfill', '2025-11-13 00:00:00'),
    (7, '007_context_aware_health', 'Context-aware health scoring', 'manual_backfill', '2025-11-13 00:00:00'),
    (8, '008_document_intelligence', 'Document intelligence features', 'manual_backfill', '2025-11-13 00:00:00'),
    (9, '009_add_full_email_body', 'Add full email body storage', 'manual_backfill', '2025-11-13 00:00:00'),
    (10, '010_performance_indexes', 'Performance optimization indexes', 'manual_backfill', '2025-11-13 00:00:00'),
    (11, '011_improved_email_categories', 'Enhanced email categorization', 'manual_backfill', '2025-11-14 00:00:00'),
    (12, '012_critical_query_indexes', 'Critical query performance indexes', 'manual_backfill', '2025-11-14 00:00:00');

-- Verify migrations
SELECT
    version,
    name,
    applied_at,
    applied_by
FROM schema_migrations
ORDER BY version;
