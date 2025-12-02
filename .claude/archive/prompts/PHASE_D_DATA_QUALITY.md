# PHASE D: Data Quality Agent Prompt

**Phase:** D - Data Quality Improvement
**Role:** Data Pipeline Agent + Human Review
**Goal:** Clean and verify data using the suggestions workflow from Phase C

---

## Context Files to Read First

1. `docs/planning/TIER1_PHASED_PLAN.md` - Your phase definition
2. `.claude/LIVE_STATE.md` - Phase B baseline metrics, Phase C status
3. `scripts/core/transcript_linker.py` - Existing transcript linking logic
4. `backend/services/ai_learning_service.py` - Suggestion application logic

---

## Prerequisites Check

Before starting:
1. Phase C complete (suggestions workflow working)
2. Test the workflow:
```bash
# Create a test suggestion
curl -X POST http://localhost:8000/api/suggestions \
  -H "Content-Type: application/json" \
  -d '{"suggestion_type": "test", "title": "Test suggestion"}'

# Verify it appears in UI at /admin/suggestions
```

---

## Your Tasks

### Task 1: Process Email→Proposal Suggestions

**Goal:** Review and approve/reject existing email-proposal link suggestions.

```bash
# Check pending suggestions
curl -s "http://localhost:8000/api/suggestions?status=pending&type=email_proposal_link" | jq 'length'
```

**For high-confidence (≥0.85):**
- Use bulk approve feature from Phase C
- Document how many approved

**For lower confidence:**
- Human must review each one in UI
- Look at: email subject, sender, proposal name
- Approve only if clearly related

### Task 2: Process Email→Project Suggestions

Same process as Task 1, but for `email_project_link` type.

### Task 3: Link Transcripts via Suggestions ONLY

**CRITICAL: Never auto-link transcripts. All must go through suggestions.**

```bash
# Run transcript linker in dry-run mode first
cd scripts/core
python transcript_linker.py --dry-run

# If looks good, create suggestions
python transcript_linker.py

# Check suggestions created
curl -s "http://localhost:8000/api/suggestions?status=pending&type=transcript_link" | jq 'length'
```

**Human review process:**
1. Go to /admin/suggestions
2. Filter by type: transcript_link
3. For each suggestion:
   - Read transcript excerpt
   - Verify project/proposal match
   - Approve or reject with reason

### Task 4: Contact Extraction & Enrichment

**Goal:** Extract new contacts from emails, create suggestions for verification.

```python
# Create script: scripts/core/contact_extractor.py

# Logic:
# 1. Scan emails for email addresses not in contacts table
# 2. Extract name from "From: Name <email>" format
# 3. Try to extract company from email domain
# 4. Create suggestion for EACH new contact
# 5. Human reviews and approves individually

# NEVER bulk-approve contacts - names matter!
```

**Create suggestions like:**
```json
{
  "suggestion_type": "contact_enrichment",
  "title": "Add contact: John Smith",
  "description": "Found in email from john.smith@acme.com",
  "suggested_data": {
    "name": "John Smith",
    "email": "john.smith@acme.com",
    "company": "ACME Corp",
    "source_email_id": 1234
  }
}
```

### Task 5: Transcript Grouping

**Goal:** Group transcripts by meeting, verify project associations.

```sql
-- Find transcripts that might be from same meeting
SELECT
    meeting_date,
    COUNT(*) as transcript_count,
    GROUP_CONCAT(id) as transcript_ids
FROM meeting_transcripts
WHERE meeting_date IS NOT NULL
GROUP BY meeting_date
HAVING transcript_count > 1;
```

**Create suggestions to group related transcripts.**

### Task 6: Backfill Missing Data

**Goal:** Fill null contact names, company fields where determinable.

```sql
-- Find contacts with missing data that can be inferred
SELECT c.id, c.email, c.name, c.company,
       e.from_name, e.from_address
FROM contacts c
JOIN emails e ON e.from_address = c.email
WHERE (c.name IS NULL OR c.name = '')
  AND e.from_name IS NOT NULL AND e.from_name != ''
LIMIT 50;
```

**Create suggestions for each backfill - do NOT auto-update.**

---

## Critical Rules

1. **NEVER auto-link transcripts** - Always via suggestions, human approves
2. **NEVER bulk-approve contacts** - Each contact reviewed individually
3. **Always create backup before bulk operations**
4. **Track everything** - Every change via suggestion system

---

## Metrics to Track

Update LIVE_STATE.md with:

```markdown
### Phase D Metrics

| Metric | Baseline (Phase B) | Current | Target |
|--------|-------------------|---------|--------|
| Email→Proposal accuracy | X% | Y% | 95%+ |
| Email→Project coverage | X% | Y% | 80%+ |
| Transcripts linked | X/Y | Z/Y | 100% |
| Contacts verified | X/Y | Z/Y | 100% |

### Suggestions Processed
- Total processed: X
- Approved: Y
- Rejected: Z
- Corrected: W
```

---

## Gate Criteria

Before declaring Phase D complete:

- [ ] All email→proposal suggestions processed
- [ ] All email→project suggestions processed
- [ ] All transcript link suggestions reviewed (100% of 39)
- [ ] Contact extraction run, suggestions created
- [ ] Contact suggestions reviewed (no bulk approve)
- [ ] Email accuracy ≥90% (re-sample to verify)
- [ ] Transcripts 100% linked (human verified)
- [ ] No critical null fields in contacts

---

## DO NOT Do

- Do NOT auto-approve anything
- Do NOT bypass the suggestions workflow
- Do NOT bulk-approve contacts
- Do NOT link transcripts directly (use suggestions)
- Do NOT skip human verification

---

## Handoff

When complete, update `.claude/LIVE_STATE.md`:

```markdown
## Phase D Status: COMPLETE

### Final Metrics
- Email→Proposal accuracy: X% (verified sample of 100)
- Email→Project coverage: X%
- Transcripts linked: 39/39 (100%)
- Contacts verified: X/Y

### Suggestions Summary
- Total processed: X
- Approved: Y
- Rejected: Z
- Corrected: W

### Data Quality Verdict
[PASS/FAIL] - Ready for Phase E

### Ready for Phase E
Phase E (Reports) can now generate reports from clean data.
```
