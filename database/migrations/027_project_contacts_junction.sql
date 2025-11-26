-- Migration: Create project_contact_assignments junction table for many-to-many relationship
-- This allows multiple contacts per project and marks primary contacts
-- Note: project_contacts table already exists for email tracking

CREATE TABLE IF NOT EXISTS project_contact_assignments (
  assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  contact_id INTEGER NOT NULL,
  is_primary BOOLEAN DEFAULT 0,
  role_on_project TEXT,  -- e.g., "Project Manager", "Decision Maker", "Technical Contact"
  notes TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
  FOREIGN KEY (contact_id) REFERENCES contacts(contact_id) ON DELETE CASCADE,
  UNIQUE(project_id, contact_id)  -- Prevent duplicate contact assignments
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_pca_project ON project_contact_assignments(project_id);
CREATE INDEX IF NOT EXISTS idx_pca_contact ON project_contact_assignments(contact_id);
CREATE INDEX IF NOT EXISTS idx_pca_primary ON project_contact_assignments(project_id, is_primary);
