# AGENT 1: Email Content Processing

**Your Mission:** Process 3,334 emails with AI analysis and build email threads

**What You're Building:**
1. `scripts/process_email_backlog.py` - Populate email_content table with AI analysis
2. `scripts/build_email_threads.py` - Build conversation threads
3. `scripts/backfill_proposal_status.py` - Infer proposal status history from emails

**CRITICAL RULES:**
- ✅ Test on 10 emails first before processing all 3,334
- ✅ Use existing database: `/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db`
- ✅ Check OpenAI API costs (~$5-10 for full run)
- ❌ DO NOT modify existing tables
- ❌ DO NOT create new tables

---

## Task 1.1: Email Content Population Script

Create `scripts/process_email_backlog.py`:

```python
#!/usr/bin/env python3
"""
Process email backlog - populate email_content table with AI analysis
"""
import sqlite3
import os
import openai
from datetime import datetime
import json
import time
import re

DB_PATH = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db"
openai.api_key = os.getenv("OPENAI_API_KEY")

class EmailContentProcessor:
    def __init__(self, batch_size=50):
        self.batch_size = batch_size
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def get_unprocessed_emails(self, limit=None):
        """Get emails without AI-processed content"""
        query = """
            SELECT e.email_id, e.subject, e.body_full, e.sender_email, e.date
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE ec.content_id IS NULL
            AND e.body_full IS NOT NULL
            AND length(e.body_full) > 50
        """
        if limit:
            query += f" LIMIT {limit}"

        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def extract_clean_body(self, body_full):
        """Extract clean email body, remove signatures/footers"""
        # Remove email signatures
        signature_patterns = [
            r'--\s*\n.*',
            r'Sent from my .*',
            r'Get Outlook for .*',
            r'________________________________.*'
        ]

        clean_body = body_full
        for pattern in signature_patterns:
            clean_body = re.sub(pattern, '', clean_body, flags=re.DOTALL | re.IGNORECASE)

        # Remove excessive whitespace
        clean_body = re.sub(r'\n{3,}', '\n\n', clean_body)
        clean_body = clean_body.strip()

        return clean_body[:4000]  # Limit to 4000 chars for API

    def get_ai_analysis(self, email):
        """Get AI analysis using GPT-4o-mini"""
        clean_body = self.extract_clean_body(email['body_full'])

        prompt = f"""Analyze this email and return JSON with the following structure:

Email:
Subject: {email['subject']}
From: {email['sender_email']}
Date: {email['date']}
Body: {clean_body}

Return ONLY valid JSON (no markdown, no extra text) with this exact structure:
{{
  "summary": "1-2 sentence summary of email content",
  "sentiment": "positive/neutral/negative",
  "category": "proposal/contract/financial/rfi/meeting/general",
  "urgency_level": "low/medium/high/urgent",
  "action_required": true/false,
  "key_points": ["point 1", "point 2"],
  "entities": ["company names", "project codes", "person names mentioned"],
  "inferred_project_code": "25BK### or null if none detected",
  "requires_response": true/false
}}"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an email analysis assistant for a design consultancy. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            result = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            result = re.sub(r'^```json\s*', '', result)
            result = re.sub(r'\s*```$', '', result)

            return json.loads(result)

        except Exception as e:
            print(f"❌ AI analysis failed for email {email['email_id']}: {e}")
            return {
                "summary": email['subject'][:200],
                "sentiment": "neutral",
                "category": "general",
                "urgency_level": "low",
                "action_required": False,
                "key_points": [],
                "entities": [],
                "inferred_project_code": None,
                "requires_response": False
            }

    def insert_email_content(self, email_id, ai_analysis, clean_body):
        """Insert into email_content table"""
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO email_content (
                    email_id, clean_body, ai_summary, sentiment, category,
                    urgency_level, action_required, key_points, entities,
                    inferred_project_code, requires_response,
                    processed_at, processing_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_id,
                clean_body,
                ai_analysis['summary'],
                ai_analysis['sentiment'],
                ai_analysis['category'],
                ai_analysis['urgency_level'],
                1 if ai_analysis['action_required'] else 0,
                json.dumps(ai_analysis['key_points']),
                json.dumps(ai_analysis['entities']),
                ai_analysis['inferred_project_code'],
                1 if ai_analysis['requires_response'] else 0,
                datetime.now().isoformat(),
                "v1.0"
            ))

            self.conn.commit()
            return True

        except Exception as e:
            print(f"❌ Failed to insert email_content for {email_id}: {e}")
            self.conn.rollback()
            return False

    def process_batch(self, limit=None, dry_run=False):
        """Process a batch of emails"""
        emails = self.get_unprocessed_emails(limit)

        print(f"📧 Found {len(emails)} unprocessed emails")

        if dry_run:
            print("🔍 DRY RUN - No changes will be made")
            if emails:
                print(f"\nFirst email preview:")
                print(f"  ID: {emails[0]['email_id']}")
                print(f"  Subject: {emails[0]['subject']}")
                print(f"  From: {emails[0]['sender_email']}")
            return

        processed = 0
        failed = 0

        for i, email in enumerate(emails, 1):
            print(f"\n[{i}/{len(emails)}] Processing email {email['email_id']}...")
            print(f"  Subject: {email['subject'][:60]}...")

            # Get AI analysis
            ai_analysis = self.get_ai_analysis(email)
            clean_body = self.extract_clean_body(email['body_full'])

            # Insert into database
            if self.insert_email_content(email['email_id'], ai_analysis, clean_body):
                print(f"  ✅ Category: {ai_analysis['category']} | Sentiment: {ai_analysis['sentiment']}")
                processed += 1
            else:
                failed += 1

            # Rate limiting
            if i % 10 == 0:
                print(f"\n⏸️  Processed {i} emails, pausing 2 seconds...")
                time.sleep(2)

        print(f"\n{'='*60}")
        print(f"✅ Processed: {processed}")
        print(f"❌ Failed: {failed}")
        print(f"{'='*60}")

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    import sys

    # Parse arguments
    dry_run = "--dry-run" in sys.argv
    test_mode = "--test" in sys.argv

    limit = 10 if test_mode else None

    processor = EmailContentProcessor()

    try:
        processor.process_batch(limit=limit, dry_run=dry_run)
    finally:
        processor.close()
