#!/usr/bin/env python3
"""
Follow-up Email Drafter

Identifies proposals needing follow-up and generates draft emails.
Drafts are stored in ai_suggestions for human review and approval.

Usage:
    python scripts/core/followup_email_drafter.py
    python scripts/core/followup_email_drafter.py --days 21
    python scripts/core/followup_email_drafter.py --project-code "25 BK-079"
    python scripts/core/followup_email_drafter.py --dry-run
"""

import sqlite3
import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = os.getenv('DATABASE_PATH', str(PROJECT_ROOT / 'database' / 'bensley_master.db'))


def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_proposals_needing_followup(conn, days_threshold: int = 14,
                                    project_code: str = None) -> List[Dict]:
    """
    Find proposals where:
    - Ball is in their court
    - More than N days since last contact
    - Status is active (not lost, declined, etc.)
    """
    cursor = conn.cursor()

    if project_code:
        cursor.execute("""
            SELECT p.proposal_id, p.project_code, p.project_name,
                   p.status, p.ball_in_court, p.days_since_contact,
                   p.last_contact_date, p.contact_email, p.contact_person,
                   p.client_company, p.next_action, p.waiting_for
            FROM proposals p
            WHERE p.project_code = ?
        """, (project_code,))
    else:
        cursor.execute("""
            SELECT p.proposal_id, p.project_code, p.project_name,
                   p.status, p.ball_in_court, p.days_since_contact,
                   p.last_contact_date, p.contact_email, p.contact_person,
                   p.client_company, p.next_action, p.waiting_for
            FROM proposals p
            WHERE p.status NOT IN ('Lost', 'Declined', 'Contract Signed', 'Dormant', 'On Hold')
            AND p.days_since_contact > ?
            AND p.ball_in_court = 'them'
            AND p.contact_email IS NOT NULL
            AND p.contact_email != ''
            ORDER BY p.days_since_contact DESC
        """, (days_threshold,))

    return [dict(row) for row in cursor.fetchall()]


def get_last_email_context(conn, project_code: str) -> Optional[Dict]:
    """Get the most recent email for context"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.subject, e.sender_email, substr(e.body_full, 1, 500) as body_preview,
               e.date, e.email_direction
        FROM emails e
        JOIN email_proposal_links epl ON e.email_id = epl.email_id
        JOIN proposals p ON epl.proposal_id = p.proposal_id
        WHERE p.project_code = ?
        ORDER BY e.date DESC
        LIMIT 1
    """, (project_code,))
    row = cursor.fetchone()
    return dict(row) if row else None


def generate_followup_draft(proposal: Dict, last_email: Optional[Dict]) -> Dict:
    """
    Generate a follow-up email draft based on proposal context.

    Returns draft with subject, body, and reasoning.
    """
    contact_name = proposal.get('contact_person', '').split()[0] if proposal.get('contact_person') else ''
    project_name = proposal.get('project_name', 'your project')
    status = proposal.get('status', 'First Contact')
    days = proposal.get('days_since_contact', 0)
    waiting_for = proposal.get('waiting_for', '')

    # Determine tone and approach based on days passed
    if days <= 14:
        urgency = "gentle"
        opener = "Hope this finds you well!"
    elif days <= 30:
        urgency = "moderate"
        opener = "I wanted to follow up on our recent discussions."
    else:
        urgency = "firm"
        opener = "I wanted to reach out as it's been a while since we last connected."

    # Build subject line
    if last_email and last_email.get('subject'):
        original_subject = last_email['subject']
        if not original_subject.lower().startswith('re:'):
            subject = f"Re: {original_subject}"
        else:
            subject = original_subject
    else:
        subject = f"Following up - {project_name}"

    # Build email body based on status
    if status == 'First Contact':
        body = f"""Dear {contact_name or 'there'},

{opener}

I wanted to follow up regarding {project_name}. We're excited about the possibility of working together on this project.

If you have any questions about our approach or would like to discuss next steps, I'd be happy to schedule a call at your convenience.

Looking forward to hearing from you.

Best regards,
"""
    elif status == 'Proposal Prep':
        body = f"""Dear {contact_name or 'there'},

{opener}

I wanted to touch base regarding {project_name}. We're currently preparing the proposal and wanted to check if you have any additional requirements or questions we should address.

Please let me know if there's anything else you'd like us to include.

Best regards,
"""
    elif status == 'Proposal Sent':
        body = f"""Dear {contact_name or 'there'},

{opener}

I wanted to follow up on the proposal we sent for {project_name}. I hope you've had a chance to review it.

If you have any questions or would like to discuss any aspects of our proposal, I'd be happy to schedule a call.

Looking forward to your feedback.

Best regards,
"""
    elif status == 'Negotiation':
        what_waiting = waiting_for if waiting_for else "the contract terms"
        body = f"""Dear {contact_name or 'there'},

{opener}

I wanted to follow up on {project_name}. We're awaiting {what_waiting} to proceed to the next stage.

Please let me know if there's anything I can help clarify or if you need any additional information from our side.

Best regards,
"""
    else:
        body = f"""Dear {contact_name or 'there'},

{opener}

I wanted to follow up regarding {project_name}. Please let me know if there have been any updates on your end, or if there's anything we can help with.

Looking forward to hearing from you.

Best regards,
"""

    return {
        'subject': subject,
        'body': body.strip(),
        'to_email': proposal.get('contact_email'),
        'to_name': proposal.get('contact_person'),
        'urgency': urgency,
        'reasoning': f"Follow-up for {status} proposal, {days} days since last contact"
    }


