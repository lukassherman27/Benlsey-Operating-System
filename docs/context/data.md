# Data Context - Database & Data Quality Patterns

**Last Updated:** 2025-12-01
**Updated By:** Organizer Agent

---

## Database Overview

**Location:** `database/bensley_master.db`
**Size:** ~107 MB
**Tables:** 115

### Core Tables

| Table | Records | Purpose |
|-------|---------|---------|
| emails | 3,356 | All imported emails |
| proposals | 87 | All proposals (pre-contract) |
| projects | 62 | Active projects (post-contract) |
| contacts | 578 | All contacts from emails/meetings |
| meeting_transcripts | 39 | AI-generated meeting transcripts |

### Link Tables

| Table | Records | Status | Notes |
|-------|---------|--------|-------|
| email_proposal_links | 660 | REBUILT | 100% FK valid after Dec 1 rebuild |
| email_project_links | 918 | NEEDS REBUILD | 98.9% orphaned |
| project_contact_links | ~108 | OK | Needs expansion |
| document_proposal_links | ? | Untested | |

---

## Data Quality Patterns (Learned: 2025-12-01)

### FK Mismatch Prevention

Link tables (email_proposal_links, email_project_links) can become orphaned if populated with IDs that don't match target tables.

**Root Cause Found (Dec 1, 2025):**
- `email_proposal_links.proposal_id` range was 1-87
- `proposals.proposal_id` range was 177-263
- **Zero overlap** = 100% orphaned links (4,872 junk records)

**Prevention Rules:**
1. Always rebuild links by `project_code`, not by ID
2. Add FK constraints after rebuild
3. Run `PRAGMA foreign_key_check` after any bulk operation
4. Keep old tables as backup until verified

### Project Code Formats

Project codes appear in two formats across the database:

| Format | Example | Tables Using |
|--------|---------|--------------|
| Full (with year) | `25 BK-087` | proposals, projects |
| Short (no year) | `BK-087` | Some legacy links |

**Solution:** Use LIKE patterns that handle both when matching:

```sql
-- Matches both "25 BK-087" and "BK-087"
WHERE e.subject LIKE '%BK-087%'

-- Or extract just the BK-XXX portion
WHERE e.subject LIKE '%' || SUBSTR(p.project_code, -7) || '%'
```

---

## Link Rebuild Methodology

When link tables need rebuilding, follow this process:

### Step 1: Create Staging Table

```sql
CREATE TABLE email_proposal_links_new (
    email_id INTEGER NOT NULL,
    proposal_id INTEGER NOT NULL,
    link_type TEXT DEFAULT 'keyword_match',
    confidence_score REAL DEFAULT 0.85,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (email_id, proposal_id),
    FOREIGN KEY (email_id) REFERENCES emails(email_id),
    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
);
```

### Step 2: Populate by Code Matching

Match by subject first (highest confidence), then body text:

```sql
-- Subject matching
INSERT INTO email_proposal_links_new (email_id, proposal_id, confidence_score)
SELECT DISTINCT e.email_id, p.proposal_id, 0.90
FROM emails e, proposals p
WHERE e.subject LIKE '%' || p.project_code || '%';
```

### Step 3: Verify Sample Quality

Manually check 5-10 random links:

```sql
SELECT e.subject, p.project_code, epl.confidence_score
FROM email_proposal_links_new epl
JOIN emails e ON epl.email_id = e.email_id
JOIN proposals p ON epl.proposal_id = p.proposal_id
ORDER BY RANDOM() LIMIT 10;
```

### Step 4: Swap Tables

```sql
ALTER TABLE email_proposal_links RENAME TO email_proposal_links_old;
ALTER TABLE email_proposal_links_new RENAME TO email_proposal_links;
```

### Step 5: Verify FK Integrity

```sql
PRAGMA foreign_key_check(email_proposal_links);
-- Should return empty (no violations)
```

