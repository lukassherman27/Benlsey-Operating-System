-- Migration 092: Cleanup Old Category Tables
-- Drops redundant categorization tables after backfill is complete
-- Created: 2025-12-25
--
-- IMPORTANT: Only run this AFTER verifying 091_backfill worked correctly!
-- Check that most emails have primary_category set before running.

-- ============================================
-- STEP 1: Drop old categorization tables
-- ============================================

-- These tables are replaced by the unified emails.primary_category field
-- and the new email_category_codes reference table

DROP TABLE IF EXISTS email_categories;
DROP TABLE IF EXISTS email_category_rules;
DROP TABLE IF EXISTS email_category_history;
DROP TABLE IF EXISTS uncategorized_emails;
DROP TABLE IF EXISTS email_tags;
DROP TABLE IF EXISTS category_patterns;

-- ============================================
-- NOTE: We keep these tables:
-- ============================================
--
-- 1. email_learned_patterns - for email→proposal linking (works well)
-- 2. email_content - for AI analysis, sentiment, action_required
--    (we'll stop using category/subcategory columns but keep the table)
-- 3. email_category_codes - NEW reference table for valid categories
--
-- We are NOT dropping columns from emails or email_content because:
-- - SQLite doesn't support DROP COLUMN in older versions
-- - The columns can be ignored and will be overwritten
-- - Cleaner to leave them than risk data loss
