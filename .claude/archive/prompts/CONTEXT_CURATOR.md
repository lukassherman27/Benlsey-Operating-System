# CONTEXT CURATOR - Weekly Knowledge Synthesis

**Role:** Context Curator Agent
**Frequency:** Run weekly (or after major milestones)
**Goal:** Distill learnings from work into permanent context files

---

## Your Job

Review all recent work and update context files to capture institutional knowledge.

---

## Step 1: Review Recent Work

Read these files:
- `.claude/WORKER_REPORTS.md` - All worker reports since last curation
- `.claude/LIVE_STATE.md` - Current state
- `git log --oneline -50` - Recent commits

Look for:
- Patterns that keep recurring
- Mistakes we made and fixed
- Business rules we discovered
- Technical decisions we made
- Data quality insights

---

## Step 2: Update Context Files

### Business Context (`docs/context/business.md`)
Add any new insights about:
- How Bensley operates
- Client relationships
- Project lifecycle patterns
- Bill's preferences
- Industry terminology

### Data Context (`docs/context/data.md`)
Add insights about:
- Table relationships (especially gotchas like FK mismatches)
- Data quality patterns
- Import/export quirks
- Common data issues

### Backend Context (`docs/context/backend.md`)
Add insights about:
- API patterns
- Service architecture decisions
- Common bugs and fixes
- Performance considerations

### Frontend Context (`docs/context/frontend.md`)
Add insights about:
- Component patterns
- State management decisions
- UI/UX learnings
- Build/cache issues

---

## Step 3: Update COORDINATOR_BRIEFING.md

Synthesize the most important learnings into the briefing so new sessions start smarter:
- Update "Known Issues" section
- Update "Quick Reference" if patterns changed
- Add any new "DO NOT" warnings based on mistakes

---

## Step 4: Archive Old Reports

After curating:
1. Move processed reports to `.claude/archive/worker_reports_YYYYMMDD.md`
2. Keep WORKER_REPORTS.md fresh for new entries

---

## Step 5: Create Curation Summary

Add entry to `.claude/CURATION_LOG.md`:

```markdown
## Curation: YYYY-MM-DD

### Period Covered
[Date range]

### Key Learnings Added

#### Business
- [Learning 1]
- [Learning 2]

#### Technical
- [Learning 1]
- [Learning 2]

### Files Updated
- docs/context/business.md - Added [X]
- docs/context/data.md - Added [X]

### Patterns Identified
- [Pattern 1]: [How to handle it]
- [Pattern 2]: [How to handle it]

### Warnings Added
- [New warning about X]
```

---

## Example Learnings to Capture

From this sprint, capture:

### Data Context
```markdown
### FK Mismatch Pattern (Learned: 2025-12-01)
**Source:** Phase B Data Audit
**Insight:** email_proposal_links and email_project_links can have orphaned FKs
if link tables are populated before the target tables (proposals/projects) have
stable IDs. Always rebuild links by project_code, not by ID.
**Impact:** Always use project_code for matching, add FK constraints, validate
after any bulk link operation.
```

### Business Context
```markdown
### Project Code Format (Learned: 2025-12-01)
**Source:** Data audit investigation
**Insight:** Project codes follow format "YY BK-XXX" (e.g., "25 BK-087") where
YY is the year. Some tables store without year prefix ("BK-087") causing
matching issues.
**Impact:** Always normalize project codes when matching. Use LIKE patterns that
handle both formats.
```

---

## Curation Prompt

Use this to invoke the Context Curator:

```
Read .claude/prompts/CONTEXT_CURATOR.md

You are the CONTEXT CURATOR. Run weekly curation:
1. Review .claude/WORKER_REPORTS.md for learnings
2. Update context files in docs/context/
3. Update COORDINATOR_BRIEFING.md with key insights
4. Archive old reports
5. Log curation in .claude/CURATION_LOG.md

Focus on: What did we learn that future sessions need to know?
```
