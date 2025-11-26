# 📧 EMAIL-PROPOSAL INTEGRATION BUILD PLAN

**Created:** 2025-11-26
**Status:** APPROVED - READY FOR EXECUTION
**Duration:** 48-64 hours (6-8 days with parallel execution)

---

## 🎯 MISSION

Transform the email-proposal system from "data exists but not usable" to "fully integrated with UI, searchable, and intelligent."

### Current Gap
- **3,356 emails** imported but only **22** have AI-processed content (99% gap!)
- Email threads table empty (0 records)
- Proposal status history barely populated (3 records)
- Frontend exists but limited - no thread view, no search, no bulk operations

### Success Criteria
✅ All 3,356 emails have AI-processed content (clean_body, summary, sentiment, action items)
✅ Email threads built and linked to proposals
✅ Complete email history visible on proposal pages
✅ Global email search with advanced filters
✅ Bulk operations (categorize 50 emails at once)
✅ Thread view shows conversation flow

---

## 📋 AGENT ASSIGNMENTS

| Agent | Role | Tasks | Time | Dependencies |
|-------|------|-------|------|--------------|
| **Agent 1** | Backend/Data Processing | Email content population, Thread builder, Status history | 16-20h | None (START FIRST) |
| **Agent 2** | Database/Schema | Schema migration, Indexes, Views | 4-6h | None (parallel with Agent 1) |
| **Agent 3** | Backend API Development | 5 API endpoints for email features | 10-14h | Agent 1 must complete |
| **Agent 4** | Frontend Components | 4 reusable email UI components | 12-16h | Agent 3 must have APIs ready |
| **Agent 5** | Frontend Integration | Wire components into proposal pages, search page | 10-14h | Agent 4 must complete |

---

## 🔧 PHASE 1: FOUNDATION (CRITICAL - DO FIRST)

### Agent 1: Backend Data Processing

#### Task 1.1: Email Content Population Script ⭐ CRITICAL PATH
**File:** `scripts/process_email_backlog.py`
**Purpose:** Process 3,334 emails lacking AI content (99% of database)

**Specifications:**
```python
#!/usr/bin/env python3
"""
Email Content Population Script
Batch process emails to extract body content and AI insights
"""
import sqlite3
import os
from openai import OpenAI

DB_PATH = "database/bensley_master.db"
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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

        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def extract_clean_body(self, body_full):
        """Extract clean email body, remove signatures/quotes"""
        # Split on common quote markers
        lines = body_full.split('\n')
        clean_lines = []

        for line in lines:
            # Stop at quote markers
            if line.strip().startswith('>') or \
               line.strip().startswith('On ') and 'wrote:' in line or \
               '-----Original Message-----' in line:
                break
            clean_lines.append(line)

        return '\n'.join(clean_lines).strip()

    def get_ai_analysis(self, email):
        """Get AI analysis: summary, sentiment, category, action items"""
        prompt = f"""Analyze this email:

Subject: {email['subject']}
From: {email['sender_email']}
Body: {self.extract_clean_body(email['body_full'])}

Return JSON with:
- summary (1-2 sentences)
- sentiment (positive/neutral/negative)
- category (proposal/contract/financial/rfi/meeting/general)
- subcategory (specific type within category)
- urgency_level (low/medium/high/urgent)
- action_required (true/false)
- key_points (array of 2-3 bullet points)
- entities (array of people, companies, projects mentioned)
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an email analysis assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"AI analysis error for email {email['email_id']}: {e}")
            return None

    def save_email_content(self, email_id, clean_body, ai_analysis_json):
        """Save processed content to email_content table"""
        import json

        try:
            analysis = json.loads(ai_analysis_json)
        except:
            analysis = {}

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO email_content (
                email_id, clean_body, ai_summary, sentiment,
                category, subcategory, urgency_level, action_required,
                key_points, entities, processing_model, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            email_id,
            clean_body,
            analysis.get('summary', ''),
            analysis.get('sentiment', 'neutral'),
            analysis.get('category', 'general'),
            analysis.get('subcategory', ''),
            analysis.get('urgency_level', 'low'),
            analysis.get('action_required', False),
            json.dumps(analysis.get('key_points', [])),
            json.dumps(analysis.get('entities', [])),
            'gpt-4o-mini'
        ))
        self.conn.commit()

    def process_batch(self):
        """Process emails in batches"""
        unprocessed = self.get_unprocessed_emails(limit=self.batch_size)

        print(f"Processing batch of {len(unprocessed)} emails...")

        for i, email in enumerate(unprocessed, 1):
            print(f"  [{i}/{len(unprocessed)}] Email {email['email_id']}: {email['subject'][:50]}...")

            clean_body = self.extract_clean_body(email['body_full'])
            ai_analysis = self.get_ai_analysis(email)

            if ai_analysis:
                self.save_email_content(email['email_id'], clean_body, ai_analysis)
                print(f"    ✓ Processed and saved")
            else:
                print(f"    ✗ AI analysis failed")

        return len(unprocessed)

    def run_full_processing(self):
        """Run processing until all emails are done"""
        total_processed = 0

        while True:
            count = self.process_batch()
            total_processed += count

            if count < self.batch_size:
                break

            print(f"\n--- Total processed so far: {total_processed} ---\n")

        print(f"\n✓ COMPLETE! Processed {total_processed} emails total")

if __name__ == "__main__":
    processor = EmailContentProcessor(batch_size=50)
    processor.run_full_processing()
```

**Runtime Estimate:** 2-3 hours for 3,334 emails @ ~3 seconds/email
**Cost Estimate:** ~$10-15 in OpenAI API calls (GPT-4o-mini)

**Testing:**
```bash
# Test on 10 emails first
python3 scripts/process_email_backlog.py --batch-size 10 --dry-run

# Run full processing
python3 scripts/process_email_backlog.py
```

---

#### Task 1.2: Email Thread Builder Script
**File:** `scripts/build_email_threads.py`
**Purpose:** Group emails into conversation threads, populate email_threads table

