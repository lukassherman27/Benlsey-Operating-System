# Data Cleanup Agent - Fix Critical Data Quality Issues

> Issues: #306, #307, #308 | Priority: P0 | Branch: `fix/data-quality-cleanup-306`

---

## CONTEXT

**BLOCKS EVERYTHING ELSE.** Can't build on broken data.

The system audit found critical data quality issues:
- **#306**: 168 orphaned project_team records → Team views broken
- **#307**: 47 duplicate invoice numbers ($12.7M) → Finance reports unreliable
- **#308**: 33 orphaned invoice_aging records (50%) → Aging dashboard wrong

This is the FIRST priority before any new features.

---

## PHASE 1: UNDERSTAND (Research First)

Before writing ANY code, understand the scope:

### Required Research
```bash
# Check orphaned project_team (#306)
sqlite3 database/bensley_master.db "
SELECT COUNT(*) as orphans
FROM project_team pt
LEFT JOIN projects p ON pt.project_id = p.project_id
WHERE p.project_id IS NULL;"

# Check duplicate invoices (#307)
sqlite3 database/bensley_master.db "
SELECT invoice_number, COUNT(*) as count, SUM(total_amount) as total
FROM invoices
GROUP BY invoice_number
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 10;"

# Check orphaned invoice_aging (#308)
sqlite3 database/bensley_master.db "
SELECT COUNT(*) as orphans
FROM invoice_aging ia
LEFT JOIN invoices i ON ia.invoice_id = i.invoice_id
WHERE i.invoice_id IS NULL;"

# Check FK enforcement status
sqlite3 database/bensley_master.db "PRAGMA foreign_keys;"
```

### Questions to Answer
1. Which projects have the most orphaned team records? Are they old/deleted?
2. For duplicate invoices - true duplicates or different invoices with same number?
3. What happens if we delete orphaned records? Any cascade effects?

### Files to Read
- `backend/services/project_service.py` - How project_team is managed
- `backend/services/invoice_service.py` - How invoices are created
- Database schema - FK constraints defined?

**STOP HERE** until you understand the current state.

---

## PHASE 2: THINK HARD (Planning)

### Design Decisions
1. **Delete or Archive?** Orphaned records - delete or move to archive table?
2. **Duplicate Resolution** For duplicate invoices, how to pick the "correct" one?
3. **FK Enforcement** Enable FKs now or wait for cleanup?

### Web Research
```
Search: "SQLite enable foreign keys migration strategy"
Search: "database data cleanup best practices orphaned records"
```

### Write Your Plan
1. First, BACKUP the database
2. Audit and categorize orphans
3. Create cleanup script with DRY RUN mode
4. Run in DRY RUN to see what would be deleted
5. Get human approval before actual delete
6. Enable FK enforcement for future protection

---

## PHASE 3: IMPLEMENT

### Step 1: Create Backup
```bash
cp database/bensley_master.db database/bensley_master_backup_$(date +%Y%m%d_%H%M%S).db
```

### Step 2: Create Cleanup Script
Create `scripts/core/data_quality_cleanup.py`:
- Accepts `--dry-run` flag (default: true)
- Logs all actions to console AND file
- Handles each issue separately
- Returns counts of what would be/was fixed

### Step 3: Handle Each Issue

**#306 - Orphaned project_team:**
```sql
DELETE FROM project_team
WHERE project_id NOT IN (SELECT project_id FROM projects);
```

**#307 - Duplicate invoices (keep lowest invoice_id):**
```sql
WITH dups AS (
  SELECT invoice_number, MIN(invoice_id) as keep_id
  FROM invoices GROUP BY invoice_number HAVING COUNT(*) > 1
)
DELETE FROM invoices
WHERE invoice_number IN (SELECT invoice_number FROM dups)
AND invoice_id NOT IN (SELECT keep_id FROM dups);
```

**#308 - Orphaned invoice_aging:**
```sql
DELETE FROM invoice_aging
WHERE invoice_id NOT IN (SELECT invoice_id FROM invoices);
```

### Step 4: Enable FK Enforcement
```python
# In database connection
connection.execute("PRAGMA foreign_keys = ON;")
```

### Files to Create/Modify
| File | Action | Purpose |
|------|--------|---------|
| `scripts/core/data_quality_cleanup.py` | Create | Main cleanup script |
| `backend/database/connection.py` | Modify | Add FK enforcement |

---

## PHASE 4: VERIFY

### Testing Checklist
- [ ] Backup created successfully
- [ ] Dry run shows expected counts
- [ ] After cleanup, zero orphans in each table
- [ ] FK enforcement enabled (`PRAGMA foreign_keys` = 1)

### Verification Commands
```bash
python scripts/core/data_quality_cleanup.py --dry-run

sqlite3 database/bensley_master.db "
SELECT 'orphaned_project_team' as issue, COUNT(*) FROM project_team pt
WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = pt.project_id)
UNION ALL
SELECT 'orphaned_invoice_aging', COUNT(*) FROM invoice_aging ia
WHERE NOT EXISTS (SELECT 1 FROM invoices i WHERE i.invoice_id = ia.invoice_id)
UNION ALL
SELECT 'duplicate_invoices', COUNT(*) - COUNT(DISTINCT invoice_number) FROM invoices;"
```

### Success Criteria
- 0 orphaned records in all three tables
- FK enforcement enabled
- Cleanup script documented for future use

---

## PHASE 5: COMPLETE

### Commit & Close Issues
```bash
git commit -m "fix(database): clean orphaned records and enable FK enforcement

- Remove 168 orphaned project_team records (#306)
- Dedupe 47 duplicate invoice numbers (#307)
- Remove 33 orphaned invoice_aging records (#308)
- Enable PRAGMA foreign_keys = ON

Fixes #306, #307, #308"

gh pr create --title "fix: Data quality cleanup (P0)" \
  --body "Fixes #306, #307, #308 - critical data quality issues blocking all other work"
```

---

## CONSTRAINTS

- **NEVER delete without backup**
- **NEVER run --execute without --dry-run first**
- **Document everything** - cleanup scripts are reusable

---

## RESOURCES

- `.claude/plans/system-architecture-ux.md` - Appendix E: Data Quality Issues
- `docs/ARCHITECTURE.md` - Database schema
