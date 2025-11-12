#!/usr/bin/env python3
"""
fix_project_id_mismatches.py

CRITICAL: Fixes email_project_links after sync_master.py changed project_ids
Uses project_code (stable) to reconnect links
"""

import sqlite3
from pathlib import Path

def fix_project_ids():
    master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
    conn = sqlite3.connect(master_db)
    cursor = conn.cursor()
    
    print("="*70)
    print("EMERGENCY FIX: Repairing Project ID Mismatches")
    print("="*70)
    
    # Step 1: Add project_code column to email_project_links if needed
    print("\n📋 Adding project_code column to links table...")
    try:
        cursor.execute("""
            ALTER TABLE email_project_links 
            ADD COLUMN project_code TEXT
        """)
        print("   ✅ Column added")
    except:
        print("   ✅ Column already exists")
    
    # Step 2: Get learned patterns to reconstruct project codes
    print("\n🔍 Reading learned patterns...")
    cursor.execute("""
        SELECT pattern_key, pattern_value
        FROM learned_patterns
        WHERE pattern_type = 'sender_to_project'
    """)
    
    sender_to_project = {sender: code for sender, code in cursor.fetchall()}
    print(f"   ✅ Found {len(sender_to_project)} sender→project patterns")
    
    # Step 3: For each link, find the project_code
    print("\n🔄 Reconstructing project codes for links...")
    cursor.execute("""
        SELECT 
            epl.email_id,
            epl.project_id as old_project_id,
            e.sender_email,
            e.subject
        FROM email_project_links epl
        JOIN emails e ON epl.email_id = e.email_id
    """)
    
    links = cursor.fetchall()
    fixed_count = 0
    
    for email_id, old_proj_id, sender, subject in links:
        project_code = None
        
        # Try to find project code from sender pattern
        if sender in sender_to_project:
            project_code = sender_to_project[sender]
        
        # If found, delete old link and insert new one
        if project_code:
            # Get new project_id
            cursor.execute("""
                SELECT project_id FROM projects WHERE project_code = ?
            """, (project_code,))
            
            result = cursor.fetchone()
            if result:
                new_project_id = result[0]
                
                # Delete old link
                cursor.execute("""
                    DELETE FROM email_project_links
                    WHERE email_id = ? AND project_id = ?
                """, (email_id, old_proj_id))
                
                # Insert new link with correct project_id
                try:
                    cursor.execute("""
                        INSERT INTO email_project_links 
                        (email_id, project_id, confidence, link_method, evidence, 
                         message_id, project_code)
                        SELECT 
                            ?,
                            ?,
                            0.95,
                            'id_fix',
                            'Fixed after project_id mismatch',
                            e.message_id,
                            ?
                        FROM emails e
                        WHERE e.email_id = ?
                    """, (email_id, new_project_id, project_code, email_id))
                    
                    fixed_count += 1
                except:
                    pass  # Skip duplicates
    
    print(f"   ✅ Fixed {fixed_count} links")
    
    # Step 4: Delete links that couldn't be fixed
    print("\n🗑️  Removing unfixable links...")
    cursor.execute("""
        DELETE FROM email_project_links
        WHERE project_id NOT IN (SELECT project_id FROM projects)
    """)
    deleted = cursor.rowcount
    print(f"   ✅ Deleted {deleted} orphaned links")
    
    conn.commit()
    
    # Step 5: Verify
    print("\n✅ VERIFICATION")
    print("="*70)
    
    cursor.execute("""
        SELECT COUNT(*) FROM email_project_links
    """)
    total = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*)
        FROM email_project_links epl
        JOIN projects p ON epl.project_id = p.project_id
    """)
    valid = cursor.fetchone()[0]
    
    print(f"\nTotal links: {total}")
    print(f"Valid links: {valid}")
    print(f"Fixed: {fixed_count}")
    print(f"Deleted: {deleted}")
    
    # Show projects with emails now
    print("\n📊 Projects with linked emails:")
    cursor.execute("""
        SELECT
          p.project_code,
          COUNT(epl.email_id) as emails
        FROM projects p
        JOIN email_project_links epl ON p.project_id = epl.project_id
        GROUP BY p.project_code
        ORDER BY emails DESC
        LIMIT 15
    """)
    
    for code, count in cursor.fetchall():
        print(f"   {code}: {count} emails")
    
    conn.close()
    
    print("\n✅ Fix complete!")

if __name__ == '__main__':
    fix_project_ids()