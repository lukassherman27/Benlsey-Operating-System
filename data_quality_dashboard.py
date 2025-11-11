#!/usr/bin/env python3
"""
data_quality_dashboard.py

Comprehensive data quality assessment:
- Missing critical data
- Low confidence entries
- Orphaned records
- Inconsistencies
- Actionable recommendations

Foundation for AI suggestion system.

Updated: Oct 24, 2025
"""

import sqlite3
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict

class DataQualityDashboard:
    def __init__(self):
        self.master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
        
        self.issues = {
            'critical': [],   # Must fix
            'high': [],       # Should fix soon
            'medium': [],     # Nice to have
            'low': []         # Optional improvements
        }
    
    def check_projects_missing_data(self):
        """Check for projects missing critical information"""
        
        # Missing timeline (proposals)
        self.cursor.execute("""
            SELECT 
                p.project_code,
                p.project_title,
                p.source_db
            FROM projects p
            WHERE p.source_db = 'proposals'
              AND NOT EXISTS (
                SELECT 1 FROM project_metadata pm
                WHERE pm.project_id = p.project_id
                  AND pm.metadata_key LIKE 'timeline_%'
              )
        """)
        
        missing_timeline = self.cursor.fetchall()
        if missing_timeline:
            self.issues['high'].append({
                'type': 'missing_timeline',
                'count': len(missing_timeline),
                'description': f"{len(missing_timeline)} proposals without timeline data",
                'projects': missing_timeline,
                'fix': 'Update Excel and re-import, or manually add timeline events'
            })
        
        # Missing location
        self.cursor.execute("""
            SELECT 
                p.project_code,
                p.project_title,
                p.country,
                p.city
            FROM projects p
            WHERE (p.country IS NULL OR p.country = '')
               OR (p.city IS NULL OR p.city = '')
        """)
        
        missing_location = self.cursor.fetchall()
        if missing_location:
            self.issues['medium'].append({
                'type': 'missing_location',
                'count': len(missing_location),
                'description': f"{len(missing_location)} projects missing location data",
                'projects': missing_location[:10],
                'fix': 'Extract from project title or email content'
            })
        
        # Missing client info
        self.cursor.execute("""
            SELECT 
                p.project_code,
                p.project_title,
                p.client_id
            FROM projects p
            WHERE p.client_id IS NULL
        """)
        
        missing_client = self.cursor.fetchall()
        if missing_client:
            self.issues['medium'].append({
                'type': 'missing_client',
                'count': len(missing_client),
                'description': f"{len(missing_client)} projects without client linkage",
                'projects': missing_client[:10],
                'fix': 'Match client names from project titles or emails'
            })
        
        # Missing fees (contracts only)
        self.cursor.execute("""
            SELECT 
                p.project_code,
                p.project_title,
                p.total_fee_usd
            FROM projects p
            WHERE p.source_db = 'contracts'
              AND (p.total_fee_usd IS NULL OR p.total_fee_usd = 0)
        """)
        
        missing_fee = self.cursor.fetchall()
        if missing_fee:
            self.issues['high'].append({
                'type': 'missing_fee',
                'count': len(missing_fee),
                'description': f"{len(missing_fee)} active projects without fee information",
                'projects': missing_fee,
                'fix': 'Extract from contracts database or emails'
            })
    
    def check_emails_not_linked(self):
        """Check for emails that should be linked to projects"""
        
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM emails e
            WHERE NOT EXISTS (
                SELECT 1 FROM email_project_links epl
                WHERE epl.email_id = e.email_id
            )
        """)
        
        unlinked_count = self.cursor.fetchone()[0]
        
        # Find emails with project codes in subject
        self.cursor.execute("""
            SELECT 
                e.email_id,
                e.date,
                e.subject,
                e.sender_email
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
            LIMIT 20
        """)
        
        linkable_emails = self.cursor.fetchall()
        
        if linkable_emails:
            self.issues['high'].append({
                'type': 'emails_not_linked',
                'count': len(linkable_emails),
                'total_unlinked': unlinked_count,
                'description': f"{len(linkable_emails)} emails mention projects but aren't linked",
                'emails': linkable_emails,
                'fix': 'Run enhanced email linking with pattern matching'
            })
    
    def check_orphaned_links(self):
        """Check for email links pointing to non-existent projects"""
        
        self.cursor.execute("""
            SELECT 
                epl.email_id,
                epl.project_code,
                e.subject
            FROM email_project_links epl
            LEFT JOIN projects p ON epl.project_code = p.project_code
            LEFT JOIN emails e ON epl.email_id = e.email_id
            WHERE p.project_id IS NULL
        """)
        
        orphaned = self.cursor.fetchall()
        
        if orphaned:
            self.issues['critical'].append({
                'type': 'orphaned_links',
                'count': len(orphaned),
                'description': f"{len(orphaned)} email links point to non-existent projects",
                'links': orphaned,
                'fix': 'Clean up broken links or create missing projects'
            })
    
    def check_rfis_missing_data(self):
        """Check RFIs for missing information"""
        
        # RFIs without due dates
        self.cursor.execute("""
            SELECT 
                r.rfi_id,
                r.project_code,
                r.subject,
                r.date_sent
            FROM rfis r
            WHERE r.date_due IS NULL
        """)
        
        no_due_date = self.cursor.fetchall()
        
        if no_due_date:
            self.issues['medium'].append({
                'type': 'rfis_no_due_date',
                'count': len(no_due_date),
                'description': f"{len(no_due_date)} RFIs without due dates",
                'rfis': no_due_date,
                'fix': 'Extract from email content or set default (7 days)'
            })
        
        # RFIs without responses beyond due date
        self.cursor.execute("""
            SELECT 
                r.rfi_id,
                r.project_code,
                r.subject,
                r.date_sent,
                r.date_due
            FROM rfis r
            WHERE r.date_responded IS NULL
              AND r.date_due < date('now')
              AND r.status = 'open'
        """)
        
        overdue = self.cursor.fetchall()
        
        if overdue:
            self.issues['critical'].append({
                'type': 'rfis_overdue',
                'count': len(overdue),
                'description': f"{len(overdue)} overdue RFIs without responses",
                'rfis': overdue,
                'fix': 'Search for response emails or mark as pending'
            })
    
    def check_data_inconsistencies(self):
        """Check for data inconsistencies"""
        
        # Fake dates (from sync issues)
        self.cursor.execute("""
            SELECT 
                p.project_code,
                p.project_title,
                p.date_created
            FROM projects p
            WHERE p.date_created >= '2025-10-22'
              AND p.source_db = 'proposals'
        """)
        
        fake_dates = self.cursor.fetchall()
        
        if fake_dates:
            self.issues['high'].append({
                'type': 'fake_dates',
                'count': len(fake_dates),
                'description': f"{len(fake_dates)} projects with auto-generated dates",
                'projects': fake_dates,
                'fix': 'Use first email date or Excel timeline data'
            })
        
        # Timeline events out of order
        self.cursor.execute("""
            SELECT 
                p.project_code,
                GROUP_CONCAT(pm.metadata_key || ':' || pm.metadata_value, '; ') as timeline
            FROM projects p
            JOIN project_metadata pm ON p.project_id = pm.project_id
            WHERE pm.metadata_key LIKE 'timeline_%'
            GROUP BY p.project_id
            HAVING COUNT(DISTINCT pm.metadata_key) >= 2
        """)
        
        timelines = self.cursor.fetchall()
        
        out_of_order = []
        for code, timeline_str in timelines:
            events = {}
            for event in timeline_str.split('; '):
                if ':' in event:
                    key, date = event.split(':', 1)
                    events[key.replace('timeline_', '')] = date
            
            # Check logical order
            if 'first_contact' in events and 'proposal_sent' in events:
                if events['first_contact'] > events['proposal_sent']:
                    out_of_order.append(code)
        
        if out_of_order:
            self.issues['medium'].append({
                'type': 'timeline_out_of_order',
                'count': len(out_of_order),
                'description': f"{len(out_of_order)} projects with illogical timeline order",
                'projects': out_of_order[:10],
                'fix': 'Review and correct timeline dates in Excel'
            })
    
    def check_low_confidence_data(self):
        """Check for data with low confidence scores"""
        
        # Low confidence email links
        self.cursor.execute("""
            SELECT 
                epl.project_code,
                COUNT(*) as count
            FROM email_project_links epl
            WHERE epl.confidence < 0.7
            GROUP BY epl.project_code
            ORDER BY count DESC
            LIMIT 10
        """)
        
        low_conf_links = self.cursor.fetchall()
        
        if low_conf_links:
            self.issues['medium'].append({
                'type': 'low_confidence_links',
                'count': sum(c[1] for c in low_conf_links),
                'description': f"Email links with confidence < 0.7",
                'projects': low_conf_links,
                'fix': 'Review and confirm or delete incorrect links'
            })
    
    def generate_report(self):
        """Run all checks and generate report"""
        print("="*70)
        print("DATA QUALITY DASHBOARD")
        print("="*70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        
        # Run all checks
        print("Running checks...")
        self.check_projects_missing_data()
        self.check_emails_not_linked()
        self.check_orphaned_links()
        self.check_rfis_missing_data()
        self.check_data_inconsistencies()
        self.check_low_confidence_data()
        
        # Calculate scores
        critical_count = len(self.issues['critical'])
        high_count = len(self.issues['high'])
        medium_count = len(self.issues['medium'])
        low_count = len(self.issues['low'])
        
        total_issues = critical_count + high_count + medium_count + low_count
        
        # Overall health score (0-100)
        score = 100
        score -= (critical_count * 20)  # -20 per critical
        score -= (high_count * 10)      # -10 per high
        score -= (medium_count * 5)     # -5 per medium
        score -= (low_count * 2)        # -2 per low
        score = max(0, score)
        
        # Display score
        print("\n" + "="*70)
        print(f"OVERALL DATA QUALITY SCORE: {score}/100")
        
        if score >= 90:
            print("🟢 EXCELLENT - System is in great shape!")
        elif score >= 75:
            print("🟡 GOOD - Minor improvements needed")
        elif score >= 50:
            print("🟠 FAIR - Several issues to address")
        else:
            print("🔴 NEEDS ATTENTION - Multiple critical issues")
        
        print("="*70)
        
        # Display issues by priority
        for priority in ['critical', 'high', 'medium', 'low']:
            issues = self.issues[priority]
            
            if not issues:
                continue
            
            icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}[priority]
            print(f"\n{icon} {priority.upper()} PRIORITY ({len(issues)} issues)")
            print("-"*70)
            
            for i, issue in enumerate(issues, 1):
                print(f"\n{i}. {issue['description']}")
                print(f"   Type: {issue['type']}")
                print(f"   Count: {issue['count']}")
                print(f"   Fix: {issue['fix']}")
                
                # Show sample data
                if 'projects' in issue and issue['projects']:
                    print(f"\n   Sample projects:")
                    for proj in issue['projects'][:3]:
                        code = proj[0] if len(proj) > 0 else 'Unknown'
                        title = proj[1] if len(proj) > 1 else 'Unknown'
                        print(f"      - {code}: {title[:50]}")
                
                if 'emails' in issue and issue['emails']:
                    print(f"\n   Sample emails:")
                    for email in issue['emails'][:3]:
                        subject = email[2] if len(email) > 2 else 'No subject'
                        print(f"      - {subject[:60]}")
                
                if 'rfis' in issue and issue['rfis']:
                    print(f"\n   Sample RFIs:")
                    for rfi in issue['rfis'][:3]:
                        code = rfi[1] if len(rfi) > 1 else 'Unknown'
                        subj = rfi[2] if len(rfi) > 2 else 'No subject'
                        print(f"      - {code}: {subj[:50]}")
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Total issues found: {total_issues}")
        print(f"  🔴 Critical: {critical_count}")
        print(f"  🟠 High: {high_count}")
        print(f"  🟡 Medium: {medium_count}")
        print(f"  🔵 Low: {low_count}")
        
        print("\n" + "="*70)
        print("NEXT STEPS")
        print("="*70)
        print("1. Fix critical issues first (data integrity)")
        print("2. Address high priority issues (missing key data)")
        print("3. Tackle medium priority issues (data enrichment)")
        print("4. Low priority issues can wait")
        print("\nOnce data quality score > 85, ready for AI integration!")
        print("="*70)
        
        return score
    
    def export_issues_for_ai(self, output_path):
        """Export issues in format for AI to review"""
        import json
        
        export_data = {
            'generated_at': datetime.now().isoformat(),
            'issues': self.issues,
            'ready_for_ai': len(self.issues['critical']) == 0
        }
        
        output_file = Path(output_path) / 'data_quality_issues.json'
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"\n✅ Issues exported to: {output_file}")
        print("   This file will be used by AI suggestion engine")

def main():
    dashboard = DataQualityDashboard()
    score = dashboard.generate_report()
    
    # Export for AI
    output_dir = Path.home() / "Desktop/BDS_SYSTEM/03_AI_QUEUE"
    output_dir.mkdir(exist_ok=True)
    dashboard.export_issues_for_ai(output_dir)
    
    dashboard.conn.close()

if __name__ == '__main__':
    main()
