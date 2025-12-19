-- Migration 084: Cleanup dead tables
-- Date: 2025-12-11
-- Description: Remove tables with 0 rows that appear unused

DROP TABLE IF EXISTS learning_events;
DROP TABLE IF EXISTS project_phase_history;
