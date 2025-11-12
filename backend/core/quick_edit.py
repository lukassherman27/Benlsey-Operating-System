#!/usr/bin/env python3
"""
quick_edit.py

Interactive tool to quickly add/edit client data in master database
"""

import sqlite3
import os
import re

class QuickEdit:
    def __init__(self):
        self.db_path = os.path.expanduser('~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db')
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def show_project(self, project_code):
        """Show project details"""
        self.cursor.execute("""
            SELECT 
                p.project_code,
                p.project_title,
                c.company_name,
                p.status,
                p.country
            FROM projects p
            LEFT JOIN clients c ON p.client_id = c.client_id
            WHERE p.project_code LIKE ?
        """, (f'%{project_code}%',))
        
        result = self.cursor.fetchone()
        if result:
            print(f"\n📋 Project: {result[0]}")
            print(f"   Title: {result[1]}")
            print(f"   Client: {result[2] if result[2] else '❌ NO CLIENT'}")
            print(f"   Status: {result[3]}")
            print(f"   Country: {result[4]}")
            return result[0]  # Return full project code
        else:
            print(f"\n❌ Project not found: {project_code}")
            return None
    
    def add_client(self, company_name, country=None, industry=None):
        """Add or get client"""
        # Check if exists
        self.cursor.execute("SELECT client_id FROM clients WHERE company_name = ?", (company_name,))
        result = self.cursor.fetchone()
        
        if result:
            print(f"✅ Client already exists: {company_name}")
            return result[0]
        
        # Add new client
        self.cursor.execute("""
            INSERT INTO clients (company_name, country, industry, notes)
            VALUES (?, ?, ?, 'Added manually')
        """, (company_name, country, industry))
        
        self.conn.commit()
        client_id = self.cursor.lastrowid
        print(f"✅ Added new client: {company_name} (ID: {client_id})")
        return client_id
    
    def link_client_to_project(self, project_code, company_name):
        """Link a client to a project"""
        # Get or create client
        client_id = self.add_client(company_name)
        
        # Update project
        self.cursor.execute("""
            UPDATE projects 
            SET client_id = ?
            WHERE project_code = ?
        """, (client_id, project_code))
        
        self.conn.commit()
        
        if self.cursor.rowcount > 0:
            print(f"✅ Linked '{company_name}' to project {project_code}")
        else:
            print(f"❌ Project not found: {project_code}")
    
    def add_contact(self, email, name, client_name, role=None, phone=None):
        """Add contact to a client"""
        # Get client
        self.cursor.execute("SELECT client_id FROM clients WHERE company_name = ?", (client_name,))
        result = self.cursor.fetchone()
        
        if not result:
            print(f"❌ Client not found: {client_name}")
            print(f"   Adding client first...")
            client_id = self.add_client(client_name)
        else:
            client_id = result[0]
        
        # Add contact
        self.cursor.execute("""
            INSERT OR REPLACE INTO contacts (client_id, email, name, role, phone)
            VALUES (?, ?, ?, ?, ?)
        """, (client_id, email, name, role, phone))
        
        self.conn.commit()
        print(f"✅ Added contact: {name} ({email}) to {client_name}")
    
    def search_projects(self, keyword):
        """Search projects by keyword"""
        self.cursor.execute("""
            SELECT 
                p.project_code,
                p.project_title,
                c.company_name,
                p.status
            FROM projects p
            LEFT JOIN clients c ON p.client_id = c.client_id
            WHERE p.project_code LIKE ? 
               OR p.project_title LIKE ?
            LIMIT 10
        """, (f'%{keyword}%', f'%{keyword}%'))
        
        results = self.cursor.fetchall()
        if results:
            print(f"\n🔍 Found {len(results)} projects:")
            for r in results:
                client = r[2] if r[2] else "NO CLIENT"
                print(f"   {r[0]} - {r[1][:50]} | Client: {client}")
        else:
            print(f"\n❌ No projects found matching: {keyword}")
    
    def list_clients(self):
        """List all clients"""
        self.cursor.execute("""
            SELECT 
                c.company_name,
                COUNT(p.project_id) as project_count
            FROM clients c
            LEFT JOIN projects p ON c.client_id = p.client_id
            GROUP BY c.client_id
            ORDER BY project_count DESC
        """)
        
        results = self.cursor.fetchall()
        if results:
            print(f"\n📊 Clients in database:")
            for r in results:
                print(f"   {r[0]} ({r[1]} projects)")
        else:
            print("\n❌ No clients in database yet")
    
    def interactive(self):
        """Interactive mode"""
        print("="*70)
        print("QUICK EDIT - Interactive Database Editor")
        print("="*70)
        print("\nCommands:")
        print("  show <project>              - Show project details")
        print("  search <keyword>            - Search projects")
        print("  clients                     - List all clients")
        print("  add client <name>           - Add a new client")
        print("  link <project> to <client>  - Link project to client")
        print("  add contact <email> <name> to <client>")
        print("  quit                        - Exit")
        print()
        
        while True:
            try:
                cmd = input("📝 > ").strip()
                
                if not cmd:
                    continue
                
                if cmd.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                # Show project
                elif cmd.startswith('show '):
                    project = cmd[5:].strip()
                    self.show_project(project)
                
                # Search
                elif cmd.startswith('search '):
                    keyword = cmd[7:].strip()
                    self.search_projects(keyword)
                
                # List clients
                elif cmd == 'clients':
                    self.list_clients()
                
                # Add client
                elif cmd.startswith('add client '):
                    client_name = cmd[11:].strip().strip('"')
                    self.add_client(client_name)
                
                # Link project to client
                elif ' to ' in cmd and cmd.startswith('link '):
                    parts = cmd[5:].split(' to ')
                    if len(parts) == 2:
                        project = parts[0].strip()
                        client = parts[1].strip().strip('"')
                        self.link_client_to_project(project, client)
                    else:
                        print("❌ Format: link <project> to <client>")
                
                # Add contact
                elif cmd.startswith('add contact '):
                    # Parse: add contact email "Name" to Client
                    match = re.match(r'add contact (\S+) "([^"]+)" to (.+)', cmd)
                    if match:
                        email = match.group(1)
                        name = match.group(2)
                        client = match.group(3).strip().strip('"')
                        self.add_contact(email, name, client)
                    else:
                        print('❌ Format: add contact email "Name" to Client')
                
                else:
                    print("❌ Unknown command. Type 'quit' to exit.")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        self.conn.close()

def main():
    editor = QuickEdit()
    editor.interactive()

if __name__ == '__main__':
    main()
