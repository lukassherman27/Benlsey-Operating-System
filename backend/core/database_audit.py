#!/usr/bin/env python3
"""
database_audit.py

Complete audit of bensley_master.db:
- What data exists
- What's missing/incomplete
- What files need to be added
- Foundation gaps
- Recommendations

Updated: Oct 24, 2025
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class DatabaseAuditor:
    def __init__(self):
        self.master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
        
        self.system_dir = Path.home() / "Desktop/BDS_SYSTEM"
    
    def print_header(self, text):
        print("\n" + "="*70)
        print(text)
        print("="*70)
    
    def print_section(self, text):
        print("\n" + "-"*70)
        print(text)
        print("-"*70)
    
    def get_table_info(self):
        """Show all tables and their row counts"""
        self.print_header("DATABASE STRUCTURE")
        
        # Get all tables
        self.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        
        tables = [row[0] for row in self.cursor.fetchall()]
        
        print(f"\nTotal tables: {len(tables)}\n")
        
        table_stats = {}
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            table_stats[table] = count
            
            # Get columns
            self.cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in self.cursor.fetchall()]
            
            print(f"📊 {table}")
            print(f"   Rows: {count:,}")
            print(f"   Columns: {len(columns)}")
            if count == 0:
                print(f"   ⚠️  EMPTY TABLE")
            print()
        
        return table_stats
    
    def audit_projects(self):
        """Audit projects data"""
        self.print_header("PROJECTS AUDIT")
        
        # Total projects
        self.cursor.execute("SELECT COUNT(*) FROM projects")
        total = self.cursor.fetchone()[0]
        print(f"\n📋 Total projects: {total}")
        
        # By source
        self.cursor.execute("""
            SELECT source_db, COUNT(*) 
            FROM projects 
            GROUP BY source_db
        """)
        print("\nBy source:")
        for source, count in self.cursor.fetchall():
            print(f"   {source}: {count}")
        
        # Data completeness
        self.print_section("DATA COMPLETENESS")
        
        checks = [
            ("Has project code", "project_code IS NOT NULL"),
            ("Has title", "project_title IS NOT NULL AND project_title != ''"),
            ("Has country", "country IS NOT NULL AND country != ''"),
            ("Has city", "city IS NOT NULL AND city != ''"),
            ("Has client", "client_id IS NOT NULL"),
            ("Has date", "date_created IS NOT NULL"),
            ("Real date (not fake)", "date_created < '2025-10-22'"),
            ("Has fee info", "total_fee_usd IS NOT NULL AND total_fee_usd > 0"),
        ]
        
        for check_name, condition in checks:
            self.cursor.execute(f"""
                SELECT COUNT(*) FROM projects WHERE {condition}
            """)
            count = self.cursor.fetchone()[0]
            pct = (count / total * 100) if total > 0 else 0
            
            icon = "✅" if pct >= 75 else "🟡" if pct >= 50 else "🔴"
            print(f"{icon} {check_name}: {count}/{total} ({pct:.0f}%)")
        
        # Sample projects
        self.print_section("SAMPLE PROJECTS")
        
        self.cursor.execute("""
            SELECT 
                project_code,
                project_title,
                country,
                city,
                source_db,
                date_created
            FROM projects
            ORDER BY date_created DESC
            LIMIT 5
        """)
        
        print("\nMost recent projects:")
        for code, title, country, city, source, date in self.cursor.fetchall():
            print(f"\n   {code} - {title[:50]}")
            print(f"   Location: {city or '?'}, {country or '?'}")
            print(f"   Source: {source} | Date: {date}")
    
    def audit_emails(self):
        """Audit emails data"""
        self.print_header("EMAILS AUDIT")
        
        # Total emails
        self.cursor.execute("SELECT COUNT(*) FROM emails")
        total = self.cursor.fetchone()[0]
        print(f"\n📧 Total emails: {total:,}")
        
        # Date range
        self.cursor.execute("""
            SELECT MIN(date), MAX(date) 
            FROM emails
        """)
        min_date, max_date = self.cursor.fetchone()
        print(f"Date range: {min_date[:10]} to {max_date[:10]}")
        
        # By sender
        self.cursor.execute("""
            SELECT sender_email, COUNT(*) as count
            FROM emails
            GROUP BY sender_email
            ORDER BY count DESC
            LIMIT 10
        """)
        
        print("\nTop 10 senders:")
        for sender, count in self.cursor.fetchall():
            print(f"   {sender}: {count:,} emails")
        
        # Linked vs unlinked
        self.cursor.execute("""
            SELECT 
                COUNT(DISTINCT e.email_id) as linked
            FROM emails e
            JOIN email_project_links epl ON e.email_id = epl.email_id
        """)
        linked = self.cursor.fetchone()[0]
        unlinked = total - linked
        link_rate = (linked / total * 100) if total > 0 else 0
        
        print(f"\n📎 Email linking:")
        print(f"   Linked: {linked:,} ({link_rate:.1f}%)")
        print(f"   Unlinked: {unlinked:,}")
        
        icon = "✅" if link_rate >= 50 else "🟡" if link_rate >= 20 else "🔴"
        print(f"   {icon} Link rate: {link_rate:.1f}%")
        
        # Emails with attachments
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM emails 
            WHERE has_attachments = 1
        """)
        with_attachments = self.cursor.fetchone()[0]
        print(f"\n📎 Emails with attachments: {with_attachments:,}")
        
        # Missing email accounts
        self.print_section("EMAIL ACCOUNTS")
        
        self.cursor.execute("""
            SELECT DISTINCT sender_email
            FROM emails
            WHERE sender_email LIKE '%bensley.com'
        """)
        
        bensley_senders = [row[0] for row in self.cursor.fetchall()]
        print(f"\nBensley team emails found: {len(bensley_senders)}")
        for email in bensley_senders:
            print(f"   {email}")
        
        print("\n⚠️  Missing email accounts to import:")
        print("   • bill@bensley.com (dad's account)")
        print("   • Other team members?")
    
    def audit_timeline_data(self):
        """Audit timeline/metadata"""
        self.print_header("TIMELINE & METADATA AUDIT")
        
        # Projects with timeline
        self.cursor.execute("""
            SELECT COUNT(DISTINCT project_id)
            FROM project_metadata
            WHERE metadata_key LIKE 'timeline_%'
        """)
        with_timeline = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM projects WHERE source_db = 'proposals'")
        total_proposals = self.cursor.fetchone()[0]
        
        print(f"\n📅 Timeline data:")
        print(f"   Proposals: {total_proposals}")
        print(f"   With timeline: {with_timeline}")
        print(f"   Missing timeline: {total_proposals - with_timeline}")
        
        # Timeline events breakdown
        self.cursor.execute("""
            SELECT metadata_key, COUNT(*) as count
            FROM project_metadata
            WHERE metadata_key LIKE 'timeline_%'
            GROUP BY metadata_key
            ORDER BY count DESC
        """)
        
        print("\nTimeline events:")
        for key, count in self.cursor.fetchall():
            event = key.replace('timeline_', '')
            print(f"   {event}: {count} projects")
    
    def audit_rfis(self):
        """Audit RFI data"""
        self.print_header("RFI AUDIT")
        
        self.cursor.execute("SELECT COUNT(*) FROM rfis")
        total = self.cursor.fetchone()[0]
        
        if total == 0:
            print("\n⚠️  NO RFIs IN DATABASE")
            print("   Need to import RFI data from emails")
            return
        
        print(f"\n📋 Total RFIs: {total}")
        
        # RFI status
        self.cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM rfis
            GROUP BY status
        """)
        
        print("\nBy status:")
        for status, count in self.cursor.fetchall():
            print(f"   {status}: {count}")
    
    def audit_files(self):
        """Check what files exist in the system"""
        self.print_header("FILES & DIRECTORIES AUDIT")
        
        # Check main directories
        dirs_to_check = [
            ("Databases", "01_DATABASES"),
            ("Scripts", "02_SCRIPTS"),
            ("AI Queue", "03_AI_QUEUE"),
            ("Documents", "04_DOCUMENTS"),
            ("Reports", "05_REPORTS"),
        ]
        
        print("\nDirectory structure:")
        for name, path in dirs_to_check:
            full_path = self.system_dir / path
            if full_path.exists():
                # Count files
                files = list(full_path.rglob('*'))
                file_count = len([f for f in files if f.is_file()])
                print(f"   ✅ {name} ({path}): {file_count} files")
            else:
                print(f"   ❌ {name} ({path}): MISSING")
        
        # Check key files
        self.print_section("KEY FILES")
        
        key_files = [
            ("Master database", "01_DATABASES/bensley_master.db"),
            ("Proposals database", "01_DATABASES/proposals.db"),
            ("Contracts database", "01_DATABASES/contracts.db"),
            ("Invoices database", "01_DATABASES/invoices.db"),
            ("Excel proposals", "Proposals_overview_.xlsx"),
        ]
        
        print("\nKey files status:")
        for name, path in key_files:
            full_path = self.system_dir / path
            if full_path.exists():
                size = full_path.stat().st_size
                size_mb = size / (1024 * 1024)
                print(f"   ✅ {name}: {size_mb:.1f} MB")
            else:
                print(f"   ❌ {name}: MISSING")
    
    def check_missing_data(self):
        """Identify what data is missing"""
        self.print_header("MISSING DATA SUMMARY")
        
        checks = [
            ("Email accounts", "Need dad's emails (~5000)", "HIGH"),
            ("Proposal PDFs", "Need to scan for proposals", "MEDIUM"),
            ("Contract PDFs", "Need to scan for contracts", "MEDIUM"),
            ("RFI emails", "More RFIs to extract", "MEDIUM"),
            ("Timeline data", "5 proposals missing", "HIGH"),
            ("Location data", "83 projects incomplete", "MEDIUM"),
            ("Client linkage", "109 projects unlinked", "MEDIUM"),
            ("Team member data", "No team table yet", "LOW"),
        ]
        
        print("\nData gaps by priority:\n")
        
        for priority in ["HIGH", "MEDIUM", "LOW"]:
            items = [c for c in checks if c[2] == priority]
            if items:
                icon = "🔴" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "🔵"
                print(f"{icon} {priority} PRIORITY:")
                for name, desc, _ in items:
                    print(f"   • {name}: {desc}")
                print()
    
    def generate_recommendations(self):
        """Generate actionable recommendations"""
        self.print_header("RECOMMENDATIONS")
        
        print("\n🎯 IMMEDIATE ACTIONS (This Weekend):")
        print("   1. Import dad's emails (~5000 emails)")
        print("   2. Update Proposals_overview_.xlsx (add 5 missing)")
        print("   3. Manual data entry (timelines, locations)")
        print("   4. Run auto-fixes again after imports")
        print("   → Target: 75/100 data quality score")
        
        print("\n📅 NEXT WEEK:")
        print("   1. Set up AI suggestion engine")
        print("   2. Create document scanner for PDFs")
        print("   3. Extract more RFIs from emails")
        print("   4. Build team members table")
        print("   → Target: 85/100 data quality score")
        
        print("\n📁 FILES TO ADD:")
        print("   • Proposal PDFs → scan into database")
        print("   • Contract PDFs → extract terms, dates")
        print("   • RFI documents → link to projects")
        print("   • Meeting notes → extract action items")
        
        print("\n🔧 SCRIPTS TO RUN:")
        print("   • email_importer.py --account dad")
        print("   • excel_importer.py (after updating)")
        print("   • manual_data_entry.py")
        print("   • quick_auto_fixes.py (after imports)")
        print("   • data_quality_dashboard.py (check score)")
    
    def run_full_audit(self):
        """Run complete audit"""
        print("="*70)
        print("BENSLEY DESIGN STUDIOS - DATABASE AUDIT")
        print("="*70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Database: {self.master_db}")
        
        self.get_table_info()
        self.audit_projects()
        self.audit_emails()
        self.audit_timeline_data()
        self.audit_rfis()
        self.audit_files()
        self.check_missing_data()
        self.generate_recommendations()
        
        print("\n" + "="*70)
        print("AUDIT COMPLETE")
        print("="*70)
        
        self.conn.close()

def main():
    auditor = DatabaseAuditor()
    auditor.run_full_audit()

if __name__ == '__main__':
    main()