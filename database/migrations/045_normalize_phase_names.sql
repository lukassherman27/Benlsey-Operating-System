-- Migration 045: Normalize Phase Names in project_fee_breakdown
-- Created: 2025-11-27
-- Purpose: Standardize phase names to match frontend PHASE_ORDER constants
--
-- Standard phases:
--   Mobilization, Concept Design, Schematic Design, Design Development,
--   Construction Documents, Construction Observation

-- Begin transaction
BEGIN TRANSACTION;

-- 1. Normalize case variations of standard phases
UPDATE project_fee_breakdown SET phase = 'Mobilization'
WHERE LOWER(TRIM(phase)) = 'mobilization';

UPDATE project_fee_breakdown SET phase = 'Concept Design'
WHERE LOWER(TRIM(phase)) IN ('concept design', 'conceptual design', 'concept')
   OR phase LIKE 'concept Design%'
   OR phase LIKE 'Concept design%';

UPDATE project_fee_breakdown SET phase = 'Schematic Design'
WHERE LOWER(TRIM(phase)) IN ('schematic design', 'schematic')
   OR phase LIKE 'Schematic design%';

UPDATE project_fee_breakdown SET phase = 'Design Development'
WHERE LOWER(TRIM(phase)) LIKE '%design development%'
   OR phase LIKE '%Design Development%';

UPDATE project_fee_breakdown SET phase = 'Construction Documents'
WHERE LOWER(TRIM(phase)) IN ('construction documents', 'construction drawing', 'construction drawings')
   OR phase LIKE '%Construction Document%'
   OR phase LIKE '%Construction Drawing%';

UPDATE project_fee_breakdown SET phase = 'Construction Observation'
WHERE LOWER(TRIM(phase)) IN ('construction observation', 'construction administration', 'ca')
   OR phase LIKE '%Construction Observation%';

-- 2. Handle project-specific phases with suffixes (keep them but normalize base name)
-- These are for projects with multiple scope items (e.g., "Main Tower Block", "Sale Center")
-- We'll rename to include scope in a consistent way

-- Create a scope column if it doesn't exist (already exists per schema)
-- The scope column will hold "Sale Center", "Main Tower Block", etc.

-- Update phase names and extract scope for split projects
UPDATE project_fee_breakdown
SET
    scope = CASE
        WHEN phase LIKE '% - Sale Center%' THEN 'Sale Center'
        WHEN phase LIKE '% - Main Tower%' THEN 'Main Tower Block'
        ELSE scope
    END,
    phase = CASE
        WHEN phase LIKE 'Concept Design - %' THEN 'Concept Design'
        WHEN phase LIKE 'Design Development - %' THEN 'Design Development'
        WHEN phase LIKE 'Construction Documents - %' THEN 'Construction Documents'
        WHEN phase LIKE 'Construction Observation - %' THEN 'Construction Observation'
        WHEN phase LIKE '%Redesign%' THEN 'Design Development'
        ELSE phase
    END
WHERE phase LIKE '% - %' OR phase LIKE '%Redesign%';

-- 3. Standardize other non-standard phases
UPDATE project_fee_breakdown SET phase = 'Additional Services'
WHERE phase IN ('Additional Work', 'Additional Service');

UPDATE project_fee_breakdown SET phase = 'Monthly Retainer'
WHERE phase IN ('monthly-payment');

UPDATE project_fee_breakdown SET phase = 'Branding'
WHERE phase IN ('Branding', 'Brand Consultancy & Immersions');

UPDATE project_fee_breakdown SET phase = 'Pre-Concept'
WHERE phase LIKE '%pre-concept%' OR phase LIKE '%Masterplan%';

-- 4. Log the migration
INSERT INTO schema_migrations (version, name, description)
SELECT 45, '045_normalize_phase_names', 'Normalized phase names in project_fee_breakdown'
WHERE NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = 45);

COMMIT;

-- Verification query (run after migration to confirm):
-- SELECT phase, COUNT(*) as count FROM project_fee_breakdown GROUP BY phase ORDER BY count DESC;
