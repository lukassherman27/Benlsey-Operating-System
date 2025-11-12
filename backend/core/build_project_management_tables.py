#!/usr/bin/env python3
"""
build_project_management_tables.py

Creates comprehensive project management tables for:
- RFI tracking
- Schedule/milestones  
- Action items
- Status history
- Deliverables
- Communication log

Updated: Oct 24, 2025 - Aligned with current database schema
"""

import sqlite3
from pathlib import Path

def create_tables():
    master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
    conn = sqlite3.connect(master_db)
    cursor = conn.cursor()
    
    print("="*70)
    print("BUILDING PROJECT MANAGEMENT TABLES")
    print("="*70)
    
    # 1. RFI Tracking
    print("\n📋 Creating RFI tracking table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rfis (
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rfi_project ON rfis(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rfi_project_code ON rfis(project_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rfi_status ON rfis(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rfi_due ON rfis(date_due)")
    print("   ✅ RFI table created")
    
    # 2. Project Schedule & Milestones
    print("\n📅 Creating schedule/milestones table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_milestones (
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
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_milestone_project ON project_milestones(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_milestone_project_code ON project_milestones(project_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_milestone_date ON project_milestones(planned_date)")
    print("   ✅ Milestones table created")
    
    # 3. Action Items (using new name to avoid conflict)
    print("\n✅ Creating action items table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS action_items_tracking (
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_action_track_project ON action_items_tracking(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_action_track_code ON action_items_tracking(project_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_action_track_assigned ON action_items_tracking(assigned_to)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_action_track_due ON action_items_tracking(due_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_action_track_status ON action_items_tracking(status)")
    print("   ✅ Action items table created")
    
    # 4. Project Status History  
    print("\n📊 Creating status history table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_status_tracking (
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_track_project ON project_status_tracking(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_track_code ON project_status_tracking(project_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_track_date ON project_status_tracking(status_date)")
    print("   ✅ Status history table created")
    
    # 5. Deliverables Tracking
    print("\n📦 Creating deliverables table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deliverables (
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
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deliverable_project ON deliverables(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deliverable_code ON deliverables(project_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deliverable_due ON deliverables(due_date)")
    print("   ✅ Deliverables table created")
    
    # 6. Communication Log
    print("\n💬 Creating communication log table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS communication_log (
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
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comm_project ON communication_log(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comm_code ON communication_log(project_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comm_date ON communication_log(comm_date)")
    print("   ✅ Communication log table created")
    
    conn.commit()
    
    # Import timeline data from project_metadata (from Excel import)
    print("\n📥 Importing timeline data from project_metadata...")
    cursor.execute("""
        INSERT OR IGNORE INTO project_milestones
        (project_id, project_code, phase, milestone_name, actual_date, status)
        SELECT 
            pm.project_id,
            p.project_code,
            CASE 
                WHEN pm.metadata_key LIKE '%first_contact%' THEN 'initiation'
                WHEN pm.metadata_key LIKE '%drafting%' THEN 'concept'
                WHEN pm.metadata_key LIKE '%proposal_sent%' THEN 'proposal'
                WHEN pm.metadata_key LIKE '%contract_signed%' THEN 'contract'
                ELSE 'other'
            END,
            REPLACE(REPLACE(pm.metadata_key, 'timeline_', ''), '_', ' '),
            pm.metadata_value,
            'complete'
        FROM project_metadata pm
        JOIN projects p ON pm.project_id = p.project_id
        WHERE pm.metadata_key LIKE 'timeline_%'
    """)
    imported = cursor.rowcount
    print(f"   ✅ Imported {imported} timeline milestones from Excel")
    
    conn.commit()
    
    # Show summary
    print("\n" + "="*70)
    print("TABLES CREATED SUCCESSFULLY")
    print("="*70)
    
    tables_to_check = [
        'rfis', 'project_milestones', 'action_items_tracking',
        'project_status_tracking', 'deliverables', 'communication_log'
    ]
    
    print("\n📋 Project Management Tables:")
    for table in tables_to_check:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   {table:<30} {count:>6} rows")
    
    conn.close()
    
    print("\n✅ Ready for data extraction and reporting!")
    print("\nNext steps:")
    print("  1. Run: python3 extract_from_emails.py")
    print("  2. Run: python3 project_reports.py")

if __name__ == '__main__':
    create_tables()
