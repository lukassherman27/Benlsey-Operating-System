-- Migration 003: Daily Work Tracking
-- Adds table for actual work logs from daily staff reports

CREATE TABLE IF NOT EXISTS daily_work_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    staff_name TEXT NOT NULL,
    work_date DATE NOT NULL,
    email_id INTEGER,

    -- Work completed
    tasks_completed TEXT,
    hours_logged REAL NOT NULL,
    status TEXT,

    -- Documentation
    photos_count INTEGER DEFAULT 0,
    photos_paths TEXT,
    files_created TEXT,

    -- Issues and planning
    issues_encountered TEXT,
    tomorrow_plan TEXT,

    -- Metadata
    submitted_time TIME,
    email_to TEXT,
    report_json_path TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (email_id) REFERENCES emails(email_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_daily_logs_project ON daily_work_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_daily_logs_staff ON daily_work_logs(staff_name);
CREATE INDEX IF NOT EXISTS idx_daily_logs_date ON daily_work_logs(work_date);
CREATE INDEX IF NOT EXISTS idx_daily_logs_project_staff ON daily_work_logs(project_id, staff_name);

-- View for planned vs actual comparison
CREATE VIEW IF NOT EXISTS work_comparison AS
SELECT
    sa.project_id,
    sa.staff_name,
    sa.allocation_percent as planned_allocation,
    COUNT(DISTINCT dwl.work_date) as days_worked,
    SUM(dwl.hours_logged) as total_hours_logged,
    AVG(dwl.hours_logged) as avg_hours_per_day,
    SUM(dwl.photos_count) as total_photos,
    COUNT(CASE WHEN dwl.issues_encountered IS NOT NULL THEN 1 END) as issues_reported
FROM staff_assignments sa
LEFT JOIN daily_work_logs dwl ON sa.project_id = dwl.project_id AND sa.staff_name = dwl.staff_name
WHERE sa.status = 'active'
GROUP BY sa.project_id, sa.staff_name;