### Step 6: Recreate Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_epl_email ON email_proposal_links(email_id);
CREATE INDEX IF NOT EXISTS idx_epl_proposal ON email_proposal_links(proposal_id);
```

### Step 7: Cleanup (After 7 Days)

```sql
DROP TABLE email_proposal_links_old;
```

---

## FK Constraints

### Current State

FK constraints are **defined** in table schemas but **not enforced** by default:

```sql
PRAGMA foreign_keys;  -- Returns 0 (disabled)
```

### To Enable

Add to every database connection:

```python
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON")
```

### Migration Ready

`database/migrations/048_enforce_fk_constraints.sql` contains:
- Validation queries
- Cleanup SQL for orphans
- Instructions for enabling FK enforcement

**Status:** Pending - run after all link tables rebuilt

---

## Data Quality Metrics (Dec 1, 2025 Baseline)

| Metric | Value | Status |
|--------|-------|--------|
| Emails linked to proposals | 371 (11%) | After rebuild |
| Proposals with email links | 24 (28%) | After rebuild |
| Contacts with names | 292 (50.5%) | Needs cleanup |
| Transcripts linked | 1 (2.6%) | Needs linking |
| email_project_links valid | 10 (1.1%) | NEEDS REBUILD |

---

## Common Queries

### Check Link Table Health

```sql
-- Count orphaned proposal links
SELECT COUNT(*) as orphans
FROM email_proposal_links epl
WHERE NOT EXISTS (
    SELECT 1 FROM proposals p WHERE p.proposal_id = epl.proposal_id
);
```

### Find Unlinked Proposals

```sql
SELECT p.project_code, p.project_name
FROM proposals p
WHERE NOT EXISTS (
    SELECT 1 FROM email_proposal_links epl WHERE epl.proposal_id = p.proposal_id
);
```

### Sample Link Quality

```sql
SELECT
    e.subject,
    p.project_code,
    epl.confidence_score,
    epl.link_type
FROM email_proposal_links epl
JOIN emails e ON epl.email_id = e.email_id
JOIN proposals p ON epl.proposal_id = p.proposal_id
ORDER BY RANDOM() LIMIT 10;
```

---

## Contact→Project Linking Pipeline

**Added:** 2025-12-01
**Script:** `scripts/core/contact_project_linker.py`
**Handler:** `backend/services/suggestion_handlers/contact_link_handler.py`

### The Intelligence Loop

```
Email → Project/Proposal (via email_*_links)
   ↓
Email → Contact (via sender_email → contacts.email)
   ↓
Contact → Project/Proposal (via project_contact_links)
```

This enables auto-categorization of future emails based on known contact associations.

### Pipeline Flow

1. **Discover links** - Analyze `email_project_links` and `email_proposal_links`
2. **Extract contacts** - Match email senders to existing contacts
3. **Create suggestions** - Generate `contact_link` suggestions for human review
4. **Apply links** - Handler creates `project_contact_links` records when approved

### Running the Pipeline

```bash
# Dry run - show what would be created
python scripts/core/contact_project_linker.py --dry-run

# Create suggestions (requires at least 1 email)
python scripts/core/contact_project_linker.py

# Only suggest if contact sent 2+ emails
python scripts/core/contact_project_linker.py --min-emails 2
```

### Suggestion Confidence Scoring

| Email Count | Confidence | Priority |
|-------------|------------|----------|
| 10+ emails | 0.95 | high |
| 5-9 emails | 0.85 | high |
| 3-4 emails | 0.75 | medium |
| 2 emails | 0.65 | low |
| 1 email | 0.55 | low |

### Database Tables

```sql
-- Link table (already exists)
project_contact_links (
    link_id, contact_id, project_id, proposal_id,
    role, email_count, confidence_score, source
)

-- Suggestions go to ai_suggestions with type = 'contact_link'
```

### Current Status (Dec 1, 2025)

| Metric | Value |
|--------|-------|
| Total contacts | 578 |
| Contacts with project links | 79 (14%) |
| `contact_link` suggestions pending | 89 |
| `new_contact` suggestions pending | 2 |

---

## Lessons Learned

1. **Always verify FK integrity** before trusting link counts
2. **ID ranges matter** - check MIN/MAX on both sides of a FK relationship
3. **Code matching > ID matching** - project codes are stable, IDs can drift
4. **Staging tables** - never modify production link tables directly
5. **Keep backups** - 7-day retention before dropping old tables
6. **Contact linking via suggestions** - Never auto-link, always create suggestions for human review
