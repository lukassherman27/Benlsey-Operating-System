#!/usr/bin/env python3
"""
Signed Contract Detector
Scans emails for signed contracts and adds them to pending review queue
"""

import sqlite3
import uuid
import re
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def detect_contract_keywords(subject, body):
    """
    Detect if email contains contract-related keywords
    Returns: (is_contract, keywords_found, contract_type, priority)
    """
    keywords = {
        'signed': ['signed', 'executed', 'finalized', 'both signed'],
        'contract': ['contract', 'agreement', 'addendum', 'amendment', 'extension'],
        'project_codes': [r'\d{2}-\d{3}', r'\d{2}\s+BK-\d{3}'],
        'urgent': ['urgent', 'asap', 'immediate', 'please review'],
    }

    text = f"{subject} {body}".lower()
    found = []
    priority = 0
    contract_type = 'new'

    # Check for signed indicator
    if any(kw in text for kw in keywords['signed']):
        found.append('signed')
        priority += 2

    # Check for contract indicator
    if any(kw in text for kw in keywords['contract']):
        found.append('contract')
        priority += 1

    # Check for project codes
    for pattern in keywords['project_codes']:
        if re.search(pattern, text):
            found.append('project_code')
            priority += 1
            break

    # Check for urgency
    if any(kw in text for kw in keywords['urgent']):
        found.append('urgent')
        priority += 2

    # Determine contract type
    if 'extension' in text or 'addendum' in text or 'amendment' in text:
        contract_type = 'extension'

    # Only flag if we have at least signed + contract OR signed + project_code
    is_contract = ('signed' in found and 'contract' in found) or \
                  ('signed' in found and 'project_code' in found)

    return is_contract, found, contract_type, priority


def extract_project_code(subject, body):
    """Extract project code from email text"""
    text = f"{subject} {body}"

    # Try 25 BK-XXX format first
    match = re.search(r'(\d{2}\s+BK-\d{3})', text)
    if match:
        return match.group(1)

    # Try 25-XXX format
    match = re.search(r'(\d{2}-\d{3})', text)
    if match:
        num = match.group(1)
        year, code = num.split('-')
        return f"{year} BK-{code}"

    return None


def extract_client_name(subject, body):
    """Attempt to extract client name"""
    text = f"{subject} {body}"

    # Common patterns
    patterns = [
        r'(?:for|from|client:?)\s+([A-Z][a-zA-Z\s&,\.]+(?:Ltd|LLC|Inc|Co|Company))',
        r'([A-Z][a-zA-Z\s&,\.]+(?:Ltd|LLC|Inc|Co|Company))',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            if len(name) > 10 and len(name) < 100:  # Reasonable length
                return name

    return None


def scan_emails_for_contracts():
    """Scan recent emails for signed contracts"""
    conn = get_connection()
    cursor = conn.cursor()

    # Get emails from last 90 days that haven't been checked for contracts
    cursor.execute("""
        SELECT
            e.email_id,
            e.subject,
            e.body_preview,
            e.sender,
            e.received_date,
            e.has_attachments
        FROM emails e
        LEFT JOIN pending_contract_reviews pcr ON e.email_id = pcr.email_id
        WHERE pcr.email_id IS NULL
          AND e.received_date >= date('now', '-90 days')
          AND e.has_attachments = 1
        ORDER BY e.received_date DESC
        LIMIT 500
    """)

    emails = [dict(row) for row in cursor.fetchall()]

    print(f"\n📧 Scanning {len(emails)} emails with attachments...")

    detected = []

    for email in emails:
        subject = email['subject'] or ''
        body = email['body_preview'] or ''

        is_contract, keywords, contract_type, priority = detect_contract_keywords(subject, body)

        if is_contract:
            project_code = extract_project_code(subject, body)
            client_name = extract_client_name(subject, body)

            detected.append({
                'email_id': email['email_id'],
                'subject': subject[:100],
                'project_code': project_code,
                'client_name': client_name,
                'contract_type': contract_type,
                'keywords': keywords,
                'priority': priority,
                'received_date': email['received_date']
            })

    print(f"✅ Found {len(detected)} potential contracts\n")

    # Add to pending reviews
    for contract in detected:
        review_id = f"CR-{uuid.uuid4().hex[:12].upper()}"

        cursor.execute("""
            INSERT INTO pending_contract_reviews (
                review_id,
                email_id,
                project_code,
                detected_date,
                status,
                contract_type,
                client_name,
                detected_keywords,
                priority,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            review_id,
            contract['email_id'],
            contract['project_code'],
            contract['received_date'],
            'pending',
            contract['contract_type'],
            contract['client_name'],
            json.dumps(contract['keywords']),
            contract['priority'],
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        print(f"📝 {review_id}: {contract['subject']}")
        if contract['project_code']:
            print(f"   Project: {contract['project_code']}")
        if contract['client_name']:
            print(f"   Client: {contract['client_name']}")
        print(f"   Type: {contract['contract_type']} | Priority: {contract['priority']}")
        print(f"   Keywords: {', '.join(contract['keywords'])}\n")

    conn.commit()
    conn.close()

    return detected


def show_pending_contracts():
    """Show all pending contract reviews"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            pcr.review_id,
            pcr.project_code,
            pcr.client_name,
            pcr.contract_type,
            pcr.priority,
            pcr.detected_date,
            pcr.status,
            e.subject
        FROM pending_contract_reviews pcr
        JOIN emails e ON pcr.email_id = e.email_id
        WHERE pcr.status = 'pending'
        ORDER BY pcr.priority DESC, pcr.detected_date DESC
    """)

    pending = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not pending:
        print("\n✅ No pending contracts to review!")
        return

    print("\n" + "="*100)
    print(f" PENDING CONTRACT REVIEWS ({len(pending)}) ".center(100, "="))
    print("="*100)
    print(f"{'ID':<15} {'Project':<15} {'Client':<30} {'Type':<12} {'Priority':<8} {'Date':<12}")
    print("-"*100)

    for p in pending:
        print(f"{p['review_id']:<15} {p['project_code'] or 'Unknown':<15} "
              f"{(p['client_name'] or 'Unknown')[:28]:<30} "
              f"{p['contract_type']:<12} {p['priority']:<8} {p['detected_date'][:10]:<12}")

    print("="*100 + "\n")


def main():
    print("\n" + "="*80)
    print(" SIGNED CONTRACT DETECTOR ".center(80, "="))
    print("="*80)

    detected = scan_emails_for_contracts()

    print("\n" + "="*80)
    print(f"✅ Detection complete! Found {len(detected)} new contracts")
    print("="*80)

    show_pending_contracts()

    print("\n📌 Next Steps:")
    print("   1. Review pending contracts in the dashboard")
    print("   2. For each contract, I'll help extract the data")
    print("   3. Confirm and import to database")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
