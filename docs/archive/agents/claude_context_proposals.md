# CLAUDE 4: PROPOSALS TRACKER CONTEXT
**Role:** Proposals Pipeline Specialist
**Priority:** MEDIUM (Pipeline visibility important)
**Estimated Time:** 6-8 hours

---

## 🎯 YOUR MISSION

Build the **proposals tracker** that helps Bill and the BD team manage the sales pipeline. Track:

1. **Proposal Pipeline** by status (Sent, Follow-up, Won, Lost)
2. **Proposal Health** indicators (last contact, response rate)
3. **Email Intelligence** integration (after Claude 1)
4. **Win/Loss Analysis** charts
5. **Weekly Reports** (automated proposal tracking)

---

## 🏗️ ARCHITECTURE CONTEXT

```
[Database: 87 proposals]
            ↓
[Your Backend API]
            ↓
[Frontend Components]
   ├─ Pipeline View (Kanban or list)
   ├─ Proposal Detail
   ├─ Win/Loss Charts
   └─ Email Follow-ups (needs Claude 1)
            ↓
[Claude 5: Reuses your pipeline widget]
```

**Proposals → Projects Lifecycle:**
```
Proposal Sent → Follow-ups → Won → Active Project → Invoicing → Complete
```

---

## 📚 FILES TO READ FIRST

**Must Read:**
1. `BENSLEY_OPERATIONS_PLATFORM_FORWARD_PLAN.md`
2. `PROPOSAL_TRACKER_GUIDE.md` (if exists in root)
3. Database schema: `proposals`, `proposal_tracker` tables
4. `backend/services/proposal_service.py` (existing service)
5. `backend/services/proposal_tracker_service.py`

**Proposals Schema:**
```sql
CREATE TABLE proposals (
    proposal_id INTEGER PRIMARY KEY,
    project_code TEXT UNIQUE,
    project_name TEXT,
    client_name TEXT,
    status TEXT,  -- 'sent', 'follow_up', 'won', 'lost', 'active'
    sent_date DATE,
    value_usd REAL,
    contact_person TEXT,
    last_contact_date DATE,
    active_project_id INTEGER
);

CREATE TABLE proposal_tracker (
    tracker_id INTEGER PRIMARY KEY,
    proposal_id INTEGER,
    action TEXT,  -- 'sent', 'follow_up', 'won', 'lost'
    action_date DATE,
    notes TEXT
);

-- Current Data:
-- 87 proposals total
-- Status breakdown: sent (20), follow_up (15), won (30), lost (22)
```

---

## 🛠️ FILES TO CREATE/MODIFY

### Backend

#### 1. `backend/services/proposal_pipeline_service.py` (NEW FILE)
```python
class ProposalPipelineService:
    def get_pipeline_summary(self):
        """Count by status: sent, follow_up, won, lost"""

    def get_proposals_by_status(self, status: str):
        """Filter proposals by status"""

    def get_proposal_health(self, proposal_id: int):
        """
        Returns:
        - Days since last contact
        - Follow-up count
        - Health score (0-100)
        """

    def get_win_loss_stats(self):
        """
        Win rate, average deal size, time to close
        """

    def get_stale_proposals(self, days_threshold=30):
        """Proposals with no activity in X days"""
```

#### 2. `backend/api/main.py` (ADD ENDPOINTS)
```python
@app.get("/api/proposals/pipeline")
async def get_proposal_pipeline()

@app.get("/api/proposals/status/{status}")
async def get_proposals_by_status(status: str)

@app.get("/api/proposals/{id}/health")
async def get_proposal_health(id: int)

@app.get("/api/proposals/stats/win-loss")
async def get_win_loss_stats()

@app.get("/api/proposals/stale")
async def get_stale_proposals(days: int = 30)
```

### Frontend

#### 3. `frontend/src/app/(dashboard)/proposals/page.tsx` (NEW FILE)
Main proposals page with:
- Pipeline summary cards (Sent, Follow-up, Won, Lost)
- Proposals list/kanban view
- Filter by status
- Search by project code or client
- Health indicators (🟢🟡🔴)

