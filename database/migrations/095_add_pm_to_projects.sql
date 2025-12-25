-- Migration 095: Add PM (Project Manager) to projects table
-- Created: 2025-12-26
-- Issue: #107 - Project management redesign

-- Add PM staff_id to projects table
ALTER TABLE projects ADD COLUMN pm_staff_id INTEGER REFERENCES staff(staff_id);

-- Create index for fast lookups by PM
CREATE INDEX IF NOT EXISTS idx_projects_pm ON projects(pm_staff_id);

-- Add PM assignment history table for tracking changes
CREATE TABLE IF NOT EXISTS project_pm_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(project_id),
    pm_staff_id INTEGER REFERENCES staff(staff_id),
    assigned_date DATE NOT NULL,
    removed_date DATE,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_pm_history_project ON project_pm_history(project_id);
CREATE INDEX IF NOT EXISTS idx_pm_history_pm ON project_pm_history(pm_staff_id);
