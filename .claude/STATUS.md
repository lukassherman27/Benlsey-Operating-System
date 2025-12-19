# System Status

**Updated:** 2025-12-19 (UX OVERHAUL AUDIT + VISION SESSION)
**Backend:** localhost:8000 | **Frontend:** localhost:3002
**Phase:** UX Overhaul - Cross-linkages, Smart Dashboard, Beautiful Pages

---

## 🎯 CURRENT STATE (Dec 19)

### Live Numbers (Updated)

| Entity | Count | Notes |
|--------|-------|-------|
| Emails | 3,843 | +1 from Dec 16 |
| Proposals | 106 | Same |
| Projects | 60 | Same |
| Contacts | 467 | -80 (cleanup) |
| Invoices | 436 | Same |
| Meetings | 7 | From transcripts |
| Tasks | 41 | 17 us, 17 them, 7 completed |
| AI Suggestions | 1,338 | 693 applied |

### Pipeline Summary (Dec 19)

| Metric | Value |
|--------|-------|
| **Active Pipeline** | $61.79M (44 proposals) |
| **Contract Signed** | $25.20M (16 proposals) |
| **Ball With Us** | 12 proposals (need action) |
| **Ball With Them** | 27 proposals (waiting) |
| **14+ Days Silent** | 13 proposals (urgent) |

### Ball in Court Distribution

| Ball | Count |
|------|-------|
| us | 44 |
| them | 36 |
| on_hold | 25 |
| mutual | 1 |

### 🚨 URGENT ITEMS (Ball With Us, Need Action)

| Code | Name | Status | Days Silent | Value |
|------|------|--------|-------------|-------|
| 25 BK-063 | Akyn Da Lat Vietnam | Proposal Sent | 30 days ⚠️ | $3.4M |
| 25 BK-087-V | Vahine Island Resort | Proposal Sent | 7 days | $2.5M |
| 25 BK-087-Q | Queen's Residence | Proposal Sent | - | $1.25M |
| 24 BK-022 | Dang Thai Mai Hanoi | Proposal Prep | 25 days | $0.69M |
| 25 BK-089 | Rajkot India | First Contact | 17 days | TBD |
| 25 BK-097 | CapitaLand Vietnam | First Contact | 23 days | TBD |

---

## 🔧 UX OVERHAUL STATUS (Dec 18-19)

### New Components Created

| Component | Location | Integrated? |
|-----------|----------|-------------|
| `entity-link.tsx` | `components/cross-link/` | ✅ Ready |
| `daily-briefing.tsx` | `components/dashboard/` | ✅ Dashboard |
| `analytics-insights.tsx` | `components/dashboard/` | ✅ Dashboard |
| `personal-projects-widget.tsx` | `components/dashboard/` | ✅ Dashboard |
| `ball-in-court.tsx` | `components/proposals/` | ⏳ Not yet |
| `health-panel.tsx` | `components/proposals/` | ⏳ Not yet |
| `action-suggestions.tsx` | `components/proposals/` | ⏳ Not yet |
| `project-health-banner.tsx` | `components/project/` | ✅ Projects Detail |
| `rfi-deliverables-panel.tsx` | `components/project/` | ✅ Projects Detail |

### Data Gaps Identified

| Field | Coverage | Action Needed |
|-------|----------|---------------|
| `health_score` | 0/106 | Need calculation logic |
| `win_probability` | 0/106 | Need calculation logic |
| `ball_in_court` | 106/106 ✅ | Working |
| `waiting_for` | 40/106 | Partial |
| `days_since_contact` | 84/106 | Good |

### Top Proposals by Email Activity

| Code | Name | Emails | Status |
|------|------|--------|--------|
| 25 BK-042 | Sabrah 5-Star Hotel | 207 | Contract Signed |
| 25 BK-037 | La Vie Hyderabad | 121 | Negotiation |
| 25 BK-017 | TARC New Delhi | 99 | Contract Signed |
| 25 BK-087 | Pearl Resorts (all) | 268 | Mixed |
| 25 BK-033 | Ritz Carlton Nusa Dua | 65 | Contract Signed |

---

## 🎨 UI VISION (From User Dec 18)

### Bill's Daily Needs
1. **Meetings today** - What's scheduled
2. **Proposals needing nudge** - Context-aware (not just days)
3. **Things to send out** - Deliverables, proposals
4. **Tasks for today/this week**

### Follow-up Logic (CRITICAL)
- NOT just "days since contact"
- **Context-aware**: "give us time to check with CEO" → wait longer
- **Commitment tracking**: "We said we'd send by Friday" → remind us
- **Ball in court**: Based on who said they'd do something next

### Project Phases (Post-Contract)
1. Mobilization → 2. Concept Design → 3. Schematic Design → 4. Design Development → 5. Construction Drawings → 6. Construction Observation

### Business Rules
- Minimum fee: $1M (exceptions for extensions)
- Project duration: ~2 years contract, often delayed
- Deliverables: drawings, renderings, perspectives

---

## 📋 PREVIOUS STATE (Dec 16)

### Task System Now Working ✅
Meeting summary emails → Tasks with ball tracking

**41 Total Tasks:**
- 17 pending (us) - Lukas, Bill, Brian, Team
- 17 pending (them) - waiting on clients
- 7 completed

**Tasks by Project:**
| Project | Us | Them | Status |
|---------|-----|------|--------|
| 25 BK-087 Pearl Resorts | 7 | 11 | Ball split |
| 25 BK-096 Jianhua Dalian | 5 | 1 | Ball mostly us |
| 25 BK-104 Siargao | 2 | 3 | Ball with them |
| 25 BK-068 Grenada | 2 | 2 | Ball split |

### Email Coverage: 90%
- Total: 3,843 emails
- Handled: 3,462 (linked or categorized)
- Unhandled: 381 (mostly old)

### CLI Workflow Commands Created
- `/daily` - Full daily workflow instructions
- `/process-emails` - Process new emails with ball tracking
- `/ball-status` - Show ball tracking for all proposals

### New Services Built
- `meeting_summary_parser.py` - Extracts tasks from Claude meeting summaries
- `ActionRequiredHandler` - Handles action_required suggestions
- **Meeting parser now wired into email_orchestrator.py** - Auto-processes meeting summaries during email sync

### Previous Work (Dec 16)
- Simplified UI to 8 nav items (removed 7 admin pages)
- Enabled GPT pipeline (`use_context_aware=True`)
- Wired 4 orphaned services

### Files Changed This Session
| File | Change |
|------|--------|
| `frontend/src/components/layout/app-shell.tsx` | Simplified nav to 7+Admin |
| `backend/services/meeting_summary_parser.py` | NEW - Parse meeting summaries → tasks |
| `backend/services/suggestion_handlers/action_item_handler.py` | Added ActionRequiredHandler |
| `backend/services/email_orchestrator.py` | Wired meeting_summary_parser into pipeline |
| `.claude/commands/daily.md` | NEW - Daily workflow instructions |
| `.claude/commands/process-emails.md` | NEW - Email processing workflow |
| `.claude/commands/ball-status.md` | NEW - Ball tracking command |

### What's NOT Working (Known)
- AI suggestions pipeline was DORMANT (0 pending) - now enabled
- RAG/Embeddings: 0 created (run `create_embeddings.py` to set up)
- Timeline aggregation: emails linked but no summaries generated
- Health scores: all NULL (need calculation logic)

---

## 📋 ROADMAP (Updated Dec 16)

### NOW → Mid-January
| Task | Status | Notes |
|------|--------|-------|
| Simplify UI | ✅ DONE | 8 nav items |
| Enable GPT pipeline | ✅ DONE | `use_context_aware=True` |
| Wire orphaned services | ✅ DONE | 4 services connected |
| Test GPT suggestions | NEXT | Run `scheduled_email_sync.py` |
| Create embeddings | PENDING | Run `create_embeddings.py` |
| RAG integration | PENDING | Wire embeddings to GPT prompts |

### January Targets
- Working suggestion loop (GPT → suggestions → approve → database fills)
- RAG providing context for AI analysis
- Daily workflow: Open app → approve suggestions → data populates

### Q1 2026 Vision
- Local Bensley AI (Ollama)
- Full context awareness
- "Create proposal for X" type commands

---

## 🟢 SYSTEM OVERHAUL COMPLETE (Dec 12)

### Phase Status (6-Phase Plan) - ALL DONE

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Database Schema Enhancement | ✅ COMPLETE |
| **Phase 2** | AI Suggestion Enhancement (Task/Meeting Detection) | ✅ COMPLETE |
| **Phase 3** | Daily Workflow / My Day Page | ✅ COMPLETE |
| **Phase 4** | Task/Deliverable UI Enhancement | ✅ COMPLETE |
| **Phase 5** | Attachment Organization + Vector Store Prep | ✅ COMPLETE |
| **Phase 6** | Admin Suggestions UI Enhancement | ✅ COMPLETE |

### Phase 4: Task/Deliverable UI ✅ COMPLETE (This Session)