**Specifications:**
```python
#!/usr/bin/env python3
"""
Email Thread Builder
Analyzes message_id and in_reply_to headers to build conversation threads
"""
import sqlite3
import re

DB_PATH = "database/bensley_master.db"

class EmailThreadBuilder:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def normalize_subject(self, subject):
        """Remove Re:, Fwd:, etc. from subject"""
        if not subject:
            return ""

        # Remove prefixes
        normalized = re.sub(r'^(Re|Fwd|Fw):\s*', '', subject, flags=re.IGNORECASE)
        normalized = normalized.strip()

        return normalized

    def get_all_emails(self):
        """Get all emails with message_id and in_reply_to"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT email_id, message_id, in_reply_to, subject, date, sender_email
            FROM emails
            ORDER BY date ASC
        """)
        return cursor.fetchall()

    def build_threads(self):
        """Build thread structure from emails"""
        emails = self.get_all_emails()

        # Map message_id → email_id
        message_map = {}
        for email in emails:
            if email['message_id']:
                message_map[email['message_id']] = email['email_id']

        # Build threads
        threads = {}  # thread_id → {subject, email_ids[], proposal_id}
        email_to_thread = {}  # email_id → thread_id
        thread_counter = 1

        for email in emails:
            # Check if this email is a reply
            if email['in_reply_to'] and email['in_reply_to'] in message_map:
                parent_email_id = message_map[email['in_reply_to']]

                # Find which thread the parent belongs to
                if parent_email_id in email_to_thread:
                    thread_id = email_to_thread[parent_email_id]
                    threads[thread_id]['email_ids'].append(email['email_id'])
                    email_to_thread[email['email_id']] = thread_id
                    continue

            # Not a reply or parent not found - check subject match
            normalized_subject = self.normalize_subject(email['subject'])

            # Look for existing thread with same subject
            found_thread = False
            for thread_id, thread_data in threads.items():
                if thread_data['subject'] == normalized_subject:
                    thread_data['email_ids'].append(email['email_id'])
                    email_to_thread[email['email_id']] = thread_id
                    found_thread = True
                    break

            # Create new thread if no match
            if not found_thread:
                thread_id = thread_counter
                thread_counter += 1

                threads[thread_id] = {
                    'subject': normalized_subject,
                    'email_ids': [email['email_id']],
                    'proposal_id': None  # Will determine later
                }
                email_to_thread[email['email_id']] = thread_id

        return threads

    def link_threads_to_proposals(self, threads):
        """Link threads to proposals based on member emails"""
        cursor = self.conn.cursor()

        for thread_id, thread_data in threads.items():
            # Check if any email in thread is linked to a proposal
            email_ids_str = ','.join(str(eid) for eid in thread_data['email_ids'])

            cursor.execute(f"""
                SELECT proposal_id, COUNT(*) as link_count
                FROM email_proposal_links
                WHERE email_id IN ({email_ids_str})
                GROUP BY proposal_id
                ORDER BY link_count DESC
                LIMIT 1
            """)

            result = cursor.fetchone()
            if result:
                thread_data['proposal_id'] = result['proposal_id']

    def save_threads(self, threads):
        """Save threads to email_threads table"""
        cursor = self.conn.cursor()

        # Clear existing threads
        cursor.execute("DELETE FROM email_threads")

        for thread_id, thread_data in threads.items():
            # Insert thread record
            cursor.execute("""
                INSERT INTO email_threads (
                    thread_id, subject_normalized, email_count,
                    proposal_id, first_email_date, last_email_date
                )
                SELECT
                    ? as thread_id,
                    ? as subject_normalized,
                    ? as email_count,
                    ? as proposal_id,
                    MIN(date) as first_email_date,
                    MAX(date) as last_email_date
                FROM emails
                WHERE email_id IN ({})
            """.format(','.join('?' * len(thread_data['email_ids']))),
                (thread_id, thread_data['subject'], len(thread_data['email_ids']),
                 thread_data['proposal_id'], *thread_data['email_ids'])
            )

            # Update emails with thread_id
            cursor.execute(f"""
                UPDATE emails
                SET thread_id = ?
                WHERE email_id IN ({','.join('?' * len(thread_data['email_ids']))})
            """, (thread_id, *thread_data['email_ids']))

        self.conn.commit()
        print(f"✓ Saved {len(threads)} threads to database")

    def run(self):
        """Build and save all email threads"""
        print("Building email threads...")
        threads = self.build_threads()

        print(f"Found {len(threads)} conversation threads")

        print("Linking threads to proposals...")
        self.link_threads_to_proposals(threads)

        print("Saving threads to database...")
        self.save_threads(threads)

        print("\n✓ Thread building complete!")

if __name__ == "__main__":
    builder = EmailThreadBuilder()
    builder.run()
```

**Testing:**
```bash
python3 scripts/build_email_threads.py

# Verify results
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM email_threads"
sqlite3 database/bensley_master.db "SELECT * FROM email_threads ORDER BY email_count DESC LIMIT 10"
```

---

#### Task 1.3: Proposal Status History Backfill
**File:** `scripts/backfill_proposal_status_history.py`
**Purpose:** Create historical status change records from email patterns and timestamps

**Specifications:**
```python
#!/usr/bin/env python3
"""
Proposal Status History Backfill
Infer status changes from proposal data and email patterns
"""
import sqlite3
from datetime import datetime

DB_PATH = "database/bensley_master.db"

class StatusHistoryBackfill:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def get_proposals(self):
        """Get all proposals with key dates"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                proposal_id, project_code, project_name,
                first_contact_date, proposal_sent_date, contract_signed_date,
                current_status, status_changed_at
            FROM proposals
            WHERE first_contact_date IS NOT NULL
            ORDER BY first_contact_date ASC
        """)
        return cursor.fetchall()

    def infer_status_changes(self, proposal):
        """Infer historical status changes from dates"""
        changes = []

        # First Contact
        if proposal['first_contact_date']:
            changes.append({
                'date': proposal['first_contact_date'],
                'old_status': None,
                'new_status': 'First Contact',
                'source': 'inferred',
                'notes': 'Initial contact date from proposal data'
            })

        # Proposal Sent
        if proposal['proposal_sent_date']:
            changes.append({
                'date': proposal['proposal_sent_date'],
                'old_status': 'First Contact',
                'new_status': 'Proposal Sent',
                'source': 'inferred',
                'notes': 'Proposal sent date from proposal data'
            })

        # Contract Signed
        if proposal['contract_signed_date']:
            changes.append({
                'date': proposal['contract_signed_date'],
                'old_status': 'Proposal Sent',
                'new_status': 'Contract Signed',
                'source': 'inferred',
                'notes': 'Contract signed date from proposal data'
            })

        # Current Status
        if proposal['status_changed_at'] and proposal['current_status']:
            changes.append({
                'date': proposal['status_changed_at'],
                'old_status': changes[-1]['new_status'] if changes else None,
                'new_status': proposal['current_status'],
                'source': 'current',
                'notes': 'Current status from proposal data'
            })

        return changes

    def save_history(self, proposal_id, changes):
        """Save status changes to proposal_status_history"""
        cursor = self.conn.cursor()

        for change in changes:
            cursor.execute("""
                INSERT INTO proposal_status_history (
                    proposal_id, old_status, new_status,
                    changed_at, source, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                proposal_id,
                change['old_status'],
                change['new_status'],
                change['date'],
                change['source'],
                change['notes']
            ))

        self.conn.commit()

    def run(self):
        """Backfill all proposal status history"""
        proposals = self.get_proposals()

        print(f"Processing {len(proposals)} proposals...")

        total_changes = 0
        for proposal in proposals:
            changes = self.infer_status_changes(proposal)

            if changes:
                self.save_history(proposal['proposal_id'], changes)
                total_changes += len(changes)
                print(f"  ✓ {proposal['project_code']}: {len(changes)} status changes")

        print(f"\n✓ Backfilled {total_changes} status changes for {len(proposals)} proposals")

if __name__ == "__main__":
    backfill = StatusHistoryBackfill()
    backfill.run()
```

