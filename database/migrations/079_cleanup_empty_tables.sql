-- Migration 079: Cleanup empty tables
-- These tables have 0 rows and are not used

DROP TABLE IF EXISTS decision_log;
DROP TABLE IF EXISTS document_proposal_links;
DROP TABLE IF EXISTS document_versions;
DROP TABLE IF EXISTS query_log;
