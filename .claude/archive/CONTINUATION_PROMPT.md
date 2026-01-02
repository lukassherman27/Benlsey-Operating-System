# CONTINUATION PROMPT - Multi-Agent Execution

**Created:** 2025-12-10
**Purpose:** Start fresh window, spawn agents to execute restructure plan

---

## SESSION SUMMARY (Dec 10, 2025)

### What Was Done
1. **Fixed 3 P0 bugs:**
   - Query page: Backend now returns raw response (not wrapped)
   - Project detail: SQL returns all needed fields + fallback to proposals
   - Project names: Daily briefing includes `project_name`

2. **Captured user requirements** (via questions):
   - Users: Bill (executive), PMs, Finance
   - Killer features: Instant context, commitment tracking, daily briefings, voice transcription
   - Dashboard: Role-based (Bill ≠ PM ≠ Finance)
   - AI suggestions: Inline + queue + daily email push

3. **Created comprehensive restructure plan:**
   - `.claude/RESTRUCTURE_PLAN.md` - Full page specs, data sources, phased implementation
   - Updated `.claude/HANDOFF.md` Section 22 - Vision & requirements
   - Updated `.claude/STATUS.md` - Fix details

### Files Updated This Session
- `backend/api/routers/query.py` - Fixed chat endpoint
- `backend/api/routers/projects.py` - Enhanced financial-summary
- `backend/api/routers/dashboard.py` - Added project_name to briefing
- `.claude/HANDOFF.md` - Added Section 22 (Vision & User Requirements)
- `.claude/STATUS.md` - Updated P0/P1 status
- `.claude/RESTRUCTURE_PLAN.md` - NEW comprehensive plan

---

## MASTER PROMPT FOR NEW SESSION

Copy everything below into a new Claude Code window:

---

## BENSLEY PLATFORM - MULTI-AGENT EXECUTION

You are the Coordinator for rebuilding the Bensley Operations Platform.

### READ THESE FILES FIRST (in order):
1. `.claude/RESTRUCTURE_PLAN.md` - The comprehensive plan (page specs, phases, timeline)
2. `.claude/HANDOFF.md` - Business context, user requirements (Section 22 is critical)
3. `.claude/STATUS.md` - Current state, what's fixed, what's broken
4. `docs/roadmap.md` - Overall vision

### THE GOAL
Transform from "developer tool" to "Bill's daily driver":
- 33 pages → 15 pages
- Role-based dashboards (Bill/PM/Finance)
- Instant context ("What's happening with Nusa Dua?")
- Commitment tracking (not just days-since-contact)
- Daily briefing emails

### PHASE 0 (REMAINING) - Fix These First
- [ ] Contacts pagination (shows 50 of 546)
- [ ] Email review queue in main navigation
- [ ] Verify all dashboard widget calculations

### PHASE 1 - Dashboard Restructure
Split into parallel workstreams:

**Backend:** New APIs for role-based stats, timeline, stakeholders, team
**Frontend:** Role detection, Bill/PM/Finance dashboards, enhanced components
**Data:** Populate empty tables (proposal_stakeholders, proposal_events)

### SPAWN THESE AGENTS IN PARALLEL

Use the Task tool with `run_in_background: true` for each agent.

---

**Agent 1: Backend - Dashboard APIs**
```
Create new dashboard endpoints for role-based stats.

READ: .claude/RESTRUCTURE_PLAN.md (Page 1 spec)
FILES: backend/api/routers/dashboard.py, backend/services/

Tasks:
1. GET /api/dashboard/stats?role=bill - Executive KPIs:
   - Pipeline value (SUM of active proposals)
   - Active projects count
   - Outstanding invoices total
   - Overdue invoices count

2. GET /api/dashboard/stats?role=pm - PM KPIs:
   - My projects count (needs user context later)
   - Deliverables due this week
   - Open RFIs count

3. GET /api/dashboard/stats?role=finance - Finance KPIs:
   - Total outstanding
   - Overdue by aging bucket (30/60/90+)
   - Recent payments (last 7 days)

Use existing tables: proposals, projects, invoices, v_proposal_priorities
Test each endpoint with curl before marking done.
```

---

**Agent 2: Backend - Timeline & Team APIs**
```
Create unified timeline and team assignment endpoints.

READ: .claude/RESTRUCTURE_PLAN.md (Page 3 and Page 4 specs)
FILES: backend/api/routers/proposals.py, backend/api/routers/projects.py

Tasks:
1. GET /api/proposals/{code}/timeline
   - Combine: emails (from email_proposal_links), meetings (meeting_transcripts), events (proposal_events)
   - Sort by date DESC
   - Include: type, date, title/subject, summary

2. GET /api/proposals/{code}/stakeholders
   - Query proposal_stakeholders table
   - Include contact details (name, email, role, company)

3. GET /api/projects/{code}/team
   - Query contact_project_mappings (150 records exist)
   - Join with contacts table
   - Group by discipline (Architecture, Interior, Landscape)

Test with real codes: 25 BK-033 (Nusa Dua), 25 BK-039 (Wynn)
```

---

