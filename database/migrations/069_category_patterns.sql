-- Migration 069: Category Patterns for Learning
-- Enhanced pattern learning for multi-category system
-- Part of Phase 2.0: Context-Aware Multi-Tag System

-- Note: We're KEEPING email_learned_patterns (121 existing patterns)
-- This new table is specifically for CATEGORY patterns (INT-*, SM-*, etc.)
-- The existing email_learned_patterns handles project/proposal linking

CREATE TABLE IF NOT EXISTS category_patterns (
    pattern_id INTEGER PRIMARY KEY,

    -- Pattern definition
    pattern_type TEXT NOT NULL CHECK(pattern_type IN (
        'sender',       -- 'john@unanet.com' -> SKIP-SPAM
        'domain',       -- '@shintamani.com' -> SM-WILD
        'keyword',      -- 'income tax' -> INT-FIN
        'subject',      -- Subject line patterns
        'sender_name'   -- 'Bill Bensley' -> PERS (by name, not email)
    )),
    pattern_key TEXT NOT NULL,              -- The pattern to match
    pattern_key_normalized TEXT,            -- Lowercase, trimmed version

    -- What this pattern maps to
    category_code TEXT NOT NULL,            -- 'INT-FIN', 'SM-WILD', 'SKIP-SPAM'

    -- Confidence tracking
    confidence REAL DEFAULT 0.7 CHECK(confidence >= 0 AND confidence <= 1),
    times_matched INTEGER DEFAULT 0,
    times_confirmed INTEGER DEFAULT 0,
    times_rejected INTEGER DEFAULT 0,

    -- Provenance
    created_from_email_id INTEGER,
    created_by TEXT DEFAULT 'user',         -- 'user', 'ai', 'rule'
    notes TEXT,

    -- State
    is_active BOOLEAN DEFAULT 1,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_matched_at TIMESTAMP,

    -- Constraints
    UNIQUE(pattern_type, pattern_key_normalized, category_code),
    FOREIGN KEY (category_code) REFERENCES categories(category_code)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_category_patterns_key ON category_patterns(pattern_key_normalized);
CREATE INDEX IF NOT EXISTS idx_category_patterns_type ON category_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_category_patterns_category ON category_patterns(category_code);
CREATE INDEX IF NOT EXISTS idx_category_patterns_active ON category_patterns(is_active, confidence DESC);

-- Update trigger
CREATE TRIGGER IF NOT EXISTS trg_category_patterns_updated_at
AFTER UPDATE ON category_patterns
BEGIN
    UPDATE category_patterns SET updated_at = datetime('now') WHERE pattern_id = NEW.pattern_id;
END;

-- Seed some obvious category patterns we know

-- SKIP patterns (spam domains)
INSERT OR IGNORE INTO category_patterns (pattern_type, pattern_key, pattern_key_normalized, category_code, confidence, notes) VALUES
('domain', '@unanet.com', '@unanet.com', 'SKIP-SPAM', 0.95, 'Unanet timesheet system notifications'),
('domain', '@pipedrive.com', '@pipedrive.com', 'SKIP-SPAM', 0.95, 'Pipedrive CRM notifications'),
('domain', '@hubspot.com', '@hubspot.com', 'SKIP-SPAM', 0.95, 'HubSpot marketing notifications'),
('domain', '@monday.com', '@monday.com', 'SKIP-SPAM', 0.9, 'Monday.com notifications'),
('domain', '@asana.com', '@asana.com', 'SKIP-SPAM', 0.9, 'Asana notifications'),
('domain', '@zoom.us', '@zoom.us', 'SKIP-AUTO', 0.9, 'Zoom meeting notifications'),
('domain', '@dropbox.com', '@dropbox.com', 'SKIP-AUTO', 0.85, 'Dropbox share notifications'),
('keyword', 'unsubscribe', 'unsubscribe', 'SKIP-SPAM', 0.8, 'Newsletter/marketing emails');

-- Internal operations patterns
INSERT OR IGNORE INTO category_patterns (pattern_type, pattern_key, pattern_key_normalized, category_code, confidence, notes) VALUES
('domain', '@naviworld.com', '@naviworld.com', 'INT-OPS', 0.9, 'NaviWorld ERP system'),
('keyword', 'D365', 'd365', 'INT-OPS', 0.85, 'Microsoft Dynamics 365'),
('keyword', 'corporate income tax', 'corporate income tax', 'INT-FIN', 0.9, 'Tax filings'),
('keyword', 'tax filing', 'tax filing', 'INT-FIN', 0.85, 'Tax-related'),
('keyword', 'invoice payment', 'invoice payment', 'INT-FIN', 0.8, 'Financial transactions'),
('keyword', 'P&L report', 'p&l report', 'INT-FIN', 0.85, 'Profit and loss reports'),
('keyword', 'timesheet', 'timesheet', 'INT-OPS', 0.75, 'Time tracking');

-- Shinta Mani patterns
INSERT OR IGNORE INTO category_patterns (pattern_type, pattern_key, pattern_key_normalized, category_code, confidence, notes) VALUES
('domain', '@shintamani.com', '@shintamani.com', 'SM', 0.8, 'Shinta Mani hotels - needs subcategory'),
('keyword', 'Shinta Mani Wild', 'shinta mani wild', 'SM-WILD', 0.9, 'Wild hotel specifically'),
('keyword', 'Shinta Mani Mustang', 'shinta mani mustang', 'SM-MUSTANG', 0.9, 'Mustang hotel'),
('keyword', 'Shinta Mani Foundation', 'shinta mani foundation', 'SM-FOUNDATION', 0.9, 'Foundation charity');

-- Migration complete marker
INSERT OR IGNORE INTO schema_migrations (version, name, description, applied_at)
VALUES (69, '069_category_patterns', 'Category patterns for learning', datetime('now'));
