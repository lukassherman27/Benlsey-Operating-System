-- Migration 007: Team Scheduling System
-- Creates tables for managing team schedules, employees, and weekly schedule reports

-- Team members (employees)
CREATE TABLE IF NOT EXISTS team_members (
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    nickname TEXT,  -- "Aood", "Moo", "Spot", etc.
    office TEXT CHECK(office IN ('Bali', 'Bangkok', 'Thailand')) NOT NULL,
    discipline TEXT CHECK(discipline IN ('Architecture', 'Interior', 'Landscape', 'Artwork', 'Management')) NOT NULL,
    is_active INTEGER DEFAULT 1,
    is_team_lead INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Weekly schedules (one per week per office)
CREATE TABLE IF NOT EXISTS weekly_schedules (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    office TEXT CHECK(office IN ('Bali', 'Bangkok')) NOT NULL,
    week_start_date TEXT NOT NULL,  -- Monday of the week (YYYY-MM-DD)
    week_end_date TEXT NOT NULL,    -- Friday of the week (YYYY-MM-DD)
    source_email_id INTEGER,        -- Reference to the email that created this
    created_by TEXT,                -- Email of person who submitted (Astuti, Aood, etc.)
    override_by TEXT,               -- If Bill overrides, his email goes here
    status TEXT CHECK(status IN ('draft', 'published', 'archived')) DEFAULT 'published',
    pdf_generated INTEGER DEFAULT 0,
    pdf_path TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (source_email_id) REFERENCES emails(email_id),
    UNIQUE(office, week_start_date)  -- One schedule per week per office
);

-- Individual schedule entries (one per person per day)
CREATE TABLE IF NOT EXISTS schedule_entries (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    work_date TEXT NOT NULL,  -- YYYY-MM-DD (Monday-Friday)

    -- Project and task details
    project_code TEXT,  -- "BK-035", "25 Downtown Mumbai", etc.
    project_name TEXT,
    discipline TEXT CHECK(discipline IN ('Architecture', 'Interior', 'Landscape', 'Artwork')),
    phase TEXT,  -- "Concept", "SD", "DD", "CD"
    task_description TEXT,  -- "Hotel - Masterplan", "3 FL Public Corridor", etc.

    -- Special statuses
    is_on_leave INTEGER DEFAULT 0,
    leave_type TEXT,  -- "Vacation / Holiday", "Mongolia Fishing", etc.
    is_unassigned INTEGER DEFAULT 0,

    -- Metadata
    raw_text TEXT,  -- Original text from email for reference
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (schedule_id) REFERENCES weekly_schedules(schedule_id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES team_members(member_id),
    UNIQUE(schedule_id, member_id, work_date)  -- One entry per person per day
);

-- Project color assignments (for PDF generation)
CREATE TABLE IF NOT EXISTS project_colors (
    color_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT UNIQUE NOT NULL,
    color_hex TEXT NOT NULL,  -- "#FF69B4" for pink, "#4CAF50" for green, etc.
    color_name TEXT,  -- "Pink", "Green", "Blue", etc.
    created_at TEXT DEFAULT (datetime('now'))
);

-- Schedule processing log
CREATE TABLE IF NOT EXISTS schedule_processing_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER,
    office TEXT,
    week_start_date TEXT,
    status TEXT CHECK(status IN ('success', 'failed', 'partial')),
    entries_created INTEGER DEFAULT 0,
    error_message TEXT,
    processed_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (email_id) REFERENCES emails(email_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_team_members_office ON team_members(office);
CREATE INDEX IF NOT EXISTS idx_team_members_discipline ON team_members(discipline);
CREATE INDEX IF NOT EXISTS idx_team_members_nickname ON team_members(nickname);
CREATE INDEX IF NOT EXISTS idx_weekly_schedules_dates ON weekly_schedules(week_start_date, week_end_date);
CREATE INDEX IF NOT EXISTS idx_schedule_entries_date ON schedule_entries(work_date);
CREATE INDEX IF NOT EXISTS idx_schedule_entries_project ON schedule_entries(project_name);
CREATE INDEX IF NOT EXISTS idx_schedule_entries_member ON schedule_entries(member_id);

-- Insert default team leads
INSERT OR IGNORE INTO team_members (email, full_name, nickname, office, discipline, is_team_lead) VALUES
    ('bensley.bali@bensley.co.id', 'Astuti', 'Astuti', 'Bali', 'Management', 1),
    ('aood@bensley.com', 'Pakheenai Saenharn', 'Aood', 'Bangkok', 'Interior', 1),
    ('moo@bensley.com', 'Natthawat Thatpakorn', 'Moo', 'Bangkok', 'Landscape', 1),
    ('bill@bensley.com', 'Bill Bensley', 'Bill', 'Bangkok', 'Management', 1),
    ('bsherman@bensley.com', 'Brian Kent Sherman', 'Brian', 'Bangkok', 'Management', 1);

-- Insert common project colors (based on the PDFs you showed me)
INSERT OR IGNORE INTO project_colors (project_name, color_hex, color_name) VALUES
    ('Cheval Blanc - Bodrum', '#FF69B4', 'Pink'),
    ('Dang Thai Mai project', '#4CAF50', 'Green'),
    ('25 Downtown Mumbai', '#00BCD4', 'Cyan'),
    ('Mandarin Oriental Bali, Indonesia', '#F5F5F5', 'Light Gray'),
    ('Capella Ubud', '#FFB6C1', 'Light Pink'),
    ('Ritz Carlton Reserve Nusa Dua', '#ADD8E6', 'Light Blue'),
    ('Tel Aviv High Rise Project in Israel', '#FFA500', 'Orange'),
    ('Villa Project in Ahmedabad, India', '#000000', 'Black'),
    ('Fenfushi', '#00008B', 'Dark Blue'),
    ('Four Seasons Rennovation', '#9370DB', 'Purple'),
    ('TARC''s Luxury Branded Residence', '#4169E1', 'Royal Blue'),
    ('St. Regis Hotel in Thousand Island', '#8B0000', 'Dark Red'),
    ('Wynn Al Marjan Island Project', '#E6E6FA', 'Lavender'),
    ('Resort Project in Udaipur, India', '#FFFF00', 'Yellow'),
    ('Pachular Estate (Shinta Mani)', '#00CED1', 'Turquoise'),
    ('Ritz Carlton Hotel Nanyan bay', '#808000', 'Olive'),
    ('Jyoti''s farm house in Delhi, India', '#CD853F', 'Peru'),
    ('Tonkin Palace', '#FF0000', 'Red');

-- Record migration
INSERT INTO schema_migrations (version, name, description) VALUES (7, '007_team_scheduling', 'Team scheduling system');
