# Database Schema Documentation

**Database:** `database/bensley_master.db` (SQLite)  
**Generated:** 2025-11-26

## Overview

The database contains 80+ tables organized into these domains:

| Domain | Tables | Purpose |
|--------|--------|---------|
| **Core Business** | projects, proposals, clients, contacts | Main entities |
| **Financial** | invoices, project_fee_breakdown, invoice_aging | Billing & payments |
| **Documents** | documents, contracts, attachments | File management |
| **Email** | emails, email_threads, email_content | Communication |
| **Intelligence** | ai_suggestions, learned_patterns, training_data | ML/AI features |
| **Audit** | audit_log, change_log, schema_migrations | Tracking |

---

## Core Tables

### projects
Main table for active/completed projects.
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
, source_type TEXT CHECK(source_type IN ('manual', 'import', 'ai', 'email_parser')), source_reference TEXT, locked_fields TEXT, locked_by TEXT, locked_at DATETIME, created_by TEXT DEFAULT 'system', updated_by TEXT, is_active_project INTEGER DEFAULT 0, health_score REAL, days_since_contact INTEGER DEFAULT 0, project_stage TEXT 
    CHECK(project_stage IN ('proposal', 'active_contract', 'archived')) 
    DEFAULT 'proposal', first_contact_date DATE, drafting_date DATE, proposal_sent_date DATE, contract_signed_date DATE, last_proposal_activity_date DATE, operator_id INTEGER REFERENCES operators(operator_id), base_path TEXT, current_phase TEXT, team_lead TEXT, target_completion DATE);
CREATE INDEX idx_projects_code ON projects(project_code);
CREATE INDEX idx_projects_client ON projects(client_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_country ON projects(country);
CREATE INDEX idx_projects_is_active ON projects(is_active_project);
CREATE INDEX idx_projects_health ON projects(health_score);
CREATE INDEX idx_projects_contact ON projects(days_since_contact);
CREATE INDEX idx_projects_stage ON projects(project_stage);
CREATE INDEX idx_projects_first_contact ON projects(first_contact_date);
CREATE INDEX idx_projects_proposal_sent ON projects(proposal_sent_date);
CREATE INDEX idx_projects_last_activity ON projects(last_proposal_activity_date);

### proposals
Pre-contract opportunities in the sales pipeline.
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
                , contract_signed_date TEXT, is_active_project INTEGER DEFAULT 0, project_phase TEXT, status_notes TEXT, expected_delay_days INTEGER, delay_reason TEXT, delay_until_date TEXT, client_response_pattern TEXT DEFAULT 'unknown', urgency_level TEXT DEFAULT 'normal', on_hold INTEGER DEFAULT 0, on_hold_reason TEXT, on_hold_until TEXT, last_contact_date TEXT, days_since_contact INTEGER, health_score REAL, win_probability REAL, last_sentiment TEXT, internal_notes TEXT, next_action TEXT, next_action_date TEXT, source_type TEXT DEFAULT 'manual', source_reference TEXT, created_by TEXT DEFAULT 'system', updated_by TEXT, locked_fields TEXT, locked_by TEXT, locked_at DATETIME, document_path TEXT, location TEXT, currency TEXT DEFAULT 'USD', proposal_sent_date TEXT, payment_terms TEXT, scope_summary TEXT, country TEXT, last_status_change DATE, status_changed_by TEXT, current_status TEXT, last_week_status TEXT, days_in_current_status INTEGER, first_contact_date DATE, days_to_sign INTEGER, days_in_drafting INTEGER, days_in_review INTEGER, num_proposals_sent INTEGER, phase TEXT, remarks TEXT);
CREATE INDEX idx_proposals_health ON proposals(health_score);
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_active ON proposals(is_active_project);
CREATE INDEX idx_proposals_days_contact ON proposals(days_since_contact);
CREATE INDEX idx_proposals_active_health
    ON proposals(is_active_project, health_score, days_since_contact);
CREATE INDEX idx_proposals_status_health
    ON proposals(status, health_score ASC);
