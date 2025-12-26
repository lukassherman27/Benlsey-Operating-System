# System Status

**Updated:** 2025-12-26 (late evening)
**Backend:** localhost:8000 | **Frontend:** localhost:3002
**Phase:** Operations - Proposals UI Complete

---

## Current State

### Live Numbers

| Entity | Count |
|--------|-------|
| Emails | 3,879 |
| Proposals | 108 |
| Projects | 67 |
| Contacts | 467 |
| Linked Emails | 2,359 (61%) |
| Patterns | 153 |

### Pipeline Summary

| Metric | Value |
|--------|-------|
| **Active Pipeline** | $77.5M (64 proposals) |
| **Overdue Actions** | 34 proposals |
| **Ball in Our Court** | 29 proposals |
| **Stalled (14+ days)** | 15 proposals |

---

## Session Work (Dec 26 Evening)

### Completed: Activity Tracking (#140), Story Builder (#141), Weekly Report (#142)

**New Backend Services:**
- `activity_extractor.py` - Extract action items, dates, decisions from emails
- `proposal_story_service.py` - Generate proposal narratives with timeline
- `weekly_report_service.py` - Monday morning summary for Bill

**New API Endpoints:**
| Endpoint | Purpose |
|----------|---------|
| `GET /api/story/proposal/{id}` | Full proposal narrative |
| `GET /api/story/timeline/{id}` | Activity timeline |
| `GET /api/weekly-report` | Full weekly report |
| `GET /api/weekly-report/quick` | Dashboard stats |
| `GET /api/weekly-report/email-preview` | HTML email preview |

### Fixed: days_since_contact Bug (PR #147)

**Problem:** Siargao showed "1 day since contact" but it was actually 17 days.

**Root Cause:** `days_since_contact` was stored statically and never updated.

**Fix:** Dynamic calculation using SQLite:
```sql
CAST(JULIANDAY('now') - JULIANDAY(COALESCE(last_contact_date, created_at)) AS INTEGER)
```

Fixed in: `proposal_tracker_service.py`, `proposal_service.py`, `weekly_report_service.py`

---

## Session Work (Dec 26 Late Evening)

### Completed: Quick Actions (#134) + Analytics Dashboard (#143)

**Quick Actions (PR #149):**
- Added "Mark Followed Up" button (green checkmark) - flips ball to client
- Added "Flip Ball" button (arrows) - toggles us/them
- Both in Actions column with loading states
- Allows Bill to manage proposals without leaving tracker

**Analytics Dashboard (PR #150):**
- New `/api/analytics/trends` endpoint with time-series data
- Added "Analytics" tab to /overview page (4th tab)
- Charts using Recharts:
  - Pipeline Value Trend (12 month line chart)
  - Win Rate Trend (12 month line chart)
  - Pipeline by Status (horizontal bar)
  - Win Rate by Deal Size (bar chart)
- Summary metrics: Total/Weighted Pipeline, Avg Win Rate, Avg Days to Win
- Stage duration cards showing avg time in each status

**Also Closed:**
- #124 (duplicate endpoints) - Investigation showed no issue
- #126 (inconsistent responses) - Deferred to Q2 2026, documented

---

## Previous Session (Dec 26 Morning)

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

### Immediate: Proposals UI Overhaul (Plan file active)

1. **Tracker Priority Banner** - Show overdue/action items at top
2. **Tracker Owner Column** - See who owns what at a glance
3. **Overview Dashboard** - Executive metrics + Action Board + Weekly tabs
4. **Detail Next Action Card** - Clear CTA on detail page
5. **Detail Horizontal Timeline** - Visual proposal journey

### Then
- [ ] #107: Project management redesign
- [ ] #117: Refactor /story endpoint (1,150 lines)

---

## Open Issues (15)

### P0 - Critical
- #115: Comprehensive proposals audit (in progress)
- #117: /story endpoint 1,150 lines - unmaintainable

### Proposals Enhancements
- #134: Quick Actions in Tracker
- #137: Saved Filter Views
- #143: Analytics Dashboard

### Cleanup
- #124: Duplicate proposal list endpoints
- #126: Inconsistent API response formats

### Project Management
- #107: Project management redesign

### Data
- #100: Legacy category column
- #101: Normalize match_method values

### Business Decisions
- #60: $0.9M invoices >90 days
- #61: Empty tables

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
