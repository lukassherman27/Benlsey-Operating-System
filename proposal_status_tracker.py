#!/usr/bin/env python3
"""
proposal_status_tracker.py

Tracks proposal pipeline status and alerts:
- Current status of each proposal
- Days in current status
- Alerts for stuck/overdue proposals
- Monthly/quarterly analytics
- Action required list

Updated: Oct 24, 2025
"""

import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import defaultdict

class ProposalTracker:
    def __init__(self):
        self.master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
        
        # Status order/progression
        self.status_order = {
            'first_contact': 1,
            'drafting': 2,
            'proposal_sent': 3,
            'on_hold': 4,
            'contract_signed': 5,
            'lost': 6
        }
        
        # Alert thresholds (days)
        self.thresholds = {
            'drafting': 7,        # Alert if drafting >7 days
            'proposal_sent': 14,  # Alert if sent but no response >14 days
            'on_hold': 30,        # Alert if on hold >30 days
        }
    
    def get_proposal_current_status(self):
        """Get current status for all proposals"""
        self.cursor.execute("""
            SELECT 
                p.project_code,
                p.project_title,
                p.date_created as first_contact_date,
                pm.metadata_key,
                pm.metadata_value as event_date
            FROM projects p
            LEFT JOIN project_metadata pm ON p.project_id = pm.project_id
            WHERE p.source_db = 'proposals'
              AND (pm.metadata_key LIKE 'timeline_%' OR pm.metadata_key IS NULL)
            ORDER BY p.project_code, pm.metadata_value DESC
        """)
        
        rows = self.cursor.fetchall()
        
        # Group by project and find latest status
        proposals = {}
        for code, title, first_contact, key, event_date in rows:
            if code not in proposals:
                proposals[code] = {
                    'project_code': code,
                    'project_title': title,
                    'first_contact': first_contact,
                    'events': []
                }
            
            if key:
                status = key.replace('timeline_', '')
                proposals[code]['events'].append({
                    'status': status,
                    'date': event_date
                })
        
        # Calculate current status for each
        result = []
        for code, data in proposals.items():
            if not data['events']:
                current_status = 'first_contact'
                status_date = data['first_contact']
            else:
                # Get most recent event
                latest = max(data['events'], key=lambda x: x['date'])
                current_status = latest['status']
                status_date = latest['date']
            
            # Calculate days in status
            if status_date:
                status_date_obj = datetime.strptime(status_date, '%Y-%m-%d').date()
                days_in_status = (date.today() - status_date_obj).days
            else:
                days_in_status = 0
            
            result.append({
                'project_code': code,
                'project_title': data['project_title'],
                'current_status': current_status,
                'status_date': status_date,
                'days_in_status': days_in_status,
                'all_events': data['events']
            })
        
        return result
    
    def generate_alerts(self, proposals):
        """Generate alerts for stuck/overdue proposals"""
        alerts = {
            'urgent': [],    # Red - needs immediate action
            'warning': [],   # Yellow - approaching threshold
            'info': []       # Blue - FYI
        }
        
        for prop in proposals:
            status = prop['current_status']
            days = prop['days_in_status']
            code = prop['project_code']
            title = prop['project_title']
            
            # Check thresholds
            if status == 'drafting' and days > self.thresholds['drafting']:
                alerts['urgent'].append({
                    'project_code': code,
                    'title': title,
                    'message': f"Drafting for {days} days (threshold: {self.thresholds['drafting']})",
                    'status': status,
                    'days': days
                })
            
            elif status == 'proposal_sent' and days > self.thresholds['proposal_sent']:
                alerts['warning'].append({
                    'project_code': code,
                    'title': title,
                    'message': f"Proposal sent {days} days ago, no response",
                    'status': status,
                    'days': days
                })
            
            elif status == 'on_hold' and days > self.thresholds['on_hold']:
                alerts['info'].append({
                    'project_code': code,
                    'title': title,
                    'message': f"On hold for {days} days",
                    'status': status,
                    'days': days
                })
            
            elif status == 'drafting' and days >= self.thresholds['drafting'] - 2:
                # Approaching threshold
                alerts['warning'].append({
                    'project_code': code,
                    'title': title,
                    'message': f"Drafting for {days} days (approaching threshold)",
                    'status': status,
                    'days': days
                })
        
        return alerts
    
    def show_status_dashboard(self):
        """Show comprehensive status dashboard"""
        print("="*70)
        print("PROPOSAL STATUS DASHBOARD")
        print("="*70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        
        proposals = self.get_proposal_current_status()
        
        # Group by status
        by_status = defaultdict(list)
        for prop in proposals:
            by_status[prop['current_status']].append(prop)
        
        # Show summary
        print("📊 SUMMARY BY STATUS:")
        for status in ['first_contact', 'drafting', 'proposal_sent', 'on_hold', 'contract_signed', 'lost']:
            count = len(by_status.get(status, []))
            if count > 0:
                status_display = status.replace('_', ' ').title()
                print(f"   {status_display:<20} {count:>3} proposals")
        
        print(f"\n   {'TOTAL':<20} {len(proposals):>3} proposals")
        
        # Generate and show alerts
        alerts = self.generate_alerts(proposals)
        
        if alerts['urgent']:
            print(f"\n🔴 URGENT ALERTS ({len(alerts['urgent'])}):")
            for alert in sorted(alerts['urgent'], key=lambda x: x['days'], reverse=True):
                print(f"   {alert['project_code']}: {alert['message']}")
                print(f"      {alert['title'][:60]}")
        
        if alerts['warning']:
            print(f"\n🟡 WARNINGS ({len(alerts['warning'])}):")
            for alert in sorted(alerts['warning'], key=lambda x: x['days'], reverse=True)[:5]:
                print(f"   {alert['project_code']}: {alert['message']}")
        
        if alerts['info']:
            print(f"\n🔵 INFO ({len(alerts['info'])} on hold >30 days)")
        
        print("\n" + "="*70)
    
    def show_active_proposals(self):
        """Show proposals that need action"""
        print("="*70)
        print("ACTIVE PROPOSALS - ACTION REQUIRED")
        print("="*70)
        
        proposals = self.get_proposal_current_status()
        
        # Filter for active statuses
        active = [p for p in proposals if p['current_status'] in ['drafting', 'proposal_sent']]
        
        if not active:
            print("\n✅ No active proposals requiring action!")
            return
        
        print(f"\nTotal: {len(active)} proposals\n")
        
        # Sort by days in status (longest first)
        active.sort(key=lambda x: x['days_in_status'], reverse=True)
        
        for prop in active:
            status_display = prop['current_status'].replace('_', ' ').title()
            days = prop['days_in_status']
            
            # Color code by urgency
            if prop['current_status'] == 'drafting' and days > 7:
                icon = "🔴"
            elif prop['current_status'] == 'proposal_sent' and days > 14:
                icon = "🟡"
            elif days > 5:
                icon = "🟠"
            else:
                icon = "🟢"
            
            print(f"{icon} {prop['project_code']} - {status_display} ({days} days)")
            print(f"   {prop['project_title'][:60]}")
            if prop['status_date']:
                print(f"   Since: {prop['status_date']}")
            print()
        
        print("="*70)
    
    def show_monthly_analytics(self):
        """Show monthly/quarterly analytics"""
        print("="*70)
        print("PROPOSAL ANALYTICS")
        print("="*70)
        
        proposals = self.get_proposal_current_status()
        
        # This month stats
        today = date.today()
        month_start = date(today.year, today.month, 1)
        
        this_month_events = []
        for prop in proposals:
            for event in prop['all_events']:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                if event_date >= month_start:
                    this_month_events.append({
                        'project': prop['project_code'],
                        'status': event['status'],
                        'date': event['date']
                    })
        
        print(f"\n📅 THIS MONTH ({month_start.strftime('%B %Y')}):")
        
        # Count by status
        month_by_status = defaultdict(int)
        for event in this_month_events:
            month_by_status[event['status']] += 1
        
        if not this_month_events:
            print(f"   ⚠️  No activity this month")
        else:
            if month_by_status.get('first_contact'):
                print(f"   New contacts: {month_by_status['first_contact']}")
            if month_by_status.get('drafting'):
                print(f"   Drafting started: {month_by_status['drafting']}")
            if month_by_status.get('proposal_sent'):
                print(f"   Proposals sent: {month_by_status['proposal_sent']}")
            if month_by_status.get('contract_signed'):
                print(f"   Contracts signed: {month_by_status['contract_signed']} 🎉")
            if month_by_status.get('lost'):
                print(f"   Lost: {month_by_status['lost']}")
        
        # Find last activity date
        all_dates = []
        for prop in proposals:
            for event in prop['all_events']:
                all_dates.append(datetime.strptime(event['date'], '%Y-%m-%d').date())
        
        if all_dates:
            last_activity = max(all_dates)
            days_since = (today - last_activity).days
            print(f"\n📊 LAST ACTIVITY:")
            print(f"   Date: {last_activity.strftime('%B %d, %Y')}")
            print(f"   Days ago: {days_since}")
            if days_since > 30:
                print(f"   ⚠️  Excel may need updating!")
        
        # Calculate ALL-TIME conversion rate
        total_proposals = len([p for p in proposals if any(e['status'] == 'proposal_sent' for e in p['all_events'])])
        won = len([p for p in proposals if any(e['status'] == 'contract_signed' for e in p['all_events'])])
        
        if total_proposals > 0:
            conversion_rate = (won / total_proposals) * 100
            print(f"\n📈 ALL-TIME STATS:")
            print(f"   Total proposals sent: {total_proposals}")
            print(f"   Won: {won}")
            print(f"   Conversion rate: {conversion_rate:.1f}%")
        
        # Average time to send proposal (all time)
        draft_to_sent_times = []
        for prop in proposals:
            drafting_date = None
            sent_date = None
            
            for event in prop['all_events']:
                if event['status'] == 'drafting' and not drafting_date:
                    drafting_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                if event['status'] == 'proposal_sent' and not sent_date:
                    sent_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
            
            if drafting_date and sent_date and sent_date > drafting_date:
                days = (sent_date - drafting_date).days
                draft_to_sent_times.append(days)
        
        if draft_to_sent_times:
            avg_time = sum(draft_to_sent_times) / len(draft_to_sent_times)
            print(f"\n⏱️  AVG TIME TO SEND (ALL-TIME):")
            print(f"   Average: {avg_time:.1f} days")
            print(f"   Fastest: {min(draft_to_sent_times)} days")
            print(f"   Slowest: {max(draft_to_sent_times)} days")
        
        print("\n" + "="*70)
    
    def show_detailed_status(self, project_code):
        """Show detailed status for a specific proposal"""
        proposals = self.get_proposal_current_status()
        prop = next((p for p in proposals if p['project_code'] == project_code), None)
        
        if not prop:
            print(f"❌ Proposal {project_code} not found")
            return
        
        print("="*70)
        print(f"PROPOSAL STATUS: {project_code}")
        print("="*70)
        
        print(f"\n📋 {prop['project_title']}")
        print(f"\n🎯 Current Status: {prop['current_status'].replace('_', ' ').title()}")
        print(f"   Days in status: {prop['days_in_status']}")
        
        if prop['all_events']:
            print(f"\n📅 Timeline:")
            for event in sorted(prop['all_events'], key=lambda x: x['date']):
                status_display = event['status'].replace('_', ' ').title()
                print(f"   {event['date']}: {status_display}")
        
        print("\n" + "="*70)
    
    def interactive(self):
        """Interactive menu"""
        while True:
            print("\n" + "="*70)
            print("PROPOSAL STATUS TRACKER")
            print("="*70)
            print("\n1. Status Dashboard")
            print("2. Active Proposals (Action Required)")
            print("3. Monthly Analytics")
            print("4. Detailed Status (specific proposal)")
            print("5. Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == '1':
                self.show_status_dashboard()
            elif choice == '2':
                self.show_active_proposals()
            elif choice == '3':
                self.show_monthly_analytics()
            elif choice == '4':
                code = input("Enter project code: ").strip()
                self.show_detailed_status(code)
            elif choice == '5':
                print("👋 Goodbye!")
                break
            
            if choice in ['1', '2', '3', '4']:
                input("\nPress Enter to continue...")
        
        self.conn.close()

def main():
    tracker = ProposalTracker()
    tracker.interactive()

if __name__ == '__main__':
    main()