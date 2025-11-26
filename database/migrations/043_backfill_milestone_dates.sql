-- Migration: Backfill planned_date for project_milestones
-- Created: 2025-11-26 by Agent 4 (Data Pipeline)
-- Reason: All 110 milestones have NULL planned_date but have actual_date
-- Strategy: For completed milestones, set planned_date = actual_date

-- Check before
-- SELECT
--     status,
--     COUNT(*) as count,
--     SUM(CASE WHEN planned_date IS NOT NULL THEN 1 ELSE 0 END) as with_planned,
--     SUM(CASE WHEN actual_date IS NOT NULL THEN 1 ELSE 0 END) as with_actual
-- FROM project_milestones
-- GROUP BY status;

-- Backfill planned_date from actual_date for completed milestones
UPDATE project_milestones
SET planned_date = actual_date
WHERE planned_date IS NULL
  AND actual_date IS NOT NULL
  AND status = 'complete';

-- Verify results
SELECT
    'After backfill:' as stage,
    COUNT(*) as total,
    SUM(CASE WHEN planned_date IS NOT NULL THEN 1 ELSE 0 END) as with_planned_date,
    SUM(CASE WHEN actual_date IS NOT NULL THEN 1 ELSE 0 END) as with_actual_date
FROM project_milestones;