CREATE INDEX idx_proposals_document_path ON proposals(document_path);
CREATE INDEX idx_proposals_location ON proposals(location);
CREATE TRIGGER log_proposals_changes
AFTER UPDATE ON proposals
FOR EACH ROW
BEGIN
    -- Log project_value changes
    INSERT INTO proposals_audit_log (
        proposal_id, project_code, field_name, old_value, new_value,
        changed_by, change_reason, change_source
    )
    SELECT NEW.proposal_id, NEW.project_code, 'project_value',
           CAST(OLD.project_value AS TEXT), CAST(NEW.project_value AS TEXT),
           COALESCE(NEW.updated_by, 'system'),
           NULL, -- change_reason captured separately
           COALESCE(NEW.source_type, 'manual')
    WHERE OLD.project_value != NEW.project_value OR (OLD.project_value IS NULL AND NEW.project_value IS NOT NULL);
    -- Log status changes
    INSERT INTO proposals_audit_log (
        proposal_id, project_code, field_name, old_value, new_value,
        changed_by, change_reason, change_source
    )
    SELECT NEW.proposal_id, NEW.project_code, 'status',
           OLD.status, NEW.status,
           COALESCE(NEW.updated_by, 'system'),
           NULL,
           COALESCE(NEW.source_type, 'manual')
    WHERE OLD.status != NEW.status OR (OLD.status IS NULL AND NEW.status IS NOT NULL);
    -- Log project_name changes
    INSERT INTO proposals_audit_log (
        proposal_id, project_code, field_name, old_value, new_value,
        changed_by, change_reason, change_source
    )
    SELECT NEW.proposal_id, NEW.project_code, 'project_name',
           OLD.project_name, NEW.project_name,
           COALESCE(NEW.updated_by, 'system'),
           NULL,
           COALESCE(NEW.source_type, 'manual')
    WHERE OLD.project_name != NEW.project_name OR (OLD.project_name IS NULL AND NEW.project_name IS NOT NULL);
    -- Log client_company changes
    INSERT INTO proposals_audit_log (
        proposal_id, project_code, field_name, old_value, new_value,
        changed_by, change_reason, change_source
    )
    SELECT NEW.proposal_id, NEW.project_code, 'client_company',
           OLD.client_company, NEW.client_company,
           COALESCE(NEW.updated_by, 'system'),
           NULL,
           COALESCE(NEW.source_type, 'manual')
    WHERE OLD.client_company != NEW.client_company OR (OLD.client_company IS NULL AND NEW.client_company IS NOT NULL);
    -- Log is_active_project changes (proposal became active project)
    INSERT INTO proposals_audit_log (
        proposal_id, project_code, field_name, old_value, new_value,
        changed_by, change_reason, change_source
    )
    SELECT NEW.proposal_id, NEW.project_code, 'is_active_project',
           CAST(OLD.is_active_project AS TEXT), CAST(NEW.is_active_project AS TEXT),
           COALESCE(NEW.updated_by, 'system'),
           'Proposal signed - became active project',
           COALESCE(NEW.source_type, 'manual')
    WHERE OLD.is_active_project != NEW.is_active_project;
    -- Log contract_signed_date changes
    INSERT INTO proposals_audit_log (
        proposal_id, project_code, field_name, old_value, new_value,
        changed_by, change_reason, change_source
    )
    SELECT NEW.proposal_id, NEW.project_code, 'contract_signed_date',
           OLD.contract_signed_date, NEW.contract_signed_date,
           COALESCE(NEW.updated_by, 'system'),
           NULL,
           COALESCE(NEW.source_type, 'manual')
    WHERE OLD.contract_signed_date != NEW.contract_signed_date OR (OLD.contract_signed_date IS NULL AND NEW.contract_signed_date IS NOT NULL);
