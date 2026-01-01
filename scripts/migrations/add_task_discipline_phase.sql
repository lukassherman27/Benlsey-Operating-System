-- Migration: Add discipline and phase columns to tasks table
-- Issue: #310 Task Management UI - Discipline/Phase Structure
-- Date: 2026-01-01

-- Add discipline column (Interior, Landscape, Lighting, FF&E, General)
ALTER TABLE tasks ADD COLUMN discipline TEXT
  CHECK (discipline IN ('Interior', 'Landscape', 'Lighting', 'FFE', 'General', NULL));

-- Add phase column (SD, DD, CD, CA)
ALTER TABLE tasks ADD COLUMN phase TEXT
  CHECK (phase IN ('SD', 'DD', 'CD', 'CA', NULL));

-- Create indexes for filtering
CREATE INDEX IF NOT EXISTS idx_tasks_discipline ON tasks(discipline);
CREATE INDEX IF NOT EXISTS idx_tasks_phase ON tasks(phase);
CREATE INDEX IF NOT EXISTS idx_tasks_discipline_phase ON tasks(discipline, phase);
