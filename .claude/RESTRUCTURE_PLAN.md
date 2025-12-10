# COMPREHENSIVE RESTRUCTURE PLAN - Bensley Operations Platform

**Created:** 2025-12-10
**Status:** Draft for Review

---

## EXECUTIVE SUMMARY

**Current State:** Working infrastructure, broken UX
**Problem:** 33 pages with no clear user journey. Bill can't find what he needs.
**Solution:** Role-based dashboards + contextual intelligence + commitment tracking
**Inspiration:** Monday.com's visual boards + Asana's portfolio view + Notion's linked databases

**Success Metric:** Bill opens this FIRST every morning, not email.

---

## PM SOFTWARE RESEARCH

Based on 2025 comparisons (Monday.com, Asana, Notion), winning patterns:

1. **Customizable Dashboards** (Monday) - 30-40 widget library, drag-and-drop
2. **Multiple Views** (Asana/Monday) - Table, Kanban, Calendar, Timeline, Map
3. **Linked Records** (Notion) - Click proposal → see ALL related data
4. **Smart Notifications** (Asana) - Push to user, daily digest emails
5. **Automation Rules** (Monday) - "When X happens, do Y"

---

## USER PERSONAS

### Bill Bensley (Executive)
**Daily Questions:**
- "What proposals need my attention TODAY?"
- "What's happening with [project name]?"
- "Where's my pipeline? What's our total value?"

**Dashboard Needs:**
- Executive KPIs (pipeline value, active projects, cash flow)
- Hot items requiring action
- Recent activity feed
- Quick search/query

### Project Manager (Spot/Aood/Ouant)
**Daily Questions:**
- "What deliverables are due this week?"
- "What RFIs need responses?"
- "What's my team's workload?"

**Dashboard Needs:**
- My Projects list (filtered to their assignments)
- Deliverables calendar
- RFI queue
- Team workload view

### Finance/Admin
**Daily Questions:**
- "Which invoices are overdue?"
- "What's our cash flow projection?"
- "Payment aging report?"

**Dashboard Needs:**
- Invoice aging
- Payment trends by client
- Outstanding receivables
- Cash flow projection

---

## PROPOSED PAGE STRUCTURE (15 Pages)

**Current:** 33 pages, poorly organized
**Proposed:** 15 core pages, role-based

```
HOME DASHBOARD (role-based)
├── Executive View (Bill)
├── PM View (Spot/Aood)
└── Finance View (Admin)

PROPOSALS (Bill's #1 Priority)
├── Pipeline Table/Kanban/Map
├── [Project Code] Detail Page
└── Weekly Report

PROJECTS (Active Contracts)
├── Projects List
├── [Project Code] Detail Page
├── Deliverables Calendar
└── RFIs Queue

INTELLIGENCE (AI Features)
├── Query/Search
├── Suggestions Review
├── Pattern Learning
└── Meeting Transcripts

OPERATIONS
├── Contacts
├── Finance/Invoices
├── Team/Assignments
└── System/Admin
```

---

## PAGE SPECIFICATIONS

### Page 1: HOME DASHBOARD (Role-Based)

**Bill's View:**
| Widget | Data Source | Purpose |
|--------|-------------|---------|
| KPI Cards | `proposals`, `projects`, `invoices` | Pipeline value, active count, outstanding |
| Hot Items | `v_proposal_priorities` | URGENT/FOLLOW UP items |
| Recent Activity | `emails`, `meetings`, `proposals` | Last 7 days activity |
| Query Widget | `query_service` | Ask anything |
| This Week's Meetings | `meetings` | Upcoming calendar |

**PM's View:**
| Widget | Data Source | Purpose |
|--------|-------------|---------|
| My Projects | `projects` filtered | Assigned projects only |
| Deliverables Due | `project_milestones` | This week's deadlines |
| RFIs Pending | `rfis` | Open items |
| Team Workload | `v_pm_workload` | Capacity view |

**Finance View:**
| Widget | Data Source | Purpose |
|--------|-------------|---------|
| Invoice Aging | `v_invoice_aging` | Overdue breakdown |
| Recent Payments | `invoices` | Last 10 payments |
| Cash Flow | `invoices` + projections | 30/60/90 day |
| Outstanding by Client | `invoices` grouped | Who owes what |

---

### Page 2: PROPOSALS - Pipeline Management

