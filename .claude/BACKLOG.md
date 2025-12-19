# Audit Findings & User Feedback Backlog

**Purpose:** Consolidated tracking of all issues from audits and user feedback. Nothing gets lost across sessions.

**Updated:** 2025-12-11 (COMPREHENSIVE AUDIT)

---

## How to Use This File

1. **New findings** → Add to appropriate section with date
2. **Completed items** → Move to "Resolved" section at bottom
3. **Every session** → Check this file for pending work
4. **Prioritize** → P0 = blocking, P1 = important, P2 = nice-to-have

---

## P0 - Critical Issues (Must Fix)

### SECURITY - SQL INJECTION
**[2025-12-11] dashboard.py has f-string SQL injection vulnerabilities**
- **Location:** `backend/api/routers/dashboard.py` lines 385-398, 440-455, 463-468
- **Issue:** `cursor.execute(f"...WHERE payment_date >= '{current_start}'...")`
- **Fix:** Convert to parameterized queries with `?` placeholders
- **Status:** 🔴 CRITICAL - DO FIRST

### SECURITY - NO AUTHENTICATION
**[2025-12-11] Zero auth on 100+ API endpoints**
- **Impact:** Anyone with network access can read/write all data
- **Fix:** Add JWT middleware + API key validation
- **Files:** `backend/api/main.py`, new `backend/api/auth.py`
- **Status:** 🔴 CRITICAL - DO SECOND

### SECURITY - OPENAI DATA LEAKAGE
**[2025-12-11] Proposal data sent to OpenAI without controls**
- **Location:** `POST /api/proposals/{code}/chat`
- **Data sent:** Full email bodies, internal notes, financials
- **Fix:** Create AI gateway with PII scrubbing, cost caps, audit logging
- **Status:** 🟠 HIGH

### GIT - DATABASE BACKUP TRACKED
**[2025-12-11] 32MB db backup in git history**
- **File:** `database/bensley_master.db.backup.20251209_125149`
- **Fix:** `git rm --cached` and add to .gitignore
- **Status:** 🟠 HIGH

---

## P1 - High Priority

### CODE CLEANUP - ORPHANED FLASK ROUTER
**[2025-12-11] Flask contracts.py not connected to FastAPI**
- **Location:** `backend/routes/contracts.py` (188 lines)
- **Issue:** Flask Blueprint with 8 endpoints, NOT registered in main.py
- **Fix:** Delete file (FastAPI has `backend/api/routers/contracts.py`)
- **Status:** 🟠 HIGH

