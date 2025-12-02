# PHASE B: Data Audit Agent Prompt

**Phase:** B - Data Audit & Baseline
**Role:** Data Audit Agent
**Goal:** Establish baseline metrics for data quality - READ ONLY, no modifications

---

## Context Files to Read First

1. `docs/planning/TIER1_PHASED_PLAN.md` - Your phase definition
2. `docs/context/database.md` - Schema reference
3. `.claude/LIVE_STATE.md` - Current system state

---

## Prerequisites Check

Before starting, verify Phase A gates passed:
```bash
curl -s http://localhost:8000/api/health
# Must return 200

grep -r "Desktop.*bensley" scripts/
# Must return empty
```

If these fail, STOP and report - Phase A is not complete.

---

## Your Tasks

### Task 1: Email→Proposal Link Audit

**Method:** Random sample of 100 email-proposal links, manually verify accuracy.

```sql
-- Get random sample of 100 email-proposal links
SELECT
    e.id as email_id,
    e.subject,
    e.from_address,
    e.sent_date,
    epl.proposal_id,
    epl.confidence_score,
    epl.match_reason,
    p.project_code,
    p.project_name
FROM email_proposal_links epl
JOIN emails e ON epl.email_id = e.id
JOIN proposals p ON epl.proposal_id = p.proposal_id
ORDER BY RANDOM()
LIMIT 100;
```

**Verification criteria:**
- Does the email content actually relate to the proposal?
- Is the project code mentioned in the email?
- Is the client/company name relevant?

**Document:** X% correct, Y% wrong, Z% uncertain

### Task 2: Email→Project Link Audit

**Method:** Random sample of 50 email-project links.

```sql
SELECT
    e.id as email_id,
    e.subject,
    e.from_address,
    eprj.project_id,
    eprj.confidence_score,
    prj.project_code,
    prj.project_name
FROM email_project_links eprj
JOIN emails e ON eprj.email_id = e.id
JOIN projects prj ON eprj.project_id = prj.id
ORDER BY RANDOM()
LIMIT 50;
```

### Task 3: Contact Data Quality Audit

```sql
-- Count nulls and issues
SELECT
    COUNT(*) as total_contacts,
    SUM(CASE WHEN name IS NULL OR name = '' THEN 1 ELSE 0 END) as null_names,
    SUM(CASE WHEN email IS NULL OR email = '' THEN 1 ELSE 0 END) as null_emails,
    SUM(CASE WHEN company IS NULL OR company = '' THEN 1 ELSE 0 END) as null_companies
FROM contacts;

-- Find duplicate emails
SELECT email, COUNT(*) as cnt
FROM contacts
WHERE email IS NOT NULL AND email != ''
GROUP BY email
HAVING cnt > 1;

-- Find malformed emails
SELECT id, name, email
FROM contacts
WHERE email NOT LIKE '%@%.%'
  AND email IS NOT NULL AND email != '';
```

### Task 4: Transcript Data Audit

```sql
-- Inventory all transcripts
SELECT
    id,
    audio_filename,
    meeting_date,
    proposal_id,
    project_id,
    LENGTH(transcript) as transcript_length,
    CASE WHEN summary IS NOT NULL THEN 'Yes' ELSE 'No' END as has_summary
FROM meeting_transcripts
ORDER BY meeting_date DESC;

-- Count linked vs unlinked
SELECT
    SUM(CASE WHEN proposal_id IS NOT NULL OR project_id IS NOT NULL THEN 1 ELSE 0 END) as linked,
    SUM(CASE WHEN proposal_id IS NULL AND project_id IS NULL THEN 1 ELSE 0 END) as unlinked
FROM meeting_transcripts;
```

### Task 5: Create DB Backup (Rollback Point)

```bash
# Create dated backup before any data changes
cp database/bensley_master.db database/bensley_master.db.backup_$(date +%Y%m%d)

# Verify backup
ls -la database/*.backup*
```

### Task 6: Document Baseline Metrics

Update `.claude/LIVE_STATE.md` with findings:

```markdown
## Phase B Data Audit Results

**Date:** YYYY-MM-DD
**Auditor:** Data Audit Agent

### Email→Proposal Links
- Total links: X
- Sample size: 100
- Accuracy: X% correct, Y% wrong, Z% uncertain
- VERDICT: [PASS/NEEDS_REBUILD] (Pass if >70%)

### Email→Project Links
- Total links: X
- Sample size: 50
- Accuracy: X%
- VERDICT: [PASS/NEEDS_REBUILD]

### Contact Quality
- Total contacts: X
- Null names: X (Y%)
- Null emails: X (Y%)
- Null companies: X (Y%)
- Duplicates: X pairs
- Malformed emails: X
- VERDICT: [PASS/NEEDS_CLEANUP]

### Transcripts
- Total: X
- Linked: X (Y%)
- Unlinked: X (Y%)
- With summaries: X
- VERDICT: [PASS/NEEDS_LINKING]

### Rollback Point
- Backup created: database/bensley_master.db.backup_YYYYMMDD
- Size: X MB
```

---

## Sampling Rules

- Email audits: Random sample of 100 (statistically significant for ~3000 emails)
- If accuracy <70%, flag for full re-processing in Phase D
- Document sampling methodology for reproducibility
- Use RANDOM() for true random selection

---

## Rollback Rules

- Always create backup before any bulk operations
- If audit reveals >50% bad data in a table, plan for full rebuild in Phase D
- Keep backup for at least 7 days

---

## Gate Criteria (You Must Verify)

Before declaring Phase B complete:

- [ ] Email→Proposal sample audited (100 links)
- [ ] Email→Project sample audited (50 links)
- [ ] Contact quality report complete
- [ ] Transcript inventory complete
- [ ] Baseline metrics in LIVE_STATE.md
- [ ] DB backup created and verified

---

## CRITICAL RULES

- **READ ONLY** - Do not modify any data
- **Document everything** - Every finding goes in LIVE_STATE.md
- **Be honest** - If data quality is bad, say so
- **Random sampling** - No cherry-picking good examples

---

## Handoff

When complete, update `.claude/LIVE_STATE.md` with:

```markdown
## Phase B Status: COMPLETE

### Summary
- Email accuracy: X% (sample of 100)
- Contact issues: X records need cleanup
- Transcripts unlinked: X of Y

### Rollback Point
- Backup: database/bensley_master.db.backup_YYYYMMDD

### Ready for Phase C
Phase C (Feedback Infrastructure) can now begin.
```