---

### Agent 2: Database Schema Engineer

#### Task 2.1: Schema Unification Migration
**File:** `database/migrations/026_email_proposal_unification.sql`
**Purpose:** Fix project_code vs proposal_id inconsistencies, add indexes

```sql
-- Email-Proposal Schema Unification Migration

-- Add proposal_id mapping to email_project_links if missing
ALTER TABLE email_project_links ADD COLUMN proposal_id INTEGER;

-- Update proposal_id based on project_code
UPDATE email_project_links
SET proposal_id = (
    SELECT proposal_id
    FROM proposals
    WHERE proposals.project_code = email_project_links.project_code
)
WHERE proposal_id IS NULL;

-- Add indexes for email queries (performance)
CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date DESC);
CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category);
CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender_email);
CREATE INDEX IF NOT EXISTS idx_emails_thread ON emails(thread_id);

CREATE INDEX IF NOT EXISTS idx_email_content_category ON email_content(category);
CREATE INDEX IF NOT EXISTS idx_email_content_action ON email_content(action_required);

CREATE INDEX IF NOT EXISTS idx_email_proposal_links_proposal ON email_proposal_links(proposal_id);
CREATE INDEX IF NOT EXISTS idx_email_proposal_links_email ON email_proposal_links(email_id);
CREATE INDEX IF NOT EXISTS idx_email_proposal_links_confidence ON email_proposal_links(confidence_score DESC);

CREATE INDEX IF NOT EXISTS idx_email_threads_proposal ON email_threads(proposal_id);

-- Create view for easy email-proposal joins
CREATE VIEW IF NOT EXISTS v_proposal_emails AS
SELECT
    e.email_id,
    e.subject,
    e.sender_email,
    e.date,
    e.category,
    e.thread_id,
    ec.ai_summary,
    ec.sentiment,
    ec.action_required,
    ec.urgency_level,
    p.proposal_id,
    p.project_code,
    p.project_name,
    epl.confidence_score,
    epl.auto_linked,
    epl.link_method
FROM emails e
LEFT JOIN email_content ec ON e.email_id = ec.email_id
LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
WHERE p.proposal_id IS NOT NULL;

-- Full-text search optimization
-- (emails_fts already exists, verify it's up to date)
DELETE FROM emails_fts;
INSERT INTO emails_fts(email_id, subject, body_full, sender_email)
SELECT email_id, subject, body_full, sender_email
FROM emails;
```

**Testing:**
```bash
sqlite3 database/bensley_master.db < database/migrations/026_email_proposal_unification.sql

# Verify indexes
sqlite3 database/bensley_master.db ".indexes emails"

# Test view
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM v_proposal_emails"
```

---

## 🔌 PHASE 2: BACKEND APIs (AFTER PHASE 1 COMPLETES)

### Agent 3: API Development

⚠️ **DEPENDENCY:** Wait for Agent 1 to complete email content population before starting these tasks.

#### Task 3.1: Enhanced Email Detail Endpoint
**File:** `backend/api/main.py` (add endpoint)
**Route:** `GET /api/emails/{email_id}/detail`

```python
@app.get("/api/emails/{email_id}/detail")
async def get_email_detail(email_id: int):
    """
    Get full email detail with AI insights, linked proposals, thread info
    """
    cursor = get_db_cursor()

    # Get email with content
    cursor.execute("""
        SELECT
            e.email_id,
            e.message_id,
            e.subject,
            e.sender_email,
            e.sender_name,
            e.recipient_email,
            e.date,
            e.body_full,
            e.category as basic_category,
            e.thread_id,
            ec.clean_body,
            ec.ai_summary,
            ec.sentiment,
            ec.category,
            ec.subcategory,
            ec.urgency_level,
            ec.action_required,
            ec.key_points,
            ec.entities,
            ec.processed_at
        FROM emails e
        LEFT JOIN email_content ec ON e.email_id = ec.email_id
        WHERE e.email_id = ?
    """, (email_id,))

    email = cursor.fetchone()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    email_dict = dict(email)

    # Get linked proposals
    cursor.execute("""
        SELECT
            p.proposal_id,
            p.project_code,
            p.project_name,
            p.current_status,
            epl.confidence_score,
            epl.auto_linked,
            epl.link_method,
            epl.evidence
        FROM email_proposal_links epl
        JOIN proposals p ON epl.proposal_id = p.proposal_id
        WHERE epl.email_id = ?
        ORDER BY epl.confidence_score DESC
    """, (email_id,))

    email_dict['linked_proposals'] = [dict(row) for row in cursor.fetchall()]

    # Get thread info if part of a thread
    if email['thread_id']:
        cursor.execute("""
            SELECT
                thread_id,
                subject_normalized,
                email_count,
                first_email_date,
                last_email_date,
                proposal_id
            FROM email_threads
            WHERE thread_id = ?
        """, (email['thread_id'],))

        thread = cursor.fetchone()
        email_dict['thread'] = dict(thread) if thread else None
    else:
        email_dict['thread'] = None

    # Get attachments
    cursor.execute("""
        SELECT
            attachment_id,
            attachment_name,
            file_size,
            mime_type,
            has_text_content,
            ai_summary
        FROM email_attachments
        WHERE email_id = ?
    """, (email_id,))

    email_dict['attachments'] = [dict(row) for row in cursor.fetchall()]

    return email_dict
```

**Test:**
```bash
curl http://localhost:8000/api/emails/123/detail | python3 -m json.tool
```

---

#### Task 3.2: Email Thread Endpoint
**Route:** `GET /api/emails/threads/{thread_id}`

```python
@app.get("/api/emails/threads/{thread_id}")
async def get_email_thread(thread_id: int):
    """
    Get all emails in a conversation thread with timeline
    """
    cursor = get_db_cursor()

    # Get thread metadata
    cursor.execute("""
        SELECT *
        FROM email_threads
        WHERE thread_id = ?
    """, (thread_id,))

    thread = cursor.fetchone()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    thread_dict = dict(thread)

    # Get all emails in thread
    cursor.execute("""
        SELECT
            e.email_id,
            e.subject,
            e.sender_email,
            e.sender_name,
            e.date,
            ec.ai_summary,
            ec.sentiment,
            ec.action_required,
            ec.urgency_level,
            LEFT(ec.clean_body, 200) as snippet
        FROM emails e
        LEFT JOIN email_content ec ON e.email_id = ec.email_id
        WHERE e.thread_id = ?
        ORDER BY e.date ASC
    """, (thread_id,))

    thread_dict['emails'] = [dict(row) for row in cursor.fetchall()]

    # Build timeline
    timeline = []
    for email in thread_dict['emails']:
        timeline.append({
            'date': email['date'],
            'event': 'Email',
            'email_id': email['email_id'],
            'sender': email['sender_email'],
            'snippet': email['snippet']
        })

    thread_dict['timeline'] = timeline

    # Get linked proposal if any
    if thread['proposal_id']:
        cursor.execute("""
            SELECT proposal_id, project_code, project_name, current_status
            FROM proposals
            WHERE proposal_id = ?
        """, (thread['proposal_id'],))

        proposal = cursor.fetchone()
        thread_dict['proposal'] = dict(proposal) if proposal else None

    return thread_dict
```

