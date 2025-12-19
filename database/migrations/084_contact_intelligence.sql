-- Migration 084: Contact Intelligence Schema
-- Enables relationship tracking, expertise matching, and AI recommendations
-- Run: sqlite3 database/bensley_master.db < database/migrations/084_contact_intelligence.sql

-- ============================================================================
-- CONTACT TYPE ENUM (conceptual - stored as TEXT)
-- ============================================================================
-- client          = someone who hires us (decision maker at client company)
-- consultant      = external expert we recommend/work with (like Jason Friedman)
-- vendor          = suppliers, contractors, fabricators
-- partner         = strategic partners, JV partners
-- investor        = investors, developers, asset owners
-- architect       = external architects we collaborate with
-- internal        = BENSLEY staff (use staff table instead)
-- other           = miscellaneous

-- ============================================================================
-- ENHANCED CONTACTS TABLE
-- ============================================================================

-- Add new columns to contacts
ALTER TABLE contacts ADD COLUMN contact_type TEXT DEFAULT 'client';
ALTER TABLE contacts ADD COLUMN expertise TEXT;  -- JSON array: ["guest experience", "F&B", "spa design"]
ALTER TABLE contacts ADD COLUMN relationship_quality TEXT;  -- excellent, good, neutral, difficult, avoid
ALTER TABLE contacts ADD COLUMN relationship_notes TEXT;  -- "Amazing to work with, always delivers"
ALTER TABLE contacts ADD COLUMN recommend_for TEXT;  -- JSON array: ["experience design", "F&B concepts"]
ALTER TABLE contacts ADD COLUMN years_known INTEGER;  -- How long we've worked together
ALTER TABLE contacts ADD COLUMN introduced_by TEXT;  -- Who introduced them to us
ALTER TABLE contacts ADD COLUMN linkedin_url TEXT;
ALTER TABLE contacts ADD COLUMN location TEXT;  -- City, Country
ALTER TABLE contacts ADD COLUMN last_interaction_date TEXT;
ALTER TABLE contacts ADD COLUMN interaction_count INTEGER DEFAULT 0;
ALTER TABLE contacts ADD COLUMN is_active INTEGER DEFAULT 1;  -- Still in touch?
ALTER TABLE contacts ADD COLUMN tags TEXT;  -- JSON array for flexible tagging

-- ============================================================================
-- CONTACT-PROJECT RELATIONSHIPS (many-to-many)
-- ============================================================================

CREATE TABLE IF NOT EXISTS contact_project_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    project_code TEXT,  -- Can be proposal or project
    role_on_project TEXT,  -- "Client Lead", "Consultant", "Contractor", "Introduced us"
    start_date TEXT,
    end_date TEXT,
    outcome TEXT,  -- "successful", "ongoing", "cancelled", "difficult"
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
);

CREATE INDEX IF NOT EXISTS idx_contact_project_history_contact ON contact_project_history(contact_id);
CREATE INDEX IF NOT EXISTS idx_contact_project_history_project ON contact_project_history(project_code);

-- ============================================================================
-- CONTACT RELATIONSHIPS (who knows who)
-- ============================================================================

CREATE TABLE IF NOT EXISTS contact_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id_1 INTEGER NOT NULL,
    contact_id_2 INTEGER NOT NULL,
    relationship_type TEXT,  -- "colleague", "boss", "reports_to", "spouse", "introduced", "knows"
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id_1) REFERENCES contacts(contact_id),
    FOREIGN KEY (contact_id_2) REFERENCES contacts(contact_id)
);

-- ============================================================================
-- EXPERTISE AREAS (for AI matching)
-- ============================================================================

