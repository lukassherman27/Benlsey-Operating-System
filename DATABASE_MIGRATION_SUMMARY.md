# DATABASE MIGRATION & CONSOLIDATION (Nov 24, 2025)

## What Happened

We discovered TWO separate databases that were causing conflicts, duplicate data, and confusion. We consolidated them into ONE master database in OneDrive.

---

## The Problem

### Two Databases Existed:
1. **Desktop:** `/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db`
   - 80.2MB, 92 tables
   - Had historical data (2013-2020)
   - 547 invoices, 138 projects, 114 proposals
   - More features but OLDER data

2. **OneDrive:** `database/bensley_master.db`
   - 86.5MB, 59 tables
   - Had current data (2024-2025)
   - 253 invoices, 46 projects, 87 proposals
   - ACCURATE current data but missing features

### Symptoms:
- Duplicate email-proposal links (958 duplicates!)
- Wrong invoice amounts (Desktop showed $348k unpaid for Dang Thai Mai, should be $1M)
- Scripts accessing different databases
- Frontend sometimes getting stale data

---

## The Solution

### Phase 1: Investigation (Nov 24, 2025)
✅ Ran complete audit comparing both databases
✅ Found OneDrive had more accurate CURRENT data
✅ Found Desktop had valuable HISTORICAL data and extra features
✅ Identified 6 critical missing tables in OneDrive

### Phase 2: Critical Data Migration
✅ **Migrated 5 missing projects** ($8.5M worth)
   - 16 BK-076: JW Marriott Jeju
   - 23 BK-029: Mandarin Oriental Bali
   - 25 BK-013: Tel Aviv High Rise
   - 25 BK-030: Beach Club MO Bali
   - 25 BK-033: Ritz Carlton Reserve Bali

✅ **Migrated fee breakdowns** (372 rows)
   - project_fee_breakdown table with all phase fees
   - Frontend API now working for fee-breakdown endpoint

✅ **Migrated 6 critical tables** (3,000 rows)
   - contacts (465 rows)
   - invoice_aging (101 rows)
   - proposal_tracker (37 rows)
   - email_attachments (1,179 rows)
   - team_members (98 rows)
   - schedule_entries (1,120 rows)

### Phase 3: Historical Data (Optional)
⏳ **Created manual review system for 547 historical invoices**
   - Exported to CSV for user review
   - User can selectively import important historical data
   - Automated import script ready

---

## Current State

### ✅ ONEDRIVE DATABASE IS NOW THE MASTER

**Location:** `database/bensley_master.db`
**Size:** ~90MB
**Tables:** 66 (added 6 critical tables)

**Contains:**
- **51 projects** (46 original + 5 migrated)
- **87 proposals** with full contact info
- **253 current invoices** (2024-2025) + user-selected historical
- **3,356 emails** with processing working
- **372 fee breakdown entries** across all phases
- **465 contacts**
- **1,179 email attachments** tracked
- **98 team members**
- **1,120 schedule entries**

**Status:** ✅ **Production ready, frontend connected, accurate data**

---

## Desktop Database

**Location:** `/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db`
**Status:** ⚠️ **ARCHIVED - Do not use**

Contains historical data (2013-2020) that may be useful for reference:
- 547 old invoices ($51M total, mostly paid)
- 87 old projects/proposals
- Historical records

**Action:** Keep as backup/archive but DO NOT use for active work.

---

## Going Forward

### ✅ ALL WORK USES ONEDRIVE DATABASE

**Environment Variable:**
```bash
DATABASE_PATH=database/bensley_master.db
```

**Scripts point to:** OneDrive database (via .env)
**Backend API uses:** OneDrive database
**Frontend connects to:** Backend → OneDrive database
**Email processor uses:** OneDrive database

### 🚫 DO NOT:
- Use Desktop database for new work
- Create new database files
- Import data without validation
- Run scripts that bypass .env configuration

### ✅ DO:
- Always use `os.getenv('DATABASE_PATH')` in scripts
- Verify database location before major operations
- Create backups before migrations (stored in `database/backups/`)
- Document any schema changes

---

## Backups Created

All backups saved in: `database/backups/`

**Key backups:**
- `bensley_master_pre_import_20251124_190604.db` - Before project import
- `bensley_master_pre_critical_20251124_191049.db` - Before critical tables
- Multiple timestamped backups throughout migration

**Restore if needed:**
```bash
cp database/backups/[backup_name].db database/bensley_master.db
```

---

## Data Validation

### Verified Projects:
✅ **24 BK-074** (Dang Thai Mai): 15 fee phases, $4.9M total, $1M unpaid
✅ **23 BK-029** (Mandarin Oriental Bali): 15 phases, $2.9M total
✅ **25 BK-033** (Ritz Carlton Bali): 15 phases, $3.15M total

### Frontend API Verified:
✅ `/api/projects/{code}/fee-breakdown` - Working
✅ Returns correct phase breakdown data
✅ Matches screenshot validation

---

## Scripts Updated

**Working with OneDrive database:**
- `smart_email_processor_v3.py` ✅
- `bensley_email_intelligence.py` ✅
- All import scripts via DATABASE_PATH ✅
- Backend API services ✅

**Archive (don't use):**
- `smart_email_processor_v1.py`
- `smart_email_processor_v2.py`
- Old migration scripts

---

## If You Need Historical Data

**Process:**
1. Review `invoices_to_review.csv` (547 invoices exported)
2. Mark which ones to import with "YES"
3. Run `python3 import_reviewed_invoices.py`
4. Selected historical invoices will be imported with proper project linking

---

## Summary

✅ **Consolidated two conflicting databases into one master**
✅ **OneDrive database is now production**
✅ **Migrated all critical data (3,000+ rows)**
✅ **Frontend API working**
✅ **Email processing ready**
✅ **All backups saved**
✅ **Desktop database archived**

**Going forward:** Everything uses `database/bensley_master.db` in OneDrive.

**Contact:** Reference this document if questions about database location or migration arise.

---

*Migration completed: November 24, 2025*
*Database consolidated by: Claude Code*
*Verified by: User validation of key projects*