END;
CREATE TRIGGER trg_proposals_status_change
AFTER UPDATE OF status ON proposals
FOR EACH ROW
WHEN OLD.status IS NOT NEW.status
BEGIN
    INSERT INTO proposal_status_history (
        proposal_id,
        project_code,
        old_status,
        new_status,
        status_date,
        changed_by,
        notes,
        source
    ) VALUES (
        NEW.proposal_id,
        NEW.project_code,
        OLD.status,
        NEW.status,
        DATE('now'),
        'system',
        'Auto-logged: Status changed from "' || COALESCE(OLD.status, 'NULL') || '" to "' || NEW.status || '"',
        'trigger'
    );
END;

### invoices
Billing records linked to projects.
CREATE TABLE IF NOT EXISTS "invoices" (
  invoice_id              INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id              INTEGER,
  invoice_number          TEXT,  -- UNIQUE constraint removed
  description             TEXT,
  invoice_date            DATE,
  due_date                DATE,
  invoice_amount          REAL,
  payment_amount          REAL,
  payment_date            DATE,
  status                  TEXT,
  notes                   TEXT,
  source_ref              TEXT,
  source_type             TEXT CHECK(source_type IN ('manual', 'import', 'ai', 'email_parser')),
  source_reference        TEXT,
  locked_fields           TEXT,
  locked_by               TEXT,
  locked_at               DATETIME,
  created_by              TEXT DEFAULT 'system',
  updated_by              TEXT, breakdown_id TEXT,
  FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
CREATE INDEX idx_invoices_project ON invoices(project_id);
CREATE INDEX idx_invoices_number ON invoices(invoice_number);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_breakdown ON invoices(breakdown_id);
CREATE INDEX idx_invoices_number_breakdown ON invoices(invoice_number, breakdown_id);
CREATE TRIGGER update_breakdown_totals_insert
    AFTER INSERT ON invoices
    FOR EACH ROW
    WHEN NEW.breakdown_id IS NOT NULL
    BEGIN
        UPDATE project_fee_breakdown
        SET
            total_invoiced = (
                SELECT COALESCE(SUM(invoice_amount), 0)
                FROM invoices
                WHERE breakdown_id = NEW.breakdown_id
            ),
            total_paid = (
                SELECT COALESCE(SUM(payment_amount), 0)
                FROM invoices
                WHERE breakdown_id = NEW.breakdown_id
            )
        WHERE breakdown_id = NEW.breakdown_id;
        UPDATE project_fee_breakdown
        SET
            percentage_invoiced = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_invoiced / phase_fee_usd * 100), 1)
                ELSE 0
            END,
            percentage_paid = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_paid / phase_fee_usd * 100), 1)
                ELSE 0
            END
        WHERE breakdown_id = NEW.breakdown_id;
    END;
CREATE TRIGGER update_breakdown_totals_update
    AFTER UPDATE ON invoices
    FOR EACH ROW
    WHEN NEW.breakdown_id IS NOT NULL OR OLD.breakdown_id IS NOT NULL
    BEGIN
        -- Update old breakdown if it changed
        UPDATE project_fee_breakdown
        SET
            total_invoiced = (
                SELECT COALESCE(SUM(invoice_amount), 0)
                FROM invoices
                WHERE breakdown_id = OLD.breakdown_id
            ),
            total_paid = (
                SELECT COALESCE(SUM(payment_amount), 0)
                FROM invoices
                WHERE breakdown_id = OLD.breakdown_id
            )
        WHERE breakdown_id = OLD.breakdown_id AND OLD.breakdown_id IS NOT NULL;
        UPDATE project_fee_breakdown
        SET
            percentage_invoiced = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_invoiced / phase_fee_usd * 100), 1)
                ELSE 0
            END,
            percentage_paid = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_paid / phase_fee_usd * 100), 1)
                ELSE 0
            END
        WHERE breakdown_id = OLD.breakdown_id AND OLD.breakdown_id IS NOT NULL;
        -- Update new breakdown
        UPDATE project_fee_breakdown
        SET
            total_invoiced = (
                SELECT COALESCE(SUM(invoice_amount), 0)
                FROM invoices
                WHERE breakdown_id = NEW.breakdown_id
            ),
            total_paid = (
                SELECT COALESCE(SUM(payment_amount), 0)
                FROM invoices
                WHERE breakdown_id = NEW.breakdown_id
            )
        WHERE breakdown_id = NEW.breakdown_id AND NEW.breakdown_id IS NOT NULL;
        UPDATE project_fee_breakdown
        SET
            percentage_invoiced = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_invoiced / phase_fee_usd * 100), 1)
                ELSE 0
            END,
            percentage_paid = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_paid / phase_fee_usd * 100), 1)
                ELSE 0
            END
        WHERE breakdown_id = NEW.breakdown_id AND NEW.breakdown_id IS NOT NULL;
    END;
