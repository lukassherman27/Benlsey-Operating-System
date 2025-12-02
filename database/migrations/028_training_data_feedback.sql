-- Training Data Feedback System
-- Collects user feedback for RLHF (Reinforcement Learning from Human Feedback)
-- This data will be used in Phase 2 to improve AI models

CREATE TABLE IF NOT EXISTS training_data_feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- User and feature identification
    user_id TEXT NOT NULL DEFAULT 'system',
    feature_name TEXT NOT NULL, -- e.g., 'email_intelligence', 'invoice_aging', 'project_health'
    component_name TEXT, -- Specific widget/component name

    -- Original data that was shown to user
    original_data TEXT, -- JSON string of original data/prediction
    original_value TEXT, -- Simple text representation

    -- User feedback
    correction_data TEXT, -- JSON string of corrected data (if applicable)
    correction_value TEXT, -- Simple text representation of correction
    helpful BOOLEAN, -- true = 👍, false = 👎, null = not rated

    -- Context
    project_code TEXT, -- Related project (if applicable)
    proposal_id INTEGER, -- Related proposal (if applicable)
    context_data TEXT, -- Additional context as JSON

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,

    -- Provenance
    source TEXT DEFAULT 'web_ui', -- 'web_ui', 'api', 'manual'
    notes TEXT,

    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id) ON DELETE SET NULL
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_training_feedback_feature ON training_data_feedback(feature_name);
CREATE INDEX IF NOT EXISTS idx_training_feedback_user ON training_data_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_training_feedback_created ON training_data_feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_training_feedback_helpful ON training_data_feedback(helpful);
CREATE INDEX IF NOT EXISTS idx_training_feedback_project ON training_data_feedback(project_code);

-- View for easy analysis
CREATE VIEW IF NOT EXISTS training_feedback_summary AS
SELECT
    feature_name,
    COUNT(*) as total_feedback,
    SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END) as helpful_count,
    SUM(CASE WHEN helpful = 0 THEN 1 ELSE 0 END) as not_helpful_count,
    SUM(CASE WHEN correction_data IS NOT NULL THEN 1 ELSE 0 END) as correction_count,
    ROUND(100.0 * SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as helpful_percentage,
    MIN(created_at) as first_feedback,
    MAX(created_at) as last_feedback
FROM training_data_feedback
GROUP BY feature_name;

-- Note: SQLite doesn't support COMMENT ON syntax
-- Comments are included in CREATE TABLE statements above
