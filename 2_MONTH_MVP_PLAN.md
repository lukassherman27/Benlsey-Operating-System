# BDS Operations Platform: 2-Month MVP Plan
**Dashboard-First Approach**

---

## Executive Summary

**Goal:** Ship two production-ready dashboards in 8 weeks
- **Proposal Dashboard** (sales pipeline management)
- **Active Projects Dashboard** (operations: payments, schedule, RFIs)

**Timeline:**
- **Phase 1** (Now - Mid-December): Dashboards + Data - 8 weeks
- **Phase 2** (December/January - Holiday): Intelligence Layer - 4-6 weeks
- **Phase 3** (February+): Multi-user Frontend - TBD

---

## Critical Distinctions

### Proposals vs. Projects

| Proposals | Active Projects |
|-----------|----------------|
| Pre-contract, sales pipeline | Won contracts, under execution |
| Track: health, follow-ups, status | Track: payments, invoices, schedules |
| Goal: Win the work | Goal: Deliver on time and budget |
| Data: proposal_health, proposal_timeline | Data: invoices, milestones, rfis |
| Owner: Bill (BD) | Owner: Project Managers |

---

## PHASE 1: Dashboards + Data (8 Weeks)

### WEEK 1-2: Data Foundation
**Goal: Complete, validated dataset**

#### Tasks:

**Email Imports:**
- [ ] Import rfi@bensley.com inbox (all historical)
  - Auto-tag as `category: 'rfi'`
  - Link to projects via smart matching
  - Parse RFI content (question, deadline, client)

- [ ] Import finance@bensley.com inbox (all historical)
  - Auto-tag as `category: 'invoice'` or `category: 'payment'`
  - Link to invoices in database
  - Extract payment confirmations

**Accounting Integration:**
- [ ] Map accounting Excel columns to database schema
  - Invoice numbers, amounts, dates
  - Payment records
  - Client names (match to `clients` table)

- [ ] Build import script with provenance
  - `source_type: 'import'`
  - `source_reference: 'accounting_excel_YYYY-MM-DD'`
  - `created_by: 'accounting_import'`

- [ ] Validate against existing invoice data
  - Flag discrepancies (amount mismatches)
  - Manual review of conflicts

**Historical Email Backfill:**
- [ ] Import last 2-3 years of emails (all accounts)
- [ ] Run smart matchers (email → project linking)
- [ ] AI categorization for uncategorized emails

**Data Quality:**
- [ ] Audit proposal health scores (recalculate if needed)
- [ ] Validate project-invoice relationships
- [ ] Check for missing critical data (project codes, client names)
- [ ] Fix data quality issues logged in `data_quality_tracking`

**Deliverable:** ✅ Complete dataset, <5% data quality issues

---

### WEEK 3-4: Proposal Dashboard
**Goal: "Sales Pipeline Command Center"**

#### Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│  PROPOSALS DASHBOARD                                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Active   │  │ Pipeline │  │ Needs    │  │ At Risk │ │
│  │ Proposals│  │ Value    │  │ Follow-up│  │         │ │
│  │   42     │  │  $8.5M   │  │    12    │  │    5    │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  PROPOSALS NEEDING FOLLOW-UP                       │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  🔴 Rosewood Phuket (BK-123)                       │ │
│  │     Last contact: 14 days ago | Value: $850K       │ │
│  │     [Follow Up] [Mark Done] [View Details]        │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  🟡 Banyan Tree Krabi (BK-125)                     │ │
│  │     Last contact: 7 days ago | Value: $420K        │ │
│  │     [Follow Up] [Mark Done] [View Details]        │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  WEEKLY CHANGES                                    │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  🆕 New: 3 proposals | Won: 2 | Lost: 1           │ │
│  │  📈 Updated: 8 proposals                           │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  ALL PROPOSALS                    [Filter ▼] [⚙️]  │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  Project Code | Client | Status | Value | Health  │ │
│  │  BK-123 | Rosewood | Active | $850K | 🟡 Medium  │ │
│  │  BK-125 | Banyan Tree | Active | $420K | 🟢 Good │ │
│  │  ...                                               │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### Components to Build:

**Summary Cards (4 cards):**
- Active Proposals count
- Total Pipeline Value (sum of active proposals)
- Needs Follow-up count (>7 days since last contact)
- At-Risk count (health score < 50)

**Priority List: "Needs Follow-up"**
- Query: Proposals with no contact in >7 days
- Sort by: Last contact date (oldest first)
- Display: Project code, client, days since contact, value
- Actions: "Follow Up" (log contact), "Mark Done", "View Details"

