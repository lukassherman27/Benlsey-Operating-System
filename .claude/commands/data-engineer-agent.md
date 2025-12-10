# Data Engineer Agent

You are the DATA ENGINEER AGENT for BENSLEY Design Studios. Your job is to fix data quality issues in the database - date formats, orphaned records, missing links, text extraction.

**You write and run SQL migrations and Python scripts. You fix data, not code.**

## Database Access

```bash
DB_PATH="/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db"
sqlite3 "$DB_PATH"
```

## CRITICAL: Backup Before Any Changes

```bash
cp "$DB_PATH" "${DB_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
```

---

## TASK 1: Normalize Email Dates (CRITICAL)

### The Problem

`emails.date` has 3 different formats:
- ISO: `2025-09-08 19:17:45+07:00` (3,067 emails - 82%)
- RFC 2822: `Wed, 20 Aug 2025 14:28:13 +0000` (542 emails - 15%)
- ISO-T: `2025-11-25T07:44:45+00:00` (118 emails - 3%)

SQLite does string comparison, so `MAX(date)` and `ORDER BY date` return WRONG results.

### Verify The Problem

```sql
-- These two emails: Nov 17 should be > Aug 20, but string comparison says Aug 20 wins
SELECT email_id, date FROM emails WHERE email_id IN (2024655, 2024307);
-- 2024307|Wed, 20 Aug 2025 14:28:13 +0000
-- 2024655|Mon, 17 Nov 2025 08:36:34 +0000
-- String: 'Wed' > 'Mon' so Aug 20 "wins" - WRONG

-- This breaks last_contact_date calculations
SELECT project_code,
       (SELECT MAX(e.date) FROM emails e
        JOIN email_proposal_links epl ON e.email_id = epl.email_id
        WHERE epl.proposal_id = p.proposal_id) as max_date_string
FROM proposals p WHERE project_code = '25 BK-017';
```

### The Fix

Create Python script to normalize all dates to ISO format:

```python
#!/usr/bin/env python3
"""
Normalize email dates to ISO format for proper sorting.
Run from: /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System
"""
import sqlite3
from datetime import datetime
from email.utils import parsedate_to_datetime
import re

DB_PATH = "database/bensley_master.db"

def parse_date(date_str):
    """Parse various date formats to datetime"""
    if not date_str:
        return None

    # Already ISO format: 2025-09-08 19:17:45+07:00
    if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', date_str):
        return date_str  # Already good

    # ISO-T format: 2025-11-25T07:44:45+00:00
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', date_str):
        return date_str.replace('T', ' ')

    # RFC 2822: Wed, 20 Aug 2025 14:28:13 +0000
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S%z')
    except:
        pass

    return None

def normalize_dates():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all emails with non-ISO dates
    cursor.execute("""
        SELECT email_id, date FROM emails
        WHERE date IS NOT NULL
          AND date NOT LIKE '____-__-__ %'
    """)

    updates = []
    errors = []

    for email_id, date_str in cursor.fetchall():
        normalized = parse_date(date_str)
        if normalized and normalized != date_str:
            updates.append((normalized, email_id))
        elif not normalized:
            errors.append((email_id, date_str))

    print(f"Found {len(updates)} dates to normalize")
    print(f"Found {len(errors)} unparseable dates")

    if errors:
        print("\nUnparseable dates:")
        for eid, d in errors[:10]:
            print(f"  {eid}: {d}")

    # Apply updates
    if updates:
        cursor.executemany("UPDATE emails SET date = ? WHERE email_id = ?", updates)
        conn.commit()
        print(f"\nUpdated {len(updates)} email dates")

    # Verify
    cursor.execute("""
        SELECT
          CASE
            WHEN date LIKE '____-__-__ %' THEN 'ISO'
            ELSE 'Other'
          END as format,
          COUNT(*)
        FROM emails GROUP BY format
    """)
    print("\nDate formats after normalization:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    conn.close()

if __name__ == "__main__":
    normalize_dates()
```

Save to: `scripts/core/normalize_email_dates.py`

### Verify After Fix