```

**Test it:**
```bash
# Test on 10 emails first (DRY RUN)
python3 scripts/process_email_backlog.py --test --dry-run

# Test on 10 emails (REAL)
python3 scripts/process_email_backlog.py --test

# Process all emails
python3 scripts/process_email_backlog.py
```

---

## Task 1.2: Email Thread Builder

Create `scripts/build_email_threads.py`:

```python
#!/usr/bin/env python3
"""
Build email conversation threads from message headers
"""
import sqlite3
from collections import defaultdict
import re

DB_PATH = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db"

class EmailThreadBuilder:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def get_all_emails(self):
        """Get all emails with headers"""
        cursor = self.conn.execute("""
            SELECT email_id, subject, message_id, in_reply_to, references, date
            FROM emails
            ORDER BY date ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def normalize_subject(self, subject):
        """Normalize subject for thread matching"""
        if not subject:
            return ""

        # Remove Re:, Fwd:, etc.
        subject = re.sub(r'^(Re|Fwd|Fw):\s*', '', subject, flags=re.IGNORECASE)
        subject = subject.strip().lower()
        return subject

    def build_threads(self):
        """Build threads using message headers and subject matching"""
        emails = self.get_all_emails()

        # Index by message_id
        by_message_id = {e['message_id']: e for e in emails if e['message_id']}

        # Build thread groups
        threads = []
        processed = set()

        for email in emails:
            if email['email_id'] in processed:
                continue

            thread_emails = [email]
            processed.add(email['email_id'])

            # Find replies by in_reply_to
            if email['message_id']:
                for other in emails:
                    if other['email_id'] in processed:
                        continue

                    if other['in_reply_to'] == email['message_id']:
                        thread_emails.append(other)
                        processed.add(other['email_id'])

            # Find by subject matching (same subject within 30 days)
            norm_subject = self.normalize_subject(email['subject'])
            if norm_subject and len(norm_subject) > 10:
                for other in emails:
                    if other['email_id'] in processed:
                        continue

                    if self.normalize_subject(other['subject']) == norm_subject:
                        thread_emails.append(other)
                        processed.add(other['email_id'])

            if len(thread_emails) > 1:
                # Sort by date
                thread_emails.sort(key=lambda x: x['date'])
                threads.append(thread_emails)

        return threads

    def insert_threads(self, threads, dry_run=False):
        """Insert threads into email_threads table"""
        if dry_run:
            print(f"🔍 DRY RUN - Would create {len(threads)} threads")
            if threads:
                print(f"\nFirst thread preview:")
                print(f"  Emails: {len(threads[0])}")
                print(f"  Subject: {threads[0][0]['subject']}")
            return

        cursor = self.conn.cursor()

        # Clear existing threads
        cursor.execute("DELETE FROM email_threads")

        for thread in threads:
            root_email = thread[0]

            # Get proposal_id if linked
            proposal_cursor = self.conn.execute("""
                SELECT proposal_id FROM email_proposal_links
                WHERE email_id = ?
                LIMIT 1
            """, (root_email['email_id'],))

            proposal_row = proposal_cursor.fetchone()
            proposal_id = proposal_row[0] if proposal_row else None

            # Create thread
            cursor.execute("""
                INSERT INTO email_threads (
                    thread_subject, root_email_id, email_count,
                    first_email_date, last_email_date, proposal_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                root_email['subject'],
                root_email['email_id'],
                len(thread),
                thread[0]['date'],
                thread[-1]['date'],
                proposal_id
            ))

            thread_id = cursor.lastrowid

            # Link all emails to thread
            for email in thread:
                cursor.execute("""
                    UPDATE emails
                    SET thread_id = ?
                    WHERE email_id = ?
                """, (thread_id, email['email_id']))

        self.conn.commit()
        print(f"✅ Created {len(threads)} threads")

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    import sys

    dry_run = "--dry-run" in sys.argv

    builder = EmailThreadBuilder()

    try:
        print("📧 Building email threads...")
        threads = builder.build_threads()
        builder.insert_threads(threads, dry_run=dry_run)
    finally:
        builder.close()
