# 📊 Agent 2: Proposal Lifecycle & Status Tracking

**Wave:** 1 (Foundation)
**Priority:** HIGH - User's #1 priority
**Status:** AWAITING AUDIT

---

## ⚠️ MANDATORY PROTOCOL

1. ✅ **READ** `.claude/MASTER_ARCHITECTURE.md`
2. ✅ **READ** `.claude/ALIGNMENT_AUDIT.md`
3. 🔍 **AUDIT** your assigned area
4. 📊 **REPORT** findings (create `AGENT2_AUDIT_REPORT.md`)
5. ⏸️ **WAIT** for user approval
6. ✅ **EXECUTE** only after approval
7. 📝 **DOCUMENT** changes

---

## 🎯 YOUR MISSION

Build proposal lifecycle tracking so user can see:
- Complete proposal history (first contact → drafting → sent → signed)
- Who changed what and when
- Days in each status
- Email thread context
- Quick status updates

**User Quote:** "I want to join meetings, talk to clients, and the AI organizes it all by project. I can say 'Hey, what was happening with this project?' and see the history."

---

## 🔍 PHASE 1: AUDIT

### Your Audit Checklist:

**1. Existing Schema Verification**
```bash
# Check if proposal_status_history exists
sqlite3 database/bensley_master.db ".schema proposal_status_history"

# Check current proposal data
sqlite3 database/bensley_master.db "SELECT project_code, current_status, days_in_current_status FROM proposals LIMIT 5"

# Check for any existing history records
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM proposal_status_history"
```

**Report:**
- [ ] Does `proposal_status_history` table exist?
- [ ] What columns does it have?
- [ ] Are there any history records currently?
- [ ] Does proposals table have `current_status` field?

**2. Backend API Audit**
```bash
# Check existing proposal endpoints
grep -n "proposals" backend/api/main.py | grep "def"

# Check what data is returned
grep -A 20 "@app.get.*proposals" backend/api/main.py | head -30
```

**Report:**
- [ ] What proposal endpoints exist?
- [ ] Do they return status_history?
- [ ] Is there a status update endpoint?
- [ ] What's missing?

**3. Frontend Components Audit**
```bash
# Check proposal frontend files
ls -lh frontend/src/app/\(dashboard\)/proposals/
ls -lh frontend/src/components/proposals/

# Check what proposal data is being used
grep -r "current_status\|status_history" frontend/src/components/proposals/
```

**Report:**
- [ ] What proposal UI components exist?
- [ ] Do they show status history?
- [ ] Is there a timeline view?
- [ ] What needs to be built?

**4. Status Change Tracking**
```bash
# Check if there's any automatic tracking
grep -n "UPDATE proposals SET.*status" *.py backend/api/main.py

# Check for triggers
sqlite3 database/bensley_master.db "SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='proposals'"
```

**Report:**
- [ ] Is status tracking automatic or manual?
- [ ] Are there database triggers?
- [ ] How are status changes currently captured?

**5. Dependency Check**
```bash
# Check proposal import scripts
ls -lh import_proposal*.py

# Verify recent import worked
sqlite3 database/bensley_master.db "SELECT COUNT(*), current_status FROM proposals GROUP BY current_status"
```

**Report:**
- [ ] Recent import successful? (77 proposals imported?)
- [ ] Status distribution correct? (On Hold: 33, Sent: 19, etc.)
- [ ] Is proposal data clean?

---

## 📊 PHASE 2: REPORT

Create `AGENT2_AUDIT_REPORT.md` with:

**Findings:**
- Existing infrastructure assessment
- What's working vs what's broken
- Backend API gaps
- Frontend UI gaps

**Proposed Solution:**
- Database changes needed (if any)
- Backend endpoints to create
- Frontend components to build
- Integration approach

**Architecture Alignment:**
- Uses existing `proposal_status_history` table? YES/NO
- Extends existing APIs? YES/NO
- Integrates with email system? HOW
- Conflicts with other agents? NONE/[DESCRIBE]

**Questions for User:**
1. Should status changes be automatic (via trigger) or manual (via API)?
2. Do you want email notifications when status changes?
3. Should AI auto-detect status from emails ("proposal sent" in subject)?

---

## ⏸️ PHASE 3: AWAIT APPROVAL

Present findings, get approval, answer questions.

---

## ✅ PHASE 4: EXECUTION

### Task 1: Backend - Status History API

**File:** `backend/api/main.py` (extend existing endpoints)

**Add endpoint:** `/api/proposals/{code}/history` (GET)
```python
@app.get("/api/proposals/{code}/history")
async def get_proposal_history(code: str):
    """Get complete status change history for a proposal"""
    cursor.execute("""
        SELECT
            h.history_id,
            h.old_status,
            h.new_status,
            h.changed_at,
            h.changed_by,
            h.notes,
            h.source
        FROM proposal_status_history h
        JOIN proposals p ON h.proposal_id = p.proposal_id
        WHERE p.project_code = ?
        ORDER BY h.changed_at DESC
    """, (code,))
    return {"history": [dict(row) for row in cursor.fetchall()]}
```

