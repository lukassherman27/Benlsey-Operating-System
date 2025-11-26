# Database Usage Guide

## Master Database Location

**✅ USE THIS:** `database/bensley_master.db`
- Located in OneDrive working directory
- Synced automatically
- All current data (2024-2025)
- 66 tables, ~90MB

**❌ DON'T USE:** `~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db`
- Archived historical data only
- Not updated
- DO NOT write to this database

---

## How to Access Database in Your Scripts

### Python Scripts

```python
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()

# ✅ CORRECT - Uses environment variable
db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
conn = sqlite3.connect(db_path)

# ❌ WRONG - Hardcoded path
conn = sqlite3.connect('~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db')
```

### Environment Variable

In `.env` file:
```bash
DATABASE_PATH=database/bensley_master.db
```

### Backend Services

Backend services automatically use the database via `DATABASE_PATH`:
```python
# backend/services/base_service.py
db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
```

---

## Database Contents

### Tables (66 total)

**Core Data:**
- `proposals` - 87 proposals with contact info
- `projects` - 51 active projects
- `invoices` - 253+ current invoices
- `emails` - 3,356 emails
- `email_proposal_links` - Email categorization

**Features:**
- `project_fee_breakdown` - 372 phase fee entries
- `invoice_aging` - 101 aging calculations
- `proposal_tracker` - 37 proposal tracking records
- `contacts` - 465 contact records
- `email_attachments` - 1,179 attachments tracked
- `team_members` - 98 team members
- `schedule_entries` - 1,120 schedule items

---

## Common Operations

### Query Projects
```python
import sqlite3
conn = sqlite3.connect('database/bensley_master.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT project_code, project_title, total_fee_usd
    FROM projects
    WHERE status = 'Active'
    ORDER BY project_code
""")

for row in cursor.fetchall():
    print(f"{row['project_code']}: {row['project_title']}")
```

### Get Project Fee Breakdown
```python
cursor.execute("""
    SELECT phase, phase_fee_usd, discipline
    FROM project_fee_breakdown
    WHERE project_code = ?
    ORDER BY phase
""", ('24 BK-074',))

for phase in cursor.fetchall():
    print(f"{phase['phase']} ({phase['discipline']}): ${phase['phase_fee_usd']:,.0f}")
```

### Get Outstanding Invoices
```python
cursor.execute("""
    SELECT
        invoice_number,
        invoice_date,
        invoice_amount - COALESCE(payment_amount, 0) as unpaid,
        project_code
    FROM invoices
    WHERE status = 'outstanding'
    ORDER BY invoice_date
""")
```

---

## Backups

### Location
All backups stored in: `database/backups/`

### Naming Convention
```
bensley_master_pre_[operation]_YYYYMMDD_HHMMSS.db
```

Examples:
- `bensley_master_pre_import_20251124_190604.db`
- `bensley_master_pre_critical_20251124_191049.db`

### Create Backup
```bash
cp database/bensley_master.db "database/backups/bensley_master_$(date +%Y%m%d_%H%M%S).db"
```

### Restore from Backup
```bash
cp database/backups/[backup_name].db database/bensley_master.db
```

---

## Migration History

**Nov 24, 2025:** Consolidated Desktop + OneDrive databases
- Migrated 5 projects ($8.5M)
- Migrated 372 fee breakdowns
- Migrated 6 critical tables (3,000 rows)
- See `DATABASE_MIGRATION_SUMMARY.md` for details

---

## Database Schema

### Key Relationships

```
proposals (87)
    ↓
projects (51) ← Links via project_code
    ↓
├─ invoices (253+) ← Links via project_id
├─ project_fee_breakdown (372) ← Links via project_code
└─ email_proposal_links ← Links via proposal_id

emails (3,356)
    ↓
└─ email_proposal_links (794) ← Links emails to proposals
```

### Important Columns

**projects:**
- `project_id` (INTEGER) - Primary key
- `project_code` (TEXT) - e.g., "24 BK-074"
- `project_title` (TEXT)
- `status` (TEXT) - Active, Proposal, Archived
- `total_fee_usd` (REAL)

**invoices:**
- `invoice_id` (INTEGER) - Primary key
- `project_id` (INTEGER) - FK to projects
- `invoice_number` (TEXT) - e.g., "I25-082"
- `invoice_amount` (REAL)
- `payment_amount` (REAL)
- `status` (TEXT) - paid, outstanding

**project_fee_breakdown:**
- `project_code` (TEXT) - e.g., "24 BK-074"
- `phase` (TEXT) - Mobilization, Concept Design, etc.
- `discipline` (TEXT) - Landscape, Architectural, Interior
- `phase_fee_usd` (REAL)

---

## Troubleshooting

### Problem: Script can't find database
**Solution:** Check DATABASE_PATH in .env points to `database/bensley_master.db`

### Problem: Empty query results
**Solution:** Verify you're querying the OneDrive database, not Desktop

### Problem: Duplicate data
**Solution:** Check you're not running scripts against Desktop database

### Problem: Old data showing
**Solution:** Make sure DATABASE_PATH is set correctly in .env

---

## Best Practices

✅ **DO:**
- Always use `os.getenv('DATABASE_PATH')`
- Create backup before major operations
- Use transactions for multiple writes
- Close connections when done
- Document schema changes

❌ **DON'T:**
- Hardcode database paths
- Use Desktop database for new work
- Make schema changes without backups
- Leave connections open
- Import data without validation

---

## Frontend API Access

Frontend connects via Backend API:
```
Frontend (Next.js)
    ↓ HTTP
Backend API (FastAPI, port 8000)
    ↓ SQLite
database/bensley_master.db
```

**Example API Endpoint:**
```
GET /api/projects/24%20BK-074/fee-breakdown
→ Returns fee breakdown from project_fee_breakdown table
```

---

## Support

**Issues with database:**
1. Check `DATABASE_PATH` in .env
2. Verify file exists: `ls -lh database/bensley_master.db`
3. Check backups: `ls database/backups/`
4. Reference `DATABASE_MIGRATION_SUMMARY.md`

**Questions about migration:**
- See `DATABASE_MIGRATION_SUMMARY.md`
- Check git history for migration scripts
- Review `complete_audit_report.txt`

---

*Last Updated: November 24, 2025*
*Database consolidated and documented*