**Tasks Page Enhanced** (`frontend/src/app/(dashboard)/tasks/page.tsx`):
- Category filter tabs (Proposal, Project, Finance, Legal, Operations, Marketing, Personal, HR, Admin, Other)
- Category badge display on each task
- Hierarchy toggle (show parent-child relationships)
- Color-coded category badges

**Deliverables Page Enhanced** (`frontend/src/app/(dashboard)/deliverables/page.tsx`):
- "Add Deliverable" button in header
- Create deliverable modal (name, project_code, type, due_date, description)
- Form validation and error handling

### Phase 5: Attachment & Vector Store ✅ COMPLETE (This Session)

**Attachment Organization Script** (`scripts/core/organize_attachments.py`):
- Shows stats: 838 organizable attachments with proposal links
- Creates folder structure: `/files/attachments/{year}/{project_code}/{document_type}/`
- Supports dry-run mode
- Updates organized_path, project_code, organized_at in database
- Document type mapping from DB field or file extension

**Embedding Scripts** - Verified existing infrastructure:
- `create_embeddings.py` uses ChromaDB (working)
- 4 SQLite embedding tables exist (email, document, proposal, contact)
- Tables are empty but schema is ready

### Phase 6: Admin Suggestions UI ✅ COMPLETE (This Session)

**Added 3 new suggestion type tabs** (`frontend/src/app/(dashboard)/admin/suggestions/page.tsx`):
- Follow-ups (follow_up_needed) - with Zap icon
- Actions (action_required) - with CheckSquare icon
- Status Updates (proposal_status_update) - with FileText icon

### TypeScript Fixes (This Session)

Fixed 3 pre-existing errors:
- Added `client_company` and `next_steps` to `ProposalDetail` type
- Fixed null safety in timeline filter expression (proposals/[projectCode]/page.tsx)
- All TypeScript errors resolved - **codebase compiles cleanly**

### Phase 1: Database Schema Enhancement ✅ COMPLETE
**Migration:** `086_comprehensive_schema_enhancement.sql` (applied)

- ✅ **Tasks:** Added `parent_task_id`, `category`, `assigned_staff_id`, `deliverable_id`
- ✅ **Deliverables:** NEW table created (was missing!) - full lifecycle tracking
- ✅ **Commitments:** NEW table - tracks promises (our_commitment / their_commitment)
- ✅ **Calendar Blocks:** NEW table - focus time, travel, vacation, site visits
- ✅ **Embeddings:** 4 tables prepared (email, document, proposal, contact)
- ✅ **Views:** v_task_hierarchy, v_deliverable_progress, v_staff_workload, v_commitment_summary

### Phase 2: AI Suggestion Enhancement ✅ COMPLETE

**GPT Prompt Enhanced** (`backend/services/gpt_suggestion_analyzer.py`):
- ✅ Action item detection from emails
- ✅ Meeting detection (request, confirmation, reschedule)
- ✅ Deadline/deliverable detection
- ✅ Commitment tracking (who promised what)

**Suggestion Writer Updated** (`backend/services/suggestion_writer.py`):
- ✅ `_write_action_item_suggestion()` - Creates task suggestions
- ✅ `_write_meeting_suggestion()` - Creates meeting suggestions
- ✅ `_write_deliverable_suggestion()` - Creates deliverable suggestions
- ✅ `_write_commitment_suggestion()` - Creates commitment suggestions

**New Handlers Created** (`backend/services/suggestion_handlers/`):
- ✅ `action_item_handler.py` - Handles action_item suggestions → tasks
- ✅ `meeting_handler.py` - Handles meeting_detected suggestions → meetings
- ✅ `commitment_handler.py` - Handles commitment suggestions → commitments
- ✅ `deadline_handler.py` - Updated to create deliverables (was tasks)

### Phase 3: Daily Workflow / My Day Page ✅ COMPLETE

**Backend:** ✅ `GET /api/my-day` endpoint created (`backend/api/routers/my_day.py`)
- Returns: greeting, tasks (today + overdue), meetings, proposals needing follow-up
- Returns: AI suggestions queue, week ahead preview, commitments

**Frontend:** ✅ Created `frontend/src/app/(dashboard)/my-day/page.tsx`
- Personal daily dashboard with greeting (time-based)
- Quick stats row: Overdue, Today, Meetings, Follow-ups
- Three-column layout: Tasks | Meetings+Proposals | Suggestions+WeekAhead
- One-click task complete/snooze
- One-click meeting join (for video meetings)
- Commitments widget (if any overdue)
- Added "My Day" to navigation (top of sidebar)

---

## 🔍 COMPREHENSIVE SYSTEM AUDIT (Dec 12, 2025)

### Frontend Pages Inventory (35 Total)

**In Navigation (14 items):**
| Route | Name | Status |
|-------|------|--------|
| `/my-day` | My Day | ✅ Working |
| `/` | Dashboard | ✅ Working |
| `/tracker` | Proposals | ✅ Working |
| `/projects` | Projects | ✅ Working |
| `/deliverables` | Deliverables | ✅ Working (15 records) |
| `/tasks` | Tasks | ✅ Working (15 tasks) |
| `/meetings` | Meetings | ✅ Working (7 meetings) |
| `/transcripts` | Transcripts | ✅ Added to nav |
| `/rfis` | RFIs | ⚠️ Needs testing |
| `/contacts` | Contacts | ✅ Working (547 contacts) |
| `/finance` | Finance | ✅ Working |
| `/query` | Query | ✅ Working |
| `/admin/suggestions` | Review | ✅ Working |
| `/admin` | Admin | ✅ Working |

**Orphan Pages (Not in Navigation):**
| Route | Lines | Assessment | Action |
|-------|-------|------------|--------|
| `/suggestions` | ~~1056~~ | ~~DUPLICATE~~ | ✅ DELETED |
| `/analytics` | 537 | Full analytics dashboard, no nav link | ADD TO NAV or DELETE |
| `/emails` | - | Email list | ADD TO NAV (Email submenu) |
| `/emails/links` | - | Email linking | ADD TO ADMIN |
| `/emails/intelligence` | - | Email intelligence | ADD TO ADMIN |
| `/emails/review` | 441 | Email review | ADD TO ADMIN |
| `/admin/audit` | 596 | System audit | ✅ Added to admin nav |
| `/admin/validation` | 465 | Data validation | ✅ Added to admin nav |
| `/admin/intelligence` | 483 | Intelligence admin | ✅ Added to admin nav |
| `/transcripts` | - | Meeting transcripts | ✅ Added to nav |
| `/search` | - | Global search | KEEP (utility) |
| `/proposals` | - | Redirect | ⏩ REDIRECT → /tracker |
| `/proposals/[projectCode]` | - | Detail page | KEEP (accessed via links) |
| `/projects/[projectCode]` | - | Detail page | KEEP (accessed via links) |

### Database Data Gaps

**Tables with Schema but NO Data (5 tables remaining):**
| Table | Records | Priority |
|-------|---------|----------|
| `deliverables` | **15** | ✅ POPULATED from contract_phases |
| `email_embeddings` | 0 | MEDIUM - Vector search prep |
| `document_embeddings` | 0 | MEDIUM - Vector search prep |
| `proposal_embeddings` | 0 | MEDIUM - Vector search prep |
| `contact_embeddings` | 0 | LOW - Future feature |
| `commitments` | 0 | MEDIUM - Tracking promises |
| `calendar_blocks` | 0 | LOW - Scheduling feature |

**Proposal Field Population:**
| Field | Populated | Total | % |
|-------|-----------|-------|---|
| `client_company` | 88 | 105 | 84% |
| `ball_in_court` | **105** | 105 | **100%** ✅ |
| `next_action_date` | 7 | 105 | 7% |
| `win_probability` | 0 | 105 | 0% |

**Other Tables:**
| Table | Records | Notes |
|-------|---------|-------|
| `proposals` | 105 | Main data |
| `projects` | 60 | Active + completed |
| `emails` | 3,809 | Growing |
| `contacts` | 547 | Needs dedup |
| `tasks` | 15 | From transcripts & emails |
| `meetings` | **7** | ✅ Created from transcripts |
| `ai_suggestions` | 1,338 | 693 applied, 619 rejected |

### AI Suggestions Status

| Status | Count |
|--------|-------|
| applied | 693 |
| rejected | 619 |
| accepted | 11 |
| approved | 7 |
| rolled_back | 7 |
| modified | 1 |

**By Type (Top 10):**
| Type | Count |
|------|-------|
| email_link | 642 |
| follow_up_needed | 195 |
| proposal_status_update | 178 |
| new_contact | 129 |
| action_required | 60 |
| email_review | 51 |
| contact_link | 38 |
| missing_data | 16 |

---

## 🔧 CLEANUP RECOMMENDATIONS

### Priority 1: Delete Duplicate/Unused Pages
- [x] Delete `/suggestions/page.tsx` (duplicate of /admin/suggestions) ✅ DONE
- [ ] Decide: Keep or delete `/analytics/page.tsx`