def create_followup_suggestion(conn, proposal: Dict, draft: Dict,
                                dry_run: bool = False) -> bool:
    """Create an ai_suggestion for the follow-up draft"""
    cursor = conn.cursor()

    # Check if we already have a pending followup suggestion for this proposal
    cursor.execute("""
        SELECT suggestion_id FROM ai_suggestions
        WHERE suggestion_type = 'follow_up_needed'
        AND project_code = ?
        AND status = 'pending'
    """, (proposal['project_code'],))

    if cursor.fetchone():
        print(f"  Skipped: Pending follow-up already exists")
        return False

    suggestion_data = {
        'proposal_id': proposal['proposal_id'],
        'project_code': proposal['project_code'],
        'project_name': proposal['project_name'],
        'to_email': draft['to_email'],
        'to_name': draft['to_name'],
        'subject': draft['subject'],
        'body': draft['body'],
        'urgency': draft['urgency'],
        'days_since_contact': proposal.get('days_since_contact'),
        'status': proposal.get('status'),
    }

    if dry_run:
        print(f"  [DRY RUN] Would create follow-up suggestion")
        print(f"    Subject: {draft['subject'][:50]}...")
        return True

    cursor.execute("""
        INSERT INTO ai_suggestions
        (source_type, source_id, suggestion_type, title, description,
         suggested_data, confidence_score, project_code, proposal_id,
         status, created_at)
        VALUES ('proposal', ?, 'follow_up_needed', ?, ?, ?, 0.8, ?, ?, 'pending', datetime('now'))
    """, (
        proposal['proposal_id'],
        f"Follow-up: {proposal['project_name'][:40]}",
        draft['reasoning'],
        json.dumps(suggestion_data),
        proposal['project_code'],
        proposal['proposal_id']
    ))
    conn.commit()
    return True


def main():
    parser = argparse.ArgumentParser(description='Follow-up Email Drafter')
    parser.add_argument('--days', type=int, default=14,
                        help='Days since contact threshold (default: 14)')
    parser.add_argument('--project-code', type=str,
                        help='Generate follow-up for specific project')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would happen without making changes')
    args = parser.parse_args()

    print("=" * 60)
    print("FOLLOW-UP EMAIL DRAFTER")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Threshold: {args.days} days since contact")
    print("=" * 60)

    conn = get_db_connection()

    # Get proposals needing follow-up
    proposals = get_proposals_needing_followup(
        conn,
        days_threshold=args.days,
        project_code=args.project_code
    )

    print(f"\nFound {len(proposals)} proposals needing follow-up")

    if not proposals:
        print("No proposals need follow-up at this time.")
        return

    results = {
        'processed': 0,
        'suggestions_created': 0,
        'skipped': 0
    }

    print("\n" + "-" * 60)
    for proposal in proposals:
        print(f"\n[{proposal['project_code']}] {proposal['project_name']}")
        print(f"  Status: {proposal['status']}, Days since contact: {proposal['days_since_contact']}")
        print(f"  Contact: {proposal['contact_person']} <{proposal['contact_email']}>")

        results['processed'] += 1

        # Get last email context
        last_email = get_last_email_context(conn, proposal['project_code'])

        # Generate draft
        draft = generate_followup_draft(proposal, last_email)
        print(f"  Draft subject: {draft['subject'][:50]}...")

        # Create suggestion
        if create_followup_suggestion(conn, proposal, draft, dry_run=args.dry_run):
            results['suggestions_created'] += 1
        else:
            results['skipped'] += 1

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Proposals processed: {results['processed']}")
    print(f"Follow-up drafts created: {results['suggestions_created']}")
    print(f"Skipped (already pending): {results['skipped']}")

    if args.dry_run:
        print("\n[DRY RUN - No changes made]")

    conn.close()


if __name__ == '__main__':
    main()
