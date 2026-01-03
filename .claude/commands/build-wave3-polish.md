# WAVE 3 - Polish & Cleanup

Run these in PARALLEL after Wave 2 completes.

---

## Agent 3A: Bill's Quick Review (#363)

```
You are a Builder Agent for the Bensley Operating System.

## Assignment
- Issue: #363
- Branch: feat/bill-quick-review-363

## Setup
Launch via: ./launch_agent.sh claude 363
This creates your worktree and sets the branch automatically.

## MANDATORY WORKFLOW

### 1. AUDIT (10 min)
Read these files:
- CLAUDE.md
- AGENTS.md
- frontend/src/app/(dashboard)/tracker/page.tsx
- frontend/src/components/proposals/quick-action-dialogs.tsx
- frontend/src/lib/constants.ts (check valid status values)

Valid statuses (from constants.ts):
- First Contact, Proposal Prep, Proposal Sent, Negotiation
- On Hold, Contract Signed, Lost, Declined, Dormant

Post findings:
gh issue comment 363 --body "AUDIT: No quick review modal exists. Need to create new component."

### 2. PLAN (5 min)
gh issue comment 363 --body "PLAN: Create BillQuickReview component with 3 actions: Pursue (->Negotiation), Drop (->Lost), Need Info"

### 3. IMPLEMENT

The Feature:
Bill sends 5-word emails like "I don't like him, drop it."

Create: frontend/src/components/proposals/bill-quick-review.tsx

Show ONLY what Bill needs:
1. Project name + location
2. Fee size
3. Key question/context (1-2 sentences)
4. Big buttons: Pursue | Drop | Need More Info

```tsx
<Dialog>
  <h2>{projectName}</h2>
  <p className="text-2xl font-bold">${projectValue}</p>
  <p>{country} - {discipline}</p>
  <p className="text-sm">{currentRemark || actionNeeded}</p>

  <div className="flex gap-4 mt-6">
    <Button onClick={handlePursue} className="bg-green-600">Pursue</Button>
    <Button onClick={handleDrop} className="bg-red-600">Drop</Button>
    <Button onClick={handleNeedInfo} variant="outline">Need Info</Button>
  </div>
</Dialog>
```

Actions (use VALID statuses from constants.ts):
- Pursue -> Update status to "Negotiation" (NOT "Active Pursuit" - that's invalid)
- Drop -> Open MarkLostDialog (sets status to "Lost")
- Need Info -> Create action item for Lukas

Add trigger button to tracker row actions.

```bash
git commit -m "feat(proposals): add Bill's Quick Review component #363"
git commit -m "feat(proposals): add Quick Review to tracker row actions #363"
```

### 4. VERIFY
```bash
cd frontend && npm run build

# Manual test:
# 1. Open /tracker
# 2. Click quick review on a proposal
# 3. Modal shows key info
# 4. Actions work correctly
```

### 5. DOCUMENT
```bash
git push -u origin feat/bill-quick-review-363
gh pr create --title "feat(proposals): add Bill's Quick Review modal #363" \
  --body "Fixes #363. Quick Review modal with Pursue/Drop/Need Info actions."
gh issue close 363 --comment "Fixed in PR."
```
```

---

## Agent 3B: Dead Code Cleanup (#377, #378)

