# CLAUDE 3: ACTIVE PROJECTS CONTEXT
**Role:** Active Projects Dashboard Specialist
**Priority:** HIGH (Invoice aging widget is critical!)
**Estimated Time:** 6-8 hours

---

## 🎯 YOUR MISSION

Build the **Active Projects dashboard** with the **invoice aging widget** as your #1 priority. This dashboard shows:

1. **Invoice Aging Widget FIRST** (user's top request):
   - Last 5 paid invoices (newest ones)
   - Largest outstanding invoices
   - Aging breakdown: <30 days, 30-90 days, >90 days
   - Bar chart visualization

2. **Project List** with status indicators
3. **Project Detail** view with timeline, team, milestones
4. **Activity Feed** (after Claude 1 completes email API)

---

## 🏗️ ARCHITECTURE CONTEXT

```
[Database: 51 projects, 253 invoices]
            ↓
[Your Backend API]
            ↓
[Frontend Components]
   ├─ Invoice Aging Widget (Priority 1!)
   ├─ Projects List
   ├─ Project Detail
   └─ Activity Feed (needs Claude 1 email API)
            ↓
[Claude 5: Reuses your invoice widget in overview]
```

---

## 📚 FILES TO READ FIRST

**Must Read:**
1. `BENSLEY_OPERATIONS_PLATFORM_FORWARD_PLAN.md` - Vision
2. `COORDINATION_MASTER.md` - Dependencies
3. Database schema for `invoices` and `projects` tables
4. `frontend/src/components/dashboard/invoice-aging-widget.tsx` (if exists - reference)

**Invoice Data Structure:**
```sql
CREATE TABLE invoices (
    invoice_id INTEGER PRIMARY KEY,
    project_id INTEGER,
    invoice_number TEXT,
    invoice_date DATE,
    due_date DATE,
    invoice_amount REAL,
    payment_amount REAL,
    payment_date DATE,
    status TEXT  -- 'paid', 'unpaid', 'overdue'
);

-- Current Data:
-- 253 invoices: 199 paid, 54 unpaid
-- Outstanding: $4.4M
```

---

## 🛠️ FILES TO CREATE/MODIFY

### Backend

#### 1. `backend/services/invoice_aging_service.py` (NEW FILE)
```python
class InvoiceAgingService:
    def get_recent_paid_invoices(self, limit=5):
        """Last 5 paid invoices, newest first"""

    def get_largest_outstanding_invoices(self, limit=10):
        """Top 10 unpaid by amount"""

    def get_aging_breakdown(self):
        """
        Returns:
        {
            "under_30": {"count": 15, "amount": 1200000},
            "30_to_90": {"count": 25, "amount": 2100000},
            "over_90": {"count": 14, "amount": 1100000}
        }
        """

    def get_invoice_aging_data(self):
        """Complete widget data"""
```

#### 2. `backend/api/main.py` (ADD ENDPOINTS)
```python
@app.get("/api/invoices/aging")
async def get_invoice_aging()

@app.get("/api/invoices/recent-paid")
async def get_recent_paid_invoices(limit: int = 5)

@app.get("/api/invoices/largest-outstanding")
async def get_largest_outstanding(limit: int = 10)

@app.get("/api/projects/active")
async def get_active_projects()

@app.get("/api/projects/{code}")
async def get_project_detail(code: str)

@app.get("/api/projects/{code}/timeline")
async def get_project_timeline(code: str)
```

### Frontend

#### 3. `frontend/src/components/projects/invoice-aging-widget.tsx` (NEW FILE - Priority 1!)
**THIS IS YOUR #1 TASK!** User specifically requested this.

```typescript
export function InvoiceAgingWidget() {
  const { data: agingData } = useQuery({
    queryKey: ['invoice-aging'],
    queryFn: () => api.getInvoiceAging(),
  });

  return (
    <div className="space-y-6">
      {/* Last 5 Paid Invoices */}
      <section>
        <h3>Recently Paid (Last 5)</h3>
        <ul>{agingData.recentPaid.map(...)}</ul>
      </section>

      {/* Largest Outstanding */}
      <section>
        <h3>Largest Outstanding</h3>
        <ul>{agingData.largestOutstanding.map(...)}</ul>
      </section>

      {/* Aging Breakdown with Bar Chart */}
      <section>
        <h3>Aging Breakdown</h3>
        <BarChart data={agingData.ageingBreakdown}>
          <Bar dataKey="count" fill="#3B82F6" />
          <Bar dataKey="amount" fill="#10B981" />
        </BarChart>

        <div className="grid grid-cols-3 gap-4">
          <AgingCard
            label="< 30 Days"
            count={15}
            amount="$1.2M"
            color="green"
          />
          <AgingCard
            label="30-90 Days"
            count={25}
            amount="$2.1M"
            color="yellow"
          />
          <AgingCard
            label="> 90 Days"
            count={14}
            amount="$1.1M"
            color="red"
          />
        </div>
      </section>
    </div>
  );
}
```

#### 4. `frontend/src/app/(dashboard)/projects/page.tsx` (NEW FILE)
Main projects page with:
- Invoice aging widget at top
- Project list with filters
- Status indicators (Active, On Hold, Completed)
- Search by project code or name

#### 5. `frontend/src/app/(dashboard)/projects/[code]/page.tsx` (NEW FILE)
Project detail page:
- Project header (code, name, client, status)
- Timeline/milestones
- Team members
- Related invoices
- Activity feed (emails, documents)

---

## ✅ YOUR TASKS (Checklist)

### Phase 1: Invoice Aging Backend (DO THIS FIRST!) ⚡
- [ ] Create `invoice_aging_service.py` with all methods
- [ ] Add `/api/invoices/aging` endpoint
- [ ] Test endpoint returns correct data
- [ ] Calculate days overdue (today - due_date)
- [ ] Categorize: <30, 30-90, >90 days
- [ ] **TEST WITH REAL DATA:** 253 invoices, 199 paid, 54 unpaid

### Phase 2: Invoice Aging Widget UI ⚡⚡
- [ ] Create `invoice-aging-widget.tsx` component
- [ ] **Section 1:** Last 5 paid invoices (newest first, show date paid)
- [ ] **Section 2:** Largest outstanding (top 10 by amount, show days overdue)
- [ ] **Section 3:** Aging breakdown bar chart (recharts library)
- [ ] **Section 3:** Three aging cards (<30, 30-90, >90 days)
- [ ] Color code: Green (<30), Yellow (30-90), Red (>90)
- [ ] **MAKE IT REUSABLE:** Claude 5 will use this in overview!

### Phase 3: Projects List Page
- [ ] Create `/projects` page
- [ ] Embed invoice aging widget at top
- [ ] Project list with status badges
- [ ] Filter by status (Active, On Hold, Completed)
- [ ] Search by code or name
- [ ] Click project → detail page

### Phase 4: Project Detail Page
- [ ] Create `/projects/[code]` page
- [ ] Project header (code, title, client, status, contract date)
- [ ] Tabs: Overview, Timeline, Invoices, Team, Activity
- [ ] Overview tab: Key info, milestones, health indicator
- [ ] Invoices tab: List of project invoices with aging

### Phase 5: Email Activity Feed (After Claude 1)
- [ ] Wait for Claude 1 to signal "Email API ready"
- [ ] Integrate `/api/emails/project/{code}` into activity feed
- [ ] Show recent emails on project detail page
- [ ] Link emails to timeline events

---

## 🔗 DEPENDENCIES

### You Depend On
**Claude 1 (Emails):** For project activity feed
- Status: Wait for Claude 1 to signal ready
- Workaround: Build invoice widget first (no dependency!)
- When ready: Integrate `/api/emails/project/{code}`

### Others Depend On You
**Claude 5 (Overview):** Will reuse your invoice aging widget
- **CRITICAL:** Make `invoice-aging-widget.tsx` reusable (export as component)
- Props interface: `<InvoiceAgingWidget compact={boolean} />`
- Compact mode: Show summary only (for overview dashboard)
- Full mode: Show all sections (for projects page)

**Signal Claude 5 when widget is ready:**
```markdown
**Status:** ✅ Invoice Widget Complete
**Deliverables:**
- ✅ invoice-aging-widget.tsx (reusable component)
- ✅ Compact and full modes
- ✅ API endpoint working

**READY FOR:** Claude 5 can now use <InvoiceAgingWidget /> in overview!
```

---

## 🎨 UI MOCKUP

### Invoice Aging Widget (Full Mode)
```
┌─────────────────────────────────────────────────────────────┐
│  📊 Invoice Aging Analysis                                   │
├─────────────────────────────────────────────────────────────┤
│  💰 Recently Paid (Last 5)                                   │
│  • I24-092 - $250,000 - BK-033 - Paid Nov 20, 2025         │
│  • I24-088 - $180,000 - BK-074 - Paid Nov 18, 2025         │
│  • I24-085 - $320,000 - BK-029 - Paid Nov 15, 2025         │
│  ...                                                         │
├─────────────────────────────────────────────────────────────┤
│  🔴 Largest Outstanding                                      │
│  • I24-015 - $450,000 - BK-033 - 45 days overdue           │
│  • I24-017 - $380,000 - BK-074 - 32 days overdue           │
│  • I24-021 - $320,000 - BK-029 - 78 days overdue           │
│  ...                                                         │
├─────────────────────────────────────────────────────────────┤
│  📈 Aging Breakdown                                          │
│                                                             │
│  ██████████████████ < 30 Days  (15 invoices, $1.2M)        │
│  ██████████████████████████████ 30-90 Days (25, $2.1M)     │
│  ████████████████ > 90 Days  (14 invoices, $1.1M)          │
│                                                             │
│  ┌─────────────┬─────────────┬─────────────┐              │
│  │  < 30 Days  │  30-90 Days │  > 90 Days  │              │
│  │  15 invoices│  25 invoices│  14 invoices│              │
│  │  $1.2M      │  $2.1M      │  $1.1M      │              │
│  │  🟢 Good    │  🟡 Warning │  🔴 Critical│              │
│  └─────────────┴─────────────┴─────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 TESTING CHECKLIST

### API Tests
```bash
# Test aging endpoint
curl http://localhost:8000/api/invoices/aging

# Should return:
{
  "recentPaid": [...5 invoices],
  "largestOutstanding": [...10 invoices],
  "agingBreakdown": {
    "under_30": {"count": 15, "amount": 1200000},
    "30_to_90": {"count": 25, "amount": 2100000},
    "over_90": {"count": 14, "amount": 1100000}
  }
}
```

### Frontend Tests
- [ ] Widget loads without errors
- [ ] Last 5 paid shows correct invoices (sorted by payment_date DESC)
- [ ] Largest outstanding shows correct amounts (sorted by invoice_amount DESC)
- [ ] Bar chart renders correctly
- [ ] Aging cards show correct counts and amounts
- [ ] Colors correct: Green (<30), Yellow (30-90), Red (>90)
- [ ] Compact mode works (for overview reuse)

---

## 🎯 SUCCESS METRICS

**You're successful when:**
1. ✅ Invoice aging widget shows accurate data
2. ✅ Last 5 paid invoices display correctly
3. ✅ Largest outstanding invoices highlighted
4. ✅ Aging breakdown (<30, 30-90, >90) is correct
5. ✅ Bar chart visualizes aging clearly
6. ✅ Widget is reusable (Claude 5 can import it)
7. ✅ Projects list page works
8. ✅ Project detail page shows timeline and team

**User Impact:**
- Bill sees invoice aging at a glance
- Project managers track overdue invoices
- Finance team identifies collection priorities

---

## 🚀 READY TO START?

**Priority Order:**
1. Build invoice aging backend (Phase 1)
2. Build invoice aging widget UI (Phase 2) ← **MOST CRITICAL**
3. Build projects list page (Phase 3)
4. Build project detail page (Phase 4)
5. Add email activity feed when Claude 1 ready (Phase 5)

**Start with the invoice widget - user specifically requested it!** 💰📊
