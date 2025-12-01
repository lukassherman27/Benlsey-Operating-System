-- Migration: 050_email_category_system.sql
-- Purpose: Create email category system with master categories, pattern rules, and uncategorized handling
-- Date: 2025-12-01

-- ============================================================================
-- 1. email_categories - Master list of all email categories
-- ============================================================================
CREATE TABLE IF NOT EXISTS email_categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,                           -- e.g., 'internal_scheduling', 'client_communication'
    description TEXT,                                     -- Human-readable description
    is_system INTEGER DEFAULT 0,                          -- 1 = built-in category, 0 = user/AI created
    parent_category_id INTEGER REFERENCES email_categories(category_id),  -- For hierarchy
    display_order INTEGER DEFAULT 100,                    -- For UI sorting
    color TEXT,                                           -- UI color code (optional)
    icon TEXT,                                            -- UI icon name (optional)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system'                      -- 'system', 'user', 'ai_suggested'
);

CREATE INDEX IF NOT EXISTS idx_email_categories_name ON email_categories(name);
CREATE INDEX IF NOT EXISTS idx_email_categories_parent ON email_categories(parent_category_id);
CREATE INDEX IF NOT EXISTS idx_email_categories_system ON email_categories(is_system);

-- ============================================================================
-- 2. email_category_rules - Pattern matching rules for auto-categorization
-- ============================================================================
CREATE TABLE IF NOT EXISTS email_category_rules (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES email_categories(category_id) ON DELETE CASCADE,
    rule_type TEXT NOT NULL CHECK(rule_type IN ('sender_domain', 'sender_email', 'subject_pattern', 'body_pattern', 'recipient_pattern')),
    pattern TEXT NOT NULL,                               -- Regex or exact match pattern
    is_regex INTEGER DEFAULT 0,                          -- 1 = regex, 0 = exact/LIKE match
    confidence REAL DEFAULT 0.8,                         -- How reliable is this rule (0-1)
    priority INTEGER DEFAULT 50,                         -- Higher = checked first
    hit_count INTEGER DEFAULT 0,                         -- Times this rule matched
    last_hit_at DATETIME,                                -- Last time this rule matched
    is_active INTEGER DEFAULT 1,                         -- 1 = active, 0 = disabled
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    learned_from TEXT DEFAULT 'manual'                   -- 'manual', 'ai_analysis', 'user_feedback'
);

CREATE INDEX IF NOT EXISTS idx_email_category_rules_category ON email_category_rules(category_id);
CREATE INDEX IF NOT EXISTS idx_email_category_rules_type ON email_category_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_email_category_rules_active ON email_category_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_email_category_rules_priority ON email_category_rules(priority DESC);

-- ============================================================================
-- 3. uncategorized_emails - Bucket for emails that don't match any rules
-- ============================================================================
CREATE TABLE IF NOT EXISTS uncategorized_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL UNIQUE REFERENCES emails(email_id) ON DELETE CASCADE,
    suggested_category_id INTEGER REFERENCES email_categories(category_id),  -- AI's best guess
    suggested_category_reason TEXT,                      -- Why AI suggested this
    confidence_score REAL,                               -- AI's confidence in suggestion
    reviewed INTEGER DEFAULT 0,                          -- 1 = human reviewed
    reviewed_by TEXT,                                    -- Who reviewed
    reviewed_at DATETIME,                                -- When reviewed
    final_category_id INTEGER REFERENCES email_categories(category_id),  -- What human chose
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_uncategorized_emails_email ON uncategorized_emails(email_id);
CREATE INDEX IF NOT EXISTS idx_uncategorized_emails_reviewed ON uncategorized_emails(reviewed);
CREATE INDEX IF NOT EXISTS idx_uncategorized_emails_suggested ON uncategorized_emails(suggested_category_id);
CREATE INDEX IF NOT EXISTS idx_uncategorized_emails_created ON uncategorized_emails(created_at DESC);

-- ============================================================================
-- 4. email_category_history - Track category changes for learning
-- ============================================================================
CREATE TABLE IF NOT EXISTS email_category_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL REFERENCES emails(email_id) ON DELETE CASCADE,
    old_category_id INTEGER REFERENCES email_categories(category_id),
    new_category_id INTEGER REFERENCES email_categories(category_id),
    changed_by TEXT NOT NULL,                            -- 'ai', 'user', 'rule'
    change_reason TEXT,                                  -- Why the change was made
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_email_category_history_email ON email_category_history(email_id);
CREATE INDEX IF NOT EXISTS idx_email_category_history_created ON email_category_history(created_at DESC);

