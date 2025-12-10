-- Migration 068: Email Tags - Multi-Tag System
-- Allows each email to have multiple tags for comprehensive categorization
-- Part of Phase 2.0: Context-Aware Multi-Tag System

-- Multi-tag link table (one email can have MANY tags)
CREATE TABLE IF NOT EXISTS email_tags (
    tag_id INTEGER PRIMARY KEY,
    email_id INTEGER NOT NULL,
    category_code TEXT NOT NULL,          -- 'INT-FIN', '25 BK-033', 'SM-WILD'
    tag_type TEXT NOT NULL CHECK(tag_type IN (
        'primary',      -- Main category (BDS, INT, SM, PERS, MKT, SKIP)
        'secondary',    -- Subcategory (INT-FIN, SM-WILD, etc.)
        'project',      -- Project/proposal link (25 BK-033)
        'action'        -- Action type (invoice, scheduling, status_update)
    )),
    confidence REAL DEFAULT 0.5 CHECK(confidence >= 0 AND confidence <= 1),
    source TEXT DEFAULT 'ai' CHECK(source IN ('ai', 'user', 'pattern', 'rule')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (email_id) REFERENCES emails(email_id) ON DELETE CASCADE
);

-- Add categorization columns to emails table
-- Note: SQLite doesn't support ADD COLUMN IF NOT EXISTS, so we use a trick
-- by checking if column exists first

-- primary_category - main bucket (BDS, INT, SM, PERS, MKT, SKIP)
ALTER TABLE emails ADD COLUMN primary_category TEXT;

-- is_categorized - flag for whether email has been categorized
ALTER TABLE emails ADD COLUMN is_categorized BOOLEAN DEFAULT 0;

-- categorized_at - when categorization happened
ALTER TABLE emails ADD COLUMN categorized_at TIMESTAMP;

-- categorized_by - who/what categorized (ai, user, pattern)
ALTER TABLE emails ADD COLUMN categorized_by TEXT;

-- Create indexes for email_tags
CREATE INDEX IF NOT EXISTS idx_email_tags_email_id ON email_tags(email_id);
CREATE INDEX IF NOT EXISTS idx_email_tags_category ON email_tags(category_code);
CREATE INDEX IF NOT EXISTS idx_email_tags_type ON email_tags(tag_type);
CREATE INDEX IF NOT EXISTS idx_email_tags_source ON email_tags(source);
CREATE INDEX IF NOT EXISTS idx_email_tags_confidence ON email_tags(confidence DESC);

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_email_tags_email_type ON email_tags(email_id, tag_type);
CREATE INDEX IF NOT EXISTS idx_email_tags_category_type ON email_tags(category_code, tag_type);

-- Create indexes on new emails columns
CREATE INDEX IF NOT EXISTS idx_emails_primary_category ON emails(primary_category);
CREATE INDEX IF NOT EXISTS idx_emails_is_categorized ON emails(is_categorized);

-- Update trigger for email_tags
CREATE TRIGGER IF NOT EXISTS trg_email_tags_updated_at
AFTER UPDATE ON email_tags
BEGIN
    UPDATE email_tags SET updated_at = datetime('now') WHERE tag_id = NEW.tag_id;
END;

-- Migration complete marker
INSERT OR IGNORE INTO schema_migrations (version, name, description, applied_at)
VALUES (68, '068_email_tags', 'Email tags multi-tag system', datetime('now'));