---

#### Task 3.3: Email Search Endpoint
**Route:** `GET /api/emails/search`

```python
@app.get("/api/emails/search")
async def search_emails(
    q: str = None,
    proposal_id: int = None,
    category: str = None,
    sender: str = None,
    date_from: str = None,
    date_to: str = None,
    action_required: bool = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Full-text search emails with filters
    """
    cursor = get_db_cursor()

    # Base query
    query = """
        SELECT
            e.email_id,
            e.subject,
            e.sender_email,
            e.date,
            e.category,
            ec.ai_summary,
            ec.sentiment,
            ec.action_required,
            ec.urgency_level,
            p.project_code,
            p.project_name
        FROM emails e
        LEFT JOIN email_content ec ON e.email_id = ec.email_id
        LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
        LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
        WHERE 1=1
    """

    params = []

    # Full-text search
    if q:
        query += """
            AND e.email_id IN (
                SELECT email_id FROM emails_fts
                WHERE emails_fts MATCH ?
            )
        """
        params.append(q)

    # Filters
    if proposal_id:
        query += " AND epl.proposal_id = ?"
        params.append(proposal_id)

    if category:
        query += " AND ec.category = ?"
        params.append(category)

    if sender:
        query += " AND e.sender_email LIKE ?"
        params.append(f"%{sender}%")

    if date_from:
        query += " AND e.date >= ?"
        params.append(date_from)

    if date_to:
        query += " AND e.date <= ?"
        params.append(date_to)

    if action_required is not None:
        query += " AND ec.action_required = ?"
        params.append(action_required)

    # Count total
    count_query = f"SELECT COUNT(DISTINCT e.email_id) as total FROM emails e LEFT JOIN email_content ec ON e.email_id = ec.email_id LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id WHERE 1=1"
    # (add same filters to count query - omitted for brevity)

    # Pagination
    query += " GROUP BY e.email_id ORDER BY e.date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]

    return {
        "results": results,
        "total": len(results),  # TODO: implement proper count
        "limit": limit,
        "offset": offset
    }
```

---

#### Task 3.4: Bulk Email Operations Endpoint
**Route:** `POST /api/emails/bulk-operations`

```python
@app.post("/api/emails/bulk-operations")
async def bulk_email_operations(operation: dict):
    """
    Perform bulk operations on multiple emails

    operation: {
        "operation": "categorize" | "link" | "flag",
        "email_ids": [123, 124, 125],
        "params": {"category": "proposal", "proposal_id": 33}
    }
    """
    op_type = operation.get('operation')
    email_ids = operation.get('email_ids', [])
    params = operation.get('params', {})

    if not email_ids:
        raise HTTPException(status_code=400, detail="No email_ids provided")

    cursor = get_db_cursor()
    updated = 0

    if op_type == "categorize":
        category = params.get('category')
        if not category:
            raise HTTPException(status_code=400, detail="Category required")

        placeholders = ','.join('?' * len(email_ids))
        cursor.execute(f"""
            UPDATE email_content
            SET category = ?, subcategory = ?
            WHERE email_id IN ({placeholders})
        """, (category, params.get('subcategory', ''), *email_ids))

        updated = cursor.rowcount

    elif op_type == "link":
        proposal_id = params.get('proposal_id')
        if not proposal_id:
            raise HTTPException(status_code=400, detail="Proposal ID required")

        for email_id in email_ids:
            cursor.execute("""
                INSERT OR REPLACE INTO email_proposal_links (
                    email_id, proposal_id, confidence_score,
                    auto_linked, link_method, evidence
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                email_id, proposal_id, 0.95,
                False, 'manual_bulk', 'Bulk operation'
            ))
            updated += 1

    elif op_type == "flag":
        action_required = params.get('action_required', True)

        placeholders = ','.join('?' * len(email_ids))
        cursor.execute(f"""
            UPDATE email_content
            SET action_required = ?
            WHERE email_id IN ({placeholders})
        """, (action_required, *email_ids))

        updated = cursor.rowcount

    conn.commit()

    return {
        "success": True,
        "operation": op_type,
        "updated": updated,
        "email_ids": email_ids
    }
```

---

#### Task 3.5: Email Linking Management Endpoints

```python
@app.post("/api/emails/{email_id}/link-proposal")
async def link_email_to_proposal(email_id: int, link: dict):
    """
    Link email to proposal with confidence score

    link: {
        "proposal_id": 33,
        "confidence_score": 0.95,
        "evidence": "Subject mentions project code"
    }
    """
    cursor = get_db_cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO email_proposal_links (
            email_id, proposal_id, confidence_score,
            auto_linked, link_method, evidence
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        email_id,
        link['proposal_id'],
        link.get('confidence_score', 0.9),
        False,
        'manual',
        link.get('evidence', '')
    ))

    conn.commit()

    return {"success": True, "email_id": email_id, "proposal_id": link['proposal_id']}


@app.delete("/api/emails/{email_id}/proposals/{proposal_id}")
async def unlink_email_from_proposal(email_id: int, proposal_id: int):
    """Remove email-proposal link"""
    cursor = get_db_cursor()

    cursor.execute("""
        DELETE FROM email_proposal_links
        WHERE email_id = ? AND proposal_id = ?
    """, (email_id, proposal_id))

    conn.commit()

    return {"success": True, "deleted": cursor.rowcount}


@app.get("/api/proposals/{project_code}/unlinked-emails")
async def get_unlinked_emails_for_proposal(project_code: str, limit: int = 20):
    """
    Suggest emails that might be related to proposal but aren't linked yet
    """
    cursor = get_db_cursor()

    # Get proposal
    cursor.execute("SELECT proposal_id, project_name FROM proposals WHERE project_code = ?", (project_code,))
    proposal = cursor.fetchone()

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Find emails mentioning project code or name that aren't linked
    cursor.execute("""
        SELECT
            e.email_id,
            e.subject,
            e.sender_email,
            e.date,
            ec.ai_summary,
            'Mentions project code in subject' as reason
        FROM emails e
        LEFT JOIN email_content ec ON e.email_id = ec.email_id
        WHERE (
            e.subject LIKE ? OR
            e.subject LIKE ? OR
            ec.clean_body LIKE ? OR
            ec.clean_body LIKE ?
        )
        AND e.email_id NOT IN (
            SELECT email_id FROM email_proposal_links
            WHERE proposal_id = ?
        )
        ORDER BY e.date DESC
        LIMIT ?
    """, (
        f"%{project_code}%",
        f"%{proposal['project_name']}%",
        f"%{project_code}%",
        f"%{proposal['project_name']}%",
        proposal['proposal_id'],
        limit
    ))

    suggestions = [dict(row) for row in cursor.fetchall()]

    return {
        "proposal_id": proposal['proposal_id'],
        "project_code": project_code,
        "suggestions": suggestions
    }
```