-- ============================================================================
-- 5. Insert default system categories
-- ============================================================================
INSERT OR IGNORE INTO email_categories (name, description, is_system, display_order, created_by) VALUES
    ('internal_scheduling', 'Bensley internal scheduling, meetings, calendar invites', 1, 10, 'system'),
    ('internal_operations', 'HR, admin, office operations, internal announcements', 1, 20, 'system'),
    ('client_communication', 'Direct communication with clients', 1, 30, 'system'),
    ('project_design', 'Design discussions, reviews, presentations', 1, 40, 'system'),
    ('project_financial', 'Invoices, payments, fees, budgets', 1, 50, 'system'),
    ('project_contracts', 'Legal, contracts, agreements, proposals', 1, 60, 'system'),
    ('vendor_supplier', 'External vendors, suppliers, contractors', 1, 70, 'system'),
    ('marketing_outreach', 'New business, cold outreach, marketing', 1, 80, 'system'),
    ('personal', 'Non-work related, personal emails', 1, 90, 'system'),
    ('automated_notification', 'System emails, newsletters, automated notifications', 1, 100, 'system');

-- ============================================================================
-- 6. Insert some default categorization rules
-- ============================================================================

-- Internal scheduling rules (Bensley domain + meeting keywords)
INSERT OR IGNORE INTO email_category_rules (category_id, rule_type, pattern, confidence, priority, learned_from)
SELECT category_id, 'sender_domain', '@bensleydesign.com', 0.7, 60, 'system'
FROM email_categories WHERE name = 'internal_scheduling';

INSERT OR IGNORE INTO email_category_rules (category_id, rule_type, pattern, is_regex, confidence, priority, learned_from)
SELECT category_id, 'subject_pattern', '(?i)(meeting|calendar|invite|zoom|teams)', 1, 0.8, 70, 'system'
FROM email_categories WHERE name = 'internal_scheduling';

-- Automated notifications (common patterns)
INSERT OR IGNORE INTO email_category_rules (category_id, rule_type, pattern, is_regex, confidence, priority, learned_from)
SELECT category_id, 'sender_email', '(?i)(noreply|no-reply|notifications|automated|system)', 1, 0.9, 80, 'system'
FROM email_categories WHERE name = 'automated_notification';

INSERT OR IGNORE INTO email_category_rules (category_id, rule_type, pattern, is_regex, confidence, priority, learned_from)
SELECT category_id, 'sender_domain', '(?i)(newsletter|mailchimp|sendgrid|mailgun)', 1, 0.85, 75, 'system'
FROM email_categories WHERE name = 'automated_notification';

-- Project financial rules
INSERT OR IGNORE INTO email_category_rules (category_id, rule_type, pattern, is_regex, confidence, priority, learned_from)
SELECT category_id, 'subject_pattern', '(?i)(invoice|payment|receipt|fee|billing|quote)', 1, 0.85, 70, 'system'
FROM email_categories WHERE name = 'project_financial';

-- Project contracts rules
INSERT OR IGNORE INTO email_category_rules (category_id, rule_type, pattern, is_regex, confidence, priority, learned_from)
SELECT category_id, 'subject_pattern', '(?i)(contract|agreement|proposal|mou|nda|terms)', 1, 0.85, 70, 'system'
FROM email_categories WHERE name = 'project_contracts';

-- Project design rules
INSERT OR IGNORE INTO email_category_rules (category_id, rule_type, pattern, is_regex, confidence, priority, learned_from)
SELECT category_id, 'subject_pattern', '(?i)(design|concept|schematic|drawing|render|review|presentation)', 1, 0.75, 65, 'system'
FROM email_categories WHERE name = 'project_design';

-- ============================================================================
-- 7. Create view for easy category analysis
-- ============================================================================
CREATE VIEW IF NOT EXISTS v_email_category_stats AS
SELECT
    ec.category_id,
    ec.name,
    ec.description,
    ec.is_system,
    COUNT(DISTINCT ecr.rule_id) as rule_count,
    COALESCE(SUM(ecr.hit_count), 0) as total_hits,
    (SELECT COUNT(*) FROM email_content WHERE category = ec.name) as email_count
FROM email_categories ec
LEFT JOIN email_category_rules ecr ON ec.category_id = ecr.category_id AND ecr.is_active = 1
GROUP BY ec.category_id;

-- ============================================================================
-- 8. Create view for uncategorized emails needing review
-- ============================================================================
CREATE VIEW IF NOT EXISTS v_uncategorized_for_review AS
SELECT
    ue.id,
    ue.email_id,
    e.subject,
    e.sender_email,
    e.date,
    e.snippet,
    ue.suggested_category_id,
    ec.name as suggested_category_name,
    ue.suggested_category_reason,
    ue.confidence_score,
    ue.created_at
FROM uncategorized_emails ue
JOIN emails e ON ue.email_id = e.email_id
LEFT JOIN email_categories ec ON ue.suggested_category_id = ec.category_id
WHERE ue.reviewed = 0
ORDER BY ue.created_at DESC;
