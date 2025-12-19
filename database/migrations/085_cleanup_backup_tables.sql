-- Migration 085: Cleanup backup tables
-- Date: 2025-12-11
-- Description: Remove backup/archive tables from Dec 11 cleanup

DROP TABLE IF EXISTS email_learned_patterns_backup_dec11;
DROP TABLE IF EXISTS learned_patterns_backup_dec11;
