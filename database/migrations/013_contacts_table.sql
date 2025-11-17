-- Migration: Create contacts table for fast email sender lookup
-- This makes Layer 1 (fast context lookup) even better

CREATE TABLE IF NOT EXISTS contacts (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE NOT NULL,
    company TEXT,
    phone TEXT,
    role TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Link contacts to projects
CREATE TABLE IF NOT EXISTS contact_project_links (
    contact_id INTEGER,
    project_code TEXT,
    role_in_project TEXT,  -- 'client', 'consultant', 'contractor', etc.
    is_primary BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contact_id, project_code),
    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id),
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contact_project_links ON contact_project_links(contact_id, project_code);

-- Populate contacts from existing email senders
INSERT OR IGNORE INTO contacts (email, name, company)
SELECT DISTINCT
    sender_email,
    sender_name,
    NULL
FROM emails
WHERE sender_email IS NOT NULL;

-- Link contacts to projects based on existing email_project_links
INSERT OR IGNORE INTO contact_project_links (contact_id, project_code, role_in_project)
SELECT
    c.contact_id,
    epl.project_code,
    'unknown'
FROM contacts c
JOIN emails e ON c.email = e.sender_email
JOIN email_project_links epl ON e.email_id = epl.email_id;