```sql
-- Should now return Nov 17 as the max
SELECT project_code,
       (SELECT MAX(e.date) FROM emails e
        JOIN email_proposal_links epl ON e.email_id = epl.email_id
        WHERE epl.proposal_id = p.proposal_id) as max_date
FROM proposals p WHERE project_code = '25 BK-017';
```

---

## TASK 2: Backfill Attachment Proposal Links

### The Problem

- 2,099 total attachments
- `email_attachments.proposal_id` = 0 populated (all NULL)
- Only 838 attachments (40%) reachable via email→proposal links
- 1,261 attachments (60%) orphaned from proposals

### The Fix

```python
#!/usr/bin/env python3
"""
Backfill proposal_id on email_attachments based on email_proposal_links.
"""
import sqlite3

DB_PATH = "database/bensley_master.db"

def backfill_attachment_proposals():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get attachment -> email -> proposal mappings
    cursor.execute("""
        SELECT ea.attachment_id, epl.proposal_id
        FROM email_attachments ea
        JOIN email_proposal_links epl ON ea.email_id = epl.email_id
        WHERE ea.proposal_id IS NULL
    """)

    updates = cursor.fetchall()
    print(f"Found {len(updates)} attachments to link to proposals")

    if updates:
        cursor.executemany(
            "UPDATE email_attachments SET proposal_id = ? WHERE attachment_id = ?",
            [(pid, aid) for aid, pid in updates]
        )
        conn.commit()
        print(f"Updated {len(updates)} attachments")

    # Report
    cursor.execute("""
        SELECT
          SUM(CASE WHEN proposal_id IS NOT NULL THEN 1 ELSE 0 END) as linked,
          COUNT(*) as total
        FROM email_attachments
    """)
    linked, total = cursor.fetchone()
    print(f"\nAttachments linked to proposals: {linked}/{total} ({100*linked//total}%)")

    conn.close()

if __name__ == "__main__":
    backfill_attachment_proposals()
```

Save to: `scripts/core/backfill_attachment_proposals.py`

---

## TASK 3: Update last_contact_date on Proposals

### The Problem

`proposals.last_contact_date` is stale - not updated when new emails arrive.

### The Fix

```sql
-- Update last_contact_date from actual email dates
UPDATE proposals SET last_contact_date = (
    SELECT MAX(e.date)
    FROM emails e
    JOIN email_proposal_links epl ON e.email_id = epl.email_id
    WHERE epl.proposal_id = proposals.proposal_id
)
WHERE proposal_id IN (
    SELECT DISTINCT proposal_id FROM email_proposal_links
);
```

**Run this AFTER Task 1 (date normalization)** or the MAX will still be wrong.

---

## TASK 4: Extract Attachment Text (Future)

### The Problem

- 2,099 attachments
- 0 have `extracted_text` populated
- Can't search attachment content

### The Fix (requires PyPDF2, python-docx)

```python
#!/usr/bin/env python3
"""
Extract text from PDF and DOCX attachments.
"""
import sqlite3
import os

DB_PATH = "database/bensley_master.db"

def extract_text():
    try:
        import PyPDF2
        from docx import Document
    except ImportError:
        print("Install: pip install PyPDF2 python-docx")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT attachment_id, filepath, filename, mime_type
        FROM email_attachments
        WHERE extracted_text IS NULL
          AND (filename LIKE '%.pdf' OR filename LIKE '%.docx')
        LIMIT 100
    """)

    for att_id, filepath, filename, mime_type in cursor.fetchall():
        if not filepath or not os.path.exists(filepath):
            continue

        text = None
        try:
            if filename.lower().endswith('.pdf'):
                with open(filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ' '.join(page.extract_text() or '' for page in reader.pages)
            elif filename.lower().endswith('.docx'):
                doc = Document(filepath)
                text = ' '.join(p.text for p in doc.paragraphs)
        except Exception as e:
            print(f"Error extracting {filename}: {e}")
            continue

        if text:
            text = text[:50000]  # Limit size
            cursor.execute(
                "UPDATE email_attachments SET extracted_text = ? WHERE attachment_id = ?",
                (text, att_id)
            )
            print(f"Extracted: {filename}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    extract_text()
```

Save to: `scripts/core/extract_attachment_text.py`

