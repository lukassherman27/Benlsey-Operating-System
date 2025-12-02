#!/usr/bin/env python3
"""
Proposal Follow-Up Tracker

Automatically identifies proposals that need follow-up based on:
- Days since last contact
- Status (active proposals only)
- Next action date

Generates daily/weekly follow-up reminders for Lukas.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def get_proposals_needing_followup(db_path, days_threshold=14):
    """
    Get all proposals that need follow-up.

    Args:
        days_threshold: Number of days after which follow-up is needed (default: 14)

    Returns:
        List of proposals needing attention
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get proposals needing follow-up
    cursor.execute("""
        SELECT
            p.project_code,
            p.project_name,
            p.client_company,
            p.contact_email,
            p.status,
            p.last_contact_date,
            p.days_since_contact,
            p.next_action,
            p.next_action_date,
            p.project_value,
            p.win_probability,
            p.health_score,
            p.internal_notes,
            COUNT(e.email_id) as email_count
        FROM proposals p
        LEFT JOIN email_proposal_links epl ON p.proposal_id = epl.proposal_id
        LEFT JOIN emails e ON epl.email_id = e.email_id
        WHERE p.status IN ('proposal', 'negotiating', 'pending')
        AND (
            p.days_since_contact IS NULL
            OR p.days_since_contact >= ?
            OR (p.next_action_date IS NOT NULL AND date(p.next_action_date) <= date('now'))
        )
        GROUP BY p.project_code
        ORDER BY
            CASE WHEN p.next_action_date IS NOT NULL AND date(p.next_action_date) <= date('now') THEN 0 ELSE 1 END,
            p.days_since_contact DESC NULLS LAST
    """, (days_threshold,))

    proposals = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return proposals

def categorize_urgency(days_since_contact, next_action_date):
    """Categorize follow-up urgency"""
    today = datetime.now().date()

    # Check if next action date has passed
    if next_action_date:
        try:
            action_date = datetime.fromisoformat(next_action_date).date()
            if action_date <= today:
                return "OVERDUE ACTION"
        except:
            pass

    if days_since_contact is None:
        return "NO CONTACT RECORDED"
    elif days_since_contact >= 90:
        return "CRITICAL (90+ days)"
    elif days_since_contact >= 60:
        return "URGENT (60-89 days)"
    elif days_since_contact >= 30:
        return "HIGH (30-59 days)"
    elif days_since_contact >= 14:
        return "MEDIUM (14-29 days)"
    else:
        return "LOW (<14 days)"

def generate_follow_up_report(proposals):
    """Generate a formatted follow-up report"""

    print("=" * 100)
    print("📋 PROPOSAL FOLLOW-UP REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 100)
    print()

    if not proposals:
        print("✅ All proposals have been followed up recently!")
        return

    # Group by urgency
    by_urgency = {}
    for proposal in proposals:
        urgency = categorize_urgency(proposal['days_since_contact'], proposal['next_action_date'])
        if urgency not in by_urgency:
            by_urgency[urgency] = []
        by_urgency[urgency].append(proposal)

    # Define urgency order
    urgency_order = [
        "OVERDUE ACTION",
        "NO CONTACT RECORDED",
        "CRITICAL (90+ days)",
        "URGENT (60-89 days)",
        "HIGH (30-59 days)",
        "MEDIUM (14-29 days)",
        "LOW (<14 days)"
    ]

    for urgency in urgency_order:
        if urgency not in by_urgency:
            continue

        proposals_in_category = by_urgency[urgency]
        print(f"\n🚨 {urgency}: {len(proposals_in_category)} proposals")
        print("-" * 100)

        for p in proposals_in_category:
            print(f"\n📌 {p['project_code']}: {p['project_name']}")
            print(f"   Client: {p['client_company']}")
            if p['contact_email']:
                print(f"   Contact: {p['contact_email']}")
            if p['project_value']:
                print(f"   Value: ${p['project_value']:,.0f}")
            if p['days_since_contact']:
                print(f"   Last Contact: {p['days_since_contact']} days ago")
            else:
                print(f"   Last Contact: Never recorded")
            if p['next_action']:
                print(f"   Next Action: {p['next_action']}")
            if p['next_action_date']:
                print(f"   Action Date: {p['next_action_date']}")
            if p['email_count'] > 0:
                print(f"   📧 {p['email_count']} emails linked")

            # Suggested follow-up
            if p['days_since_contact'] and p['days_since_contact'] >= 90:
                print(f"   💡 SUGGESTED ACTION: Call client ASAP to check status")
            elif p['days_since_contact'] and p['days_since_contact'] >= 30:
                print(f"   💡 SUGGESTED ACTION: Send friendly follow-up email")
            elif p['next_action_date']:
                print(f"   💡 SUGGESTED ACTION: Complete scheduled action: {p['next_action']}")

    print("\n" + "=" * 100)
    print(f"📊 SUMMARY: {len(proposals)} proposals need follow-up")

    # Calculate potential value at risk
    total_value = sum(p['project_value'] for p in proposals if p['project_value'])
    print(f"💰 Total Value at Risk: ${total_value:,.0f}")
    print("=" * 100)

def main():
    db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

    # Get proposals needing follow-up (14+ days)
    proposals = get_proposals_needing_followup(db_path, days_threshold=14)

    # Generate report
    generate_follow_up_report(proposals)

    print("\n💡 TIP: Run this script daily or integrate into your morning routine!")
    print("   Command: python3 proposal_follow_up_tracker.py")

if __name__ == '__main__':
    main()