CREATE TABLE IF NOT EXISTS expertise_areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,  -- "guest experience", "F&B design", "spa consulting"
    category TEXT,  -- "consulting", "design", "operations", "technical"
    description TEXT,
    keywords TEXT,  -- JSON array of related terms for matching
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Seed common expertise areas
INSERT OR IGNORE INTO expertise_areas (name, category, keywords) VALUES
    ('guest experience', 'consulting', '["guest journey", "experience design", "touchpoints", "moments", "curation"]'),
    ('F&B design', 'design', '["restaurant", "bar", "kitchen", "dining", "food and beverage"]'),
    ('F&B consulting', 'consulting', '["restaurant concept", "menu", "culinary", "chef"]'),
    ('spa design', 'design', '["wellness", "spa", "treatment rooms", "relaxation"]'),
    ('spa consulting', 'consulting', '["wellness programs", "treatments", "spa operations"]'),
    ('landscape architecture', 'design', '["gardens", "outdoor", "planting", "hardscape"]'),
    ('interior design', 'design', '["interiors", "FF&E", "furniture", "finishes"]'),
    ('architecture', 'design', '["buildings", "structures", "masterplan"]'),
    ('lighting design', 'design', '["lighting", "fixtures", "ambiance", "illumination"]'),
    ('branding', 'consulting', '["brand", "identity", "naming", "positioning"]'),
    ('hotel operations', 'consulting', '["hotel management", "operations", "standards"]'),
    ('development', 'consulting', '["real estate", "feasibility", "pro forma", "investment"]'),
    ('project management', 'consulting', '["PM", "construction management", "coordination"]'),
    ('procurement', 'consulting', '["FF&E procurement", "sourcing", "purchasing"]'),
    ('art curation', 'consulting', '["artwork", "art program", "sculptures", "installations"]'),
    ('sustainability', 'consulting', '["green", "LEED", "sustainable", "eco", "environmental"]');

-- ============================================================================
-- CONTACT EXPERTISE MAPPING (many-to-many)
-- ============================================================================

CREATE TABLE IF NOT EXISTS contact_expertise (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    expertise_id INTEGER NOT NULL,
    proficiency TEXT DEFAULT 'expert',  -- expert, proficient, familiar
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id),
    FOREIGN KEY (expertise_id) REFERENCES expertise_areas(id),
    UNIQUE(contact_id, expertise_id)
);

-- ============================================================================
-- RECOMMENDATIONS LOG (track AI suggestions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS contact_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    project_code TEXT,
    recommendation_reason TEXT,  -- "expertise in guest experience matches client need"
    recommended_by TEXT,  -- "ai" or staff name
    status TEXT DEFAULT 'suggested',  -- suggested, contacted, engaged, declined
    outcome TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
);

-- ============================================================================
-- VIEWS FOR AI QUERIES
-- ============================================================================

-- View: Find consultants by expertise
CREATE VIEW IF NOT EXISTS v_consultants_by_expertise AS
SELECT
    c.contact_id,
    c.name,
    c.company,
    c.contact_type,
    c.expertise,
    c.relationship_quality,
    c.relationship_notes,
    c.recommend_for,
    c.years_known,
    e.name as expertise_area,
    e.category as expertise_category,
    ce.proficiency
FROM contacts c
LEFT JOIN contact_expertise ce ON c.contact_id = ce.contact_id
LEFT JOIN expertise_areas e ON ce.expertise_id = e.id
WHERE c.contact_type IN ('consultant', 'partner', 'vendor')
AND c.is_active = 1;

-- View: Contact with project count
CREATE VIEW IF NOT EXISTS v_contact_project_summary AS
SELECT
    c.contact_id,
    c.name,
    c.company,
    c.contact_type,
    c.relationship_quality,
    COUNT(DISTINCT cph.project_code) as project_count,
    GROUP_CONCAT(DISTINCT cph.project_code) as projects,
    MAX(cph.start_date) as last_project_date
FROM contacts c
LEFT JOIN contact_project_history cph ON c.contact_id = cph.contact_id
GROUP BY c.contact_id;

-- ============================================================================
-- EXAMPLE: How to add Jason Friedman
-- ============================================================================
--
-- INSERT INTO contacts (name, email, contact_type, company, expertise,
--     relationship_quality, relationship_notes, recommend_for, years_known, location)
-- VALUES (
--     'Jason Friedman',
--     'jason@example.com',
--     'consultant',
--     'Friedman Hospitality',
--     '["guest experience", "F&B curation", "hospitality consulting"]',
--     'excellent',
--     'Amazing consultant, worked together for 10+ years. Go-to for guest experience design.',
--     '["experience design", "F&B concepts", "service design", "guest journey mapping"]',
--     10,
--     'USA'
-- );
--
-- -- Link expertise
-- INSERT INTO contact_expertise (contact_id, expertise_id, proficiency)
-- SELECT
--     (SELECT contact_id FROM contacts WHERE name = 'Jason Friedman'),
--     id,
--     'expert'
-- FROM expertise_areas WHERE name IN ('guest experience', 'F&B consulting');
