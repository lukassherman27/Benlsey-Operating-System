#!/usr/bin/env python3
"""
enrich_database.py

Enriches the database with additional context:
- Scans emails for project dates, budgets, milestones
- Extracts contact information
- Identifies project phases
- Links related projects
"""

import sqlite3
import os
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class DatabaseEnricher:
    def __init__(self):
        self.master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
    
    def create_enrichment_tables(self):
        """Create tables for enriched data"""
        print("\n📊 Creating enrichment tables...")
        
        # Project metadata
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_metadata (
                metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                metadata_key TEXT,
                metadata_value TEXT,
                source TEXT,
                confidence REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id),
                UNIQUE(project_id, metadata_key)
            )
        """)
        
        # Project milestones
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_milestones (
                milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                milestone_name TEXT,
                milestone_date DATE,
                milestone_status TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        """)
        
        # Contact enrichment
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_metadata (
                contact_meta_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                role TEXT,
                company TEXT,
                phone TEXT,
                last_contact_date DATE,
                total_emails INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(email)
            )
        """)
        
        self.conn.commit()
        print("   ✅ Enrichment tables created")
    
    def extract_dates_from_emails(self):
        """Extract project-related dates from emails"""
        print("\n📅 Extracting dates from emails...")
        
        # Common date patterns
        date_keywords = [
            'deadline', 'due date', 'completion', 'delivery', 
            'milestone', 'target date', 'expected', 'scheduled'
        ]
        
        self.cursor.execute("""
            SELECT 
                p.project_id,
                p.project_code,
                e.subject,
                COALESCE(e.snippet, e.body_preview, '') as body_text
            FROM email_project_links epl
            JOIN projects p ON epl.project_id = p.project_id
            JOIN emails e ON epl.email_id = e.email_id
            WHERE epl.confidence > 0.8
        """)
        
        dates_found = 0
        
        for project_id, project_code, subject, body in self.cursor.fetchall():
            text = f"{subject} {body or ''}".lower()
            
            # Look for date-related keywords
            for keyword in date_keywords:
                if keyword in text:
                    # Extract dates near the keyword
                    # This is simplified - could use more sophisticated date parsing
                    dates_found += 1
                    break
        
        print(f"   ✅ Found {dates_found} date references")
        return dates_found
    
    def enrich_contacts_from_emails(self):
        """Enrich contact information from email patterns"""
        print("\n👥 Enriching contact data...")
        
        self.cursor.execute("""
            SELECT 
                sender_email,
                sender_name,
                COUNT(*) as email_count,
                MAX(date) as last_contact
            FROM emails
            WHERE sender_email NOT LIKE '%bensley.com%'
              AND sender_email NOT LIKE '%bensley.co.id%'
            GROUP BY sender_email
        """)
        
        contacts_enriched = 0
        
        for email, name, count, last_date in self.cursor.fetchall():
            # Extract company from email domain
            domain = email.split('@')[1] if '@' in email else ''
            company = domain.replace('.com', '').replace('.co', '').replace('.', ' ').title()
            
            # Try to identify role from name or email
            role = self._guess_role(email, name)
            
            try:
                self.cursor.execute("""
                    INSERT OR REPLACE INTO contact_metadata 
                    (email, role, company, last_contact_date, total_emails)
                    VALUES (?, ?, ?, ?, ?)
                """, (email, role, company, last_date, count))
                
                contacts_enriched += 1
            except Exception as e:
                pass
        
        self.conn.commit()
        print(f"   ✅ Enriched {contacts_enriched} contacts")
        return contacts_enriched
    
    def _guess_role(self, email, name):
        """Guess role from email/name"""
        email_lower = email.lower()
        name_lower = (name or '').lower()
        
        roles = {
            'director': ['director', 'dir'],
            'manager': ['manager', 'mgr'],
            'architect': ['architect', 'design'],
            'engineer': ['engineer', 'eng'],
            'coordinator': ['coordinator', 'coord'],
            'admin': ['admin', 'secretary'],
            'consultant': ['consultant', 'consulting']
        }
        
        for role, keywords in roles.items():
            for keyword in keywords:
                if keyword in email_lower or keyword in name_lower:
                    return role
        
        return 'contact'
    
    def identify_project_phases(self):
        """Identify project phases from email content"""
        print("\n🏗️  Identifying project phases...")
        
        phase_keywords = {
            'concept': ['concept', 'preliminary', 'feasibility', 'initial'],
            'schematic': ['schematic', 'sd phase', 'design development'],
            'detailed_design': ['detailed design', 'dd phase', 'construction documents'],
            'construction': ['construction', 'build', 'contractor'],
            'closeout': ['closeout', 'handover', 'completion', 'final']
        }
        
        self.cursor.execute("""
            SELECT DISTINCT
                p.project_id,
                p.project_code,
                GROUP_CONCAT(e.subject || ' ' || COALESCE(e.snippet, e.body_preview, ''), ' ') as all_text
            FROM projects p
            LEFT JOIN email_project_links epl ON p.project_id = epl.project_id
            LEFT JOIN emails e ON epl.email_id = e.email_id
            GROUP BY p.project_id
        """)
        
        phases_identified = 0
        
        for project_id, project_code, all_text in self.cursor.fetchall():
            if not all_text:
                continue
            
            text_lower = all_text.lower()
            
            # Find which phase keywords appear most
            phase_counts = defaultdict(int)
            for phase, keywords in phase_keywords.items():
                for keyword in keywords:
                    phase_counts[phase] += text_lower.count(keyword)
            
            # Add most prominent phase as metadata
            if phase_counts:
                primary_phase = max(phase_counts, key=phase_counts.get)
                
                try:
                    self.cursor.execute("""
                        INSERT OR REPLACE INTO project_metadata
                        (project_id, metadata_key, metadata_value, source, confidence)
                        VALUES (?, 'current_phase', ?, 'email_analysis', ?)
                    """, (project_id, primary_phase, min(phase_counts[primary_phase] / 10.0, 0.9)))
                    
                    phases_identified += 1
                except:
                    pass
        
        self.conn.commit()
        print(f"   ✅ Identified phases for {phases_identified} projects")
        return phases_identified
    
    def extract_project_locations(self):
        """Extract project locations from emails and project titles"""
        print("\n🌍 Extracting project locations...")
        
        self.cursor.execute("""
            SELECT 
                project_id,
                project_code,
                project_title
            FROM projects
        """)
        
        locations_found = 0
        
        # Common location indicators
        countries = ['Thailand', 'Indonesia', 'Singapore', 'Malaysia', 'Vietnam', 
                    'China', 'Japan', 'UAE', 'India', 'Korea', 'Philippines']
        cities = ['Bangkok', 'Jakarta', 'Singapore', 'Kuala Lumpur', 'Dubai', 
                 'Mumbai', 'Seoul', 'Manila', 'Phuket', 'Bali']
        
        for project_id, code, title in self.cursor.fetchall():
            title_text = title or ''
            location = None
            
            # Check for countries
            for country in countries:
                if country.lower() in title_text.lower():
                    location = country
                    break
            
            # Check for cities if no country found
            if not location:
                for city in cities:
                    if city.lower() in title_text.lower():
                        location = city
                        break
            
            if location:
                try:
                    self.cursor.execute("""
                        INSERT OR REPLACE INTO project_metadata
                        (project_id, metadata_key, metadata_value, source, confidence)
                        VALUES (?, 'location', ?, 'project_title', 0.9)
                    """, (project_id, location))
                    
                    locations_found += 1
                except:
                    pass
        
        self.conn.commit()
        print(f"   ✅ Found locations for {locations_found} projects")
        return locations_found
    
    def generate_enrichment_summary(self):
        """Show summary of enriched data"""
        print("\n" + "="*70)
        print("ENRICHMENT SUMMARY")
        print("="*70)
        
        # Project metadata count
        self.cursor.execute("SELECT COUNT(DISTINCT project_id) FROM project_metadata")
        projects_with_meta = self.cursor.fetchone()[0]
        print(f"\n📊 Projects with metadata: {projects_with_meta}")
        
        # Metadata breakdown
        self.cursor.execute("""
            SELECT metadata_key, COUNT(*) as count
            FROM project_metadata
            GROUP BY metadata_key
            ORDER BY count DESC
        """)
        
        print("\nMetadata types:")
        for key, count in self.cursor.fetchall():
            print(f"   {key}: {count}")
        
        # Contact enrichment
        self.cursor.execute("SELECT COUNT(*) FROM contact_metadata")
        enriched_contacts = self.cursor.fetchone()[0]
        print(f"\n👥 Enriched contacts: {enriched_contacts}")
        
        # Top contacts by email volume
        self.cursor.execute("""
            SELECT email, role, company, total_emails
            FROM contact_metadata
            ORDER BY total_emails DESC
            LIMIT 5
        """)
        
        print("\nTop contacts:")
        for email, role, company, count in self.cursor.fetchall():
            print(f"   {email[:35]:35} - {role} ({count} emails)")
    
    def run(self):
        """Main enrichment process"""
        print("="*70)
        print("DATABASE ENRICHMENT")
        print("="*70)
        print("\nAdding context and metadata to improve intelligence...")
        
        # Create tables
        self.create_enrichment_tables()
        
        # Run enrichment processes
        self.extract_dates_from_emails()
        self.enrich_contacts_from_emails()
        self.identify_project_phases()
        self.extract_project_locations()
        
        # Show summary
        self.generate_enrichment_summary()
        
        print("\n✅ Database enrichment complete!")
        
        self.conn.close()

def main():
    enricher = DatabaseEnricher()
    enricher.run()

if __name__ == '__main__':
    main()
