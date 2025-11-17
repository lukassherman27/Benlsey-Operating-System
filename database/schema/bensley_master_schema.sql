-- ============================================================================
-- Bensley Intelligence Platform - Canonical Database Schema
-- ============================================================================
-- 
-- This is the CANONICAL schema exported from the live production database.
-- It represents the ACTUAL current state after all migrations have been applied.
-- 
-- Export Date: 2025-11-14
-- Database: bensley_master.db
-- Schema Version: 012 (12 migrations applied)
-- 
-- Statistics:
--   - 51 tables
--   - 107 indexes
--   - 4 views
--   - 3 triggers
-- 
-- Key Tables:
--   - proposals (87 records) - Enhanced with health scoring & active project flag
--   - emails (181 records) - Linked to proposals via email_proposal_links
--   - email_content (0 records) - AI-processed email analysis
--   - documents (852 records) - Indexed files linked to proposals
--   - contacts_only (205 records) - External contacts extracted from emails
-- 
-- To recreate this database:
--   sqlite3 bensley_master.db < database/schema/bensley_master_schema.sql
-- 
-- To verify migrations:
--   SELECT * FROM schema_migrations ORDER BY version;
-- 
-- ============================================================================

CREATE TABLE projects (
  project_id              INTEGER PRIMARY KEY AUTOINCREMENT,
  project_code            TEXT UNIQUE NOT NULL,           -- "25 BK-001"
  project_title           TEXT,
  client_id               INTEGER,
  source_db               TEXT,                           -- 'proposals' | 'contracts'
  status                  TEXT,                           -- 'Proposal' | 'Active' | 'Completed' | 'On-Hold'
  project_type            TEXT,                           -- 'Hotel' | 'Residential' | 'Resort' | 'Restaurant'
  country                 TEXT,
  city                    TEXT,
  total_fee_usd           REAL,
  contract_term_months    INTEGER,
  contract_expiry_date    DATE,
  date_created            DATE,
  folder_path             TEXT,
  notes                   TEXT,
  updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
  source_ref              TEXT                            -- 'proposals.db:projects:123'
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE clients (
  client_id               INTEGER PRIMARY KEY AUTOINCREMENT,
  company_name            TEXT UNIQUE NOT NULL,
  country                 TEXT,
  industry                TEXT,
  notes                   TEXT,
  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE contacts (
  contact_id              INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id               INTEGER,
  email                   TEXT UNIQUE NOT NULL,
  name                    TEXT,
  role                    TEXT,
  phone                   TEXT,
  notes                   TEXT,
  FOREIGN KEY (client_id) REFERENCES clients(client_id)
);
CREATE TABLE client_aliases (
  client_id               INTEGER,
  alias                   TEXT,
  alias_type              TEXT,                           -- 'email_domain' | 'company_variant' | 'manual'
  confidence              REAL DEFAULT 1.0,
  created_by              TEXT,                           -- 'ai' | 'manual' | 'import'
  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (client_id, alias),
  FOREIGN KEY (client_id) REFERENCES clients(client_id)
);
CREATE TABLE invoices (
  invoice_id              INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id              INTEGER,
  invoice_number          TEXT UNIQUE,
  description             TEXT,
  invoice_date            DATE,
  due_date                DATE,
  invoice_amount          REAL,
  payment_amount          REAL,
  payment_date            DATE,
  status                  TEXT,                           -- 'Paid' | 'Partial' | 'Unpaid' | 'Overdue'
  notes                   TEXT,
  source_ref              TEXT,
  FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
CREATE TABLE emails (
  email_id                INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id              TEXT UNIQUE NOT NULL,
  thread_id               TEXT,
  date                    DATETIME,
  sender_email            TEXT,
  sender_name             TEXT,
  recipient_emails        TEXT,                           -- Comma-separated or JSON
  subject                 TEXT,
  snippet                 TEXT,
  body_preview            TEXT,
  has_attachments         INTEGER DEFAULT 0,
  processed               INTEGER DEFAULT 0,
  ai_summary              TEXT,
  source_ref              TEXT,                           -- 'emails.db:emails:456'
  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
, folder TEXT, body_full TEXT);
CREATE TABLE email_tags (
  email_id                INTEGER,
  tag                     TEXT,
  tag_type                TEXT,                           -- 'category' | 'priority' | 'topic' | 'project_mention' | 'client_mention'
  confidence              REAL DEFAULT 0.0,
  created_by              TEXT,                           -- 'ai' | 'manual' | 'rule'
  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (email_id, tag, tag_type),
  FOREIGN KEY (email_id) REFERENCES emails(email_id)
);
CREATE TABLE project_tags (
  project_id              INTEGER,
  tag                     TEXT,
  tag_type                TEXT,                           -- 'location' | 'type' | 'status' | 'category'
  confidence              REAL DEFAULT 1.0,
  created_by              TEXT,
  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (project_id, tag, tag_type),
  FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
CREATE TABLE tag_mappings (
  raw_tag                 TEXT PRIMARY KEY,
  canonical_tag           TEXT NOT NULL,
  tag_type                TEXT,
  notes                   TEXT
);
CREATE TABLE email_project_links (
  email_id                INTEGER,
  project_id              INTEGER,
  confidence              REAL DEFAULT 0.0,
  link_method             TEXT,                           -- 'alias' | 'ai' | 'manual' | 'subject_match'
  evidence                TEXT,                           -- Why this link was made
  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP, message_id TEXT, project_code TEXT,
  PRIMARY KEY (email_id, project_id),
  FOREIGN KEY (email_id) REFERENCES emails(email_id),
  FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
CREATE TABLE email_client_links (
  email_id                INTEGER,
  client_id               INTEGER,
  confidence              REAL DEFAULT 0.0,
  link_method             TEXT,
  evidence                TEXT,
  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (email_id, client_id),
  FOREIGN KEY (email_id) REFERENCES emails(email_id),
  FOREIGN KEY (client_id) REFERENCES clients(client_id)
);
CREATE TABLE action_items (
  action_id               INTEGER PRIMARY KEY AUTOINCREMENT,
  email_id                INTEGER,
  project_id              INTEGER,
  description             TEXT,
  due_date                DATE,
  priority                TEXT,                           -- 'high' | 'medium' | 'low'
  status                  TEXT DEFAULT 'open',            -- 'open' | 'completed' | 'cancelled'
  assigned_to             TEXT,
  completed_date          DATE,
  confidence              REAL,
  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (email_id) REFERENCES emails(email_id),
  FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
CREATE TABLE audit_log (
  log_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp               DATETIME DEFAULT CURRENT_TIMESTAMP,
  actor                   TEXT,                           -- 'system' | 'ai' | 'user:name'
  action                  TEXT,                           -- 'insert' | 'update' | 'delete' | 'sync' | 'link' | 'tag'
  entity_type             TEXT,                           -- 'project' | 'email' | 'invoice' | 'tag' | 'link'
  entity_id               TEXT,
  details                 TEXT                            -- JSON with changes
);
CREATE TABLE sync_history (
  sync_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  source_db               TEXT,                           -- 'proposals.db' | 'contracts.db' | 'emails.db'
  sync_start              DATETIME,
  sync_end                DATETIME,
  records_processed       INTEGER,
  records_inserted        INTEGER,
  records_updated         INTEGER,
  errors                  TEXT,
  status                  TEXT                            -- 'success' | 'partial' | 'failed'
);
CREATE TABLE contacts_only (
                contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                email_count INTEGER DEFAULT 0,
                first_seen DATE,
                last_seen DATE,
                notes TEXT
            );
CREATE TABLE learned_patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                pattern_key TEXT,
                pattern_value TEXT,
                confidence REAL,
                occurrences INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(pattern_type, pattern_key, pattern_value)
            );
CREATE TABLE project_metadata (
                metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                metadata_key TEXT,
                metadata_value TEXT,
                source TEXT,
                confidence REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id),
                UNIQUE(project_id, metadata_key)
            );
CREATE TABLE contact_metadata (
                contact_meta_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                role TEXT,
                company TEXT,
                phone TEXT,
                last_contact_date DATE,
                total_emails INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(email)
            );
CREATE TABLE project_documents (
                document_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                file_path TEXT UNIQUE,
                file_name TEXT,
                file_type TEXT,
                file_size INTEGER,
                confidence REAL,
                link_method TEXT,
                evidence TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            );
CREATE TABLE rfis (
            rfi_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            project_code TEXT,
            rfi_number TEXT,
            subject TEXT,
            description TEXT,
            date_sent DATE,
            date_due DATE,
            date_responded DATE,
            status TEXT DEFAULT 'open',
            priority TEXT DEFAULT 'normal',
            sender_email TEXT,
            sender_name TEXT,
            response_email_id INTEGER,
            extracted_from_email_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP, extraction_confidence REAL DEFAULT 0.5,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        );
CREATE TABLE project_milestones (
            milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            project_code TEXT,
            phase TEXT,
            milestone_name TEXT,
            milestone_type TEXT,
            planned_date DATE,
            actual_date DATE,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            extracted_from_email BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        );
CREATE TABLE action_items_tracking (
            action_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            project_code TEXT,
            description TEXT NOT NULL,
            assigned_to TEXT,
            assigned_by TEXT,
            due_date DATE,
            completed_date DATE,
            priority TEXT DEFAULT 'normal',
            status TEXT DEFAULT 'pending',
            category TEXT,
            source_email_id INTEGER,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP, confidence REAL DEFAULT 0.5,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        );
CREATE TABLE project_status_tracking (
            status_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            project_code TEXT,
            status_date DATE,
            phase TEXT,
            completion_pct INTEGER,
            current_activity TEXT,
            waiting_on TEXT,
            waiting_on_email TEXT,
            next_milestone TEXT,
            next_milestone_date DATE,
            notes TEXT,
            extracted_from_email BOOLEAN DEFAULT 0,
            source_email_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP, confidence REAL DEFAULT 0.5,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        );
CREATE TABLE deliverables (
            deliverable_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            project_code TEXT,
            deliverable_name TEXT,
            deliverable_type TEXT,
            phase TEXT,
            due_date DATE,
            submitted_date DATE,
            approved_date DATE,
            status TEXT DEFAULT 'pending',
            revision_number INTEGER DEFAULT 0,
            notes TEXT,
            file_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        );
CREATE TABLE communication_log (
            comm_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            project_code TEXT,
            comm_date DATE,
            comm_type TEXT,
            subject TEXT,
            participants TEXT,
            summary TEXT,
            key_decisions TEXT,
            action_items_generated INTEGER DEFAULT 0,
            email_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        );
CREATE TABLE data_quality_tracking (
                issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_table TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                issue_type TEXT NOT NULL,
                severity TEXT CHECK(severity IN ('critical', 'high', 'medium', 'low')),
                description TEXT,
                suggested_fix TEXT,
                suggested_value TEXT,
                ai_confidence REAL,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'reviewed', 'approved', 'rejected', 'fixed')),
                reviewed_by TEXT,
                reviewed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
CREATE TABLE data_confidence_scores (
                score_id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_table TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                field_value TEXT,
                confidence_score REAL NOT NULL,
                source TEXT,
                calculation_method TEXT,
                calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(data_table, record_id, field_name)
            );
CREATE TABLE ai_suggestions_queue (
                suggestion_id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_table TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                current_value TEXT,
                suggested_value TEXT NOT NULL,
                confidence REAL NOT NULL,
                reasoning TEXT,
                evidence TEXT,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'applied')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                reviewed_at DATETIME,
                applied_at DATETIME
            );
CREATE TABLE learning_patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                pattern_rule TEXT NOT NULL,
                confidence_weight REAL DEFAULT 1.0,
                times_used INTEGER DEFAULT 0,
                times_correct INTEGER DEFAULT 0,
                accuracy REAL,
                source TEXT CHECK(source IN ('manual', 'ai_learned', 'user_correction')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME
            );
CREATE TABLE proposals (
                    proposal_id INTEGER PRIMARY KEY,
                    project_code TEXT UNIQUE NOT NULL,
                    project_name TEXT,
                    client_company TEXT,
                    contact_person TEXT,
                    contact_phone TEXT,
                    contact_email TEXT,
                    project_value REAL,
                    is_landscape INTEGER DEFAULT 0,
                    is_architect INTEGER DEFAULT 0,
                    is_interior INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'proposal',
                    created_at TEXT,
                    updated_at TEXT
                , contract_signed_date TEXT, is_active_project INTEGER DEFAULT 0, project_phase TEXT, status_notes TEXT, expected_delay_days INTEGER, delay_reason TEXT, delay_until_date TEXT, client_response_pattern TEXT DEFAULT 'unknown', urgency_level TEXT DEFAULT 'normal', on_hold INTEGER DEFAULT 0, on_hold_reason TEXT, on_hold_until TEXT, last_contact_date TEXT, days_since_contact INTEGER, health_score REAL, win_probability REAL, last_sentiment TEXT, internal_notes TEXT, next_action TEXT, next_action_date TEXT);
CREATE TABLE project_contacts (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_address TEXT UNIQUE NOT NULL,
    full_name TEXT,
    company TEXT,
    phone TEXT,
    is_internal INTEGER DEFAULT 0,  -- 1 for @bensley.com staff
    first_seen TEXT,
    last_contact TEXT,
    total_emails INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE project_contact_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    contact_id INTEGER NOT NULL,
    role TEXT,  -- 'client', 'consultant', 'contractor', 'operator', 'internal'
    email_count INTEGER DEFAULT 0,
    confidence_score REAL DEFAULT 0.5,
    first_linked TEXT DEFAULT (datetime('now')),
    last_activity TEXT DEFAULT (datetime('now')),
    notes TEXT,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    FOREIGN KEY (contact_id) REFERENCES project_contacts(contact_id),
    UNIQUE(proposal_id, contact_id)
);
CREATE TABLE email_proposal_links (
                    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id INTEGER,
                    proposal_id INTEGER,
                    confidence_score REAL,
                    match_reasons TEXT,
                    auto_linked INTEGER DEFAULT 0,
                    created_at TEXT,
                    FOREIGN KEY (email_id) REFERENCES emails(email_id),
                    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
                );
CREATE TABLE email_content (
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
    created_at TEXT DEFAULT (datetime('now')), subcategory TEXT, urgency_level TEXT CHECK(urgency_level IN ('low', 'medium', 'high', 'critical')), client_sentiment TEXT CHECK(client_sentiment IN ('positive', 'neutral', 'negative', 'frustrated')), action_required INTEGER DEFAULT 0, follow_up_date DATE,
    FOREIGN KEY (email_id) REFERENCES emails(email_id)
);
CREATE TABLE attachments (
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
CREATE TABLE email_threads (
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
CREATE TABLE document_versions (
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
CREATE TABLE decisions (
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
CREATE TABLE proposal_timeline (
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
CREATE TABLE proposal_state (
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
CREATE TABLE change_log (
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
CREATE TABLE training_data (
    training_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT,                     -- classify/extract/summarize
    input_data TEXT,                    -- Email content
    output_data TEXT,                   -- Model's answer
    model_used TEXT,                    -- gpt-4/claude/etc
    confidence REAL,                    -- How sure was model
    human_verified INTEGER DEFAULT 0,  -- 1 if human checked
    created_at TEXT DEFAULT (datetime('now'))
, feedback TEXT);
CREATE TABLE documents (
    document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL, -- pdf, docx, doc, xlsx, etc.
    file_size INTEGER,
    created_date TEXT,
    modified_date TEXT,
    indexed_at TEXT DEFAULT (datetime('now')),

    -- Extracted metadata
    document_type TEXT, -- proposal, contract, invoice, rfi, schedule, etc.
    project_code TEXT,
    document_date TEXT,
    version TEXT,
    status TEXT, -- draft, final, signed, etc.

    -- Extracted content
    text_content TEXT,
    page_count INTEGER,

    FOREIGN KEY (project_code) REFERENCES proposals(project_code)
);
CREATE TABLE document_intelligence (
    intelligence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,

    -- Key information extracted by AI
    fee_amount TEXT,
    fee_currency TEXT,
    scope_summary TEXT,
    timeline TEXT,
    key_deliverables TEXT, -- JSON array
    special_terms TEXT,
    decision_makers TEXT, -- JSON array of people

    -- AI summary
    executive_summary TEXT,
    key_changes TEXT, -- Compared to previous version

    -- Processing metadata
    extracted_at TEXT DEFAULT (datetime('now')),
    model_used TEXT,
    confidence_score REAL,

    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);
CREATE TABLE document_proposal_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    proposal_id INTEGER NOT NULL,
    link_type TEXT, -- primary, reference, supersedes, etc.
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    UNIQUE(document_id, proposal_id)
);
CREATE INDEX idx_projects_code ON projects(project_code);
CREATE INDEX idx_projects_client ON projects(client_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_country ON projects(country);
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contacts_client ON contacts(client_id);
CREATE INDEX idx_client_aliases_alias ON client_aliases(alias);
CREATE INDEX idx_invoices_project ON invoices(project_id);
CREATE INDEX idx_invoices_number ON invoices(invoice_number);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_emails_message ON emails(message_id);
CREATE INDEX idx_emails_thread ON emails(thread_id);
CREATE INDEX idx_emails_sender ON emails(sender_email);
CREATE INDEX idx_emails_date ON emails(date);
CREATE INDEX idx_email_tags_email ON email_tags(email_id);
CREATE INDEX idx_email_tags_tag ON email_tags(tag);
CREATE INDEX idx_email_tags_type ON email_tags(tag_type);
CREATE INDEX idx_project_tags_project ON project_tags(project_id);
CREATE INDEX idx_project_tags_tag ON project_tags(tag);
CREATE INDEX idx_email_project_links_email ON email_project_links(email_id);
CREATE INDEX idx_email_project_links_project ON email_project_links(project_id);
CREATE INDEX idx_email_client_links_email ON email_client_links(email_id);
CREATE INDEX idx_email_client_links_client ON email_client_links(client_id);
CREATE INDEX idx_action_items_email ON action_items(email_id);
CREATE INDEX idx_action_items_project ON action_items(project_id);
CREATE INDEX idx_action_items_status ON action_items(status);
CREATE INDEX idx_action_items_due ON action_items(due_date);
CREATE INDEX idx_rfi_project ON rfis(project_id);
CREATE INDEX idx_rfi_project_code ON rfis(project_code);
CREATE INDEX idx_rfi_status ON rfis(status);
CREATE INDEX idx_rfi_due ON rfis(date_due);
CREATE INDEX idx_milestone_project ON project_milestones(project_id);
CREATE INDEX idx_milestone_project_code ON project_milestones(project_code);
CREATE INDEX idx_milestone_date ON project_milestones(planned_date);
CREATE INDEX idx_action_track_project ON action_items_tracking(project_id);
CREATE INDEX idx_action_track_code ON action_items_tracking(project_code);
CREATE INDEX idx_action_track_assigned ON action_items_tracking(assigned_to);
CREATE INDEX idx_action_track_due ON action_items_tracking(due_date);
CREATE INDEX idx_action_track_status ON action_items_tracking(status);
CREATE INDEX idx_status_track_project ON project_status_tracking(project_id);
CREATE INDEX idx_status_track_code ON project_status_tracking(project_code);
CREATE INDEX idx_status_track_date ON project_status_tracking(status_date);
CREATE INDEX idx_deliverable_project ON deliverables(project_id);
CREATE INDEX idx_deliverable_code ON deliverables(project_code);
CREATE INDEX idx_deliverable_due ON deliverables(due_date);
CREATE INDEX idx_comm_project ON communication_log(project_id);
CREATE INDEX idx_comm_code ON communication_log(project_code);
CREATE INDEX idx_comm_date ON communication_log(comm_date);
CREATE INDEX idx_contact_links_proposal ON project_contact_links(proposal_id);
CREATE INDEX idx_contact_links_contact ON project_contact_links(contact_id);
CREATE INDEX idx_contacts_internal ON project_contacts(is_internal);
CREATE INDEX idx_email_content_email ON email_content(email_id);
CREATE INDEX idx_email_content_category ON email_content(category);
CREATE INDEX idx_attachments_email ON attachments(email_id);
CREATE INDEX idx_threads_proposal ON email_threads(proposal_id);
CREATE INDEX idx_decisions_proposal ON decisions(proposal_id);
CREATE INDEX idx_timeline_proposal ON proposal_timeline(proposal_id);
CREATE INDEX idx_timeline_timestamp ON proposal_timeline(timestamp);
CREATE INDEX idx_documents_project_code ON documents(project_code);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_modified ON documents(modified_date);
CREATE INDEX idx_doc_proposal_links ON document_proposal_links(proposal_id);
CREATE VIEW project_contacts_view AS
SELECT
    p.project_code,
    p.project_name,
    c.full_name,
    c.email_address,
    c.company,
    c.is_internal,
    l.role,
    l.email_count,
    l.confidence_score,
    l.last_activity
FROM project_contact_links l
JOIN proposals p ON l.proposal_id = p.proposal_id
JOIN project_contacts c ON l.contact_id = c.contact_id
ORDER BY p.project_code, l.email_count DESC
/* project_contacts_view(project_code,project_name,full_name,email_address,company,is_internal,role,email_count,confidence_score,last_activity) */;
CREATE VIEW contact_projects_view AS
SELECT
    c.full_name,
    c.email_address,
    c.company,
    c.is_internal,
    GROUP_CONCAT(p.project_code, ', ') as projects,
    COUNT(p.project_code) as project_count,
    SUM(l.email_count) as total_emails
FROM project_contacts c
LEFT JOIN project_contact_links l ON c.contact_id = l.contact_id
LEFT JOIN proposals p ON l.proposal_id = p.proposal_id
GROUP BY c.contact_id
ORDER BY total_emails DESC
/* contact_projects_view(full_name,email_address,company,is_internal,projects,project_count,total_emails) */;
CREATE VIEW recent_activity AS
SELECT
    p.project_code,
    p.project_name,
    pt.event_type,
    pt.event_summary,
    pt.timestamp,
    pt.importance
FROM proposal_timeline pt
JOIN proposals p ON pt.proposal_id = p.proposal_id
ORDER BY pt.timestamp DESC
/* recent_activity(project_code,project_name,event_type,event_summary,timestamp,importance) */;
CREATE VIEW proposal_health AS
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
ORDER BY ps.health_score DESC
/* proposal_health(project_code,project_name,current_status,days_since_last_contact,health_score,waiting_on,next_action,total_emails,decisions_made) */;
CREATE INDEX idx_emails_folder ON emails(folder);
CREATE VIRTUAL TABLE emails_fts USING fts5(
    email_id UNINDEXED,
    subject,
    body_full,
    content='emails',
    content_rowid='email_id'
)
/* emails_fts(email_id,subject,body_full) */;
CREATE TABLE IF NOT EXISTS 'emails_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'emails_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'emails_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'emails_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TRIGGER emails_ai AFTER INSERT ON emails BEGIN
  INSERT INTO emails_fts(email_id, subject, body_full)
  VALUES (new.email_id, new.subject, new.body_full);
END;
CREATE TRIGGER emails_ad AFTER DELETE ON emails BEGIN
  DELETE FROM emails_fts WHERE email_id = old.email_id;
END;
CREATE TRIGGER emails_au AFTER UPDATE ON emails BEGIN
  UPDATE emails_fts SET subject = new.subject, body_full = new.body_full
  WHERE email_id = new.email_id;
END;
CREATE INDEX idx_proposals_health ON proposals(health_score);
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_active ON proposals(is_active_project);
CREATE INDEX idx_proposals_days_contact ON proposals(days_since_contact);
CREATE INDEX idx_email_content_importance ON email_content(importance_score);
CREATE INDEX idx_epl_proposal ON email_proposal_links(proposal_id);
CREATE INDEX idx_epl_email ON email_proposal_links(email_id);
CREATE INDEX idx_dpl_proposal ON document_proposal_links(proposal_id);
CREATE INDEX idx_dpl_document ON document_proposal_links(document_id);
CREATE INDEX idx_proposals_active_health
    ON proposals(is_active_project, health_score, days_since_contact);
CREATE INDEX idx_emails_date_folder
    ON emails(date, folder);
CREATE INDEX idx_email_content_subcategory ON email_content(subcategory);
CREATE INDEX idx_email_content_urgency ON email_content(urgency_level);
CREATE INDEX idx_email_content_action ON email_content(action_required);
CREATE INDEX idx_email_content_category_importance
    ON email_content(category, importance_score DESC);
CREATE INDEX idx_email_content_followup
    ON email_content(follow_up_date, action_required);
CREATE INDEX idx_proposals_status_health
    ON proposals(status, health_score ASC);
CREATE INDEX idx_email_content_urgent_action
    ON email_content(urgency_level, action_required);
CREATE INDEX idx_epl_proposal_confidence
    ON email_proposal_links(proposal_id, confidence_score DESC);
CREATE INDEX idx_dpl_proposal_type
    ON document_proposal_links(proposal_id, link_type);
CREATE INDEX idx_emails_body_full
    ON emails(body_full) WHERE body_full IS NOT NULL;
