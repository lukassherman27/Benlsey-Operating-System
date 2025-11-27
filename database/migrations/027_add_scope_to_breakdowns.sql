-- Migration 027: Add scope/area field to project_fee_breakdown
-- This allows one project to have multiple scopes/areas, each with their own phase breakdowns
--
-- Examples:
--   Wynn Marjan: 4 scopes (Indian Brasserie, Mediterranean Restaurant, Day Club, Night Club)
--   Capella Ubud: 1 scope (general)
--   Art Deco: 2 scopes (Sale Center, Main Tower Block)

-- Add scope column (nullable for backward compatibility)
ALTER TABLE project_fee_breakdown ADD COLUMN scope TEXT;

-- Create index for scope queries
CREATE INDEX IF NOT EXISTS idx_breakdown_scope ON project_fee_breakdown(project_code, scope);

-- Update existing records to use "general" scope
-- This maintains backward compatibility for simple projects
UPDATE project_fee_breakdown
SET scope = 'general'
WHERE scope IS NULL;

-- Note: breakdown_id format will change to include scope:
-- Old: {project_code}_{discipline}_{phase}
-- New: {project_code}_{scope}_{discipline}_{phase}
--
-- This requires regenerating breakdown_ids for all existing records
-- Run fix_breakdown_ids_with_scope.py after this migration