### Priority 2: Consolidate Admin Pages
- [x] Add `/admin/audit` to admin nav ✅ DONE
- [x] Add `/admin/validation` to admin nav ✅ DONE
- [x] Add `/admin/intelligence` to admin nav ✅ DONE
- [ ] Consolidate `/emails/*` pages into admin submenu

### Priority 3: Populate Empty Tables
- [x] Create deliverables from contract phases (15 created) ✅ DONE
- [x] Create meetings from transcripts (3 new, 7 total) ✅ DONE
- [x] Set ball_in_court on all proposals (105/105 = 100%) ✅ DONE
- [ ] Add next_action_date to more proposals (currently 7/105)

### Priority 4: Add Transcripts to Nav
- [x] Add `/transcripts` to main navigation ✅ DONE
- [x] Remove `/contracts` from nav (was just a redirect) ✅ DONE

---

## 🚀 NEXT PHASE PLAN (Integrating Cleanup + Roadmap)

### Phase A: Quick Wins ✅ COMPLETE
**Goal:** Clean up obvious issues before moving forward

| Task | Status | Action |
|------|--------|--------|
| Delete `/suggestions/page.tsx` | ✅ DONE | Removed duplicate file |
| Add hidden admin pages to nav | ✅ DONE | Updated app-shell.tsx |
| Add `/transcripts` to nav | ✅ DONE | Updated app-shell.tsx |
| Remove `/contracts` from nav | ✅ DONE | Was just a redirect |

### Phase B: Data Population ✅ COMPLETE
**Goal:** Fill empty tables so features actually work

| Table | Status | Result |
|-------|--------|--------|
| `deliverables` | ✅ DONE | 15 created from contract_phases |
| `meetings` | ✅ DONE | 3 new, 7 total (from transcripts) |
| `ball_in_court` | ✅ DONE | 105/105 = 100% populated |

### Phase C: January Roadmap Items
**From roadmap.md Week 1-4:**

| Week | Task | Status |
|------|------|--------|
| W1 | Verify dashboard displays real data | ✅ Already working |
| W2 | Connect projects@bensley.com | Need credentials |
| W3 | Meeting Recorder MVP | Web form + transcription |
| W4 | Bill's First Query (Slack/Web) | Read-only access |

### Phase D: Intelligence Layer (Building Toward Brain)
**Roadmap Layer 3:**

| Feature | What It Does | Dependencies |
|---------|--------------|--------------|
| Task extraction from emails | GPT analyzes emails → creates task suggestions | ✅ Handler exists |
| Deliverable tracking | Track progress toward milestones | Phase B (data population) |
| Project health scores | Auto-calculate from signals | Already in proposal-story |
| Action items | Surface "respond to X" items | Already in hot-items-widget |

---

## 📋 IMMEDIATE ACTION PLAN

**This Session (Dec 12) - ALL COMPLETE:**
1. ✅ Audit complete
2. ✅ Clean up nav (add hidden pages, remove duplicate)
3. ✅ Create deliverables from contract_phases (15 created)
4. ✅ Link transcripts to meetings (3 new, 7 total)
5. ✅ Set ball_in_court on all proposals (100%)

**Next Steps:**
1. Get projects@bensley.com credentials from IT
2. Plan Meeting Recorder MVP
3. Design Bill's Query interface
4. Add next_action_date to more proposals

---

### Files Created This Session
| File | Purpose |
|------|---------|
| `database/migrations/086_comprehensive_schema_enhancement.sql` | Full schema enhancement |
| `backend/services/suggestion_handlers/action_item_handler.py` | Action item → task |
| `backend/services/suggestion_handlers/meeting_handler.py` | Meeting detection → meeting |
| `backend/services/suggestion_handlers/commitment_handler.py` | Commitment tracking |
| `backend/api/routers/my_day.py` | My Day dashboard endpoint |
| `frontend/src/app/(dashboard)/my-day/page.tsx` | My Day frontend page |

### Files Modified This Session
| File | Changes |
|------|---------|
| `backend/services/gpt_suggestion_analyzer.py` | Added task/meeting/deliverable/commitment detection prompts |
| `backend/services/suggestion_writer.py` | Added 4 new suggestion writing methods |
| `backend/services/suggestion_handlers/deadline_handler.py` | Updated to create deliverables |
| `backend/services/suggestion_handlers/__init__.py` | Registered new handlers |
| `backend/api/main.py` | Added my_day router |
| `frontend/src/lib/types.ts` | Added My Day types |
| `frontend/src/lib/api.ts` | Added getMyDay API call |
| `frontend/src/components/layout/app-shell.tsx` | Added My Day to navigation |

---

## 📋 PREVIOUS SESSION: SECURITY HARDENING (Dec 11)

### System Health Scores (Updated Dec 11)

| Area | Before | After | Notes |
|------|--------|-------|-------|
| Security | **D** | **C+** | SQL injection FIXED, still needs auth |
| Backend | **B-** | **B+** | Orphaned code removed, clean FastAPI |
| Frontend | **A-** | **A** | All API calls via api.ts now |
| Database | **C+** | **B** | 9 dead tables dropped (108→99) |
| Code Quality | **B** | **B+** | Deprecated scripts archived |
| AI Readiness | **D+** | **D+** | Still needs AI gateway |

### Target: A- Security (auth), B+ AI Readiness (gateway)

---

## 🚧 AFTER CLEANUP: UNIFIED TASK SYSTEM (User Requirements Dec 11)

### User Vision for Tasks
**Current Problem:** Tasks exist but aren't functional - can't assign, edit, or do anything with them.

**Requirements Gathered:**
1. **Assignees from staff table** - Pull from existing staff table (Bill, Lukas, Brian, etc.)
2. **Full task management** - Complete, reassign, edit details (title, description, due date, priority)
3. **Parent-child hierarchy** - Tasks under deliverables (e.g., "Schematic Design" → 20 subtasks)
4. **Categories** - Fixed + custom: Proposal, Project, Finance, Legal, Operations, Marketing, Personal
5. **Switchable groupings** - View by assignee, category, or due date
6. **Multi-functional** - Not just proposals: invoices, legal, Shinta Mani, Bill's land sale, social media

### User Vision for Task Suggestions (AI-Powered)
**DON'T auto-create tasks.** Instead:
1. **Scan meeting summaries** → Suggest action items
2. **Scan incoming emails** → Suggest "respond to [client]" tasks
3. **Extract deadlines** from emails or default 10 days
4. **Show in daily review** alongside email links and status updates
5. **User approves/rejects** each suggestion

**Integrate with existing `ai_suggestions` system** - New type `task_suggestion`:
- Source: email_id or transcript_id
- Proposed: title, assignee, due_date, priority
- Linked: proposal_id
- Confidence score for auto-approval threshold

### Meetings Page Fix (DONE)
- Fixed `/api/meetings` to return ALL meetings (not just upcoming)
- Dec 11 Pearl Resorts meeting now shows in calendar
- Supports date range filtering

### Files to Modify for Task System
| File | Changes Needed |
|------|----------------|
| `backend/services/suggestion_handlers/task_handler.py` | EXISTS - Wire up to create tasks on approval |
| `backend/services/suggestion_writer.py` | Add task suggestion creation from emails |
| `backend/api/routers/tasks.py` | Add PATCH for edit, assignee dropdown |
| `frontend/src/app/(dashboard)/tasks/page.tsx` | Full task management UI |
| `database/migrations/084_task_enhancements.sql` | Add parent_task_id, category columns |

---

## 🎯 VAHINE ISLAND CASE STUDY (Dec 11 - Data Population)

### What We Did
Used 25 BK-087 (Vahine Island) as a case study to populate real data:

1. **Imported 21 new emails** including Dec 11 meeting summary
2. **Created 8 action items as tasks** from Dec 11 contract negotiation meeting:
   - Critical: Revise contracts (Lukas, due Dec 12)
   - Medium: Research Marquesas/Queen's Hotel history (Bill, due Dec 31)
   - Low: Plan site visit (Team, post-signing)
   - Client tasks (4): Review contracts, provide documents, finalize program, arrange architect
3. **Created new proposal** 25 BK-108 (Marquesas Islands 5-Star Luxury Resort)
4. **Synced 2 meetings** to meetings table (Nov 17 office visit, Dec 11 contract discussion)
5. **Updated ball_in_court** to "us" (critical task due tomorrow)

### Vahine Island Data Now
| Data Type | Count |
|-----------|-------|
| Emails | 62 (58 + 4 Dec 11) |
| Tasks | 8 (4 ours, 4 theirs) |
| Meetings | 2 (Nov 17, Dec 11) |
| Status | Proposal Sent |
| Ball | Us (contract revision due Dec 12) |

### Key Learning
- Meeting summaries are in email body_full field
- Tasks need manual extraction or Claude summary paste workflow
- proposal_events and meetings tables need to stay in sync
- assignee values can be: us, them, Lukas, Bill, Team, etc.