---

## 🎨 PHASE 3: FRONTEND COMPONENTS (AFTER PHASE 2)

### Agent 4: UI Components

⚠️ **DEPENDENCY:** Wait for Agent 3 to complete API endpoints before starting.

#### Task 4.1: Email Detail Modal Component
**File:** `frontend/src/components/emails/email-detail-modal.tsx`

```tsx
'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Calendar, User, Mail, Tag, AlertCircle, FileText } from 'lucide-react'

interface EmailDetailModalProps {
  emailId: number | null
  isOpen: boolean
  onClose: () => void
}

export function EmailDetailModal({ emailId, isOpen, onClose }: EmailDetailModalProps) {
  const { data: email, isLoading } = useQuery({
    queryKey: ['email-detail', emailId],
    queryFn: () => api.getEmailDetail(emailId!),
    enabled: !!emailId && isOpen
  })

  if (!emailId) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{email?.subject || 'Loading...'}</DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="p-8 text-center">Loading email details...</div>
        ) : email ? (
          <div className="space-y-6">
            {/* Email Metadata */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-gray-500" />
                <span className="font-medium">From:</span>
                <span>{email.sender_name || email.sender_email}</span>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <span className="font-medium">Date:</span>
                <span>{new Date(email.date).toLocaleString()}</span>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-gray-500" />
                <span className="font-medium">To:</span>
                <span>{email.recipient_email}</span>
              </div>
              <div className="flex items-center gap-2">
                <Tag className="w-4 h-4 text-gray-500" />
                <span className="font-medium">Category:</span>
                <Badge variant="outline">{email.category}</Badge>
              </div>
            </div>

            {/* AI Insights Panel */}
            {email.ai_summary && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className="w-4 h-4 text-blue-600" />
                  <span className="font-semibold text-blue-900">AI Summary</span>
                </div>
                <p className="text-sm text-blue-800">{email.ai_summary}</p>

                <div className="mt-3 flex gap-4 text-xs">
                  <div>
                    <span className="text-gray-600">Sentiment:</span>{' '}
                    <Badge
                      variant={
                        email.sentiment === 'positive' ? 'success' :
                        email.sentiment === 'negative' ? 'destructive' :
                        'secondary'
                      }
                    >
                      {email.sentiment}
                    </Badge>
                  </div>
                  <div>
                    <span className="text-gray-600">Urgency:</span>{' '}
                    <Badge variant="outline">{email.urgency_level}</Badge>
                  </div>
                  {email.action_required && (
                    <Badge variant="destructive">Action Required</Badge>
                  )}
                </div>
              </div>
            )}

            {/* Key Points */}
            {email.key_points && JSON.parse(email.key_points).length > 0 && (
              <div>
                <h4 className="font-semibold mb-2 text-sm">Key Points</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  {JSON.parse(email.key_points).map((point: string, i: number) => (
                    <li key={i}>{point}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Linked Proposals */}
            {email.linked_proposals && email.linked_proposals.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2 text-sm">Linked Proposals</h4>
                <div className="space-y-2">
                  {email.linked_proposals.map((proposal: any) => (
                    <div
                      key={proposal.proposal_id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded border"
                    >
                      <div>
                        <div className="font-medium">
                          {proposal.project_code} - {proposal.project_name}
                        </div>
                        <div className="text-xs text-gray-500">
                          Status: {proposal.current_status}
                        </div>
                      </div>
                      <div className="text-xs text-gray-500">
                        Confidence: {(proposal.confidence_score * 100).toFixed(0)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Thread Info */}
            {email.thread && (
              <div className="bg-purple-50 border border-purple-200 rounded p-3">
                <div className="text-sm">
                  <span className="font-medium">Part of conversation:</span>{' '}
                  {email.thread.subject_normalized}
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  {email.thread.email_count} messages in thread
                </div>
                <Button
                  variant="link"
                  size="sm"
                  className="p-0 h-auto mt-2"
                  onClick={() => {/* TODO: Open thread viewer */}}
                >
                  View full conversation →
                </Button>
              </div>
            )}

            {/* Email Body */}
            <div className="border-t pt-4">
              <h4 className="font-semibold mb-2 text-sm">Email Content</h4>
              <div className="bg-gray-50 p-4 rounded text-sm whitespace-pre-wrap">
                {email.clean_body || email.body_full}
              </div>
            </div>

            {/* Attachments */}
            {email.attachments && email.attachments.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2 text-sm flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Attachments ({email.attachments.length})
                </h4>
                <div className="space-y-2">
                  {email.attachments.map((attachment: any) => (
                    <div
                      key={attachment.attachment_id}
                      className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm"
                    >
                      <span>{attachment.attachment_name}</span>
                      <span className="text-xs text-gray-500">
                        {(attachment.file_size / 1024).toFixed(0)} KB
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="flex gap-2 border-t pt-4">
              <Button variant="outline" size="sm">
                <Tag className="w-4 h-4 mr-1" />
                Categorize
              </Button>
              <Button variant="outline" size="sm">
                Link to Proposal
              </Button>
              <Button variant="outline" size="sm">
                Flag for Follow-up
              </Button>
            </div>
          </div>
        ) : (
          <div>Email not found</div>
        )}
      </DialogContent>
    </Dialog>
  )
}
```

**API Function (add to `frontend/src/lib/api.ts`):**
```typescript
export const api = {
  // ... existing functions

  getEmailDetail: async (emailId: number) => {
    const response = await fetch(`${API_BASE_URL}/api/emails/${emailId}/detail`)
    if (!response.ok) throw new Error('Failed to fetch email detail')
    return response.json()
  },

  // ... more email functions
}
```

---

#### Task 4.2: Email Thread Viewer Component
**File:** `frontend/src/components/emails/email-thread-viewer.tsx`

