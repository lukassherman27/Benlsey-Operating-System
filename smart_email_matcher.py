#!/usr/bin/env python3
"""
smart_email_matcher.py

Intelligent email matcher with contact learning
- Matches by project name (fuzzy)
- Learns from contact-project relationships
- Filters @bensley.com as internal (not clients)
- Multi-project contact support
- 70% confidence = auto-link (lowered from 90%)
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
            'errors': 0,
            'contacts_learned': 0
        }

        # Initialize
        self.run_migration()
        self.proposals = self.load_proposals()
        self.contact_cache = self.load_contact_relationships()

    def run_migration(self):
        """Run contact learning migration"""
        migration_file = Path(__file__).parent / "database/migrations/004_smart_contact_learning.sql"

        if migration_file.exists():
            print("Running contact learning migration...")
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
                self.conn.executescript(migration_sql)
                self.conn.commit()
            print("✓ Migration complete")

    def load_proposals(self):
        """Load all proposals"""
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

    def load_contact_relationships(self):
        """Load learned contact-project relationships"""
        print("Loading contact relationships...")

        self.cursor.execute("""
            SELECT
                c.email_address,
                c.full_name,
                c.is_internal,
                l.proposal_id,
                l.email_count,
                l.confidence_score
            FROM project_contact_links l
            JOIN project_contacts c ON l.contact_id = c.contact_id
        """)

        # Build cache: {email: [{proposal_id, count, score}, ...]}
        cache = {}
        for row in self.cursor.fetchall():
            email = row['email_address']
            if email not in cache:
                cache[email] = {
                    'name': row['full_name'],
                    'internal': row['is_internal'],
                    'projects': []
                }
            cache[email]['projects'].append({
                'proposal_id': row['proposal_id'],
                'email_count': row['email_count'],
                'score': row['confidence_score']
            })

        print(f"✓ Loaded {len(cache)} known contacts")
        return cache

    def is_internal_email(self, email_addr):
        """Check if email is internal (@bensley.com)"""
        return '@bensley.com' in email_addr.lower()

    def extract_name_from_email(self, email_str):
        """Extract name from 'Name <email@domain.com>' format"""
        if not email_str:
            return ''

        # Try to extract name before <email>
        match = re.match(r'^"?([^<"]+)"?\s*<', email_str)
        if match:
            return match.group(1).strip()

        return ''

    def extract_email_address(self, email_str):
        """Extract email from 'Name <email@domain.com>' format"""
        if not email_str:
            return ''

        match = re.search(r'[\w\.-]+@[\w\.-]+', email_str)
        if match:
            return match.group(0).lower()
        return email_str.lower()

    def similarity(self, a, b):
        """Calculate similarity ratio between two strings"""
        a = a.lower().strip()
        b = b.lower().strip()
        return SequenceMatcher(None, a, b).ratio()

    def calculate_match_score(self, email_subject, email_from, email_to, proposal):
        """Calculate confidence score using learned relationships"""
        scores = []
        reasons = []

        from_email = self.extract_email_address(email_from)

        # Skip internal emails for contact matching
        if self.is_internal_email(from_email):
            reasons.append("Internal email (not counted as contact)")

        # 1. Check learned contact relationships (weight: 60%)
        if from_email in self.contact_cache and not self.is_internal_email(from_email):
            contact = self.contact_cache[from_email]
            for proj in contact['projects']:
                if proj['proposal_id'] == proposal['proposal_id']:
                    weight = min(proj['email_count'] / 10.0, 0.6)  # Max 60%, scales with email count
                    scores.append(weight)
                    reasons.append(f"Known contact: {contact['name']} ({proj['email_count']} emails)")
                    break

        # 2. Project name in subject (weight: 40%)
        if proposal['project_name']:
            subject_match = self.similarity(email_subject, proposal['project_name'])
            if subject_match > 0.5:
                scores.append(subject_match * 0.4)
                reasons.append(f"Project name match: {subject_match*100:.0f}%")

        # 3. Client company mention (weight: 30%)
        if proposal['client_company']:
            company = proposal['client_company'].lower()
            if company in email_subject.lower() or company in email_from.lower():
                scores.append(0.3)
                reasons.append(f"Client company: {proposal['client_company']}")

        # 4. Project code in subject (weight: 50%)
        if proposal['project_code']:
            code = proposal['project_code']
            if code in email_subject or code.replace('-', '') in email_subject:
                scores.append(0.5)
                reasons.append(f"Project code: {code}")

        # Calculate total
        if scores:
            total_score = min(sum(scores), 1.0)
            return total_score, reasons

        return 0.0, []

    def learn_contact(self, email_from, proposal_id):
        """Learn or update contact-project relationship"""
        email_addr = self.extract_email_address(email_from)
        full_name = self.extract_name_from_email(email_from)

        if not email_addr:
            return

        is_internal = 1 if self.is_internal_email(email_addr) else 0

        try:
            # Get or create contact
            self.cursor.execute("""
                INSERT OR IGNORE INTO project_contacts
                (email_address, full_name, is_internal, first_seen, total_emails)
                VALUES (?, ?, ?, datetime('now'), 0)
            """, (email_addr, full_name, is_internal))

            self.cursor.execute("""
                UPDATE project_contacts
                SET full_name = COALESCE(NULLIF(full_name, ''), ?),
                    last_contact = datetime('now'),
                    total_emails = total_emails + 1,
                    updated_at = datetime('now')
                WHERE email_address = ?
            """, (full_name, email_addr))

            # Get contact_id
            self.cursor.execute(
                "SELECT contact_id FROM project_contacts WHERE email_address = ?",
                (email_addr,)
            )
            contact_id = self.cursor.fetchone()['contact_id']

            # Update or create link
            self.cursor.execute("""
                INSERT INTO project_contact_links
                (proposal_id, contact_id, email_count, last_activity, confidence_score)
                VALUES (?, ?, 1, datetime('now'), 0.5)
                ON CONFLICT(proposal_id, contact_id) DO UPDATE SET
                    email_count = email_count + 1,
                    last_activity = datetime('now'),
                    confidence_score = MIN(1.0, confidence_score + 0.1)
            """, (proposal_id, contact_id))

            self.conn.commit()
            self.stats['contacts_learned'] += 1

        except Exception as e:
            print(f"   ⚠ Error learning contact: {e}")

    def match_email(self, email_subject, email_from, email_to):
        """Find best matching proposal"""
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
        """Create emails tables"""
        try:
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
            print("✓ Email tables ready")
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

        return body[:200].strip() if body else ""

    def process_folder(self, mail, folder_name, max_emails=None):
        """Process emails from folder"""
        print(f"\n📂 Processing {folder_name}...")

        try:
            mail.select(folder_name, readonly=True)
            status, messages = mail.search(None, 'ALL')

            if status != 'OK':
                print(f"   ⚠ Could not search {folder_name}")
                return

            email_ids = messages[0].split()
            total_emails = len(email_ids)

            if max_emails:
                email_ids = email_ids[-max_emails:]
                print(f"   Processing last {len(email_ids)} of {total_emails} emails")
            else:
                print(f"   Found {total_emails} emails")

            for i, email_id in enumerate(email_ids, 1):
                try:
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    if status != 'OK':
                        continue

                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    subject = msg.get('Subject', '')
                    from_addr = msg.get('From', '')
                    to_addr = msg.get('To', '')
                    date_str = msg.get('Date', '')
                    message_id = msg.get('Message-ID', f'no-id-{email_id}')
                    body_preview = self.parse_email_body(msg)

                    if i % 10 == 0:
                        print(f"   [{i}/{len(email_ids)}] Processed...")

                    self.stats['emails_scanned'] += 1

                    # Match to proposal
                    match, score, reasons = self.match_email(subject, from_addr, to_addr)

                    if match and score > 0.3:
                        # Save email
                        self.cursor.execute("""
                            INSERT OR IGNORE INTO emails
                            (message_id, subject, sender_email, recipient_emails,
                             date, body_preview, folder, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            message_id, subject, from_addr, to_addr,
                            date_str, body_preview, folder_name,
                            datetime.now().isoformat()
                        ))

                        self.cursor.execute(
                            "SELECT email_id FROM emails WHERE message_id = ?",
                            (message_id,)
                        )
                        email_record = self.cursor.fetchone()

                        if email_record:
                            email_db_id = email_record[0]

                            # Auto-link if score >= 70%
                            if score >= 0.7:
                                self.cursor.execute("""
                                    INSERT OR IGNORE INTO email_proposal_links
                                    (email_id, proposal_id, confidence_score,
                                     match_reasons, auto_linked, created_at)
                                    VALUES (?, ?, ?, ?, 1, ?)
                                """, (
                                    email_db_id, match['proposal_id'], score,
                                    ' | '.join(reasons), datetime.now().isoformat()
                                ))

                                # Learn contact relationship
                                self.learn_contact(from_addr, match['proposal_id'])

                                self.stats['auto_linked'] += 1

                                if i <= 5:
                                    print(f"\n   ✓ AUTO-LINKED ({score*100:.0f}%)")
                                    print(f"      {subject[:50]}")
                                    print(f"      → {match['project_code']}")
                            else:
                                # Manual review
                                self.cursor.execute("""
                                    INSERT OR IGNORE INTO email_proposal_links
                                    (email_id, proposal_id, confidence_score,
                                     match_reasons, auto_linked, created_at)
                                    VALUES (?, ?, ?, ?, 0, ?)
                                """, (
                                    email_db_id, match['proposal_id'], score,
                                    ' | '.join(reasons), datetime.now().isoformat()
                                ))
                                self.stats['manual_review'] += 1
                    else:
                        self.stats['no_match'] += 1

                    self.conn.commit()

                except Exception as e:
                    print(f"   ✗ Error: {e}")
                    self.stats['errors'] += 1

        except Exception as e:
            print(f"   ✗ Folder error: {e}")

    def print_summary(self):
        """Print summary"""
        print("\n" + "="*80)
        print("✅ SMART EMAIL MATCHING COMPLETE")
        print("="*80)

        print(f"\nSummary:")
        print(f"  Emails scanned:       {self.stats['emails_scanned']}")
        print(f"  ✓ Auto-linked (≥70%): {self.stats['auto_linked']}")
        print(f"  ? Manual review:      {self.stats['manual_review']}")
        print(f"  ✗ No match:           {self.stats['no_match']}")
        print(f"  📚 Contacts learned:  {self.stats['contacts_learned']}")
        print(f"  ⚠ Errors:             {self.stats['errors']}")

        # Top matches
        print(f"\n📊 Top Matched Proposals:")
        self.cursor.execute("""
            SELECT p.project_code, p.project_name, COUNT(*) as email_count
            FROM email_proposal_links l
            JOIN proposals p ON l.proposal_id = p.proposal_id
            WHERE l.auto_linked = 1
            GROUP BY p.project_code
            ORDER BY email_count DESC
            LIMIT 10
        """)

        for row in self.cursor.fetchall():
            print(f"   {row['project_code']}: {row['project_name'][:40]:40} ({row['email_count']} emails)")

        print("="*80)

    def run(self, max_emails_per_folder=None):
        """Run matching process"""
        print("="*80)
        print("🧠 SMART EMAIL MATCHER WITH CONTACT LEARNING")
        print("="*80)
        print(f"Database: {self.db_path}")
        print(f"Proposals: {len(self.proposals)}")
        print(f"Known contacts: {len(self.contact_cache)}")
        print(f"Auto-link threshold: 70%")

        self.create_tables()
        mail = self.connect_email()
        if not mail:
            return

        try:
            self.process_folder(mail, 'INBOX', max_emails_per_folder)
            self.process_folder(mail, 'Sent', max_emails_per_folder)
            mail.logout()
            print("\n✓ Email connection closed")
        except Exception as e:
            print(f"\n✗ Error: {e}")

        self.print_summary()
        self.conn.close()

def main():
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "database/bensley_master.db"
    max_emails = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        return

    if max_emails:
        print(f"📌 Testing with last {max_emails} emails per folder\n")

    try:
        matcher = SmartEmailMatcher(db_path)
        matcher.run(max_emails_per_folder=max_emails)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
