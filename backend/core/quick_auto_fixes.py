#!/usr/bin/env python3
"""
quick_auto_fixes.py

Safe automated fixes for obvious data quality issues:
1. Extract locations from project titles
2. Link emails with project codes in subject
3. Fix fake dates using email timestamps
4. Set RFI default due dates

All changes are logged and reversible.
Only fixes HIGH CONFIDENCE issues.

Updated: Oct 24, 2025
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime, timedelta

class AutoFixer:
    def __init__(self):
        self.master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
        
        self.stats = {
            'locations_added': 0,
            'emails_linked': 0,
            'dates_fixed': 0,
            'rfis_updated': 0
        }
        
        # Known countries/cities for extraction
        self.countries = [
            'India', 'China', 'Vietnam', 'Thailand', 'Indonesia', 'Malaysia',
            'Singapore', 'Philippines', 'Cambodia', 'Laos', 'Myanmar', 'Maldives',
            'UAE', 'United Arab Emirates', 'Nepal', 'Sri Lanka', 'Bhutan',
            'Kenya', 'Nigeria', 'Egypt', 'Morocco', 'South Africa',
            'USA', 'United States', 'Mexico', 'Brazil', 'Argentina',
            'UK', 'United Kingdom', 'France', 'Italy', 'Spain', 'Greece',
            'Australia', 'New Zealand', 'Japan', 'Korea', 'Israel'
        ]
        
        self.cities = [
            'Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata',
            'Beijing', 'Shanghai', 'Hong Kong', 'Hanoi', 'Ho Chi Minh',
            'Bangkok', 'Phuket', 'Chiang Mai', 'Bali', 'Jakarta',
            'Singapore', 'Kuala Lumpur', 'Manila', 'Dubai', 'Abu Dhabi',
            'Kathmandu', 'Colombo', 'Nairobi', 'Lagos', 'Cairo',
            'New York', 'Los Angeles', 'London', 'Paris', 'Rome',
            'Sydney', 'Melbourne', 'Tokyo', 'Seoul', 'Tel Aviv'
        ]
    
    def log_change(self, table, record_id, field, old_value, new_value, confidence, reason):
        """Log all changes for audit trail"""
        self.cursor.execute("""
            INSERT INTO data_quality_tracking
            (data_table, record_id, issue_type, description, suggested_fix, 
             suggested_value, ai_confidence, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'fixed')
        """, (table, record_id, 'auto_fix', 
              f"Changed {field} from '{old_value}' to '{new_value}'",
              reason, new_value, confidence))
    
    def extract_location_from_title(self, title):
        """Extract country and city from project title"""
        if not title:
            return None, None
        
        country = None
        city = None
        
        # Check for country
        for c in self.countries:
            if c in title:
                country = c
                break
        
        # Check for city
        for ct in self.cities:
            if ct in title:
                city = ct
                break
        
        return country, city
    
    def fix_locations(self):
        """Extract and add missing locations from titles"""
        print("="*70)
        print("FIX 1: EXTRACTING LOCATIONS FROM TITLES")
        print("="*70)
        
        self.cursor.execute("""
            SELECT 
                project_id,
                project_code,
                project_title,
                country,
                city
            FROM projects
            WHERE (country IS NULL OR country = '')
               OR (city IS NULL OR city = '')
        """)
        
        projects = self.cursor.fetchall()
        print(f"\nFound {len(projects)} projects with missing location data")
        
        for project_id, code, title, current_country, current_city in projects:
            country, city = self.extract_location_from_title(title)
            
            changes = []
            
            # Update country if missing and found
            if (not current_country or current_country == '') and country:
                self.cursor.execute("""
                    UPDATE projects SET country = ? WHERE project_id = ?
                """, (country, project_id))
                
                self.log_change('projects', project_id, 'country', 
                               current_country, country, 0.9, 
                               f"Extracted from title: '{title}'")
                
                changes.append(f"country: {country}")
                self.stats['locations_added'] += 1
            
            # Update city if missing and found
            if (not current_city or current_city == '') and city:
                self.cursor.execute("""
                    UPDATE projects SET city = ? WHERE project_id = ?
                """, (city, project_id))
                
                self.log_change('projects', project_id, 'city',
                               current_city, city, 0.85,
                               f"Extracted from title: '{title}'")
                
                changes.append(f"city: {city}")
                self.stats['locations_added'] += 1
            
            if changes:
                print(f"   ✅ {code}: Added {', '.join(changes)}")
        
        self.conn.commit()
        print(f"\n✅ Added location data to {self.stats['locations_added']} fields")
    
    def link_emails_with_project_codes(self):
        """Link emails that have project codes in subject"""
        print("\n" + "="*70)
        print("FIX 2: LINKING EMAILS WITH PROJECT CODES")
        print("="*70)
        
        # Find unlinked emails with BK- in subject
        self.cursor.execute("""
            SELECT 
                e.email_id,
                e.subject,
                e.date
            FROM emails e
            WHERE NOT EXISTS (
                SELECT 1 FROM email_project_links epl
                WHERE epl.email_id = e.email_id
            )
            AND e.subject LIKE '%BK-%'
        """)
        
        unlinked = self.cursor.fetchall()
        print(f"\nFound {len(unlinked)} unlinked emails with project codes")
        
        # Get all valid project codes
        self.cursor.execute("SELECT project_id, project_code FROM projects")
        valid_codes = {code: pid for pid, code in self.cursor.fetchall()}
        
        for email_id, subject, date in unlinked:
            # Extract potential project codes
            matches = re.findall(r'\d{2}\s*BK-\d{3}', subject, re.IGNORECASE)
            
            for match in matches:
                # Normalize code format
                normalized = re.sub(r'\s+', ' ', match).upper()
                
                if normalized in valid_codes:
                    project_id = valid_codes[normalized]
                    
                    # Link it
                    self.cursor.execute("""
                        INSERT OR IGNORE INTO email_project_links
                        (email_id, project_id, project_code, confidence, link_method, evidence)
                        VALUES (?, ?, ?, 0.95, 'auto_code_match', ?)
                    """, (email_id, project_id, normalized, 
                          f"Code found in subject: {subject[:50]}"))
                    
                    if self.cursor.rowcount > 0:
                        self.stats['emails_linked'] += 1
                        print(f"   ✅ Linked email to {normalized}: {subject[:60]}")
                    
                    break  # Only link to first match
        
        self.conn.commit()
        print(f"\n✅ Linked {self.stats['emails_linked']} emails to projects")
    
    def fix_fake_dates(self):
        """Fix auto-generated dates using email timestamps"""
        print("\n" + "="*70)
        print("FIX 3: FIXING AUTO-GENERATED DATES")
        print("="*70)
        
        # Find projects with fake dates
        self.cursor.execute("""
            SELECT 
                p.project_id,
                p.project_code,
                p.project_title,
                p.date_created
            FROM projects p
            WHERE p.date_created >= '2025-10-22'
              AND p.source_db = 'proposals'
        """)
        
        fake_dates = self.cursor.fetchall()
        print(f"\nFound {len(fake_dates)} projects with auto-generated dates")
        
        for project_id, code, title, fake_date in fake_dates:
            # Try to find first email for this project
            self.cursor.execute("""
                SELECT MIN(e.date)
                FROM email_project_links epl
                JOIN emails e ON epl.email_id = e.email_id
                WHERE epl.project_code = ?
            """, (code,))
            
            result = self.cursor.fetchone()
            first_email_date = result[0] if result else None
            
            if first_email_date:
                # Use email date
                self.cursor.execute("""
                    UPDATE projects 
                    SET date_created = ?
                    WHERE project_id = ?
                """, (first_email_date, project_id))
                
                self.log_change('projects', project_id, 'date_created',
                               fake_date, first_email_date, 0.8,
                               'Used first email date')
                
                self.stats['dates_fixed'] += 1
                print(f"   ✅ {code}: {fake_date} → {first_email_date[:10]}")
            else:
                # Try timeline data
                self.cursor.execute("""
                    SELECT MIN(metadata_value)
                    FROM project_metadata
                    WHERE project_id = ?
                      AND metadata_key LIKE 'timeline_%'
                """, (project_id,))
                
                result = self.cursor.fetchone()
                timeline_date = result[0] if result else None
                
                if timeline_date:
                    self.cursor.execute("""
                        UPDATE projects 
                        SET date_created = ?
                        WHERE project_id = ?
                    """, (timeline_date, project_id))
                    
                    self.log_change('projects', project_id, 'date_created',
                                   fake_date, timeline_date, 0.9,
                                   'Used timeline first_contact date')
                    
                    self.stats['dates_fixed'] += 1
                    print(f"   ✅ {code}: {fake_date} → {timeline_date}")
        
        self.conn.commit()
        print(f"\n✅ Fixed {self.stats['dates_fixed']} fake dates")
    
    def fix_rfi_due_dates(self):
        """Set default due dates for RFIs (7 days from received)"""
        print("\n" + "="*70)
        print("FIX 4: SETTING RFI DUE DATES")
        print("="*70)
        
        self.cursor.execute("""
            SELECT 
                rfi_id,
                project_code,
                subject,
                date_sent
            FROM rfis
            WHERE date_due IS NULL
        """)
        
        rfis = self.cursor.fetchall()
        print(f"\nFound {len(rfis)} RFIs without due dates")
        
        for rfi_id, code, subject, sent_date in rfis:
            # Calculate due date: 7 days from received
            sent = datetime.strptime(sent_date, '%Y-%m-%d %H:%M:%S')
            due = sent + timedelta(days=7)
            due_str = due.strftime('%Y-%m-%d')
            
            self.cursor.execute("""
                UPDATE rfis 
                SET date_due = ?
                WHERE rfi_id = ?
            """, (due_str, rfi_id))
            
            self.log_change('rfis', rfi_id, 'date_due',
                           None, due_str, 0.7,
                           'Default 7 days from received')
            
            self.stats['rfis_updated'] += 1
            print(f"   ✅ {code}: Set due date to {due_str}")
        
        self.conn.commit()
        print(f"\n✅ Set due dates for {self.stats['rfis_updated']} RFIs")
    
    def generate_summary(self):
        """Show summary of all fixes"""
        print("\n" + "="*70)
        print("AUTO-FIX SUMMARY")
        print("="*70)
        
        print(f"\n📍 Locations added: {self.stats['locations_added']}")
        print(f"📧 Emails linked: {self.stats['emails_linked']}")
        print(f"📅 Dates fixed: {self.stats['dates_fixed']}")
        print(f"📋 RFIs updated: {self.stats['rfis_updated']}")
        
        total = sum(self.stats.values())
        print(f"\n✅ Total fixes applied: {total}")
        
        # Check new quality score
        print("\n" + "="*70)
        print("CHECKING NEW QUALITY SCORE...")
        print("="*70)
        
        # Quick quality check
        issues = 0
        
        # Missing timeline
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
        missing_timeline = self.cursor.fetchone()[0]
        issues += missing_timeline * 10
        
        # Missing location
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM projects
            WHERE (country IS NULL OR country = '')
        """)
        missing_location = self.cursor.fetchone()[0]
        issues += missing_location * 5
        
        # Fake dates
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM projects
            WHERE date_created >= '2025-10-22'
              AND source_db = 'proposals'
        """)
        fake_dates = self.cursor.fetchone()[0]
        issues += fake_dates * 10
        
        # Unlinked emails with codes
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM emails e
            WHERE NOT EXISTS (
                SELECT 1 FROM email_project_links epl
                WHERE epl.email_id = e.email_id
            )
            AND e.subject LIKE '%BK-%'
        """)
        unlinked = self.cursor.fetchone()[0]
        issues += unlinked * 10
        
        estimated_score = max(0, 100 - issues)
        
        print(f"\n📊 Estimated new score: ~{estimated_score}/100")
        
        if estimated_score >= 75:
            print("🟢 GOOD - Ready for AI integration!")
        elif estimated_score >= 60:
            print("🟡 FAIR - A few more fixes needed")
        else:
            print("🟠 More work needed - run data_quality_dashboard.py")
        
        print("\n" + "="*70)
        print("NEXT STEPS")
        print("="*70)
        print("1. Run: python3 data_quality_dashboard.py")
        print("2. Review changes in data_quality_tracking table")
        print("3. If score > 70, ready for AI integration!")
        print("="*70)
    
    def run(self):
        """Execute all auto-fixes"""
        print("Starting safe auto-fixes...")
        print("All changes are logged and reversible\n")
        
        self.fix_locations()
        self.link_emails_with_project_codes()
        self.fix_fake_dates()
        self.fix_rfi_due_dates()
        self.generate_summary()
        
        self.conn.close()

def main():
    fixer = AutoFixer()
    fixer.run()

if __name__ == '__main__':
    main()
