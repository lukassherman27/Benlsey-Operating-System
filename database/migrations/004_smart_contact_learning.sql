-- Migration 004: Smart Contact Learning System
-- Adds intelligent contact tracking with multi-project support

-- Contacts table - one entry per unique person
CREATE TABLE IF NOT EXISTS project_contacts (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_address TEXT UNIQUE NOT NULL,
    full_name TEXT,
    company TEXT,
    phone TEXT,
    is_internal INTEGER DEFAULT 0,  -- 1 for @bensley.com staff
    first_seen TEXT,
    last_contact TEXT,
    total_emails INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Many-to-many: Contacts work on multiple projects
CREATE TABLE IF NOT EXISTS project_contact_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    contact_id INTEGER NOT NULL,
    role TEXT,  -- 'client', 'consultant', 'contractor', 'operator', 'internal'
    email_count INTEGER DEFAULT 0,
    confidence_score REAL DEFAULT 0.5,
    first_linked TEXT DEFAULT (datetime('now')),
    last_activity TEXT DEFAULT (datetime('now')),
    notes TEXT,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    FOREIGN KEY (contact_id) REFERENCES project_contacts(contact_id),
    UNIQUE(proposal_id, contact_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_contacts_email ON project_contacts(email_address);
CREATE INDEX IF NOT EXISTS idx_contact_links_proposal ON project_contact_links(proposal_id);
CREATE INDEX IF NOT EXISTS idx_contact_links_contact ON project_contact_links(contact_id);
CREATE INDEX IF NOT EXISTS idx_contacts_internal ON project_contacts(is_internal);

-- View: Projects with their contacts
CREATE VIEW IF NOT EXISTS project_contacts_view AS
SELECT
    p.project_code,
    p.project_name,
    c.full_name,
    c.email_address,
    c.company,
    c.is_internal,
    l.role,
    l.email_count,
    l.confidence_score,
    l.last_activity
FROM project_contact_links l
JOIN proposals p ON l.proposal_id = p.proposal_id
JOIN project_contacts c ON l.contact_id = c.contact_id
ORDER BY p.project_code, l.email_count DESC;

-- View: Contacts with all their projects
CREATE VIEW IF NOT EXISTS contact_projects_view AS
SELECT
    c.full_name,
    c.email_address,
    c.company,
    c.is_internal,
    GROUP_CONCAT(p.project_code, ', ') as projects,
    COUNT(p.project_code) as project_count,
    SUM(l.email_count) as total_emails
FROM project_contacts c
LEFT JOIN project_contact_links l ON c.contact_id = l.contact_id
LEFT JOIN proposals p ON l.proposal_id = p.proposal_id
GROUP BY c.contact_id
ORDER BY total_emails DESC;
