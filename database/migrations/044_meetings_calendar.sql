-- Migration: Create meetings table for calendar functionality
-- Created: 2025-11-26 by Agent 5 (Bensley Brain Intelligence)
-- Purpose: Store scheduled meetings for calendar view and pre-meeting briefings

-- Main meetings table
CREATE TABLE IF NOT EXISTS meetings (
    meeting_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Basic info
    title TEXT NOT NULL,
    description TEXT,
    meeting_type TEXT CHECK(meeting_type IN (
        'proposal_discussion',
        'concept_presentation',
        'design_review',
        'client_call',
        'internal',
        'site_visit',
        'contract_negotiation',
        'kickoff',
        'progress_update',
        'final_presentation',
        'other'
    )) DEFAULT 'other',

    -- Date/Time
    meeting_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    timezone TEXT DEFAULT 'Asia/Bangkok',
    is_all_day INTEGER DEFAULT 0,

    -- Location
    location TEXT,  -- "Zoom", "Office", "Client Site", etc.
    meeting_link TEXT,  -- Video call URL

    -- Project/Proposal linkage
    project_id INTEGER,
    project_code TEXT,
    proposal_id INTEGER,

    -- Participants (JSON array of contact_ids or names)
    participants TEXT,  -- JSON: [{"name": "John", "email": "john@client.com", "role": "client"}]
    organizer TEXT,

    -- Status
    status TEXT CHECK(status IN ('scheduled', 'confirmed', 'cancelled', 'completed', 'rescheduled')) DEFAULT 'scheduled',

    -- Source tracking
    source TEXT CHECK(source IN ('manual', 'email_extracted', 'chat_input', 'calendar_sync')) DEFAULT 'manual',
    source_email_id INTEGER,  -- If extracted from email
    extraction_confidence REAL,

    -- Briefing
    briefing_generated INTEGER DEFAULT 0,
    briefing_content TEXT,  -- Cached pre-meeting briefing
    briefing_generated_at DATETIME,

    -- Notes
    notes TEXT,
    agenda TEXT,  -- JSON: ["Item 1", "Item 2"]
    outcome TEXT,  -- Post-meeting notes

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',

    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    FOREIGN KEY (source_email_id) REFERENCES emails(email_id)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_meetings_date ON meetings(meeting_date);
CREATE INDEX IF NOT EXISTS idx_meetings_project ON meetings(project_code);
CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status);
CREATE INDEX IF NOT EXISTS idx_meetings_upcoming ON meetings(meeting_date, status) WHERE status IN ('scheduled', 'confirmed');

-- Meeting reminders table
CREATE TABLE IF NOT EXISTS meeting_reminders (
    reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL,
    remind_at DATETIME NOT NULL,
    reminder_type TEXT CHECK(reminder_type IN ('email', 'notification', 'briefing')) DEFAULT 'notification',
    sent INTEGER DEFAULT 0,
    sent_at DATETIME,

    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id) ON DELETE CASCADE
);

-- User query log for learning preferences
CREATE TABLE IF NOT EXISTS user_query_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    query_type TEXT,  -- 'proposal', 'project', 'meeting', 'email', etc.
    filters_used TEXT,  -- JSON of filters applied
    results_count INTEGER,
    execution_time_ms INTEGER,
    user_id TEXT DEFAULT 'bill',
    query_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    day_of_week INTEGER,  -- 0=Monday, 6=Sunday
    hour_of_day INTEGER
);

CREATE INDEX IF NOT EXISTS idx_query_log_user ON user_query_log(user_id);
CREATE INDEX IF NOT EXISTS idx_query_log_type ON user_query_log(query_type);
CREATE INDEX IF NOT EXISTS idx_query_log_timestamp ON user_query_log(query_timestamp);

-- Learned user patterns table
CREATE TABLE IF NOT EXISTS learned_user_patterns (
    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT DEFAULT 'bill',
    pattern_type TEXT,  -- 'weekly_check', 'daily_metric', 'preferred_filter'
    pattern_description TEXT,
    pattern_data TEXT,  -- JSON with pattern details
    confidence REAL,
    occurrences INTEGER DEFAULT 1,
    last_seen DATETIME,
    suggestion_made INTEGER DEFAULT 0,
    suggestion_accepted INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Verify tables created
SELECT 'meetings' as table_name, COUNT(*) as count FROM meetings
UNION ALL
SELECT 'meeting_reminders', COUNT(*) FROM meeting_reminders
UNION ALL
SELECT 'user_query_log', COUNT(*) FROM user_query_log
UNION ALL
SELECT 'learned_user_patterns', COUNT(*) FROM learned_user_patterns;
