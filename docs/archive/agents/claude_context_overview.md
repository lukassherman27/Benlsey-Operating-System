# CLAUDE 5: OVERVIEW DASHBOARD CONTEXT
**Role:** Dashboard Integration Specialist
**Priority:** MEDIUM (Final assembly of all widgets)
**Estimated Time:** 4-6 hours

---

## 🎯 YOUR MISSION

Build the **main overview dashboard** that serves as the central hub. You integrate widgets from all other Claudes:

1. **KPI Cards** (Revenue, Active Projects, Proposals, Invoices)
2. **Invoice Aging Widget** (from Claude 3)
3. **Recent Emails Widget** (from Claude 1)
4. **Proposal Pipeline Widget** (from Claude 4)
5. **Query Widget** (from Claude 2)
6. **Quick Actions** menu

This is the first page users see when they log in. Make it powerful!

---

## 🏗️ ARCHITECTURE CONTEXT

```
YOU ARE THE ASSEMBLER:

[Claude 1] → Recent Emails Widget
               ↓
[Claude 2] → Query Widget        } → YOUR DASHBOARD
               ↓                      (Unified Experience)
[Claude 3] → Invoice Aging Widget
               ↓
[Claude 4] → Pipeline Widget
```

**Your job:** Import their components and arrange them beautifully.

---

## 📚 FILES TO READ FIRST

**Must Read:**
1. `BENSLEY_OPERATIONS_PLATFORM_FORWARD_PLAN.md`
2. `COORDINATION_MASTER.md` - Track others' progress
3. `frontend/src/app/(dashboard)/page.tsx` - Current dashboard
4. `frontend/src/components/dashboard/` - Existing widgets

**Wait For These Components:**
- `frontend/src/components/emails/recent-emails-widget.tsx` (Claude 1)
- `frontend/src/components/query/query-widget.tsx` (Claude 2)
- `frontend/src/components/projects/invoice-aging-widget.tsx` (Claude 3) ⚡ PRIORITY
- `frontend/src/components/proposals/proposal-pipeline-widget.tsx` (Claude 4)

---

## 🛠️ FILES TO CREATE/MODIFY

### Frontend

#### 1. `frontend/src/app/(dashboard)/page.tsx` (REBUILD)
Complete dashboard layout:
```typescript
export default function DashboardPage() {
  return (
    <div className="space-y-6 p-6">
      {/* KPI Cards Row */}
      <KPICards />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LEFT COLUMN */}
        <div className="space-y-6">
          {/* Invoice Aging - Claude 3 */}
          <InvoiceAgingWidget compact={true} />

          {/* Recent Emails - Claude 1 */}
          <RecentEmailsWidget limit={5} />
        </div>

        {/* RIGHT COLUMN */}
        <div className="space-y-6">
          {/* Proposal Pipeline - Claude 4 */}
          <ProposalPipelineWidget compact={true} />

          {/* Quick Query - Claude 2 */}
          <QueryWidget compact={true} />
        </div>
      </div>

      {/* Bottom Row */}
      <QuickActionsWidget />
    </div>
  );
}
```

#### 2. `frontend/src/components/dashboard/kpi-cards.tsx` (NEW FILE)
4 KPI cards:
```typescript
export function KPICards() {
  const { data } = useQuery({
    queryKey: ['dashboard-kpis'],
    queryFn: () => api.getDashboardKPIs(),
  });

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <KPICard
        title="Active Revenue"
        value="$12.4M"
        change="+8.2%"
        icon={<DollarSign />}
      />
      <KPICard
        title="Active Projects"
        value="51"
        change="+3"
        icon={<Briefcase />}
      />
      <KPICard
        title="Active Proposals"
        value="35"
        change="+5"
        icon={<FileText />}
      />
      <KPICard
        title="Outstanding"
        value="$4.4M"
        change="-2.1%"
        icon={<AlertCircle />}
      />
    </div>
  );
}
```

