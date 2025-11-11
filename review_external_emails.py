#!/usr/bin/env python3
"""
review_external_emails.py

Shows all external email senders grouped by frequency
You manually assign them to projects
System learns from your assignments
"""

import sqlite3
from pathlib import Path

class EmailReviewer:
    def __init__(self):
        self.master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
    
    def show_external_senders(self):
        """Show all external email senders"""
        print("\n" + "="*70)
        print("EXTERNAL EMAIL SENDERS")
        print("="*70)
        
        self.cursor.execute("""
            SELECT 
                sender_email,
                sender_name,
                COUNT(*) as email_count,
                substr(GROUP_CONCAT(subject, ' | '), 1, 100) as sample_subjects
            FROM emails
            WHERE sender_email NOT LIKE '%bensley.com%'
              AND sender_email NOT LIKE '%bensley.co.id%'
              AND sender_email IS NOT NULL
            GROUP BY sender_email
            ORDER BY email_count DESC
        """)
        
        senders = []
        
        print(f"\n{'#':<4} {'Email':<40} {'Name':<25} {'Emails':>7}")
        print("-"*70)
        
        for i, (email, name, count, subjects) in enumerate(self.cursor.fetchall(), 1):
            email_short = email[:38] if len(email) <= 40 else email[:37] + '...'
            name_short = (name or 'Unknown')[:23]
            
            print(f"{i:<4} {email_short:<40} {name_short:<25} {count:>7}")
            
            senders.append({
                'num': i,
                'email': email,
                'name': name,
                'count': count,
                'subjects': subjects
            })
        
        return senders
    
    def show_sender_details(self, sender_email):
        """Show detailed emails from a sender"""
        print(f"\n{'='*70}")
        print(f"EMAILS FROM: {sender_email}")
        print(f"{'='*70}")
        
        self.cursor.execute("""
            SELECT 
                email_id,
                subject,
                date,
                snippet
            FROM emails
            WHERE sender_email = ?
            ORDER BY email_id DESC
            LIMIT 10
        """, (sender_email,))
        
        for email_id, subject, date, snippet in self.cursor.fetchall():
            print(f"\nEmail ID: {email_id}")
            print(f"Subject: {subject}")
            print(f"Date: {date}")
            if snippet:
                print(f"Snippet: {snippet[:100]}...")
            print("-"*70)
    
    def show_projects(self):
        """Show available projects"""
        print("\n" + "="*70)
        print("AVAILABLE PROJECTS")
        print("="*70)
        
        self.cursor.execute("""
            SELECT project_code, project_title
            FROM projects
            ORDER BY project_code
        """)
        
        print(f"\n{'Project Code':<15} {'Title':<55}")
        print("-"*70)
        
        for code, title in self.cursor.fetchall():
            title_short = title[:53] if len(title) <= 55 else title[:52] + '...'
            print(f"{code:<15} {title_short:<55}")
    
    def assign_sender_to_project(self, sender_email, project_code, confidence=0.95):
        """Assign a sender to a project"""
        # Get project_id
        self.cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        result = self.cursor.fetchone()
        
        if not result:
            print(f"❌ Project not found: {project_code}")
            return False
        
        project_id = result[0]
        
        # Add pattern
        self.cursor.execute("""
            INSERT OR REPLACE INTO learned_patterns
            (pattern_type, pattern_key, pattern_value, confidence, occurrences)
            VALUES ('sender_to_project', ?, ?, ?, 1)
        """, (sender_email, project_code, confidence))
        
        # Get domain
        domain = sender_email.split('@')[1] if '@' in sender_email else None
        
        if domain and domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']:
            # Also add domain pattern with lower confidence
            self.cursor.execute("""
                INSERT OR IGNORE INTO learned_patterns
                (pattern_type, pattern_key, pattern_value, confidence, occurrences)
                VALUES ('domain_to_project', ?, ?, ?, 1)
            """, (domain, project_code, confidence * 0.85))
        
        # Link all emails from this sender to the project
        self.cursor.execute("""
            INSERT OR IGNORE INTO email_project_links (email_id, project_id, confidence, link_method, evidence)
            SELECT 
                e.email_id,
                ?,
                ?,
                'manual_assignment',
                'Manually assigned sender to project'
            FROM emails e
            WHERE e.sender_email = ?
        """, (project_id, confidence, sender_email))
        
        linked_count = self.cursor.rowcount
        
        self.conn.commit()
        
        print(f"✅ Assigned {sender_email} → {project_code}")
        print(f"✅ Linked {linked_count} emails")
        
        return True
    
    def save_assignments_to_file(self):
        """Save all learned patterns to a file for backup"""
        output_file = Path.home() / "Desktop/BDS_SYSTEM/email_assignments.txt"
        
        self.cursor.execute("""
            SELECT pattern_key, pattern_value, confidence
            FROM learned_patterns
            WHERE pattern_type = 'sender_to_project'
            ORDER BY pattern_value, confidence DESC
        """)
        
        with open(output_file, 'w') as f:
            f.write("# Email Sender → Project Assignments\n")
            f.write("# Format: email | project_code | confidence\n\n")
            
            for email, project, conf in self.cursor.fetchall():
                f.write(f"{email} | {project} | {conf}\n")
        
        print(f"\n✅ Saved assignments to: {output_file}")
    
    def interactive(self):
        """Interactive assignment mode"""
        print("="*70)
        print("EXTERNAL EMAIL ASSIGNMENT TOOL")
        print("="*70)
        print("\nCommands:")
        print("  list                    - List all external senders")
        print("  show <num>              - Show details for sender #")
        print("  projects                - List all projects")
        print("  assign <num> <project>  - Assign sender # to project")
        print("  save                    - Save assignments to file")
        print("  quit                    - Exit")
        print()
        
        senders = self.show_external_senders()
        
        while True:
            try:
                cmd = input("\n📝 > ").strip()
                
                if not cmd:
                    continue
                
                if cmd in ['quit', 'exit', 'q']:
                    print("👋 Saving and exiting...")
                    self.save_assignments_to_file()
                    break
                
                elif cmd == 'list':
                    senders = self.show_external_senders()
                
                elif cmd == 'projects':
                    self.show_projects()
                
                elif cmd.startswith('show '):
                    try:
                        num = int(cmd.split()[1])
                        if 1 <= num <= len(senders):
                            self.show_sender_details(senders[num-1]['email'])
                        else:
                            print(f"❌ Invalid number. Use 1-{len(senders)}")
                    except (ValueError, IndexError):
                        print("❌ Usage: show <number>")
                
                elif cmd.startswith('assign '):
                    try:
                        # Better parsing for quoted project codes
                        import shlex
                        parts = shlex.split(cmd)  # Handles quotes properly
                        
                        if len(parts) < 3:
                            raise ValueError("Not enough arguments")
                        
                        num = int(parts[1])
                        project_code = parts[2]
                        
                        if 1 <= num <= len(senders):
                            sender = senders[num-1]
                            self.assign_sender_to_project(sender['email'], project_code)
                        else:
                            print(f"❌ Invalid number. Use 1-{len(senders)}")
                    except (ValueError, IndexError) as e:
                        print("❌ Usage: assign <number> <project_code>")
                        print("   Example: assign 5 \"22 BK-095\"")
                        print(f"   Error: {e}")
                
                elif cmd == 'save':
                    self.save_assignments_to_file()
                
                else:
                    print("❌ Unknown command")
            
            except KeyboardInterrupt:
                print("\n👋 Saving and exiting...")
                self.save_assignments_to_file()
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        self.conn.close()

def main():
    reviewer = EmailReviewer()
    reviewer.interactive()

if __name__ == '__main__':
    main()