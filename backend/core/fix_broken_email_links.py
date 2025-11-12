#!/usr/bin/env python3
"""
fix_broken_email_links.py

CRITICAL FIX: Repairs email_project_links that broke due to email_id changes
Uses message_id (stable) to reconnect links to emails
"""

import sqlite3
from pathlib import Path

def fix_links():
    master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
    conn = sqlite3.connect(master_db)
    cursor = conn.cursor()
    
    print("="*70)
    print("EMERGENCY FIX: Repairing Broken Email Links")
    print("="*70)
    
    # Step 1: Add message_id column to email_project_links if it doesn't exist
    print("\n📋 Adding message_id column to links table...")
    try:
        cursor.execute("""
            ALTER TABLE email_project_links 
            ADD COLUMN message_id TEXT
        """)
        print("   ✅ Column added")
    except:
        print("   ✅ Column already exists")
    
    # Step 2: For existing links, try to find message_id from old email_id
    # (This won't work for orphaned links, but worth trying)
    print("\n🔧 Attempting to salvage orphaned links...")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM email_project_links epl
        LEFT JOIN emails e ON epl.email_id = e.email_id
        WHERE e.email_id IS NULL
    """)
    orphaned = cursor.fetchone()[0]
    print(f"   ⚠️  Found {orphaned} orphaned links")
    
    # Step 3: Delete orphaned links (they can't be recovered)
    print("\n🗑️  Removing orphaned links...")
    cursor.execute("""
        DELETE FROM email_project_links
        WHERE email_id NOT IN (SELECT email_id FROM emails)
    """)
    deleted = cursor.rowcount
    print(f"   ✅ Deleted {deleted} orphaned links")
    
    # Step 4: Re-apply learned patterns to recreate links
    print("\n🔄 Re-linking emails using learned patterns...")
    
    # Get all learned sender patterns
    cursor.execute("""
        SELECT pattern_key, pattern_value, confidence
        FROM learned_patterns
        WHERE pattern_type = 'sender_to_project'
    """)
    
    patterns = cursor.fetchall()
    links_created = 0
    
    for sender_email, project_code, confidence in patterns:
        # Get project_id
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        result = cursor.fetchone()
        if not result:
            continue
        project_id = result[0]
        
        # Link all emails from this sender
        cursor.execute("""
            INSERT OR IGNORE INTO email_project_links 
            (email_id, project_id, confidence, link_method, evidence, message_id)
            SELECT 
                e.email_id,
                ?,
                ?,
                'pattern_reapply',
                'Relinked after sync using ' || ?,
                e.message_id
            FROM emails e
            WHERE e.sender_email = ?
        """, (project_id, confidence, sender_email, sender_email))
        
        links_created += cursor.rowcount
    
    print(f"   ✅ Created {links_created} new links")
    
    conn.commit()
    
    # Step 5: Show results
    print("\n" + "="*70)
    print("FIX COMPLETE")
    print("="*70)
    
    cursor.execute("SELECT COUNT(*) FROM email_project_links")
    total_links = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(DISTINCT epl.email_id)
        FROM email_project_links epl
        JOIN emails e ON epl.email_id = e.email_id
    """)
    valid_links = cursor.fetchone()[0]
    
    print(f"\n✅ Total links: {total_links}")
    print(f"✅ Valid links: {valid_links}")
    print(f"✅ Deleted orphaned: {deleted}")
    print(f"✅ Created new: {links_created}")
    
    # Show top projects
    print("\n📊 Projects with most emails:")
    cursor.execute("""
        SELECT 
            p.project_code,
            p.project_title,
            COUNT(epl.email_id) as emails
        FROM projects p
        JOIN email_project_links epl ON p.project_id = epl.project_id
        JOIN emails e ON epl.email_id = e.email_id
        GROUP BY p.project_id
        ORDER BY emails DESC
        LIMIT 10
    """)
    
    for code, title, count in cursor.fetchall():
        title_short = title[:40] + '...' if len(title) > 40 else title
        print(f"   {code}: {count} emails - {title_short}")
    
    conn.close()

if __name__ == '__main__':
    fix_links()