### CODE CLEANUP - DISABLED SCRIPTS NOT ARCHIVED
**[2025-12-11] 3 disabled scripts still in scripts/core/**
- `email_project_linker.py` (994 lines) - Disabled Dec 2
- `email_linker.py` (~600 lines) - Deprecated
- `migrate_links_to_suggestions.py` (~300 lines) - One-time migration done
- **Fix:** Move to `scripts/archive/deprecated_2025-12/`
- **Status:** 🟡 MEDIUM

### FRONTEND - HARDCODED LOCALHOST
**[2025-12-11] Dashboard page bypasses api.ts**
- **Location:** `frontend/src/app/(dashboard)/page.tsx` line 39
- **Issue:** `fetch(\`http://localhost:8000/api/dashboard/stats...\`)`
- **Fix:** Use `api.getDashboardStats()` from api.ts
- **Status:** 🟡 MEDIUM

### DATABASE - REDUNDANT TABLES
**[2025-12-11] proposals (103 rows) vs proposal_tracker (81 rows)**
- **Issue:** Duplicate data, different schemas, backend confusion
- **Fix:** Migrate proposal_tracker data → proposals, then DROP proposal_tracker
- **Status:** 🟡 MEDIUM

### DATABASE - DEAD TABLES (0 rows)
**[2025-12-11] Empty tables that should be removed**
- `learning_events`, `project_context`, `project_files`, `project_phase_history`
- **Fix:** DROP tables (or document as Phase 2 placeholders)
- **Status:** 🟢 LOW

### DATABASE - BACKUP ARTIFACTS
**[2025-12-11] Migration backup tables in production**
- `email_learned_patterns_backup_dec11` (151 rows)
- `learned_patterns_backup_dec11` (341 rows)
- `email_project_links_archive_2024` (918 rows)
- `email_proposal_links_archive_2024` (4,872 rows)
- **Fix:** Export to CSV, then DROP
- **Status:** 🟢 LOW

### DOCUMENTATION - CONFLICTING SSOTs
**[2025-12-11] Multiple conflicting instruction files**
- `.claude/STATUS.md` - "All phases complete"
- `.claude/HANDOFF.md` - Agent instructions
- `.cursorrules` - "Frontend only, don't touch backend"
- **Fix:** Consolidate into single source of truth, delete .cursorrules
- **Status:** 🟡 MEDIUM

### Data Enrichment Needed

**[2025-12-11] Timeline Events Need Source Linking**
- **User Feedback:** "why is the remark for everything in first contact.... and then the proposals like status change should be linked to either a manual entry / change orrrr it should be linked to the actual emails"
- **Problem:** Proposal timeline events are generic, not linked to source emails or manual entries
- **Example:** Status change to "Contract Signed" should link to the email saying "please find attached our signed copy"
- **Solution Needed:**
  1. Add `source_email_id` and `source_type` columns to timeline/milestones tables
  2. AI should detect status-changing language in emails ("signed contract", "approved", "rejected")
  3. Manual override UI to mark emails as "milestone events"
- **Files Affected:** `backend/api/routers/proposals.py` (story endpoint), proposal timeline tables
- **Status:** BACKLOGGED - needs schema design

### Previous Audit Findings

**[2025-12-10] 42 Projects Missing contract_signed_date**
- **Impact:** Contract signed KPIs wrong
- **Status:** FIXED (Dec 11) - Backfilled 37 projects from invoice dates

**[2025-12-10] 9 Tables Referenced but Don't Exist**
- **Tables:** project_context, project_files, project_financials, etc.
- **Status:** FIXED (Dec 11) - Created via migration 082

---

## P2 - Nice to Have / Future Enhancements

### Calendar & Meetings

**[2025-12-11] Meeting Detail Modal**
- Show on calendar click: meeting title, date, time, location, linked proposal/project, attendees, transcript link
- **Status:** BACKLOGGED - Phase 4.3 in plan

### Task Integration

**[2025-12-11] Auto-create Tasks from Action Items**
- When summary saved with action_items, create task in tasks table
- Link task to proposal via proposal_id
- Set source_transcript_id
- **Status:** BACKLOGGED - Phase 5.1 in plan

**[2025-12-11] Task Completion Updates Ball Status**
- When task completed, update ball_in_court status on proposal
- **Status:** BACKLOGGED - Phase 5.2 in plan

### UI Polish

**[2025-12-10] Remove duplicate health score in detail page**
- Hero section has health, Story component also has health
- **Status:** BACKLOGGED

**[2025-12-10] Add quick status buttons on tracker (inline dropdown)**
- **Status:** FIXED (Dec 11) - Added inline status dropdown

### Data Quality

**[2025-12-10] Debug email linking pipeline (81 proposals have 0 emails)**
- **Status:** VERIFIED OK - 86/102 proposals have links (1977 total)
- 16 proposals without links are mostly Declined/Contract Signed (expected)

---

## Resolved (Keep for Reference)

### Dec 11, 2025

- [x] **P0: Missing Tab Components** - Audit was wrong, components exist
- [x] **P0: 9 Missing Database Tables** - Created via migration 082
- [x] **P1: Backfill contract_signed_date** - 37 projects updated
- [x] **P1: Hot Items navigation** - Fixed to `/tracker?filter=needs-followup`
- [x] **P1: Claude Summary Integration** - Full workflow complete
  - Backend: POST /api/meeting-transcripts/{id}/claude-summary
  - Frontend: Paste summary modal with auto-parsing
  - Tasks created automatically from action items
- [x] **P1: Proposal Tasks/Meetings Widgets** - Added to proposal detail page
- [x] **P1: Calendar Month View** - Added with Week/Month toggle
- [x] **P1: Calendar Type Filter** - Added client/internal/site_visit/review filters

### Dec 10, 2025

- [x] **P0: Backend was querying wrong table** - Fixed proposal_tracker_service.py
- [x] **P0: Deliverables endpoint crashing** - Added defensive error handling
- [x] **P1: Ball-in-court indicator** - NEW column in tracker
- [x] **P1: Status colors** - All 11 statuses have distinct colors
- [x] **P1: Chat-driven corrections** - AI parses corrections, creates suggestions

---

## Session Continuation Notes

### Current Phase: Phase 5 (Task Integration) - PENDING

**What's Done:**
- Phase 1-4 complete
- Core meeting/task/calendar infrastructure built

**What's Next:**
1. Auto-create tasks from meeting summary action items
2. Task completion → ball status update
3. Enhanced task page with meeting/proposal links

### Key Files for Reference
```
backend/api/routers/transcripts.py   - Claude summary endpoint
backend/api/routers/tasks.py         - Task CRUD
frontend/src/components/transcripts/paste-summary-modal.tsx
frontend/src/components/proposals/proposal-tasks.tsx
frontend/src/components/proposals/proposal-meetings.tsx
frontend/src/app/(dashboard)/meetings/page.tsx - Calendar with Month view
```

### Database Changes This Session
```sql
-- Migration 082: Missing project tables
project_context, project_files, project_financials

-- Migration 083: Meeting-Task integration
ALTER TABLE tasks ADD COLUMN source_transcript_id
ALTER TABLE tasks ADD COLUMN source_meeting_id
CREATE INDEX idx_tasks_source_transcript
CREATE INDEX idx_meetings_proposal_date
```