**Agent 3: Frontend - Dashboard Components**
```
Build role-based dashboard components.

READ: .claude/RESTRUCTURE_PLAN.md (Page 1 spec)
FILES: frontend/src/components/dashboard/, frontend/src/app/(dashboard)/page.tsx

Tasks:
1. KPICard component:
   - Large number display
   - Label and subtitle
   - Trend indicator (up/down arrow + percentage)
   - Color variants (green/amber/red)

2. RoleSwitcher component:
   - Tabs or dropdown: Executive / PM / Finance
   - Store selection in localStorage
   - Conditionally render dashboard sections

3. ActivityFeed component:
   - Recent activity list (emails, meetings, status changes)
   - From last 7 days
   - Click to expand/navigate

4. Enhance existing HotItemsWidget:
   - Show project names (already fixed in backend)
   - Add "View Context" button → opens modal with full context

Use shadcn/ui components. Test in browser at localhost:3002.
```

---

**Agent 4: Frontend - Enhanced Detail Pages**
```
Enhance proposal and project detail pages.

READ: .claude/RESTRUCTURE_PLAN.md (Pages 3 and 4 specs)
FILES:
- frontend/src/app/(dashboard)/tracker/[projectCode]/page.tsx (or similar)
- frontend/src/app/(dashboard)/projects/[projectCode]/page.tsx
- frontend/src/components/

Tasks:
1. UnifiedTimeline component:
   - Vertical timeline display
   - Icons by type (email, meeting, document, event)
   - Expandable items (click to see full content)
   - Filters by type

2. StakeholdersCard component:
   - List of contacts with roles
   - Company, email, phone
   - "Add Stakeholder" button (for future)

3. InlineSuggestionCard component:
   - Yellow/amber card style
   - Shows AI suggestion text
   - Buttons: [Take Action] [Dismiss] [Learn Pattern]
   - Query ai_suggestions filtered by project_code

Wire to new backend APIs when they exist. Mock data initially if needed.
```

---

**Agent 5: Data Population**
```
Populate empty intelligence tables from existing data.

READ: .claude/RESTRUCTURE_PLAN.md (Database Gaps section)
DATABASE: database/bensley_master.db

Tables to populate:
1. proposal_stakeholders (currently 0 records):
   - Extract unique contacts from email_proposal_links
   - For each proposal, find distinct sender_email addresses
   - Match to contacts table where possible
   - Create suggestion for human review (don't auto-populate)

2. proposal_events (currently 0 records):
   - Create events from meeting_transcripts (12 records)
   - Match transcript.project_code to proposals
   - Event type: 'meeting'

3. Verify proposal_follow_ups logic:
   - Check v_proposal_priorities view is working
   - Ensure days_silent calculation is correct

IMPORTANT: Create ai_suggestions for human review. DO NOT auto-insert.
Output: Report of suggestions created for review.
```

---

### COORDINATION RULES

1. **Read the plan first** - All agents must read RESTRUCTURE_PLAN.md
2. **Agents work in parallel** - Backend and Frontend can run simultaneously
3. **Backend before Frontend for NEW APIs** - If frontend needs API that doesn't exist, wait
4. **Test everything** - Backend: curl. Frontend: browser at localhost:3002
5. **Update STATUS.md** - Each agent reports what they completed
6. **Don't create random files** - Use existing folder structure
7. **Always include project names** - Never show bare project codes

### SUCCESS CRITERIA

Phase 0 + 1 complete when:
- [ ] Contacts page shows all 546 with pagination
- [ ] Review queue is in main navigation
- [ ] Bill's dashboard shows real KPIs (pipeline value, active projects, outstanding)
- [ ] Proposal detail shows unified timeline
- [ ] Project detail shows team assignments
- [ ] No console errors in browser
- [ ] All widgets show real data (verified against database)

### START SEQUENCE

1. Read the 4 context files listed above
2. Spawn Agent 5 (Data) first - it populates tables others need
3. Spawn Agents 1 & 2 (Backend) in parallel
4. Spawn Agents 3 & 4 (Frontend) after backend APIs exist
5. Coordinate, handle issues, report progress
6. Update STATUS.md when each phase completes

---

## QUICK REFERENCE

### Key Tables
| Table | Records | Purpose |
|-------|---------|---------|
| proposals | 102 | Sales pipeline |
| projects | 60 | Active contracts |
| emails | 3,773 | All synced emails |
| email_proposal_links | 1,926 | Email→proposal mapping |
| invoices | 420 | Payment tracking |
| v_proposal_priorities | view | URGENT/FOLLOW UP calc |
| contact_project_mappings | 150 | Team assignments |
| proposal_stakeholders | 0 | EMPTY - needs population |
| proposal_events | 0 | EMPTY - needs population |

### Key Frontend Files
| Purpose | File |
|---------|------|
| Main dashboard | `frontend/src/app/(dashboard)/page.tsx` |
| Dashboard widgets | `frontend/src/components/dashboard/*.tsx` |
| Proposal tracker | `frontend/src/app/(dashboard)/tracker/page.tsx` |
| Project detail | `frontend/src/app/(dashboard)/projects/[projectCode]/page.tsx` |
| API client | `frontend/src/lib/api.ts` |

### Key Backend Files
| Purpose | File |
|---------|------|
| Dashboard API | `backend/api/routers/dashboard.py` |
| Proposals API | `backend/api/routers/proposals.py` |
| Projects API | `backend/api/routers/projects.py` |
| Query service | `backend/services/query_service.py` |

### Commands
```bash
# Start backend
cd backend && uvicorn api.main:app --reload --port 8000

# Start frontend
cd frontend && npm run dev

# Check database
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM proposals;"

# Test endpoint
curl http://localhost:8000/api/dashboard/stats?role=bill
```

---

## END OF PROMPT

Copy everything from "## BENSLEY PLATFORM - MULTI-AGENT EXECUTION" to here into a new Claude Code window.
