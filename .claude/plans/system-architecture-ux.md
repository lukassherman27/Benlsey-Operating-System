# System Architecture & UX Plan

**Created:** 2026-01-01
**Author:** Claude System Architect Agent
**Purpose:** Comprehensive audit + role-based design plan

---

## 1. Executive Summary

### The Vision
Bill Bensley is the **CONSUMER** of this system, not the producer. Information flows TO him through emails, meetings, and AI suggestions. He reviews, approves, and makes decisions - but doesn't input data manually.

### Key Insight
```
EMAIL → AI PROCESSING → SUGGESTIONS → BILL REVIEWS
                                          ↓
                              LEARNING LOOP → PATTERNS
```

### Priority Order (Per Lukas)
1. **Bill/Brian Executive View** - First priority
2. PM Views - Future
3. Designer Views - Future (email-based workflow)
4. Finance/Admin Views - Future

---

## 2. Current State Audit

### 2.1 Users & Authentication

| Staff | Role | Department | Has Login | Notes |
|-------|------|------------|-----------|-------|
| William Bensley | Owner | Leadership | Yes | Primary user |
| Brian Petrie | Principal | Leadership | No | Needs login |
| Lukas Sherman | Director | Leadership | Yes | Admin |
| Brian Kent Sherman | PM | Leadership | Yes | Project Manager |
| Astuti | PM | Leadership | No | Needs login |
| 95 Designers | Mid/Senior | Design | No | Email-based workflow |

**Gap:** No RBAC exists. Everyone with login sees everything.

### 2.2 Frontend Pages (15 Total)

| Page | Route | Current Function | Fits Executive View? |
|------|-------|------------------|---------------------|
| Dashboard | `/` | Overview with many tabs | Needs simplification |
| Proposals | `/proposals` | Pipeline table | YES - Critical |
| Projects | `/projects` | Active projects list | YES - Critical |
| Tasks | `/tasks` | Kanban board | YES - Filtered |
| Tracker | `/tracker` | Proposal pipeline | MERGE with Dashboard |
| Finance | `/finance` | Invoice aging | YES - Critical |
| Emails | `/emails` | Email list | NO - Backend tool |
| Meetings | `/meetings` | Calendar/meeting list | YES - Simplified |
| Contacts | `/contacts` | Contact database | NO - Backend tool |
| Schedule | `/schedule` | Weekly schedule | NO - PM tool |
| Files | `/files` | Document browser | NO - PM tool |
| Settings | `/settings` | App settings | NO - Admin only |
| Search | `/search` | Global search | YES - Keep |
| My Day | `/my-day` | Personal dashboard | FUTURE |
| Suggestions | `/suggestions` | AI review queue | FUTURE |

### 2.3 Backend API Routers (39 Total)

| Router | Endpoints | Executive Relevance |
|--------|-----------|---------------------|
| proposals.py | CRUD, stats, quick actions | HIGH |
| projects.py | CRUD, phases, health | HIGH |
| invoices.py | Aging, outstanding | HIGH |
| finance.py | Metrics, trends | HIGH |
| tasks.py | Task management | MEDIUM |
| dashboard.py | Aggregate metrics | HIGH |
| weekly_report.py | Monday email | HIGH |
| suggestions.py | AI suggestions queue | MEDIUM |
| emails.py | Email management | LOW (backend) |
| contacts.py | Contact management | LOW |
| *35 others* | Various utilities | LOW |

### 2.4 Database Schema Summary

**Core Tables:** 108 total
- **Proposals:** proposals, proposal_status_history, proposal_follow_ups
- **Projects:** projects, project_phases, project_team, deliverables
- **Emails:** emails, email_content, email_proposal_links, email_project_links
- **Finance:** invoices, invoice_aging, contract_phases
- **AI/Learning:** ai_suggestions, email_learned_patterns, suggestion_decisions
- **Staff:** staff, team_members, staff_skills

---

## 3. User Roles & Permissions Matrix

### 3.1 Role Definitions

| Role | Person(s) | Input Mode | Dashboard Type | Access Level |
|------|-----------|------------|----------------|--------------|
| **Executive** | Bill, Brian | Review only | Strategic | Full read, limited write |
| **Director** | Lukas | Full access | Admin | Full CRUD, settings |
| **PM** | Astuti, Brian K | UI + Email | Operational | Own projects + tasks |
| **Designer** | 95 staff | Email only | None (future) | Daily work submission |
| **Finance** | TBD | UI | Financial | Invoices only |

