#!/usr/bin/env python3
"""
query_linked_emails_stable.py

Query emails linked to projects using message_id (STABLE)
"""

import sqlite3
from pathlib import Path

master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
conn = sqlite3.connect(master_db)

print("="*70)
print("QUERY LINKED EMAILS (STABLE VERSION - using message_id)")
print("="*70)
print("\nCommands:")
print("  projects           - Show all projects with email counts")
print("  emails <code>      - Show emails for a project")
print("  contacts <code>    - Show contacts emailing about project")
print("  quit               - Exit")
print()

while True:
    try:
        cmd = input("🔍 > ").strip()
        
        if not cmd:
            continue
        
        if cmd in ['quit', 'exit', 'q']:
            break
        
        elif cmd == 'projects':
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                  p.project_code,
                  p.project_title,
                  COUNT(*) as emails,
                  ROUND(AVG(epl.confidence), 2) as avg_conf
                FROM projects p
                JOIN email_project_links epl ON p.project_id = epl.project_id
                JOIN emails e ON epl.message_id = e.message_id
                GROUP BY p.project_id
                ORDER BY emails DESC
            """)
            
            print(f"\n{'Project':<15} {'Title':<42} {'Emails':>7}  {'Conf':>5}")
            print("-"*70)
            for code, title, count, conf in cursor.fetchall():
                title_short = title[:40] if len(title) <= 42 else title[:39] + '...'
                print(f"{code:<15} {title_short:<42} {count:>7}  {conf:>5}")
        
        elif cmd.startswith('emails '):
            project_code = cmd[7:].strip().strip('"')  # Handle quoted codes
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                  e.sender_email,
                  e.subject,
                  e.date,
                  epl.confidence
                FROM email_project_links epl
                JOIN emails e ON epl.message_id = e.message_id
                JOIN projects p ON epl.project_id = p.project_id
                WHERE p.project_code = ?
                ORDER BY e.date DESC
            """, (project_code,))
            
            results = cursor.fetchall()
            
            if not results:
                print(f"\n❌ No emails found for {project_code}")
            else:
                print(f"\n📧 {len(results)} emails for {project_code}:")
                print("-"*70)
                for sender, subject, date, conf in results:
                    sender_short = sender[:40]
                    subject_short = subject[:50] if subject else '(no subject)'
                    print(f"\n{date} - {sender_short}")
                    print(f"  {subject_short}")
                    print(f"  confidence: {conf}")
        
        elif cmd.startswith('contacts '):
            project_code = cmd[9:].strip().strip('"')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                  e.sender_email,
                  COUNT(*) as email_count
                FROM email_project_links epl
                JOIN emails e ON epl.message_id = e.message_id
                JOIN projects p ON epl.project_id = p.project_id
                WHERE p.project_code = ?
                GROUP BY e.sender_email
                ORDER BY email_count DESC
            """, (project_code,))
            
            results = cursor.fetchall()
            
            if not results:
                print(f"\n❌ No contacts found for {project_code}")
            else:
                print(f"\n👥 Contacts emailing about {project_code}:")
                print("-"*70)
                for sender, count in results:
                    print(f"{sender:<45} {count:>3} emails")
        
        else:
            print("❌ Unknown command")
    
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
        break
    except Exception as e:
        print(f"❌ Error: {e}")

conn.close()
