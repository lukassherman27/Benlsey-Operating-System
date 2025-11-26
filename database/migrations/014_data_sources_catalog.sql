-- Migration 014: Data Sources Catalog Table
-- Purpose: Track all data ingestion batches for audit trail

CREATE TABLE IF NOT EXISTS data_sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL CHECK(source_type IN ('manual_excel', 'email_batch', 'ai_inference', 'pdf_extraction', 'api_import')),
    source_file TEXT,                -- File path or URL
    ingestion_batch_id TEXT UNIQUE,  -- UUID for batch tracking
    ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ingested_by TEXT,                -- 'user:bill', 'system:auto', 'script:import_invoices'
    row_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    checksum TEXT,                   -- SHA256 of source file for integrity
    status TEXT CHECK(status IN ('success', 'partial', 'failed', 'in_progress')) DEFAULT 'in_progress',
    notes TEXT,
    metadata TEXT                    -- JSON for additional context
);

CREATE INDEX idx_data_sources_type ON data_sources(source_type);
CREATE INDEX idx_data_sources_batch ON data_sources(ingestion_batch_id);
CREATE INDEX idx_data_sources_date ON data_sources(ingested_at);