---

## 🎯 MEETING/CALENDAR/TASKS INTEGRATION (Dec 11)

### Plan File
Full plan at: `/Users/lukassherman/.claude/plans/clever-knitting-tarjan.md`
All issues tracked in: `.claude/BACKLOG.md`

### Phase Status Summary

| Phase | Status | Key Deliverables |
|-------|--------|------------------|
| Phase 1: P0 Stability | ✅ COMPLETE | Tabs verified, 3 tables created, 37 dates backfilled |
| Phase 2: Claude Summary | ✅ COMPLETE | Endpoint + modal + tasks auto-creation |
| Phase 3: Proposal Widgets | ✅ COMPLETE | Tasks widget + meetings widget |
| Phase 4: Unified Calendar | ✅ COMPLETE | Month view + Week/Month toggle + type filters |
| Phase 5: Task Integration | ✅ COMPLETE | Ball status updates on task completion + enhanced tasks page |

### Phase 1: P0 Stability ✅ COMPLETE

- ✅ **Missing tab components** - AUDIT WAS WRONG, both OverviewTab & ActiveProjectsTab exist
- ✅ **3 Missing tables created** via migration 082:
  - `project_context`, `project_files`, `project_financials`
- ✅ **contract_signed_date backfilled** - 37 projects updated from invoice dates (44/60 now have dates)
- ✅ **Hot Items link verified** - Already points to `/tracker?filter=needs-followup`

### Phase 2: Claude Summary Integration ✅ COMPLETE

**Backend:** `POST /api/meeting-transcripts/{id}/claude-summary`
- File: `backend/api/routers/transcripts.py:364-502`
- Accepts: `{summary, key_points[], action_items[], next_meeting_date?, proposal_code?}`
- Creates tasks automatically from action_items with `source_transcript_id` link
- Creates follow-up meeting if `next_meeting_date` provided

**Frontend:** `frontend/src/components/transcripts/paste-summary-modal.tsx`
- Auto-parses Claude summaries (sections: Summary, Key Points, Action Items, Next Meeting)
- Priority detection (urgent/high/normal/low keywords)
- Assignee extraction from `(name)` or `[@name]` patterns
- Proposal selector dropdown
- Edit action items before saving

**Integration:** `/transcripts` page has "Save Claude Summary" button

**Database:** Migration 083 applied
```sql
ALTER TABLE tasks ADD COLUMN source_transcript_id
ALTER TABLE tasks ADD COLUMN source_meeting_id
CREATE INDEX idx_tasks_source_transcript
CREATE INDEX idx_meetings_proposal_date
```

### Phase 3: Proposal Page Enhancements ✅ COMPLETE

**Tasks Widget:** `frontend/src/components/proposals/proposal-tasks.tsx`
- Fetches from `api.getProjectTasks(projectCode)`
- Sorts: overdue first → priority → due_date
- Checkbox to complete tasks inline
- "From Meeting" badge for transcript-linked tasks

**Meetings Widget:** `frontend/src/components/proposals/proposal-meetings.tsx`
- Separates upcoming/past meetings
- Collapsible past meetings section
- "Join" button for video meeting links

**Integration:** `/proposals/[projectCode]/page.tsx`
- 2-column grid with widgets above ProposalStory on Story tab

### Phase 4: Unified Calendar ✅ COMPLETE

**File:** `frontend/src/app/(dashboard)/meetings/page.tsx`

Features:
- **Month Calendar View** - Full month grid, 2 meetings per day with "+N" overflow
- **Week/Month Toggle** - Button group switches views
- **Type Filter** - Badge-based filter: all, client, internal, site_visit, review
- Both views use `filteredMeetings` for consistency

### Phase 5: Task Integration ✅ COMPLETE

**Phase 5.1: Ball Status Update on Task Completion**
- File: `backend/api/routers/tasks.py`
- Added `assignee` column to tasks table (default: 'us')
- `complete_task` endpoint now updates proposal's ball_in_court:
  - If all "our" tasks completed → ball_in_court = 'them'
  - Sets waiting_for = 'Completed all action items - awaiting client response'
- `update_task` endpoint has same logic when status changes to completed
- Tested: Task completion on 25 BK-070 updated ball from empty to "them"

**Phase 5.2: Enhanced Tasks Page**
- File: `frontend/src/app/(dashboard)/tasks/page.tsx`
- Added "From Meetings" tab (shows tasks with source_transcript_id or source_meeting_id)
- Added fromMeetings stat counter
- Tasks linked to proposals now link to `/proposals/` (not `/projects/`)
- "From Meeting" badge shows with link to `/transcripts` for meeting-sourced tasks
- Task interface updated with: source_transcript_id, source_meeting_id, assignee

### Files Modified This Session

**New Files:**
| File | Purpose |
|------|---------|
| `database/migrations/082_add_missing_project_tables.sql` | Create 3 missing tables |
| `database/migrations/083_meeting_task_integration.sql` | Task-meeting schema |
| `frontend/src/components/transcripts/paste-summary-modal.tsx` | Claude summary paste UI |
| `frontend/src/components/proposals/proposal-tasks.tsx` | Tasks widget |
| `frontend/src/components/proposals/proposal-meetings.tsx` | Meetings widget |
| `.claude/BACKLOG.md` | Persistent audit/feedback tracking |

**Modified Files:**
| File | Changes |
|------|---------|
| `backend/api/routers/transcripts.py` | Claude summary endpoint |
| `backend/api/routers/tasks.py` | Ball status update on task completion |
| `frontend/src/lib/api.ts` | 3 new API methods |
| `frontend/src/app/(dashboard)/transcripts/page.tsx` | Save Claude Summary button |
| `frontend/src/app/(dashboard)/proposals/[projectCode]/page.tsx` | Widgets integration |
| `frontend/src/app/(dashboard)/meetings/page.tsx` | Month view + filters |
| `frontend/src/app/(dashboard)/tasks/page.tsx` | From Meetings tab + proposal links |
| `frontend/src/components/transcripts/paste-summary-modal.tsx` | Fixed API call (getProposals) |

---

## 🔧 PROPOSAL STORY PAGE REWRITE (Dec 10 Late Night)

### What Was Done
1. **Story endpoint completely rewritten** (`/api/proposals/{code}/story`)
   - Now returns: `internal_notes` (fee breakdown, scope, proposal history), `correspondence_summary`, ALL emails, milestones, action items
   - Timeline only shows **milestones that moved proposal forward** (was showing all 53 emails, now ~6 key events)
   - Milestone detection: first_contact, proposal_sent, meeting_scheduled, contract_discussion, client_response

2. **Frontend Story component rebuilt** (`proposal-story.tsx`)
   - Health bar with signals (Recent contact, Meeting scheduled, Active progression)
   - Summary blurb at top (from `correspondence_summary`)
   - Proposal Details card with fee breakdown/scope (from `internal_notes`)
   - Clean milestone timeline (not every email)
   - Email threads grouped with expand/collapse

3. **Email linking fixed** for Vahine Island
   - Dec 9 emails (2028077, 2028080) were in DB but NOT linked to proposal
   - Manually linked them, updated `last_contact_date`

### Files Modified
- `backend/api/routers/proposals.py` - Rewrote `/story` endpoint (~200 lines)
- `frontend/src/components/proposals/proposal-story.tsx` - Complete rewrite

### Issues Found (Next Session)
1. **Email linking not automatic** - New emails imported but not linked to proposals
2. **Proposal page has duplicate health scores** - Hero has one, Story has another
3. **Financials tab wrong for proposals** - Shows invoice data, should show fee breakdown
4. **Too many tabs** - Should simplify to 4: Story | Details | Emails | Documents
5. **Dec 11 meeting not showing** - `proposal_events` table has Nov 17 meeting but not Dec 11 Zoom

### Vahine Island (25 BK-087) Data
```
Emails: 55 (was 53, linked 2 more)
Milestones: 6 key events
Status: Negotiation, Ball: them
Waiting for: Dec 11 call with Bill
Proposal History: V1 $3.45M (Jul 28), V2 $3.75M (Nov 21)
```

---

## ✅ PROPOSAL TRACKER FULLY FIXED (Dec 10 Evening)

### What Was Fixed
| Issue | Root Cause | Fix |
|-------|-----------|-----|
| **Hoxton shows 0 emails** | Backend queried `email_project_links` (519) instead of `email_proposal_links` (1,941) | Changed to correct table |
| **Most proposals 0 emails** | Wrong table - only signed projects had links | Now uses `email_proposal_links` for all proposals |
| **Timeline dates broken** | Frontend expected `status_date`, backend returned `changed_date` | Kept original field name |
| **Documents tab empty** | No endpoint existed | Created `/api/proposals/{code}/documents` |
| **Briefing empty** | Returned `{}` hardcoded | Created `/api/proposals/{code}/briefing` |
| **TARC limited to 50 emails** | LIMIT clause | Removed limit |
| **React key warning** | Used `event.history_id` but API returns `id` | Fixed to use `event.id` |

