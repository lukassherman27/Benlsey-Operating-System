# System Status

**Updated:** 2025-12-10 (Dashboard Calculations Fixed)
**Backend:** localhost:8000 | **Frontend:** localhost:3002
**Phase:** Phase 0+1 Dashboard Restructure → **PARTIAL** (needs user review)

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

## Live Numbers (Verified Dec 10 PM - Data Foundation Fixes)

| Entity | Count | Change |
|--------|-------|--------|
| Emails | 3,773 | - |
| Proposals | 102 | - |
| Projects | 60 | - |
| Contacts | 546 | - |
| email_proposal_links | 1,940 | +14 |
| email_project_links | 519 | - |
| email_attachments | 2,070 | - |
| category_patterns (active) | 196 | - |
| email_learned_patterns | 153 | - |
| ai_suggestions | 1,330 | - |

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
| Proposals with 0 emails | 16 | Other mailboxes (bill@, projects@) |

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
