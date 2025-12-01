# Frontend Build Plan - Week 3-4

**Status:** Ready to build dashboards
**Current blockers:** None - can build with existing data

---

## Current Frontend Status

### ✅ What Works:
- Navigation updated with new structure (Proposals, Projects, Query, Emails)
- App shell component fixed
- Dev server running on localhost:3002
- Backend API running on localhost:8000 (93 endpoints)

### ✅ Existing Pages:
1. `/` - Overview/Dashboard (exists but needs work)
2. `/proposals` - Proposals list page
3. `/proposals/[projectCode]` - Proposal detail page
4. `/emails` - Emails list page
5. `/query` - Query interface page

### ❌ Missing Pages (Need to Build):
1. `/projects` - **Active Projects Dashboard** (HIGH PRIORITY)
2. `/projects/[projectCode]` - **Project Detail Page** (HIGH PRIORITY)

---

## Week 3-4 Tasks: Build Dashboards

### **Task 1: Fix Dashboard Home (/)**
**File:** `frontend/src/app/(dashboard)/page.tsx`
**Time:** 2-3 hours

**Should show:**
- Quick stats (active proposals, active projects, outstanding invoices)
- Recent activity
- Proposals needing follow-up (top 5)
- Projects at risk (top 5)
- Quick links to Proposals and Projects dashboards

**API endpoints to use:**
- GET /api/dashboard/stats
- GET /api/proposals/needs-follow-up
- GET /api/proposals/at-risk
- GET /api/invoices/outstanding
- GET /api/projects/active

---

### **Task 2: Build Proposal Dashboard**
**File:** `frontend/src/app/(dashboard)/proposals/page.tsx`
**Time:** 4-6 hours
**Status:** Page exists, needs enhancement

**Layout:**
```
┌──────────────────────────────────────────┐
│  PROPOSALS DASHBOARD                      │
├──────────────────────────────────────────┤
│  ┌────────┐ ┌────────┐ ┌────────┐       │
│  │ Active │ │Pipeline│ │ Needs  │       │
│  │   42   │ │ $8.5M  │ │Follow  │       │
│  │        │ │        │ │  Up:12 │       │
│  └────────┘ └────────┘ └────────┘       │
│                                           │
│  PROPOSALS NEEDING FOLLOW-UP             │
│  ┌────────────────────────────────────┐  │
│  │ 🔴 BK-123 Rosewood Phuket          │  │
│  │    Last contact: 14 days ago       │  │
│  │    Value: $850K                    │  │
│  └────────────────────────────────────┘  │
│                                           │
│  ALL PROPOSALS (Table)                   │
│  Code | Client | Status | Value | Health│
│  ────────────────────────────────────── │
│  BK-123 | Rosewood | Active | $850K | 🟡│
│  BK-125 | Banyan | Active | $420K | 🟢 │
└──────────────────────────────────────────┘
```

**Components needed:**
- Summary cards (4 metrics)
- Priority list component (proposals needing follow-up)
- Table component (all proposals)
- Filters (status, date range, value)

**API endpoints:**
- ✅ GET /api/proposals/stats
- ✅ GET /api/proposals/needs-follow-up
- ✅ GET /api/proposals/at-risk
- ✅ GET /api/proposals (list with filters)
- ✅ GET /api/proposals/weekly-changes

---

### **Task 3: Build Active Projects Dashboard** (NEW PAGE)
**File:** `frontend/src/app/(dashboard)/projects/page.tsx` (CREATE THIS)
**Time:** 4-6 hours
**Priority:** 🔴 HIGH

