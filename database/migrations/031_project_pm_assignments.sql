-- Migration: Project PM Assignments
-- Created: 2025-11-26
-- Purpose: Track dynamic PM assignment to projects based on specialty and phase
--
-- User Requirements:
-- - PMs have specialties (Interiors, Architecture, Landscape) with sub-specialties
-- - Assignment changes based on project phase/milestone
-- - Main PM = point of contact who organizes/schedules/presents
-- - Must be dynamic - can reassign as project evolves

-- Project PM assignments (who's responsible for what project at what phase)
CREATE TABLE IF NOT EXISTS project_pm_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    project_code TEXT NOT NULL,
    member_id INTEGER NOT NULL,  -- FK to team_members
    role TEXT NOT NULL DEFAULT 'assigned',  -- 'lead', 'assigned', 'support', 'reviewer'
    phase TEXT,  -- NULL means all phases; else: 'concept', 'schematic', 'DD', 'CD', 'construction'
    start_date DATE NOT NULL DEFAULT (date('now')),
    end_date DATE,  -- NULL = current assignment
    is_primary INTEGER DEFAULT 0,  -- Is this the main point of contact?
    notes TEXT,
    assigned_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (member_id) REFERENCES team_members(member_id)
);

CREATE INDEX IF NOT EXISTS idx_pm_assignments_project ON project_pm_assignments(project_code);
CREATE INDEX IF NOT EXISTS idx_pm_assignments_member ON project_pm_assignments(member_id);
CREATE INDEX IF NOT EXISTS idx_pm_assignments_active ON project_pm_assignments(end_date) WHERE end_date IS NULL;

-- Team member specialties (sub-specialties within disciplines)
-- Example: An Interior PM might specialize in "hotels" or "residential"
CREATE TABLE IF NOT EXISTS team_member_specialties (
    specialty_id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    specialty_category TEXT NOT NULL,  -- 'hotel', 'residential', 'restaurant', 'retail', etc.
    proficiency_level TEXT DEFAULT 'standard',  -- 'expert', 'standard', 'learning'
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (member_id) REFERENCES team_members(member_id)
);

CREATE INDEX IF NOT EXISTS idx_member_specialties ON team_member_specialties(member_id);

-- Add sub_specialty to team_members if not exists
-- This is the primary specialty within their discipline
ALTER TABLE team_members ADD COLUMN sub_specialty TEXT;

-- Add assigned_pm_id to rfis table (foreign key to team_members)
-- This links an RFI to the responsible PM
ALTER TABLE rfis ADD COLUMN assigned_pm_id INTEGER REFERENCES team_members(member_id);

-- View: Get current PM for each project
CREATE VIEW IF NOT EXISTS v_current_project_pms AS
SELECT
    p.project_id,
    p.project_code,
    p.project_title,
    pa.member_id,
    tm.full_name as pm_name,
    tm.nickname as pm_nickname,
    tm.email as pm_email,
    tm.discipline,
    pa.role,
    pa.phase,
    pa.is_primary,
    pa.start_date
FROM projects p
LEFT JOIN project_pm_assignments pa ON p.project_id = pa.project_id
    AND pa.end_date IS NULL  -- Current assignments only
LEFT JOIN team_members tm ON pa.member_id = tm.member_id
WHERE tm.is_active = 1 OR tm.is_active IS NULL;

-- View: PM workload (how many active projects each PM has)
CREATE VIEW IF NOT EXISTS v_pm_workload AS
SELECT
    tm.member_id,
    tm.full_name,
    tm.nickname,
    tm.discipline,
    COUNT(DISTINCT pa.project_id) as active_projects,
    SUM(CASE WHEN pa.is_primary = 1 THEN 1 ELSE 0 END) as primary_projects,
    COUNT(DISTINCT CASE WHEN r.status = 'open' THEN r.rfi_id END) as open_rfis,
    COUNT(DISTINCT CASE WHEN r.status = 'open' AND date(r.date_due) < date('now') THEN r.rfi_id END) as overdue_rfis
FROM team_members tm
LEFT JOIN project_pm_assignments pa ON tm.member_id = pa.member_id
    AND pa.end_date IS NULL
LEFT JOIN rfis r ON tm.member_id = r.assigned_pm_id
WHERE tm.is_active = 1
GROUP BY tm.member_id, tm.full_name, tm.nickname, tm.discipline
ORDER BY active_projects DESC;

-- Insert example specialty categories
-- (These are common project types at Bensley)
INSERT OR IGNORE INTO team_member_specialties (member_id, specialty_category, proficiency_level, notes)
SELECT member_id, 'hotels', 'expert', 'Primary specialty'
FROM team_members WHERE discipline = 'Interior' AND is_team_lead = 1
LIMIT 1;
