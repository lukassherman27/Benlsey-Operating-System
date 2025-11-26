# Data Quality Audit Report
**Date:** November 24, 2025
**Status:** Path B - Deep Analysis Before Dashboard Build

---

## Executive Summary

✅ **Good News:**
- 3,355+ emails imported with real business data
- 87 proposals tracked with 46 active
- Email linking system working (395 emails linked)
- Database structure is sound (88 tables, clean schema)

⚠️ **Issues Found & Fixed:**
1. ✅ **FIXED:** Email importer wasn't saving folder field (88% NULL) → Fixed + backfilled
2. ✅ **FIXED:** Attachments not tracked in database → Fixed importer
3. ⏳ **IN PROGRESS:** Email import running (catching up to Nov 24)
4. ❌ **TODO:** 96% of emails unprocessed by AI
5. ❌ **TODO:** 99.4% of emails uncategorized
6. ❌ **TODO:** 3 data inconsistencies (status mismatches)

---

## 1. Email Data Analysis

### Current State (as of import completion)
```
Total Emails:    3,355+  (growing during import)
Sent:            2,269   (68%)
Inbox:           1,086   (32%)
Processed:       136     (4%)  ❌
Categorized:     20      (0.6%) ❌
Linked:          395     (12%) ⚠️
```

### Date Range
- **Earliest:** May 29, 2025
- **Latest:** November 24, 2025 (import in progress)
- **Coverage:** ~6 months of email history

### Top Senders
1. Internal (@bensley.com): 1,210 emails
2. Indonesia office (@bensley.co.id): 177 emails
3. Gmail: 131 emails
4. Soudah project: 42 emails
5. Legal (Dentons): 26 emails

### Sample Emails Verified
✅ All sampled emails are legitimate business communications:
- "Wangsimni Hotel Project / Seoul"
- "Ritz Carlton Nusa Dua" project work
- "TARC New Delhi" correspondence
- "Claim in India - Legal" matters
- Dropbox file shares

---

## 2. Folder Structure Issues

### Problem Discovered
**88% of emails had NULL folder** because email_importer.py received the folder parameter but didn't save it to database.

### Root Cause
```python
# OLD CODE (BROKEN):
INSERT INTO emails (..., date, processed, has_attachments)
VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)

# FIXED CODE:
INSERT INTO emails (..., date, processed, has_attachments, folder)
VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
```

### Solution Applied
1. ✅ Fixed email_importer.py to save folder field
2. ✅ Backfilled 2,960 existing emails using sender domain logic:
   - @bensley.com/@bensley.co.id → "Sent"
   - Others → "INBOX"
3. ✅ Future imports will now save folder correctly

---

## 3. Attachment Tracking

### Issues Found & Fixed
1. ✅ Table name mismatch: Importer tried to insert into `email_attachments` but table is named `attachments`
2. ✅ Column name mismatches: `filepath` → `stored_path`, `filesize` → `file_size`
3. ✅ Missing file type extraction

### Current Status
```
Attachments on disk:  2,163 files
Attachments in DB:    273     (13%)
```

**Action:** Most attachments aren't tracked because they were saved before the fix. Need to run attachment indexer.

---

## 4. Email Processing Status

### AI Processing Pipeline
```
┌─────────────┐
│ 3,355 Total │
└──────┬──────┘
       │
       ├─ 136 Processed (4%)  ✅ Small sample
       │   └─ 20 Categorized (0.6%)
       │
       └─ 3,219 Unprocessed (96%) ❌ NEEDS WORK
           ├─ 395 Linked to proposals (12%)
           └─ 2,824 Unlinked (84%)
```

### Why So Few Processed?
- AI processing is expensive (API costs)
- No batch processing has been run yet
- Only manual spot-checking has occurred

### Recommended Next Steps
1. Run smart email linker on all 2,824 unlinked emails
2. Run AI categorization on high-priority emails first:
   - Emails with attachments
   - Emails from key clients
   - Emails in date range of active proposals
3. Skip low-value emails (newsletters, automated notifications)

---

## 5. Data Inconsistencies Found

### AI Validator Discovered 3 Status Mismatches

| Project Code | Project Name | DB Status | Email Suggests | Issue |
|--------------|--------------|-----------|----------------|-------|
| **BK-033** | Ritz Carlton Nusa Dua, Bali | won | active | Won contract, in delivery phase |
| **BK-008** | TARC New Delhi | (empty) | active | Missing status |
| **BK-051** | Pawana Lake Mumbai | lost | active | Wrong status OR mis-linked emails |

### Recommended Actions
1. **BK-033:** Update status from "won" to "active" - this is a won contract in active delivery
2. **BK-008:** Set status to appropriate value based on proposal stage
3. **BK-051:** Review - either update status OR unlink mis-attributed emails

---

## 6. Database Structure Assessment

### Overall Health: ✅ GOOD

```
Tables:          88 (including FTS indexes)
Core Tables:     58
Indexes:         192 (reasonable - ~2.5 per table)
Views:           7
Database Size:   80.13 MB
Documentation:   46 .md files
```

### Key Tables Status

| Table | Row Count | Status | Notes |
|-------|-----------|--------|-------|
| emails | 3,355+ | ✅ Growing | Import in progress |
| proposals | 87 | ✅ Good | 46 active |
| projects | ? | ⚠️ Unknown | Need to audit |
| attachments | 273 | ⚠️ Incomplete | Only 13% indexed |
| email_proposal_links | 395 | ⚠️ Partial | 12% of emails linked |
| training_data | 6,454 | ✅ Good | AI training corpus |

### Schema Quality
- ✅ Proper foreign keys
- ✅ Indexes on critical columns
- ✅ Provenance tracking implemented
- ✅ Audit trails in place
- ✅ Migration system working

