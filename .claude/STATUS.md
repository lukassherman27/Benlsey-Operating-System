# System Status

**Updated:** 2025-12-26
**Backend:** localhost:8000 | **Frontend:** localhost:3002
**Phase:** Operations - Project Management Redesign

---

## Current State

### Live Numbers

| Entity | Count |
|--------|-------|
| Emails | 3,879 |
| Proposals | 108 |
| Projects | 67 |
| Contacts | 467 |
| Invoices | 436 |
| Patterns | 153 |
| Staff | 100 |
| Contract Phases | 15 |
| Schedule Entries | 1,120 |

### Email Linking Stats

| Metric | Count |
|--------|-------|
| Linked emails | 2,095 (54%) |
| Unlinked (linkable) | 515 |
| Unlinked (standalone) | 1,269 (correctly not linked) |

### Pipeline Summary

| Metric | Value |
|--------|-------|
| **Active Pipeline** | $41.97M (35 proposals) |
| **Contract Signed** | $25.58M (18 proposals) |
| **Declined/Lost** | 26 proposals |
| **Dormant** | 24 proposals |

---

## Session Work (Dec 26)

### Major Work: Project Management Redesign (#107)

**Problem:** Projects page was 95% finance metrics, 5% project management. No visibility into:
- Where project is in lifecycle (Concept → SD → DD → CD → CA)
- Who's working on it (PM, team, schedule)
- What we sent to client (submissions, feedback)
- Daily work (Bill/Brian review)

**Solution:** Complete redesign with new tables and components.

### Database Migrations Created

| Migration | Purpose |
|-----------|---------|
| 095 | Add `pm_staff_id` to projects + PM history table |
| 096 | Create `daily_work` table (Bill/Brian review workflow) |
| 097 | Create `client_submissions` table (track what we send) |

### New Tables

```sql
-- PM on projects
projects.pm_staff_id INTEGER REFERENCES staff(staff_id)
project_pm_history (track PM assignment changes)

-- Daily work for Bill/Brian review
daily_work (
  staff_id, project_code, work_date,
  description, task_type, attachments,
  reviewer_id, review_status, review_comments
)

-- Client submissions tracking
client_submissions (
  project_code, discipline, phase_name,
  submission_type, title, revision_number,
  submitted_date, files, client_feedback, status,
  linked_invoice_id
)
```

### Components Built

| Component | Purpose |
|-----------|---------|
| `PhaseProgressBar` | Visual Concept→SD→DD→CD→CA pipeline |
| `PhaseProgressCompact` | Compact version for list view |
| `ProjectCard` | New card for project list with phase progress |
| `ConversationView` | iMessage-style email view for proposals |

### API Endpoints Added

| Endpoint | Purpose |
|----------|---------|
| `GET /projects/{code}/phases` | Phase status for progress bar |
| `GET /proposals/{code}/conversation` | Emails for iMessage view |

### Issues Completed

| Issue | Description |
|-------|-------------|
| #98 | Conversation view for proposals (PR #103 merged) |
| #107 | Project management redesign (in progress) |
| #108 | Missing getProposalConversation API (PR #112) |
| #109 | POST /api/proposals wrong table (PR #112) |
| #110 | Typo project_coder in query service (PR #112) |
| #111 | Wrong column names in queries (PR #112) |

---

## Branch Status

| Branch | Purpose | Status |
|--------|---------|--------|
| `feat/project-management-107` | Project redesign | In progress |
| `main` | Production | Up to date |

---

## What's Working

| Feature | Status | Notes |
|---------|--------|-------|
| Proposal Tracker | Live | action_owner, ball_in_court tracking |
| Proposal Conversation | New | iMessage-style email view |
| Email Linking | Live | 54% linked, 515 to process |
| Pattern Learning | Live | 153 patterns, feedback working |
| Project Phases | New | Phase progress visualization |
| Finance Dashboard | Live | |
| Meeting Transcripts | Live | |

---

## What's Next

### Immediate (Issue #107)
- [ ] Redesign projects list page with phase progress
- [ ] Build daily work review UI for Bill/Brian
- [ ] Add PM assignments to projects
- [ ] Build submissions timeline component

### Upcoming
- [ ] #14: PM dashboard view
- [ ] #7: Claude CLI email workflow
- [ ] #20: Follow-up email drafting

---

## Open Issues (6)

### Project Management
- #107: Project management redesign (in progress)
- #14: PM dashboard (depends on #107)

### Data Cleanup
- #100: Legacy category column
- #101: Normalize match_method values

### Features
- #7: Claude CLI email workflow

### Automation (Phase 2)
- #19: Contact research
- #20: Follow-up drafting

### Business Decisions
- #60: $0.9M invoices >90 days
- #61: Empty tables (Phase 2)

### Infrastructure
- #22: OneDrive cleanup

---

## Database Schema Highlights

### Staff (100 people)
- 95 Design, 5 Leadership
- Owner: Bill, Principal: Brian, Director: Lukas
- No PM roles defined yet (need to identify PMs)

### Contract Phases (15 phases)
- Disciplines: Architecture, Interior, Landscape
- Phases: Mobilization, Concept, SD, DD, CD, CA
- Fee tracking per phase

### Schedule Entries (1,120 entries)
- Who works on what project each day
- Discipline, phase, task description
- Ready for daily work integration

---

## Quick Commands

```bash
# Start servers
cd backend && python3 -m uvicorn api.main:app --reload --port 8000
cd frontend && npm run dev

# Email sync
python scripts/core/scheduled_email_sync.py

# Check stats
sqlite3 database/bensley_master.db "
SELECT 'emails', COUNT(*) FROM emails
UNION SELECT 'proposals', COUNT(*) FROM proposals
UNION SELECT 'projects', COUNT(*) FROM projects
UNION SELECT 'staff', COUNT(*) FROM staff;
"
```

---

## For Full Context
- `CLAUDE.md` - Workflow rules
- `.claude/HANDOFF.md` - Business context
- `docs/ARCHITECTURE.md` - System design
- `docs/roadmap.md` - Vision and phases