CREATE TRIGGER update_breakdown_totals_delete
    AFTER DELETE ON invoices
    FOR EACH ROW
    WHEN OLD.breakdown_id IS NOT NULL
    BEGIN
        UPDATE project_fee_breakdown
        SET
            total_invoiced = (
                SELECT COALESCE(SUM(invoice_amount), 0)
                FROM invoices
                WHERE breakdown_id = OLD.breakdown_id
            ),
            total_paid = (
                SELECT COALESCE(SUM(payment_amount), 0)
                FROM invoices
                WHERE breakdown_id = OLD.breakdown_id
            )
        WHERE breakdown_id = OLD.breakdown_id;
        UPDATE project_fee_breakdown
        SET
            percentage_invoiced = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_invoiced / phase_fee_usd * 100), 1)
                ELSE 0
            END,
            percentage_paid = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_paid / phase_fee_usd * 100), 1)
                ELSE 0
            END
        WHERE breakdown_id = OLD.breakdown_id;
    END;

### emails
Email communications, linked to projects/proposals.
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
, folder TEXT, body_full TEXT, source_type TEXT CHECK(source_type IN ('manual', 'import', 'ai', 'email_parser')) DEFAULT 'email_parser', source_reference TEXT, created_by TEXT DEFAULT 'email_parser', updated_by TEXT, category TEXT, ai_confidence REAL, ai_extracted_data TEXT, date_normalized DATETIME, stage TEXT, collection TEXT);
CREATE INDEX idx_emails_message ON emails(message_id);
CREATE INDEX idx_emails_thread ON emails(thread_id);
CREATE INDEX idx_emails_sender ON emails(sender_email);
CREATE INDEX idx_emails_date ON emails(date);
CREATE INDEX idx_emails_folder ON emails(folder);
CREATE INDEX idx_emails_date_folder
    ON emails(date, folder);
CREATE INDEX idx_emails_body_full
    ON emails(body_full) WHERE body_full IS NOT NULL;
CREATE INDEX idx_emails_category ON emails(category);
CREATE INDEX idx_emails_processed ON emails(processed);
CREATE INDEX idx_emails_date_normalized ON emails(date_normalized);
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

### contacts
People associated with clients and projects.
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
CREATE INDEX idx_contacts_email ON contacts(email);

---

## Table Statistics

- projects|54
- proposals|89
- invoices|253
- emails|3356
- contacts|465
- documents|852
- project_fee_breakdown|279

---

## Key Relationships

```
clients (1) ──────< (N) projects
projects (1) ─────< (N) invoices
projects (1) ─────< (N) emails
projects (1) ─────< (N) project_fee_breakdown
proposals (1) ────< (N) proposal_status_history
proposals (1) ────< (N) email_proposal_links >──── emails
contacts (N) >────< (N) projects (via project_contacts)
```

## Views

The database includes several views for common queries:
- `v_proposal_lifecycle` - Proposal journey tracking
- `v_contract_history` - Contract version history
- `v_pm_workload` - Project manager assignments
- `v_deliverables_dashboard` - Deliverables status
- `v_rfi_summary` - RFI tracking summary

---

## Migration History

Migrations are stored in `database/migrations/` with numbered SQL files.
Current schema version tracked in `schema_migrations` table.

See `database/migrations/` for full migration history.
