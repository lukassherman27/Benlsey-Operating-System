#!/usr/bin/env python3
"""
Calculate proposal health scores, action items, and insights from email data.
Issue #113: Fix empty insight fields on proposals.
Issue #127: Add action_due calculation.

This script:
1. Calculates health_score (0-100) based on activity, status, and email patterns
2. Populates action_needed with concrete next steps
3. Calculates action_due date based on status and last contact
4. Assigns action_owner based on proposal characteristics
5. Analyzes sentiment from recent client emails
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = "database/bensley_master.db"

# Status categories
ACTIVE_STATUSES = ['First Contact', 'Proposal Sent', 'Proposal Prep', 'Negotiation', 'On Hold']
CLOSED_WON = ['Contract Signed']
CLOSED_LOST = ['Declined', 'Lost', 'Dormant']


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def calculate_health_score(proposal: Dict[str, Any], email_stats: Dict[str, Any]) -> int:
    """
    Calculate health score (0-100) based on:
    - Days since last contact (0-40 points)
    - Ball in court status (0-20 points)
    - Email activity (0-20 points)
    - Status progression (0-20 points)
    """
    score = 100

    # Days since contact penalty (max -40)
    days = proposal.get('days_since_contact') or 0
    if days > 60:
        score -= 40
    elif days > 30:
        score -= 30
    elif days > 14:
        score -= 15
    elif days > 7:
        score -= 5

    # Ball in court penalty (max -20)
    ball = proposal.get('ball_in_court', 'us')
    status = proposal.get('status', '')
    if ball == 'them' and days > 14:
        score -= 20  # They're stalling
    elif ball == 'them' and days > 7:
        score -= 10
    elif ball == 'on_hold':
        score -= 15

    # Email activity bonus/penalty (max -20)
    email_count = email_stats.get('email_count', 0)
    recent_emails = email_stats.get('recent_email_count', 0)  # Last 30 days
    if email_count == 0:
        score -= 20  # No communication at all
    elif recent_emails == 0 and days > 14:
        score -= 15  # No recent activity
    elif recent_emails > 3:
        score += 5  # Active conversation (capped at 100)

    # Status-based adjustment
    if status == 'Negotiation':
        score += 10  # Close to winning
    elif status == 'On Hold':
        score -= 10

    return max(0, min(100, score))


def determine_action_needed(proposal: Dict[str, Any], email_stats: Dict[str, Any]) -> str:
    """
    Determine concrete action needed based on proposal state.
    Returns actionable text like "Follow up - 14 days since last contact"
    """
    days = proposal.get('days_since_contact') or 0
    ball = proposal.get('ball_in_court', 'us')
    status = proposal.get('status', '')
    waiting_for = proposal.get('waiting_for', '')

    # If we know what we're waiting for, use that
    if waiting_for:
        if ball == 'them':
            return f"Waiting on: {waiting_for}"
        else:
            return f"Need to provide: {waiting_for}"

    # Generate action based on status and timing
    if status == 'First Contact':
        if days > 14:
            return f"Follow up on initial contact ({days} days ago)"
        elif days > 7:
            return "Schedule introductory call"
        else:
            return "Prepare proposal scope"

    elif status == 'Proposal Prep':
        return "Complete and send proposal"

    elif status == 'Proposal Sent':
        if ball == 'them':
            if days > 21:
                return f"Check in on proposal ({days} days - may need re-engagement)"
            elif days > 14:
                return f"Follow up on proposal ({days} days since sent)"
            elif days > 7:
                return "Gentle follow-up on proposal status"
            else:
                return "Awaiting client review"
        else:
            return "Address client questions/feedback"

    elif status == 'Negotiation':
        if ball == 'them':
            if days > 14:
                return f"Push for decision ({days} days in negotiation)"
            else:
                return "Awaiting contract/terms decision"
        else:
            return "Send revised terms/proposal"

    elif status == 'On Hold':
        if days > 30:
            return "Check if project should be reactivated or closed"
        else:
            return "On hold - review status periodically"

    elif status in CLOSED_WON:
        return "Active project - no proposal action needed"

    elif status in CLOSED_LOST:
        return "Closed - no action needed"

    return "Review proposal status"


def assign_action_owner(proposal: Dict[str, Any]) -> Optional[str]:
    """
    Assign owner based on proposal characteristics:
    - bill: High-value deals (>$1M), key client relationships
    - brian: Design-focused, technical reviews
    - lukas: Operations, standard follow-ups, admin
    - mink: Specific technical disciplines
    """
    value = proposal.get('project_value') or 0
    status = proposal.get('status', '')

    # High-value = Bill
    if value >= 1000000:
        return 'bill'

    # Negotiation stage = Bill (needs senior attention)
    if status == 'Negotiation':
        return 'bill'

    # Mid-value = Brian
    if value >= 300000:
        return 'brian'

    # Everything else = Lukas
    return 'lukas'


def calculate_action_due(proposal: Dict[str, Any]) -> Optional[str]:
    """
    Calculate when the next action is due based on status and last contact.
    Issue #127: This field was 0% populated.

    Returns ISO date string (YYYY-MM-DD) for when action is due.
    """
    status = proposal.get('status', '')
    days = proposal.get('days_since_contact') or 0
    ball = proposal.get('ball_in_court', 'us')
    last_contact = proposal.get('last_contact_date')

    # Closed proposals don't need action due dates
    if status in CLOSED_WON + CLOSED_LOST:
        return None

    # Calculate base date (last contact or today)
    if last_contact:
        try:
            base_date = datetime.strptime(last_contact[:10], '%Y-%m-%d')
        except (ValueError, TypeError):
            base_date = datetime.now()
    else:
        base_date = datetime.now()

    # Determine follow-up window based on status and ball in court
    if status == 'Negotiation':
        # Negotiation = urgent, short window
        if ball == 'us':
            follow_up_days = 3  # We need to respond quickly
        else:
            follow_up_days = 7  # Follow up after 1 week
    elif status == 'Proposal Sent':
        if ball == 'us':
            follow_up_days = 2  # We have questions to answer
        else:
            follow_up_days = 7  # Standard follow-up window
    elif status == 'First Contact':
        follow_up_days = 7  # Week to schedule intro call
    elif status == 'Proposal Prep':
        follow_up_days = 5  # Should send proposal within 5 days
    elif status == 'On Hold':
        follow_up_days = 30  # Monthly check-in
    else:
        follow_up_days = 14  # Default 2-week window

    due_date = base_date + timedelta(days=follow_up_days)
    return due_date.strftime('%Y-%m-%d')


def get_email_stats(conn, proposal_id: int) -> Dict[str, Any]:
    """Get email statistics for a proposal"""
    cursor = conn.cursor()

    # Total emails linked
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM email_proposal_links
        WHERE proposal_id = ?
    """, (proposal_id,))
    total = cursor.fetchone()['count']

    # Recent emails (last 30 days)
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM email_proposal_links epl
        JOIN emails e ON epl.email_id = e.email_id
        WHERE epl.proposal_id = ?
          AND e.date >= date('now', '-30 days')
    """, (proposal_id,))
    recent = cursor.fetchone()['count']

    # Last client email
    cursor.execute("""
        SELECT e.date, e.subject, e.snippet, e.sender_category
        FROM email_proposal_links epl
        JOIN emails e ON epl.email_id = e.email_id
        WHERE epl.proposal_id = ?
          AND e.sender_category = 'client'
        ORDER BY e.date DESC
        LIMIT 1
    """, (proposal_id,))
    last_client = cursor.fetchone()

    return {
        'email_count': total,
        'recent_email_count': recent,
        'last_client_email': dict(last_client) if last_client else None
    }


def simple_sentiment(text: str) -> str:
    """
    Simple keyword-based sentiment analysis.
    Returns: 'positive', 'neutral', 'concerned', 'negative'
    """
    if not text:
        return 'neutral'

    text = text.lower()

    positive_words = ['thank', 'great', 'excellent', 'approve', 'agree', 'happy',
                     'pleased', 'look forward', 'excited', 'proceed', 'confirm']
    negative_words = ['concern', 'issue', 'problem', 'delay', 'unfortunately',
                     'unable', 'cannot', 'disappointed', 'reconsider', 'budget']

    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)

    if neg_count > pos_count + 1:
        return 'concerned'
    elif neg_count > 0 and pos_count == 0:
        return 'concerned'
    elif pos_count > neg_count:
        return 'positive'
    else:
        return 'neutral'


def analyze_last_sentiment(email_stats: Dict[str, Any]) -> Optional[str]:
    """Analyze sentiment from last client email"""
    last_email = email_stats.get('last_client_email')
    if not last_email:
        return None

    text = (last_email.get('subject', '') + ' ' + (last_email.get('snippet') or '')).strip()
    return simple_sentiment(text)


def update_proposal(conn, proposal_id: int, updates: Dict[str, Any]):
    """Update proposal with calculated values"""
    cursor = conn.cursor()

    set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [proposal_id]

    cursor.execute(f"""
        UPDATE proposals
        SET {set_clause}, updated_at = datetime('now')
        WHERE proposal_id = ?
    """, values)


def run_calculations():
    """Main function to calculate and update all proposals"""
    conn = get_connection()
    cursor = conn.cursor()

    # Get all proposals
    cursor.execute("""
        SELECT
            proposal_id, project_code, project_name, status,
            ball_in_court, days_since_contact, project_value,
            waiting_for, health_score, action_needed, action_owner,
            last_contact_date
        FROM proposals
    """)
    proposals = [dict(row) for row in cursor.fetchall()]

    logger.info(f"Processing {len(proposals)} proposals...")

    updated = 0
    for proposal in proposals:
        proposal_id = proposal['proposal_id']
        status = proposal.get('status', '')

        # Get email stats
        email_stats = get_email_stats(conn, proposal_id)

        # Calculate new values
        new_health = calculate_health_score(proposal, email_stats)
        new_action = determine_action_needed(proposal, email_stats)
        new_owner = assign_action_owner(proposal)
        new_sentiment = analyze_last_sentiment(email_stats)
        new_action_due = calculate_action_due(proposal)

        # Build update dict
        updates = {
            'health_score': new_health,
            'action_needed': new_action,
            'action_due': new_action_due,
        }

        # Only set owner if not already set or if it's a pipeline proposal
        if status in ACTIVE_STATUSES:
            updates['action_owner'] = new_owner

        if new_sentiment:
            updates['last_sentiment'] = new_sentiment

        # Update
        update_proposal(conn, proposal_id, updates)
        updated += 1

        if updated % 20 == 0:
            logger.info(f"Processed {updated}/{len(proposals)}...")

    conn.commit()
    conn.close()

    logger.info(f"Done! Updated {updated} proposals.")

    # Print summary
    print("\n" + "="*60)
    print("PROPOSAL INSIGHTS CALCULATION COMPLETE")
    print("="*60)
    print(f"Total proposals processed: {updated}")
    print("\nRun this query to see results:")
    print("""
sqlite3 database/bensley_master.db "
SELECT project_code, status, health_score, action_due, action_owner, action_needed
FROM proposals
WHERE status IN ('First Contact', 'Proposal Sent', 'Negotiation', 'On Hold')
ORDER BY action_due ASC
LIMIT 20;
"
    """)


if __name__ == "__main__":
    run_calculations()
