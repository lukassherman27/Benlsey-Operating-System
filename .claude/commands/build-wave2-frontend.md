# WAVE 2 - Frontend Features

Run these in PARALLEL (no dependencies between them).

---

## Agent 2A: Lost Reason + Ball Flip (#360)

```
You are a Builder Agent for the Bensley Operating System.

## Assignment
- Issue: #360
- Branch: feat/lost-reason-ball-flip-360

## Setup
Launch via: ./launch_agent.sh claude 360
This creates your worktree and sets the branch automatically.

## MANDATORY WORKFLOW

### 1. AUDIT (10 min)
Read these files:
- CLAUDE.md
- AGENTS.md
- frontend/src/components/proposals/quick-action-dialogs.tsx (MarkLostDialog)
- frontend/src/app/(dashboard)/proposals/[projectCode]/page.tsx

Post findings:
gh issue comment 360 --body "AUDIT: MarkLostDialog exists but missing reason dropdown. BallInCourt shows but not clickable on detail page."

### 2. PLAN (5 min)
gh issue comment 360 --body "PLAN: Add reason dropdown to MarkLostDialog, wire up ball flip on detail page"

### 3. IMPLEMENT

Work 1: Enhance MarkLostDialog
- Add dropdown for lost reason:
  - Price too high
  - Timing not right
  - Chose competitor
  - Project cancelled
  - Client unresponsive
  - Other
- Add optional text field for competitor name
- Save to lost_reason and lost_to_competitor columns

Work 2: Ball Flip on Detail Page
- Find BallInCourt component usage in detail page
- Wire up the flip action (change ball_in_court via API)
- Optimistic update + toast confirmation

Files to modify:
- frontend/src/components/proposals/quick-action-dialogs.tsx
- frontend/src/app/(dashboard)/proposals/[projectCode]/page.tsx
- frontend/src/components/proposals/ball-in-court.tsx (if needed)

```bash
git commit -m "feat(proposals): add lost reason dropdown to MarkLostDialog #360"
git commit -m "feat(proposals): wire up ball flip on detail page #360"
```

### 4. VERIFY
```bash
cd frontend && npm run build
# No errors

# Manual test:
# 1. Open proposal detail page
# 2. Click ball-in-court -> should flip
# 3. Mark as Lost -> should prompt for reason
```

### 5. DOCUMENT
```bash
git push -u origin feat/lost-reason-ball-flip-360
gh pr create --title "feat(proposals): add lost reason capture and ball flip #360" \
  --body "Fixes #360. Lost reason dropdown added, ball flip working on detail page."
gh issue close 360 --comment "Fixed in PR."
```
```

---

## Agent 2B: My Day View (#362)

```
You are a Builder Agent for the Bensley Operating System.

## Assignment
- Issue: #362
- Branch: feat/my-day-view-362

## Setup
Launch via: ./launch_agent.sh claude 362
This creates your worktree and sets the branch automatically.

## MANDATORY WORKFLOW

### 1. AUDIT (10 min)
Read these files:
- CLAUDE.md
- AGENTS.md
- frontend/src/app/(dashboard)/tracker/page.tsx
- Look for existing date/filter logic

Post findings:
gh issue comment 362 --body "AUDIT: Tracker page has proposalsData available. Need to add My Day section above stats cards."

### 2. PLAN (5 min)
gh issue comment 362 --body "PLAN: Create MyDaySection component, filter by action_due + ball_in_court, add above stats"

### 3. IMPLEMENT

Create: frontend/src/app/(dashboard)/tracker/components/my-day-section.tsx

Show sections:
1. Overdue - action_due < today AND ball_in_court = 'us'
2. Due Today - action_due = today
3. Due This Week - action_due within 7 days

```typescript
const todayActions = proposals.filter(p =>
  p.action_due === today && p.ball_in_court === 'us'
);
```

Render as cards with:
- Project name
- Action needed
- Days overdue (if overdue)
- Quick action buttons

Design:
- Use existing ds design system tokens
- Match existing card styling
- Collapsible if list is long (>5 items)

Add to tracker page above the stats cards.

```bash
git commit -m "feat(proposals): add My Day section component #362"
git commit -m "feat(proposals): integrate My Day into tracker page #362"
```

### 4. VERIFY
```bash
cd frontend && npm run build
# No errors

# Manual test:
# 1. Open /tracker
# 2. See "My Day" section at top
# 3. Shows prioritized actions
```

### 5. DOCUMENT
```bash
git push -u origin feat/my-day-view-362
gh pr create --title "feat(proposals): add My Day prioritized task view #362" \
  --body "Fixes #362. My Day section added showing overdue, due today, due this week."
gh issue close 362 --comment "Fixed in PR."
```
```

---

## Agent 2C: Conversation Improvements (#364)

```
You are a Builder Agent for the Bensley Operating System.

## Assignment
- Issue: #364
- Branch: feat/conversation-improvements-364

## Setup
Launch via: ./launch_agent.sh claude 364
This creates your worktree and sets the branch automatically.

## IMPORTANT: Security Constraint (#385)
Do NOT return body_full by default. Return body_preview only.
Create separate endpoint for full body if needed.

## MANDATORY WORKFLOW

### 1. AUDIT (10 min)
Read these files:
- CLAUDE.md
- AGENTS.md
- frontend/src/components/proposals/conversation-view.tsx
- backend/api/routers/proposals.py (conversation endpoint)
- Check issue #385 for security requirements

Post findings:
gh issue comment 364 --body "AUDIT: Conversation returns ALL emails, no pagination or search. Also returns body_full which violates #385."

### 2. PLAN (5 min)
gh issue comment 364 --body "PLAN: Add page/per_page/search params to backend. Return body_preview by default (per #385). Add search input and pagination to frontend."

### 3. IMPLEMENT

Backend Work:
```python
@router.get("/proposals/{code}/conversation")
async def get_conversation(
    code: str,
    page: int = 1,
    per_page: int = 20,
    search: str = None
):
```
- Add search filter (subject, body_preview, sender)
- Return body_preview NOT body_full (per #385)
- Add separate endpoint for full body if needed

Frontend Work:
- Add search input above conversation
- Add pagination controls at bottom
- Show "Load more" or page numbers

```bash
git commit -m "feat(api): add pagination and search to conversation endpoint #364"
git commit -m "fix(security): return body_preview not body_full per #385 #364"
git commit -m "feat(ui): add search and pagination to conversation view #364"
```

### 4. VERIFY
```bash
# Backend
cd backend && python -c "from api.routers.proposals import router; print('OK')"

# Frontend
cd frontend && npm run build

# Manual test:
# 1. Open proposal detail -> Conversation tab
# 2. Should show pagination
# 3. Search should filter results
# 4. body_full should NOT be in API response
```

### 5. DOCUMENT
```bash
git push -u origin feat/conversation-improvements-364
gh pr create --title "feat(proposals): add conversation search and pagination #364" \
  --body "Fixes #364. Conversation now paginated (20/page) with search. Also respects #385 by not returning body_full."
gh issue close 364 --comment "Fixed in PR."
```
```
