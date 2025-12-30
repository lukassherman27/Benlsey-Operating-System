#!/usr/bin/env python3
"""
Backfill proposal_activities from existing data.
Issue #140: Activity Tracking Database

This script populates proposal_activities from:
1. email_proposal_links - All linked emails become activities
2. proposals table - Extract milestones from known dates
3. meeting_transcripts - If linked to proposals

Run once to seed historical data, then new activities are created on sync.
"""

import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = "database/bensley_master.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def backfill_email_activities(conn):
    """Create activities from email_proposal_links."""
    cursor = conn.cursor()

    # Check how many we already have
    cursor.execute("SELECT COUNT(*) FROM proposal_activities WHERE source_type = 'email'")
    existing = cursor.fetchone()[0]
    if existing > 0:
        logger.info(f"Already have {existing} email activities, skipping backfill")
        return 0

    # Get all linked emails with their details
    cursor.execute("""
        SELECT
            epl.email_id,
            epl.proposal_id,
            e.date as email_date,
            e.subject,
            e.sender_email,
            e.sender_category,
            e.snippet,
            e.body_preview,
            CASE
                WHEN e.sender_category IN ('bill', 'brian', 'lukas', 'mink', 'bensley_other') THEN 'email_sent'
                ELSE 'email_received'
            END as activity_type,
            CASE
                WHEN e.sender_category = 'bill' THEN 'bill'
                WHEN e.sender_category = 'brian' THEN 'brian'
                WHEN e.sender_category = 'lukas' THEN 'lukas'
                WHEN e.sender_category = 'mink' THEN 'mink'
                WHEN e.sender_category = 'bensley_other' THEN 'bensley'
                ELSE 'client'
            END as actor
        FROM email_proposal_links epl
        JOIN emails e ON epl.email_id = e.email_id
        WHERE e.date IS NOT NULL
        ORDER BY e.date
    """)

    emails = cursor.fetchall()
    logger.info(f"Found {len(emails)} linked emails to backfill")

    count = 0
    for email in emails:
        try:
            cursor.execute("""
                INSERT INTO proposal_activities (
                    proposal_id, activity_type, activity_date,
                    source_type, source_id,
                    actor, actor_email,
                    title, summary
                ) VALUES (?, ?, ?, 'email', ?, ?, ?, ?, ?)
            """, (
                email['proposal_id'],
                email['activity_type'],
                email['email_date'],
                str(email['email_id']),
                email['actor'],
                email['sender_email'],
                email['subject'],
                email['snippet'] or email['body_preview']
            ))
            count += 1
        except Exception as e:
            logger.error(f"Error inserting activity for email {email['email_id']}: {e}")

    conn.commit()
    logger.info(f"Created {count} email activities")
    return count


def backfill_milestones(conn):
    """Create milestones from known proposal dates."""
    cursor = conn.cursor()

    # Check how many we already have
    cursor.execute("SELECT COUNT(*) FROM proposal_milestones")
    existing = cursor.fetchone()[0]
    if existing > 0:
        logger.info(f"Already have {existing} milestones, skipping backfill")
        return 0

    # Get proposals with their key dates
    cursor.execute("""
        SELECT
            proposal_id, project_code, project_name, status,
            first_contact_date, proposal_sent_date, contract_signed_date,
            project_value
        FROM proposals
        WHERE first_contact_date IS NOT NULL
           OR proposal_sent_date IS NOT NULL
           OR contract_signed_date IS NOT NULL
    """)

    proposals = cursor.fetchall()
    logger.info(f"Found {len(proposals)} proposals with milestone dates")

    count = 0
    for p in proposals:
        # First contact milestone
        if p['first_contact_date']:
            try:
                cursor.execute("""
                    INSERT INTO proposal_milestones (
                        proposal_id, milestone_type, milestone_date,
                        description, proposal_value_at_milestone, status_at_milestone, created_by
                    ) VALUES (?, 'first_contact', ?, ?, ?, 'First Contact', 'system')
                """, (
                    p['proposal_id'],
                    p['first_contact_date'],
                    f"Initial contact for {p['project_name']}",
                    p['project_value']
                ))
                count += 1
            except Exception as e:
                logger.error(f"Error creating first_contact milestone for {p['project_code']}: {e}")

        # Proposal sent milestone
        if p['proposal_sent_date']:
            try:
                cursor.execute("""
                    INSERT INTO proposal_milestones (
                        proposal_id, milestone_type, milestone_date,
                        description, proposal_value_at_milestone, status_at_milestone, created_by
                    ) VALUES (?, 'proposal_sent', ?, ?, ?, 'Proposal Sent', 'system')
                """, (
                    p['proposal_id'],
                    p['proposal_sent_date'],
                    f"Proposal sent for {p['project_name']}",
                    p['project_value']
                ))
                count += 1
            except Exception as e:
                logger.error(f"Error creating proposal_sent milestone for {p['project_code']}: {e}")

        # Contract signed milestone
        if p['contract_signed_date']:
            try:
                cursor.execute("""
                    INSERT INTO proposal_milestones (
                        proposal_id, milestone_type, milestone_date,
                        description, proposal_value_at_milestone, status_at_milestone, created_by
                    ) VALUES (?, 'contract_signed', ?, ?, ?, 'Contract Signed', 'system')
                """, (
                    p['proposal_id'],
                    p['contract_signed_date'],
                    f"Contract signed for {p['project_name']} - WON!",
                    p['project_value']
                ))
                count += 1
            except Exception as e:
                logger.error(f"Error creating contract_signed milestone for {p['project_code']}: {e}")

        # Lost/Declined milestone based on current status
        if p['status'] in ('Lost', 'Declined'):
            try:
                cursor.execute("""
                    INSERT INTO proposal_milestones (
                        proposal_id, milestone_type, milestone_date,
                        description, proposal_value_at_milestone, status_at_milestone, created_by
                    ) VALUES (?, ?, date('now'), ?, ?, ?, 'system')
                """, (
                    p['proposal_id'],
                    'lost' if p['status'] == 'Lost' else 'declined',
                    f"Proposal {p['status'].lower()} for {p['project_name']}",
                    p['project_value'],
                    p['status']
                ))
                count += 1
            except Exception as e:
                logger.error(f"Error creating lost/declined milestone for {p['project_code']}: {e}")

    conn.commit()
    logger.info(f"Created {count} milestones")
    return count


