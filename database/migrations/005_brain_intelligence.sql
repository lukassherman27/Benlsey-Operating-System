-- Migration 005: Email Intelligence & Brain Schema
-- Adds content analysis, relationships, and intelligence layers

-- Email content analysis
CREATE TABLE IF NOT EXISTS email_content (
    content_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,
    clean_body TEXT,                    -- Signature/banner stripped
    quoted_text TEXT,                   -- Preserved separately
    category TEXT,                      -- contract/invoice/design/rfi/schedule/meeting/general
    key_points TEXT,                    -- JSON: ["fee discussion", "deadline set"]
    entities TEXT,                      -- JSON: {amounts: [], dates: [], people: []}
    sentiment TEXT,                     -- positive/neutral/concerned/urgent
    importance_score REAL DEFAULT 0.5,  -- 0-1 (filter noise)
    ai_summary TEXT,                    -- One sentence summary
    processing_model TEXT,              -- gpt-4/gpt-3.5/distilled (for tracking)
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (email_id) REFERENCES emails(email_id)
);

-- Attachments tracking
CREATE TABLE IF NOT EXISTS attachments (
    attachment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT,                     -- pdf/dwg/jpg/doc/etc
    file_size INTEGER,
    mime_type TEXT,
    stored_path TEXT,                   -- Where file is saved
    extracted_data TEXT,                -- JSON: contract data, drawing metadata, etc
    category TEXT,                      -- contract/proposal/drawing/photo/invoice
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (email_id) REFERENCES emails(email_id)
);

-- Email threads (conversations)
CREATE TABLE IF NOT EXISTS email_threads (
    thread_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_normalized TEXT,
    proposal_id INTEGER,
    emails TEXT,                        -- JSON: [email_id, email_id, ...] in order
    first_email_date TEXT,
    last_email_date TEXT,
    message_count INTEGER DEFAULT 0,
    status TEXT,                        -- open/resolved/waiting
    resolution TEXT,                    -- "Fee agreed" or "Waiting response"
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

-- Document versions (track changes)
CREATE TABLE IF NOT EXISTS document_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    doc_type TEXT,                      -- contract/proposal/scope/timeline
    version_number INTEGER,
    filename TEXT,
    file_path TEXT,
    extracted_data TEXT,                -- JSON: fees, terms, scope items
    changes_from_previous TEXT,         -- JSON: what changed
    created_by TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

-- Decisions log
CREATE TABLE IF NOT EXISTS decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    decision_text TEXT NOT NULL,
    decided_by TEXT,                    -- Person who made decision
    decided_at TEXT,
    reason TEXT,                        -- Why this decision
    impact TEXT,                        -- What this affects
    source_email_id INTEGER,            -- Email where decided
    source_document_id INTEGER,         -- Document where recorded
    category TEXT,                      -- fee/scope/timeline/personnel
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    FOREIGN KEY (source_email_id) REFERENCES emails(email_id)
);

-- Proposal timeline (everything that happened)
CREATE TABLE IF NOT EXISTS proposal_timeline (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    event_type TEXT,                    -- email_sent/document_created/decision_made/contact_made
    event_summary TEXT,                 -- AI-generated one-liner
    event_data TEXT,                    -- JSON: full details
    importance REAL DEFAULT 0.5,        -- 0-1
    timestamp TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

-- Proposal current state (what AI needs to know)
CREATE TABLE IF NOT EXISTS proposal_state (
    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER UNIQUE NOT NULL,
    current_status TEXT,                -- active/waiting/negotiating/closing/won/lost
    waiting_on TEXT,                    -- "Client signature" or "Our proposal"
    last_contact_date TEXT,
    days_since_last_contact INTEGER,
    next_action TEXT,                   -- "Follow up with Joe"
    open_issues TEXT,                   -- JSON: [{issue, since, severity}]
    key_decisions TEXT,                 -- JSON: [decision summaries]
    current_fee REAL,
    current_scope_version INTEGER,
    health_score REAL DEFAULT 0.7,      -- 0-1 (how well is this going?)
    last_updated TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);

-- Change log (audit everything)
CREATE TABLE IF NOT EXISTS change_log (
    change_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT,                   -- proposal/email/document/decision
    entity_id INTEGER,
    field_changed TEXT,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT,                    -- system/user/ai/import
    changed_at TEXT DEFAULT (datetime('now')),
    reason TEXT
);

-- Distillation training data (for future model training)
CREATE TABLE IF NOT EXISTS training_data (
    training_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT,                     -- classify/extract/summarize
    input_data TEXT,                    -- Email content
    output_data TEXT,                   -- Model's answer
    model_used TEXT,                    -- gpt-4/claude/etc
    confidence REAL,                    -- How sure was model
    human_verified INTEGER DEFAULT 0,  -- 1 if human checked
    created_at TEXT DEFAULT (datetime('now'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_email_content_email ON email_content(email_id);
CREATE INDEX IF NOT EXISTS idx_email_content_category ON email_content(category);
CREATE INDEX IF NOT EXISTS idx_attachments_email ON attachments(email_id);
CREATE INDEX IF NOT EXISTS idx_threads_proposal ON email_threads(proposal_id);
CREATE INDEX IF NOT EXISTS idx_decisions_proposal ON decisions(proposal_id);
CREATE INDEX IF NOT EXISTS idx_timeline_proposal ON proposal_timeline(proposal_id);
CREATE INDEX IF NOT EXISTS idx_timeline_timestamp ON proposal_timeline(timestamp);

-- Views for easy querying

-- Recent activity by proposal
CREATE VIEW IF NOT EXISTS recent_activity AS
SELECT
    p.project_code,
    p.project_name,
    pt.event_type,
    pt.event_summary,
    pt.timestamp,
    pt.importance
FROM proposal_timeline pt
JOIN proposals p ON pt.proposal_id = p.proposal_id
ORDER BY pt.timestamp DESC;

-- Proposal health dashboard
CREATE VIEW IF NOT EXISTS proposal_health AS
SELECT
    p.project_code,
    p.project_name,
    ps.current_status,
    ps.days_since_last_contact,
    ps.health_score,
    ps.waiting_on,
    ps.next_action,
    COUNT(DISTINCT e.email_id) as total_emails,
    COUNT(DISTINCT d.decision_id) as decisions_made
FROM proposals p
LEFT JOIN proposal_state ps ON p.proposal_id = ps.proposal_id
LEFT JOIN email_proposal_links epl ON p.proposal_id = epl.proposal_id
LEFT JOIN emails e ON epl.email_id = e.email_id
LEFT JOIN decisions d ON p.proposal_id = d.proposal_id
GROUP BY p.proposal_id
ORDER BY ps.health_score DESC;
