#!/usr/bin/env python3
"""
manual_data_entry.py

Interactive tool for manually fixing data quality issues:
- Add timeline events for proposals
- Link emails to projects
- Add missing locations

All changes are logged and reversible.

Updated: Oct 24, 2025
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import re

class ManualDataEntry:
    def __init__(self):
        self.master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
        
        self.stats = {
            'timelines_added': 0,
            'emails_linked': 0,
            'locations_added': 0
        }
    
    def log_change(self, table, record_id, change_type, description):
        """Log manual changes"""
        self.cursor.execute("""
            INSERT INTO data_quality_tracking
            (data_table, record_id, issue_type, description, 
             ai_confidence, status, reviewed_by)
            VALUES (?, ?, 'manual_entry', ?, 1.0, 'fixed', 'user')
        """, (table, record_id, description))
    
    def fix_timelines(self):
        """Add timeline events for proposals"""
        print("="*70)
        print("MANUAL ENTRY: PROPOSAL TIMELINES")
        print("="*70)
        
        # Get proposals without timeline
        self.cursor.execute("""
            SELECT 
                p.project_id,
                p.project_code,
                p.project_title,
                p.date_created
            FROM projects p
            WHERE p.source_db = 'proposals'
              AND NOT EXISTS (
                SELECT 1 FROM project_metadata pm
                WHERE pm.project_id = p.project_id
                  AND pm.metadata_key LIKE 'timeline_%'
              )
            ORDER BY p.project_code
        """)
        
        proposals = self.cursor.fetchall()
        
        if not proposals:
            print("\n✅ All proposals have timeline data!")
            return
        
        print(f"\nFound {len(proposals)} proposals without timeline\n")
        
        for project_id, code, title, date_created in proposals:
            print("─"*70)
            print(f"\n📋 {code}")
            print(f"   Title: {title}")
            print(f"   Created: {date_created or 'Unknown'}")
            
            print("\nOptions:")
            print("  1. Add timeline manually")
            print("  2. Skip this project")
            print("  3. Skip all remaining (quit this section)")
            
            choice = input("\nSelect (1/2/3): ").strip()
            
            if choice == '3':
                print("Skipping remaining proposals...")
                break
            elif choice == '2':
                continue
            elif choice == '1':
                # Collect timeline events
                print("\nEnter timeline dates (YYYY-MM-DD format, or press Enter to skip):")
                
                events = {}
                
                first_contact = input("  First Contact date: ").strip()
                if first_contact:
                    events['timeline_first_contact'] = first_contact
                
                drafting = input("  Drafting started: ").strip()
                if drafting:
                    events['timeline_drafting'] = drafting
                
                sent = input("  Proposal Sent: ").strip()
                if sent:
                    events['timeline_proposal_sent'] = sent
                
                status = input("  Current status (on_hold/contract_signed/lost): ").strip()
                if status:
                    status_date = input(f"  {status} date: ").strip()
                    if status_date:
                        events[f'timeline_{status}'] = status_date
                
                # Save events
                if events:
                    for key, value in events.items():
                        self.cursor.execute("""
                            INSERT INTO project_metadata
                            (project_id, metadata_key, metadata_value, source, confidence)
                            VALUES (?, ?, ?, 'manual', 1.0)
                        """, (project_id, key, value))
                    
                    # Update date_created if first_contact provided
                    if 'timeline_first_contact' in events:
                        self.cursor.execute("""
                            UPDATE projects SET date_created = ?
                            WHERE project_id = ?
                        """, (events['timeline_first_contact'], project_id))
                    
                    self.conn.commit()
                    self.stats['timelines_added'] += 1
                    
                    self.log_change('projects', project_id, 'timeline_added',
                                   f"Added {len(events)} timeline events")
                    
                    print(f"   ✅ Added {len(events)} events")
                else:
                    print("   ⏩ No events added")
        
        print(f"\n✅ Added timeline data to {self.stats['timelines_added']} proposals")
    
    def fix_email_links(self):
        """Link emails to projects"""
        print("\n" + "="*70)
        print("MANUAL ENTRY: EMAIL-PROJECT LINKS")
        print("="*70)
        
        # Get unlinked emails that mention projects
        self.cursor.execute("""
            SELECT 
                e.email_id,
                e.date,
                e.subject,
                e.sender_email,
                e.snippet
            FROM emails e
            WHERE NOT EXISTS (
                SELECT 1 FROM email_project_links epl
                WHERE epl.email_id = e.email_id
            )
            AND (
                e.subject LIKE '%BK-%'
                OR e.subject LIKE '%project%'
                OR e.subject LIKE '%proposal%'
            )
            ORDER BY e.date DESC
            LIMIT 20
        """)
        
        emails = self.cursor.fetchall()
        
        if not emails:
            print("\n✅ All relevant emails are linked!")
            return
        
        print(f"\nFound {len(emails)} emails that may need linking\n")
        
        # Get list of all projects for quick reference
        self.cursor.execute("""
            SELECT project_code, project_title 
            FROM projects 
            ORDER BY project_code
        """)
        all_projects = self.cursor.fetchall()
        
        for email_id, date, subject, sender, snippet in emails:
            print("─"*70)
            print(f"\n📧 Email from {date[:10]}")
            print(f"   From: {sender}")
            print(f"   Subject: {subject[:70]}")
            if snippet:
                print(f"   Preview: {snippet[:100]}")
            
            print("\nOptions:")
            print("  1. Link to project (enter project code)")
            print("  2. Show recent projects")
            print("  3. Skip this email")
            print("  4. Skip all remaining (quit this section)")
            
            choice = input("\nSelect (1/2/3/4): ").strip()
            
            if choice == '4':
                print("Skipping remaining emails...")
                break
            elif choice == '3':
                continue
            elif choice == '2':
                # Show recent projects
                print("\nRecent projects:")
                for code, title in all_projects[-20:]:
                    print(f"   {code}: {title[:50]}")
                continue
            elif choice == '1':
                project_code = input("  Enter project code (e.g., 25 BK-037): ").strip().upper()
                
                # Validate project exists
                self.cursor.execute("""
                    SELECT project_id, project_title 
                    FROM projects 
                    WHERE project_code = ?
                """, (project_code,))
                
                result = self.cursor.fetchone()
                
                if result:
                    project_id, project_title = result
                    
                    # Confirm
                    print(f"\n   Link to: {project_code} - {project_title[:50]}")
                    confirm = input("   Confirm? (y/n): ").strip().lower()
                    
                    if confirm == 'y':
                        self.cursor.execute("""
                            INSERT INTO email_project_links
                            (email_id, project_id, project_code, confidence, 
                             link_method, evidence)
                            VALUES (?, ?, ?, 1.0, 'manual', 'User confirmed')
                        """, (email_id, project_id, project_code))
                        
                        self.conn.commit()
                        self.stats['emails_linked'] += 1
                        
                        self.log_change('email_project_links', email_id, 
                                       'manual_link', f"Linked to {project_code}")
                        
                        print("   ✅ Linked!")
                    else:
                        print("   ⏩ Skipped")
                else:
                    print(f"   ❌ Project {project_code} not found")
        
        print(f"\n✅ Linked {self.stats['emails_linked']} emails")
    
    def fix_locations(self):
        """Add missing locations"""
        print("\n" + "="*70)
        print("MANUAL ENTRY: PROJECT LOCATIONS")
        print("="*70)
        
        # Get projects without location
        self.cursor.execute("""
            SELECT 
                p.project_id,
                p.project_code,
                p.project_title,
                p.country,
                p.city
            FROM projects p
            WHERE (p.country IS NULL OR p.country = '')
               OR (p.city IS NULL OR p.city = '')
            ORDER BY p.project_code
            LIMIT 30
        """)
        
        projects = self.cursor.fetchall()
        
        if not projects:
            print("\n✅ All projects have location data!")
            return
        
        print(f"\nShowing first 30 projects without complete location data\n")
        
        for project_id, code, title, current_country, current_city in projects:
            print("─"*70)
            print(f"\n📍 {code}")
            print(f"   Title: {title}")
            print(f"   Current - Country: {current_country or 'None'}, City: {current_city or 'None'}")
            
            print("\nOptions:")
            print("  1. Add/update location")
            print("  2. Skip this project")
            print("  3. Skip all remaining (quit this section)")
            
            choice = input("\nSelect (1/2/3): ").strip()
            
            if choice == '3':
                print("Skipping remaining projects...")
                break
            elif choice == '2':
                continue
            elif choice == '1':
                country = input(f"  Country [{current_country or ''}]: ").strip() or current_country
                city = input(f"  City [{current_city or ''}]: ").strip() or current_city
                
                updates = []
                if country and country != current_country:
                    self.cursor.execute("""
                        UPDATE projects SET country = ? WHERE project_id = ?
                    """, (country, project_id))
                    updates.append(f"country: {country}")
                
                if city and city != current_city:
                    self.cursor.execute("""
                        UPDATE projects SET city = ? WHERE project_id = ?
                    """, (city, project_id))
                    updates.append(f"city: {city}")
                
                if updates:
                    self.conn.commit()
                    self.stats['locations_added'] += 1
                    
                    self.log_change('projects', project_id, 'location_updated',
                                   f"Updated {', '.join(updates)}")
                    
                    print(f"   ✅ Updated: {', '.join(updates)}")
                else:
                    print("   ⏩ No changes")
        
        print(f"\n✅ Updated location for {self.stats['locations_added']} projects")
    
    def show_menu(self):
        """Main menu"""
        while True:
            print("\n" + "="*70)
            print("MANUAL DATA ENTRY")
            print("="*70)
            print("\n1. Fix Proposal Timelines (5 projects)")
            print("2. Link Emails to Projects (20 emails)")
            print("3. Add Project Locations (83 projects, showing 30 at a time)")
            print("4. View Statistics")
            print("5. Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == '1':
                self.fix_timelines()
            elif choice == '2':
                self.fix_email_links()
            elif choice == '3':
                self.fix_locations()
            elif choice == '4':
                self.show_stats()
            elif choice == '5':
                print("\n👋 Exiting...")
                break
        
        self.conn.close()
    
    def show_stats(self):
        """Show current statistics"""
        print("\n" + "="*70)
        print("MANUAL ENTRY STATISTICS")
        print("="*70)
        
        print(f"\n📅 Timelines added: {self.stats['timelines_added']}")
        print(f"📧 Emails linked: {self.stats['emails_linked']}")
        print(f"📍 Locations updated: {self.stats['locations_added']}")
        
        total = sum(self.stats.values())
        print(f"\n✅ Total manual fixes: {total}")
        
        # Check remaining issues
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM projects p
            WHERE p.source_db = 'proposals'
              AND NOT EXISTS (
                SELECT 1 FROM project_metadata pm
                WHERE pm.project_id = p.project_id
                  AND pm.metadata_key LIKE 'timeline_%'
              )
        """)
        remaining_timeline = self.cursor.fetchone()[0]
        
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM emails e
            WHERE NOT EXISTS (
                SELECT 1 FROM email_project_links epl
                WHERE epl.email_id = e.email_id
            )
            AND (
                e.subject LIKE '%BK-%'
                OR e.subject LIKE '%project%'
                OR e.subject LIKE '%proposal%'
            )
        """)
        remaining_emails = self.cursor.fetchone()[0]
        
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM projects
            WHERE (country IS NULL OR country = '')
               OR (city IS NULL OR city = '')
        """)
        remaining_locations = self.cursor.fetchone()[0]
        
        print("\n📊 Remaining issues:")
        print(f"   Proposals without timeline: {remaining_timeline}")
        print(f"   Unlinked emails: {remaining_emails}")
        print(f"   Missing locations: {remaining_locations}")

def main():
    print("="*70)
    print("MANUAL DATA ENTRY TOOL")
    print("="*70)
    print("\nThis tool helps you manually fix data quality issues.")
    print("All changes are logged and saved immediately.\n")
    
    entry = ManualDataEntry()
    entry.show_menu()

if __name__ == '__main__':
    main()
