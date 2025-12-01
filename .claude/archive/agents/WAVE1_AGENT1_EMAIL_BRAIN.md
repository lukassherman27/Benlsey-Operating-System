# 🧠 Agent 1: Email Brain Foundation

**Wave:** 1 (Foundation)
**Priority:** CRITICAL - Everything depends on this
**Status:** AWAITING AUDIT

---

## ⚠️ MANDATORY PROTOCOL

### YOU MUST FOLLOW THIS SEQUENCE:

1. ✅ **READ** `.claude/MASTER_ARCHITECTURE.md`
2. ✅ **READ** `.claude/ALIGNMENT_AUDIT.md`
3. 🔍 **AUDIT** your assigned area (see below)
4. 📊 **REPORT** findings to user
5. ⏸️ **WAIT** for user approval
6. ✅ **EXECUTE** only after approval
7. 📝 **DOCUMENT** changes made

**DO NOT SKIP THE AUDIT AND REPORT PHASES**

---

## 🎯 YOUR MISSION

Fix email body content extraction so that `email_content` table gets populated with:
- Clean email body text
- Quoted text separation
- AI-generated summaries
- Key points extraction
- Entity recognition
- Sentiment analysis
- Action items

**Current Problem:** 3,356 emails imported but `email_content` table is EMPTY (0 records)

---

## 🔍 PHASE 1: AUDIT (DO THIS FIRST)

### Your Audit Checklist:

**1. Database Path Verification**
```bash
# Check which scripts have wrong database path
grep -l "Desktop/BDS_SYSTEM" *.py

# Check current email import script
grep -n "DB_PATH\|bensley_master" import_all_emails.py smart_email_system.py
```

**Report:**
- [ ] How many email scripts have wrong database path?
- [ ] Which script is the PRIMARY email importer?
- [ ] Does it currently extract email body content?

**2. Table Structure Verification**
```bash
# Check email_content table structure
sqlite3 database/bensley_master.db "PRAGMA table_info(email_content)"

# Check if any content exists
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM email_content"
```

**Report:**
- [ ] Does `email_content` table have all required columns?
- [ ] Are there any records in it currently?
- [ ] What columns are missing (if any)?

**3. Existing Script Analysis**
```bash
# Analyze smart_email_system.py
cat smart_email_system.py | grep -A 10 "def.*process"

# Check what it writes to database
grep -n "INSERT INTO\|UPDATE.*SET" smart_email_system.py
```

**Report:**
- [ ] Does `smart_email_system.py` extract email body?
- [ ] What table does it write to? (emails.category or email_content?)
- [ ] Is the script architecture sound or needs rewrite?

**4. Email Import Flow Analysis**
```bash
# Check import_all_emails.py or equivalent
ls -lh *email*.py | head -10

# Identify the current importer
grep -l "INBOX\|imap" *.py
```

**Report:**
- [ ] Which script imports emails from tmail.bensley.com?
- [ ] Does it extract body content during import or after?
- [ ] Is it using IMAP correctly?

**5. Dependencies & Conflicts Check**
```bash
# Check for email processing dependencies
grep -n "import.*email\|from.*email" smart_email_system.py import_all_emails.py

# Check OpenAI API usage
grep -n "openai\|OpenAI" smart_email_system.py
```

**Report:**
- [ ] What Python libraries are needed?
- [ ] Is OpenAI API key configured?
- [ ] Are there conflicts with other email scripts?

---

## 📊 PHASE 2: REPORT (CREATE THIS DOCUMENT)

### Create: `AGENT1_AUDIT_REPORT.md`

**Template:**
```markdown
# Agent 1 Email Brain - Audit Report

## Summary
[One paragraph: What's broken, why, and recommended fix]

## Findings

### Database Path Issue
- Scripts with wrong path: [NUMBER]
- Primary importer: [SCRIPT NAME]
- Current path: [PATH]
- Correct path: [PATH]

### Email Content Extraction
- Current state: [WORKING/BROKEN]
- Table being used: [TABLE NAME]
- Body content extraction: [YES/NO]
- AI analysis: [YES/NO/PARTIAL]

### Architecture Assessment
- Script quality: [GOOD/NEEDS WORK/REWRITE]
- Recommendation: [FIX/EXTEND/REPLACE]
- Estimated effort: [HOURS]

## Proposed Solution

### Option A: [DESCRIPTION]
**Pros:** ...
**Cons:** ...
**Effort:** ... hours

### Option B: [DESCRIPTION]
**Pros:** ...
**Cons:** ...
**Effort:** ... hours

## Recommendation
[Which option and why]

## Questions for User
1. [Question about approach]
2. [Question about priorities]
3. [Question about constraints]

## Next Steps (After Approval)
1. [Step 1]
2. [Step 2]
3. [Step 3]
```

**STOP HERE AND WAIT FOR USER RESPONSE**

---

## ⏸️ PHASE 3: AWAIT APPROVAL

After creating your audit report, you MUST:
1. Present findings to user
2. Explain your recommended approach
3. Answer user's questions
4. Get explicit approval to proceed

**DO NOT PROCEED TO PHASE 4 WITHOUT APPROVAL**

---

## ✅ PHASE 4: EXECUTION (Only After Approval)