```

**Test it:**
```bash
# Dry run
python3 scripts/build_email_threads.py --dry-run

# Real run
python3 scripts/build_email_threads.py
```

---

## Task 1.3: Backfill Proposal Status History

Create `scripts/backfill_proposal_status.py`:

```python
#!/usr/bin/env python3
"""
Backfill proposal status history by inferring from email patterns
"""
import sqlite3
from datetime import datetime

DB_PATH = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db"

class StatusBackfiller:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def get_proposals_with_emails(self):
        """Get proposals that have linked emails"""
        cursor = self.conn.execute("""
            SELECT DISTINCT p.proposal_id, p.project_code, p.current_status
            FROM proposals p
            JOIN email_proposal_links epl ON p.proposal_id = epl.proposal_id
            ORDER BY p.project_code
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_status_from_email_content(self, proposal_id):
        """Infer status changes from email AI analysis"""
        cursor = self.conn.execute("""
            SELECT e.email_id, e.date, e.subject, ec.ai_summary, ec.category
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE epl.proposal_id = ?
            ORDER BY e.date ASC
        """, (proposal_id,))

        emails = [dict(row) for row in cursor.fetchall()]

        status_events = []

        for email in emails:
            inferred_status = None

            # Pattern matching on subject and summary
            text = (email['subject'] + ' ' + (email['ai_summary'] or '')).lower()

            if any(word in text for word in ['won', 'accepted', 'signed', 'approved']):
                inferred_status = 'Won'
            elif any(word in text for word in ['lost', 'declined', 'rejected']):
                inferred_status = 'Lost'
            elif any(word in text for word in ['proposal', 'quote', 'submitted']):
                inferred_status = 'Proposal Sent'
            elif any(word in text for word in ['meeting', 'call scheduled']):
                inferred_status = 'In Discussion'

            if inferred_status:
                status_events.append({
                    'date': email['date'],
                    'status': inferred_status,
                    'email_id': email['email_id']
                })

        return status_events

    def backfill_history(self, dry_run=False):
        """Backfill proposal_status_history table"""
        proposals = self.get_proposals_with_emails()

        print(f"📊 Processing {len(proposals)} proposals...")

        total_events = 0
        cursor = self.conn.cursor()

        for proposal in proposals:
            status_events = self.get_status_from_email_content(proposal['proposal_id'])

            if status_events:
                print(f"\n{proposal['project_code']}: {len(status_events)} status events")

                if not dry_run:
                    for event in status_events:
                        cursor.execute("""
                            INSERT OR IGNORE INTO proposal_status_history (
                                proposal_id, old_status, new_status,
                                changed_at, changed_by, change_reason, source_email_id
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            proposal['proposal_id'],
                            None,  # Don't know old status
                            event['status'],
                            event['date'],
                            'system',
                            'Inferred from email content',
                            event['email_id']
                        ))

                        total_events += 1

        if not dry_run:
            self.conn.commit()
            print(f"\n✅ Created {total_events} status history events")
        else:
            print(f"\n🔍 DRY RUN - Would create {total_events} events")

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    import sys

    dry_run = "--dry-run" in sys.argv

    backfiller = StatusBackfiller()

    try:
        backfiller.backfill_history(dry_run=dry_run)
    finally:
        backfiller.close()
```

**Test it:**
```bash
python3 scripts/backfill_proposal_status.py --dry-run
python3 scripts/backfill_proposal_status.py
```

---

## SUCCESS CRITERIA

When done, verify:

```bash
# Should be 3,356 (not 22!)
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM email_content"

# Should be >0
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM email_threads"

# Should be >3
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM proposal_status_history"
```

**Report back:** "Agent 1 complete. Email content: X processed, Threads: Y created, Status events: Z backfilled."
