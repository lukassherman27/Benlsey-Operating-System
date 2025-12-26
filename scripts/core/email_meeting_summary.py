#!/usr/bin/env python3
"""
Email Meeting Summary to Attendees

Sends polished meeting summaries to attendees identified in the transcript.
Looks up contact emails from the database and formats a professional email.

Usage:
    python email_meeting_summary.py TRANSCRIPT_ID
    python email_meeting_summary.py TRANSCRIPT_ID --send      # Actually send
    python email_meeting_summary.py TRANSCRIPT_ID --preview   # Preview only
    python email_meeting_summary.py --list                    # List transcripts with summaries
"""

import os
import sys
import json
import sqlite3
import smtplib
import argparse
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Add parent paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv
load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

# Email settings from environment
EMAIL_SENDER = os.getenv("EMAIL_USERNAME", "lukas@bensley.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_SERVER = os.getenv("EMAIL_SERVER", "tmail.bensley.com")
SMTP_PORT = 465
SMTP_USE_SSL = True

# Default CC for all meeting summaries (internal team)
DEFAULT_CC = ["lukas@bensley.com"]

# Bensley team domains
BENSLEY_DOMAINS = ["bensley.com"]


# =============================================================================
# DATABASE HELPERS
# =============================================================================

def get_db_connection():
    """Get database connection."""
    db_path = Path(DB_PATH)
    if not db_path.is_absolute():
        db_path = Path(__file__).parent.parent.parent / DB_PATH

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_transcript(transcript_id: int) -> Optional[Dict]:
    """Get transcript with polished summary."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            t.*,
            p.project_name,
            p.project_code,
            p.client_company
        FROM meeting_transcripts t
        LEFT JOIN proposals p ON t.proposal_id = p.proposal_id
        WHERE t.id = ?
    """, (transcript_id,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def find_contact_email(name: str, company: str = None) -> Optional[str]:
    """
    Look up email for a contact by name.
    Returns email if found with high confidence.
    """
    if not name:
        return None

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clean name for matching
    name_clean = name.strip().lower()
    name_parts = name_clean.split()

    # Try exact match first
    cursor.execute("""
        SELECT email, name, company
        FROM contacts
        WHERE LOWER(name) = ?
        AND email IS NOT NULL
    """, (name_clean,))

    row = cursor.fetchone()
    if row and row['email']:
        conn.close()
        return row['email']

    # Try partial match (first name + last name contains)
    if len(name_parts) >= 2:
        first_name = name_parts[0]
        last_name = name_parts[-1]

        cursor.execute("""
            SELECT email, name
            FROM contacts
            WHERE (LOWER(name) LIKE ? AND LOWER(name) LIKE ?)
            AND email IS NOT NULL
        """, (f"%{first_name}%", f"%{last_name}%"))

        row = cursor.fetchone()
        if row and row['email']:
            conn.close()
            return row['email']

    # Try with company context
    if company:
        company_clean = company.strip().lower()
        cursor.execute("""
            SELECT c.email, c.name, cl.company_name
            FROM contacts c
            LEFT JOIN clients cl ON c.client_id = cl.client_id
            WHERE LOWER(c.name) LIKE ?
            AND (LOWER(cl.company_name) LIKE ? OR LOWER(c.company) LIKE ?)
            AND c.email IS NOT NULL
        """, (f"%{name_parts[0]}%", f"%{company_clean}%", f"%{company_clean}%"))

        row = cursor.fetchone()
        if row and row['email']:
            conn.close()
            return row['email']

    conn.close()
    return None


def get_team_member_email(name: str) -> Optional[str]:
    """Look up Bensley team member email."""
    if not name:
        return None

    conn = get_db_connection()
    cursor = conn.cursor()

    name_clean = name.strip().lower()

    # Common Bensley team mappings
    TEAM_EMAILS = {
        "lukas": "lukas@bensley.com",
        "lukas sherman": "lukas@bensley.com",
        "bill": "bill@bensley.com",
        "bill bensley": "bill@bensley.com",
        "brian": "bsherman@bensley.com",
        "brian sherman": "bsherman@bensley.com",
        "jirachai": "jirachai@bensley.com",
    }

    # Check static mapping first
    for key, email in TEAM_EMAILS.items():
        if key in name_clean:
            conn.close()
            return email

    # Try team_members table if it exists
    try:
        cursor.execute("""
            SELECT email, name
            FROM team_members
            WHERE LOWER(name) LIKE ?
            AND email IS NOT NULL
        """, (f"%{name_clean.split()[0]}%",))

        row = cursor.fetchone()
        if row and row['email']:
            conn.close()
            return row['email']
    except:
        pass

    conn.close()
    return None


# =============================================================================
# PARTICIPANT PARSING
# =============================================================================

def parse_participants(participants_json: str) -> List[Dict]:
    """
    Parse participants from JSON string.

    Expected formats:
    - List of dicts: [{"name": "John", "role": "CEO", "type": "client"}, ...]
    - List of strings: ["John Doe", "Jane Smith", ...]
    - Comma-separated string: "John Doe, Jane Smith"
    """
    if not participants_json:
        return []

    try:
        data = json.loads(participants_json)

        if isinstance(data, list):
            if all(isinstance(p, dict) for p in data):
                return data
            elif all(isinstance(p, str) for p in data):
                return [{"name": p, "role": None, "type": "unknown"} for p in data]

        return []
    except json.JSONDecodeError:
        # Try comma-separated string
        if isinstance(participants_json, str):
            names = [n.strip() for n in participants_json.split(',')]
            return [{"name": n, "role": None, "type": "unknown"} for n in names if n]
        return []


def categorize_attendees(participants: List[Dict]) -> Tuple[List[str], List[str]]:
    """
    Categorize attendees into external (To) and internal (CC).

    Returns:
        (external_emails, internal_emails)
    """
    external_emails = []
    internal_emails = []

    for p in participants:
        name = p.get('name', '')
        ptype = p.get('type', '').lower()
        company = p.get('company', '') or p.get('role', '')

        # Skip unknown/empty
        if not name:
            continue

        email = None

        # Check if internal team member
        if ptype == 'team' or 'bensley' in company.lower():
            email = get_team_member_email(name)
            if email:
                internal_emails.append(email)
            continue

        # External: look up in contacts
        email = find_contact_email(name, company)
        if email:
            # Double-check if it's actually a Bensley email
            if any(email.endswith(f"@{d}") for d in BENSLEY_DOMAINS):
                internal_emails.append(email)
            else:
                external_emails.append(email)

    # Deduplicate
    external_emails = list(set(external_emails))
    internal_emails = list(set(internal_emails))

    return external_emails, internal_emails


# =============================================================================
# EMAIL FORMATTING
# =============================================================================

def format_email_subject(transcript: Dict) -> str:
    """Format email subject line."""
    title = transcript.get('meeting_title') or 'Meeting'
    date = transcript.get('meeting_date') or transcript.get('recorded_date', '')

    if date:
        try:
            dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
            date_str = dt.strftime('%B %d, %Y')
        except:
            date_str = date[:10] if len(date) >= 10 else date
    else:
        date_str = datetime.now().strftime('%B %d, %Y')

    project_name = transcript.get('project_name', '')
    project_code = transcript.get('project_code') or transcript.get('detected_project_code', '')

    if project_code and project_name:
        return f"Meeting Summary - {project_code} {project_name} | {date_str}"
    elif project_name:
        return f"Meeting Summary - {project_name} | {date_str}"
    else:
        return f"Meeting Summary - {title} | {date_str}"


def format_email_html(transcript: Dict) -> str:
    """Format polished summary as HTML email."""
    polished = transcript.get('polished_summary', '')

    if not polished:
        # Fallback to regular summary
        polished = transcript.get('summary', 'No summary available.')

    # Meeting metadata
    title = transcript.get('meeting_title', 'Meeting')
    date = transcript.get('meeting_date') or transcript.get('recorded_date', '')
    meeting_type = transcript.get('meeting_type', '')
    project_name = transcript.get('project_name', '')
    client = transcript.get('client_company', '')

    # Parse participants for display
    participants = parse_participants(transcript.get('participants', ''))
    participants_html = ""
    if participants:
        names = [p.get('name', '') for p in participants if p.get('name')]
        if names:
            participants_html = f"<p><strong>Attendees:</strong> {', '.join(names)}</p>"

    # Format date
    date_display = date
    if date:
        try:
            dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
            date_display = dt.strftime('%B %d, %Y')
        except:
            date_display = date[:10] if len(date) >= 10 else date

    # Convert polished summary markdown to HTML (basic)
    # Replace markdown headers with HTML
    import re
    summary_html = polished
    summary_html = re.sub(r'^### (.+)$', r'<h4 style="color: #1a73e8; margin-top: 20px;">\1</h4>', summary_html, flags=re.MULTILINE)
    summary_html = re.sub(r'^## (.+)$', r'<h3 style="color: #1a73e8; margin-top: 25px;">\1</h3>', summary_html, flags=re.MULTILINE)
    summary_html = re.sub(r'^# (.+)$', r'<h2 style="color: #333;">\1</h2>', summary_html, flags=re.MULTILINE)

    # Bold and italic
    summary_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', summary_html)
    summary_html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', summary_html)

    # Lists
    summary_html = re.sub(r'^- (.+)$', r'<li>\1</li>', summary_html, flags=re.MULTILINE)
    summary_html = re.sub(r'(<li>.*</li>\n?)+', r'<ul>\g<0></ul>', summary_html)

    # Line breaks
    summary_html = summary_html.replace('\n\n', '</p><p>')
    summary_html = f"<p>{summary_html}</p>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 25px;
                border-left: 4px solid #1a73e8;
            }}
            .header h1 {{
                margin: 0 0 10px 0;
                color: #1a73e8;
                font-size: 20px;
            }}
            .header p {{
                margin: 5px 0;
                color: #5f6368;
                font-size: 14px;
            }}
            .content {{
                padding: 0 10px;
            }}
            h2, h3, h4 {{
                color: #1a73e8;
            }}
            ul {{
                padding-left: 25px;
            }}
            li {{
                margin: 8px 0;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                color: #9e9e9e;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{title}</h1>
            {"<p><strong>Project:</strong> " + project_name + "</p>" if project_name else ""}
            {"<p><strong>Client:</strong> " + client + "</p>" if client else ""}
            <p><strong>Date:</strong> {date_display}</p>
            {"<p><strong>Type:</strong> " + meeting_type + "</p>" if meeting_type else ""}
            {participants_html}
        </div>

        <div class="content">
            {summary_html}
        </div>

        <div class="footer">
            Meeting notes prepared by BENSLEY Design Studios<br>
            Recorded: {date_display}
        </div>
    </body>
    </html>
    """


def format_email_text(transcript: Dict) -> str:
    """Format polished summary as plain text email."""
    polished = transcript.get('polished_summary', '')

    if not polished:
        polished = transcript.get('summary', 'No summary available.')

    title = transcript.get('meeting_title', 'Meeting')
    date = transcript.get('meeting_date') or transcript.get('recorded_date', '')
    project_name = transcript.get('project_name', '')

    header = f"""
{title}
{'=' * len(title)}

Project: {project_name if project_name else 'N/A'}
Date: {date[:10] if date else 'Unknown'}

---

"""

    footer = """

---

Meeting notes prepared by BENSLEY Design Studios
"""

    return header + polished + footer


# =============================================================================
# EMAIL SENDING
# =============================================================================

def send_email(
    to_emails: List[str],
    cc_emails: List[str],
    subject: str,
    html_body: str,
    text_body: str
) -> bool:
    """Send email with HTML and text versions."""

    if not EMAIL_PASSWORD:
        print("ERROR: EMAIL_PASSWORD not set. Cannot send email.")
        return False

    if not to_emails and not cc_emails:
        print("ERROR: No recipients specified.")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = ", ".join(to_emails) if to_emails else ""
        msg['Cc'] = ", ".join(cc_emails) if cc_emails else ""

        # Attach both text and HTML versions
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # All recipients for sending
        all_recipients = to_emails + cc_emails

        # Send
        if SMTP_USE_SSL:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)

        print(f"Email sent successfully to {len(all_recipients)} recipients")
        return True

    except Exception as e:
        print(f"ERROR: Failed to send email: {e}")
        return False


def mark_email_sent(transcript_id: int):
    """Mark transcript as having email sent."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Add sent timestamp to a tracking field or create suggestion
    try:
        cursor.execute("""
            UPDATE meeting_transcripts
            SET processed_date = datetime('now')
            WHERE id = ?
        """, (transcript_id,))
        conn.commit()
    except Exception as e:
        print(f"Warning: Could not update transcript: {e}")

    conn.close()


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def preview_email(transcript_id: int):
    """Preview email without sending."""
    transcript = get_transcript(transcript_id)

    if not transcript:
        print(f"ERROR: Transcript {transcript_id} not found")
        return

    if not transcript.get('polished_summary') and not transcript.get('summary'):
        print(f"ERROR: Transcript {transcript_id} has no summary")
        return

    # Parse participants
    participants = parse_participants(transcript.get('participants', ''))
    external_emails, internal_emails = categorize_attendees(participants)

    # Add default CC
    internal_emails = list(set(internal_emails + DEFAULT_CC))

    # Format email
    subject = format_email_subject(transcript)
    html_body = format_email_html(transcript)
    text_body = format_email_text(transcript)

    print("\n" + "=" * 60)
    print("EMAIL PREVIEW")
    print("=" * 60)
    print(f"\nFrom: {EMAIL_SENDER}")
    print(f"To: {', '.join(external_emails) if external_emails else '(no external recipients found)'}")
    print(f"CC: {', '.join(internal_emails)}")
    print(f"Subject: {subject}")
    print("\n" + "-" * 60)
    print("\nPARTICIPANTS DETECTED:")
    for p in participants:
        name = p.get('name', 'Unknown')
        ptype = p.get('type', 'unknown')
        role = p.get('role', '')
        email = find_contact_email(name) or get_team_member_email(name) or '(not found)'
        print(f"  - {name} [{ptype}] {role} -> {email}")
    print("\n" + "-" * 60)
    print("\nTEXT BODY:")
    print(text_body[:1000] + "..." if len(text_body) > 1000 else text_body)
    print("\n" + "=" * 60)

    return {
        'to': external_emails,
        'cc': internal_emails,
        'subject': subject,
        'html': html_body,
        'text': text_body
    }


def send_meeting_summary(transcript_id: int, force: bool = False):
    """Send meeting summary email to attendees."""
    transcript = get_transcript(transcript_id)

    if not transcript:
        print(f"ERROR: Transcript {transcript_id} not found")
        return False

    if not transcript.get('polished_summary') and not transcript.get('summary'):
        print(f"ERROR: Transcript {transcript_id} has no summary")
        return False

    # Parse participants
    participants = parse_participants(transcript.get('participants', ''))
    external_emails, internal_emails = categorize_attendees(participants)

    # Add default CC
    internal_emails = list(set(internal_emails + DEFAULT_CC))

    # Warning if no external recipients
    if not external_emails and not force:
        print("\nWARNING: No external recipient emails found.")
        print("Detected participants but could not find their emails:")
        for p in participants:
            if p.get('type', '').lower() != 'team':
                print(f"  - {p.get('name', 'Unknown')}")
        print("\nUse --force to send anyway (to internal CC only)")
        return False

    # Format and send
    subject = format_email_subject(transcript)
    html_body = format_email_html(transcript)
    text_body = format_email_text(transcript)

    print(f"\nSending to: {', '.join(external_emails) if external_emails else '(internal only)'}")
    print(f"CC: {', '.join(internal_emails)}")

    success = send_email(external_emails, internal_emails, subject, html_body, text_body)

    if success:
        mark_email_sent(transcript_id)
        print(f"\nSuccessfully sent meeting summary for transcript {transcript_id}")

    return success


def list_transcripts_with_summaries():
    """List transcripts that have polished summaries."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            meeting_title,
            meeting_date,
            detected_project_code,
            polished_summary IS NOT NULL as has_polished,
            summary IS NOT NULL as has_summary,
            participants
        FROM meeting_transcripts
        WHERE polished_summary IS NOT NULL OR summary IS NOT NULL
        ORDER BY id DESC
        LIMIT 20
    """)

    rows = cursor.fetchall()
    conn.close()

    print("\n" + "=" * 80)
    print("TRANSCRIPTS WITH SUMMARIES")
    print("=" * 80)
    print(f"{'ID':<6} {'Date':<12} {'Project':<12} {'Type':<10} {'Title':<30}")
    print("-" * 80)

    for row in rows:
        row = dict(row)
        summary_type = "Polished" if row['has_polished'] else "Basic"
        title = (row.get('meeting_title') or 'Untitled')[:28]
        date = (row.get('meeting_date') or '')[:10]
        project = row.get('detected_project_code') or '-'

        print(f"{row['id']:<6} {date:<12} {project:<12} {summary_type:<10} {title}")

    print("\n")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Email polished meeting summaries to attendees"
    )
    parser.add_argument(
        'transcript_id',
        type=int,
        nargs='?',
        help="Transcript ID to email"
    )
    parser.add_argument(
        '--send',
        action='store_true',
        help="Actually send the email (default is preview)"
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help="Preview the email without sending"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help="Send even if no external recipients found"
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help="List transcripts with summaries"
    )

    args = parser.parse_args()

    if args.list:
        list_transcripts_with_summaries()
        return

    if not args.transcript_id:
        parser.print_help()
        print("\n\nExamples:")
        print("  python email_meeting_summary.py --list")
        print("  python email_meeting_summary.py 37 --preview")
        print("  python email_meeting_summary.py 37 --send")
        return

    if args.send:
        send_meeting_summary(args.transcript_id, force=args.force)
    else:
        preview_email(args.transcript_id)


if __name__ == "__main__":
    main()
