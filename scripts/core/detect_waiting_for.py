#!/usr/bin/env python3
"""
Detect waiting_for status for proposals based on email content analysis.

This script analyzes the MOST RECENT emails for each proposal to determine:
- waiting_for: 'client_response' (ball with them) or 'our_response' (we need to act)
- last_sender: 'us' or 'them'
- last_action_type: what the last substantive action was

Logic:
1. Get the most recent 3 emails for each proposal
2. Classify each email by its "action type" (not just who sent it)
3. Determine who has the "ball" based on content patterns

Action Types:
- QUESTION: Asked something that needs answer
- REQUEST: Asked for something to be done/sent
- PROMISE: Said they will do something
- DELIVERY: Sent/attached something
- ACKNOWLEDGMENT: Just said thanks/ok/received
- UPDATE: Provided status update without asking anything
- CLOSING: Wrapping up, looking forward to working together
"""

import sqlite3
import re
import os
from datetime import datetime

DATABASE_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

# Bensley email domains
BENSLEY_DOMAINS = ['bensley.com', 'bensleydesign.com', 'bensley.co.th', 'bensley.id']

def is_bensley_email(email: str) -> bool:
    """Check if email is from Bensley (internal)"""
    if not email:
        return False
    email_lower = email.lower()
    return any(domain in email_lower for domain in BENSLEY_DOMAINS)