**Add endpoint:** `/api/proposals/{code}/status` (PUT)
```python
@app.put("/api/proposals/{code}/status")
async def update_proposal_status(
    code: str,
    status_update: dict  # {new_status, changed_by, notes}
):
    """Update proposal status and log to history"""
    # Get current status
    cursor.execute("SELECT proposal_id, current_status FROM proposals WHERE project_code = ?", (code,))
    proposal = cursor.fetchone()

    # Insert history record
    cursor.execute("""
        INSERT INTO proposal_status_history (
            proposal_id, old_status, new_status,
            changed_by, notes, source, changed_at
        ) VALUES (?, ?, ?, ?, ?, 'manual', datetime('now'))
    """, (
        proposal['proposal_id'],
        proposal['current_status'],
        status_update['new_status'],
        status_update['changed_by'],
        status_update.get('notes', '')
    ))

    # Update proposal
    cursor.execute("""
        UPDATE proposals
        SET current_status = ?,
            status_changed_at = datetime('now'),
            days_in_current_status = 0
        WHERE project_code = ?
    """, (status_update['new_status'], code))

    conn.commit()
    return {"success": True}
```

### Task 2: Frontend - Proposal Detail Page

**File:** `frontend/src/app/(dashboard)/proposals/[code]/page.tsx`

```tsx
export default function ProposalDetailPage({ params }: { params: { code: string } }) {
  const { data: proposal } = useQuery({
    queryKey: ['proposal', params.code],
    queryFn: () => api.getProposal(params.code)
  })

  const { data: history } = useQuery({
    queryKey: ['proposal-history', params.code],
    queryFn: () => api.getProposalHistory(params.code)
  })

  return (
    <div>
      <ProposalHeader proposal={proposal} />
      <StatusTimeline history={history} />
      <LinkedEmails projectCode={params.code} />
      <QuickStatusUpdate proposal={proposal} />
    </div>
  )
}
```

**Component:** `StatusTimeline.tsx`
```tsx
function StatusTimeline({ history }: { history: StatusHistory[] }) {
  return (
    <div className="space-y-4">
      {history.map((item) => (
        <div key={item.history_id} className="flex gap-4 border-l-2 pl-4">
          <div>
            <Badge>{item.new_status}</Badge>
            <p className="text-sm text-gray-500">{item.changed_at}</p>
            <p className="text-sm">by {item.changed_by}</p>
            {item.notes && <p className="text-sm mt-2">{item.notes}</p>}
          </div>
        </div>
      ))}
    </div>
  )
}
```

### Task 3: Auto-Tracking via Trigger (Optional)

**Migration:** `database/migrations/035_proposal_auto_tracking.sql`
```sql
-- Trigger to automatically log status changes
CREATE TRIGGER IF NOT EXISTS log_proposal_status_change
AFTER UPDATE OF current_status ON proposals
FOR EACH ROW
WHEN OLD.current_status != NEW.current_status
BEGIN
    INSERT INTO proposal_status_history (
        proposal_id, old_status, new_status,
        changed_at, source
    ) VALUES (
        NEW.proposal_id,
        OLD.current_status,
        NEW.current_status,
        datetime('now'),
        'auto'
    );
END;
```

### Task 4: Testing
```bash
# Test history endpoint
curl http://localhost:8000/api/proposals/25%20BK-001/history

# Test status update
curl -X PUT http://localhost:8000/api/proposals/25%20BK-001/status \
  -H "Content-Type: application/json" \
  -d '{"new_status": "Proposal Sent", "changed_by": "user", "notes": "Sent via email"}'

# Verify history was logged
sqlite3 database/bensley_master.db "SELECT * FROM proposal_status_history ORDER BY changed_at DESC LIMIT 5"
```

---

## 📝 PHASE 5: DOCUMENTATION

Update:
- `MASTER_ARCHITECTURE.md` - Add new endpoints
- Create `AGENT2_COMPLETION_REPORT.md`
- Document API endpoints for other agents

---

## 🤝 COORDINATION

**You need from Agent 1:**
- Email content populated (to link emails to proposals)

**You provide to Agent 3:**
- Status history available
- Proposal detail API working

**Potential conflicts:**
- None if using existing tables

---

## 🚫 WHAT NOT TO DO

- DON'T create a new proposal_status_history table (it exists!)
- DON'T replace existing proposal endpoints
- DON'T build a separate frontend app
- DON'T skip the audit phase

---

**STATUS:** Ready for audit
**NEXT:** Agent creates AGENT2_AUDIT_REPORT.md
