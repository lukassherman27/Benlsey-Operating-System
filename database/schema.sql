-- Bensley Intelligence Platform Database Schema
-- Generated: 2024-11-12

CREATE TABLE projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_code TEXT UNIQUE NOT NULL,
            project_name TEXT,
            client_name TEXT,
            status TEXT DEFAULT 'active',
            value REAL,
            start_date DATE,
            completion_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE emails (
            email_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_email TEXT,
            recipients TEXT,
            subject TEXT,
            snippet TEXT,
            body TEXT,
            date TIMESTAMP,
            processed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE email_project_links (
            link_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER,
            project_id INTEGER,
            confidence REAL DEFAULT 0.0,
            link_method TEXT,
            evidence TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email_id) REFERENCES emails(email_id),
            FOREIGN KEY (project_id) REFERENCES projects(project_id),
            UNIQUE(email_id, project_id)
        );

CREATE TABLE email_tags (
            tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER,
            tag TEXT,
            tag_type TEXT,
            confidence REAL DEFAULT 1.0,
            created_by TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email_id) REFERENCES emails(email_id)
        );

CREATE TABLE tag_mappings (
            mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_tag TEXT UNIQUE,
            canonical_tag TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE learned_patterns (
            pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT,
            pattern_key TEXT,
            pattern_value TEXT,
            confidence REAL DEFAULT 0.0,
            occurrences INTEGER DEFAULT 1,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE contacts (
            contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            company TEXT,
            role TEXT,
            is_client INTEGER DEFAULT 0,
            first_seen TIMESTAMP,
            last_seen TIMESTAMP,
            email_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE rfis (
            rfi_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT,
            deadline DATE,
            assigned_to TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        );

CREATE TABLE proposals (
            proposal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_code TEXT,
            client_name TEXT,
            project_name TEXT,
            value REAL,
            status TEXT DEFAULT 'draft',
            submission_date DATE,
            follow_up_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE project_milestones (
            milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            milestone_name TEXT,
            due_date DATE,
            completion_date DATE,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        );

CREATE TABLE action_items_tracking (
            action_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            description TEXT,
            assigned_to TEXT,
            due_date DATE,
            status TEXT DEFAULT 'pending',
            priority TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        );