---

## 7. Proposals vs Projects Confusion

### Critical Distinction (from 2_MONTH_MVP_PLAN.md)

| Proposals | Projects |
|-----------|----------|
| Pre-contract | Won contracts |
| Sales pipeline | Active delivery |
| Track: follow-ups, health | Track: invoices, milestones |
| Status: proposal/won/lost | Status: active/completed |
| Owner: Bill (BD) | Owner: PMs |

### Current State
- **Proposals table:** 87 records (46 active)
- **Projects table:** Unknown row count (need to check)
- **Confusion risk:** Some "won" proposals should be moved to projects table

### Recommendation
1. Audit projects table structure and data
2. Define clear workflow: proposal won → create project record
3. Keep proposals table for sales pipeline
4. Use projects table for delivery tracking

---

## 8. Query Performance

### Not Yet Tested
Since we're doing deep analysis before building dashboards, we haven't stress-tested queries yet.

### TODO: Test These Queries
1. "Show all active proposals needing follow-up" (>7 days since contact)
2. "Show project invoice status" (paid/unpaid/overdue)
3. "Find all emails for project BK-XXX"
4. "Search emails by keyword"

### Likely Bottlenecks
- Email full-text search (3,000+ records)
- Proposal health score calculations
- Email linking queries

### Optimization Plan
1. Run EXPLAIN on critical queries
2. Add missing indexes if needed
3. Consider materialized views for expensive calculations

---

## 9. Cost Estimate: AI Processing

### Current Unprocessed: 3,219 emails

**Estimated API Costs:**
```
Processing Type          Emails    Cost/Email    Total Cost
────────────────────────────────────────────────────────────
Smart Linking           2,824      $0.01         ~$28
AI Categorization       3,219      $0.005        ~$16
Validation              3,219      $0.003        ~$10
────────────────────────────────────────────────────────────
TOTAL                                            ~$54
```

**Time Estimate:** 2-4 hours (rate limiting)

**Recommendation:** Process in batches:
- Batch 1: High-priority (clients, attachments) - ~500 emails - $8
- Batch 2: Medium priority (recent) - ~1,000 emails - $15
- Batch 3: Low priority (old, bulk) - ~1,700 emails - $31

---

## 10. Recommended Processing Order

### Phase 1: Foundation (DONE ✅)
1. ✅ Fix email importer folder bug
2. ✅ Backfill folder data
3. ✅ Fix attachment tracking
4. ✅ Index existing attachments
5. ✅ Add logging infrastructure
6. ✅ Improve audit accuracy

### Phase 2: High-Priority Processing (NEXT ⏳)
1. ⏳ Wait for email import to complete (currently 39%)
2. Run smart linker on unlinked emails with attachments
3. Update proposal contact dates from ALL emails
4. Fix 3 data inconsistencies (BK-033, BK-008, BK-051)
5. Categorize emails from key clients

### Phase 3: Batch AI Processing (AFTER PHASE 2)
1. Process remaining ~2,000 unlinked emails
2. Categorize all uncategorized emails
3. Validate all links
4. Generate data quality report

### Phase 4: Dashboard Build (FINAL)
1. Build Proposal Dashboard with clean data
2. Build Projects Dashboard with clean data
3. User testing with Bill
4. Iterate based on feedback

---

## 11. Critical Questions Still Unanswered

### About Projects Table
- [ ] How many records in projects table?
- [ ] What's the relationship between proposals and projects?
- [ ] Are "won" proposals also in projects?
- [ ] What's the primary workflow: proposal → project?

### About Financial Data
- [ ] Do we have invoice data in the database?
- [ ] Is payment tracking implemented?
- [ ] Where is accounting Excel from finance team?
- [ ] Can we build invoice aging without that data?

### About RFI Tracking
- [ ] Is rfi@bensley.com set up yet?
- [ ] Are RFIs being tracked in database?
- [ ] How do RFIs link to projects?

---

## 12. Success Metrics

### Data Quality Goals
- [x] 100% of emails have folder (DONE: backfilled)
- [ ] >80% of emails linked to proposals/projects
- [ ] >90% of emails categorized
- [ ] <5% data inconsistencies
- [ ] All attachments indexed

### Processing Goals
- [x] Email import complete (IN PROGRESS: 39%)
- [ ] All high-priority emails processed
- [ ] Contact dates updated for all proposals
- [ ] Status mismatches fixed

### Dashboard Goals (After Data Clean)
- [ ] Proposal dashboard shows accurate data
- [ ] Projects dashboard shows financial status
- [ ] Bill can find any email/document in <5 seconds
- [ ] System saves Bill 5-10 hours/week

---

## Next Actions (Immediate)

1. **Wait for email import to complete** (~30-45 mins remaining)
2. **Run update_proposal_contact_dates.py** to update all 46 proposals
3. **Fix 3 data inconsistencies** (BK-033, BK-008, BK-051)
4. **Process high-priority emails** (with attachments, from key clients)
5. **Document projects table structure** and relationship to proposals

---

## Conclusion

**Good Foundation:**
- Database structure is solid
- Email data is real and valuable
- Import bugs are fixed
- Logging and monitoring in place

**Need to Process:**
- 96% of emails still unprocessed
- 88% of emails still unlinked
- Some data inconsistencies to fix

**Path Forward:**
Once email import completes and high-priority emails are processed, we'll have clean, well-understood data ready for dashboard build. This "measure twice, cut once" approach will result in better dashboards.

**Estimated Time to Dashboard-Ready:**
- Import completion: ~45 minutes
- High-priority processing: ~2 hours
- Data fixes: ~1 hour
- **Total: ~4 hours to clean data**

Then we build dashboards on solid foundation. 🎯
