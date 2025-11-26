#!/usr/bin/env python3
"""
Email Thread Builder - Task 1.2
Analyzes subjects and message_ids to build conversation threads
Groups emails by normalized subject and links to proposals
"""
import sqlite3
import re
import json
import os
from collections import defaultdict

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

class EmailThreadBuilder:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def normalize_subject(self, subject: str) -> str:
        """Remove Re:, Fwd:, FW:, etc. and normalize whitespace"""
        if not subject:
            return ""

        # Remove common prefixes (case-insensitive)
        patterns = [
            r'^(Re|RE|Fwd|FW|Fw):\s*',  # Re:, Fwd:, etc.
            r'^\[RE\]',                   # [RE]
            r'^\[External\]',             # [External]
            r'^=\?utf-8\?.*\?=',          # Encoded subjects
        ]

        normalized = subject.strip()

        # Remove prefixes iteratively
        changed = True
        while changed:
            changed = False
            for pattern in patterns:
                new_subject = re.sub(pattern, '', normalized, flags=re.IGNORECASE).strip()
                if new_subject != normalized:
                    normalized = new_subject
                    changed = True

        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def get_all_emails(self):
        """Get all emails for threading"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                email_id, message_id, subject, date, sender_email,
                category, stage
            FROM emails
            WHERE subject IS NOT NULL AND subject != ''
            ORDER BY date ASC
        """)
        return cursor.fetchall()

    def build_threads(self):
        """Build thread structure from emails based on normalized subjects"""
        emails = self.get_all_emails()
        print(f"📧 Processing {len(emails)} emails...")

        # Group by normalized subject
        subject_groups = defaultdict(list)

        for email in emails:
            normalized = self.normalize_subject(email['subject'])
            if normalized and len(normalized) > 5:  # Skip very short subjects
                subject_groups[normalized].append(dict(email))

        # Convert groups to threads
        threads = {}
        thread_counter = 1

        for subject, email_list in subject_groups.items():
            if len(email_list) >= 1:  # Include single emails as threads too (for consistency)
                # Sort by date
                email_list.sort(key=lambda e: e['date'] or '')

                threads[thread_counter] = {
                    'thread_id': thread_counter,
                    'subject_normalized': subject,
                    'emails': [e['email_id'] for e in email_list],
                    'email_count': len(email_list),
                    'first_email_date': email_list[0]['date'],
                    'last_email_date': email_list[-1]['date'],
                    'participants': list(set(e['sender_email'] for e in email_list if e['sender_email']))
                }
                thread_counter += 1

        return threads

    def link_threads_to_proposals(self, threads):
        """Link threads to proposals based on email_content linked_project_code"""
        cursor = self.conn.cursor()
        linked_count = 0

        for thread_id, thread_data in threads.items():
            email_ids = thread_data['emails']

            if not email_ids:
                continue

            # Get linked project codes from email_content
            placeholders = ','.join('?' * len(email_ids))
            cursor.execute(f"""
                SELECT linked_project_code, COUNT(*) as cnt
                FROM email_content
                WHERE email_id IN ({placeholders})
                AND linked_project_code IS NOT NULL
                GROUP BY linked_project_code
                ORDER BY cnt DESC
                LIMIT 1
            """, email_ids)

            result = cursor.fetchone()
            if result and result['linked_project_code']:
                # Get proposal_id from project_code
                project_code = result['linked_project_code'].split(':')[0].strip()  # Handle "25 BK-044: Name" format
                cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?", (project_code,))
                proposal = cursor.fetchone()
                if proposal:
                    thread_data['proposal_id'] = proposal['proposal_id']
                    linked_count += 1
            else:
                thread_data['proposal_id'] = None

        print(f"🔗 Linked {linked_count} threads to proposals")
        return threads

    def save_threads(self, threads):
        """Save threads to email_threads table and update emails.thread_id"""
        cursor = self.conn.cursor()

        # Clear existing threads
        cursor.execute("DELETE FROM email_threads")

        saved_count = 0
        for thread_id, thread_data in threads.items():
            try:
                # Insert thread record
                cursor.execute("""
                    INSERT INTO email_threads (
                        thread_id, subject_normalized, proposal_id, emails,
                        first_email_date, last_email_date, message_count, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    thread_data['thread_id'],
                    thread_data['subject_normalized'][:500],  # Limit length
                    thread_data.get('proposal_id'),
                    json.dumps(thread_data['emails']),
                    thread_data['first_email_date'],
                    thread_data['last_email_date'],
                    thread_data['email_count'],
                    'active'
                ))

                # Update emails with thread_id (use string to match schema)
                if thread_data['emails']:
                    placeholders = ','.join('?' * len(thread_data['emails']))
                    cursor.execute(f"""
                        UPDATE emails
                        SET thread_id = ?
                        WHERE email_id IN ({placeholders})
                    """, (str(thread_data['thread_id']), *thread_data['emails']))

                saved_count += 1

            except Exception as e:
                print(f"  Error saving thread {thread_id}: {e}")

        self.conn.commit()
        print(f"💾 Saved {saved_count} threads to database")

    def get_stats(self):
        """Get thread statistics"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM email_threads")
        total_threads = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM email_threads WHERE proposal_id IS NOT NULL")
        linked_threads = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM email_threads WHERE message_count > 1")
        multi_email_threads = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(message_count) FROM email_threads")
        max_emails = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(message_count) FROM email_threads")
        avg_emails = cursor.fetchone()[0] or 0

        return {
            'total_threads': total_threads,
            'linked_to_proposals': linked_threads,
            'multi_email_threads': multi_email_threads,
            'max_emails_in_thread': max_emails,
            'avg_emails_per_thread': round(avg_emails, 1)
        }

    def run(self):
        """Build and save all email threads"""
        print("=" * 60)
        print("EMAIL THREAD BUILDER - Task 1.2")
        print("=" * 60)

        print("\n📊 Building email threads...")
        threads = self.build_threads()

        print(f"   Found {len(threads)} unique conversation threads")

        # Filter to just multi-message threads for stats
        multi_threads = {k: v for k, v in threads.items() if v['email_count'] > 1}
        print(f"   {len(multi_threads)} have multiple emails (actual conversations)")

        print("\n🔗 Linking threads to proposals...")
        threads = self.link_threads_to_proposals(threads)

        print("\n💾 Saving threads to database...")
        self.save_threads(threads)

        # Show stats
        stats = self.get_stats()
        print("\n" + "=" * 60)
        print("✅ THREAD BUILDING COMPLETE")
        print("=" * 60)
        print(f"Total threads: {stats['total_threads']}")
        print(f"Linked to proposals: {stats['linked_to_proposals']}")
        print(f"Multi-email threads: {stats['multi_email_threads']}")
        print(f"Largest thread: {stats['max_emails_in_thread']} emails")
        print(f"Average emails/thread: {stats['avg_emails_per_thread']}")

        # Show sample threads
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT thread_id, subject_normalized, message_count, proposal_id
            FROM email_threads
            ORDER BY message_count DESC
            LIMIT 10
        """)

        print("\n📋 Top 10 threads by email count:")
        for row in cursor.fetchall():
            proposal_info = f" → Proposal {row['proposal_id']}" if row['proposal_id'] else ""
            print(f"   [{row['message_count']:2d} emails] {row['subject_normalized'][:50]}...{proposal_info}")

if __name__ == "__main__":
    builder = EmailThreadBuilder()
    builder.run()
