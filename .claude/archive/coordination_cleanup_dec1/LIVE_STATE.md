# LIVE_STATE.md - System Status

**Last Updated:** 2025-12-01 18:30
**Updated By:** Organizer Agent
**Status:** Reality Check Sprint COMPLETE

---

## CURRENT SYSTEM HEALTH

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API | ✅ Running | Port 8000, 28 routers |
| Frontend | ✅ Running | Port 3002, 23 pages |
| Database | ✅ Healthy | 3,498 emails, cleaned |
| Email Import | ✅ Fixed | Was broken 7 days |
| Suggestion Handlers | ✅ Fixed | Was applying to wrong records |
| Categorization | ✅ Reset | Rule-based, 2,837 categorized |

---

## DEC 1 SPRINT SUMMARY

### What Was Broken → Fixed

| Issue | Before | After |
|-------|--------|-------|
| Email import | Broken 7 days (env var) | ✅ 142 emails imported |
| email_content dupes | 5,607 rows (2,126 dupes) | ✅ 3,481 (unique) |
| Suggestion handlers | Applied to wrong record | ✅ Correct target_id |
| Contact encoding | 5 RFC 2047 garbage | ✅ Decoded (Korean, Chinese, etc.) |
| Project status | Mixed case (archived) | ✅ Normalized (Archived) |
| Admin links | 2 dead 404 links | ✅ Removed |
| RFI numbers | 2 null values | ✅ Auto-assigned |
| Category rules | @bensleydesign.com | ✅ @bensley.com |

### Workers Deployed: 13
- Phase 0: 1 (env fix)
- Phase 1: 3 (data cleanup)
- Phase 2: 3 (orchestration)
- Phase 3: 2 (UI fixes)
- Wave 3: 4 (features)

---

## CURRENT DATA STATUS

### Emails
| Metric | Value |
|--------|-------|
| Total emails | 3,498 |
| Linked to proposals | 660 (19%) |
| Linked to projects | 200 (6%) |
| Categorized | 2,837 (81%) |
| In review bucket | 661 (19%) |

### Categorization (NEW Rule-Based System)
| Category | Count |
|----------|-------|
| internal_scheduling | 1,924 |
| project_contracts | 426 |
| project_design | 271 |
| project_financial | 168 |
| automated_notification | 46 |
| general | 2 |
| uncategorized | 661 |

### Suggestions
| Status | Count |
|--------|-------|
| Pending | 7,475 |
| Approved | 9 |
| Rejected | 436 |
| Modified | 1 |
| **Total** | **7,921** |

---

## API STRUCTURE (28 Routers)

### Core Business
- `/api/proposals` - Proposal management
- `/api/projects` - Project management
- `/api/emails` - Email processing
- `/api/invoices` - Invoice management
- `/api/contracts` - Contract management

### Operations
- `/api/rfis` - RFI management
- `/api/meetings` - Meeting management
- `/api/milestones` - Milestone tracking
- `/api/deliverables` - Deliverables
- `/api/outreach` - Client outreach
- `/api/transcripts` - Meeting transcripts

### Documents & Files
- `/api/documents` - Document management
- `/api/files` - File management

### Intelligence & AI
- `/api/suggestions` - AI suggestions
- `/api/dashboard` - Dashboard & KPIs
- `/api/query` - Natural language queries
- `/api/intelligence` - AI intelligence
- `/api/email-categories` - Email categorization (NEW)

### Context & Admin
- `/api/context` - Context & notes
- `/api/training` - AI training data
- `/api/admin` - Admin & validation (includes run-pipeline)

### Finance & Analytics
- `/api/finance` - Financial data
- `/api/analytics` - Analytics

### Learning & Agents
- `/api/learning` - Learning system
- `/api/agent` - Agent interface

### Other
- `/api/contacts` - Contact management
- `/api/tasks` - Task management
- `/api/health` - Health checks

---

## FRONTEND PAGES (23)

### Dashboard
- `/` - Main dashboard

### Core
- `/projects` - Projects list
- `/projects/[code]` - Project detail
- `/projects/[code]/emails` - Project emails
- `/proposals` - Proposals redirect
- `/proposals/[code]` - Proposal detail
- `/tracker` - Proposal tracker
- `/contacts` - Contact management
- `/contracts` - Contract management

### Operations
- `/deliverables` - Deliverables
- `/rfis` - RFIs
- `/meetings` - Meetings
- `/tasks` - Tasks
- `/finance` - Finance

### Intelligence
- `/query` - Natural language query
- `/system` - System status

### Admin
- `/admin` - Admin overview
- `/admin/suggestions` - AI suggestions
- `/admin/email-categories` - Category management
- `/admin/email-links` - Email links
- `/admin/validation` - Data validation
- `/admin/financial-entry` - Financial entry
- `/admin/project-editor` - Project editor

---

## SUGGESTION HANDLERS (8 Types)

| Type | Handler | Target Table |
|------|---------|--------------|
| follow_up_needed | FollowUpHandler | tasks |
| transcript_link | TranscriptLinkHandler | meeting_transcripts |
| new_contact | ContactHandler | contacts |
| fee_change | FeeChangeHandler | proposals |
| deadline_detected | DeadlineHandler | tasks |
| info | InfoHandler | (none) |
| email_link | EmailLinkHandler | email_*_links |
| proposal_status_update | ProposalStatusHandler | proposal_tracker |

---

## NEW ENDPOINTS (Dec 1)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/run-pipeline` | POST | Full pipeline trigger |
| `/api/emails/scan-sent-proposals` | POST | Detect sent proposals |
| `/api/email-categories` | GET | List categories |
| `/api/email-categories/stats` | GET | Category stats |
| `/api/email-categories/uncategorized` | GET | Review bucket |
| `/api/email-categories/rules` | GET | Categorization rules |
| `/api/email-categories/{id}/assign/{email_id}` | POST | Assign category |

---

## REMAINING ISSUES

### Still Open
1. **Query [object Object] error** - Frontend error handling
2. **Admin nav unification** - Two different nav structures
3. **Timeline "Failed to load"** - API response format issue

### Low Priority
- 7,475 pending suggestions need processing
- 661 uncategorized emails need review

---

## QUICK REFERENCE

### Start Services
```bash
# Backend
cd backend && uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev
```

### Common Commands
```bash
# Run full pipeline
curl -X POST http://localhost:8000/api/admin/run-pipeline

# Generate weekly report
python scripts/core/generate_weekly_proposal_report.py

# Import new emails
python scripts/core/scheduled_email_sync.py

# Check health
curl http://localhost:8000/api/health
```

### Key Files
- Database: `database/bensley_master.db`
- Backup: `database/backups/pre_dedup_20251201.db`
- Reports: `reports/Bensley_Proposal_Overview_*.pdf`

---

## HANDOFF NOTES

### For Next Session
1. Three UI issues remain (Query error, admin nav, timeline)
2. Suggestion backlog (7,475) needs batch processing strategy
3. Weekly report ready to generate for Bill
4. System is stable - focus on polish, not fixes

### Key Learnings
1. ENV var mismatches can silently break features for days
2. Always add unique constraints when deduping
3. Handler registry pattern works well
4. Rule-based categorization more reliable than AI for simple cases