### 3.2 Feature Access by Role

| Feature | Executive | Director | PM | Designer | Finance |
|---------|-----------|----------|-----|----------|---------|
| View proposals | All | All | Assigned | None | Summary |
| Edit proposals | Quick actions | Full | Limited | None | None |
| View projects | All | All | Assigned | None | Summary |
| View financials | All | All | Own | None | All |
| Approve suggestions | Yes | Yes | Own | None | None |
| Manage staff | No | Yes | No | No | No |
| View emails | Summary | All | Own | None | None |
| Create tasks | No | Yes | Yes | Via email | No |

### 3.3 Data Visibility Rules

```typescript
// Pseudo-code for role-based filtering
interface RoleFilter {
  executive: { /* all data, no filters */ },
  pm: {
    projects: "WHERE pm_id = current_user OR team_member",
    proposals: "WHERE assigned_to = current_user",
    emails: "WHERE project IN (user_projects)",
  },
  designer: {
    // Future: only their submitted work
  },
  finance: {
    projects: "SELECT financial_columns ONLY",
    invoices: "all",
  }
}
```

---

## 4. Executive Dashboard Design

### 4.1 Design Principles (From Research)

Based on [2025 dashboard design best practices](https://www.domo.com/learn/article/operational-vs-executive-dashboards):

1. **Strategic over Operational** - High-level KPIs, not granular data
2. **5-second rule** - Key metrics visible immediately
3. **Drill-down optional** - Summary first, details on demand
4. **AI-curated** - System surfaces what needs attention
5. **Minimal input** - Designed for consumption, not data entry

### 4.2 Executive View Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTIVE DASHBOARD                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PIPELINE     │  │ ACTIVE       │  │ OUTSTANDING  │          │
│  │ $42.5M       │  │ PROJECTS     │  │ INVOICES     │          │
│  │ 47 proposals │  │ 23 active    │  │ $2.1M        │          │
│  │ ↑ 3 this week│  │ 15 countries │  │ 4 critical   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ NEEDS YOUR ATTENTION (AI-Curated)                    [View]││
│  │ ───────────────────────────────────────────────────────────││
│  │ 1. Nusa Dua - No response in 21 days          [Follow Up] ││
│  │ 2. La Vie - Contract ready for signature      [View]      ││
│  │ 3. Invoice #1234 - 95 days outstanding        [Escalate]  ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │ PROPOSAL PIPELINE       │  │ THIS WEEK'S ACTIVITY        │  │
│  │ ───────────────────────│  │ ─────────────────────────── │  │
│  │ First Contact    12    │  │ Mon: 3 meetings, 2 proposals │  │
│  │ Proposal Sent    18    │  │ Tue: Site visit Nusa Dua     │  │
│  │ Negotiation       8    │  │ Wed: Today                   │  │
│  │ On Hold           5    │  │ Thu: Call with Vahine        │  │
│  │ Contract Signed   4    │  │ Fri: Review session          │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ RECENT WINS & LOSSES                                       ││
│  │ ✓ Won: Taiwan Taitung ($3.2M) - Jan 15                    ││
│  │ ✗ Lost: Dubai Marina ($1.8M) - Jan 12                     ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Executive Actions (Minimal Input)

Bill should be able to do these with 1-2 clicks:

| Action | Current UI | Proposed |
|--------|------------|----------|
| Mark proposal Won | Navigate to detail page | Quick action button on row |
| Mark proposal Lost | Navigate to detail page | Quick action button on row |
| Schedule follow-up | No easy way | "Follow Up" button → datepicker |
| Approve suggestion | Suggestions page | Inline approve/reject |
| View full history | Multiple clicks | "Story" button → modal |

### 4.4 Navigation Simplification

**Current Navigation (15 items):**
```
Dashboard | Proposals | Projects | Tasks | Tracker | Finance |
Emails | Meetings | Contacts | Schedule | Files | Settings |
Search | My Day | Suggestions
```

**Proposed Executive Navigation (6 items):**
```
Dashboard | Pipeline | Projects | Finance | Calendar | Search
```

Where:
- **Dashboard** = Executive view (KPIs + Needs Attention)
- **Pipeline** = Proposals (merged Tracker)
- **Projects** = Active projects with financials
- **Finance** = Invoice aging + collections
- **Calendar** = Meetings + deadlines
- **Search** = Global search

Hidden from Executive View:
- Emails (backend tool)
- Contacts (backend tool)
- Schedule (PM tool)
- Files (PM tool)
- Settings (Admin only)
- Tasks (embedded in projects)
- Suggestions (embedded inline)

---

## 5. Data Flow Architecture

### 5.1 Email-First Data Flow

```
                          INCOMING DATA
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   lukas@bensley.com    projects@bensley.com   dailywork@bensley.com
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  EMAIL IMPORTER     │
                    │  (scheduled_sync)   │
                    └─────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  PATTERN MATCHER    │
                    │  (pattern_first)    │
                    └─────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
        Match Found?                      No Match
              │                                 │
              ▼                                 ▼
    Auto-link to Project/           Queue for AI Analysis
    Proposal (confidence >0.90)           │
              │                           ▼
              │                 ┌─────────────────────┐
              │                 │  CLAUDE ANALYSIS    │
              │                 │  (with DB context)  │
              │                 └─────────────────────┘
              │                           │
              └───────────┬───────────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │  AI SUGGESTIONS     │
                │  (for Bill to review│
                └─────────────────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │  BILL APPROVES      │
                │  (1-click actions)  │
                └─────────────────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │  LEARNING LOOP      │
                │  (patterns updated) │
                └─────────────────────┘
```

### 5.2 UI Input Data Flow (Secondary)

```
                    PM / LUKAS INPUT
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   Proposal Status    Project Update     Invoice Added
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │  API ENDPOINTS     │
                 │  (proposals, etc)  │
                 └────────────────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │  AUDIT LOG         │
                 │  (who changed what)│
                 └────────────────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │  DASHBOARD REFRESH │
                 └────────────────────┘
```

---

## 6. Implementation Plan - GitHub Issue Roadmap

### The Vision (From Lukas)

> "Right now, all the information is siloed. If you want to know something about finances, you go to the finance lady, she has shitty Excel templates, you have to ask her, wait..."
> "But if you want the information RIGHT NOW, you can't."
> "The system needs to have all that information so Bill/Brian can always check, always see, whenever they want."

### Current vs Target State

| System | Current | Target |
|--------|---------|--------|
| **Proposals** | 80% done | Fully automated reports |
| **Project Management** | 10% done | THE BIG BUILD |
| **Finance** | 40% done | Self-serve dashboards |
| **Social Media** | 0% | Future |

---

### SEQUENCED ISSUE ROADMAP

**No dates. Just order. What blocks what.**

#### FIRST: Data Cleanup
Can't build on broken data.

| Issue | Title | Priority | Blocks |
|-------|-------|----------|--------|
| #306 | Fix orphaned project_team records | P0 | Team views |
| #307 | Fix duplicate invoices ($12.7M) | P0 | Finance reports |
| #308 | Fix orphaned invoice_aging records | P0 | Aging dashboard |
| #60 | Review old invoices | P0 | Business decision |

#### SECOND: Backfill Infrastructure
Get data INTO the system. Build forms for input.

| Issue | Title | Priority | Enables |
|-------|-------|----------|---------|
| #309 | [EPIC] Project Management System | P0 | Everything below |
| #310 | Task Management UI (Discipline/Phase) | P1 | PMs enter all tasks |
| #313 | Deliverables CRUD & Tracking | P1 | Track what's due |
| #311 | Daily Work Collection & Review | P1 | Designer submissions |

#### THIRD: Visibility Layer
See the data that's now flowing in.

| Issue | Title | Priority | Enables |
|-------|-------|----------|---------|
| #312 | Weekly Scheduling UI | P1 | Consolidated schedule view |
| #319 | Executive Dashboard | P1 | Bill/Brian self-serve |
| #292 | Suggestion Review UI | P1 | Fast approval queue |

#### FOURTH: Cleanup & Access Control
Polish the system, add role-based views.

| Issue | Title | Priority | Enables |
|-------|-------|----------|---------|
| #316 | Fix duplicate suggestions | P1 | Clean review queue |
| #317 | Consolidate email categories | P1 | One category system |
| #318 | RBAC Implementation | P1 | PMs see only their projects |

#### FIFTH: Meeting Integration
Connect meetings to everything else.

| Issue | Title | Priority | Enables |
|-------|-------|----------|---------|
| #314 | Meeting → Tasks Pipeline | P2 | Action items flow to tasks |
| #209 | MS Calendar Integration | P2 | Auto-import meetings |
| #320 | Weekly Report Enhancements | P2 | Include meeting summaries |

#### LATER: Analytics & Intelligence
Once data collection is solid.

| Issue | Title | Priority |
|-------|-------|----------|
| #315 | Capacity Planning | P2 |
| #210 | Gantt Chart | P2 |
| #198 | Vector Embeddings | P2 |
| #199 | AI Query Interface | P2 |
| #200 | Proactive Alerts | P2 |

#### FUTURE: Local AI

| Issue | Title | Priority |
|-------|-------|----------|
| #201 | Ollama Integration | P2 |
| #202 | Fine-tune Bensley Model | P2 |
| #203 | Creative Archive (40 years) | P2 |

---

### DEPENDENCY GRAPH

```
Data Cleanup (#306, #307, #308, #60)
    │
    ▼
Backfill Infrastructure (#309, #310, #311, #313)
    │
    ▼
Visibility Layer (#312, #319, #292)
    │
    ▼
Access Control (#316, #317, #318)
    │
    ▼
Meeting Integration (#314, #209, #320)
    │
    ▼
Analytics (#315, #210, #198-200)
    │
    ▼
Local AI (#201, #202, #203)
```

---

### THE FOUR SYSTEMS

#### 1. Proposals (Lukas's Job) - 80% Done
- Weekly reports to Bill ✓
- Track all proposals, fees, revisions ✓
- Bill/Brian can self-serve check status
- Remaining: #320 Weekly Report Enhancements

#### 2. Project Management - THE BIG BUILD
Epic: #309

> "Projects, we haven't done anything yet. That's going to need a lot of work."
> "The project management is the difficult thing - actually managing the designers."

What it encompasses:
- **Tasks by Discipline/Phase** (#310) - Interior, Landscape, Lighting, FF&E
- **Daily Work Collection** (#311) - What designers did today
- **Weekly Scheduling** (#312) - Who works on what
- **Deliverables Tracking** (#313) - What's due when
- **Meeting → Tasks** (#314) - Transcripts become action items
- **Capacity Planning** (#315) - How many projects can we take?

#### 3. Finance - 40% Done
- Invoice aging exists ✓
- Revenue trends exist ✓
- Remaining: Fix data quality (#307, #308), cash flow forecasting

#### 4. Social Media - Future
- Instagram analytics
- Content planning
- Not started yet

---

## 7. Technical Specifications

### 7.1 New Database Tables

```sql
-- Role-based access control
CREATE TABLE IF NOT EXISTS user_roles (
  role_id INTEGER PRIMARY KEY AUTOINCREMENT,
  role_name TEXT UNIQUE NOT NULL,
  can_view_all_proposals BOOLEAN DEFAULT 0,
  can_edit_proposals BOOLEAN DEFAULT 0,
  can_view_all_projects BOOLEAN DEFAULT 0,
  can_edit_projects BOOLEAN DEFAULT 0,
  can_view_financials BOOLEAN DEFAULT 0,
  can_approve_suggestions BOOLEAN DEFAULT 0,
  can_manage_staff BOOLEAN DEFAULT 0,
  can_view_all_emails BOOLEAN DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Default roles
INSERT INTO user_roles (role_name, can_view_all_proposals, can_edit_proposals, can_view_all_projects, can_edit_projects, can_view_financials, can_approve_suggestions, can_manage_staff, can_view_all_emails) VALUES
  ('executive', 1, 0, 1, 0, 1, 1, 0, 0),
  ('director', 1, 1, 1, 1, 1, 1, 1, 1),
  ('pm', 0, 0, 0, 1, 0, 1, 0, 0),
  ('designer', 0, 0, 0, 0, 0, 0, 0, 0),
  ('finance', 0, 0, 0, 0, 1, 0, 0, 0),
  ('viewer', 0, 0, 0, 0, 0, 0, 0, 0);
```

### 7.2 New API Endpoints

```python
# backend/api/routers/executive.py

@router.get("/executive/dashboard")
async def get_executive_dashboard(current_user: User = Depends(get_current_user)):
    """Executive-specific dashboard with aggregated KPIs"""

@router.get("/executive/needs-attention")
async def get_needs_attention(current_user: User = Depends(get_current_user)):
    """AI-curated list of items needing executive review"""

@router.post("/executive/quick-action/{action_type}")
async def execute_quick_action(
    action_type: str,  # won, lost, follow_up, approve, reject
    target_id: int,
    current_user: User = Depends(get_current_user)
):
    """Execute quick actions with minimal input"""
```

### 7.3 Frontend Components

```typescript
// New components needed
components/
  executive/
    executive-dashboard.tsx      // Main executive view
    needs-attention-widget.tsx   // AI-curated action items
    quick-action-buttons.tsx     // Won/Lost/Follow-up
    inline-suggestion.tsx        // Approve/reject inline
    story-modal.tsx              // Full history view
  layout/
    role-nav.tsx                 // Role-based navigation
```

---

## 8. Success Metrics

### Bill's Experience
- [ ] Can see pipeline health in <5 seconds
- [ ] Can mark proposal Won/Lost with 1 click
- [ ] Sees AI suggestions inline (no separate page)
- [ ] Doesn't see operational tools (emails, files, schedule)

### System Health
- [ ] 90%+ emails auto-linked via patterns
- [ ] <50 suggestions/day needing manual review
- [ ] Suggestion approval rate >80%
- [ ] Pattern accuracy >95%

### Data Quality
- [ ] 0 orphaned email links
- [ ] All proposals have last_contact_date
- [ ] All projects have PM assigned
- [ ] Invoice aging accurate to database

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Bill finds UI too complex | High | Start with minimal view, add on request |
| RBAC breaks existing flows | Medium | Test thoroughly before deploying |
| Pattern matching too aggressive | Medium | Keep approval queue, don't auto-apply |
| Email channel confusion | Low | Clear documentation, gradual rollout |

---

## 10. References

- [Domo: Operational vs Executive Dashboards](https://www.domo.com/learn/article/operational-vs-executive-dashboards)
- [UXPin: Dashboard Design Principles 2025](https://www.uxpin.com/studio/blog/dashboard-design-principles/)
- [Improvado: Dashboard Design Best Practices](https://improvado.io/blog/dashboard-design-guide)
- [Think Design: Three Types of Dashboards](https://think.design/blog/three-types-of-dashboards/)

---

## Appendix A: Current Navigation Inventory

| Route | Page | Components | API Calls |
|-------|------|------------|-----------|
| `/` | Dashboard | OverviewTab, ActiveProjectsTab, FinancialDashboard | Multiple |
| `/proposals` | Proposals | ProposalTable, filters, stats | GET /proposals |
| `/projects` | Projects | ProjectTable, TaskKanban, Timeline | GET /projects/active |
| `/tasks` | Tasks | TaskKanban, TaskList | GET /tasks |
| `/tracker` | Tracker | ProposalPipeline | GET /proposals |
| `/finance` | Finance | InvoiceAging, RevenueTrends | GET /finance/* |
| `/emails` | Emails | EmailList, EmailDetail | GET /emails |
| `/meetings` | Meetings | MeetingList, Calendar | GET /meetings |
| `/contacts` | Contacts | ContactTable | GET /contacts |
| `/schedule` | Schedule | WeeklySchedule | GET /schedule |
| `/files` | Files | FileExplorer | GET /files |
| `/settings` | Settings | AppSettings | GET /settings |
| `/search` | Search | GlobalSearch | GET /search |
| `/my-day` | My Day | PersonalDashboard | Various |

## Appendix B: Email Channel Plan

| Channel | Address | Purpose | Processing |
|---------|---------|---------|------------|
| Primary | lukas@bensley.com | Proposals, BD | Active |
| Projects | projects@bensley.com | Client comms, RFIs | Planned Jan |
| Daily Work | dailywork@bensley.com | Designer submissions | Planned Jan |
| Bill | bill@bensley.com | Bill's inbox | Planned (needs approval) |
| Invoices | invoices@bensley.com | Payment tracking | Planned Feb |
| Scheduling | scheduling@bensley.com | PM coordination | Planned Feb |

---

## Appendix C: DEEP FRONTEND AUDIT (Per-Page Analysis)

### Pages by Status

**Fully Functional (Production Ready):**

| Page | Route | Key Features | API Calls | User Type |
|------|-------|--------------|-----------|-----------|
| Dashboard | `/` | KPI cards, status breakdown, proposals needing follow-up | getProposalStats, getProposals, getInvoiceAging, getActiveProjects | Executive |
| Proposals Detail | `/proposals/[code]` | Story tab, stakeholders, documents, timeline, tasks | getProposalDetail, getProposalTimeline | Executive, PM |
| Projects | `/projects` | Phase distribution, filters, kanban tasks, timeline | getActiveProjects, getTasks | PM, Executive |
| Projects Detail | `/projects/[code]` | 7 tabs (Overview, Phases, Daily Work, Deliverables, Team, Tasks, Finance) | getProjectDetail, getInvoicesByProject, getProjectPhases, getProjectTeam | PM |
| Tasks | `/tasks` | Kanban/List views, drag-drop, snooze, complete | getTasks, stats | PM, Team |
| Tracker | `/tracker` | Pipeline funnel, saved views, quick actions (Won/Lost), export | getProposalTrackerStats, getProposalTrackerList | Executive |
| Finance | `/finance` | Invoice aging, revenue trends, client payment behavior | getDashboardFinancialMetrics, getInvoiceAging, getRevenueTrends | Executive, Finance |
| Meetings | `/meetings` | Calendar/List views, meeting detail modal, transcript summary | getMeetings | Executive, PM |
| My Day | `/my-day` | Personalized: overdue tasks, today's meetings, AI suggestions, week ahead | getMyDay (auto-refresh 60s) | PM, Team |

**Redirects/Placeholders:**

| Page | Route | Status | Notes |
|------|-------|--------|-------|
| Proposals | `/proposals` | Redirect | → `/tracker` |
| Contacts | `/contacts` | Placeholder | Intentional - directs to project contacts (Issue #240) |
| Suggestions | `/suggestions` | Redirect | → `/admin/suggestions` (Issue #232) |

**Missing from Codebase:**
- `/schedule` - Not implemented
- `/files` - Not implemented
- `/settings` - Not implemented
- `/search` - Not implemented

### Technical Patterns Observed

- **Data Fetching:** React Query with 5-minute stale times
- **State Management:** Local useState + Query Client mutations
- **Authentication:** Session-based with RBAC hooks (canViewFinancials)
- **URL Encoding:** Proper handling of project codes like "24 BK-033"
- **Error Handling:** Skeleton loaders, error states, retry buttons
- **Real-Time:** My Day refreshes every 60 seconds

---

## Appendix D: DEEP BACKEND AUDIT (All Routers)

### Router Summary

| Router | Lines | Endpoints | Status | Frontend Uses |
|--------|-------|-----------|--------|---------------|
| suggestions.py | 2,720 | 27 | Fully Functional | Yes - Queue |
| projects.py | 2,373 | 30+ | Fully Functional | Yes - Heavy |
| proposals.py | 1,553 | 25 | Fully Functional | Yes - Heavy |
| admin.py | 1,532 | 20+ | Fully Functional | Admin only |
| dashboard.py | 1,308 | 8 | Fully Functional | Yes |
| emails.py | 976 | 28 | Fully Functional | Yes |
| tasks.py | 785 | 10 | Fully Functional | Yes |
| transcripts.py | 620 | 12 | Fully Functional | Yes |
| team.py | 519 | 12 | Fully Functional | Yes |
| rfis.py | 461 | 12 | Fully Functional | Yes |
| contacts.py | 440 | 10 | Fully Functional | Yes |
| invoices.py | 415 | 14 | Fully Functional | Yes |
| activities.py | 384 | 12 | Fully Functional | Yes |
| my_day.py | 363 | 10 | Fully Functional | Yes |
| deliverables.py | 354 | 11 | Fully Functional | Yes |
| analytics.py | 323 | 8 | Fully Functional | Yes |
| finance.py | 298 | 6 | Fully Functional | Yes (RBAC) |
| meetings.py | 261 | 9 | Fully Functional | Yes |

**Total: 39 routers, 200+ endpoints, 35+ database tables touched**

### Key API Patterns

1. **Standardized Response Format (Issue #126)**
   - `list_response()` for paginated lists
   - `item_response()` for single items
   - `action_response()` for POST/PUT/DELETE

2. **RBAC Implementation**
   - `finance.py` uses `require_role("executive", "finance")`
   - `projects.py` filters by PM assignment
   - Dashboard stats role-based

3. **Learning Loop (emails.py + suggestions.py)**
   - NEVER auto-links (all suggestions require approval)
   - Pattern learning from approvals
   - Rejection tracking

---

## Appendix E: CRITICAL DATA QUALITY ISSUES

### Issues Found (Database Audit)

| Issue | Count | Impact | Priority |
|-------|-------|--------|----------|
| **Orphaned project_team records** | 168 | Team assignments broken | P0 |
| **Orphaned invoice_aging records** | 33 (50%) | Aging reports unreliable | P0 |
| **Duplicate invoice numbers** | 47 (116 rows, $12.7M) | Financial reporting | P0 |
| **Contract Signed without project** | 5 | Workflow gap | P1 |
| **Projects missing client_id** | 67 (100%) | Client relationship | P1 |
| **Contacts missing client_id** | 467 (100%) | Client relationship | P1 |
| **Staff missing last_name** | 87 (87%) | Incomplete directory | P2 |
| **Unlinked emails** | 1,465 (38%) | Lost context | P2 |
| **Empty deliverables table** | 0 rows | Feature unused | P3 |
| **Empty suggestion_decisions** | 0 rows | Audit trail missing | P3 |

### Data Integrity Notes

- SQLite does NOT enforce foreign keys by default
- Application-level validation has allowed orphans
- Recommendation: Enable FK enforcement + cleanup script

### What's Working Well

- No duplicate primary keys
- Email categorization 100% complete
- Core FK relationships (email→proposal/project) clean
- AI suggestions 97% processed
- Email linking confidence scores high (0.84-0.99)

---

## Appendix F: EMAIL PIPELINE DEEP ANALYSIS

### Complete Flow

```
SCHEDULED_EMAIL_SYNC (every 15 min)
  │
  ├─→ [1] IMAP SYNC → emails table
  │   Trigger: Cron/LaunchAgent
  │   Tables: emails
  │
  ├─→ [2] PATTERN-FIRST LINKER (pattern_first_linker.py)
  │   Priority Order:
  │   1. Skip spam (noreply@, newsletter@, zoom.us, etc)
  │   2. Thread inheritance (95% confidence)
  │   3. Project code in subject [25 BK-070] (98% confidence)
  │   4. Sender pattern match (learned)
  │   5. Domain pattern match (learned)
  │   6. Keyword pattern match (lowest priority)
  │   7. No match → needs_gpt
  │   Tables: email_proposal_links, email_project_links, ai_suggestions
  │
  ├─→ [3] EMAIL ORCHESTRATOR
  │   ├─→ Pattern Linker (redundant, high-recall)
  │   ├─→ Meeting Summary Parser → tasks table
  │   └─→ AI Learning Service (GPT) → SuggestionWriter
  │       Tables: ai_suggestions, emails, contact_context
  │
  └─→ [4] BATCH SUGGESTION SERVICE
      Confidence Tiers:
      - AUTO_APPROVE (>0.90): Auto-link immediately
      - BATCH_REVIEW (0.70-0.90): Group by sender
      - INDIVIDUAL (0.50-0.70): Per-email review
      - LOG_ONLY (<0.50): Skip
      Tables: suggestion_batches, batch_emails, email_learned_patterns
```

### Pattern Learning Loop

```
User Approves Suggestion
  ↓
extract_patterns_from_email_suggestion()
  ↓
store_email_pattern():
  - If exists: confidence += 0.05, times_correct += 1
  - If new: INSERT with confidence=0.75
  ↓
Log to learning_events table
```

### Known Issues

| Issue | Description | Fix |
|-------|-------------|-----|
| Duplicate suggestions | Pattern linker creates `link_review`, GPT creates `email_link` for same email | Add dedup check |
| Auto-apply not aggressive | 98% confidence still creates suggestion | Auto-apply for >95% |
| Batch unknowns lost | Low confidence logged but never analyzed by GPT | Escalate to GPT |
| Three category systems | `primary_category`, `email_type`, `email_content.category` | Consolidate to one |
| Learning high friction | Must approve suggestion to trigger pattern boost | Add explicit "learn" button |

---

## Appendix G: ARCHIVED/DEPRECATED CODE

### Archived Services (backend/services/archive/)

| File | Purpose | Status |
|------|---------|--------|
| cli_review_helper.py | CLI suggestion review | Archived |
| comprehensive_auditor.py | System audit | Archived |
| email_category_service.py | Old categorization | Replaced |
| email_content_processor_claude.py | Claude processor | Archived |
| email_link_processor.py | Old linker | Replaced by pattern_first_linker |
| email_tagger_service.py | Old tagging | Replaced |
| excel_importer.py | One-time import | Archived |
| file_organizer.py | File sorting | Archived |
| schedule_email_parser.py | Schedule parsing | Archived |
| schedule_emailer.py | Email scheduling | Archived |
| schedule_pdf_parser.py | PDF parsing | Archived |

### Deprecated in Active Code

| File | Line | Comment |
|------|------|---------|
| follow_up_agent.py | 529 | "DEPRECATED: Individual follow_up suggestions are now replaced with weekly report" |
| email_content_processor_claude.py | 448 | "key_points (deprecated)" |

### TODO/FIXME Comments

| File | Issue |
|------|-------|
| schedule_email_parser.py:278 | "TODO: Match nickname to member_id from team_members table" |

---

## Appendix H: USER WORKFLOW MAPPING

### Bill's Daily Workflow (Executive)

```
Morning:
1. Open Dashboard → See KPIs, "Needs Attention" list
2. Click proposal needing follow-up → View story/timeline
3. Mark as "Followed Up" or "Won/Lost"
4. Check meetings for today
5. Review any AI suggestions inline

Afternoon:
1. Check Finance tab for invoice aging
2. Escalate critical invoices

Weekly:
1. Review Monday morning email report (automated)
2. Check pipeline trends
```

### PM Workflow (Astuti/Brian K)

```
Daily:
1. Open My Day → See overdue tasks, today's meetings
2. Complete tasks or snooze
3. Open Projects → Check their assigned projects
4. Review deliverables status
5. Submit daily work (if applicable)

Weekly:
1. Update project phases
2. Review team workload
3. Respond to RFIs
```

### Designer Workflow (95 staff)

```
Daily:
1. Send email to dailywork@bensley.com with attachments
2. (No UI access currently)

Future:
1. Submit via web form
2. See feedback from Bill/Brian
```

---

## Appendix I: GITHUB ISSUES BY PRIORITY

### P0 - Critical (Do First)

| Issue | Title | Area |
|-------|-------|------|
| #306 | Fix orphaned project_team records | Database |
| #307 | Fix duplicate invoices ($12.7M) | Database |
| #308 | Fix orphaned invoice_aging records | Database |
| #309 | [EPIC] Project Management System | Projects |
| #60 | Review old invoices (business decision) | Finance |

### P1 - High (Do After P0s)

| Issue | Title | Area |
|-------|-------|------|
| #310 | Task Management UI (Discipline/Phase) | Projects |
| #311 | Daily Work Collection & Review | Projects |
| #312 | Weekly Scheduling UI | Projects |
| #313 | Deliverables CRUD & Tracking | Projects |
| #316 | Fix duplicate suggestions | Email |
| #317 | Consolidate email categories | Email |
| #318 | RBAC Implementation | Security |
| #319 | Executive Dashboard | Frontend |
| #292 | Suggestion Review UI | Learning |

### P2 - Medium (Do After P1s)

| Issue | Title | Area |
|-------|-------|------|
| #314 | Meeting → Tasks Pipeline | Meetings |
| #315 | Capacity Planning | Analytics |
| #320 | Weekly Report Enhancements | Proposals |
| #209 | MS Calendar Integration | Meetings |
| #210 | Gantt Chart | Projects |
| #208 | Document Parsing | Infrastructure |
| #211 | Error Tracking (Sentry) | Infrastructure |
| #198 | Vector Embeddings | Intelligence |
| #199 | AI Query Interface | Intelligence |
| #200 | Proactive Alerts | Intelligence |
| #201 | Ollama Integration | Local AI |
| #202 | Fine-tune Bensley Model | Local AI |
| #203 | Creative Archive | Local AI |
| #22 | OneDrive Cleanup | Infrastructure |

### Documentation & Research

| Issue | Title |
|-------|-------|
| #214 | Data Linking Reference |
| #151 | Dashboard Library Research |
| #205 | Research Agent (ongoing) |
