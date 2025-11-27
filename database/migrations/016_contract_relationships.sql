-- Migration 016: Add Contract Relationship Fields to Projects Table
-- Adds support for parent-child project relationships (additional services, extensions, components)

-- Add contract relationship fields to projects table
ALTER TABLE projects ADD COLUMN parent_project_code TEXT;
ALTER TABLE projects ADD COLUMN relationship_type TEXT DEFAULT 'standalone';
  -- Values: 'standalone', 'additional_services', 'extension', 'component', 'amendment'
ALTER TABLE projects ADD COLUMN component_type TEXT;
  -- Values: 'restaurant', 'club', 'landscape', 'interior', 'spa', 'monthly_maintenance'
ALTER TABLE projects ADD COLUMN cancellation_date TEXT;
ALTER TABLE projects ADD COLUMN cancellation_reason TEXT;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_projects_parent ON projects(parent_project_code);
CREATE INDEX IF NOT EXISTS idx_projects_relationship ON projects(relationship_type);

-- Update migration ledger
INSERT INTO schema_migrations (version, name, description, applied_at)
VALUES (16, '016_contract_relationships',
       'Add parent-child relationship fields to projects table for tracking additional services and contract amendments',
       datetime('now'));