#### 4. `frontend/src/components/proposals/proposal-pipeline-widget.tsx` (NEW FILE)
Reusable widget for overview dashboard:
```typescript
export function ProposalPipelineWidget({ compact = false }) {
  // Shows pipeline summary
  // Sent: 20 | Follow-up: 15 | Won: 30 | Lost: 22
  // Bar chart or card grid
}
```

#### 5. `frontend/src/app/(dashboard)/proposals/[id]/page.tsx` (NEW FILE)
Proposal detail:
- Proposal info (client, value, status)
- Timeline (sent, follow-ups, won/lost)
- Related emails (after Claude 1)
- Actions: Update status, add note, mark won/lost

---

## ✅ YOUR TASKS (Checklist)

### Phase 1: Pipeline Backend
- [ ] Create `proposal_pipeline_service.py`
- [ ] Add pipeline endpoints to main.py
- [ ] Calculate proposal health scores
- [ ] Win/loss statistics

### Phase 2: Proposals List Page
- [ ] Create `/proposals` page
- [ ] Pipeline summary cards at top
- [ ] Proposals list with status badges
- [ ] Filter and search
- [ ] Health indicators

### Phase 3: Proposal Detail Page
- [ ] Create `/proposals/[id]` page
- [ ] Proposal header (code, client, value, status)
- [ ] Timeline of actions
- [ ] Update status form
- [ ] Add notes functionality

### Phase 4: Pipeline Widget (For Claude 5)
- [ ] Create `proposal-pipeline-widget.tsx`
- [ ] Compact mode for overview
- [ ] Full mode for proposals page
- [ ] Make reusable (export as component)

### Phase 5: Email Integration (After Claude 1)
- [ ] Wait for Claude 1 "Email API ready" signal
- [ ] Integrate `/api/emails/proposal/{id}`
- [ ] Show related emails on detail page
- [ ] Auto-update last_contact_date from emails

---

## 🔗 DEPENDENCIES

### You Depend On
**Claude 1 (Emails):** For email intelligence
- Workaround: Build proposal UI first (no dependency)
- When ready: Integrate email follow-ups

### Others Depend On You
**Claude 5 (Overview):** Will use your pipeline widget
- Export: `<ProposalPipelineWidget compact={true} />`
- Signal when ready

---

## 🎨 UI MOCKUP

```
┌─────────────────────────────────────────────────────────────┐
│  📝 Proposals Pipeline                                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┬──────────┬──────────┬──────────┐             │
│  │  Sent    │ Follow-up│   Won    │   Lost   │             │
│  │    20    │    15    │    30    │    22    │             │
│  │ $5.2M    │ $3.8M    │ $12.4M   │ $4.1M    │             │
│  └──────────┴──────────┴──────────┴──────────┘             │
├─────────────────────────────────────────────────────────────┤
│  🔍 [Search] [Status ▼] [Client ▼]                         │
├─────────────────────────────────────────────────────────────┤
│  🟢 BK-068 Wellness Resort Grenada        $450K   Sent     │
│     Last contact: 5 days ago                                │
│                                                             │
│  🟡 BK-072 Bodrum Additional Services     $320K   Follow-up│
│     Last contact: 18 days ago - NEEDS FOLLOW UP            │
│                                                             │
│  🔴 BK-051 Pawana Lake Mumbai            $680K   Lost      │
│     Lost to competitor - 45 days ago                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 SUCCESS METRICS

**You're successful when:**
1. ✅ Pipeline shows accurate status breakdown
2. ✅ Health indicators show stale proposals
3. ✅ Win/loss stats calculate correctly
4. ✅ Proposal detail shows full timeline
5. ✅ Email integration works (after Claude 1)
6. ✅ Pipeline widget reusable (Claude 5)

**User Impact:**
- Bill sees pipeline at a glance
- BD team knows which proposals need follow-up
- Win/loss analysis improves future proposals

---

## 🚀 READY TO START?

1. Read proposal schemas
2. Update COORDINATION_MASTER.md
3. Build pipeline backend
4. Create proposals list page
5. Add email intelligence when Claude 1 ready
6. Make widget reusable for Claude 5!

**Help Bill close more deals!** 🎯📈
