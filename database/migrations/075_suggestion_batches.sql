-- Migration 075: Suggestion Batch System
-- Groups suggestions by sender/pattern for efficient batch review

-- Batch groupings for efficient review
CREATE TABLE IF NOT EXISTS suggestion_batches (
    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    grouping_key TEXT NOT NULL,           -- e.g., "sender:john@acme.com" or "domain:acme.com"
    grouping_type TEXT NOT NULL,          -- 'sender', 'domain', 'project', 'pattern'
    suggested_project_code TEXT,          -- Target project code
    suggested_project_name TEXT,          -- Target project name for display
    proposal_id INTEGER,                  -- Link to proposal if applicable
    confidence_score REAL NOT NULL,       -- Aggregated confidence
    confidence_tier TEXT NOT NULL,        -- 'auto_approve', 'batch_review', 'individual', 'log_only'
    email_count INTEGER DEFAULT 0,        -- Number of emails in batch
    status TEXT DEFAULT 'pending',        -- 'pending', 'approved', 'rejected', 'partial'
    review_notes TEXT,
    reviewed_by TEXT,
    reviewed_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

-- Emails belonging to each batch
CREATE TABLE IF NOT EXISTS batch_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    email_id INTEGER NOT NULL,
    individual_confidence REAL,           -- Confidence for this specific email
    match_signals TEXT,                   -- JSON: what signals contributed to match
    status TEXT DEFAULT 'pending',        -- Can override batch status per-email
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (batch_id) REFERENCES suggestion_batches(batch_id),
    FOREIGN KEY (email_id) REFERENCES emails(email_id),
    UNIQUE(batch_id, email_id)
);

-- Low confidence emails that need manual review or were skipped
CREATE TABLE IF NOT EXISTS low_confidence_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,
    best_guess_project TEXT,              -- What we think it might be
    best_guess_name TEXT,                 -- Project name for display
    confidence REAL,                      -- Why we're not confident
    signals TEXT,                         -- JSON: partial matches, weak signals
    reason TEXT,                          -- Why confidence is low
    reviewed INTEGER DEFAULT 0,           -- Has human looked at this?
    reviewed_by TEXT,
    reviewed_at TEXT,
    final_project TEXT,                   -- What human decided (if reviewed)
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (email_id) REFERENCES emails(email_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_batches_status ON suggestion_batches(status);
CREATE INDEX IF NOT EXISTS idx_batches_tier ON suggestion_batches(confidence_tier);
CREATE INDEX IF NOT EXISTS idx_batches_project ON suggestion_batches(suggested_project_code);
CREATE INDEX IF NOT EXISTS idx_batch_emails_batch ON batch_emails(batch_id);
CREATE INDEX IF NOT EXISTS idx_batch_emails_email ON batch_emails(email_id);
CREATE INDEX IF NOT EXISTS idx_low_conf_reviewed ON low_confidence_log(reviewed);
CREATE INDEX IF NOT EXISTS idx_low_conf_email ON low_confidence_log(email_id);

-- View for pending batch review
CREATE VIEW IF NOT EXISTS pending_batches_view AS
SELECT 
    b.batch_id,
    b.grouping_key,
    b.grouping_type,
    b.suggested_project_code,
    b.suggested_project_name,
    b.confidence_score,
    b.confidence_tier,
    b.email_count,
    b.status,
    b.created_at,
    GROUP_CONCAT(be.email_id) as email_ids
FROM suggestion_batches b
LEFT JOIN batch_emails be ON b.batch_id = be.batch_id
WHERE b.status = 'pending'
GROUP BY b.batch_id
ORDER BY b.confidence_tier, b.confidence_score DESC;

-- View for low confidence items needing review
CREATE VIEW IF NOT EXISTS low_confidence_review_view AS
SELECT 
    l.id,
    l.email_id,
    e.sender_email,
    e.subject,
    e.date,
    l.best_guess_project,
    l.best_guess_name,
    l.confidence,
    l.signals,
    l.reason
FROM low_confidence_log l
JOIN emails e ON l.email_id = e.email_id
WHERE l.reviewed = 0
ORDER BY l.created_at DESC;