**Layout:**
```
┌──────────────────────────────────────────┐
│  ACTIVE PROJECTS DASHBOARD                │
├──────────────────────────────────────────┤
│  ┌────────┐ ┌────────┐ ┌────────┐       │
│  │ Active │ │Outstand│ │Upcoming│       │
│  │Projects│ │Invoices│ │Deadlines│      │
│  │   28   │ │ $1.2M  │ │   15   │       │
│  └────────┘ └────────┘ └────────┘       │
│                                           │
│  FINANCIAL OVERVIEW                      │
│  ┌────────────────────────────────────┐  │
│  │ 💰 Overdue Invoices (60+ days)     │  │
│  │    BK-070: $85,000 (87 days)       │  │
│  │    [Send Reminder] [Mark Paid]     │  │
│  └────────────────────────────────────┘  │
│                                           │
│  UPCOMING DEADLINES                      │
│  📅 BK-123: Schematic Design - Nov 25   │
│  📅 BK-089: Construction Docs - Nov 28  │
│                                           │
│  ALL ACTIVE PROJECTS (Table)             │
│  Code | Client | Phase | Next | Status  │
└──────────────────────────────────────────┘
```

**Components needed:**
- Summary cards (4 metrics)
- Financial widget (overdue invoices)
- Schedule widget (upcoming milestones)
- RFI widget (unanswered RFIs)
- Table component (all projects)

**API endpoints:**
- ✅ GET /api/projects/active
- ✅ GET /api/invoices/outstanding
- ✅ GET /api/invoices/stats
- ✅ GET /api/milestones
- ✅ GET /api/rfis
- ✅ GET /api/finance/recent-payments

**Create file structure:**
```bash
mkdir -p src/app/(dashboard)/projects
touch src/app/(dashboard)/projects/page.tsx
mkdir -p src/app/(dashboard)/projects/[projectCode]
touch src/app/(dashboard)/projects/[projectCode]/page.tsx
```

---

### **Task 4: Build Project Detail Page** (NEW PAGE)
**File:** `frontend/src/app/(dashboard)/projects/[projectCode]/page.tsx` (CREATE THIS)
**Time:** 3-4 hours
**Priority:** 🔴 HIGH

**Sections:**
1. **Header:** Project code, client, phase, contract value
2. **Financial Summary:** Invoices, payments, outstanding
3. **Schedule:** Milestones, deadlines, Gantt chart
4. **RFIs:** All RFIs for this project
5. **Documents:** Contract, invoices, schedules
6. **Communication:** Emails, meetings

