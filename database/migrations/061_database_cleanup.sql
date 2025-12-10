-- Migration: 061_database_cleanup.sql
-- Purpose: Clean up orphaned FK rows and drop empty tables
-- Date: 2025-12-02
-- Author: Database Cleanup Agent
--
-- Summary:
-- 1. Delete 391 orphaned rows from document_proposal_links (100% have invalid proposal_id)
-- 2. Delete 14 orphaned rows from project_contact_links (invalid project_id or proposal_id)
-- 3. Drop 24 empty tables that have never been used
--
-- Note: team_members and team_member_specialties are NOT touched because:
-- - team_members is referenced by schedule_entries (1120 rows)
-- - Both tables have active data
-- - Consolidation with staff table requires broader refactoring

-- ============================================================================
-- PART 1: Fix FK Violations
-- ============================================================================

-- 1a. Delete ALL document_proposal_links (100% orphaned - no valid proposal_id references)
-- Before: 391 rows, 0 with valid FK
DELETE FROM document_proposal_links;

-- 1b. Delete orphaned project_contact_links with invalid project_id
-- These reference project_id = 115078 which doesn't exist
DELETE FROM project_contact_links
WHERE project_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = project_contact_links.project_id);

-- 1c. Delete orphaned project_contact_links with invalid proposal_id
-- These reference proposal_ids (33, 44, 45, 52) that don't exist
DELETE FROM project_contact_links
WHERE proposal_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM proposals p WHERE p.proposal_id = project_contact_links.proposal_id);

-- ============================================================================
-- PART 2: Drop Empty Tables (24 tables, all verified 0 rows)
-- ============================================================================

-- AI/ML feature tables (never populated)
DROP TABLE IF EXISTS ai_action_queue;
DROP TABLE IF EXISTS ai_observations;
DROP TABLE IF EXISTS learned_user_patterns;
DROP TABLE IF EXISTS suggestion_actions;

-- Logging/audit tables (never populated)
DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS change_log;
DROP TABLE IF EXISTS pattern_usage_log;
DROP TABLE IF EXISTS email_pattern_usage_log;

-- Meeting/action tracking (never populated)
DROP TABLE IF EXISTS action_items;
DROP TABLE IF EXISTS decisions;
DROP TABLE IF EXISTS meeting_reminders;

-- Project management tables (never populated)
DROP TABLE IF EXISTS deliverables;
DROP TABLE IF EXISTS project_tags;
DROP TABLE IF EXISTS project_contact_assignments;
DROP TABLE IF EXISTS project_pm_assignments;
DROP TABLE IF EXISTS rfi_responses;

-- Proposal tracking tables (never populated)
DROP TABLE IF EXISTS proposal_documents;
DROP TABLE IF EXISTS proposal_state;
DROP TABLE IF EXISTS proposal_timeline;

-- Client/category tables (never populated)
DROP TABLE IF EXISTS client_aliases;
DROP TABLE IF EXISTS category_patterns;
DROP TABLE IF EXISTS email_category_history;

-- Contract tables (never populated)
DROP TABLE IF EXISTS contract_versions;

-- Email tables (never populated)
DROP TABLE IF EXISTS email_client_links;

-- ============================================================================
-- VERIFICATION QUERIES (run these after migration)
-- ============================================================================

-- Verify FK integrity
-- PRAGMA foreign_key_check(document_proposal_links);  -- Should return empty
-- PRAGMA foreign_key_check(project_contact_links);    -- Should return empty

-- Verify tables dropped
-- SELECT COUNT(*) FROM sqlite_master WHERE name = 'action_items';  -- Should be 0

-- Count remaining tables
-- SELECT COUNT(*) FROM sqlite_master WHERE type = 'table';  -- Should be ~91 (115 - 24)