def backfill_transcript_activities(conn):
    """Create activities from meeting_transcripts linked to proposals."""
    cursor = conn.cursor()

    # Check if we have transcript links
    cursor.execute("""
        SELECT COUNT(*) FROM meeting_transcripts
        WHERE proposal_id IS NOT NULL OR detected_project_code IS NOT NULL
    """)
    transcript_count = cursor.fetchone()[0]

    if transcript_count == 0:
        logger.info("No transcripts linked to proposals/projects")
        return 0

    # Get linked transcripts
    cursor.execute("""
        SELECT
            t.id as transcript_id,
            t.proposal_id,
            p.proposal_id as derived_proposal_id,
            COALESCE(t.meeting_date, t.recorded_date) as meeting_date,
            COALESCE(t.meeting_title, t.audio_filename) as title,
            t.summary,
            t.participants as attendees
        FROM meeting_transcripts t
        LEFT JOIN proposals p ON t.detected_project_code = p.project_code
        WHERE t.proposal_id IS NOT NULL OR p.proposal_id IS NOT NULL
    """)

    transcripts = cursor.fetchall()
    logger.info(f"Found {len(transcripts)} transcripts to backfill")

    count = 0
    for t in transcripts:
        proposal_id = t['proposal_id'] or t['derived_proposal_id']
        if not proposal_id:
            continue

        try:
            cursor.execute("""
                INSERT INTO proposal_activities (
                    proposal_id, activity_type, activity_date,
                    source_type, source_id,
                    actor, title, summary
                ) VALUES (?, 'meeting', ?, 'transcript', ?, 'team', ?, ?)
            """, (
                proposal_id,
                t['meeting_date'],
                str(t['transcript_id']),
                t['title'],
                t['summary']
            ))
            count += 1
        except Exception as e:
            logger.error(f"Error creating activity for transcript {t['transcript_id']}: {e}")

    conn.commit()
    logger.info(f"Created {count} meeting activities")
    return count


def print_summary(conn):
    """Print summary of what was created."""
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("ACTIVITY TRACKING BACKFILL COMPLETE")
    print("=" * 60)

    cursor.execute("SELECT COUNT(*) FROM proposal_activities")
    print(f"Total activities: {cursor.fetchone()[0]}")

    cursor.execute("""
        SELECT activity_type, COUNT(*) as cnt
        FROM proposal_activities
        GROUP BY activity_type
        ORDER BY cnt DESC
    """)
    print("\nBy type:")
    for row in cursor.fetchall():
        print(f"  {row['activity_type']}: {row['cnt']}")

    cursor.execute("SELECT COUNT(*) FROM proposal_milestones")
    print(f"\nTotal milestones: {cursor.fetchone()[0]}")

    cursor.execute("""
        SELECT milestone_type, COUNT(*) as cnt
        FROM proposal_milestones
        GROUP BY milestone_type
        ORDER BY cnt DESC
    """)
    print("\nBy type:")
    for row in cursor.fetchall():
        print(f"  {row['milestone_type']}: {row['cnt']}")

    cursor.execute("SELECT COUNT(*) FROM proposal_action_items")
    print(f"\nTotal action items: {cursor.fetchone()[0]}")
    print("(Action items will be populated by AI Story Builder)")


def main():
    conn = get_connection()

    logger.info("Starting activity tracking backfill...")

    # Backfill in order
    email_count = backfill_email_activities(conn)
    milestone_count = backfill_milestones(conn)
    transcript_count = backfill_transcript_activities(conn)

    print_summary(conn)
    conn.close()

    logger.info("Backfill complete!")


if __name__ == "__main__":
    main()