**API endpoints:**
- ✅ GET /api/projects/{project_code}/financial-summary
- ✅ GET /api/projects/{project_code}/timeline
- ✅ GET /api/invoices/by-project/{project_code}
- ✅ GET /api/proposals/{proposal_id}/rfis (use project's proposal_id)
- ✅ GET /api/proposals/by-code/{project_code}/emails/timeline

---

### **Task 5: Polish Existing Pages**

**Emails Page:** (`/emails`)
- Already exists
- Add better filtering
- Show categorization tags
- Link to related projects

**Query Page:** (`/query`)
- Already exists
- Polish UI
- Add query suggestions
- Show recent queries

---

## Component Library Setup

### Recommended: Use shadcn/ui (already configured)

**Install additional components:**
```bash
npx shadcn-ui@latest add card
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add table
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add select
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add calendar
```

---

## Data to Populate

### From Existing Database:

**Proposals:**
- ✅ Exists in `proposals` table
- ✅ Health scores in `proposal_health` table
- ✅ Timeline in `proposal_timeline` table
- ✅ Email links in `email_proposal_links` table

**Projects:**
- ✅ Exists in `projects` table
- ✅ Invoices in `invoices` table
- ✅ Milestones in `project_milestones` table
- ✅ RFIs in `rfis` table
- ✅ Contract data in `contract_metadata` + `contract_phases` tables

**Client/Relationship Data:**
- ✅ Clients in `clients` table
- ✅ Client aliases in `client_aliases` table
- ✅ Project-contact links in `project_contact_links` table
- ✅ Email-project links in `email_project_links` table

### What's Missing (but OK for MVP):
- ⚠️ Contract PDFs (blocked by finance team - but have metadata)
- ⚠️ Invoice PDFs (blocked by finance team - but have data from Excel)
- ⚠️ Some historical RFI data (scattered - will capture going forward)

---

## Next Session Checklist:

### Immediate (1-2 hours):
1. [✅] Check localhost:3002 - verify pages load
2. [✅] Fix dashboard home (/) - works correctly
3. [✅] Create `/projects` page directory structure

### This Week (Week 3):
4. [✅] Build Active Projects Dashboard (`/projects` page)
5. [✅] Build Project Detail Page (`/projects/[projectCode]` page)
6. [ ] Polish Proposal Dashboard
7. [⚠️] Connect all pages to real API data (some backend schema issues need fixing)

### Next Week (Week 4):
8. [ ] Add charts/visualizations (Recharts)
9. [ ] Mobile responsive design
10. [ ] Loading states & error handling
11. [ ] Polish navigation & breadcrumbs

---

## Success Criteria:

**By end of Week 3:**
- ✅ Both dashboards (Proposals + Projects) functional
- ✅ Can view proposal details
- ✅ Can view project details
- ✅ Real data from API showing correctly

**By end of Week 4:**
- ✅ Dashboards look beautiful
- ✅ Mobile responsive
- ✅ Fast loading (<2 seconds)
- ✅ Bill can use for daily operations

---

**Remember:** We're building with existing data. Don't wait for contract/invoice PDFs from finance team. The metadata and Excel data is enough for MVP!

**Last Updated:** 2025-11-19
**Status:** ✅ Projects pages built! Backend API schema needs minor fixes.

---

## ✅ Completed in This Session (2025-11-19)

### Pages Created:
1. **Active Projects Dashboard** (`/projects/page.tsx`) - COMPLETE
   - Summary cards (Active Projects, Outstanding Invoices, Upcoming Deadlines, Unanswered RFIs)
   - Financial Overview widget (Overdue invoices with actions)
   - Upcoming Deadlines section (30-day view)
   - Unanswered RFIs section
   - All Active Projects table with project details

2. **Project Detail Page** (`/projects/[projectCode]/page.tsx`) - COMPLETE
   - Header with project code, phase, client name
   - Financial Summary cards (Contract Value, Paid to Date, Outstanding, Payment Progress)
   - Payment Progress Bar visualization
   - Invoices section with status badges (Paid, Pending, Overdue)
   - Schedule & Milestones timeline
   - Communication & Documents sections (Recent Emails, Documents)

### API Functions Added:
Added to `frontend/src/lib/api.ts`:
- `getActiveProjects()` - GET /api/projects/active
- `getProjectDetail(projectCode)` - GET /api/projects/{code}/financial-summary
- `getProjectTimeline(projectCode)` - GET /api/projects/{code}/timeline
- `getInvoiceStats()` - GET /api/invoices/stats
- `getOutstandingInvoices()` - GET /api/invoices/outstanding
- `getInvoicesByProject(projectCode)` - GET /api/invoices/by-project/{code}
- `getMilestones(params)` - GET /api/milestones
- `getRfis(params)` - GET /api/rfis
- `getProposalRfis(proposalId)` - GET /api/proposals/{id}/rfis

### Navigation Updated:
- ✅ `/` - Dashboard Home (already working)
- ✅ `/proposals` - Proposals Dashboard (already working)
- ✅ `/projects` - **NEW** Active Projects Dashboard
- ✅ `/projects/[code]` - **NEW** Project Detail Page
- ✅ `/query` - Query Interface (already working)
- ✅ `/emails` - Emails List (already working)

### Known Issues to Fix:
⚠️ **Backend API Schema Mismatch:**
- `/api/projects/active` returns error: `"no such column: p.client_name"`
- This is a backend SQL query issue that needs to be fixed in `backend/api/main.py`
- The SQL query is trying to select columns that don't exist in the current database schema
- **Fix needed:** Update the backend endpoint to use the correct column names from the actual database schema

---

**Next Steps:**
1. Fix backend `/api/projects/active` endpoint schema mismatch
2. Test all project pages with real data
3. Polish Proposal Dashboard
4. Add loading states and error handling