```tsx
'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { MessageCircle, ChevronDown, ChevronRight } from 'lucide-react'
import { useState } from 'react'

interface EmailThreadViewerProps {
  threadId: number | null
  isOpen: boolean
  onClose: () => void
}

export function EmailThreadViewer({ threadId, isOpen, onClose }: EmailThreadViewerProps) {
  const [expandedEmails, setExpandedEmails] = useState<Set<number>>(new Set())

  const { data: thread, isLoading } = useQuery({
    queryKey: ['email-thread', threadId],
    queryFn: () => api.getEmailThread(threadId!),
    enabled: !!threadId && isOpen
  })

  const toggleEmail = (emailId: number) => {
    const newExpanded = new Set(expandedEmails)
    if (newExpanded.has(emailId)) {
      newExpanded.delete(emailId)
    } else {
      newExpanded.add(emailId)
    }
    setExpandedEmails(newExpanded)
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5" />
            {thread?.subject_normalized || 'Email Thread'}
          </DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="p-8 text-center">Loading conversation...</div>
        ) : thread ? (
          <div className="space-y-4">
            {/* Thread Metadata */}
            <div className="bg-gray-50 p-4 rounded">
              <div className="flex justify-between items-center">
                <div className="text-sm">
                  <span className="font-medium">{thread.email_count}</span> messages
                  <span className="mx-2">·</span>
                  <span className="text-gray-600">
                    {new Date(thread.first_email_date).toLocaleDateString()} -
                    {new Date(thread.last_email_date).toLocaleDateString()}
                  </span>
                </div>
                {thread.proposal && (
                  <Badge variant="outline">
                    {thread.proposal.project_code} - {thread.proposal.project_name}
                  </Badge>
                )}
              </div>
            </div>

            {/* Email Messages */}
            <div className="space-y-3">
              {thread.emails?.map((email: any, index: number) => {
                const isExpanded = expandedEmails.has(email.email_id)
                const isFirst = index === 0
                const isLast = index === thread.emails.length - 1

                return (
                  <div
                    key={email.email_id}
                    className={`border rounded-lg ${isLast ? 'border-blue-300 bg-blue-50' : 'bg-white'}`}
                  >
                    {/* Email Header */}
                    <div
                      className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                      onClick={() => toggleEmail(email.email_id)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3 flex-1">
                          {isExpanded ? (
                            <ChevronDown className="w-5 h-5 text-gray-400 mt-0.5" />
                          ) : (
                            <ChevronRight className="w-5 h-5 text-gray-400 mt-0.5" />
                          )}

                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{email.sender_name || email.sender_email}</span>
                              {isFirst && <Badge variant="secondary" size="sm">First</Badge>}
                              {isLast && <Badge variant="default" size="sm">Latest</Badge>}
                              {email.action_required && <Badge variant="destructive" size="sm">Action Required</Badge>}
                            </div>

                            <div className="text-sm text-gray-600 mt-1">
                              {new Date(email.date).toLocaleString()}
                            </div>

                            {!isExpanded && email.snippet && (
                              <div className="text-sm text-gray-700 mt-2 line-clamp-2">
                                {email.snippet}...
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {email.sentiment && (
                            <Badge
                              variant={
                                email.sentiment === 'positive' ? 'success' :
                                email.sentiment === 'negative' ? 'destructive' :
                                'secondary'
                              }
                              size="sm"
                            >
                              {email.sentiment}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Expanded Email Body */}
                    {isExpanded && (
                      <div className="border-t p-4 bg-gray-50">
                        {email.ai_summary && (
                          <div className="mb-3 p-3 bg-blue-100 border border-blue-200 rounded text-sm">
                            <div className="font-medium text-blue-900 mb-1">AI Summary</div>
                            <div className="text-blue-800">{email.ai_summary}</div>
                          </div>
                        )}

                        <div className="text-sm whitespace-pre-wrap">
                          {email.clean_body || '(No content)'}
                        </div>

                        <div className="mt-3 pt-3 border-t">
                          <button
                            className="text-sm text-blue-600 hover:text-blue-800"
                            onClick={(e) => {
                              e.stopPropagation()
                              // TODO: Open full email detail modal
                            }}
                          >
                            View full details →
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            {/* Timeline Visualization */}
            <div className="border-t pt-4">
              <h4 className="font-semibold text-sm mb-3">Conversation Timeline</h4>
              <div className="space-y-2">
                {thread.timeline?.map((event: any, index: number) => (
                  <div key={index} className="flex items-center gap-3 text-sm">
                    <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                    <div className="text-gray-600">{new Date(event.date).toLocaleDateString()}</div>
                    <div className="font-medium">{event.sender}</div>
                    <div className="text-gray-500 flex-1 truncate">{event.snippet}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div>Thread not found</div>
        )}
      </DialogContent>
    </Dialog>
  )
}
```

**API Function:**
```typescript
getEmailThread: async (threadId: number) => {
  const response = await fetch(`${API_BASE_URL}/api/emails/threads/${threadId}`)
  if (!response.ok) throw new Error('Failed to fetch email thread')
  return response.json()
},
```

---

#### Task 4.3: Reusable Email List Component
**File:** `frontend/src/components/emails/email-list.tsx`

