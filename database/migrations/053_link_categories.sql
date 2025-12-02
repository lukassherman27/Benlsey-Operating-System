-- Migration 053: Link Categories System
-- Allows flexible categorization of emails, contacts, transcripts beyond just project/proposal codes

-- Categories table for organizing links
CREATE TABLE IF NOT EXISTS link_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category_type TEXT NOT NULL DEFAULT 'custom',  -- 'project', 'proposal', 'internal', 'brand', 'client', 'custom'
    description TEXT,
    color TEXT DEFAULT '#6366f1',  -- Hex color for UI display
    icon TEXT DEFAULT 'folder',    -- Icon name for UI
    is_active INTEGER DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed with some default categories based on user's examples
INSERT OR IGNORE INTO link_categories (name, category_type, description, color, icon, sort_order) VALUES
    ('Internal Bensley', 'internal', 'Internal company communications and scheduling', '#3b82f6', 'building', 10),
    ('Shinta Mani', 'brand', 'Shinta Mani brand/hotel related', '#8b5cf6', 'star', 20),
    ('Marketing', 'internal', 'Marketing and promotional content', '#ec4899', 'megaphone', 30),
    ('HR / Admin', 'internal', 'Human resources and administrative', '#f59e0b', 'users', 40),
    ('Vendor / Supplier', 'external', 'Vendor and supplier communications', '#10b981', 'truck', 50),
    ('Spam / Irrelevant', 'system', 'Spam or irrelevant emails to ignore', '#6b7280', 'trash', 100);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_link_categories_type ON link_categories(category_type);
CREATE INDEX IF NOT EXISTS idx_link_categories_active ON link_categories(is_active);

-- Extend email_links to support category assignment
-- Note: email_project_links already has project_code, we add category_id as alternative
ALTER TABLE email_project_links ADD COLUMN category_id INTEGER REFERENCES link_categories(id);
ALTER TABLE email_project_links ADD COLUMN link_type TEXT DEFAULT 'project';  -- 'project', 'proposal', 'category'

-- Extend contact assignments similarly
ALTER TABLE project_contact_assignments ADD COLUMN category_id INTEGER REFERENCES link_categories(id);
ALTER TABLE project_contact_assignments ADD COLUMN assignment_type TEXT DEFAULT 'project';

-- Track category usage for learning
CREATE TABLE IF NOT EXISTS category_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES link_categories(id),
    pattern_type TEXT NOT NULL,  -- 'sender', 'domain', 'subject_keyword'
    pattern_value TEXT NOT NULL,
    confidence REAL DEFAULT 0.8,
    match_count INTEGER DEFAULT 1,
    created_by TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category_id, pattern_type, pattern_value)
);

CREATE INDEX IF NOT EXISTS idx_category_patterns_lookup ON category_patterns(pattern_type, pattern_value);