def classify_email_action(body: str, subject: str) -> str:
    """
    Classify the primary action/intent of an email.
    Returns: QUESTION, REQUEST, PROMISE, DELIVERY, ACKNOWLEDGMENT, UPDATE, CLOSING
    """
    if not body:
        body = ""
    if not subject:
        subject = ""

    text = (body + " " + subject).lower()

    # Clean up HTML entities and extra whitespace
    text = re.sub(r'&nbsp;|&amp;|&lt;|&gt;', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    # Priority 1: REQUEST patterns (someone asking us/them to DO something)
    request_patterns = [
        r'can you (please )?(send|provide|share|resend|forward|update|confirm|let)',
        r'could you (please )?(send|provide|share|resend|forward|update|confirm|let)',
        r'please (send|provide|share|resend|forward|give|update|confirm|let|advise)',
        r'kindly (send|provide|share|resend|forward|give|update|confirm)',
        r'we need (you to|the|your)',
        r'we (are|were) hoping (you|to get)',
        r'awaiting (your|the|a)',
        r'looking forward to (receiving|getting|your)',
        r'when can (you|we expect)',
        r'do you have (the|a|any)',
    ]
    for pattern in request_patterns:
        if re.search(pattern, text):
            return 'REQUEST'

    # Priority 2: QUESTION patterns (asking for information/decision)
    question_patterns = [
        r'\?\s*$',  # Ends with question mark
        r'what (do you|would you|is your|are your)',
        r'how (do you|would you|should we)',
        r'when (can|will|would|should)',
        r'is (there|this|it|that) (ok|okay|fine|acceptable)',
        r'any (update|news|progress|feedback)',
        r'let (me|us) know (if|what|when|how|your)',
    ]
    for pattern in question_patterns:
        if re.search(pattern, text):
            return 'QUESTION'

    # Priority 3: DELIVERY patterns (sending/attaching something)
    delivery_patterns = [
        r'(please )?(find |see )?(attached|enclosed)',
        r'(i\'m |we\'re |we are )?sending (you |the )?',
        r'here (is|are) (the|our|your)',
        r'(i\'ve|we\'ve|we have) (sent|attached|shared|provided)',
        r'as (attached|promised|discussed|requested)',
        r'(proposal|contract|documents?|files?|drawings?) attached',
        r'per (your )?request',
        r'following up .* (attached|sending)',
    ]
    for pattern in delivery_patterns:
        if re.search(pattern, text):
            return 'DELIVERY'

    # Priority 4: PROMISE patterns (saying they will do something)
    promise_patterns = [
        r'(i\'ll|we\'ll|we will|i will) (send|get back|revert|update|provide|share)',
        r'will (revert|get back|send|respond|update|provide)',
        r'(i|we) (am|are) (working|looking) (on|into)',
        r'(will|should) be (sending|providing|getting|sharing)',
        r'once (i|we) (have|get|receive)',
        r'as soon as (i|we)',
        r'shortly|soon|in (a|the) (few|next|coming)',
    ]
    for pattern in promise_patterns:
        if re.search(pattern, text):
            return 'PROMISE'

    # Priority 5: ACKNOWLEDGMENT patterns (just confirming receipt/understanding)
    ack_patterns = [
        r'^(thanks|thank you|received|noted|ok|okay|got it|sounds good)',
        r'(thanks|thank you) (for|so much)',
        r'^received\.?\s*$',
        r'^noted\.?\s*$',
        r'^great\.?\s*$',
        r'^perfect\.?\s*$',
        r'(will|shall) (review|look|check|go through)',
    ]
    for pattern in ack_patterns:
        if re.search(pattern, text[:200]):  # Check beginning of email
            return 'ACKNOWLEDGMENT'

    # Priority 6: CLOSING patterns (wrapping up, looking forward)
    closing_patterns = [
        r'look(ing)? forward to (working|collaborating|partnering)',
        r'(excited|delighted|pleased) to (work|partner|collaborate)',
        r'thank (you|u) .* (welcoming|hospitality|meeting)',
        r'(was |were )?great (to |meeting|seeing)',
        r'(enjoyed|pleasure) (meeting|seeing|talking)',
    ]
    for pattern in closing_patterns:
        if re.search(pattern, text):
            return 'CLOSING'

    # Priority 7: UPDATE patterns (providing info without asking)
    update_patterns = [
        r'(just )?(wanted to|just to) (update|inform|let you know)',
        r'(fyi|for your (info|information|reference))',
        r'(quick )?(update|status):?',
        r'(i|we) (wanted|thought) (you|to)',
    ]
    for pattern in update_patterns:
        if re.search(pattern, text):
            return 'UPDATE'

    # Default: treat as UPDATE
    return 'UPDATE'


def determine_waiting_for(emails: list) -> tuple:
    """
    Given a list of recent emails (newest first), determine waiting_for status.

    Returns: (waiting_for, last_sender, last_action_type, reasoning)

    Logic:
    - If they sent a REQUEST/QUESTION → we need to respond → our_response
    - If we sent a REQUEST/QUESTION → they need to respond → client_response
    - If they sent a PROMISE → they'll do something → client_response
    - If we sent a PROMISE → we need to deliver → our_response
    - If they sent DELIVERY → we need to review/respond → our_response (usually)
    - If we sent DELIVERY → they need to review/respond → client_response
    - ACKNOWLEDGMENT doesn't change the ball (look at previous email)
    - CLOSING usually means waiting for client next steps → client_response
    """
    if not emails:
        return (None, None, None, "No emails")

    # Look at most recent emails
    for i, email in enumerate(emails[:3]):  # Check up to 3 recent emails
        sender = email['sender']  # 'us' or 'them'
        action = email['action_type']

        # Skip acknowledgments - they don't move the ball
        if action == 'ACKNOWLEDGMENT' and i < len(emails) - 1:
            continue

        # Determine waiting_for based on sender + action combination
        if sender == 'them':
            if action in ['REQUEST', 'QUESTION']:
                return ('our_response', sender, action, f"They asked something (#{i+1})")
            elif action == 'PROMISE':
                return ('client_response', sender, action, f"They promised to deliver (#{i+1})")
            elif action == 'DELIVERY':
                return ('our_response', sender, action, f"They sent something to review (#{i+1})")
            elif action == 'CLOSING':
                return ('client_response', sender, action, f"Closing pleasantries - ball with them (#{i+1})")
            elif action == 'UPDATE':
                # They provided update - usually we're waiting for more from them
                return ('client_response', sender, action, f"They provided update (#{i+1})")
        else:  # sender == 'us'
            if action in ['REQUEST', 'QUESTION']:
                return ('client_response', sender, action, f"We asked something (#{i+1})")
            elif action == 'PROMISE':
                return ('our_response', sender, action, f"We promised to deliver (#{i+1})")
            elif action == 'DELIVERY':
                return ('client_response', sender, action, f"We sent something (#{i+1})")
            elif action in ['CLOSING', 'UPDATE']:
                return ('client_response', sender, action, f"We updated them (#{i+1})")

    # Fallback: check last sender
    last = emails[0]
    if last['sender'] == 'us':
        return ('client_response', 'us', last['action_type'], "We sent last (fallback)")
    else:
        return ('our_response', 'them', last['action_type'], "They sent last (fallback)")


def main():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # First, add columns if they don't exist
    try:
        cursor.execute("ALTER TABLE proposals ADD COLUMN waiting_for TEXT")
        print("Added waiting_for column")
    except:
        pass  # Column exists

    try:
        cursor.execute("ALTER TABLE proposals ADD COLUMN last_sender TEXT")
        print("Added last_sender column")
    except:
        pass  # Column exists

    try:
        cursor.execute("ALTER TABLE proposals ADD COLUMN last_action_type TEXT")
        print("Added last_action_type column")
    except:
        pass  # Column exists

    try:
        cursor.execute("ALTER TABLE proposals ADD COLUMN last_email_date TEXT")
        print("Added last_email_date column")
    except:
        pass  # Column exists

    try:
        cursor.execute("ALTER TABLE proposals ADD COLUMN our_emails_count INTEGER DEFAULT 0")
        print("Added our_emails_count column")
    except:
        pass

    try:
        cursor.execute("ALTER TABLE proposals ADD COLUMN their_emails_count INTEGER DEFAULT 0")
        print("Added their_emails_count column")
    except:
        pass

    conn.commit()

    # Get all proposals with email links
    cursor.execute("""
        SELECT DISTINCT p.proposal_id, p.project_code, p.project_name
        FROM proposals p
        JOIN email_proposal_links epl ON p.proposal_id = epl.proposal_id
        WHERE p.current_status NOT IN ('lost', 'archived', 'n.a')
        ORDER BY p.project_code
    """)
    proposals = cursor.fetchall()

    print(f"\nAnalyzing {len(proposals)} proposals with linked emails...\n")

    results = {
        'client_response': 0,
        'our_response': 0,
        'unknown': 0
    }

    sample_output = []

    for prop in proposals:
        proposal_id = prop['proposal_id']
        project_code = prop['project_code']
        project_name = prop['project_name']

        # Get recent emails for this proposal (newest first)
        cursor.execute("""
            SELECT
                e.email_id,
                e.sender_email,
                e.subject,
                e.body_full,
                e.date_normalized
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            WHERE epl.proposal_id = ?
            ORDER BY e.date_normalized DESC
            LIMIT 5
        """, (proposal_id,))
        emails_raw = cursor.fetchall()

        if not emails_raw:
            continue

        # Process emails
        emails = []
        for e in emails_raw:
            sender_email = e['sender_email'] or ''
            is_from_us = is_bensley_email(sender_email)
            action = classify_email_action(e['body_full'], e['subject'])
            emails.append({
                'sender': 'us' if is_from_us else 'them',
                'action_type': action,
                'date': e['date_normalized'],
                'subject': e['subject']
            })

        # Get email counts
        cursor.execute("""
            SELECT
                SUM(CASE WHEN e.sender_email LIKE '%bensley%' THEN 1 ELSE 0 END) as our_count,
                SUM(CASE WHEN e.sender_email NOT LIKE '%bensley%' THEN 1 ELSE 0 END) as their_count
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            WHERE epl.proposal_id = ?
        """, (proposal_id,))
        counts = cursor.fetchone()
        our_count = counts['our_count'] or 0
        their_count = counts['their_count'] or 0

        # Determine waiting_for
        waiting_for, last_sender, last_action, reasoning = determine_waiting_for(emails)

        # Update database
        cursor.execute("""
            UPDATE proposals SET
                waiting_for = ?,
                last_sender = ?,
                last_action_type = ?,
                last_email_date = ?,
                our_emails_count = ?,
                their_emails_count = ?
            WHERE proposal_id = ?
        """, (waiting_for, last_sender, last_action, emails[0]['date'] if emails else None,
              our_count, their_count, proposal_id))

        # Track results
        if waiting_for:
            results[waiting_for] = results.get(waiting_for, 0) + 1
        else:
            results['unknown'] += 1

        # Sample output for verification
        if len(sample_output) < 20:
            sample_output.append({
                'code': project_code,
                'name': project_name[:35],
                'waiting_for': waiting_for,
                'last_sender': last_sender,
                'last_action': last_action,
                'reasoning': reasoning,
                'recent_emails': [(e['sender'], e['action_type'], e['subject'][:30] if e['subject'] else '') for e in emails[:3]]
            })

    conn.commit()

    # Print results
    print("=" * 80)
    print("WAITING_FOR DETECTION RESULTS")
    print("=" * 80)
    print(f"\n  client_response (ball with them): {results['client_response']}")
    print(f"  our_response (we need to act):    {results['our_response']}")
    print(f"  unknown:                           {results['unknown']}")

    print("\n" + "=" * 80)
    print("SAMPLE ANALYSIS (first 20)")
    print("=" * 80)

    for s in sample_output:
        print(f"\n{s['code']} ({s['name']})")
        print(f"  → waiting_for: {s['waiting_for']} | last_sender: {s['last_sender']} | action: {s['last_action']}")
        print(f"  → reasoning: {s['reasoning']}")
        print(f"  → recent: {s['recent_emails']}")

    # Show proposals needing our response (urgent)
    print("\n" + "=" * 80)
    print("URGENT: PROPOSALS NEEDING OUR RESPONSE")
    print("=" * 80)

    cursor.execute("""
        SELECT
            project_code,
            project_name,
            current_status,
            days_since_contact,
            last_action_type,
            our_emails_count,
            their_emails_count
        FROM proposals
        WHERE waiting_for = 'our_response'
        AND current_status NOT IN ('lost', 'archived', 'n.a', 'Contract Signed', 'Contract signed')
        ORDER BY days_since_contact DESC
        LIMIT 15
    """)

    urgent = cursor.fetchall()
    for u in urgent:
        print(f"\n  {u['project_code']} ({u['project_name'][:40]})")
        print(f"    Status: {u['current_status']} | {u['days_since_contact']} days silent")
        print(f"    Last action: {u['last_action_type']} | Emails: us={u['our_emails_count']}, them={u['their_emails_count']}")

    conn.close()
    print("\n\nDone!")


if __name__ == "__main__":
    main()