### Files Modified
- `backend/services/proposal_tracker_service.py` - Fixed email query (line 497) + history field (line 455)
- `backend/api/routers/proposals.py` - Added documents + briefing endpoints
- `frontend/src/lib/api.ts` - Updated to call new endpoints
- `frontend/src/components/proposals/proposal-timeline.tsx` - Fixed React key warning

### Verified Results
| Project | Before | After |
|---------|--------|-------|
| **25 BK-003** (George Hotel) | 0 emails | **6 emails** |
| **25 BK-086** (Hoxton) | 0 emails | **26 emails** |
| **25 BK-017** (TARC) | 50 emails | **98 emails** |

### All Proposal Tracker Endpoints Now Working ✅
- `GET /api/proposal-tracker/stats` - 102 total proposals
- `GET /api/proposal-tracker/list` - All proposals with email counts
- `GET /api/proposal-tracker/{code}` - Full proposal details
- `GET /api/proposal-tracker/{code}/history` - Status change timeline
- `GET /api/proposal-tracker/{code}/emails` - **NOW WORKING** (was broken)
- `GET /api/proposals/{code}/timeline` - Combined timeline
- `GET /api/proposals/{code}/documents` - **NEW ENDPOINT**
- `GET /api/proposals/{code}/briefing` - **NEW ENDPOINT**
- `GET /api/proposals/{code}/stakeholders` - Contacts for proposal

---

## 🚨 CRITICAL FIX: Backend Now Queries `proposals` Table (Dec 10 Late)

### Problem
- Backend was querying stale `proposal_tracker` table (only 44 records, wrong values)
- Nathawan showed $37M THB instead of $1.2M USD
- TARC (25 BK-017) not appearing in Contract Signed list
- Click filtering broken (Lost only showed 10, not 25)
- History endpoint broken ("no such column: id")

### Fixes Applied ✅
1. **`get_stats()`** - Now queries `proposals` table for all stats
2. **`get_proposals_list()`** - Now queries `proposals` + LEFT JOIN `proposal_tracker` + email stats
3. **`get_proposal_by_code()`** - Now queries `proposals` table (was 404 for most proposals)
4. **`get_status_history()`** - Fixed column names (`history_id` not `id`, `status_date` not `changed_date`)
5. **Active count** - Now excludes Contract Signed (was counting won as active)
6. **Lost filter** - Now includes both Lost + Declined (IN clause)

### File Changed
`backend/services/proposal_tracker_service.py` - 4 functions rewritten

---

## Live Pipeline Numbers (from API - Dec 10 CORRECTED)

| Metric | Count | Notes |
|--------|-------|-------|
| **Total Proposals** | 102 | All time |
| **Won (Contract Signed)** | 16 | Including TARC |
| **Lost / Declined** | 25 | Lost (10) + Declined (15) |
| **Still Active** | 39 | Excludes Won + Lost + Dormant |
| **Dormant** | 22 | Stalled, not counted in Active |

**Pipeline Stages:**
- First Contact: 11
- Proposal Prep: 3
- Proposal Sent: 18
- Negotiation: 3
- On Hold: 4

**Validation:** 16 + 25 + 39 + 22 = 102 ✓

---

## Frontend Updates (Dec 10 Late)

