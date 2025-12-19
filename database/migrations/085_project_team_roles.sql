-- Migration 085: Project Team & Stakeholder Roles
-- Tracks who's involved in each project with their specific role
-- Run: sqlite3 database/bensley_master.db < database/migrations/085_project_team_roles.sql

-- ============================================================================
-- PROJECT ROLES (standardized role types)
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_role_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT UNIQUE NOT NULL,
    role_category TEXT NOT NULL,  -- owner, client_team, consultant, contractor, bensley
    description TEXT,
    typical_responsibilities TEXT
);

-- Seed standard project roles
INSERT OR IGNORE INTO project_role_types (role_name, role_category, description) VALUES
    -- Owner/Developer side
    ('Owner', 'owner', 'Property owner or investor'),
    ('Developer', 'owner', 'Development company'),
    ('Asset Manager', 'owner', 'Manages property portfolio'),

    -- Client team
    ('Project Director', 'client_team', 'Overall project lead from client side'),
    ('Project Manager', 'client_team', 'Day-to-day project management'),
    ('Design Manager', 'client_team', 'Manages design process for client'),
    ('Procurement Manager', 'client_team', 'Handles purchasing/sourcing'),
    ('Technical Director', 'client_team', 'Technical oversight'),

    -- Consultants (external)
    ('Executive Architect', 'consultant', 'Local architect of record'),
    ('Structural Engineer', 'consultant', 'Structural engineering'),
    ('MEP Engineer', 'consultant', 'Mechanical/Electrical/Plumbing'),
    ('Lighting Designer', 'consultant', 'Lighting design consultant'),
    ('Acoustic Consultant', 'consultant', 'Acoustics and sound'),
    ('Kitchen Consultant', 'consultant', 'Commercial kitchen design'),
    ('Spa Consultant', 'consultant', 'Spa/wellness consulting'),
    ('Pool Consultant', 'consultant', 'Pool engineering'),
    ('Landscape Architect', 'consultant', 'External landscape (if not BENSLEY)'),
    ('Wayfinding/Signage', 'consultant', 'Signage and wayfinding'),
    ('Brand Consultant', 'consultant', 'Branding and identity'),
    ('F&B Consultant', 'consultant', 'Food & beverage concepts'),
    ('Guest Experience', 'consultant', 'Guest journey and experience design'),
    ('Sustainability', 'consultant', 'LEED/sustainability consultant'),
    ('Cost Consultant', 'consultant', 'Quantity surveyor / cost management'),
    ('FF&E Procurement', 'consultant', 'FF&E sourcing and procurement'),
    ('Art Consultant', 'consultant', 'Art curation and procurement'),
    ('Operator', 'consultant', 'Hotel operator (Marriott, Hilton, etc.)'),

    -- Contractors
    ('General Contractor', 'contractor', 'Main construction contractor'),
    ('Fit-out Contractor', 'contractor', 'Interior fit-out'),
    ('Landscape Contractor', 'contractor', 'Landscape installation'),
    ('FF&E Installer', 'contractor', 'Furniture installation'),

    -- BENSLEY team
    ('Design Director', 'bensley', 'BENSLEY design lead'),
    ('Project Architect', 'bensley', 'BENSLEY project architect'),
    ('Interior Designer', 'bensley', 'BENSLEY interior designer'),
    ('Landscape Designer', 'bensley', 'BENSLEY landscape designer'),
    ('Project Coordinator', 'bensley', 'BENSLEY project coordinator');

-- ============================================================================
-- PROJECT TEAM MEMBERS (who's on each project)
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_team (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code TEXT NOT NULL,

    -- Link to contact OR staff (one should be set)
    contact_id INTEGER,  -- External people (from contacts table)
    staff_id INTEGER,    -- BENSLEY team (from staff table)

    -- Role info
    role_type_id INTEGER,  -- Links to project_role_types
    role_custom TEXT,      -- If role not in standard list
    company TEXT,          -- Company they represent

    -- Status
    is_active INTEGER DEFAULT 1,
    start_date TEXT,
    end_date TEXT,

    -- Contact preferences for this project
    preferred_contact_method TEXT,  -- email, whatsapp, phone, wechat

    -- Relationship
    introduced_by TEXT,  -- Who brought them onto project
    notes TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id),
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id),
    FOREIGN KEY (role_type_id) REFERENCES project_role_types(id)
);

CREATE INDEX IF NOT EXISTS idx_project_team_project ON project_team(project_code);
CREATE INDEX IF NOT EXISTS idx_project_team_contact ON project_team(contact_id);
CREATE INDEX IF NOT EXISTS idx_project_team_staff ON project_team(staff_id);

-- ============================================================================
-- VIEW: Full project team with details
-- ============================================================================

CREATE VIEW IF NOT EXISTS v_project_team_full AS
SELECT
    pt.id,
    pt.project_code,
    COALESCE(c.name, s.first_name || ' ' || COALESCE(s.last_name, '')) as person_name,
    COALESCE(c.email, s.email) as email,
    COALESCE(c.company, 'BENSLEY') as company,
    prt.role_name,
    prt.role_category,
    COALESCE(pt.role_custom, prt.role_name) as display_role,
    CASE
        WHEN pt.staff_id IS NOT NULL THEN 'internal'
        ELSE 'external'
    END as team_type,
    pt.is_active,
    c.relationship_quality,
    c.expertise,
    pt.notes
FROM project_team pt
LEFT JOIN contacts c ON pt.contact_id = c.contact_id
LEFT JOIN staff s ON pt.staff_id = s.staff_id
LEFT JOIN project_role_types prt ON pt.role_type_id = prt.id;

-- ============================================================================
-- VIEW: Find consultants available for projects
-- ============================================================================

CREATE VIEW IF NOT EXISTS v_available_consultants AS
SELECT
    c.contact_id,
    c.name,
    c.company,
    c.expertise,
    c.relationship_quality,
    c.relationship_notes,
    c.recommend_for,
    prt.role_name as typical_role,
    COUNT(DISTINCT pt.project_code) as active_projects
FROM contacts c
LEFT JOIN project_team pt ON c.contact_id = pt.contact_id AND pt.is_active = 1
LEFT JOIN contact_expertise ce ON c.contact_id = ce.contact_id
LEFT JOIN expertise_areas ea ON ce.expertise_id = ea.id
LEFT JOIN project_role_types prt ON prt.role_name LIKE '%' || ea.name || '%'
WHERE c.contact_type = 'consultant'
AND c.is_active = 1
GROUP BY c.contact_id;

-- ============================================================================
-- EXAMPLE: Adding team to a project
-- ============================================================================
--
-- -- Add owner
-- INSERT INTO project_team (project_code, contact_id, role_type_id, company)
-- SELECT '25 BK-087', contact_id,
--     (SELECT id FROM project_role_types WHERE role_name = 'Owner'),
--     'Pearl Resorts'
-- FROM contacts WHERE name = 'Romain Debray';
--
-- -- Add BENSLEY team member
-- INSERT INTO project_team (project_code, staff_id, role_type_id)
-- SELECT '25 BK-087', staff_id,
--     (SELECT id FROM project_role_types WHERE role_name = 'Design Director')
-- FROM staff WHERE nickname = 'Bill';
--
-- -- Add external consultant
-- INSERT INTO project_team (project_code, contact_id, role_type_id, company, notes)
-- SELECT '25 BK-087', contact_id,
--     (SELECT id FROM project_role_types WHERE role_name = 'Guest Experience'),
--     'Jason Friedman Consulting',
--     'Recommended for F&B experience curation'
-- FROM contacts WHERE name = 'Jason Friedman';
