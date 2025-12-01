# MASTER MIGRATION PLAN: Database Consolidation

**Status:** Planning Phase
**Coordinator:** Master Planning Claude
**Goal:** Consolidate Desktop + OneDrive databases into single source of truth

---

## THE SITUATION

### Current State
We have **TWO databases** that diverged:

**1. Desktop Database** (MAIN PRODUCTION)
- Location: `/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db`
- Size: 80MB
- Last Modified: Nov 24, 2025 12:08pm
- Architecture: **90 tables, 192 indexes** (MOST COMPLETE)
- Data:
  - 3,194 emails
  - 138 projects
  - 114 proposals
  - **547 invoices** (MOST COMPLETE)

**2. OneDrive Database** (TEST/SUBSET)
- Location: `/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db`
- Size: 86MB
- Last Modified: Nov 24, 2025 6:23pm
- Architecture: **59 tables, 124 indexes** (SUBSET)
- Data:
  - 3,356 emails (162 MORE than Desktop)
  - 46 projects
  - 87 proposals
  - 253 invoices

### Why This Happened
- Desktop = Main production database with all features
- OneDrive = Subset database created for testing/recent work
- We've been accidentally working on OneDrive (via .env path)
- They diverged and now have different data

### Key Differences

**Desktop Has (that OneDrive doesn't):**
- 38 additional tables (proposal_tracker, project_fee_breakdown, audit_rules, etc.)
- 294 more invoices (CRITICAL financial data)
- 92 more projects
- 68 more indexes

**OneDrive Has (that Desktop doesn't):**
- 162 more emails (recent imports)
- `date_normalized` column in emails (CRITICAL schema fix)
- 7 newer tables (ai_observations, contract_phases, data_sources, etc.)
- Newer schema columns with provenance tracking

---

## THE DECISION

**USE DESKTOP AS MASTER** because:
1. Has 90 tables vs 59 (way more features)
2. Has 547 invoices vs 253 (CRITICAL financial data)
3. Has 138 projects vs 46 (3x more)
4. Architecture score: 40 vs 9

**MIGRATE FROM ONEDRIVE:**
1. 162 additional emails
2. Schema improvements (date_normalized, provenance columns)
3. 7 newer tables
4. Recent work/migrations

---

## MASTER PLAN: 8 PHASES

### PHASE 1: BACKUP & SAFETY
**Objective:** Ensure we can rollback if anything goes wrong

**Tasks:**
1. Create timestamped backup of Desktop database
2. Create timestamped backup of OneDrive database
3. Create backup of .env file
4. Verify backups are readable
5. Document current .env DATABASE_PATH setting

**Output:** `/backups/YYYY-MM-DD-HH-MM/` folder with all backups

**Assignable to:** Implementation Claude
**Estimated tokens:** ~500

---

### PHASE 2: SCHEMA ANALYSIS
**Objective:** Document exact schema differences for migration

**Tasks:**
1. Export complete schema of Desktop database (all CREATE TABLE statements)
2. Export complete schema of OneDrive database
3. Generate diff of schemas (table by table, column by column)
4. Identify:
   - Columns in OneDrive that Desktop needs
   - Tables in OneDrive that Desktop needs
   - Indexes in OneDrive that Desktop needs
5. Create SQL migration script to add missing schemas to Desktop

**Output:**
- `schema_diff_report.txt`
- `migrate_schema_desktop.sql`

**Assignable to:** Implementation Claude
**Estimated tokens:** ~1000

---

### PHASE 3: DATA QUALITY AUDIT
**Objective:** Understand what data is unique to each database

**Tasks:**
1. Find emails in OneDrive NOT in Desktop (by message_id)
2. Find emails in Desktop NOT in OneDrive
3. Compare invoice data quality:
   - Which invoices are in both?
   - Which are only in Desktop?
   - Which are only in OneDrive?
4. Compare projects data:
   - Identify overlaps by project_code
   - Flag any data conflicts
5. Generate detailed audit report

**Output:**
- `data_audit_report.txt`
- List of message_ids to migrate
- List of invoice_ids to migrate (if any)

**Assignable to:** Implementation Claude
**Estimated tokens:** ~1500

---

### PHASE 4: SCHEMA MIGRATION
**Objective:** Apply OneDrive's schema improvements to Desktop

**Tasks:**
1. Run `migrate_schema_desktop.sql` on Desktop database
2. Add `date_normalized` column to Desktop emails table
3. Add provenance columns (source_type, source_reference, created_by, etc.)
4. Add the 7 new tables from OneDrive
5. Populate date_normalized from existing date column
6. Create indexes on new columns
7. Verify schema migration successful

**Output:** Desktop database with updated schema

**Assignable to:** Implementation Claude
**Estimated tokens:** ~800

---

### PHASE 5: DATA MIGRATION
**Objective:** Move unique data from OneDrive → Desktop

**Tasks:**
1. Migrate 162 unique emails from OneDrive → Desktop
   - Use message_id to avoid duplicates
   - Preserve all metadata
2. Migrate any unique contract_phases records
3. Migrate any unique ai_observations records
4. Migrate any unique data_sources records
5. Verify no data loss
6. Verify no duplicates created

**Output:** Desktop database with complete data

**Assignable to:** Implementation Claude
**Estimated tokens:** ~1000

---

### PHASE 6: COPY TO ONEDRIVE LOCATION
**Objective:** Put the consolidated Desktop database in the OneDrive location (where .env points)

**Tasks:**
1. Verify Desktop database is complete and correct
2. Archive the old OneDrive database
3. Copy consolidated Desktop database → OneDrive location
4. Verify copy successful (file size, table counts)
5. Test database opens correctly at new location

**Output:** Consolidated database at OneDrive location

**Assignable to:** Implementation Claude
**Estimated tokens:** ~500

---

### PHASE 7: VALIDATION
**Objective:** Verify the migration was successful

**Tasks:**
1. Count all tables in consolidated database (should be 90+ tables)
2. Count all emails (should be 3,194 + 162 = 3,356)
3. Count all invoices (should be 547)
4. Count all projects (should be 138)
5. Verify date_normalized column exists and is populated
6. Verify all new tables exist
7. Run sample queries to ensure data integrity
8. Compare with Bill's Excel files (invoice mappings)

**Output:** Validation report confirming success

**Assignable to:** Implementation Claude
**Estimated tokens:** ~800

---

### PHASE 8: CLEANUP & DOCUMENTATION
**Objective:** Clean up old databases and document the new structure

**Tasks:**
1. Archive Desktop database (original location)
2. Update .env file if needed
3. Update README/documentation with:
   - New database location
   - Migration date
   - What was migrated
4. Create CURRENT_DATABASE_STATE.md documentation
5. Delete any temporary migration files
6. Test that all scripts still work with new database

**Output:** Clean, documented, consolidated system

**Assignable to:** Implementation Claude
**Estimated tokens:** ~500

---

## RISK ASSESSMENT

### HIGH RISK
- **Data loss during migration** → Mitigated by Phase 1 backups
- **Schema conflicts** → Mitigated by Phase 2 detailed analysis
- **Duplicate data** → Mitigated by using unique keys (message_id, invoice_id)

### MEDIUM RISK
- **Scripts pointing to wrong database** → Mitigated by .env consistency
- **Performance degradation** → Mitigated by keeping all indexes

### LOW RISK
- **Disk space** → Both databases are <100MB
- **Downtime** → Can run migration offline

---

## COORDINATION PROTOCOL

### For Each Phase:
1. **Master Claude (me)** reviews the phase requirements
2. **Implementation Claude** receives:
   - Phase objectives
   - Specific tasks list
   - Expected outputs
   - File paths
3. **Implementation Claude** executes and reports back
4. **Master Claude** validates outputs before next phase
5. If issues found, Implementation Claude fixes before proceeding

### Communication Format:
```
PHASE: [number]
STATUS: [in_progress|completed|blocked]
OUTPUTS: [list of files created]
ISSUES: [any problems encountered]
READY_FOR_NEXT_PHASE: [yes|no]
```

---

## CURRENT STATUS

- [x] Phase 0: Analysis & Planning (COMPLETE)
- [ ] Phase 1: Backup & Safety (READY TO START)
- [ ] Phase 2: Schema Analysis
- [ ] Phase 3: Data Quality Audit
- [ ] Phase 4: Schema Migration
- [ ] Phase 5: Data Migration
- [ ] Phase 6: Copy to OneDrive Location
- [ ] Phase 7: Validation
- [ ] Phase 8: Cleanup & Documentation

---

## NEXT ACTION

**Ready to start Phase 1 when you give the go-ahead.**

Would you like me to:
1. Start Phase 1 with an Implementation Claude now?
2. Review/modify the plan first?
3. Add additional validation steps?
