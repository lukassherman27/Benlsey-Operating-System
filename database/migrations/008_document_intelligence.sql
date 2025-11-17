-- Migration 008: Document Intelligence System
-- Index and extract intelligence from proposal documents

-- Document registry
CREATE TABLE IF NOT EXISTS documents (
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

-- Document intelligence (AI-extracted information)
CREATE TABLE IF NOT EXISTS document_intelligence (
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

-- Document-proposal links (many-to-many)
CREATE TABLE IF NOT EXISTS document_proposal_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    proposal_id INTEGER NOT NULL,
    link_type TEXT, -- primary, reference, supersedes, etc.
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
    UNIQUE(document_id, proposal_id)
);

-- Document versions (track revisions)
CREATE TABLE IF NOT EXISTS document_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    previous_version_id INTEGER,
    version_number TEXT,
    changes_summary TEXT,
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    FOREIGN KEY (previous_version_id) REFERENCES documents(document_id)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_documents_project_code ON documents(project_code);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_modified ON documents(modified_date);
CREATE INDEX IF NOT EXISTS idx_doc_proposal_links ON document_proposal_links(proposal_id);
