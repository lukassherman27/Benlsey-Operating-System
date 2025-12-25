-- Migration 096: Create daily_work table for Bill/Brian review workflow
-- Created: 2025-12-26
-- Issue: #107 - Project management redesign
--
-- This table tracks daily work submissions from staff.
-- Staff email their work to a shared inbox, we parse and store here.
-- Bill/Brian review and provide feedback.

CREATE TABLE IF NOT EXISTS daily_work (
    daily_work_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Who submitted
    staff_id INTEGER REFERENCES staff(staff_id),
    staff_name TEXT,  -- Denormalized for quick display

    -- What project
    project_id INTEGER REFERENCES projects(project_id),
    project_code TEXT,

    -- When
    work_date DATE NOT NULL,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- What they did
    description TEXT,
    task_type TEXT,  -- 'drawing', 'model', 'presentation', 'research', 'coordination', 'other'
    discipline TEXT CHECK(discipline IN ('Architecture', 'Interior', 'Landscape', 'Artwork', 'Other')),
    phase TEXT,  -- 'Concept', 'SD', 'DD', 'CD', 'CA'
    hours_spent REAL,

    -- Source
    source_email_id INTEGER REFERENCES emails(email_id),
    raw_email_text TEXT,

    -- Attachments (JSON array of file info)
    -- [{filename: "floor-plan-v3.pdf", path: "/path/to/file", size_bytes: 12345}]
    attachments TEXT,

    -- Review by Bill/Brian
    reviewer_id INTEGER REFERENCES staff(staff_id),
    reviewer_name TEXT,
    review_status TEXT DEFAULT 'pending' CHECK(review_status IN ('pending', 'reviewed', 'needs_revision', 'approved')),
    review_comments TEXT,
    reviewed_at DATETIME,

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_daily_work_date ON daily_work(work_date);
CREATE INDEX IF NOT EXISTS idx_daily_work_staff ON daily_work(staff_id);
CREATE INDEX IF NOT EXISTS idx_daily_work_project ON daily_work(project_code);
CREATE INDEX IF NOT EXISTS idx_daily_work_review_status ON daily_work(review_status);
CREATE INDEX IF NOT EXISTS idx_daily_work_reviewer ON daily_work(reviewer_id);

-- Trigger to update updated_at
CREATE TRIGGER IF NOT EXISTS trg_daily_work_updated
AFTER UPDATE ON daily_work
FOR EACH ROW
BEGIN
    UPDATE daily_work SET updated_at = CURRENT_TIMESTAMP WHERE daily_work_id = NEW.daily_work_id;
END;