#### 3. `frontend/src/components/dashboard/quick-actions-widget.tsx` (NEW FILE)
Quick action buttons:
```typescript
export function QuickActionsWidget() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <QuickAction
        label="New Proposal"
        icon={<Plus />}
        href="/proposals/new"
      />
      <QuickAction
        label="Check Invoices"
        icon={<Receipt />}
        href="/projects?filter=invoices"
      />
      <QuickAction
        label="Search Emails"
        icon={<Mail />}
        href="/emails"
      />
      <QuickAction
        label="Run Query"
        icon={<Search />}
        href="/query"
      />
    </div>
  );
}
```

### Backend

#### 4. `backend/api/main.py` (ADD ENDPOINT)
```python
@app.get("/api/dashboard/kpis")
async def get_dashboard_kpis():
    """
    Returns:
    {
        "active_revenue": 12400000,
        "active_projects": 51,
        "active_proposals": 35,
        "outstanding_invoices": 4400000
    }
    """
```

---

## ✅ YOUR TASKS (Checklist)

### Phase 1: Wait & Plan
- [ ] Monitor COORDINATION_MASTER.md daily
- [ ] Track when other Claudes signal widgets ready
- [ ] Plan dashboard layout (sketch it out)
- [ ] Read all widget prop interfaces

### Phase 2: KPI Cards
- [ ] Create `kpi-cards.tsx` component
- [ ] Add `/api/dashboard/kpis` backend endpoint
- [ ] Display 4 KPI cards
- [ ] Add loading and error states

### Phase 3: Import Widgets (WAIT FOR SIGNALS)
- [ ] Wait: Claude 3 signals "Invoice widget ready" ⚡
- [ ] Import: `<InvoiceAgingWidget compact={true} />`
- [ ] Wait: Claude 1 signals "Email API ready"
- [ ] Import: `<RecentEmailsWidget limit={5} />`
- [ ] Wait: Claude 4 signals "Pipeline widget ready"
- [ ] Import: `<ProposalPipelineWidget compact={true} />`
- [ ] Wait: Claude 2 signals "Query widget ready"
- [ ] Import: `<QueryWidget compact={true} />`

### Phase 4: Layout & Polish
- [ ] Arrange widgets in 2-column grid
- [ ] Add quick actions at bottom
- [ ] Mobile responsive (stack on mobile)
- [ ] Loading states for each widget
- [ ] Empty states if no data

### Phase 5: Integration Testing
- [ ] All widgets load without errors
- [ ] KPIs show correct data
- [ ] Clicking widget opens full page
- [ ] Quick actions navigate correctly
- [ ] Dashboard loads in <2 seconds

---

## 🔗 DEPENDENCIES

### You Depend On (CRITICAL)
**You MUST wait for these Claudes to signal ready:**

**Claude 1 (Emails):**
- Need: `<RecentEmailsWidget />` component
- Status: Check COORDINATION_MASTER.md
- Workaround: Show "Loading emails..." placeholder

**Claude 2 (Query):**
- Need: `<QueryWidget />` component
- Status: Check COORDINATION_MASTER.md
- Workaround: Show "Query interface coming soon"

**Claude 3 (Projects):**
- Need: `<InvoiceAgingWidget compact={true} />` ⚡ PRIORITY
- Status: Check COORDINATION_MASTER.md
- Workaround: Show "Loading invoice data..."

**Claude 4 (Proposals):**
- Need: `<ProposalPipelineWidget compact={true} />`
- Status: Check COORDINATION_MASTER.md
- Workaround: Show "Loading pipeline..."

### Nobody Depends On You
**You're the final assembler.** Users depend on you for unified experience!

---