### Task 1: Fix Database Path
**File:** Create `database_config.py`
```python
#!/usr/bin/env python3
"""
CANONICAL DATABASE CONFIGURATION
All scripts MUST import from here
"""
from pathlib import Path

DB_PATH = str(Path(__file__).parent / "database" / "bensley_master.db")

def get_db_connection():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
```

**Files to Update:**
- `smart_email_system.py` - Change DB_PATH to import from config
- `import_all_emails.py` - Change DB_PATH to import from config
- Any other email scripts with wrong path

### Task 2: Fix Email Content Extraction
**File:** `smart_email_system.py` (or create new `email_content_extractor.py`)

**Add function:**
```python
def extract_and_store_content(self, email_id: int, email: Dict):
    """
    Extract email body content and store in email_content table
    """
    # Get email body (handle HTML and plain text)
    body = email.get('body', '')
    clean_body = self._clean_email_body(body)
    quoted_text = self._extract_quoted_text(body)

    # AI analysis (if body has content)
    if len(clean_body) > 50:
        analysis = self._analyze_with_ai(clean_body)

        # Store in email_content table
        self.cursor.execute("""
            INSERT OR REPLACE INTO email_content (
                email_id, clean_body, quoted_text,
                category, subcategory, key_points, entities,
                sentiment, importance_score, ai_summary,
                urgency_level, action_required, processing_model
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email_id, clean_body, quoted_text,
            analysis['category'], analysis['subcategory'],
            json.dumps(analysis['key_points']),
            json.dumps(analysis['entities']),
            analysis['sentiment'], analysis['importance_score'],
            analysis['summary'], analysis['urgency'],
            analysis['action_required'], 'gpt-4o-mini'
        ))
        self.conn.commit()
```

### Task 3: Re-Process Existing Emails
**Script:** Create `backfill_email_content.py`
```python
#!/usr/bin/env python3
"""
Backfill email_content table for all 3,356 existing emails
"""
import database_config
from smart_email_system import SmartEmailSystem

def main():
    conn = database_config.get_db_connection()
    cursor = conn.cursor()

    # Get all emails without content
    cursor.execute("""
        SELECT e.email_id
        FROM emails e
        LEFT JOIN email_content ec ON e.email_id = ec.email_id
        WHERE ec.content_id IS NULL
        LIMIT 100  -- Process in batches
    """)

    emails = cursor.fetchall()
    print(f"Processing {len(emails)} emails...")

    processor = SmartEmailSystem()
    for email in emails:
        try:
            processor.process_email(email['email_id'])
        except Exception as e:
            print(f"Error processing {email['email_id']}: {e}")

    conn.close()

if __name__ == "__main__":
    main()
```

### Task 4: Test & Verify
```bash
# Test on 10 sample emails first
python3 backfill_email_content.py

# Verify content was stored
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM email_content"

# Check a sample
sqlite3 database/bensley_master.db "SELECT email_id, category, LEFT(clean_body, 100) FROM email_content LIMIT 5"
```

---

## 📝 PHASE 5: DOCUMENTATION

After completing execution, update:

**1. MASTER_ARCHITECTURE.md**
- Update "Current State Assessment"
- Document what you fixed
- Add to CHANGE LOG

**2. Create AGENT1_COMPLETION_REPORT.md**
```markdown
# Agent 1 Email Brain - Completion Report

## What Was Done
- Fixed database paths in [N] scripts
- Modified smart_email_system.py to use email_content table
- Processed [N] emails successfully
- email_content table now has [N] records

## Testing Results
- [X] Database path correct
- [X] Email body extraction working
- [X] AI categorization working
- [X] email_content table populated

## Issues Encountered
[Any problems and how they were resolved]

## Handoff for Next Agents
- email_content table ready for use
- Scripts available: [LIST]
- API endpoints needed: [LIST for backend agent]

## Metrics
- Time taken: [HOURS]
- Emails processed: [NUMBER]
- Success rate: [PERCENTAGE]
- Cost: $[AMOUNT] in API calls
```

---

## 🚫 WHAT NOT TO DO

1. **DON'T** create a completely new email system
2. **DON'T** replace `smart_email_system.py` - extend it
3. **DON'T** create duplicate tables
4. **DON'T** use a different database path
5. **DON'T** skip the audit phase
6. **DON'T** proceed without user approval

---

## 🤝 COORDINATION WITH OTHER AGENTS

**You provide to Agent 3 (Proposal APIs):**
- email_content table populated
- Categorization data available
- Email body text searchable

**You provide to Agent 4 (RFI Detection):**
- Email content with action_required flags
- Categorized emails (rfi_request category)
- Clean body text for analysis

**You need from no one:** You're first in the dependency chain

---

## 📞 QUESTIONS TO ASK USER

Before starting execution, confirm:
1. Should I fix all 29 scripts with wrong DB path, or just the critical ones?
2. Do you want batch processing (100 emails at a time) or all at once?
3. What's your OpenAI API budget for this? (~$5-10 for 3,356 emails)
4. Should I create a new script or modify existing smart_email_system.py?

---

**STATUS:** Ready for audit phase
**NEXT STEP:** Agent starts audit and creates AGENT1_AUDIT_REPORT.md