```tsx
'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Mail, Search, Filter, MoreVertical } from 'lucide-react'
import { EmailDetailModal } from './email-detail-modal'

interface EmailListProps {
  proposalId?: number
  showBulkActions?: boolean
  limit?: number
}

export function EmailList({ proposalId, showBulkActions = true, limit = 50 }: EmailListProps) {
  const [selectedEmails, setSelectedEmails] = useState<Set<number>>(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedEmailId, setSelectedEmailId] = useState<number | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)

  const { data: emailData, isLoading } = useQuery({
    queryKey: ['emails', proposalId, searchQuery],
    queryFn: () => api.searchEmails({
      proposal_id: proposalId,
      q: searchQuery || undefined,
      limit
    })
  })

  const emails = emailData?.results || []

  const toggleEmail = (emailId: number) => {
    const newSelected = new Set(selectedEmails)
    if (newSelected.has(emailId)) {
      newSelected.delete(emailId)
    } else {
      newSelected.add(emailId)
    }
    setSelectedEmails(newSelected)
  }

  const toggleAll = () => {
    if (selectedEmails.size === emails.length) {
      setSelectedEmails(new Set())
    } else {
      setSelectedEmails(new Set(emails.map(e => e.email_id)))
    }
  }

  const handleRowClick = (emailId: number) => {
    setSelectedEmailId(emailId)
    setIsDetailModalOpen(true)
  }

  const handleBulkCategorize = async (category: string) => {
    await api.bulkEmailOperations({
      operation: 'categorize',
      email_ids: Array.from(selectedEmails),
      params: { category }
    })
    // Refresh list
  }

  return (
    <div className="space-y-4">
      {/* Search & Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Search emails..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline">
          <Filter className="w-4 h-4 mr-2" />
          Filters
        </Button>
      </div>

      {/* Bulk Actions Toolbar */}
      {showBulkActions && selectedEmails.size > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded p-3 flex items-center justify-between">
          <span className="text-sm font-medium">
            {selectedEmails.size} email{selectedEmails.size > 1 ? 's' : ''} selected
          </span>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => handleBulkCategorize('proposal')}>
              Categorize as Proposal
            </Button>
            <Button size="sm" variant="outline" onClick={() => handleBulkCategorize('contract')}>
              Categorize as Contract
            </Button>
            <Button size="sm" variant="outline">
              Link to Proposal
            </Button>
          </div>
        </div>
      )}

      {/* Email Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              {showBulkActions && (
                <TableHead className="w-12">
                  <Checkbox
                    checked={selectedEmails.size === emails.length && emails.length > 0}
                    onCheckedChange={toggleAll}
                  />
                </TableHead>
              )}
              <TableHead>Date</TableHead>
              <TableHead>From</TableHead>
              <TableHead>Subject</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                  Loading emails...
                </TableCell>
              </TableRow>
            ) : emails.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                  <Mail className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  No emails found
                </TableCell>
              </TableRow>
            ) : (
              emails.map((email: any) => (
                <TableRow
                  key={email.email_id}
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleRowClick(email.email_id)}
                >
                  {showBulkActions && (
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={selectedEmails.has(email.email_id)}
                        onCheckedChange={() => toggleEmail(email.email_id)}
                      />
                    </TableCell>
                  )}
                  <TableCell className="text-sm text-gray-600">
                    {new Date(email.date).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-sm">
                    {email.sender_email}
                  </TableCell>
                  <TableCell className="font-medium text-sm">
                    {email.subject}
                    {email.ai_summary && (
                      <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                        {email.ai_summary}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    {email.category && (
                      <Badge variant="outline" size="sm">
                        {email.category}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {email.action_required && (
                        <Badge variant="destructive" size="sm">Action</Badge>
                      )}
                      {email.urgency_level === 'urgent' && (
                        <Badge variant="destructive" size="sm">Urgent</Badge>
                      )}
                      {email.sentiment === 'positive' && (
                        <Badge variant="success" size="sm">😊</Badge>
                      )}
                      {email.sentiment === 'negative' && (
                        <Badge variant="destructive" size="sm">😟</Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        // TODO: Show context menu
                      }}
                    >
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {emails.length >= limit && (
        <div className="flex justify-center">
          <Button variant="outline">Load More</Button>
        </div>
      )}

      {/* Email Detail Modal */}
      <EmailDetailModal
        emailId={selectedEmailId}
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false)
          setSelectedEmailId(null)
        }}
      />
    </div>
  )
}
```

**API Function:**
```typescript
searchEmails: async (params: {
  q?: string
  proposal_id?: number
  category?: string
  limit?: number
}) => {
  const queryParams = new URLSearchParams()
  if (params.q) queryParams.set('q', params.q)
  if (params.proposal_id) queryParams.set('proposal_id', String(params.proposal_id))
  if (params.category) queryParams.set('category', params.category)
  if (params.limit) queryParams.set('limit', String(params.limit))

  const response = await fetch(`${API_BASE_URL}/api/emails/search?${queryParams}`)
  if (!response.ok) throw new Error('Failed to search emails')
  return response.json()
},

bulkEmailOperations: async (operation: {
  operation: string
  email_ids: number[]
  params: any
}) => {
  const response = await fetch(`${API_BASE_URL}/api/emails/bulk-operations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(operation)
  })
  if (!response.ok) throw new Error('Bulk operation failed')
  return response.json()
},
```

---

#### Task 4.4: Email Activity Widget
**File:** `frontend/src/components/proposals/email-activity-widget.tsx`

```tsx
'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Mail, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react'

interface EmailActivityWidgetProps {
  projectCode: string
  onViewAll?: () => void
}

export function EmailActivityWidget({ projectCode, onViewAll }: EmailActivityWidgetProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['email-activity', projectCode],
    queryFn: async () => {
      const emails = await api.getProposalEmails(projectCode)

      // Calculate metrics
      const now = new Date()
      const last7Days = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      const last30Days = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      const last37Days = new Date(now.getTime() - 37 * 24 * 60 * 60 * 1000)

      const recent7 = emails.filter((e: any) => new Date(e.date) >= last7Days).length
      const recent30 = emails.filter((e: any) => new Date(e.date) >= last30Days).length
      const previous7 = emails.filter((e: any) =>
        new Date(e.date) >= last37Days && new Date(e.date) < last30Days
      ).length

      const actionRequired = emails.filter((e: any) => e.action_required).length

      const latest = emails.sort((a: any, b: any) =>
        new Date(b.date).getTime() - new Date(a.date).getTime()
      )[0]

      return {
        total: emails.length,
        recent7,
        recent30,
        previous7,
        actionRequired,
        latest,
        trend: recent7 > previous7 ? 'up' : recent7 < previous7 ? 'down' : 'flat'
      }
    }
  })

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-gray-500">
          Loading email activity...
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg flex items-center gap-2">
          <Mail className="w-5 h-5" />
          Email Activity
        </CardTitle>
        {data?.actionRequired > 0 && (
          <Badge variant="destructive">
            {data.actionRequired} action{data.actionRequired > 1 ? 's' : ''} required
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <div className="text-2xl font-bold">{data?.recent7 || 0}</div>
            <div className="text-xs text-gray-600">Last 7 days</div>
          </div>
          <div>
            <div className="text-2xl font-bold">{data?.recent30 || 0}</div>
            <div className="text-xs text-gray-600">Last 30 days</div>
          </div>
          <div>
            <div className="text-2xl font-bold">{data?.total || 0}</div>
            <div className="text-xs text-gray-600">Total</div>
          </div>
        </div>

        {data?.trend && (
          <div className="flex items-center gap-2 text-sm mb-4">
            {data.trend === 'up' ? (
              <><TrendingUp className="w-4 h-4 text-green-600" />
              <span className="text-green-600">More active than last week</span></>
            ) : data.trend === 'down' ? (
              <><TrendingDown className="w-4 h-4 text-red-600" />
              <span className="text-red-600">Less active than last week</span></>
            ) : (
              <span className="text-gray-600">Similar to last week</span>
            )}
          </div>
        )}

        {data?.latest && (
          <div className="border-t pt-4">
            <div className="text-sm font-medium mb-2">Latest Email</div>
            <div className="text-xs text-gray-600">
              From: {data.latest.sender_email}
            </div>
            <div className="text-xs text-gray-600">
              {new Date(data.latest.date).toLocaleString()}
            </div>
            {data.latest.ai_summary && (
              <div className="text-xs text-gray-700 mt-2 line-clamp-2">
                {data.latest.ai_summary}
              </div>
            )}
          </div>
        )}

        <Button
          variant="outline"
          size="sm"
          className="w-full mt-4"
          onClick={onViewAll}
        >
          View all emails →
        </Button>
      </CardContent>
    </Card>
  )
}
```

---

### Agent 5: Frontend Integration

⚠️ **DEPENDENCY:** Wait for Agent 4 to complete components before starting.

#### Task 5.1: Enhance Proposal Email Tab
**File:** `frontend/src/app/(dashboard)/proposals/[projectCode]/page.tsx` (modify existing)

Find the Emails tab section and replace with:

```tsx
{/* Emails Tab - ENHANCED */}
<TabsContent value="emails" className="space-y-4">
  <EmailList
    proposalId={proposal.proposal_id}
    showBulkActions={true}
    limit={100}
  />