## 🎨 DASHBOARD LAYOUT

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Bensley Operations Dashboard                            │
├─────────────────────────────────────────────────────────────┤
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐              │
│  │ $12.4M │ │  51    │ │  35    │ │ $4.4M  │              │
│  │Revenue │ │Projects│ │Proposal│ │Outstand│              │
│  │ +8.2%  │ │  +3    │ │  +5    │ │ -2.1%  │              │
│  └────────┘ └────────┘ └────────┘ └────────┘              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Invoice Aging    │  │ Proposal Pipeline│               │
│  │ < 30: $1.2M      │  │ Sent:  20        │               │
│  │ 30-90: $2.1M     │  │ Won:   30        │               │
│  │ > 90: $1.1M 🔴   │  │ Lost:  22        │               │
│  └──────────────────┘  └──────────────────┘               │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Recent Emails    │  │ Quick Query      │               │
│  │ • BK-033 Kickoff │  │ [Ask a question] │               │
│  │ • BK-074 Invoice │  │                  │               │
│  │ • BK-068 Proposal│  │ 🔍 [Search]      │               │
│  └──────────────────┘  └──────────────────┘               │
├─────────────────────────────────────────────────────────────┤
│  [+ New Proposal] [Check Invoices] [Search] [Run Query]    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 TESTING CHECKLIST

### Widget Integration Tests
- [ ] Invoice aging widget renders (from Claude 3)
- [ ] Recent emails widget renders (from Claude 1)
- [ ] Pipeline widget renders (from Claude 4)
- [ ] Query widget renders (from Claude 2)

### Navigation Tests
- [ ] Click invoice widget → opens `/projects` with invoice tab
- [ ] Click email widget → opens `/emails`
- [ ] Click pipeline widget → opens `/proposals`
- [ ] Click query widget → opens `/query`
- [ ] Quick actions navigate correctly

### Performance Tests
- [ ] Dashboard loads in <2 seconds
- [ ] All widgets load in parallel (no waterfall)
- [ ] Loading states show immediately
- [ ] No console errors or warnings

---

## 📊 STATUS REPORTING

### Before You Can Start
```markdown
**Status:** ⏳ Waiting for dependencies
**Blocked:** Need widgets from Claude 1, 3, 4
**Progress:** 0%
**Workaround:** Planning layout, building KPI cards
```

### When Dependencies Ready
```markdown
**Status:** 🔄 In Progress
**Progress:** 40%
**Integrated:** Invoice widget (Claude 3) ✅
**Waiting:** Email widget (Claude 1), Pipeline (Claude 4)
```

### When Complete
```markdown
**Status:** ✅ Complete
**Progress:** 100%
**Deliverables:**
- ✅ Dashboard page with 4 KPI cards
- ✅ Invoice aging widget integrated
- ✅ Recent emails widget integrated
- ✅ Pipeline widget integrated
- ✅ Query widget integrated
- ✅ Quick actions menu
- ✅ Mobile responsive
- ✅ Loads in <2 seconds

**READY FOR:** End users!
```

---

## 💡 COORDINATION TIPS

### How to Wait for Dependencies

**Check COORDINATION_MASTER.md daily:**
```markdown
### Claude 3: Active Projects
**Status:** ✅ Invoice Widget Complete
**Deliverables:**
- ✅ invoice-aging-widget.tsx (reusable)

**READY FOR:** Claude 5 can now use <InvoiceAgingWidget />
```

**When you see "READY FOR: Claude 5":**
1. Immediately import their component
2. Test it in your dashboard
3. Update COORDINATION_MASTER.md with progress
4. Thank them! (Optional but nice)

---

## 🎯 SUCCESS METRICS

**You're successful when:**
1. ✅ All 4 KPI cards show accurate data
2. ✅ All 4 widgets integrated and working
3. ✅ Dashboard is beautiful and intuitive
4. ✅ Users prefer dashboard over Excel
5. ✅ Loads fast (<2 seconds)
6. ✅ Mobile responsive
7. ✅ No errors in console

**User Impact:**
- Bill sees everything at a glance
- Decision-making faster
- Reduces time spent in Excel/email
- **Success: Bill uses this every morning**

---

## 🚀 READY TO START?

**Your Timeline:**
1. **Day 1:** Build KPI cards (can do now!)
2. **Day 2:** Wait for Claude 3 invoice widget → Integrate
3. **Day 2-3:** Other widgets become ready → Integrate
4. **Day 3:** Polish layout, add quick actions
5. **Day 4:** Test everything, optimize performance

**You're the maestro conducting the orchestra!** 🎼

**Check COORDINATION_MASTER.md constantly for signals!**
