# Agent 4: Data Pipeline & Quality

**Role:** Ensure data flows into the system and maintain data quality
**Owner:** `scripts/`, `voice_transcriber/`, `database/migrations/`
**Do NOT touch:** `frontend/`, `backend/api/` (unless data-related bugs)

---

## Context

You are responsible for:
1. Voice transcription pipeline (already built)
2. Email import pipeline
3. Data quality checks and fixes
4. Database migrations if needed

**Read these files FIRST:**
1. `CLAUDE.md` - Project context
2. `.claude/CODEBASE_INDEX.md` - Where things live
3. `voice_transcriber/transcriber.py` - Existing transcriber
4. `database/SCHEMA.md` - Database structure

---

## Current Data State

| Table | Records | Quality |
|-------|---------|---------|
| projects | 54 | Good |
| proposals | 89 | Good |
| invoices | 253 | Good |
| emails | 3,356 | Good |
| meeting_transcripts | 10 | Growing |
| communication_log | 321 | Good |
| rfis | 3 | Sparse |
| project_milestones | 110 | Need dates |

**Key Issues:**
- RFIs: Only 3 records (sparse)
- Milestones: 110 records but ALL have NULL `planned_date`
- Need continuous email import running

---

## Your Tasks (Priority Order)

### P0: Verify Voice Transcriber is Running

**Check status:**
```bash
cd voice_transcriber
python transcriber.py --status
```

**Expected output:**
- Voice Memos folder exists
- Database connected
- API keys set
- Some files already processed

**If not working:**
1. Check `voice_transcriber/config.py` for settings
2. Verify OPENAI_API_KEY and ANTHROPIC_API_KEY
3. Check voice memos folder path

**Start continuous watcher:**
```bash
# Foreground (for testing)
python transcriber.py

# Or run once
python transcriber.py --once
```

**Verify transcripts are being created:**
```sql
SELECT id, audio_filename, detected_project_code, created_at
FROM meeting_transcripts
ORDER BY created_at DESC
LIMIT 5;
```

---

### P1: RFI Data Quality Check

**Current state:** Only 3 RFIs exist

**Query to check:**
```sql
SELECT * FROM rfis;

SELECT
    project_code,
    COUNT(*) as rfi_count,
    SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count
FROM rfis
GROUP BY project_code;
```

**Action items:**
1. Check if RFIs are being detected from emails
2. Review `scripts/core/rfi_detector.py`
3. Potentially re-run RFI detection on existing emails

**Re-run RFI detection (if needed):**
```bash
cd scripts/core
python rfi_detector.py --reprocess
```

---

### P1: Milestone Data Fix

**Problem:** All 110 milestones have NULL `planned_date`

**Check current state:**
```sql
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN planned_date IS NOT NULL THEN 1 ELSE 0 END) as with_date,
    SUM(CASE WHEN actual_date IS NOT NULL THEN 1 ELSE 0 END) as with_actual
FROM project_milestones;

-- Sample records
SELECT milestone_id, project_code, phase, milestone_name, planned_date, actual_date, status
FROM project_milestones
LIMIT 10;
```

**Options:**
1. **Backfill from actual_date:** If milestone is complete, copy actual_date to planned_date
2. **Manual entry:** Create a script to add planned dates from project schedules
3. **Future dates:** For active projects, estimate planned dates

**Migration script (Option 1):**

**Create file:** `database/migrations/033_backfill_milestone_dates.sql`

```sql
-- Backfill planned_date from actual_date for completed milestones
UPDATE project_milestones
SET planned_date = actual_date
WHERE planned_date IS NULL
  AND actual_date IS NOT NULL
  AND status = 'complete';

-- Verify
SELECT
    status,
    COUNT(*) as count,
    SUM(CASE WHEN planned_date IS NOT NULL THEN 1 ELSE 0 END) as with_planned
FROM project_milestones
GROUP BY status;
```

---

### P1: Email Import Status Check

**Check recent email imports:**
```sql
SELECT
    DATE(received_date) as date,
    COUNT(*) as emails
FROM emails
WHERE received_date > date('now', '-7 days')
GROUP BY DATE(received_date)
ORDER BY date DESC;
```

**If no recent emails:**
1. Check `backend/services/email_importer.py`
2. Verify IMAP credentials in config
3. Run manual import

**Manual import:**
```bash
cd backend
python -m services.email_importer --run-once
```

---

### P2: Communication Log Enhancement

The `communication_log` table links everything together. Verify it's being populated:

```sql
-- Check recent entries
SELECT comm_id, project_code, comm_date, comm_type, subject
FROM communication_log
ORDER BY comm_date DESC
LIMIT 10;

-- Check distribution by type
SELECT comm_type, COUNT(*) as count
FROM communication_log
GROUP BY comm_type;
```

**Expected types:** email, meeting, call, note

**If meetings not appearing:**
The voice transcriber should add entries to `communication_log` after processing. Check `voice_transcriber/transcriber.py` for this functionality.

---

### P2: Data Quality Report Script

**Create file:** `scripts/analysis/data_quality_report.py`