1. **Pipeline stages corrected** - Now shows actual stages from database:
   - First Contact → Proposal Prep → Proposal Sent → Negotiation → On Hold
   - (Was showing "Drafting" which doesn't exist)

2. **Last Contact column** - Replaced "Country" (mostly empty) with email stats:
   - Shows last email date + email count per proposal

3. **Types updated** - Added `email_count` and `first_email_date` to `ProposalTrackerItem`

---

## Still Broken (Next Session)

| Issue | Status |
|-------|--------|
| **Most proposals have 0 emails** | Only 7 of 96 2025 proposals have email links |
| **Proposal detail page empty** | Timeline/history now loads, but remarks/summary empty |
| **Contacts table garbage** | 546 contacts but data is malformed/encoded |
| **No document tracking** | Documents not linked to proposals |
| **Meeting dates not extracted** | Need to parse from emails |

---

---

## CRITICAL FIX: Proposals Page Analytics (Dec 10, 2025 Late PM)

### Problem
Analytics cards (6 KPI cards at top of /tracker page) were NOT rendering because:
- Backend returned stats at ROOT level: `{total_proposals: 44, ...}`
- Frontend expected stats NESTED: `{success: true, stats: {...}}`
- So `statsData.stats` was `undefined` and cards didn't render

### Fix Applied ✅
**File:** `backend/api/routers/proposals.py` line 388
```python
# Before:
return stats

# After:
return {"success": True, "stats": stats}
```

### What User Should Now See at /tracker
1. **6 analytics cards** at top (Pipeline Value, Close to Signing, Needs Follow-up, etc.)
2. **Pipeline bar** showing status breakdown
3. **Table** with proposals

**Refresh browser to see changes** (backend auto-reloaded)

---

## Hot Items Widget Fix (Dec 10, 2025 Evening)

### Problems Fixed ✅
1. **Shows active PROJECTS instead of PROPOSALS** - Widget now queries `proposals` table for pipeline items needing follow-up
2. **Missing project names** - Now displays "25 BK-033 (Ritz-Carlton Nusa Dua)" format everywhere
3. **"999 days no contact"** - NULL dates now handled gracefully ("No contact recorded")
4. **Wrong navigation** - Clicks now go directly to `/proposals/{code}` detail page
5. **Shows only 6 items** - Increased to 10 visible items

### Changes Applied
**Backend:** `/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/backend/api/routers/dashboard.py`
- Changed query from `projects` table to `proposals` table
- Filters to `is_active_project = 0` (proposals not yet converted to projects)
- Excludes Lost/Declined/Dormant/Contract Signed/Cancelled
- Shows proposals with >7 days no contact
- Categories: URGENT (14+ days or NULL), NEEDS ATTENTION (7-13 days)
- Fixed column name: `project_value` not `total_fee_usd`
- Added NULL handling for `last_contact_date`

**Frontend:** `/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/frontend/src/components/dashboard/hot-items-widget.tsx`
- Display format: `${project_code} (${project_name})`
- Navigation: `/proposals/${project_code}` (was `/tracker?code=${project_code}`)
- Increased from 6 to 10 visible items
- Increased urgent/needs_attention slicing from 3/2 to 5/5 items each

### Verified Results
```
Found 30 proposals needing follow-up
- 30 URGENT (no contact or 14+ days)
- 0 NEEDS ATTENTION (7-13 days)

Sample urgent items:
  - 25 BK-004 (The Ritz-Carlton Hotel Nanyan Bay, China)
  - 25 BK-007 (The Oberoi Resort and Residential Villa Project, I)
  - 25 BK-010 (Hummingbird Club)
```

**Next:** Restart backend to apply changes

---

## Dashboard Calculation Fixes (Dec 10, 2025 PM)

### Problem
Dashboard KPIs were calculating values incorrectly:
- **Remaining Contract Value** was subtracting ALL payments (including from completed projects) instead of only active projects
- **Outstanding Invoices** included invoices from ALL projects, not just active ones
- Formula was wrong: Was `Total - Paid`, should be `Total - Paid - Outstanding`

### Solution Applied ✅
Updated all dashboard calculations to:
1. **Filter to active projects only** - Only count invoices from `is_active_project = 1`
2. **Fix formula** - Remaining = Total Contract - Paid - Outstanding
3. **Add breakdown** - API now returns `{total_contract, paid, outstanding, value}` for transparency

### Files Modified
- `backend/api/routers/dashboard.py` - Fixed 3 functions:
  - `get_role_based_stats()` - Bill & Finance roles now filter to active projects
  - `get_dashboard_kpis()` - Main KPI endpoint uses correct formula
  - `get_decision_tiles()` - Overdue invoices filtered to active projects

### Verified Results
```
Total Contract (Active):  $63,028,778.00
Paid (Active):           $31,261,156.14
Outstanding (Active):     $4,204,736.25
REMAINING:               $27,562,885.61

Comparison (if we used ALL projects):
All Paid:                $35,998,083.64  (Difference: $4.7M)
All Outstanding:         $4,843,573.75   (Difference: $638K)
```

**Impact:** More accurate financial picture - excludes completed/inactive project money

---

## Data Foundation Audit (Dec 10, 2025)

### Issues Fixed ✅
- **FK enforcement:** ENABLED in dependencies.py and base_service.py
- **Invoice due_dates:** 418/420 backfilled (2 missing invoice_date)
- **is_active_project:** Set for 49 active projects
- **learning_events table:** Created and ready
- **proposal_status_history:** Seeded with current data
- **Pattern counter:** Fixed - `times_matched` now increments when patterns match (was always 0)
- **Email dates:** All 3,773 emails now ISO format (normalized 49)
- **Dashboard calculations:** Fixed to filter to active projects only (Dec 10 PM)

### Issues Remaining ⚠️
- **53 projects missing contract_signed_date** - Need manual data entry
- **37 proposals missing project_value** - Need proposal documents
- **Pattern usage:** Counter now working (verified: 3 patterns used, 4 total matches)

### Database Health ✅
- **Tables:** 98 (was 108, dropped 10 dead tables)
- **Orphaned links:** 0
- **FK enforcement:** ON
- **Date quality:** 100% ISO format (3,773/3,773)
- **Invoice coverage:** 99.5% with due_dates (418/420)

---

## 🚀 MULTI-AGENT SPRINT (Dec 10, 2025)

### ⚠️ HONEST ASSESSMENT
**What got done:** New APIs, new components, data fixes
**What's still broken:** Most pages untested, pattern matching, many widgets
**User feedback:** "still so many pages still needs so much fucking work"
**Next session:** User will provide specific priorities

### Phase 0 Fixes ✅ DONE
- ✅ **Contacts pagination** - Added First/Prev/Next/Last buttons
- ✅ **Review link in main nav** - Added "Review" link to AI Suggestions
- ✅ **Currency data fixed** - All proposal values now USD (was mixing VND, INR, CNY)
- ✅ **Pipeline value corrected** - $87.5M active pipeline (was $176M due to currency bug)

### Phase 1 Backend APIs ✅ CREATED (not fully tested)
- `GET /api/dashboard/stats?role={bill|pm|finance}`
- `GET /api/proposals/{code}/timeline`
- `GET /api/proposals/{code}/stakeholders`
- `GET /api/projects/{code}/team`

### Phase 1 Frontend Components ✅ CREATED (integration unclear)
- `KPICard`, `RoleSwitcher` - on dashboard page
- `StakeholdersCard`, `TeamCard` - on detail pages
- Build passes

### ❌ STILL BROKEN (not addressed this session)
- Pattern matching "Times Used: 0"
- RFIs page console errors
- Many widgets showing wrong/no data
- Most of the 33 pages not verified
- No page-by-page audit done

### Data Status
- `proposal_stakeholders`: 110 records
- `proposal_events`: 26 records
- `v_proposal_priorities`: Working
- All currencies now USD

---

## 🚨 UX FIX SPRINT STATUS (Dec 10 - Earlier)

**Overall Grade: C+ → B-** - Fixes applied, needs testing.

### P0 - Query Page ✅ FIXED
- **Root cause:** Backend called `process_chat()` which didn't exist, AND wrapped response in `item_response()` which frontend didn't expect
- **Fix 1:** Changed to call `query_with_context()` - File: `backend/api/routers/query.py:81`
- **Fix 2:** Return raw result instead of wrapped - File: `backend/api/routers/query.py:87`
- **Test:** Backend returns `{success: true, results: [...]}` directly ✅

### P0 - Project Detail Pages ✅ FIXED
- **Root cause:** SQL only returned 5 fields, frontend expected 10+
- **Fix:** Added `project_name`, `current_phase`, `contract_signed_date`, `paid_to_date_usd`, etc.
- **Bonus:** Falls back to `proposals` table if not in `projects` (for pre-contract)
- **File:** `backend/api/routers/projects.py:157-260`
- **Test:** Restart backend and verify

### P1 - Project Names ✅ FIXED
- **Root cause:** Daily briefing didn't include `project_name` field
- **Fix:** Added `project_name` to urgent/needs_attention responses
- **File:** `backend/api/routers/dashboard.py:532, 541`
- **Note:** Financial service already had `project_name` - frontend was correct

### P1 - Remaining Issues
- Email review queue (`/admin/suggestions`) not in main navigation
- 153 learned patterns exist but "Times Used: 0" - pattern matching not triggering
- RFIs page has console errors
- Dashboard widgets need verification (remaining contract value calculation, etc.)

---

## What's Working ✅
- Email sync (3,773 emails, automated hourly)
- Proposal pipeline table
- Finance pages (invoice aging, payments)
- Dashboard stats (real numbers)
- Data quality excellent (0 orphans)

---

## Multi-Agent Workflow

**Agents available:** Auditor, Frontend, Backend, Data Engineer
**Prompts:** See `.claude/HANDOFF.md` Section 22

---

## 🚀 LEARNING LOOP - VERIFIED WORKING

### How It Actually Works (Clarified Dec 10)

**Two Separate Systems:**

| System | What It Does | Requires Approval? |
|--------|--------------|-------------------|
| **Layer 1: Auto-Categorization** | Assigns `internal_scheduling`, `project_contracts`, etc. | ❌ NO - Automatic |
| **Layer 2: AI Suggestions** | Creates `email_link`, `new_contact`, `missing_data` | ✅ YES - User reviews |

**Current Coverage:**
- 92% categorized automatically (3,459/3,770)
- 151 learned patterns for email→proposal linking
- Correction flow exists at `/admin/suggestions` → "Reject with Correction"

### Session Fixes (Dec 10)
- ✅ Linked 9 Soi 27/Hoxton emails to 25 BK-086 (were unlinked after bad suggestion)
- ✅ Created pattern: `Soi 27` → 25 BK-086 (Hoxton Hotel)
- ✅ Created pattern: `@landunion.com` → 25 BK-086 (client domain)
- ✅ Verified learning loop UI exists in `/admin/suggestions`

### UI Fixes (Dec 10)
- ✅ Tracker: Added `?filter=needs-followup` URL param support
- ✅ Tracker: Added Suspense wrapper (Next.js 14+ requirement)
- ✅ HotItemsWidget: Fixed suggestion links → `/admin/suggestions`
- ✅ QueryWidget: **FIXED** - Dynamic import with ssr:false, re-enabled on dashboard
- ✅ Build: Verified passing (no TypeScript errors)

### UI Fixes (Dec 10 - Session 2)
- ✅ QueryWidget: Fixed SSR localStorage issue with dynamic import wrapper
- ✅ QueryWidget: Re-enabled on main dashboard (was commented out)
- ✅ Finance page: Implemented **Revenue Trends** chart (real data, last 12 months)
- ✅ Finance page: Implemented **Client Payment Behavior** chart (top clients, payment speed)
- ✅ Backend: Added `/api/invoices/revenue-trends` endpoint

---

## 🔧 SYSTEM CLEANUP SPRINT (Dec 10-11 - COMPLETE ✅)

### Phase 1 (Dec 10)
- ✅ **DB tables dropped:** 105 → 103 (decision_log, document_proposal_links, document_versions, query_log)
- ✅ **SSR "use client" check:** All 33 dashboard pages already have directive
- ✅ **Unused UI components:** Files don't exist (avatar.tsx, dropdown-menu.tsx, tooltip.tsx)
- ✅ **Proposal Intelligence tables created:** Migration 078 applied (6 new tables + 3 views)

### Phase 2 (Dec 11)
- ✅ **Browser API audit:** invoice-aging-widget `window.URL` is SAFE (only in click handler)
- ✅ **Contact archives dropped:** Migration 080 - contacts_only_archive, project_contacts_archive, contact_metadata_archive (backups, data already in contacts table)
- ✅ **Pattern tables cleaned:** learned_patterns + learning_patterns dropped (never read by any code). KEPT: email_learned_patterns (153 patterns for email→proposal linking) + category_patterns (196 patterns for email categories)
- ✅ **Deliverables endpoint:** Deleted commented `seed-from-milestones` code
- ✅ **Dead services deleted (7 files):** schedule_emailer.py, schedule_pdf_generator.py, schedule_pdf_parser.py, comprehensive_auditor.py, cli_review_helper.py, file_organizer.py, intelligence_service.py

### Final Numbers
**Database:** 103 → 98 tables (dropped 5 more dead tables)
**Backend services:** 60 → 53 files (deleted 7 orphaned)
**Frontend:** 35 pages, 87 components, SSR all good

### Known Frontend Issues (RESOLVED)
- ~~QueryWidget uses localStorage during SSR~~ → **FIXED** with dynamic import
- White screen after builds = stale webpack chunks. Fix: `rm -rf .next && npm run dev`
- ~~Finance page has placeholder charts~~ → **FIXED** with real data charts

### Known Gap
When rejecting a suggestion, user must SELECT the correct proposal + check "Learn from correction" for the system to learn. If they just click "Reject" without providing the correct answer, no pattern is created.

---

## Foundation Status

Wave 1 + Wave 2 agents ran Dec 10. All critical fixes applied.

---

## Live Numbers (Updated Dec 16 - CLI Workflow Session)

| Entity | Count | Change |
|--------|-------|--------|
| Emails | 3,842 | +37 |
| Proposals | 106 | +3 |
| Projects | 60 | - |
| Contacts | 547 | +1 |
| email_proposal_links | 1,995 | +60 |
| email_project_links | 576 | +63 |
| Emails handled (linked or categorized) | 3,304 | **86%** ↑ |
| Unhandled (needs review) | 538 | **14%** |
| BDS emails linked | 710/974 | **73%** |
| email_attachments | 2,070 | - |
| category_patterns (active) | 196 | - |
| email_learned_patterns | 153 | +17 |
| ai_suggestions | 1,338 | - |

### Email Coverage Note
- **Linked to proposals:** 1,995 emails
- **Linked to projects:** 576 emails
- **Categorized (INT/PERS/SKIP/SM/MKT):** 918 emails that don't need proposal links
- **Unhandled:** 538 emails need categorization (internal comms, Bensley Brain discussions, etc.)

### Email Linking Health (Dec 11)
- **87 of 103 active proposals have emails linked (84%)**
- 16 proposals without emails predate email import (no emails to link)
- Confidence threshold lowered from 0.7 to 0.5 for better pattern matching
- Fixed `link_categories` table (was blocking email_project_links inserts)

### Proposal Pipeline
| Status | Count |
|--------|-------|
| Proposal Sent | 25 |
| Dormant | 24 | ← +7 marked dormant
| Contract Signed | 16 |
| First Contact | 12 | ← -7 (moved to Dormant)
| Lost | 8 |
| Proposal Prep | 6 |
| Negotiation | 5 |
| Declined | 4 |
| Meeting Held | 1 |
| On Hold | 1 |

**Active pipeline:** 38 proposals = **$87.5M USD** (not Lost/Declined/Dormant/Contract Signed/Cancelled)
**Note:** Currency data fixed Dec 10 - all values now USD (was incorrectly mixing VND, INR, CNY etc)

---

## What's Working

| System | Status |
|--------|--------|
| Email sync | Automated (cron hourly) |
| Email coverage | 92% categorized (3,416/3,727 in email_content) |
| Email→Proposal linking | 49% (1,833 emails) |
| Email→Project linking | 14% (513 emails) |
| Attachment→Proposal linking | 40% (838/2,099) |
| Date sorting | **Fixed** (all ISO format now) |
| Contact names | **Fixed** (0 missing, was 218) |
| Batch suggestion system | Working (48 batches approved) |
| Learned patterns | 341 patterns |
| Frontend | 34 pages (**build broken - needs fix**) |
| Backend API | 29 routers |

---

## What's Broken

| Issue | Impact | Fix |
|-------|--------|-----|
| ~~Frontend build~~ | ~~Can't deploy~~ | ✅ FIXED Dec 10 |
| ~~/api/proposals/stats~~ | ~~Dashboard zeros~~ | ✅ FIXED Dec 10 |
| ~~12 pending suggestions~~ | ~~Queue not empty~~ | ✅ APPROVED Dec 10 |
| ~~29 orphaned attachments~~ | ~~Dead references~~ | ✅ DELETED Dec 10 |
| ~~7 stale proposals~~ | ~~Wrong status~~ | ✅ MARKED DORMANT Dec 10 |
| ~~Hardcoded password~~ | ~~Security risk~~ | ✅ DELETED Dec 10 |

**All blockers resolved!**

---

## What's NOT Connected

| Source | Status |
|--------|--------|
| lukas@bensley.com | ✅ Active (automated) |
| bill@bensley.com | January 2026 |
| projects@bensley.com | January 2026 |
| invoices@bensley.com | January 2026 |
| dailywork@bensley.com | Q1 2026 |
| scheduling@bensley.com | Q1 2026 |

---

## Suggestion System Stats (Post Wave 2 - Final)

| Status | Count |
|--------|-------|
| applied | 692 | ← **Was 63 before Wave 1 (11x improvement)** |
| rejected | 548 |
| approved | 71 | ← Cannot auto-apply (see below) |
| accepted | 11 |
| rolled_back | 7 |
| pending | 0 |
| modified | 1 |

### 71 Approved (Cannot Auto-Apply)
| Type | Count | Why Failed |
|------|-------|------------|
| contact_link | 37 | Already linked or contact deleted |
| proposal_status_update | 16 | Wrong status format (lowercase vs TitleCase) |
| new_contact | 15 | Contacts already exist |
| new_proposal | 2 | No handler implemented |
| transcript_link | 1 | Transcript not found |

**Action:** These are stale suggestions. Consider rejecting them to clean up the queue.

### Wave 2 Enrichments Applied ✅
- 25 BK-074 (Project Sumba) → Sanda Hotel Co.,Ltd
- 25 BK-078 (Taitung Resort) → Queena Plaza Hotel Group
- 25 BK-062 (Solaire Manila) → Solaire Resort & Casino
- 25 BK-071 (Wangsimni Seoul) → Chairman Ahn Development Group

### Learned Patterns
- **341 patterns** stored
- **48 batches** approved

---

## Recent Work (Dec 8-10, 2025)

### Dec 10 (Full Day - Wave 1 + Wave 2 Agents)

#### WAVE 1 RESULTS
| Agent | Key Outcomes |
|-------|--------------|
| Builder | Created `apply_approved_suggestions.py`, fixed `approve_suggestion()` to set 'applied' status, **applied 688 suggestions** |
| Audit | Verified fixes, deleted 8 orphaned links, identified 12 malformed suggestions |
| Enrichment | Created 4 suggestions for client_company (pending review) |
| Outreach | Drafted follow-up emails (Lukas sent separately) |

#### WAVE 2 RESULTS
| Agent | Key Outcomes |
|-------|--------------|
| Audit (Final) | **Verified foundation is solid** - 0 orphans, 0 duplicates, 90% reduction in approved-not-applied |
| Data Engineer | Applied 4 client_company enrichments, confirmed gaps require manual entry |
| Builder | Fixed 27 bare except handlers across 16 files, verified frontend build passes |

#### KEY FIXES (Dec 10)
- **688 suggestions now properly applied** (was 63 - 10x improvement)
- 12 malformed email_links rejected
- 8 orphaned links deleted
- `approve_suggestion()` now sets status='applied' when changes succeed
- Zero orphaned links remaining
- Zero duplicate links

**Coordinator:**
- Emails sent: Meerut (25 BK-099), 625-Acre Punjab (25 BK-098), Siargao portfolio (25 BK-104)
- Created 5 Agent Prompts: `/contract-agent`, `/proposal-enrichment-agent`, `/audit-agent`, `/data-engineer-agent`, `/builder-agent`
- Reconciled conflicting agent reports (Audit Agent was wrong about email coverage)
- Updated STATUS.md with verified numbers
- Wrote January 2026 plan in roadmap.md

**Siargao fee proposal** - Lukas drafting (25 BK-104: 2.4ha, 10 villas + 4 residences, full scope)

### Dec 8-9 Summary

### Dec 9 (Evening - Audit Agent Session)
- **Status updates per Lukas:**
  - 25 BK-035 (Ratua Private Island) → **Lost** (going with Dubai company)
  - 25 BK-046 (Sukhothai Restaurant) → **Dormant** (no response)
  - 25 BK-054 (Xitan Hotel China) → **Lost** (dead)
  - 25 BK-052 (Santani Jebel Shams) → **Lost** (client declined)
  - 25 BK-041 (Paragon Dai Phuoc) → **On Hold** (Q1 2026)
  - 25 BK-029 (Pondicherry) → **Declined** (Millennium not doing)
  - 25 BK-039 (Wynn Marjan) → **Negotiation** (active with Helenka/Kim)
  - 25 BK-006 (Fenfushi Island Maldives) → **Contract Signed**
  - 24 BK-015 (Shinta Mani Mustang) → **Contract Signed**
- **Email linking audit - 108 new links:**
  - 25 BK-039 (Wynn Marjan): 31 emails linked
  - 25 BK-044 (Reliance Industries): 32 emails linked
  - 25 BK-063 (Akyn Hospitality Da Lat): 82 emails linked
  - 25 BK-081 (Lianhua Mountain): 21 emails linked
  - 25 BK-057 (Sol Group Korea): 10 emails linked
  - 25 BK-043 (Equinox Hotels/Sumba): 9 emails linked
- **Contacts updated with emails:** Reliance (Monalisa Parmar), Akyn (Nguyen Thi Be Thuy), Lianhua (Liu Shuai), Wynn (Kim Lange/Helenka), Equinox (Carlos De Ory)
- **Approved 4 pending batches + 1 suggestion**
- **Proposals with zero emails: 10 remaining** (legacy imports, emails in other mailboxes)

### Dec 9 (Afternoon - Coordinator Session)
- Reviewed all 15 INQUIRY-PENDING emails (6 distinct inquiries)
- Created 4 new proposals from inquiries:
  - 25 BK-104 (Pilar Cliff-Front Luxury Villas, Siargao, Philippines) - Jason Holdsworth - **Meeting Held**
  - 25 BK-105 (Ayun Resort Raja Ampat, Indonesia) - David Gomez/Ayun Group - First Contact
  - 25 BK-106 (Hyatt Resort Uttarakhand, India) - Sumit Pratap Singh/Gunjan Group - **Proposal Prep**
  - 25 BK-107 (Residential Project Punjab, India) - Magandip Riar - Meeting Held
- Updated existing 25 BK-079 → renamed to "Kasara Ghat Development, Kasuli, India"
- **Full thread linking for all 5 proposals:**
  - 25 BK-104: 6 emails (was 2)
  - 25 BK-105: 2 emails (was 1)
  - 25 BK-106: 23 emails (was 5) - includes all Brian/Lukas/Mink correspondence
  - 25 BK-107: 8 emails (was 4)
  - 25 BK-079: 10 emails (was 7)
- Created 2 new contacts (Jason Holdsworth, Damien J)
- Updated 5 existing contacts with full info (David Gomez, Sumit, Magandip, Mohnish, Vipul)
- Created 8 learned patterns for future email matching
- **INQUIRY-PENDING emails: 0 remaining**

### Dec 9 (Early AM - Coordinator Session)
- Full system audit revealed **92% emails were already handled** (previous "53%" metric was wrong)
- Fixed pattern matching - `times_used` counter wasn't incrementing
- Added patterns: PERS-BILL (Canggu land sale), SKIP-AUTO (SaaS), PERS-INVEST (crypto)
- Categorized remaining 294 emails → **100% email coverage**
- Approved 63 suggestions (46 email_link, 17 contact_link)
- Created Sanmar Bangladesh proposal (25 BK-103)
- Marked 12 stale proposals as Dormant
- Created 9 missing contacts
- 15 emails marked INQUIRY-PENDING for review (potential new projects)

### Dec 8 (Multiple Agents)
- Fixed emails.category garbage, email extraction regex, suggestion duplicates
- Converted follow_up_needed to weekly report
- Dropped 5 unused tables, fixed orphaned links
- Full audit identified correct metrics

### Data Quality Fixes
| Issue | Status |
|-------|--------|
| Pattern matching not incrementing | Fixed (batch_suggestion_service.py) |
| 294 unhandled emails | Fixed (100% coverage now) |
| emails.category garbage | Fixed (NULLed + 5 files updated) |
| Email extraction broken | Fixed (RFC 5322 regex) |
| Suggestion duplicates | Fixed (unique index + code dedup) |
| follow_up flood (150/day) | Fixed (weekly report instead) |
| Orphaned proposal links | Fixed (12 deleted) |
| Emails with NULL date | Fixed (118 backfilled) |

---

## Data Gaps (Require Manual Entry)

| Gap | Count | Source Needed |
|-----|-------|---------------|
| Missing client_company | 18 | Proposal docs |
| Missing contact_email | 9 | Business cards/LinkedIn |
| Proposals with 0 emails | 16 | **Predate email import** - no data available |

**Active Proposals Missing client_company (5):**
- 25 BK-009 (Safari Lodge Masai Mara) - Proposal Sent
- 25 BK-010 (Hummingbird Club) - Proposal Sent
- 25 BK-014 (Sanya Baoli Hilton) - Proposal Sent
- 25 BK-080 (Coorg Resort) - Proposal Sent
- 25 BK-101 (Texas Property) - First Contact

**Email Coverage by Proposal:**
- 20+ emails: 34 proposals (excellent)
- 6-20 emails: 34 proposals (good)
- 1-5 emails: 18 proposals (minimal)
- 0 emails: 16 proposals (need other sources)

---

## Priority Tasks (Next)

### Completed ✅
1. ~~**FIX PATTERN MATCHING**~~ ✅ Fixed - times_used now increments
2. ~~**Add missing patterns**~~ ✅ Added PERS-BILL, SKIP-AUTO, PERS-INVEST patterns
3. ~~**Categorize all emails**~~ ✅ 100% coverage (0 unhandled)
4. ~~**Review INQUIRY-PENDING emails**~~ ✅ All 15 processed (4 new proposals, linked, contacts created)
5. ~~**Apply approved suggestions**~~ ✅ 688 applied (was 63)
6. ~~**Clean orphaned links**~~ ✅ 0 remaining

### Completed (Dec 10 - Session 2)
**Proposal Intelligence System** - Migration created & applied ✅
- ✅ Migration 078_proposal_intelligence_system.sql - 6 new tables + 3 views
- ✅ `proposal_events` - Track meetings, calls, site visits, deadlines
- ✅ `proposal_follow_ups` - Track follow-up attempts and responses
- ✅ `proposal_silence_reasons` - Why we're not worried about silence
- ✅ `proposal_documents` - Document/proposal version tracking
- ✅ `proposal_decision_info` - Client decision timeline & competition
- ✅ `proposal_stakeholders` - Multiple contacts per proposal
- ✅ `v_proposal_priorities` - Smart priority view (URGENT/FOLLOW UP/MONITOR)
- ✅ `v_upcoming_proposal_events` - Upcoming events view
- ✅ `v_proposal_document_status` - Document tracking view

**Use Case Example:** When you schedule a meeting with a client for January, add it to `proposal_events` and add a `proposal_silence_reasons` entry with `valid_until` set to that date. The system will show "OK - scheduled_meeting" instead of "FOLLOW UP" for that proposal.

### Completed (Dec 11)
**Sent Email Linking + Proposal Version Tracking** - 100% complete ✅
- ✅ Migration 076_sent_email_linking.sql - Created & run
- ✅ Migration 077_proposal_version_tracking.sql - Created & run
- ✅ `sent_email_linker.py` - New service created
- ✅ `pattern_first_linker.py` - Modified to call sent_email_linker for @bensley.com
- ✅ `proposal_version_service.py` - Created with 5 methods
- ✅ API endpoints added:
  - `POST /api/emails/process-sent-emails` - Process unlinked sent emails
  - `GET /api/proposals/{project_code}/versions` - Get proposal versions & fee history
  - `GET /api/proposals/{project_code}/fee-history` - Get fee timeline
  - `GET /api/proposals/search/by-client` - Search proposals by client name
- ✅ Tested - All endpoints working

**Features Now Available:**
- Sent emails FROM @bensley.com now match via recipient (not skipped as internal)
- "How many proposals did we send to Vahine Island?" → `/api/proposals/search/by-client?client=Vahine&include_versions=true`
- Proposal version tracking with fee change history

### January 2026
1. **Connect projects@bensley.com** - Get credentials, add to .env
2. **Connect bill@bensley.com** - Requires Bill approval
3. **Process 71 approved suggestions** - 53 ready to apply, 18 need review
4. **Fill data gaps** - Manual entry for missing contact info
5. **37 projects with zero emails** - Old projects, backfill when data available

### Follow-up Email Status (Dec 10)
| Code | Name | Status |
|------|------|--------|
| 25 BK-099 | Meerut Hotel (Sarthak) | ✅ SENT |
| 25 BK-098 | 625-Acre India (Bhavleen) | ✅ SENT |
| 25 BK-104 | Siargao (Damien J/Jason) | ✅ Portfolio SENT - drafting fee proposal |
| 25 BK-100 | Krisala Pune (Nisha) | Pending |
| 25 BK-097 | CapitaLand Vietnam (Vu Hoang) | Pending |
| 25 BK-105 | Raja Ampat (David Gomez) | Pending |
| 25 BK-071 | Korea/Jinny | Pending |
| 25 BK-080 | Coorg (Akanksha) | Pending |
| 25 BK-050 | Manali (Manoj) | Pending |

**NOTE:** 25 BK-037 (La Vie) - HOLD - Bill said "vinod is a lying bastard stay away" - need clarification

### Other Proposals Needing Follow-up
| Code | Name | Last Contact | Days | Action |
|------|------|--------------|------|--------|
| 25 BK-063 | Akyn Da Lat | Nov 5 | 34 | **Follow up** |
| 25 BK-081 | Lianhua Mountain | Nov 6 | 33 | **Follow up** |
| 25 BK-045 | MDM Busan | Nov 6 | 33 | **Follow up** (Negotiation!) |
| 25 BK-057 | Sol Group Korea | Sep 22 | 78 | Dormant? |
| 25 BK-066 | Country Group Delhi | Sep 29 | 71 | Dormant? |
| 25 BK-067 | Mongolia UB Group | Sep 25 | 75 | Dormant? |
| 25 BK-053 | Darwish Oman | Aug 12 | 119 | Mark Dormant |
| 25 BK-107 | Punjab (Magandip) | Aug 27 | 104 | Mark Dormant |

---

## Quick Commands

```bash
# Run servers
cd backend && uvicorn api.main:app --reload --port 8000
cd frontend && npm run dev

# Sync emails
python scripts/core/scheduled_email_sync.py

# Weekly stale proposals report
python scripts/core/generate_stale_proposals_report.py

# Check suggestion counts
sqlite3 database/bensley_master.db "SELECT suggestion_type, status, COUNT(*) FROM ai_suggestions GROUP BY suggestion_type, status;"
```

---

## Notes

- Folder has typo: `Benlsey-Operating-System` (use this one)
- Email sync: cron hourly
- `contract_expired` is valid project status (flags for renewal review)
- staff vs team_members: keep both (HR view vs scheduling view)
