-- Migration 017: Add is_active_project column to projects table
-- Purpose: API code expects this column but it's missing from schema

-- Add is_active_project column (1 = active project, 0 = pipeline proposal)
ALTER TABLE projects ADD COLUMN is_active_project INTEGER DEFAULT 0;

-- Set is_active_project based on existing status
UPDATE projects
SET is_active_project = 1
WHERE status IN ('Active', 'active', 'Active Contract');

-- Create index for performance
CREATE INDEX idx_projects_is_active ON projects(is_active_project);
