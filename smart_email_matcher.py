#!/usr/bin/env python3
"""
smart_email_matcher.py

Intelligent email matcher for proposals
- Matches by project name (fuzzy)
- Matches by contact email
- Matches by client company name
- 90% confidence = auto-link
- Below 90% = manual review
"""

import imaplib
import email
import sqlite3
import re
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
import os
from dotenv import load_dotenv

load_dotenv()

class SmartEmailMatcher:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Email settings
        self.email_server = os.getenv('EMAIL_SERVER', 'tmail.bensley.com')
        self.email_port = int(os.getenv('EMAIL_PORT', 993))
        self.email_username = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD')

        # Stats
        self.stats = {
            'emails_scanned': 0,
            'auto_linked': 0,
            'manual_review': 0,
            'no_match': 0,
            'errors': 0
        }

        # Load proposals into memory for fast matching
        self.proposals = self.load_proposals()

    def load_proposals(self):
        """Load all proposals from database"""
        print("Loading proposals...")
        self.cursor.execute("""
            SELECT proposal_id, project_code, project_name,
                   client_company, contact_email
            FROM proposals
        """)

        proposals = []
        for row in self.cursor.fetchall():
            proposals.append({
                'proposal_id': row['proposal_id'],
                'project_code': row['project_code'],
                'project_name': row['project_name'] or '',
                'client_company': row['client_company'] or '',
                'contact_email': row['contact_email'] or '',
            })

        print(f"✓ Loaded {len(proposals)} proposals")
        return proposals

    def similarity(self, a, b):
        """Calculate similarity ratio between two strings"""
        a = a.lower().strip()
        b = b.lower().strip()
        return SequenceMatcher(None, a, b).ratio()

    def extract_email_address(self, email_str):
        """Extract email from 'Name <email@domain.com>' format"""
        if not email_str:
            return ''

        match = re.search(r'[\w\.-]+@[\w\.-]+', email_str)
        if match:
            return match.group(0).lower()
        return email_str.lower()

    def calculate_match_score(self, email_subject, email_from, email_to, proposal):
        """Calculate confidence score for email-proposal match"""
        scores = []
        reasons = []

        # 1. Project name in subject (weight: 50%)
        if proposal['project_name']:
            subject_match = self.similarity(email_subject, proposal['project_name'])
            if subject_match > 0.5:
                scores.append(subject_match * 0.5)
                reasons.append(f"Project name match in subject: {subject_match*100:.0f}%")

        # 2. Contact email match (weight: 40%)
        if proposal['contact_email']:
            contact_email = proposal['contact_email'].lower()
            from_email = self.extract_email_address(email_from)
            to_emails = [self.extract_email_address(e) for e in email_to.split(',')]

            if from_email == contact_email or contact_email in to_emails:
                scores.append(0.4)
                reasons.append(f"Contact email match: {contact_email}")

        # 3. Client company in subject or from (weight: 30%)
        if proposal['client_company']:
            company = proposal['client_company'].lower()
            subject_lower = email_subject.lower()
            from_lower = email_from.lower()

            if company in subject_lower or company in from_lower:
                scores.append(0.3)
                reasons.append(f"Client company mentioned: {proposal['client_company']}")

        # 4. Project code in subject (weight: 40%)
        if proposal['project_code']:
            code = proposal['project_code']
            if code in email_subject or code.replace('-', '') in email_subject:
                scores.append(0.4)
                reasons.append(f"Project code found: {code}")

        # Calculate total score
        if scores:
            total_score = min(sum(scores), 1.0)  # Cap at 100%
            return total_score, reasons

        return 0.0, []

    def match_email(self, email_subject, email_from, email_to):
        """Find best matching proposal for an email"""
        best_match = None
        best_score = 0.0
        best_reasons = []

        for proposal in self.proposals:
            score, reasons = self.calculate_match_score(
                email_subject, email_from, email_to, proposal
            )

            if score > best_score:
                best_score = score
                best_match = proposal
                best_reasons = reasons

        return best_match, best_score, best_reasons

    def create_tables(self):
        """Create tables for email tracking"""
        try:
            # Emails table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    email_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE,
                    subject TEXT,
                    sender_email TEXT,
                    recipient_emails TEXT,
                    date TEXT,
                    body_preview TEXT,
                    folder TEXT,
                    created_at TEXT
                )
            """)

            # Email-proposal links
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_proposal_links (
                    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id INTEGER,
                    proposal_id INTEGER,
                    confidence_score REAL,
                    match_reasons TEXT,
                    auto_linked INTEGER DEFAULT 0,
                    created_at TEXT,
                    FOREIGN KEY (email_id) REFERENCES emails(email_id),
                    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
                )
            """)

            self.conn.commit()
            print("✓ Database tables ready")
        except Exception as e:
            print(f"✗ Error creating tables: {e}")

    def connect_email(self):
        """Connect to email server"""
        print(f"\nConnecting to {self.email_server}:{self.email_port}...")

        try:
            mail = imaplib.IMAP4_SSL(self.email_server, self.email_port)
            mail.login(self.email_username, self.email_password)
            print(f"✓ Connected as {self.email_username}")
            return mail
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return None

    def parse_email_body(self, msg):
        """Extract text preview from email"""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                pass

        # Return first 200 chars as preview
        return body[:200].strip() if body else ""

    def process_folder(self, mail, folder_name, max_emails=None):
        """Process emails from a specific folder"""
        print(f"\n📂 Processing {folder_name}...")

        try:
            mail.select(folder_name, readonly=True)

            # Search for all emails
            status, messages = mail.search(None, 'ALL')

            if status != 'OK':
                print(f"   ⚠ Could not search {folder_name}")
                return

            email_ids = messages[0].split()
            total_emails = len(email_ids)

            if max_emails:
                email_ids = email_ids[-max_emails:]  # Get most recent
                print(f"   Processing last {len(email_ids)} of {total_emails} emails")
            else:
                print(f"   Found {total_emails} emails")

            for i, email_id in enumerate(email_ids, 1):
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')

                    if status != 'OK':
                        continue

                    # Parse email
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    # Extract fields
                    subject = msg.get('Subject', '')
                    from_addr = msg.get('From', '')
                    to_addr = msg.get('To', '')
                    date_str = msg.get('Date', '')
                    message_id = msg.get('Message-ID', f'no-id-{email_id}')
                    body_preview = self.parse_email_body(msg)

                    # Progress
                    if i % 10 == 0:
                        print(f"   [{i}/{len(email_ids)}] Processed...")

                    self.stats['emails_scanned'] += 1

                    # Match to proposal
                    match, score, reasons = self.match_email(subject, from_addr, to_addr)

                    if match and score > 0.3:  # Minimum 30% match
                        # Save email to database
                        self.cursor.execute("""
                            INSERT OR IGNORE INTO emails
                            (message_id, subject, sender_email, recipient_emails,
                             date, body_preview, folder, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            message_id,
                            subject,
                            from_addr,
                            to_addr,
                            date_str,
                            body_preview,
                            folder_name,
                            datetime.now().isoformat()
                        ))

                        # Get email_id
                        self.cursor.execute(
                            "SELECT email_id FROM emails WHERE message_id = ?",
                            (message_id,)
                        )
                        email_record = self.cursor.fetchone()

                        if email_record:
                            email_db_id = email_record[0]

                            # Auto-link if score >= 90%
                            if score >= 0.9:
                                self.cursor.execute("""
                                    INSERT OR IGNORE INTO email_proposal_links
                                    (email_id, proposal_id, confidence_score,
                                     match_reasons, auto_linked, created_at)
                                    VALUES (?, ?, ?, ?, 1, ?)
                                """, (
                                    email_db_id,
                                    match['proposal_id'],
                                    score,
                                    ' | '.join(reasons),
                                    datetime.now().isoformat()
                                ))
                                self.stats['auto_linked'] += 1

                                if i <= 5:  # Show first few
                                    print(f"\n   ✓ AUTO-LINKED ({score*100:.0f}%)")
                                    print(f"      Email: {subject[:50]}")
                                    print(f"      → {match['project_code']}: {match['project_name'][:40]}")
                            else:
                                # Store for manual review
                                self.cursor.execute("""
                                    INSERT OR IGNORE INTO email_proposal_links
                                    (email_id, proposal_id, confidence_score,
                                     match_reasons, auto_linked, created_at)
                                    VALUES (?, ?, ?, ?, 0, ?)
                                """, (
                                    email_db_id,
                                    match['proposal_id'],
                                    score,
                                    ' | '.join(reasons),
                                    datetime.now().isoformat()
                                ))
                                self.stats['manual_review'] += 1

                                if i <= 3:  # Show first few
                                    print(f"\n   ? REVIEW NEEDED ({score*100:.0f}%)")
                                    print(f"      Email: {subject[:50]}")
                                    print(f"      → {match['project_code']}: {match['project_name'][:40]}")
                    else:
                        self.stats['no_match'] += 1

                    self.conn.commit()

                except Exception as e:
                    print(f"   ✗ Error processing email {i}: {e}")
                    self.stats['errors'] += 1
                    continue

        except Exception as e:
            print(f"   ✗ Error accessing folder: {e}")

    def show_review_items(self):
        """Show emails needing manual review"""
        print("\n" + "="*80)
        print("📋 EMAILS NEEDING MANUAL REVIEW")
        print("="*80)

        self.cursor.execute("""
            SELECT e.subject, e.sender_email,
                   p.project_code, p.project_name,
                   l.confidence_score, l.match_reasons,
                   l.link_id
            FROM email_proposal_links l
            JOIN emails e ON l.email_id = e.email_id
            JOIN proposals p ON l.proposal_id = p.proposal_id
            WHERE l.auto_linked = 0
            ORDER BY l.confidence_score DESC
            LIMIT 20
        """)

        reviews = self.cursor.fetchall()

        if not reviews:
            print("✓ No items need review - all matches were high confidence!")
            return

        print(f"\nShowing top 20 of {len(reviews)} items:\n")

        for row in reviews:
            print(f"Email: {row['subject'][:60]}")
            print(f"From:  {row['sender_email'][:60]}")
            print(f"Match: {row['project_code']} - {row['project_name'][:40]}")
            print(f"Score: {row['confidence_score']*100:.0f}%")
            print(f"Why:   {row['match_reasons']}")
            print()

    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "="*80)
        print("✅ SMART EMAIL MATCHING COMPLETE")
        print("="*80)

        print(f"\nSummary:")
        print(f"  Emails scanned:      {self.stats['emails_scanned']}")
        print(f"  ✓ Auto-linked (≥90%): {self.stats['auto_linked']}")
        print(f"  ? Manual review:      {self.stats['manual_review']}")
        print(f"  ✗ No match:           {self.stats['no_match']}")
        print(f"  ⚠ Errors:             {self.stats['errors']}")

        # Show top matches
        print(f"\n📊 Top Matched Proposals:")
        self.cursor.execute("""
            SELECT p.project_code, p.project_name, COUNT(*) as email_count
            FROM email_proposal_links l
            JOIN proposals p ON l.proposal_id = p.proposal_id
            WHERE l.auto_linked = 1
            GROUP BY p.project_code, p.project_name
            ORDER BY email_count DESC
            LIMIT 10
        """)

        for row in self.cursor.fetchall():
            print(f"   {row['project_code']}: {row['project_name'][:40]:40} ({row['email_count']} emails)")

        print("="*80)

    def run(self, max_emails_per_folder=None):
        """Run the email matching process"""
        print("="*80)
        print("🧠 SMART EMAIL MATCHER FOR PROPOSALS")
        print("="*80)
        print(f"Database: {self.db_path}")
        print(f"Proposals loaded: {len(self.proposals)}")
        print(f"Confidence threshold: 90% (auto-link)")

        # Create tables
        self.create_tables()

        # Connect to email
        mail = self.connect_email()
        if not mail:
            return

        try:
            # Process INBOX
            self.process_folder(mail, 'INBOX', max_emails_per_folder)

            # Process Sent
            self.process_folder(mail, 'Sent', max_emails_per_folder)

            # Logout
            mail.logout()
            print("\n✓ Email connection closed")

        except Exception as e:
            print(f"\n✗ Error during processing: {e}")

        # Show results
        self.print_summary()
        self.show_review_items()

        # Close database
        self.conn.close()

def main():
    import sys

    # Get database path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "database/bensley_master.db"

    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        print(f"\nUsage: python3 smart_email_matcher.py [database_path]")
        return

    # Get max emails (optional - for testing)
    max_emails = None
    if len(sys.argv) > 2:
        try:
            max_emails = int(sys.argv[2])
            print(f"📌 Testing with last {max_emails} emails per folder")
        except:
            pass

    try:
        matcher = SmartEmailMatcher(db_path)
        matcher.run(max_emails_per_folder=max_emails)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