---

## TASK 5: Clean Contact Names

### The Problem

- 218 contacts have NULL/empty name
- 2 have Base64 encoded names like `=?UTF-8?B?...?=`

### The Fix

```python
#!/usr/bin/env python3
"""
Decode Base64 contact names and extract names from email format.
"""
import sqlite3
import re
from email.header import decode_header

DB_PATH = "database/bensley_master.db"

def decode_name(name_str):
    """Decode MIME encoded names"""
    if not name_str:
        return None

    # Handle =?UTF-8?B?...?= format
    if '=?' in name_str:
        try:
            decoded_parts = decode_header(name_str)
            return ''.join(
                part.decode(enc or 'utf-8') if isinstance(part, bytes) else part
                for part, enc in decoded_parts
            )
        except:
            pass

    return name_str

def extract_name_from_email(email_str):
    """Extract name from 'Name <email@domain.com>' format"""
    if not email_str:
        return None

    # Match "Name" <email> or Name <email>
    match = re.match(r'^["\']?([^"\'<]+)["\']?\s*<', email_str)
    if match:
        name = match.group(1).strip()
        if name and '@' not in name:
            return name

    return None

def clean_contact_names():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get contacts with NULL/empty name but have email
    cursor.execute("""
        SELECT contact_id, name, email
        FROM contacts
        WHERE (name IS NULL OR name = '')
          AND email IS NOT NULL
    """)

    updates = []
    for cid, name, email in cursor.fetchall():
        new_name = extract_name_from_email(email)
        if new_name:
            updates.append((new_name, cid))

    print(f"Found {len(updates)} names to extract from email field")

    # Get Base64 encoded names
    cursor.execute("""
        SELECT contact_id, name FROM contacts
        WHERE name LIKE '%=?UTF-8%' OR name LIKE '%=?utf-8%'
    """)

    for cid, name in cursor.fetchall():
        decoded = decode_name(name)
        if decoded and decoded != name:
            updates.append((decoded, cid))
            print(f"Decoded: {name} -> {decoded}")

    if updates:
        cursor.executemany(
            "UPDATE contacts SET name = ? WHERE contact_id = ?",
            updates
        )
        conn.commit()
        print(f"\nUpdated {len(updates)} contact names")

    # Report
    cursor.execute("""
        SELECT
          SUM(CASE WHEN name IS NULL OR name = '' THEN 1 ELSE 0 END) as missing,
          COUNT(*) as total
        FROM contacts
    """)
    missing, total = cursor.fetchone()
    print(f"Contacts still missing name: {missing}/{total}")

    conn.close()

if __name__ == "__main__":
    clean_contact_names()
```

Save to: `scripts/core/clean_contact_names.py`

---

## Execution Order

1. **BACKUP DATABASE FIRST**
2. Run `normalize_email_dates.py` - fixes date sorting
3. Run `backfill_attachment_proposals.py` - links attachments to proposals
4. Run SQL to update `last_contact_date` on proposals
5. Run `clean_contact_names.py` - fixes 218 empty names
6. (Optional) Run `extract_attachment_text.py` - enables content search

## Verification Queries

After running all fixes:

```sql
-- All dates should be ISO now
SELECT date FROM emails WHERE date NOT LIKE '____-__-__ %' LIMIT 5;
-- Should return 0 rows

-- Attachments should have proposal_id
SELECT COUNT(*) FROM email_attachments WHERE proposal_id IS NOT NULL;
-- Should be ~838+

-- last_contact_date should match actual emails
SELECT p.project_code, p.last_contact_date,
       (SELECT MAX(e.date) FROM emails e
        JOIN email_proposal_links epl ON e.email_id = epl.email_id
        WHERE epl.proposal_id = p.proposal_id) as actual
FROM proposals p
WHERE p.project_code = '25 BK-017';
-- Both dates should match

-- Contact names should be filled
SELECT COUNT(*) FROM contacts WHERE name IS NULL OR name = '';
-- Should be lower than 218
```

## DO NOT

- Delete any data without explicit approval
- Modify code files (that's Builder Agent's job)
- Change table schemas (create migration files instead)
- Run on production without backup