```python
#!/usr/bin/env python3
"""
Data Quality Report for BDS Operations Platform
Run weekly to check data health
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DATABASE_PATH", "database/bensley_master.db")

def run_report():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print(f"BDS DATA QUALITY REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Table counts
    tables = [
        "projects", "proposals", "invoices", "emails",
        "meeting_transcripts", "rfis", "project_milestones",
        "communication_log", "contacts", "clients"
    ]

    print("\n📊 TABLE COUNTS:")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count}")
        except:
            print(f"  {table}: ERROR")

    # Recent activity
    print("\n📅 RECENT ACTIVITY (7 days):")

    cursor.execute("""
        SELECT COUNT(*) FROM emails
        WHERE received_date > date('now', '-7 days')
    """)
    print(f"  New emails: {cursor.fetchone()[0]}")

    cursor.execute("""
        SELECT COUNT(*) FROM meeting_transcripts
        WHERE created_at > date('now', '-7 days')
    """)
    print(f"  New transcripts: {cursor.fetchone()[0]}")

    # Data quality issues
    print("\n⚠️  DATA QUALITY ISSUES:")

    cursor.execute("""
        SELECT COUNT(*) FROM project_milestones
        WHERE planned_date IS NULL
    """)
    null_dates = cursor.fetchone()[0]
    if null_dates > 0:
        print(f"  Milestones without planned_date: {null_dates}")

    cursor.execute("""
        SELECT COUNT(*) FROM rfis WHERE status = 'open'
    """)
    open_rfis = cursor.fetchone()[0]
    print(f"  Open RFIs: {open_rfis}")

    cursor.execute("""
        SELECT COUNT(*) FROM invoices
        WHERE (paid IS NULL OR paid = 0)
        AND invoice_date < date('now', '-30 days')
    """)
    overdue = cursor.fetchone()[0]
    print(f"  Overdue invoices (>30 days): {overdue}")

    # Transcript coverage
    print("\n🎤 TRANSCRIPT COVERAGE:")
    cursor.execute("""
        SELECT
            COUNT(DISTINCT detected_project_code) as projects_with_transcripts,
            (SELECT COUNT(DISTINCT project_code) FROM projects) as total_projects
        FROM meeting_transcripts
        WHERE detected_project_code IS NOT NULL
    """)
    row = cursor.fetchone()
    print(f"  Projects with transcripts: {row[0]} / {row[1]}")

    conn.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    run_report()
```

**Run weekly:**
```bash
python scripts/analysis/data_quality_report.py
```

---

### P2: Set Up Email Addresses (Documentation)

**New emails to create:**
1. `rfi@bensley.com` - For RFI tracking (forward-only, not historical)
2. `finance@bensley.com` - For invoice/payment emails

**Document in:** `docs/guides/EMAIL_SETUP.md`

```markdown
# Email Setup Guide

## New Email Addresses

### rfi@bensley.com
- Purpose: Receive RFI notifications from clients/contractors
- Forward all RFIs here for automatic tracking
- System will auto-detect project and create RFI records

### finance@bensley.com
- Purpose: Receive invoice/payment emails
- System will auto-link to projects and invoices
- Helps track payment confirmations

## IMAP Configuration
- Server: [your mail server]
- Port: 993 (SSL)
- Credentials: [stored in .env]

## Testing
1. Send test email to address
2. Run: `python -m backend.services.email_importer --run-once`
3. Check emails table for new entry
```

---

## Database Quick Reference

```bash
# Connect to database
sqlite3 database/bensley_master.db

# Useful commands
.tables                    # List all tables
.schema table_name         # Show table structure
.mode column              # Pretty print
.headers on               # Show column names
```

**Key tables:**
```sql
-- Emails with project links
SELECT e.email_id, e.subject, p.project_code
FROM emails e
JOIN email_project_links epl ON e.email_id = epl.email_id
JOIN projects p ON epl.project_id = p.project_id
LIMIT 5;

-- Meeting transcripts
SELECT id, audio_filename, detected_project_code, match_confidence
FROM meeting_transcripts;

-- RFIs
SELECT rfi_id, project_code, subject, status, date_due
FROM rfis;

-- Milestones
SELECT milestone_id, project_code, milestone_name, planned_date, status
FROM project_milestones
WHERE status != 'complete';
```

---

## Files You Own

```
voice_transcriber/
├── transcriber.py          # Main transcription script
├── config.py              # Configuration
└── processed_files.json   # Track processed files

scripts/
├── core/
│   ├── rfi_detector.py    # RFI detection from emails
│   └── smart_email_brain.py  # Email processing
├── analysis/
│   └── data_quality_report.py  # NEW
├── imports/
│   └── ... import scripts
└── maintenance/
    └── ... fix scripts

database/
├── bensley_master.db      # THE database
├── migrations/            # Schema changes
└── SCHEMA.md             # Documentation
```

---

## When You're Done

1. Confirm transcriber is running continuously
2. Report data quality metrics to team
3. Document any data issues found
4. Create tickets for manual data entry (if needed)

---

## Do NOT

- Modify API code (Agent 1's job)
- Modify frontend (Agent 2's job)
- Deploy anything (Agent 3's job)
- Add AI features (Agent 5's job)

---

**Estimated Time:** 6-8 hours total
**Start:** Can begin immediately (parallel with all agents)
**Checkpoint:** After data quality report shows no critical issues
**Ongoing:** Run transcriber continuously, weekly quality reports
