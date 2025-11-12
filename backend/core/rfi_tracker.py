#!/usr/bin/env python3
"""
rfi_tracker.py

Comprehensive RFI tracking system:
- Extracts RFIs with due dates
- Matches responses from sent emails
- Calculates response times
- Shows overdue/due soon alerts
- Analytics dashboard

Updated: Oct 24, 2025
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import defaultdict

class RFITracker:
    def __init__(self):
        self.master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
    
    def extract_due_date_from_content(self, subject, snippet):
        """Try to extract due date from email content"""
        text = f"{subject} {snippet or ''}"
        
        # Common date patterns
        patterns = [
            r'due[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'respond by[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'deadline[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'due date[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed = self.parse_date_string(date_str)
                if parsed:
                    return parsed
        
        # Default: 7 days from received
        return None
    
    def parse_date_string(self, date_str):
        """Parse various date formats"""
        formats = [
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%m/%d/%y',
            '%d %B %Y',
            '%d %b %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        return None
    
    def find_response_email(self, rfi_email_id, rfi_subject, rfi_date, project_code):
        """Find if we responded to this RFI"""
        
        # Clean RFI number from subject
        rfi_number = None
        rfi_patterns = [
            r'RFI[\s-]?([\w-]+)',
            r'(DAE-RFI-CIR-\d+)',
            r'(NRC-INF-[\w-]+)',
        ]
        
        for pattern in rfi_patterns:
            match = re.search(pattern, rfi_subject, re.IGNORECASE)
            if match:
                rfi_number = match.group(1)
                break
        
        if not rfi_number:
            return None
        
        # Look for responses
        self.cursor.execute("""
            SELECT 
                e.email_id,
                e.date,
                e.subject
            FROM emails e
            LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
            WHERE (
                -- Same project
                epl.project_code = ?
                OR
                -- Contains RFI number
                e.subject LIKE ?
                OR
                -- Reply to thread (has Re: and similar subject)
                (e.subject LIKE 'Re:%' AND e.subject LIKE ?)
            )
            AND e.sender_email = 'bsherman@bensley.com'
            AND e.date > ?
            ORDER BY e.date
            LIMIT 1
        """, (project_code, f'%{rfi_number}%', f'%{rfi_subject[:30]}%', rfi_date))
        
        result = self.cursor.fetchone()
        
        if result:
            response_id, response_date, response_subject = result
            return {
                'email_id': response_id,
                'date': response_date,
                'subject': response_subject
            }
        
        return None
    
    def update_rfi_with_response(self, rfi_id, response_info):
        """Update RFI with response information"""
        if not response_info:
            return
        
        self.cursor.execute("""
            UPDATE rfis
            SET date_responded = ?,
                response_email_id = ?,
                status = 'responded'
            WHERE rfi_id = ?
        """, (response_info['date'], response_info['email_id'], rfi_id))
    
    def reprocess_rfis(self):
        """Reprocess all RFIs to extract due dates and match responses"""
        print("="*70)
        print("REPROCESSING RFIs")
        print("="*70)
        
        # Get all RFIs
        self.cursor.execute("""
            SELECT 
                r.rfi_id,
                r.project_code,
                r.subject,
                r.date_sent,
                r.date_due,
                r.extracted_from_email_id,
                e.snippet
            FROM rfis r
            LEFT JOIN emails e ON r.extracted_from_email_id = e.email_id
        """)
        
        rfis = self.cursor.fetchall()
        print(f"\nProcessing {len(rfis)} RFIs...")
        
        updated = 0
        responses_found = 0
        
        for rfi_id, project_code, subject, date_sent, date_due, email_id, snippet in rfis:
            changes = False
            
            # Extract due date if missing
            if not date_due:
                due = self.extract_due_date_from_content(subject, snippet)
                if not due:
                    # Default: 7 days from received
                    sent_date = datetime.strptime(date_sent, '%Y-%m-%d %H:%M:%S').date()
                    due = sent_date + timedelta(days=7)
                
                self.cursor.execute("""
                    UPDATE rfis SET date_due = ? WHERE rfi_id = ?
                """, (due.strftime('%Y-%m-%d'), rfi_id))
                changes = True
            
            # Find response
            response = self.find_response_email(email_id, subject, date_sent, project_code)
            if response:
                self.update_rfi_with_response(rfi_id, response)
                responses_found += 1
                changes = True
            
            if changes:
                updated += 1
        
        self.conn.commit()
        
        print(f"\n✅ Updated: {updated} RFIs")
        print(f"✅ Responses found: {responses_found}")
        print("\n" + "="*70)
    
    def show_rfi_dashboard(self):
        """Show comprehensive RFI dashboard"""
        print("="*70)
        print("RFI STATUS DASHBOARD")
        print("="*70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        
        # Get all RFIs with project info
        self.cursor.execute("""
            SELECT 
                r.rfi_id,
                r.project_code,
                p.project_title,
                r.rfi_number,
                r.subject,
                r.date_sent,
                r.date_due,
                r.date_responded,
                r.status,
                r.sender_email
            FROM rfis r
            LEFT JOIN projects p ON r.project_code = p.project_code
            ORDER BY r.project_code, r.date_sent DESC
        """)
        
        rfis = self.cursor.fetchall()
        
        if not rfis:
            print("✅ No RFIs found!")
            return
        
        # Group by project
        by_project = defaultdict(list)
        for rfi in rfis:
            project_code = rfi[1]
            by_project[project_code].append(rfi)
        
        # Stats
        total = len(rfis)
        overdue = 0
        due_soon = 0
        responded = 0
        total_response_days = []
        
        today = date.today()
        
        for project_code, project_rfis in by_project.items():
            project_title = project_rfis[0][2] or "Unknown"
            
            print(f"\n{project_code} - {project_title[:50]} ({len(project_rfis)} RFIs)")
            print("─"*70)
            
            # Categorize
            overdue_rfis = []
            due_soon_rfis = []
            open_rfis = []
            closed_rfis = []
            
            for rfi_data in project_rfis:
                (rfi_id, _, _, rfi_num, subj, sent, due, responded_date, 
                 status, sender) = rfi_data
                
                sent_date = datetime.strptime(sent, '%Y-%m-%d %H:%M:%S').date()
                due_date = datetime.strptime(due, '%Y-%m-%d').date() if due else None
                
                days_since = (today - sent_date).days
                
                rfi_info = {
                    'number': rfi_num or 'Unknown',
                    'subject': subj,
                    'sent_date': sent_date,
                    'due_date': due_date,
                    'responded_date': responded_date,
                    'days_since': days_since,
                    'sender': sender
                }
                
                if responded_date:
                    resp_date = datetime.strptime(responded_date, '%Y-%m-%d').date()
                    response_time = (resp_date - sent_date).days
                    total_response_days.append(response_time)
                    rfi_info['response_time'] = response_time
                    closed_rfis.append(rfi_info)
                    responded += 1
                elif due_date:
                    days_until_due = (due_date - today).days
                    rfi_info['days_until_due'] = days_until_due
                    
                    if days_until_due < 0:
                        overdue_rfis.append(rfi_info)
                        overdue += 1
                    elif days_until_due <= 3:
                        due_soon_rfis.append(rfi_info)
                        due_soon += 1
                    else:
                        open_rfis.append(rfi_info)
                else:
                    open_rfis.append(rfi_info)
            
            # Display by category
            if overdue_rfis:
                print(f"\n🔴 OVERDUE ({len(overdue_rfis)}):")
                for rfi in overdue_rfis:
                    print(f"   {rfi['number']}: {rfi['subject'][:50]}")
                    print(f"      Received: {rfi['sent_date']} ({rfi['days_since']} days ago)")
                    print(f"      Due: {rfi['due_date']} (OVERDUE BY {abs(rfi['days_until_due'])} DAYS)")
                    print(f"      Status: ❌ NO RESPONSE SENT")
                    print()
            
            if due_soon_rfis:
                print(f"\n🟡 DUE SOON ({len(due_soon_rfis)}):")
                for rfi in due_soon_rfis:
                    print(f"   {rfi['number']}: {rfi['subject'][:50]}")
                    print(f"      Received: {rfi['sent_date']} ({rfi['days_since']} days ago)")
                    print(f"      Due: {rfi['due_date']} (in {rfi['days_until_due']} days)")
                    print(f"      Status: ❌ NO RESPONSE SENT")
                    print()
            
            if open_rfis:
                print(f"\n🟢 OPEN ({len(open_rfis)}):")
                for rfi in open_rfis:
                    print(f"   {rfi['number']}: {rfi['subject'][:50]}")
                    print(f"      Received: {rfi['sent_date']} ({rfi['days_since']} days ago)")
                    if rfi.get('due_date'):
                        print(f"      Due: {rfi['due_date']} (in {rfi['days_until_due']} days)")
                    else:
                        print(f"      Due: Not set")
                    print(f"      Status: ❌ NO RESPONSE SENT")
                    print()
            
            if closed_rfis:
                print(f"\n✅ RESPONDED ({len(closed_rfis)}):")
                for rfi in closed_rfis:
                    print(f"   {rfi['number']}: {rfi['subject'][:50]}")
                    print(f"      Responded: {rfi['responded_date']} ({rfi['response_time']} days)")
                    print()
        
        # Analytics
        print("\n" + "="*70)
        print("ANALYTICS")
        print("="*70)
        print(f"\nTotal RFIs: {total}")
        print(f"Overdue: {overdue} 🔴")
        print(f"Due within 3 days: {due_soon} 🟡")
        print(f"Responded: {responded} ✅")
        print(f"Response rate: {(responded/total*100):.1f}%")
        
        if total_response_days:
            avg_response = sum(total_response_days) / len(total_response_days)
            print(f"\nAvg response time: {avg_response:.1f} days")
            print(f"Fastest response: {min(total_response_days)} days")
            print(f"Slowest response: {max(total_response_days)} days")
        
        print("\n" + "="*70)
    
    def show_project_rfis(self, project_code):
        """Show all RFIs for a specific project"""
        print("="*70)
        print(f"RFIs FOR PROJECT: {project_code}")
        print("="*70)
        
        self.cursor.execute("""
            SELECT 
                p.project_title,
                COUNT(r.rfi_id) as total_rfis,
                SUM(CASE WHEN r.status = 'open' THEN 1 ELSE 0 END) as open_count,
                SUM(CASE WHEN r.date_responded IS NOT NULL THEN 1 ELSE 0 END) as responded_count
            FROM projects p
            LEFT JOIN rfis r ON p.project_code = r.project_code
            WHERE p.project_code = ?
            GROUP BY p.project_id
        """, (project_code,))
        
        result = self.cursor.fetchone()
        
        if not result or result[1] == 0:
            print(f"\n❌ No RFIs found for {project_code}")
            return
        
        title, total, open_count, responded = result
        
        print(f"\n📋 {title}")
        print(f"\nTotal RFIs: {total}")
        print(f"Open: {open_count}")
        print(f"Responded: {responded}")
        
        # List all RFIs
        self.cursor.execute("""
            SELECT 
                r.rfi_number,
                r.subject,
                r.date_sent,
                r.date_due,
                r.date_responded,
                r.status
            FROM rfis r
            WHERE r.project_code = ?
            ORDER BY r.date_sent DESC
        """, (project_code,))
        
        rfis = self.cursor.fetchall()
        
        print(f"\n📄 RFI LIST:")
        for num, subj, sent, due, responded, status in rfis:
            print(f"\n   {num or 'N/A'}: {subj[:60]}")
            print(f"      Sent: {sent}")
            if due:
                print(f"      Due: {due}")
            if responded:
                print(f"      Responded: {responded} ✅")
            else:
                print(f"      Status: ⏳ Awaiting response")
        
        print("\n" + "="*70)
    
    def interactive(self):
        """Interactive menu"""
        while True:
            print("\n" + "="*70)
            print("RFI TRACKER")
            print("="*70)
            print("\n1. RFI Dashboard (all projects)")
            print("2. Project RFIs (specific project)")
            print("3. Reprocess RFIs (extract due dates & match responses)")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == '1':
                self.show_rfi_dashboard()
            elif choice == '2':
                code = input("Enter project code: ").strip()
                self.show_project_rfis(code)
            elif choice == '3':
                self.reprocess_rfis()
            elif choice == '4':
                print("👋 Goodbye!")
                break
            
            if choice in ['1', '2', '3']:
                input("\nPress Enter to continue...")
        
        self.conn.close()

def main():
    tracker = RFITracker()
    tracker.interactive()

if __name__ == '__main__':
    main()
