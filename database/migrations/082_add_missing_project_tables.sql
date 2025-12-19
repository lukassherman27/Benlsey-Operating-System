-- Migration 082: Add missing project tables
-- These tables are referenced by services but don't exist in the database

-- 1. project_context - for notes, tasks, reminders linked to proposals
CREATE TABLE IF NOT EXISTS project_context (
    context_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER,
    context_type TEXT CHECK(context_type IN ('note', 'task', 'reminder', 'action_item', 'decision', 'question')),
    context_text TEXT NOT NULL,
    priority TEXT DEFAULT 'normal' CHECK(priority IN ('low', 'normal', 'high', 'critical')),
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed', 'cancelled', 'pending')),
    due_date DATE,
    assigned_to TEXT,
    created_by TEXT DEFAULT 'system',
    related_email_id INTEGER,
    related_milestone_id INTEGER,
    agent_action_taken TEXT,
    agent_action_result TEXT,
    agent_action_timestamp DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    FOREIGN KEY (related_email_id) REFERENCES emails(email_id),
    FOREIGN KEY (related_milestone_id) REFERENCES project_milestones(milestone_id)
);

CREATE INDEX IF NOT EXISTS idx_project_context_proposal ON project_context(proposal_id);
CREATE INDEX IF NOT EXISTS idx_project_context_type ON project_context(context_type);
CREATE INDEX IF NOT EXISTS idx_project_context_status ON project_context(status);
CREATE INDEX IF NOT EXISTS idx_project_context_due ON project_context(due_date);

-- 2. project_files - for tracking files/documents linked to proposals
CREATE TABLE IF NOT EXISTS project_files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER,
    filename TEXT NOT NULL,
    file_type TEXT CHECK(file_type IN ('drawing', 'presentation', 'contract', 'proposal', 'report', 'image', 'document', 'other')),
    file_category TEXT CHECK(file_category IN ('concept', 'schematic', 'detail', 'final', 'reference', 'correspondence')),
    file_path TEXT,
    onedrive_path TEXT,
    onedrive_url TEXT,
    file_size INTEGER,
    version INTEGER DEFAULT 1,
    uploaded_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    uploaded_by TEXT,
    description TEXT,
    tags TEXT,  -- JSON array of tags
    is_latest_version INTEGER DEFAULT 1,
    related_milestone_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    FOREIGN KEY (related_milestone_id) REFERENCES project_milestones(milestone_id)
);

CREATE INDEX IF NOT EXISTS idx_project_files_proposal ON project_files(proposal_id);
CREATE INDEX IF NOT EXISTS idx_project_files_type ON project_files(file_type);
CREATE INDEX IF NOT EXISTS idx_project_files_category ON project_files(file_category);
CREATE INDEX IF NOT EXISTS idx_project_files_latest ON project_files(is_latest_version);

-- 3. project_financials - for payment tracking linked to proposals
CREATE TABLE IF NOT EXISTS project_financials (
    financial_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER,
    payment_type TEXT CHECK(payment_type IN ('deposit', 'milestone', 'final', 'additional', 'retainer')),
    milestone_id INTEGER,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    percentage_of_total REAL,
    due_date DATE,
    invoice_number TEXT,
    invoice_sent_date DATE,
    payment_received_date DATE,
    payment_method TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'invoiced', 'paid', 'overdue', 'cancelled')),
    days_outstanding INTEGER DEFAULT 0,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    FOREIGN KEY (milestone_id) REFERENCES project_milestones(milestone_id)
);

CREATE INDEX IF NOT EXISTS idx_project_financials_proposal ON project_financials(proposal_id);
CREATE INDEX IF NOT EXISTS idx_project_financials_status ON project_financials(status);
CREATE INDEX IF NOT EXISTS idx_project_financials_due ON project_financials(due_date);