**Weekly Changes Widget:**
- New proposals this week
- Proposals won this week
- Proposals lost this week
- Proposals with status updates

**All Proposals Table:**
- Columns: Project Code, Client, Status, Total Value, Health Score, Last Contact
- Filters: Status (active/won/lost), Value range, Date range
- Sort: Any column
- Click row → Proposal Detail Page

#### API Endpoints Needed:
- ✅ GET /api/proposals/stats (already exists)
- ✅ GET /api/proposals/needs-follow-up (already exists)
- ✅ GET /api/proposals/at-risk (already exists)
- ✅ GET /api/proposals/weekly-changes (already exists)
- ✅ GET /api/proposals (list with filters) (already exists)

#### Frontend Work:
- React components for each widget
- State management (React Query or Zustand)
- Responsive design (desktop + tablet)
- Auto-refresh every 5 minutes
- Loading states, error handling

**Deliverable:** ✅ Proposal Dashboard live at /dashboard/proposals

---

### Proposal Detail Page

**URL:** `/proposals/{project_code}`

**Sections:**

1. **Header**
   - Project code, client name, status badge
   - Total value, health score
   - Quick actions: "Send Follow-up", "Update Status", "Mark Won/Lost"

2. **Timeline**
   - Visual timeline of key events
   - First contact, proposal sent, follow-ups, meetings
   - Data from `proposal_timeline` table

3. **Health Indicators**
   - Last contact date (red if >14 days)
   - Proposal age
   - Response rate
   - Engagement score

4. **Financial Summary**
   - Proposed total fee
   - Breakdown by discipline (if available)
   - Comparison to similar projects

5. **Communication History**
   - All emails related to this proposal
   - Meetings, calls logged
   - Quick email composer

6. **Context & Notes**
   - AI-generated summary
   - Manual notes
   - Related documents

**API Endpoints:**
- ✅ GET /api/proposals/{identifier} (already exists)
- ✅ GET /api/proposals/{identifier}/timeline (already exists)
- ✅ GET /api/proposals/{identifier}/health (already exists)
- ✅ GET /api/proposals/by-code/{project_code}/emails/timeline (already exists)

**Deliverable:** ✅ Proposal Detail Page live

---

### WEEK 5-6: Active Projects Dashboard
**Goal: "Operations Command Center"**

#### Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│  ACTIVE PROJECTS DASHBOARD                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Active   │  │Outstanding│  │ Upcoming │  │Unanswered│ │
│  │ Projects │  │ Invoices  │  │Milestones│  │  RFIs    │ │
│  │   28     │  │  $1.2M    │  │    15    │  │    8     │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  FINANCIAL OVERVIEW                                │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  💰 Overdue Invoices (60+ days)                    │ │
│  │     BK-070: $85,000 (Invoice #I24-045) - 87 days  │ │
│  │     [Send Reminder] [Mark Paid] [View Project]    │ │
│  │                                                     │ │
│  │  💰 Recent Payments                                │ │
│  │     BK-045: $120,000 received Nov 10              │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  UPCOMING DEADLINES (Next 14 Days)                 │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  📅 BK-123: Schematic Design - Nov 25 (5 days)    │ │
│  │  📅 BK-089: Construction Docs - Nov 28 (8 days)   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  RFI TRACKER                                       │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  🔴 BK-070: Soil testing requirements (Overdue)   │ │
│  │     Received: Nov 5 | Due: Nov 15                 │ │
│  │     [Respond] [Mark Answered] [View Thread]       │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  ALL ACTIVE PROJECTS          [Filter ▼] [⚙️]      │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  Code | Client | Phase | Next Milestone | Status  │ │
│  │  BK-070 | Rosewood | CD | Nov 28 | 🟢 On Track   │ │
│  │  BK-089 | Banyan | DD | Nov 30 | 🟡 At Risk     │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### Components to Build:

**Summary Cards (4 cards):**
- Active Projects count
- Outstanding Invoices total ($)
- Upcoming Milestones (next 14 days)
- Unanswered RFIs count

**Financial Widget:**
- Overdue invoices (30/60/90 day buckets)
- Actions: "Send Reminder", "Mark Paid"
- Recent payments (last 7 days)
- Projected cash flow (optional for MVP)

**Schedule Widget:**
- Upcoming milestones (next 14 days)
- Sort by: Date (soonest first)
- Color code: 🔴 <3 days, 🟡 3-7 days, 🟢 >7 days
- Overdue milestones (separate section)

**RFI Tracker Widget:**
- Unanswered RFIs by project
- Overdue RFIs (past due date)
- Actions: "Respond", "Mark Answered"
- Link to email thread

**All Projects Table:**
- Columns: Project Code, Client, Current Phase, Next Milestone, Status
- Filters: Status, Client, Date range
- Click row → Project Detail Page

#### API Endpoints Needed:
- ✅ GET /api/projects/active (already exists)
- ✅ GET /api/invoices/outstanding (already exists)
- ✅ GET /api/invoices/stats (already exists)
- ✅ GET /api/milestones (already exists)
- ✅ GET /api/rfis (already exists)
- ✅ GET /api/finance/recent-payments (already exists)

#### Frontend Work:
- React components for each widget
- Financial summary calculations
- Schedule timeline visualization
- RFI status indicators
- Auto-refresh every 5 minutes

**Deliverable:** ✅ Active Projects Dashboard live at /dashboard/projects

---

### Project Detail Page

**URL:** `/projects/{project_code}`

**Sections:**

1. **Header**
   - Project code, client, current phase
   - Contract value, total invoiced, total paid
   - Status: On track / At risk / Behind

2. **Financial Summary**
   - All invoices (issued, paid, outstanding)
   - Payment schedule vs. actuals
   - Aging report for this project
   - Quick action: "Send invoice", "Record payment"

3. **Schedule & Milestones**
   - Gantt chart or timeline view
   - All phases and milestones
   - Completed vs. upcoming
   - Overdue items highlighted

4. **RFI Management**
   - All RFIs for this project
   - Status: Pending, Answered, Overdue
   - Quick respond interface
   - Email thread viewer

5. **Documents**
   - Contract document
   - Invoices (PDFs)
   - Schedules
   - RFI correspondence

6. **Communication History**
   - All emails tagged to this project
   - Meetings, calls
   - Quick email composer

**API Endpoints:**
- ✅ GET /api/projects/{project_code}/financial-summary (already exists)
- ✅ GET /api/projects/{project_code}/timeline (already exists)
- ✅ GET /api/invoices/by-project/{project_code} (already exists)
- ✅ GET /api/proposals/{proposal_id}/rfis (already exists)
- ✅ GET /api/proposals/by-code/{project_code}/emails/timeline (already exists)

**Deliverable:** ✅ Project Detail Page live

---

### WEEK 7-8: Polish & Integration

#### Navigation
- [ ] Top nav bar: "Proposals" | "Projects" | "Settings"
- [ ] Sidebar (optional): Quick filters, saved views
- [ ] Breadcrumbs on detail pages
- [ ] Back button, keyboard shortcuts

#### Data Refresh
- [ ] Auto-refresh dashboards every 5 minutes
- [ ] Manual refresh button
- [ ] "Last updated" timestamp
- [ ] Loading states (skeleton loaders)

#### Mobile Responsive
- [ ] Dashboard cards stack on mobile
- [ ] Tables → swipeable cards on mobile
- [ ] Touch-friendly tap targets
- [ ] Test on iPhone/iPad

#### Performance
- [ ] Lazy load detail pages
- [ ] Pagination for long lists (>50 items)
- [ ] Cache API responses (React Query)
- [ ] Optimize bundle size

#### Error Handling
- [ ] Graceful API failures (show cached data)
- [ ] User-friendly error messages
- [ ] Retry logic for failed requests
- [ ] Contact support link

#### User Testing
- [ ] Bill walkthrough (30 min session)
- [ ] Collect feedback on workflows
- [ ] Fix critical UX issues
- [ ] Validate data accuracy

#### Deployment
- [ ] Deploy to staging server
- [ ] Test with production data (copy of DB)
- [ ] Performance testing (load time)
- [ ] Security review (no exposed secrets)

**Deliverable:** ✅ Production-ready dashboards deployed

---

## PHASE 2: Intelligence Layer (4-6 Weeks)
**Timeline: December/January (Holiday period)**

### Goals:
1. Natural language query interface
2. Data cleaning & organization
3. Vector store / RAG setup
4. Local LLM installation
5. Model distillation pipeline

### Why This Timing:
- Data will be complete and validated from Phase 1
- You'll know what queries users need (based on dashboard usage patterns)
- Holiday = focused deep work time
- Can refine data structure based on what's missing

### Deliverables:
- Query interface: "Show me outstanding RFIs for BK-070"
- Semantic search via RAG
- Local LLM running (Ollama + Llama)
- Training pipeline collecting Claude responses
- Data quality at >95%

---

## PHASE 3: Multi-User Frontend (TBD)
**Timeline: February onwards**

### User Roles:

**1. Executive View (Bill)** - Full access
- All dashboards
- All projects and proposals
- Financial summary
- Query interface
- Settings & admin

**2. Project Manager View** - Project-specific
- Assigned projects only
- RFI management
- Schedule updates
- Limited financial view (no full pipeline value)
- No proposal pipeline access

**3. Finance View (Accounting Team)** - Financial focus
- Invoice tracker (all projects)
- Payment status
- Financial reports
- Client payment history
- No proposal pipeline
- No project schedules

**4. Read-Only View** - View only, no edits
- Project status
- Schedule view
- Document access
- No financial data
- No edit permissions

### Features:
- Sign-in/authentication (email + password)
- Role-based permissions (enforce in backend)
- Different dashboard layouts per role
- Audit logging (who changed what, when)
- User management (add/remove users, change roles)

---

## Tech Stack Summary

### Backend (Already Built!)
- ✅ FastAPI with 93 endpoints
- ✅ SQLite database (complete schema)
- ✅ Claude API integration
- ✅ Email importer (IMAP)
- ✅ Provenance tracking

### Frontend (To Build)
- **Framework:** Next.js 14 (App Router)
- **UI Library:** shadcn/ui or Material-UI
- **State:** React Query (server state) + Zustand (client state)
- **Styling:** Tailwind CSS
- **Charts:** Recharts or Chart.js
- **Tables:** TanStack Table (React Table)

### Deployment (Phase 1)
- **Backend:** Local Mac (FastAPI on port 8000)
- **Frontend:** Local dev server (Next.js on port 3002)
- **Database:** SQLite (file-based)
- **Later:** Deploy to staging server, production Mac Mini

---

## Success Metrics

### End of Week 2:
- ✅ Database size >2GB (all data imported)
- ✅ <5% data quality issues
- ✅ All invoices from accounting matched to projects

### End of Week 4:
- ✅ Proposal Dashboard loads in <2 seconds
- ✅ Can identify proposals needing follow-up accurately
- ✅ Bill uses it to track pipeline daily

### End of Week 6:
- ✅ Projects Dashboard shows real-time invoice status
- ✅ RFI tracker shows accurate overdue items
- ✅ Schedule widget shows next 2 weeks of milestones

### End of Week 8:
- ✅ Both dashboards production-ready
- ✅ Zero critical bugs
- ✅ Bill can manage proposals + projects from one interface
- ✅ Saves 5-10 hours/week vs. Excel + email

---

## Risks & Mitigations

### Risk 1: Accounting Excel integration takes longer than expected
**Mitigation:**
- Start with manual mapping (first 10 rows)
- Validate with accounting team early (Week 1)
- Have fallback: manual invoice entry UI

### Risk 2: Data quality issues delay dashboard build
**Mitigation:**
- Week 2 is buffer for data cleanup
- Don't start dashboard UI until data validated
- Build data quality dashboard first (identify gaps)

### Risk 3: Dashboard UI takes longer than expected
**Mitigation:**
- Use UI component library (shadcn/ui) - don't build from scratch
- Start with basic layout, polish later
- Week 7-8 is buffer for polish

### Risk 4: API endpoints missing critical data
**Mitigation:**
- Review API endpoints in Week 2 (before UI work)
- Add missing endpoints early
- Most endpoints already exist (93 total)

---

## Next Steps

### This Week (Week 1):
1. [ ] Build rfi@bensley.com email importer
2. [ ] Build finance@bensley.com email importer
3. [ ] Test with last 100 emails from each inbox
4. [ ] Validate email-to-project linking

### Next Week (Week 2):
1. [ ] Map accounting Excel to database schema
2. [ ] Build import script with validation
3. [ ] Import historical emails (last 2 years)
4. [ ] Run data quality audit
5. [ ] Fix critical data issues

### Week 3 (Start Proposal Dashboard):
1. [ ] Design dashboard wireframe
2. [ ] Set up Next.js pages structure
3. [ ] Build summary cards component
4. [ ] Connect to existing API endpoints

---

**Let's ship this!** 🚀

**Last Updated:** 2025-11-19
**Status:** Ready to start Week 1
**Confidence:** 95% (backend done, focus on data + UI)
