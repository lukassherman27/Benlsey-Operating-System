#!/usr/bin/env python3
"""
Initialize Bensley Intelligence Platform Database
Creates all necessary tables for the platform
"""

import sqlite3
import os
from pathlib import Path

def create_database():
    """Create database with all necessary tables"""

    # Database path
    db_path = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Creating database at: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Core Projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
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
        )
    """)

    # Emails table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            email_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_email TEXT,
            recipients TEXT,
            subject TEXT,
            snippet TEXT,
            body TEXT,
            date TIMESTAMP,
            processed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Email-Project links
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_project_links (
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
        )
    """)

    # Email tags
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_tags (
            tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER,
            tag TEXT,
            tag_type TEXT,
            confidence REAL DEFAULT 1.0,
            created_by TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email_id) REFERENCES emails(email_id)
        )
    """)

    # Tag mappings for normalization
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tag_mappings (
            mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_tag TEXT UNIQUE,
            canonical_tag TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Learned patterns for intelligence
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learned_patterns (
            pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT,
            pattern_key TEXT,
            pattern_value TEXT,
            confidence REAL DEFAULT 0.0,
            occurrences INTEGER DEFAULT 1,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Contacts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
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
        )
    """)

    # RFIs (Requests for Information)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rfis (
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
        )
    """)

    # Proposals
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proposals (
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
        )
    """)

    # Project milestones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_milestones (
            milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            milestone_name TEXT,
            due_date DATE,
            completion_date DATE,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        )
    """)

    # Action items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS action_items_tracking (
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
        )
    """)

    conn.commit()
    print("✅ Database tables created successfully!")

    # Insert some sample data for testing
    cursor.execute("""
        INSERT OR IGNORE INTO projects (project_code, project_name, client_name, status, value)
        VALUES
            ('BK-001', 'Luxury Resort Design', 'Mandarin Oriental', 'active', 2500000),
            ('BK-002', 'Boutique Hotel Interiors', 'Rosewood Hotels', 'active', 1800000),
            ('BK-003', 'Villa Master Plan', 'Private Client', 'in-progress', 950000)
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO proposals (project_code, client_name, project_name, value, status, submission_date)
        VALUES
            ('BK-004', 'Four Seasons', 'Spa Design Proposal', 750000, 'submitted', '2024-11-01'),
            ('BK-005', 'Aman Resorts', 'Landscape Architecture', 1200000, 'draft', NULL)
    """)

    conn.commit()
    print("✅ Sample data inserted!")

    # Show stats
    cursor.execute("SELECT COUNT(*) FROM projects")
    project_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM proposals")
    proposal_count = cursor.fetchone()[0]

    print(f"\n📊 Database Summary:")
    print(f"   Projects: {project_count}")
    print(f"   Proposals: {proposal_count}")
    print(f"\n✅ Database ready at: {db_path}")

    conn.close()

if __name__ == '__main__':
    create_database()
