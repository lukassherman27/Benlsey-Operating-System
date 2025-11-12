#!/usr/bin/env python3
"""
project_reports.py

Generates comprehensive project reports:
- Project status summary
- RFI report
- Action items / To-do list  
- Who are we waiting on
- Schedule overview

Updated: Oct 24, 2025 - Aligned with current database schema
"""

import sqlite3
from pathlib import Path
from datetime import datetime, date

class ProjectReports:
    def __init__(self):
        self.master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
    
    def project_status_report(self, project_code):
        """Complete status report for a project"""
        print("="*70)
        print(f"PROJECT STATUS REPORT: {project_code}")
        print("="*70)
        
        # Basic project info
        self.cursor.execute("""
            SELECT 
                p.project_title,
                p.status,
                p.country,
                p.total_fee_usd,
                p.contract_expiry_date,
                p.date_created,
                c.company_name
            FROM projects p
            LEFT JOIN clients c ON p.client_id = c.client_id
            WHERE p.project_code = ?
        """, (project_code,))
        
        result = self.cursor.fetchone()
        if not result:
            print(f"❌ Project {project_code} not found")
            return
        
        title, status, country, fee, expiry, date_created, client = result
        
        print(f"\n📊 PROJECT INFO")
        print(f"   Title: {title}")
        print(f"   Client: {client or 'Unknown'}")
        print(f"   Status: {status or 'Unknown'}")
        if country:
            print(f"   Country: {country}")
        if fee:
            print(f"   Total Fee: ${fee:,.0f}")
        if date_created:
            print(f"   Started: {date_created}")
        if expiry:
            print(f"   Contract Expiry: {expiry}")
        
        # Timeline/milestones
        self.cursor.execute("""
            SELECT milestone_name, actual_date, phase
            FROM project_milestones
            WHERE project_code = ?
            ORDER BY actual_date DESC
            LIMIT 5
        """, (project_code,))
        
        milestones = self.cursor.fetchall()
        if milestones:
            print(f"\n📅 TIMELINE")
            for name, date, phase in milestones:
                print(f"   {date}: {name}")
        
        # Current phase/status
        self.cursor.execute("""
            SELECT phase, status_date, current_activity, waiting_on
            FROM project_status_tracking
            WHERE project_code = ?
            ORDER BY status_date DESC
            LIMIT 1
        """, (project_code,))
        
        phase_result = self.cursor.fetchone()
        if phase_result:
            phase, phase_date, activity, waiting = phase_result
            print(f"\n📍 CURRENT PHASE")
            print(f"   Phase: {phase}")
            print(f"   Last Update: {phase_date}")
            if activity:
                print(f"   Activity: {activity}")
            if waiting:
                print(f"   ⚠️  Waiting on: {waiting}")
        
        # Email activity
        self.cursor.execute("""
            SELECT COUNT(*), MAX(e.date)
            FROM email_project_links epl
            JOIN emails e ON epl.email_id = e.email_id
            WHERE epl.project_code = ?
        """, (project_code,))
        
        email_count, last_email = self.cursor.fetchone()
        print(f"\n📧 EMAIL ACTIVITY")
        print(f"   Total emails: {email_count}")
        if last_email:
            print(f"   Last email: {last_email}")
        
        # Open RFIs
        self.cursor.execute("""
            SELECT COUNT(*),
                   SUM(CASE WHEN date_due < date('now') THEN 1 ELSE 0 END) as overdue
            FROM rfis
            WHERE project_code = ?
              AND status = 'open'
        """, (project_code,))
        
        rfi_count, overdue = self.cursor.fetchone()
        if rfi_count and rfi_count > 0:
            print(f"\n📋 OPEN RFIs: {rfi_count}")
            if overdue:
                print(f"   🔴 {overdue} OVERDUE")
        
        # Pending action items
        self.cursor.execute("""
            SELECT COUNT(*),
                   SUM(CASE WHEN due_date < date('now') THEN 1 ELSE 0 END) as overdue
            FROM action_items_tracking
            WHERE project_code = ?
              AND status = 'pending'
        """, (project_code,))
        
        action_count, action_overdue = self.cursor.fetchone()
        if action_count and action_count > 0:
            print(f"\n✅ PENDING ACTION ITEMS: {action_count}")
            if action_overdue:
                print(f"   🔴 {action_overdue} OVERDUE")
        
        # Key contacts
        self.cursor.execute("""
            SELECT e.sender_email, COUNT(*) as email_count
            FROM email_project_links epl
            JOIN emails e ON epl.email_id = e.email_id
            WHERE epl.project_code = ?
              AND e.sender_email NOT LIKE '%bensley%'
            GROUP BY e.sender_email
            ORDER BY email_count DESC
            LIMIT 5
        """, (project_code,))
        
        contacts = self.cursor.fetchall()
        if contacts:
            print(f"\n👥 KEY CONTACTS")
            for email, count in contacts:
                print(f"   {email:<45} {count} emails")
        
        print("\n" + "="*70)
    
    def rfi_report(self, status='open'):
        """Generate RFI report"""
        print("="*70)
        print(f"RFI REPORT - {status.upper()}")
        print("="*70)
        
        where_clause = ""
        if status != 'all':
            where_clause = f"AND r.status = '{status}'"
        
        self.cursor.execute(f"""
            SELECT 
                r.project_code,
                p.project_title,
                r.rfi_number,
                r.subject,
                r.date_sent,
                r.date_due,
                r.status,
                r.sender_email,
                CASE 
                    WHEN r.date_due < date('now') AND r.status = 'open' THEN '🔴 OVERDUE'
                    WHEN r.date_due <= date('now', '+3 days') AND r.status = 'open' THEN '🟡 DUE SOON'
                    WHEN r.status = 'open' THEN '🟢 Open'
                    ELSE '✅ ' || r.status
                END as urgency
            FROM rfis r
            LEFT JOIN projects p ON r.project_code = p.project_code
            WHERE 1=1 {where_clause}
            ORDER BY 
                CASE WHEN r.date_due < date('now') THEN 0 ELSE 1 END,
                r.date_due,
                r.project_code
        """)
        
        rfis = self.cursor.fetchall()
        
        if not rfis:
            print("\n✅ No RFIs found")
            return
        
        print(f"\nTotal RFIs: {len(rfis)}\n")
        
        current_project = None
        for code, title, num, subj, sent, due, stat, sender, urgency in rfis:
            if code != current_project:
                print(f"\n{code} - {(title or 'Unknown')[:50]}")
                print("-"*70)
                current_project = code
            
            due_str = due if due else 'No due date'
            print(f"  {urgency} RFI {num}: {(subj or 'No subject')[:40]}")
            print(f"      Due: {due_str} | From: {(sender or 'Unknown')[:35]}")
        
        print("\n" + "="*70)
    
    def action_items_report(self, assigned_to='Bill'):
        """My to-do list"""
        print("="*70)
        print(f"ACTION ITEMS FOR: {assigned_to}")
        print("="*70)
        
        self.cursor.execute("""
            SELECT 
                a.project_code,
                p.project_title,
                a.description,
                a.due_date,
                a.priority,
                a.assigned_by,
                CASE 
                    WHEN a.due_date < date('now') THEN '🔴 OVERDUE'
                    WHEN a.due_date <= date('now', '+3 days') THEN '🟡 URGENT'
                    WHEN a.due_date <= date('now', '+7 days') THEN '🟠 This Week'
                    ELSE '🟢 Upcoming'
                END as urgency
            FROM action_items_tracking a
            LEFT JOIN projects p ON a.project_code = p.project_code
            WHERE a.status = 'pending'
              AND (a.assigned_to = ? OR a.assigned_to IS NULL)
            ORDER BY 
                CASE WHEN a.due_date < date('now') THEN 0 ELSE 1 END,
                a.due_date,
                a.project_code
        """, (assigned_to,))
        
        actions = self.cursor.fetchall()
        
        if not actions:
            print("\n✅ No pending action items!")
            return
        
        print(f"\nTotal action items: {len(actions)}\n")
        
        for code, title, desc, due, priority, assigned_by, urgency in actions:
            due_str = due if due else 'No due date'
            print(f"{urgency} {code} - {(title or 'Unknown')[:35]}")
            print(f"   {desc[:60]}")
            print(f"   Due: {due_str} | From: {assigned_by or 'Unknown'}")
            print()
        
        print("="*70)
    
    def waiting_on_report(self):
        """Who are we waiting on?"""
        print("="*70)
        print("WAITING ON REPORT")
        print("="*70)
        
        # Open RFIs
        self.cursor.execute("""
            SELECT 
                r.project_code,
                p.project_title,
                r.rfi_number,
                r.subject,
                r.sender_email,
                r.date_sent,
                r.date_due,
                CASE 
                    WHEN r.date_due < date('now') THEN 'OVERDUE'
                    ELSE 'PENDING'
                END as status
            FROM rfis r
            LEFT JOIN projects p ON r.project_code = p.project_code
            WHERE r.status = 'open'
            ORDER BY r.date_due
        """)
        
        open_rfis = self.cursor.fetchall()
        
        if open_rfis:
            print(f"\n📋 OPEN RFIs ({len(open_rfis)}):")
            for code, title, num, subj, sender, sent, due, stat in open_rfis:
                status_icon = "🔴" if stat == "OVERDUE" else "⏳"
                print(f"\n{status_icon} {code} - RFI {num}")
                print(f"   {(subj or 'No subject')[:50]}")
                print(f"   Waiting on: {sender or 'Unknown'}")
                print(f"   Due: {due or 'No date'}")
        
        # Projects with "waiting_on" status
        self.cursor.execute("""
            SELECT 
                psh.project_code,
                p.project_title,
                psh.waiting_on,
                psh.waiting_on_email,
                psh.status_date
            FROM project_status_tracking psh
            LEFT JOIN projects p ON psh.project_code = p.project_code
            WHERE psh.waiting_on IS NOT NULL
              AND psh.status_date = (
                  SELECT MAX(status_date) 
                  FROM project_status_tracking 
                  WHERE project_code = psh.project_code
              )
            ORDER BY psh.status_date
        """)
        
        waiting = self.cursor.fetchall()
        
        if waiting:
            print(f"\n⏳ PROJECTS WITH PENDING ITEMS ({len(waiting)}):")
            for code, title, waiting_on, email, date in waiting:
                print(f"\n{code} - {(title or 'Unknown')[:45]}")
                print(f"   Waiting on: {waiting_on}")
                if email:
                    print(f"   Contact: {email}")
                print(f"   Since: {date}")
        
        if not open_rfis and not waiting:
            print("\n✅ Not waiting on anyone!")
        
        print("\n" + "="*70)
    
    def schedule_overview(self):
        """Overview of all project schedules"""
        print("="*70)
        print("SCHEDULE OVERVIEW")
        print("="*70)
        
        # Projects by phase
        self.cursor.execute("""
            SELECT 
                p.status,
                COUNT(*) as count
            FROM projects p
            WHERE p.status IS NOT NULL
            GROUP BY p.status
            ORDER BY count DESC
        """)
        
        statuses = self.cursor.fetchall()
        if statuses:
            print("\n📊 PROJECTS BY STATUS:")
            for status, count in statuses:
                print(f"   {status:<20} {count:>3}")
        
        # Recent milestones
        self.cursor.execute("""
            SELECT 
                m.project_code,
                p.project_title,
                m.milestone_name,
                m.actual_date,
                m.phase
            FROM project_milestones m
            LEFT JOIN projects p ON m.project_code = p.project_code
            WHERE m.actual_date >= date('now', '-30 days')
            ORDER BY m.actual_date DESC
            LIMIT 10
        """)
        
        milestones = self.cursor.fetchall()
        
        if milestones:
            print(f"\n📅 RECENT MILESTONES (Last 30 days):")
            for code, title, milestone, date, phase in milestones:
                print(f"\n{date} - {code}")
                print(f"   {milestone} ({phase})")
        
        print("\n" + "="*70)
    
    def interactive(self):
        """Interactive report menu"""
        while True:
            print("\n" + "="*70)
            print("PROJECT REPORTS MENU")
            print("="*70)
            print("\n1. Project Status Report (specific project)")
            print("2. RFI Report (all/open/overdue)")
            print("3. My Action Items")
            print("4. Who Are We Waiting On")
            print("5. Schedule Overview")
            print("6. Exit")
            
            choice = input("\nSelect report (1-6): ").strip()
            
            if choice == '1':
                code = input("Enter project code: ").strip()
                self.project_status_report(code)
            
            elif choice == '2':
                status = input("Status (all/open): ").strip().lower() or 'open'
                self.rfi_report(status)
            
            elif choice == '3':
                assigned = input("Assigned to (default: Bill): ").strip() or 'Bill'
                self.action_items_report(assigned)
            
            elif choice == '4':
                self.waiting_on_report()
            
            elif choice == '5':
                self.schedule_overview()
            
            elif choice == '6':
                print("👋 Goodbye!")
                break
            
            input("\nPress Enter to continue...")
        
        self.conn.close()

def main():
    reports = ProjectReports()
    reports.interactive()

if __name__ == '__main__':
    main()