**Views:**
1. **Table View** (default) - Sortable, filterable
2. **Kanban View** - Drag proposals between statuses
3. **Map View** - Proposals by country/location
4. **Timeline View** - Expected decision dates

**Data Query:**
```sql
SELECT
    p.project_code,
    p.project_name,
    p.current_status,
    p.total_value,
    vpp.actual_last_contact,
    vpp.days_silent,
    vpp.priority_status,
    vpp.next_event,
    vpp.silence_reason,
    (SELECT COUNT(*) FROM email_proposal_links WHERE proposal_id = p.proposal_id) as email_count
FROM proposals p
LEFT JOIN v_proposal_priorities vpp ON p.project_code = vpp.project_code
WHERE p.current_status NOT IN ('Lost', 'Declined', 'Dormant')
```

---

### Page 3: PROPOSAL DETAIL - Single Source of Truth

**Sections:**
| Section | Data Source | Notes |
|---------|-------------|-------|
| Overview | `proposals` | Status, client, value, location |
| Stakeholders | `proposal_stakeholders` | All contacts (needs population) |
| Timeline | `emails` + `meetings` + `events` | Unified view |
| Emails | `email_proposal_links` | 1,926 links exist |
| Meetings | `meeting_transcripts` | 12 records |
| Documents | `proposal_documents` | Newly created table |
| Follow-ups | `proposal_follow_ups` | Newly created table |
| AI Suggestions | `ai_suggestions` | Inline for this proposal |

---

### Page 4: PROJECT DETAIL - Active Contract Overview

**Sections:**
| Section | Data Source | Notes |
|---------|-------------|-------|
| Project Info | `projects` | Phase, team, contract value |
| Team Assignments | `contact_project_mappings` | 150 records exist |
| Deliverables | `project_milestones` | Due dates, status |
| RFIs | `rfis` | Open items |
| Payments | `invoices` | 420 records |
| Emails | `email_project_links` | 519 links |
| Meetings | `meeting_transcripts` | Linked transcripts |

---

## INTELLIGENT FEATURES

### 1. Instant Context (Query System)
**Flow:**
1. Bill types: "What's happening with Nusa Dua?"
2. System identifies `project_code = '25 BK-033'`
3. Fetches ALL data in parallel
4. GPT summarizes into natural language
5. Returns structured response with citations

**Status:** ✅ Working (recently fixed Dec 10)

---

### 2. Commitment Tracking (NEW)

**Problem:** Current system only tracks "last contact date". Doesn't track COMMITMENTS.

**Solution:** Extract commitments from emails/meetings
- "I'll send you the proposal by Friday" → Creates action item
- System monitors: If Friday passes, flags as broken commitment
- Shows: "⚠️ Proposal promised 3 days ago - still pending"

**New Table:**
```sql
CREATE TABLE action_items_tracking (
    action_id INTEGER PRIMARY KEY,
    project_code TEXT,
    description TEXT,
    committed_by TEXT,  -- 'us' or 'client'
    due_date DATE,
    completed BOOLEAN DEFAULT 0,
    source_type TEXT,  -- 'email', 'meeting', 'manual'
    source_id INTEGER
);
```

---

### 3. Daily Briefing Email

**Bill's Morning Email (8am Bangkok):**
```
Good morning Bill,

HOT ITEMS (3):
🔴 25 BK-063 (Akyn Da Lat) - 34 days no contact
🟡 25 BK-039 (Wynn Marjan) - Negotiation, 12 days
⚠️ 25 BK-033 (Nusa Dua) - Invoice 45 days overdue

TODAY'S MEETINGS (2):
10am - Nusa Dua CD Review
2pm  - Siargao client call

PIPELINE: 50 active ($12.4M), 16 projects, $450K outstanding
```

---

### 4. Inline AI Suggestions

**On Proposal Page:**
```
┌─────────────────────────────────────────────────┐
│ ⚠️ AI SUGGESTION                               │
│                                                 │
│ No contact with Kim (Wynn) in 12 days.          │
│ Last email: Negotiation update (Nov 28)         │
│                                                 │
│ [Schedule Follow-up] [Dismiss] [Learn Pattern]  │
└─────────────────────────────────────────────────┘
```

---

## MISSING COMPONENTS

### Backend Endpoints Needed
1. `GET /api/dashboard/stats?role={bill|pm|finance}`
2. `GET /api/proposals/{code}/timeline`
3. `GET /api/proposals/{code}/stakeholders`
4. `GET /api/projects/{code}/deliverables`
5. `GET /api/projects/{code}/team`
6. `GET /api/team/workload`

