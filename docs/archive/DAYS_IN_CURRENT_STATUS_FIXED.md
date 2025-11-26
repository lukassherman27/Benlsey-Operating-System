# ✅ days_in_current_status Fixed - Computed Field Implementation

**Date:** 2025-11-25
**Status:** COMPLETE
**Approach:** Computed field (dynamic calculation)

---

## Problem

The `days_in_current_status` column in `proposal_tracker` table was stored as an INTEGER but never updated, causing stale/incorrect values.

---

## Solution: Computed Field

Replaced all static column references with dynamic JULIANDAY calculation:

```sql
CAST(JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER) as days_in_current_status
```

**Benefits:**
- ✅ Always accurate (never stale)
- ✅ No cron job needed
- ✅ Simpler to maintain
- ✅ Real-time calculation

---

## Changes Made

### File: backend/services/proposal_tracker_service.py

**4 queries updated:**

#### 1. Stats Query (Line 26)
**Before:**
```python
COALESCE(AVG(days_in_current_status), 0) as avg_days_in_status
```

**After:**
```python
COALESCE(AVG(CAST(JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER)), 0) as avg_days_in_status
```

#### 2. Follow-up Filter (Line 62)
**Before:**
```python
AND days_in_current_status > 14
```

**After:**
```python
AND CAST(JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER) > 14
```

#### 3. Proposal List Query (Line 184)
**Before:**
```python
SELECT
    ...
    days_in_current_status,
    ...
FROM proposal_tracker
```

**After:**
```python
SELECT
    ...
    CAST(JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER) as days_in_current_status,
    ...
FROM proposal_tracker
```

#### 4. Single Proposal Query (Line 225)
**Before:**
```python
SELECT
    ...
    days_in_current_status,
    ...
FROM proposal_tracker
WHERE project_code = ?
```

**After:**
```python
SELECT
    ...
    CAST(JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER) as days_in_current_status,
    ...
FROM proposal_tracker
WHERE project_code = ?
```

---

## Testing

### Database Test
```bash
sqlite3 database/bensley_master.db "
SELECT
    project_code,
    status_changed_date,
    CAST(JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER) as computed_days
FROM proposal_tracker
WHERE status_changed_date IS NOT NULL
LIMIT 5
"
```

**Results:**
```
25 BK-003|2024-09-13|438
25 BK-007|2024-10-18|403
25 BK-008|2024-09-27|424
25 BK-009|2024-09-27|424
25 BK-011|2024-09-20|431
```

✅ Realistic values (400+ days for proposals from Sept/Oct 2024)

---

### API Test 1: Stats Endpoint
```bash
curl http://localhost:8000/api/proposal-tracker/stats
```

**Result:**
```json
{
    "success": true,
    "stats": {
        "total_proposals": 37,
        "avg_days_in_status": 390.89,
        "needs_followup": 34
    }
}
```

✅ Average of 391 days - realistic!

---

### API Test 2: Single Proposal
```bash
curl http://localhost:8000/api/proposal-tracker/25%20BK-003
```

**Result:**
```json
{
    "success": true,
    "proposal": {
        "project_code": "25 BK-003",
        "status_changed_date": "2024-09-13",
        "days_in_current_status": 438
    }
}
```

✅ 438 days (Sept 13, 2024 → Nov 25, 2025) - correct!

---

## How It Works

### JULIANDAY Function
SQLite's `JULIANDAY()` converts dates to Julian day numbers (continuous count of days):

```sql
JULIANDAY('2024-09-13') = 2460565.5
JULIANDAY('2025-11-25') = 2461003.5
Difference = 438 days
```

### CAST to INTEGER
Ensures whole number of days (no decimals):
```sql
CAST(438.0 AS INTEGER) = 438
```

---

## Verification Script

To manually verify any proposal:

```bash
sqlite3 database/bensley_master.db "
SELECT
    project_code,
    status_changed_date,
    CAST(JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER) as days_in_current_status,
    current_status
FROM proposal_tracker
WHERE project_code = '25 BK-003'
"
```

---

## Performance Impact

**Minimal to none:**
- JULIANDAY is a built-in SQLite function (very fast)
- Calculation happens only when querying (not on every row in table)
- For typical queries (10-50 proposals), difference is microseconds
- Indexes on `status_changed_date` can help if needed

---

## Alternative Not Used: Daily Cron Job

We could have used a daily update job:

```python
# backend/jobs/update_proposal_days.py
cursor.execute("""
    UPDATE proposal_tracker
    SET days_in_current_status = CAST(
        JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER
    )
    WHERE status_changed_date IS NOT NULL
""")
```

**Why we didn't:**
- ❌ Requires cron setup
- ❌ Data stale until next run
- ❌ More complexity
- ❌ Can fail silently

---

## Success Criteria

- [x] days_in_current_status always accurate
- [x] No stale data
- [x] No cron job needed
- [x] Works in all queries (stats, list, single)
- [x] Tested with real data
- [x] API returns correct values

---

## Summary

**Problem:** Static column with stale values
**Solution:** Dynamic computed field using JULIANDAY
**Result:** Always accurate, real-time calculation

**Timeline:** 15 minutes
**Quality:** Production-ready

✅ COMPLETE
