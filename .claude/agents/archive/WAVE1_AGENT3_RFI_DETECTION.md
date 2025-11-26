# 🎯 Agent 3: RFI Detection & Tracking System

**Wave:** 1 (Foundation)
**Priority:** HIGH - User setting up rfi@bensley.com
**Status:** AWAITING AUDIT

---

## ⚠️ MANDATORY PROTOCOL

1. ✅ **READ** `.claude/MASTER_ARCHITECTURE.md`
2. ✅ **READ** `.claude/ALIGNMENT_AUDIT.md`
3. 🔍 **AUDIT** your assigned area
4. 📊 **REPORT** findings (create `AGENT3_AUDIT_REPORT.md`)
5. ⏸️ **WAIT** for user approval
6. ✅ **EXECUTE** only after approval
7. 📝 **DOCUMENT** changes

---

## 🎯 YOUR MISSION

Build RFI detection and tracking system:
- Auto-detect RFI requests from emails
- Track RFI status (open, assigned, responded, closed)
- Alert on overdue RFIs
- Link RFIs to projects and emails
- Dashboard for PM workload

**User Context:** "In our contracts it will say: If your RFI request isn't sent to rfi@bensley.com, you can't be mad at us for missing it."

---

## 🔍 PHASE 1: AUDIT

### Your Audit Checklist:

**1. RFI Table Verification**
```bash
# Check if rfis table exists and its structure
sqlite3 database/bensley_master.db ".schema rfis"

# Check for any existing RFI records
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM rfis"

# Check email_project_links for potential RFIs
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM email_project_links"
```

**Report:**
- [ ] Does `rfis` table exist?
- [ ] What columns does it have?
- [ ] Are there any RFI records currently?
- [ ] What's the schema - does it match requirements?

**2. Email Categorization Check**
```bash
# Check if smart_email_system already detects RFIs
grep -n "rfi\|RFI" smart_email_system.py

# Check email_content for RFI categories
sqlite3 database/bensley_master.db "SELECT category, COUNT(*) FROM email_content GROUP BY category"
```

**Report:**
- [ ] Does smart_email_system already detect RFIs?
- [ ] What email categories exist?
- [ ] Is there an "rfi_request" category?
- [ ] What RFI detection logic exists?

**3. Backend API Audit**
```bash
# Check for existing RFI endpoints
grep -n "rfi\|RFI" backend/api/main.py

# Check what's available
grep -B 5 -A 10 "def.*rfi" backend/api/main.py
```

**Report:**
- [ ] Are there any RFI endpoints?
- [ ] What's implemented vs missing?
- [ ] Is there an RFI dashboard endpoint?

**4. Email Routing Check**
```bash
# Check if rfi@bensley.com email exists
# Check email import scripts for folder handling
grep -n "folder\|mailbox" import_all_emails.py smart_email_system.py
```

**Report:**
- [ ] Is rfi@bensley.com set up in email system?
- [ ] How are emails currently imported?
- [ ] Can we route specific folders/addresses?

**5. AI Detection Capabilities**
```bash
# Check what AI analysis is currently done
grep -A 20 "openai\|analyze" smart_email_system.py
```

**Report:**
- [ ] Is AI categorization working?
- [ ] What prompts are used?
- [ ] Can we add RFI detection keywords?

---

## 📊 PHASE 2: REPORT

Create `AGENT3_AUDIT_REPORT.md` with:

**Findings:**
- RFI table readiness
- Email detection capabilities
- API gaps
- Integration points with Agent 1 (email brain)

**Proposed Solution:**
- RFI detection keywords/patterns
- Auto-creation logic
- Assignment rules (link to project PMs)
- Alert system

**Architecture Alignment:**
- Uses existing `rfis` table? YES/NO
- Integrates with Agent 1's email_content? HOW
- Backend API approach
- Frontend dashboard approach

**Questions for User:**
1. Who should RFIs be auto-assigned to? (Project PM? You? Bill?)
2. What's the SLA for RFI response? (24hrs? 48hrs?)
3. Should we email alert on new RFIs?
4. Keywords that indicate RFI: "request", "clarification", "question", etc.?

---

## ⏸️ PHASE 3: AWAIT APPROVAL

---

## ✅ PHASE 4: EXECUTION

### Task 1: RFI Detection Logic

**File:** `rfi_detector.py` (new file)
```python
#!/usr/bin/env python3
"""
RFI Detection from Email Content
"""
import database_config
import re
from datetime import datetime

class RFIDetector:
    RFI_KEYWORDS = [
        r'\brfi\b',
        r'request for information',
        r'clarification needed',
        r'please clarify',
        r'can you provide',
        r'need information',
        r'urgent question',
        r'require clarification'
    ]

    RFI_SUBJECT_PATTERNS = [
        r'^rfi',
        r'\[rfi\]',
        r'request.*information',
        r'clarification.*needed'
    ]

    def detect_rfi(self, email_id: int, email_content: dict, email_meta: dict):
        """
        Detect if email is an RFI request
        Returns: (is_rfi: bool, confidence: float, category: str)
        """
        subject = email_meta.get('subject', '').lower()
        body = email_content.get('clean_body', '').lower()

        # Check subject line
        for pattern in self.RFI_SUBJECT_PATTERNS:
            if re.search(pattern, subject, re.IGNORECASE):
                return (True, 0.95, 'explicit_rfi')

        # Check from rfi@bensley.com
        if 'rfi@bensley.com' in email_meta.get('to', '').lower():
            return (True, 0.90, 'rfi_address')

        # Check body content for keywords
        keyword_matches = 0
        for pattern in self.RFI_KEYWORDS:
            if re.search(pattern, body, re.IGNORECASE):
                keyword_matches += 1

        if keyword_matches >= 2:
            return (True, 0.75, 'keyword_match')

        # Check for question marks + project reference
        if body.count('?') >= 2 and email_content.get('project_code'):
            return (True, 0.60, 'question_pattern')

        return (False, 0.0, None)

    def create_rfi_from_email(self, email_id: int, project_id: int, category: str):
        """Create RFI record from detected email"""
        conn = database_config.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO rfis (
                email_id,
                project_id,
                category,
                priority,
                status,
                detected_at,
                due_date
            ) VALUES (?, ?, ?, 'medium', 'open', datetime('now'), date('now', '+48 hours'))
        """, (email_id, project_id, category))

        rfi_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return rfi_id
```

