# 📅 Agent 4: Deliverables & Scheduling System

**Wave:** 2 (Intelligence)
**Priority:** HIGH - PM workload tracking
**Status:** AWAITING AUDIT

---

## ⚠️ MANDATORY PROTOCOL

1. ✅ **READ** `.claude/MASTER_ARCHITECTURE.md`
2. ✅ **READ** `.claude/ALIGNMENT_AUDIT.md`
3. 🔍 **AUDIT** your assigned area
4. 📊 **REPORT** findings (create `AGENT4_AUDIT_REPORT.md`)
5. ⏸️ **WAIT** for user approval
6. ✅ **EXECUTE** only after approval
7. 📝 **DOCUMENT** changes

---

## 🎯 YOUR MISSION

Build deliverables detection and PM workload tracking:
- Extract deliverables from contracts and emails
- Track deadlines and submission status
- PM workload dashboard (who's working on what)
- Alert on approaching/overdue deliverables
- Link deliverables to projects and phases

**User Context:** "I want to see PM workload - who has what deliverables coming up, what's overdue"

---

## 🔍 PHASE 1: AUDIT

### Your Audit Checklist:

**1. Deliverables Table Verification**
```bash
# Check if deliverables table exists and structure
sqlite3 database/bensley_master.db ".schema deliverables"

# Check for any existing deliverable records
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM deliverables"

# Check what fields are available
sqlite3 database/bensley_master.db "PRAGMA table_info(deliverables)"
```

**Report:**
- [ ] Does `deliverables` table exist?
- [ ] What columns does it have?
- [ ] Are there any deliverable records currently?
- [ ] Schema match requirements? (deadline, status, assigned_to, submission_date, etc.)

**2. Contract/Email Content Check**
```bash
# Check if contracts have deliverable data
sqlite3 database/bensley_master.db "SELECT contract_id, deliverable_schedule FROM contract_metadata LIMIT 5"

# Check email_content for deliverable mentions
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM email_content WHERE clean_body LIKE '%deliverable%' OR clean_body LIKE '%submission%'"

# Check project phases
sqlite3 database/bensley_master.db "SELECT * FROM contract_phases LIMIT 5"
```

**Report:**
- [ ] Do contracts contain deliverable information?
- [ ] Where is deliverable data stored? (contract_metadata? separate field?)
- [ ] Can we extract from email_content?
- [ ] Are project phases linked to deliverables?

**3. PM Assignment Data**
```bash
# Check if there's PM assignment info
sqlite3 database/bensley_master.db "SELECT project_code, project_manager FROM projects WHERE project_manager IS NOT NULL LIMIT 10"

# Check for PM-related fields
grep -n "project_manager\|pm\|assigned" backend/api/main.py
```

**Report:**
- [ ] Is PM assignment data available?
- [ ] Where is it stored? (projects.project_manager?)
- [ ] Can we link deliverables to specific PMs?

**4. Deadline/Timeline Data**
```bash
# Check for timeline/deadline tables
sqlite3 database/bensley_master.db "SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%timeline%' OR name LIKE '%schedule%')"

# Check proposal_timeline
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM proposal_timeline"

# Check contract_phases for dates
sqlite3 database/bensley_master.db "SELECT phase_name, start_date, end_date FROM contract_phases LIMIT 10"
```

**Report:**
- [ ] What timeline/scheduling tables exist?
- [ ] Are phase dates populated?
- [ ] Can we derive deliverable deadlines from phases?

**5. Backend API Audit**
```bash
# Check for existing deliverable endpoints
grep -n "deliverable" backend/api/main.py

# Check PM workload endpoints
grep -n "workload\|pm" backend/api/main.py
```

**Report:**
- [ ] Are there any deliverable endpoints?
- [ ] What's implemented vs missing?
- [ ] Is there a PM workload endpoint?

---

## 📊 PHASE 2: REPORT

Create `AGENT4_AUDIT_REPORT.md` with:

**Findings:**
- Deliverables table readiness
- Contract/email data availability
- PM assignment infrastructure
- Timeline/deadline data sources

**Proposed Solution:**
- Deliverable detection approach (parse contracts? emails? both?)
- Auto-population logic vs manual entry
- PM workload calculation method
- Alert system design

**Architecture Alignment:**
- Uses existing `deliverables` table? YES/NO
- Integrates with Agent 1's email_content? HOW
- Links to contract_phases? HOW
- Backend API approach

**Questions for User:**
1. Should deliverables be auto-extracted from contracts or manually entered?
2. Who assigns deliverables to PMs? (Auto from project_manager field?)
3. What constitutes a "deliverable"? (drawings, reports, schedules, etc.)
4. Alert timing? (7 days before? 3 days before?)

---

## ⏸️ PHASE 3: AWAIT APPROVAL

---

## ✅ PHASE 4: EXECUTION

### Task 1: Deliverable Detection Logic

**File:** `deliverable_extractor.py` (new file)
```python
#!/usr/bin/env python3
"""
Deliverable Extraction from Contracts and Emails
"""
import database_config
import re
from datetime import datetime, timedelta

class DeliverableExtractor:
    DELIVERABLE_KEYWORDS = [
        r'deliverable',
        r'submission',
        r'drawings?',
        r'report',
        r'schedule',
        r'design development',
        r'construction documents?',
        r'schematic design'
    ]

    DEADLINE_PATTERNS = [
        r'due\s+(?:by|on)?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        r'deadline:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        r'submit\s+by\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s+deadline'
    ]

    def extract_from_contract(self, project_id: int, contract_text: str):
        """
        Extract deliverables from contract text
        Returns: List of (deliverable_name, deadline, phase)
        """
        deliverables = []

        # Parse contract sections for deliverable mentions
        lines = contract_text.split('\n')
        for i, line in enumerate(lines):
            for keyword in self.DELIVERABLE_KEYWORDS:
                if re.search(keyword, line, re.IGNORECASE):
                    # Look for deadline in surrounding lines
                    context = '\n'.join(lines[max(0, i-3):min(len(lines), i+4)])
                    deadline = self._extract_deadline(context)

                    deliverables.append({
                        'name': line.strip(),
                        'deadline': deadline,
                        'source': 'contract'
                    })

        return deliverables

    def extract_from_email(self, email_id: int, email_body: str):
        """
        Extract deliverable mentions from emails
        """
        deliverables = []

        # Look for deliverable + deadline patterns
        for keyword in self.DELIVERABLE_KEYWORDS:
            matches = re.finditer(keyword, email_body, re.IGNORECASE)
            for match in matches:
                start = max(0, match.start() - 100)
                end = min(len(email_body), match.end() + 100)
                context = email_body[start:end]

                deadline = self._extract_deadline(context)
                if deadline:
                    deliverables.append({
                        'name': context.strip()[:200],
                        'deadline': deadline,
                        'source': f'email_{email_id}'
                    })

        return deliverables

    def _extract_deadline(self, text: str):
        """Extract date from text"""
        for pattern in self.DEADLINE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Parse date (handle various formats)
                    date_str = match.group(1)
                    # Add date parsing logic here
                    return date_str
                except:
                    continue
        return None

    def create_deliverable(self, project_id: int, deliverable: dict):
        """Create deliverable record in database"""
        conn = database_config.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO deliverables (
                project_id,
                deliverable_name,
                deadline,
                status,
                assigned_to,
                source,
                created_at
            ) VALUES (?, ?, ?, 'pending', ?, ?, datetime('now'))
        """, (
            project_id,
            deliverable['name'],
            deliverable['deadline'],
            deliverable.get('assigned_to'),
            deliverable['source']
        ))

        deliverable_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return deliverable_id
```

### Task 2: PM Workload Calculation

**File:** `pm_workload_tracker.py` (new file)
```python
#!/usr/bin/env python3
"""
PM Workload Tracking and Calculation
"""
import database_config
from datetime import datetime, timedelta

class PMWorkloadTracker:
    def get_pm_workload(self, pm_name: str = None):
        """
        Calculate PM workload (upcoming deliverables, overdue items)
        """
        conn = database_config.get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                p.project_manager,
                COUNT(CASE WHEN d.status = 'pending' THEN 1 END) as pending_count,
                COUNT(CASE WHEN d.status = 'overdue' THEN 1 END) as overdue_count,
                COUNT(CASE WHEN date(d.deadline) BETWEEN date('now') AND date('now', '+7 days') THEN 1 END) as due_soon_count
            FROM deliverables d
            JOIN projects p ON d.project_id = p.project_id
            WHERE 1=1
        """
        params = []

        if pm_name:
            query += " AND p.project_manager = ?"
            params.append(pm_name)

        query += " GROUP BY p.project_manager"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_upcoming_deliverables(self, pm_name: str = None, days_ahead: int = 30):
        """Get deliverables coming up in next N days"""
        conn = database_config.get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                d.deliverable_id,
                d.deliverable_name,
                d.deadline,
                d.status,
                p.project_code,
                p.project_title,
                p.project_manager,
                julianday(d.deadline) - julianday('now') as days_until_due
            FROM deliverables d
            JOIN projects p ON d.project_id = p.project_id
            WHERE d.status IN ('pending', 'in_progress')
            AND date(d.deadline) BETWEEN date('now') AND date('now', '+' || ? || ' days')
        """
        params = [days_ahead]

        if pm_name:
            query += " AND p.project_manager = ?"
            params.append(pm_name)

        query += " ORDER BY d.deadline ASC"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
```

### Task 3: Backend Deliverables APIs

**File:** `backend/api/main.py` (add endpoints)

```python
@app.get("/api/deliverables")
async def get_deliverables(
    status: str = None,
    project_code: str = None,
    pm_name: str = None
):
    """Get deliverables with optional filters"""
    query = """
        SELECT
            d.deliverable_id,
            d.deliverable_name,
            d.deadline,
            d.status,
            d.submission_date,
            d.assigned_to,
            p.project_code,
            p.project_title,
            p.project_manager
        FROM deliverables d
        JOIN projects p ON d.project_id = p.project_id
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND d.status = ?"
        params.append(status)

    if project_code:
        query += " AND p.project_code = ?"
        params.append(project_code)

    if pm_name:
        query += " AND p.project_manager = ?"
        params.append(pm_name)

    query += " ORDER BY d.deadline ASC"

    cursor.execute(query, params)
    return {"deliverables": [dict(row) for row in cursor.fetchall()]}

@app.get("/api/deliverables/overdue")
async def get_overdue_deliverables():
    """Get overdue deliverables"""
    cursor.execute("""
        SELECT
            d.*,
            p.project_code,
            p.project_title,
            p.project_manager,
            julianday('now') - julianday(d.deadline) as days_overdue
        FROM deliverables d
        JOIN projects p ON d.project_id = p.project_id
        WHERE d.status IN ('pending', 'in_progress')
        AND date(d.deadline) < date('now')
        ORDER BY days_overdue DESC
    """)
    return {"overdue_deliverables": [dict(row) for row in cursor.fetchall()]}

@app.get("/api/pm-workload")
async def get_pm_workload(pm_name: str = None):
    """Get PM workload summary"""
    from pm_workload_tracker import PMWorkloadTracker
    tracker = PMWorkloadTracker()
    workload = tracker.get_pm_workload(pm_name)
    upcoming = tracker.get_upcoming_deliverables(pm_name, days_ahead=30)

    return {
        "workload_summary": workload,
        "upcoming_deliverables": upcoming
    }

@app.put("/api/deliverables/{deliverable_id}/submit")
async def submit_deliverable(deliverable_id: int, submission: dict):
    """Mark deliverable as submitted"""
    cursor.execute("""
        UPDATE deliverables
        SET status = 'submitted',
            submission_date = datetime('now'),
            submission_notes = ?
        WHERE deliverable_id = ?
    """, (submission.get('notes'), deliverable_id))
    conn.commit()
    return {"success": True}
```

### Task 4: Frontend PM Workload Dashboard

**File:** `frontend/src/app/(dashboard)/deliverables/page.tsx`
```tsx
'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export default function DeliverablesPage() {
  const { data: workload } = useQuery({
    queryKey: ['pm-workload'],
    queryFn: () => api.getPMWorkload()
  })

  const { data: overdue } = useQuery({
    queryKey: ['deliverables-overdue'],
    queryFn: () => api.getOverdueDeliverables()
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">PM Workload & Deliverables</h1>

      {/* PM Workload Summary */}
      <PMWorkloadSummary data={workload?.workload_summary} />

      {/* Overdue Alert */}
      {overdue?.overdue_deliverables?.length > 0 && (
        <OverdueAlert deliverables={overdue.overdue_deliverables} />
      )}

      {/* Upcoming Deliverables Timeline */}
      <UpcomingDeliverables data={workload?.upcoming_deliverables} />
    </div>
  )
}
```

### Task 5: Test Deliverable Detection
```bash
# Run deliverable extractor on existing contracts
python3 deliverable_extractor.py

# Check created deliverables
sqlite3 database/bensley_master.db "SELECT * FROM deliverables ORDER BY deadline ASC LIMIT 10"

# Test API
curl http://localhost:8000/api/deliverables
curl http://localhost:8000/api/deliverables/overdue
curl http://localhost:8000/api/pm-workload
```

---

## 📝 PHASE 5: DOCUMENTATION

Update MASTER_ARCHITECTURE.md, create completion report.

---

## 🤝 COORDINATION

**You need from Agent 1:**
- ✅ CRITICAL: email_content table populated (for extracting deliverables from emails)

**You need from Agent 2:**
- Project data with PM assignments

**You provide to others:**
- Deliverable tracking system
- PM workload data
- Can be extended for other deadline types

---

## 🚫 WHAT NOT TO DO

- DON'T create new deliverables table (exists!)
- DON'T build separate contract parser if one exists
- DON'T skip dependency check on Agent 1

---

**STATUS:** Ready for audit
**DEPENDENCY:** Agent 1 must complete email content extraction first
