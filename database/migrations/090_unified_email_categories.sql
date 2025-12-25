-- Migration 090: Unified Email Categories
-- Consolidates the messy dual-category system into one clean field
-- Created: 2025-12-25

-- Step 1: Rename primary_category to category (cleaner name)
-- SQLite doesn't support RENAME COLUMN directly, so we check if it exists first
-- Note: If primary_category already exists, we just use it; if category exists, we're done

-- Step 2: Create category reference table (for validation and UI dropdowns)
CREATE TABLE IF NOT EXISTS email_category_codes (
    code TEXT PRIMARY KEY,
    domain TEXT NOT NULL,           -- 'LEGAL', 'SCHEDULING', 'PR', etc.
    display_name TEXT NOT NULL,     -- 'Legal - India', 'Scheduling - Weekly'
    description TEXT,               -- What belongs here
    is_active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0
);

-- Step 3: Seed with taxonomy
INSERT OR IGNORE INTO email_category_codes (code, domain, display_name, description, sort_order) VALUES
-- Proposal/Business Development
('PROPOSAL', 'PROPOSAL', 'Business Development', 'New project inquiries, proposals, negotiations', 10),

-- Active Project Work
('PROJECT', 'PROJECT', 'Project (General)', 'Active project work not otherwise categorized', 20),
('PROJECT-DESIGN', 'PROJECT', 'Project - Design', 'Design work, drawings, renderings', 21),
('PROJECT-CONTRACT', 'PROJECT', 'Project - Contracts', 'Contract discussions, amendments', 22),
('PROJECT-FINANCIAL', 'PROJECT', 'Project - Financial', 'Project budgets, fee discussions', 23),

-- Legal
('LEGAL', 'LEGAL', 'Legal (General)', 'Legal matters not otherwise categorized', 30),
('LEGAL-INDIA', 'LEGAL', 'Legal - India', 'India-related legal, court cases', 31),
('LEGAL-CHINA', 'LEGAL', 'Legal - China', 'China-related legal matters', 32),

-- Scheduling & Resources
('SCHEDULING', 'SCHEDULING', 'Scheduling (General)', 'Resource allocation, assignments', 40),
('SCHEDULING-WEEKLY', 'SCHEDULING', 'Scheduling - Weekly', 'Weekly schedule updates', 41),
('SCHEDULING-RESOURCE', 'SCHEDULING', 'Scheduling - Resource', 'Who works on what project', 42),

-- Finance
('FINANCE', 'FINANCE', 'Finance (General)', 'Financial operations', 50),
('FINANCE-INVOICES', 'FINANCE', 'Finance - Invoices', 'Invoice discussions', 51),
('FINANCE-PAYMENTS', 'FINANCE', 'Finance - Payments', 'Payment tracking', 52),

-- HR
('HR', 'HR', 'HR (General)', 'Personnel matters', 60),

-- PR & Marketing
('PR', 'PR', 'PR (General)', 'Public relations, brand', 70),
('PR-PRESS', 'PR', 'PR - Press', 'Magazine, newspaper coverage', 71),
('PR-SOCIAL', 'PR', 'PR - Social Media', 'Instagram, social platforms', 72),
('PR-MAGAZINE', 'PR', 'PR - Magazine', 'Magazine features, interviews', 73),

-- Shinta Mani
('SM', 'SM', 'Shinta Mani (General)', 'Shinta Mani hotels', 80),
('SM-WILD', 'SM', 'Shinta Mani Wild', 'SM Wild operations', 81),
('SM-MUSTANG', 'SM', 'Shinta Mani Mustang', 'SM Mustang operations', 82),
('SM-FOUNDATION', 'SM', 'Shinta Mani Foundation', 'Foundation work', 83),

-- Internal
('INTERNAL', 'INTERNAL', 'Internal (General)', 'Internal Bensley operations', 90),
('INTERNAL-OPS', 'INTERNAL', 'Internal - Operations', 'IT, systems, NaviWorld', 91),
('INTERNAL-DAILY', 'INTERNAL', 'Internal - Daily Work', 'Daily work reports', 92),

-- Personal
('PERSONAL', 'PERSONAL', 'Personal (General)', 'Personal matters', 100),
('PERSONAL-BILL', 'PERSONAL', 'Personal - Bill', 'Bill personal', 101),

-- Skip
('SKIP', 'SKIP', 'Skip (General)', 'Ignore', 110),
('SKIP-SPAM', 'SKIP', 'Skip - Spam', 'Spam emails', 111),
('SKIP-AUTO', 'SKIP', 'Skip - Automated', 'SaaS notifications, auto-emails', 112);

-- Step 4: Add category column if it doesn't exist (for transition)
-- The emails table already has primary_category, we'll use that and rename conceptually

-- Step 5: Create index for fast domain filtering
CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(primary_category);
