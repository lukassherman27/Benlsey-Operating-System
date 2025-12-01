# Agent 4: Data Pipeline

**Role:** Data processing, email linking, database operations
**Invoke:** "Act as the data pipeline agent" or reference this file
**Owner:** `scripts/`, `database/`, migrations

---

## What I Own

```
scripts/
├── core/
│   ├── email_linker.py        # Main email linking logic
│   ├── smart_email_brain.py   # AI email processor
│   ├── query_brain.py         # Natural language queries
│   └── health_check.py        # System health
├── imports/                   # Data import scripts
├── analysis/                  # Audit scripts
└── maintenance/               # Fix scripts

database/
├── bensley_master.db          # THE database (OneDrive)
├── migrations/                # SQL migrations
└── backups/                   # Backups
```

## What I DO NOT Touch

- `backend/` - Backend Agent's territory
- `frontend/` - Frontend Agent's territory
- Deployment configs

---

## Primary Mission: Email Linking

### Context & Constraints

- **Canonical DB:** `database/bensley_master.db` (OneDrive copy). Avoid older desktop DB.
- **Proposals = biz dev (unsigned), Projects = signed** - Keep outputs separated
- **Safe mode by default:** High-confidence → link; Medium/Low → suggestions

### High-Confidence Rules (Auto-Link to `email_project_links`)

1. **Explicit project code match** in subject/body
   - Patterns: `BK-xxx`, `[A-Z]{2}\s?-?\d{2,3}`, canonical patterns

2. **Exact contact-to-project match** via `project_contact_links`/`contacts`

3. **Thread inheritance:** Replies inherit project from root email using `message_id`/`in_reply_to`/`thread_id`

### Medium/Low Confidence (Create `ai_suggestions` with type='email_link')

- Domain → client → project matches
- Fuzzy project name hints
- Ambiguous/multi signals
- **Include rationale:** "domain match client X", "thread inherit", etc.

### Implementation Requirements

- **Idempotent:** No duplicates; safe to rerun; use upsert/unique checks
- **Schema awareness:** Join against `projects` (NOT `proposals`) for linking
- **Use existing signals:** `contacts`, `project_contact_links`, `clients`/domains, thread metadata
- **Batch processing:** Add temporary indexes on lookup fields if needed (subject, from_domain, contact_email)
- **Error handling:** Don't corrupt DB; dry-run/preview mode helpful
- **Logging:** Per-rule counts, confidence buckets, rationale in suggestions

---

## Email Linking Procedure

### Step 1: Baseline Counts
```sql
SELECT COUNT(*) FROM emails;
SELECT COUNT(*) FROM email_project_links;
SELECT COUNT(*) FROM ai_suggestions WHERE suggestion_type='email_link';
```

### Step 2: Run Linking Script
```bash
cd scripts/core
python email_linker.py --mode safe
# Or with dry-run first
python email_linker.py --dry-run
```

### Step 3: Checkpoints
- After +500 high-confidence links: Report progress
- After +1000 high-confidence links: Report progress
- After +2000 high-confidence links: Report progress

### Step 4: Final Verification
```sql
SELECT
  (SELECT COUNT(*) FROM email_project_links) as linked,
  (SELECT COUNT(*) FROM emails) as total,
  ROUND(100.0 * (SELECT COUNT(*) FROM email_project_links) / (SELECT COUNT(*) FROM emails), 1) as percentage;

SELECT COUNT(*) FROM ai_suggestions WHERE suggestion_type='email_link';
```

---

## Logging Format

```
[RULE] project_code_match: 847 emails linked (high confidence)
[RULE] contact_match: 234 emails linked (high confidence)
[RULE] thread_inherit: 156 emails linked (high confidence)
[SUGGESTION] domain_match: 312 suggestions created (medium confidence)
[SUGGESTION] fuzzy_name: 89 suggestions created (low confidence)
[SKIP] no_signals: 423 emails (reason: no project indicators)
[SKIP] personal: 156 emails (reason: personal/newsletter)
```

---

## Report Template

```markdown
# Email Linking Report - [DATE]

## Results
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Emails Linked | X | Y | +Z |
| Link % | X% | Y% | +Z% |
| Suggestions Created | X | Y | +Z |

## Rules Applied
| Rule | Links Created | Confidence |
|------|---------------|------------|
| project_code_match | X | High |
| contact_match | X | High |
| thread_inherit | X | High |
| domain_match | X (suggestions) | Medium |
| fuzzy_name | X (suggestions) | Low |

## Unlinked Analysis
| Reason | Count |
|--------|-------|
| No project indicators | X |
| Multiple ambiguous matches | X |
| Personal/spam emails | X |
| Missing contacts | X |

## Issues Found
- [Any problems encountered]

## Recommendations
- [Next steps]
```

---

## Database Health Checks

```sql
-- Check for orphan links
SELECT 'orphan_email_links' as issue, COUNT(*) as cnt
FROM email_project_links
WHERE email_id NOT IN (SELECT email_id FROM emails);

SELECT 'orphan_project_links' as issue, COUNT(*) as cnt
FROM email_project_links
WHERE project_id NOT IN (SELECT project_id FROM projects);

-- Check for duplicates
SELECT email_id, project_id, COUNT(*) as cnt
FROM email_project_links
GROUP BY email_id, project_id
HAVING cnt > 1;

-- Suggestion breakdown
SELECT suggestion_type, status, COUNT(*) as cnt
FROM ai_suggestions
GROUP BY suggestion_type, status;
```

---

## Other Data Tasks

### Import Data
```bash
python scripts/imports/import_[type].py --dry-run  # Preview
python scripts/imports/import_[type].py            # Execute
```

### Run Migrations
```bash
sqlite3 database/bensley_master.db < database/migrations/XXX_name.sql
```

### Voice Transcriber Status
```bash
cd voice_transcriber
python transcriber.py --status
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Check email linking % | `sqlite3 database/bensley_master.db "SELECT ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM emails), 1) FROM email_project_links;"` |
| Count suggestions | `sqlite3 database/bensley_master.db "SELECT suggestion_type, status, COUNT(*) FROM ai_suggestions GROUP BY suggestion_type, status;"` |
| Run linker (safe) | `python scripts/core/email_linker.py --mode safe` |
| Dry run | `python scripts/core/email_linker.py --dry-run` |
| Database connect | `sqlite3 database/bensley_master.db` |

---

## Files I Reference

| Purpose | File |
|---------|------|
| Email linker | `scripts/core/email_linker.py` |
| Smart brain | `scripts/core/smart_email_brain.py` |
| Database | `database/bensley_master.db` |
| Migrations | `database/migrations/` |
| Voice transcriber | `voice_transcriber/transcriber.py` |

---

## Current Sprint Task: Email Linking Sprint

**Goal:** Increase email linking from 15% to 80%+

**Current State:**
- Total emails: 3,356
- Currently linked: 521 (15.5%)
- Target: 2,685+ linked (80%)
- Gap: 2,164 emails

**Approach:**
1. Audit current `email_linker.py` logic
2. Add/enhance matching rules
3. Process unlinked emails in batches
4. Create suggestions for uncertain matches
5. Report results

**Deliverables:**
1. Starting count: 521 linked
2. Ending count: ???
3. % coverage: ???
4. Suggestions created (count, confidence distribution)
5. Rules added/improved
6. Unlinked reasons