### Task 2: Integrate with Email Processing

**File:** Modify `smart_email_system.py` (add RFI detection)
```python
# Add to _handle_ai_analysis method
def _handle_ai_analysis(self, email_id, analysis, context):
    # Existing code...

    # NEW: RFI Detection
    if context.get('projects'):
        from rfi_detector import RFIDetector
        detector = RFIDetector()

        is_rfi, confidence, category = detector.detect_rfi(
            email_id,
            {'clean_body': email['body']},
            {'subject': email['subject'], 'to': email['to']}
        )

        if is_rfi and confidence > 0.70:
            print(f"   🎯 RFI detected (confidence: {confidence*100:.0f}%)")
            rfi_id = detector.create_rfi_from_email(
                email_id,
                context['projects'][0]['project_id'],
                category
            )
            print(f"   ✅ Created RFI #{rfi_id}")
```

### Task 3: Backend RFI APIs

**File:** `backend/api/main.py` (add endpoints)

```python
@app.get("/api/rfis")
async def get_rfis(status: str = None, project_code: str = None):
    """Get RFIs with optional filters"""
    query = """
        SELECT
            r.rfi_id,
            r.status,
            r.priority,
            r.category,
            r.due_date,
            r.detected_at,
            r.responded_at,
            p.project_code,
            p.project_title,
            e.subject as email_subject,
            e.sender_email
        FROM rfis r
        JOIN projects p ON r.project_id = p.project_id
        JOIN emails e ON r.email_id = e.email_id
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND r.status = ?"
        params.append(status)

    if project_code:
        query += " AND p.project_code = ?"
        params.append(project_code)

    query += " ORDER BY r.due_date ASC"

    cursor.execute(query, params)
    return {"rfis": [dict(row) for row in cursor.fetchall()]}

@app.get("/api/rfis/overdue")
async def get_overdue_rfis():
    """Get RFIs past due date"""
    cursor.execute("""
        SELECT
            r.*,
            p.project_code,
            p.project_title,
            julianday('now') - julianday(r.due_date) as days_overdue
        FROM rfis r
        JOIN projects p ON r.project_id = p.project_id
        WHERE r.status IN ('open', 'assigned')
        AND date(r.due_date) < date('now')
        ORDER BY days_overdue DESC
    """)
    return {"overdue_rfis": [dict(row) for row in cursor.fetchall()]}

@app.put("/api/rfis/{rfi_id}/respond")
async def respond_to_rfi(rfi_id: int, response: dict):
    """Mark RFI as responded"""
    cursor.execute("""
        UPDATE rfis
        SET status = 'responded',
            responded_at = datetime('now'),
            response_summary = ?
        WHERE rfi_id = ?
    """, (response.get('summary'), rfi_id))
    conn.commit()
    return {"success": True}
```

### Task 4: Frontend RFI Dashboard

**File:** `frontend/src/app/(dashboard)/rfis/page.tsx`
```tsx
export default function RFIDashboard() {
  const { data: rfis } = useQuery({
    queryKey: ['rfis'],
    queryFn: () => api.getRFIs()
  })

  const { data: overdue } = useQuery({
    queryKey: ['rfis-overdue'],
    queryFn: () => api.getOverdueRFIs()
  })

  return (
    <div>
      <RFIStats rfis={rfis} overdue={overdue} />
      <OverdueAlert rfis={overdue} />
      <RFITable rfis={rfis} />
    </div>
  )
}
```

### Task 5: Test RFI Detection
```bash
# Run RFI detector on existing emails
python3 rfi_detector.py

# Check created RFIs
sqlite3 database/bensley_master.db "SELECT * FROM rfis ORDER BY detected_at DESC LIMIT 10"

# Test API
curl http://localhost:8000/api/rfis
curl http://localhost:8000/api/rfis/overdue
```

---

## 📝 PHASE 5: DOCUMENTATION

Update MASTER_ARCHITECTURE.md, create completion report.

---

## 🤝 COORDINATION

**You need from Agent 1:**
- ✅ CRITICAL: email_content table populated with body text
- ✅ Email categorization working

**You provide to others:**
- RFI detection working
- RFI API endpoints available
- Can be extended for other detection types

---

## 🚫 WHAT NOT TO DO

- DON'T create new rfis table (exists!)
- DON'T build separate email importer
- DON'T skip dependency check on Agent 1

---

**STATUS:** Ready for audit
**DEPENDENCY:** Agent 1 must complete email content extraction first
