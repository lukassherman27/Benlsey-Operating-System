-- Migration 102: Create uploaded_files table for OneDrive integration
-- Issue: #243 - OneDrive file upload and storage integration

CREATE TABLE IF NOT EXISTS uploaded_files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    project_code TEXT NOT NULL,
    category TEXT NOT NULL,
    file_type TEXT,
    onedrive_path TEXT,
    onedrive_id TEXT,
    local_path TEXT,
    download_url TEXT,
    file_size INTEGER,
    mime_type TEXT,
    uploaded_by TEXT,
    uploaded_for TEXT,
    version INTEGER DEFAULT 1,
    is_latest_version INTEGER DEFAULT 1,
    supersedes_file_id INTEGER REFERENCES uploaded_files(file_id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_uploaded_files_project ON uploaded_files(project_code);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_category ON uploaded_files(project_code, category);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_type ON uploaded_files(file_type);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_uploaded_by ON uploaded_files(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_onedrive_id ON uploaded_files(onedrive_id);