</TabsContent>
```

That's it! The `EmailList` component handles everything: search, filters, bulk operations, detail modal, etc.

---

#### Task 5.2: Add Email Activity Widget to Overview Tab

In the same file, find the Overview tab and add the widget:

```tsx
<TabsContent value="overview" className="space-y-6">
  {/* Existing overview content */}

  {/* ADD THIS */}
  <EmailActivityWidget
    projectCode={params.projectCode}
    onViewAll={() => {
      // Switch to Emails tab
      const tabsList = document.querySelector('[value="emails"]') as HTMLElement
      tabsList?.click()
    }}
  />
</TabsContent>
```

---

#### Task 5.3: Create Global Email Search Page
**File:** `frontend/src/app/(dashboard)/emails/page.tsx` (new file)

```tsx
'use client'

import { useState } from 'react'
import { EmailList } from '@/components/emails/email-list'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Search, Filter, X } from 'lucide-react'

export default function EmailsPage() {
  const [filters, setFilters] = useState({
    category: null as string | null,
    actionRequired: null as boolean | null,
    dateRange: null as string | null
  })

  const clearFilters = () => {
    setFilters({
      category: null,
      actionRequired: null,
      dateRange: null
    })
  }

  const hasActiveFilters = Object.values(filters).some(v => v !== null)

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Email Search</h1>
        <p className="text-gray-600 mt-1">
          Search and manage emails across all proposals
        </p>
      </div>

      {/* Filters Sidebar */}
      <div className="grid grid-cols-4 gap-6">
        <div className="space-y-4">
          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm">Filters</h3>
              {hasActiveFilters && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                >
                  <X className="w-4 h-4 mr-1" />
                  Clear
                </Button>
              )}
            </div>

            {/* Category Filter */}
            <div className="mb-4">
              <div className="text-sm font-medium mb-2">Category</div>
              <div className="space-y-1">
                {['proposal', 'contract', 'financial', 'rfi', 'meeting', 'general'].map(cat => (
                  <button
                    key={cat}
                    className={`w-full text-left px-2 py-1 text-sm rounded hover:bg-gray-100 ${
                      filters.category === cat ? 'bg-blue-100 text-blue-700' : ''
                    }`}
                    onClick={() => setFilters({ ...filters, category: cat })}
                  >
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Action Required Filter */}
            <div className="mb-4">
              <div className="text-sm font-medium mb-2">Status</div>
              <button
                className={`w-full text-left px-2 py-1 text-sm rounded hover:bg-gray-100 ${
                  filters.actionRequired === true ? 'bg-red-100 text-red-700' : ''
                }`}
                onClick={() => setFilters({ ...filters, actionRequired: true })}
              >
                Action Required
              </button>
            </div>

            {/* Date Range Filter */}
            <div>
              <div className="text-sm font-medium mb-2">Date Range</div>
              <div className="space-y-1">
                {['last-7-days', 'last-30-days', 'last-90-days', 'last-year'].map(range => (
                  <button
                    key={range}
                    className={`w-full text-left px-2 py-1 text-sm rounded hover:bg-gray-100 ${
                      filters.dateRange === range ? 'bg-blue-100 text-blue-700' : ''
                    }`}
                    onClick={() => setFilters({ ...filters, dateRange: range })}
                  >
                    {range.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Email List (3 columns) */}
        <div className="col-span-3">
          {hasActiveFilters && (
            <div className="mb-4 flex gap-2">
              {filters.category && (
                <Badge variant="outline">
                  Category: {filters.category}
                </Badge>
              )}
              {filters.actionRequired && (
                <Badge variant="destructive">
                  Action Required
                </Badge>
              )}
              {filters.dateRange && (
                <Badge variant="outline">
                  {filters.dateRange.split('-').join(' ')}
                </Badge>
              )}
            </div>
          )}

          <EmailList
            showBulkActions={true}
            limit={100}
          />
        </div>
      </div>
    </div>
  )
}
```

**Add to navigation** (in `frontend/src/components/layout/app-shell.tsx`):
```tsx
{/* Add to nav items */}
<Link href="/emails">
  <Mail className="w-4 h-4 mr-2" />
  Emails
</Link>
```

---

## ✅ TESTING CHECKLIST

### Phase 1 Testing
- [ ] Email content script processes 50 test emails successfully
- [ ] `email_content` table grows from 22 → 3,356 records
- [ ] Thread builder creates threads (check `email_threads` table has >0 records)
- [ ] Proposal status history has 100+ records (was 3)
- [ ] Database migration runs without errors
- [ ] Indexes created (verify with `.indexes emails`)

### Phase 2 Testing
- [ ] `GET /api/emails/123/detail` returns full email with AI insights
- [ ] `GET /api/emails/threads/45` returns conversation thread
- [ ] `GET /api/emails/search?q=contract` returns search results
- [ ] Bulk categorize 10 emails works
- [ ] Link/unlink email-proposal works

### Phase 3 Testing
- [ ] Email detail modal opens and shows full email
- [ ] Thread viewer shows conversation flow
- [ ] Email list component displays with search
- [ ] Bulk select and categorize works
- [ ] Proposal email tab shows enhanced list
- [ ] Email activity widget shows metrics
- [ ] Global email search page works with filters

---

## 🚀 LAUNCH SEQUENCE

1. **Agent 1 starts immediately** - Email content population (CRITICAL PATH)
2. **Agent 2 runs parallel** - Database schema migration
3. **Agents 1 & 2 complete** → Checkpoint: Verify data populated
4. **Agent 3 starts** - Build API endpoints
5. **Agent 3 completes** → Checkpoint: Test all APIs with curl/Postman
6. **Agent 4 starts** - Build UI components
7. **Agent 4 completes** → Checkpoint: Test components in isolation
8. **Agent 5 starts** - Wire everything together
9. **Final testing** - End-to-end user flows

---

## 📊 SUCCESS METRICS

- ✅ 3,356 emails processed (from 22)
- ✅ 100+ email threads created
- ✅ 200+ status history records
- ✅ 5 new API endpoints working
- ✅ 4 new UI components integrated
- ✅ <2 second page load for proposal email tab
- ✅ Search returns results in <500ms
- ✅ Bulk operations handle 50+ emails

---

**READY TO EXECUTE! 🚀**

Distribute this document to your 5 agents and let them execute in the specified order.
