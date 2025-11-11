#!/usr/bin/env python3
"""
query_linked_emails.py

Query tool to explore your intelligently-linked emails
See the results of the auto-linking system
"""

import sqlite3
import os

class LinkedEmailsQuery:
    def __init__(self):
        self.master_db = os.path.expanduser('~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db')
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
    
    def show_projects_with_emails(self):
        """Show projects and how many emails are linked"""
        print("\n📊 PROJECTS WITH LINKED EMAILS")
        print("="*70)
        
        self.cursor.execute("""
            SELECT 
                p.project_code,
                p.project_title,
                COUNT(epl.email_id) as email_count,
                ROUND(AVG(epl.confidence), 2) as avg_confidence
            FROM projects p
            LEFT JOIN email_project_links epl ON p.project_id = epl.project_id
            GROUP BY p.project_id
            HAVING email_count > 0
            ORDER BY email_count DESC
            LIMIT 20
        """)
        
        print(f"\n{'Project':<15} {'Title':<40} {'Emails':>8} {'Avg Conf':>10}")
        print("-"*70)
        
        for code, title, count, conf in self.cursor.fetchall():
            title_short = title[:38] + '..' if len(title) > 40 else title
            print(f"{code:<15} {title_short:<40} {count:>8} {conf:>10}")
    
    def show_emails_for_project(self, project_code):
        """Show all emails linked to a specific project"""
        print(f"\n📧 EMAILS FOR PROJECT: {project_code}")
        print("="*70)
        
        self.cursor.execute("""
            SELECT 
                e.sender_email,
                e.subject,
                e.date,
                epl.confidence,
                epl.link_method,
                epl.evidence
            FROM email_project_links epl
            JOIN emails e ON epl.email_id = e.email_id
            JOIN projects p ON epl.project_id = p.project_id
            WHERE p.project_code = ?
            ORDER BY e.date DESC
        """, (project_code,))
        
        results = self.cursor.fetchall()
        
        if not results:
            print(f"❌ No emails found for project {project_code}")
            return
        
        for sender, subject, date, conf, method, evidence in results:
            print(f"\nFrom: {sender}")
            print(f"Subject: {subject}")
            print(f"Date: {date}")
            print(f"Confidence: {conf:.2f} ({method})")
            print(f"Evidence: {evidence}")
            print("-"*70)
    
    def show_emails_by_tag(self, tag):
        """Show emails with a specific tag"""
        print(f"\n🏷️  EMAILS TAGGED: {tag}")
        print("="*70)
        
        self.cursor.execute("""
            SELECT 
                e.sender_email,
                e.subject,
                e.date,
                et.confidence
            FROM email_tags et
            JOIN emails e ON et.email_id = e.email_id
            WHERE et.tag = ?
            ORDER BY e.date DESC
            LIMIT 20
        """, (tag,))
        
        results = self.cursor.fetchall()
        
        if not results:
            print(f"❌ No emails found with tag: {tag}")
            return
        
        for sender, subject, date, conf in results:
            print(f"{date[:10]} | {sender[:30]:30} | {subject[:40]}")
    
    def show_available_tags(self):
        """Show all available tags"""
        print("\n🏷️  AVAILABLE TAGS")
        print("="*70)
        
        self.cursor.execute("""
            SELECT tag, COUNT(*) as count
            FROM email_tags
            GROUP BY tag
            ORDER BY count DESC
        """)
        
        for tag, count in self.cursor.fetchall():
            print(f"  {tag}: {count}")
    
    def interactive(self):
        """Interactive query mode"""
        print("="*70)
        print("LINKED EMAILS QUERY TOOL")
        print("="*70)
        print("\nCommands:")
        print("  projects            - Show projects with linked emails")
        print("  emails <code>       - Show emails for a project")
        print("  tags                - List available tags")
        print("  tag <tagname>       - Show emails with tag")
        print("  quit                - Exit")
        print()
        
        while True:
            try:
                cmd = input("🔍 > ").strip()
                
                if not cmd:
                    continue
                
                if cmd.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                elif cmd == 'projects':
                    self.show_projects_with_emails()
                
                elif cmd.startswith('emails '):
                    project_code = cmd[7:].strip()
                    self.show_emails_for_project(project_code)
                
                elif cmd == 'tags':
                    self.show_available_tags()
                
                elif cmd.startswith('tag '):
                    tag = cmd[4:].strip()
                    self.show_emails_by_tag(tag)
                
                else:
                    print("❌ Unknown command")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        self.conn.close()

def main():
    query = LinkedEmailsQuery()
    query.interactive()

if __name__ == '__main__':
    main()