### Frontend Components Needed
1. **Kanban Board** - `react-beautiful-dnd`
2. **Map View** - `react-leaflet`
3. **Calendar View** - `react-big-calendar`
4. **Gantt Chart** - Timeline view
5. **KPI Card** - Large metrics with trends
6. **Suggestion Card** - Yellow inline suggestions
7. **Pagination** - For contacts (50 of 546)

### Database Gaps
Tables exist but need DATA:
- `proposal_stakeholders` - 0 records
- `proposal_events` - 0 records
- `proposal_follow_ups` - 0 records
- `action_items_tracking` - TABLE DOESN'T EXIST (new)

---

## PHASED IMPLEMENTATION

### Phase 0: Foundation Fixes (1 week) ← CURRENT
- [✅] Fix query page
- [✅] Fix project detail API
- [✅] Fix hot items project names
- [ ] Fix contacts pagination
- [ ] Fix email review queue navigation

### Phase 1: Dashboard Restructure (2 weeks)
- Backend: Role-based stats, timeline APIs
- Frontend: Bill's dashboard, PM dashboard, Finance dashboard
- **Success:** Each user sees relevant dashboard on login

### Phase 2: Enhanced Detail Pages (2 weeks)
- Proposal detail (timeline, stakeholders, inline suggestions)
- Project detail (team, deliverables, RFIs, payments)
- **Success:** "What's happening with [project]?" → one page has everything

### Phase 3: Multiple Views (2 weeks)
- Proposals: Kanban, Map, Timeline views
- Projects: Kanban, Calendar, Gantt views
- **Success:** Users switch views easily

### Phase 4: Intelligence (3 weeks)
- Commitment tracking (GPT extracts from emails)
- Daily briefings (role-based email digests)
- Inline suggestions (show on pages)
- **Success:** Bill gets daily email, commitments auto-tracked

### Phase 5: Team Workload (1 week)
- `/team` page, workload charts, capacity planning
- **Success:** PMs see who's overloaded

### Phase 6: Polish (1 week)
- Pagination, loading states, error handling, mobile
- **Success:** System feels professional

---

## TIMELINE

| Month | Phase | Deliverables |
|-------|-------|--------------|
| Dec 2025 | 0 + 1 | Foundation + Dashboards |
| Jan 2026 | 2 + 3 | Detail pages + Multiple views |
| Feb 2026 | 4 + 5 | Intelligence + Team workload |
| Mar 2026 | 6 | Polish + Testing + Launch |

**Total:** 3 months to production

---

## SUCCESS METRICS

### Short-term (End of January)
- Bill opens platform daily (5+ days/week)
- Query usage (10+ queries/week)
- AI suggestions approved (80%+ rate)

### Medium-term (End of March)
- Daily active users (5+ including Bill, Lukas, PMs)
- Email coverage (95%+ categorized)
- Follow-up success (50%+ proposals get timely follow-up)

### Long-term (Q2 2026)
- Team adoption (15+ active users)
- Proposals close faster (20% reduction)
- Invoice collection (10% faster)
- **Bill says: "I can't work without this"**

---

## WHAT MAKES THIS DIFFERENT?

| Feature | Monday.com | Bensley Platform |
|---------|------------|------------------|
| Data model | Generic tasks | Proposals, Projects, RFIs |
| Email intelligence | Manual | Auto-suggests, learns |
| AI suggestions | No | Yes - learns from interactions |
| Instant context | No | Full history in seconds |
| Commitment tracking | Manual | Extracts from emails |
| Daily briefings | Generic | Role-based |
| Phase tracking | Generic | MOB, CD, DD, CDocs, CO |

**Key Advantage:** This system LEARNS. Monday.com is static.

---

## NEXT STEPS

1. **Finish Phase 0** - Contacts pagination, review queue nav
2. **Build Bill's Dashboard** - Role detection, enhanced widgets
3. **Enhance Proposal Detail** - Timeline, stakeholders
4. **Test with Bill** - Get feedback, adjust
5. **Iterate**

---

## SOURCES

- [Notion vs Asana vs Monday.com (2025)](https://ones.com/blog/notion-vs-asana-vs-monday-com/)
- [Notion vs Monday: Comparison (2025)](https://thebusinessdive.com/notion-vs-monday)
- [Ultimate Showdown 2025](https://ones.com/blog/picking-the-right-project-management-tool/)
