-- Migration 067: Complete Categories for Bill's Universe
-- Creates master category table for multi-tag email categorization
-- Part of Phase 2.0: Context-Aware Multi-Tag System

-- Master category table
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    category_code TEXT UNIQUE NOT NULL,  -- 'INT-FIN', 'SM-WILD', etc.
    category_name TEXT NOT NULL,
    parent_code TEXT,                     -- 'INT' for 'INT-FIN', NULL for top-level
    category_type TEXT NOT NULL,          -- 'design', 'internal', 'shinta_mani', 'personal', 'marketing', 'skip'
    description TEXT,
    access_level TEXT DEFAULT 'management',
    is_active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert all categories

-- Design Business (links to project codes like 25 BK-033)
INSERT OR IGNORE INTO categories (category_code, category_name, parent_code, category_type, description, sort_order) VALUES
('BDS', 'Design Business', NULL, 'design', 'Bensley Design Studios - active proposals and projects. Links to specific project codes like 25 BK-033.', 1);

-- Internal Operations
INSERT OR IGNORE INTO categories (category_code, category_name, parent_code, category_type, description, sort_order) VALUES
('INT', 'Internal Operations', NULL, 'internal', 'Bensley internal operations - not project-specific', 10),
('INT-FIN', 'Finance', 'INT', 'internal', 'Taxes, accounting, invoices, payments, financial reports', 11),
('INT-OPS', 'IT/Systems', 'INT', 'internal', 'Email setup, software, BOS, NaviWorld, D365, IT support', 12),
('INT-HR', 'Human Resources', 'INT', 'internal', 'Hiring, policies, team management, benefits', 13),
('INT-LEGAL', 'Legal', 'INT', 'internal', 'Contracts for Bensley itself, IP, compliance, corporate legal', 14),
('INT-SCHED', 'Scheduling', 'INT', 'internal', 'PM scheduling, site visits, team calendars, resource planning', 15),
('INT-DAILY', 'Daily Work', 'INT', 'internal', 'Team updates, progress reports, internal communications', 16);

-- Shinta Mani Hotels (Bill OWNS these - NOT design projects)
INSERT OR IGNORE INTO categories (category_code, category_name, parent_code, category_type, description, sort_order) VALUES
('SM', 'Shinta Mani Hotels', NULL, 'shinta_mani', 'Bill''s hotel ownership - P&L, operations, not design work', 20),
('SM-WILD', 'Shinta Mani Wild', 'SM', 'shinta_mani', 'Shinta Mani Wild operations, bookings, P&L', 21),
('SM-MUSTANG', 'Shinta Mani Mustang', 'SM', 'shinta_mani', 'Shinta Mani Mustang operations, bookings, P&L', 22),
('SM-ANGKOR', 'Shinta Mani Angkor', 'SM', 'shinta_mani', 'Shinta Mani Angkor operations, bookings, P&L', 23),
('SM-FOUNDATION', 'Shinta Mani Foundation', 'SM', 'shinta_mani', 'Charity foundation, monthly reports, donations', 24);

-- Personal (Bill)
INSERT OR IGNORE INTO categories (category_code, category_name, parent_code, category_type, description, sort_order) VALUES
('PERS', 'Personal', NULL, 'personal', 'Bill''s personal matters', 30),
('PERS-ART', 'Gallery/Art', 'PERS', 'personal', 'Bill''s art gallery, paintings, exhibitions, art sales', 31),
('PERS-INVEST', 'Investments', 'PERS', 'personal', 'Land sales, property investments, personal deals', 32),
('PERS-FAMILY', 'Family', 'PERS', 'personal', 'Personal family correspondence', 33),
('PERS-PRESS', 'Press/Speaking', 'PERS', 'personal', 'Interviews, speaking engagements, lectures', 34);

-- Marketing/Brand
INSERT OR IGNORE INTO categories (category_code, category_name, parent_code, category_type, description, sort_order) VALUES
('MKT', 'Marketing/Brand', NULL, 'marketing', 'Brand and marketing activities', 40),
('MKT-SOCIAL', 'Social Media', 'MKT', 'marketing', 'Instagram, content creation, engagement metrics', 41),
('MKT-PRESS', 'Press Coverage', 'MKT', 'marketing', 'Articles, features, awards, media coverage', 42),
('MKT-WEB', 'Website', 'MKT', 'marketing', 'Website analytics, updates, SEO', 43);

-- Skip (truly irrelevant)
INSERT OR IGNORE INTO categories (category_code, category_name, parent_code, category_type, description, sort_order) VALUES
('SKIP', 'Skip/Ignore', NULL, 'skip', 'Emails to skip - spam, automated, duplicates', 90),
('SKIP-SPAM', 'Spam', 'SKIP', 'skip', 'Marketing spam, newsletters, unwanted solicitations', 91),
('SKIP-AUTO', 'Automated', 'SKIP', 'skip', 'System notifications we don''t need to track', 92),
('SKIP-DUP', 'Duplicate', 'SKIP', 'skip', 'Already processed or duplicate content', 93);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_categories_code ON categories(category_code);
CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_code);
CREATE INDEX IF NOT EXISTS idx_categories_type ON categories(category_type);
CREATE INDEX IF NOT EXISTS idx_categories_active ON categories(is_active);

-- Create update trigger
CREATE TRIGGER IF NOT EXISTS trg_categories_updated_at
AFTER UPDATE ON categories
BEGIN
    UPDATE categories SET updated_at = datetime('now') WHERE category_id = NEW.category_id;
END;

-- Migration complete marker
INSERT OR IGNORE INTO schema_migrations (version, name, description, applied_at)
VALUES (67, '067_complete_categories', 'Complete categories for Bill universe', datetime('now'));
