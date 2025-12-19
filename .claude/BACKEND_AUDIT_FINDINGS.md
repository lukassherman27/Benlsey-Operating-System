# Backend Proposal System Audit - Critical Findings

**Date:** 2025-12-10
**Severity:** HIGH - System is overcomplicated and has data sync issues

---

## CRITICAL ISSUE #1: Two Tables, Out of Sync

### The Problem
There are TWO tables storing proposal data:
- `proposals` - 102 records (the REAL source of truth)
- `proposal_tracker` - 81 records (a DUPLICATE that's missing 21 proposals)

### Missing from proposal_tracker:
```
25 BK-001 - Ramhan Marina Hotel Abu Dhabi
25 BK-002 - Tonkin Palace Hanoi
25 BK-017 - TARC Luxury Residence Delhi
24 BK-018 - Ritz-Carlton Nanyan Bay Extension
25 BK-025 - APEC Downtown Vietnam
25 BK-030 - Beach Club Mandarin Oriental Bali
25 BK-033 - Ritz Carlton Reserve Nusa Dua
... and 14 more
```

### Why This is Breaking Things:
The service does LEFT JOINs between `proposals` and `proposal_tracker`:
```python
FROM proposals p
LEFT JOIN proposal_tracker pt ON p.project_code = pt.project_code
```

So proposals NOT in `proposal_tracker` get NULL for:
- country
- current_remark
- project_summary
- waiting_on
- next_steps
- etc.

### FIX:
**ELIMINATE `proposal_tracker` TABLE ENTIRELY**

All the fields it has either:
1. Already exist in `proposals` table (contact_person, status, value, etc.)
2. Should be calculated on-the-fly (days_in_status from history)
3. Are redundant (project_name, project_code stored twice)

---

## CRITICAL ISSUE #2: 5 Proposal Services (Too Many!)

### Current Services:
| Service | Lines | Purpose | Needed? |
|---------|-------|---------|---------|
| `proposal_service.py` | 24,012 | CRUD operations | YES |
| `proposal_tracker_service.py` | 23,936 | Tracking/status | MERGE INTO proposal_service |
| `proposal_intelligence_service.py` | 13,489 | AI analysis | MAYBE |
| `proposal_query_service.py` | 9,249 | Search queries | MERGE INTO proposal_service |
| `proposal_version_service.py` | 14,435 | Version history | KEEP (audit trail) |

### Recommendation:
Consolidate to 2 services:
1. `proposal_service.py` - All CRUD, queries, tracking
2. `proposal_version_service.py` - Audit trail only

---

## CRITICAL ISSUE #3: 24 Endpoints (Too Many!)

### Current Endpoints:
```
/proposals                           - List all
/proposals/stats                     - Stats
/proposals/at-risk                   - At risk list
/proposals/needs-follow-up           - Follow up list
/proposals/weekly-changes            - Weekly changes
/proposals/needs-attention           - Attention list
/proposals                    (POST) - Create
/proposal-tracker/stats              - DUPLICATE stats
/proposal-tracker/list               - DUPLICATE list
/proposal-tracker/disciplines        - Discipline filter
/proposal-tracker/countries          - Country filter
/proposal-tracker/{code}             - Detail
/proposal-tracker/{code}      (PUT)  - Update
/proposal-tracker/{code}/history     - Status history
/proposal-tracker/{code}/emails      - Email list
/proposals/{code}/versions           - Version history
/proposals/{code}/fee-history        - Fee changes
/proposals/search/by-client          - Client search
/proposals/{code}/timeline           - Timeline
/proposals/{code}/stakeholders       - Stakeholders
/proposals/{code}/documents          - Documents
/proposals/{code}/briefing           - Briefing
/proposals/{code}/story              - Story
/proposals/summary                   - Summary
```

### OBVIOUS DUPLICATES:
- `/proposals/stats` vs `/proposal-tracker/stats` - SAME DATA
- `/proposals` vs `/proposal-tracker/list` - SAME DATA
- `/proposals/at-risk` vs `/proposals/needs-attention` - OVERLAP

### Recommendation:
Consolidate to ~10 endpoints:
```
GET  /proposals                 - List with filters
GET  /proposals/stats           - Dashboard stats
GET  /proposals/{code}          - Detail
PUT  /proposals/{code}          - Update
GET  /proposals/{code}/timeline - Emails + status changes
GET  /proposals/{code}/history  - Version history
GET  /proposals/{code}/documents - Attachments
POST /proposals                 - Create
```

---

## ISSUE #4: Calculated Fields Done Wrong

### Days in Status
**Current:** Uses `COALESCE(pt.status_changed_date, p.updated_at, p.created_at)`
- Falls back to `updated_at` which changes on ANY update, not status changes
- Shows wrong number of days

**Should be:**
```sql
SELECT
    CAST(JULIANDAY('now') - JULIANDAY(
        (SELECT MAX(status_date)
         FROM proposal_status_history
         WHERE proposal_id = p.proposal_id
         AND new_status = p.status)
    ) AS INTEGER) as days_in_status
FROM proposals p
```

### Last Contact
**Current:** Sometimes null, sometimes from proposal_tracker, sometimes from emails
**Should be:** Always from MAX(emails.date) for linked emails:
```sql
SELECT MAX(e.date) as last_contact
FROM emails e
JOIN email_proposal_links epl ON e.email_id = epl.email_id
WHERE epl.proposal_id = p.proposal_id
```

---

## ISSUE #5: email_project_links vs email_proposal_links

**In `get_email_intelligence()` (line 486-514):**
The query correctly uses `email_proposal_links` now.

**BUT** the original audit found some endpoints using `email_project_links` (which is for SIGNED projects only, not proposals).

Double-check ALL queries that touch emails to ensure they use:
- `email_proposal_links` for proposals
- `email_project_links` for active projects (post-contract)

---

## SIMPLIFICATION PLAN

### Phase 1: Database Cleanup (30 min)
1. Migrate any unique data from `proposal_tracker` to `proposals`
2. DROP `proposal_tracker` table
3. Update all services to query `proposals` directly

### Phase 2: Service Consolidation (2 hours)
1. Merge `proposal_tracker_service.py` into `proposal_service.py`
2. Merge `proposal_query_service.py` into `proposal_service.py`
3. Delete the merged files

### Phase 3: Endpoint Cleanup (1 hour)
1. Remove duplicate endpoints
2. Consolidate `/proposal-tracker/*` into `/proposals/*`
3. Update frontend to use consolidated endpoints

### Phase 4: Fix Calculated Fields (30 min)
1. Fix `days_in_status` calculation
2. Fix `last_contact` calculation
3. Use `correspondence_summary` for remarks

---

## Quick Wins (Can Do Now)

### 1. Sync proposal_tracker to proposals (5 min)
```sql
INSERT INTO proposal_tracker (project_code, project_name, project_value, current_status)
SELECT project_code, project_name, project_value, status
FROM proposals
WHERE project_code NOT IN (SELECT project_code FROM proposal_tracker);
```

### 2. Fix days_in_status calculation (10 min)
Update `proposal_tracker_service.py` line 226 to use history table

### 3. Show correspondence_summary as remark (5 min)
Change `COALESCE(pt.current_remark, p.status_notes, '')` to include `p.correspondence_summary`

---

## Files to Modify

| File | Action | Priority |
|------|--------|----------|
| `proposal_tracker_service.py` | Fix queries, eventually merge | HIGH |
| `proposal_service.py` | Add missing methods | MEDIUM |
| `proposals.py` (router) | Remove duplicate endpoints | MEDIUM |
| `api.ts` (frontend) | Update to use consolidated endpoints | LOW |

---

## Summary

The proposal backend is **overcomplicated** with:
- 2 data tables (should be 1)
- 5 services (should be 2)
- 24 endpoints (should be ~10)
- Inconsistent data sources

**Root cause:** Multiple developers/agents added features without understanding existing code.

**Solution:** Consolidate everything to use `proposals` table as single source of truth, merge services, remove duplicate endpoints.

**Estimated cleanup time:** 4-5 hours for full consolidation.