```
You are a Builder Agent for the Bensley Operating System.

## Assignment
- Issues: #377, #378
- Branch: chore/cleanup-dead-code-377-378

## Setup
Launch via: ./launch_agent.sh claude 377
This creates your worktree and sets the branch automatically.

## MANDATORY WORKFLOW

### 1. AUDIT (10 min)
Read these files:
- CLAUDE.md
- AGENTS.md

For #377 - Check these are unused:
```bash
rg -n "ProposalsManager" frontend/src/
rg -n "ProposalTasks" frontend/src/
rg -n "ProposalEmailsCard" frontend/src/
rg -n "ProposalTimeline" frontend/src/
rg -n "ProposalsWeeklyReport" frontend/src/
```

Files to delete (if unused):
1. frontend/src/components/proposals/proposals-manager.tsx
2. frontend/src/components/proposals/proposal-tasks.tsx
3. frontend/src/components/proposals/proposal-emails-card.tsx
4. frontend/src/components/proposals/proposal-timeline.tsx
5. frontend/src/components/proposals/proposals-weekly-report.tsx

For #378 - Investigate:
- proposal_story_service.py vs proposal_detail_story_service.py
- What's the difference? Can they be consolidated?

Post findings:
gh issue comment 377 --body "AUDIT: Confirmed 5 components are unused: [list]"
gh issue comment 378 --body "AUDIT: Service comparison: [findings]"

### 2. PLAN (5 min)
gh issue comment 377 --body "PLAN: Delete 5 unused components"
gh issue comment 378 --body "PLAN: [consolidate OR document for future]"

### 3. IMPLEMENT

For #377:
- Delete the 5 unused files
- Verify build still works

For #378:
- If consolidation is complex, just document findings in issue comment
- Don't do major refactor in this wave

```bash
git commit -m "chore(cleanup): remove 5 dead proposal components #377"
git commit -m "docs(services): document service duplication findings #378"
```

### 4. VERIFY
```bash
cd frontend && npm run build
# Should succeed with fewer files

cd backend && python -c "from services.proposal_service import ProposalService; print('OK')"
```

### 5. DOCUMENT
```bash
git push -u origin chore/cleanup-dead-code-377-378
gh pr create --title "chore(cleanup): remove dead code and document services #377 #378" \
  --body "Fixes #377. Documents #378."
gh issue close 377 --comment "Deleted: proposals-manager, proposal-tasks, proposal-emails-card, proposal-timeline, proposals-weekly-report"
gh issue comment 378 --body "Investigated: [findings]. Recommend: [action]"
```
```

---

## Agent 3C: Performance Fixes (#381)

```
You are a Builder Agent for the Bensley Operating System.

## Assignment
- Issue: #381
- Branch: perf/fixes-381

## Setup
Launch via: ./launch_agent.sh claude 381
This creates your worktree and sets the branch automatically.

## MANDATORY WORKFLOW

### 1. AUDIT (10 min)
Read these files:
- CLAUDE.md
- AGENTS.md
- backend/services/proposal_detail_story_service.py
- backend/services/proposal_tracker_service.py

Bug 1: N+1 Query in Timeline (~lines 258-275)
```python
# Current (bad):
for attachment in attachments:
    cursor.execute("SELECT direction FROM emails WHERE id = ?", (attachment.email_id,))
```

Bug 2: Hardcoded Year (~lines 148-184)
```python
# Current (bad):
WHERE date >= '2025-01-01'
WHERE date >= '2024-01-01'
```

Post findings:
gh issue comment 381 --body "AUDIT: N+1 at line X, hardcoded year at line Y"

### 2. PLAN (5 min)
gh issue comment 381 --body "PLAN: Batch email query with empty guard, add dynamic year filter"

### 3. IMPLEMENT

Fix N+1 (with guard for empty list):
```python
# Get all email IDs
email_ids = [a.email_id for a in attachments if a.email_id]

# Guard against empty list (avoids invalid SQL)
if email_ids:
    placeholders = ','.join('?' * len(email_ids))
    cursor.execute(f"SELECT id, direction FROM emails WHERE id IN ({placeholders})", email_ids)
    direction_map = {row[0]: row[1] for row in cursor.fetchall()}
else:
    direction_map = {}

# Lookup
for attachment in attachments:
    direction = direction_map.get(attachment.email_id)
```

Fix Hardcoded Year:
```python
from datetime import date

current_year = date.today().year
start_of_year = f"{current_year}-01-01"
start_of_last_year = f"{current_year - 1}-01-01"
```

```bash
git commit -m "perf(proposals): fix N+1 query in timeline #381"
git commit -m "perf(proposals): use dynamic year filter #381"
```

### 4. VERIFY
```bash
cd backend
python -c "from services.proposal_tracker_service import ProposalTrackerService; print('OK')"
```

### 5. DOCUMENT
```bash
git push -u origin perf/fixes-381
gh pr create --title "perf(proposals): fix N+1 query and dynamic year filter #381" \
  --body "Fixes #381. N+1 fixed with batch query (with empty guard), year filter now dynamic."
gh issue close 381 --comment "Fixed in PR."
```
```
