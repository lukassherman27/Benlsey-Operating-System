# 🔀 GitHub Workflow Strategy for Multi-Agent Development

**Repository:** Bensley Operating System
**Purpose:** Coordinate 5 agents building email-proposal integration without conflicts

---

## 🎯 Strategy Overview

**Key Principles:**
1. **One branch per agent** - No stepping on each other's toes
2. **Sequential merging** - Respect dependencies (Agent 1 → 3 → 4 → 5)
3. **PR reviews** - YOU review before merging (no auto-merges)
4. **Protected main** - Can't push directly, forces PR workflow
5. **Issue tracking** - One issue per major task

---

## 📋 Setup Instructions (Do This First)

### 1. Protect Main Branch
```bash
# On GitHub.com: Settings → Branches → Add rule
# Branch name: main
# ✅ Require pull request before merging
# ✅ Require approvals: 1
# ✅ Dismiss stale reviews
# ✅ Require status checks to pass
```

### 2. Create Project Board
```
GitHub → Projects → New Project → Board
Name: "Email-Proposal Integration"

Columns:
- 📋 Backlog
- 🏃 In Progress
- 👀 In Review
- ✅ Complete
- 🚫 Blocked
```

### 3. Create Issues (One Per Agent Task)

**Issue Template:**
```markdown
## Task: [Agent N] [Task Name]

**Agent:** Agent N
**Phase:** 1/2/3
**Priority:** Critical/High/Medium
**Estimated Time:** X hours

### Deliverables
- [ ] Script/component created
- [ ] Tests passing
- [ ] Documentation updated
- [ ] PR submitted

### Dependencies
- Blocks: #issue_number
- Blocked by: #issue_number

### Branch
`phase1/agent1-email-processing`

### Definition of Done
- Code reviewed
- Tests pass
- No merge conflicts
- Documentation complete
```

**Create These Issues:**
```
#1: [Agent 1] Email Content Population Script
#2: [Agent 1] Email Thread Builder
#3: [Agent 1] Proposal Status History Backfill
#4: [Agent 2] Database Schema Migration
#5: [Agent 3] Email Detail API Endpoint
#6: [Agent 3] Email Thread API Endpoint
#7: [Agent 3] Email Search API Endpoint
#8: [Agent 3] Bulk Operations API
#9: [Agent 3] Email Linking APIs
#10: [Agent 4] Email Detail Modal Component
#11: [Agent 4] Email Thread Viewer Component
#12: [Agent 4] Email List Component
#13: [Agent 4] Email Activity Widget
#14: [Agent 5] Enhance Proposal Email Tab
#15: [Agent 5] Create Email Search Page
```

---

## 🚀 Agent Workflow (Give This to Each Agent)

### Agent Setup (Each Agent Does This)

#### Step 1: Create Your Branch
```bash
# Agent 1
git checkout main
git pull origin main
git checkout -b phase1/agent1-email-processing

# Agent 2
git checkout main
git pull origin main
git checkout -b phase1/agent2-database-schema

# Agent 3
git checkout main
git pull origin main
git checkout -b phase2/agent3-backend-apis

# Agent 4
git checkout main
git pull origin main
git checkout -b phase3/agent4-ui-components

# Agent 5
git checkout main
git pull origin main
git checkout -b phase3/agent5-integration
```

#### Step 2: Link to Issue
```bash
# In your commits, reference the issue number
git commit -m "feat: email content processor script - closes #1"
```

#### Step 3: Push Regularly (Every Hour or After Major Progress)
```bash
git add .
git commit -m "wip: email thread builder progress"
git push origin phase1/agent1-email-processing
```

#### Step 4: Create PR When Task Complete
```bash
# Push final changes
git push origin phase1/agent1-email-processing

# On GitHub.com:
# 1. Navigate to your branch
# 2. Click "Compare & pull request"
# 3. Fill out PR template (below)
# 4. Assign to yourself
# 5. Request review from user
# 6. Link to issue (closes #1)
```

---

## 📝 Pull Request Template

Create `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## Description
[Describe what this PR does - which agent task]

## Related Issues
Closes #[issue_number]

## Agent
- [ ] Agent 1 - Data Processing
- [ ] Agent 2 - Database Schema
- [ ] Agent 3 - Backend APIs
- [ ] Agent 4 - UI Components
- [ ] Agent 5 - Integration

## Type of Change
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Database migration
- [ ] Documentation update

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for complex logic
- [ ] Documentation updated (if needed)
- [ ] No merge conflicts with main
- [ ] Tests added/updated (if applicable)
- [ ] All tests passing
- [ ] Database migrations tested (if applicable)

## Testing Performed
[Describe how you tested your changes]

```bash
# Example test commands you ran
python3 scripts/process_email_backlog.py --batch-size 10
# Result: Processed 10 emails successfully
```

## Screenshots/Logs
[Add screenshots or logs showing functionality]

## Dependencies
- [ ] This PR depends on #[other_PR] being merged first
- [ ] No dependencies - can merge independently

## Notes for Reviewer
[Any context the reviewer should know]

## Deployment Notes
[Any special deployment steps needed]
```

---

## 🔄 Merge Order (CRITICAL - Follow This Sequence)

### Phase 1: Foundation (Can merge in parallel)
1. **Agent 2 PR** → Merge FIRST (database schema - others may need it)
2. **Agent 1 PR** → Merge second (email processing - CRITICAL PATH)

**Checkpoint:** After Phase 1 merges, verify:
```bash
# Check email_content table populated
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM email_content"
# Should be 3,356

# Check threads created
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM email_threads"
# Should be >0

# Check migration applied
sqlite3 database/bensley_master.db ".schema email_proposal_links"
# Should have indexes
```

### Phase 2: Backend APIs (Sequential merge)
3. **Agent 3 PR** → Merge after Agent 1 complete

**Checkpoint:** After Agent 3 merges, test APIs:
```bash
curl http://localhost:8000/api/emails/123/detail
curl http://localhost:8000/api/emails/search?q=contract
```

### Phase 3: Frontend (Sequential merge)
4. **Agent 4 PR** → Merge after Agent 3 complete
5. **Agent 5 PR** → Merge LAST (integration depends on everything)

**Final Checkpoint:** Full integration test
- Open http://localhost:3002/proposals/25BK033
- Click Emails tab → should show enhanced list
- Click email → modal opens with AI insights
- Search emails → results appear

---

## 🚨 Handling Merge Conflicts

### If Agent 3 Has Conflicts with Main (After Agent 1 merged)

```bash
# Agent 3's branch
git checkout phase2/agent3-backend-apis
git fetch origin
git merge origin/main

# Resolve conflicts in your editor
# Then:
git add .
git commit -m "merge: resolve conflicts with main after Agent 1 merge"
git push origin phase2/agent3-backend-apis
```

### Conflict Prevention Strategy
**Each agent works on separate files:**
- **Agent 1:** Only touches `scripts/` folder
- **Agent 2:** Only touches `database/migrations/`
- **Agent 3:** Only touches `backend/api/main.py` (different sections)
- **Agent 4:** Only touches `frontend/src/components/emails/`
- **Agent 5:** Only touches existing proposal pages (minimal edits)

**Minimal overlap = minimal conflicts**

---

## 📊 GitHub Project Board Workflow

### Backlog Column
- All 15 issues start here

### In Progress Column
- Agent moves issue here when starting work
- Agent creates branch and links to issue

### In Review Column
- Agent moves issue here when PR submitted
- User reviews PR

### Complete Column
- User moves issue here after merging PR

### Blocked Column
- Agent moves issue here if waiting on another agent
- Example: Agent 3 blocked by Agent 1 (dependency)

---

## 🎯 Efficient Commands for You (User/Reviewer)

### View All Open PRs
```bash
gh pr list
# Or on GitHub.com: Pull Requests tab
```

### Review a PR
```bash
# Checkout the PR locally to test
gh pr checkout 1

# Test the changes
python3 scripts/process_email_backlog.py --batch-size 10

# If good, approve on GitHub.com
# Then merge with button
```

### Check Overall Progress
```bash
# See what's merged
git log --oneline --graph --all

# See what's in progress
gh pr list --state open
```

### Merge a PR (After Approval)
```bash
# On GitHub.com:
# 1. Click "Merge pull request"
# 2. Use "Squash and merge" (cleaner history)
# 3. Delete branch after merge
```

---

## 🔍 Automated Checks (Optional - Set Up Later)

### GitHub Actions for CI/CD
Create `.github/workflows/test.yml`:

```yaml
name: Test Email Processing

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run database migration
        run: |
          sqlite3 database/bensley_master.db < database/migrations/026_email_proposal_unification.sql

      - name: Test email processor (dry run)
        run: |
          python3 scripts/process_email_backlog.py --batch-size 5 --dry-run

      - name: Test API endpoints (if backend changes)
        run: |
          cd backend
          python -m pytest tests/

      - name: Frontend build test
        run: |
          cd frontend
          npm install
          npm run build
```

This runs automatically on every PR to catch issues early.

---

## 📋 Quick Reference for Each Agent

### Agent 1 Checklist
- [ ] Create branch `phase1/agent1-email-processing`
- [ ] Move issues #1, #2, #3 to "In Progress"
- [ ] Build scripts in `scripts/` folder
- [ ] Test with small batch first (10 emails)
- [ ] Run full processing (3,334 emails)
- [ ] Commit regularly with good messages
- [ ] Create PR when done
- [ ] Wait for review and merge

### Agent 2 Checklist
- [ ] Create branch `phase1/agent2-database-schema`
- [ ] Move issue #4 to "In Progress"
- [ ] Create migration file
- [ ] Test migration on backup database first
- [ ] Run migration on main database
- [ ] Verify indexes created
- [ ] Create PR when done
- [ ] This should merge FIRST (others may depend on schema)

### Agent 3 Checklist
- [ ] **WAIT for Agent 1 PR to merge** (CRITICAL DEPENDENCY)
- [ ] Pull latest main: `git pull origin main`
- [ ] Create branch from updated main
- [ ] Move issues #5-9 to "In Progress"
- [ ] Build API endpoints in `backend/api/main.py`
- [ ] Test each endpoint with curl
- [ ] Create PR when done
- [ ] Mark dependencies in PR (depends on Agent 1)

### Agent 4 Checklist
- [ ] **WAIT for Agent 3 PR to merge** (needs APIs)
- [ ] Pull latest main
- [ ] Create branch from updated main
- [ ] Move issues #10-13 to "In Progress"
- [ ] Build components in `frontend/src/components/emails/`
- [ ] Test each component in isolation
- [ ] Create PR when done

### Agent 5 Checklist
- [ ] **WAIT for Agent 4 PR to merge** (needs components)
- [ ] Pull latest main
- [ ] Create branch from updated main
- [ ] Move issues #14-15 to "In Progress"
- [ ] Integrate components into existing pages
- [ ] Test full user flows
- [ ] Create PR when done (FINAL PR)

---

## 🎯 Benefits of This GitHub Strategy

### 1. **Prevents Fragmentation**
- All work tracked in one repo
- Clear dependency chain
- Review checkpoints before merging

### 2. **Parallel Work Enabled**
- Agents 1 & 2 work simultaneously
- No waiting when not needed
- Clear blocking relationships

### 3. **Rollback Safety**
- Each merge is a checkpoint
- Can revert specific PRs if needed
- Protected main branch prevents accidents

### 4. **Audit Trail**
- Every change documented in PRs
- Issue comments track decisions
- Clear history of who did what

### 5. **Testing Gates**
- Can test each PR before merging
- Prevents broken code in main
- CI/CD can automate tests

### 6. **Collaboration Efficiency**
- Agents see each other's progress
- Can review each other's PRs
- Project board shows bottlenecks

---

## 🚀 First Steps (Do These Now)

1. **Create project board** on GitHub
2. **Create 15 issues** from template above
3. **Protect main branch** (require PR reviews)
4. **Add PR template** (`.github/PULL_REQUEST_TEMPLATE.md`)
5. **Brief each agent** on their branch name and workflow
6. **Agent 1 & 2 start** (they can work in parallel)

---

## 📞 Communication Protocol

**When to notify user:**
- ✅ PR created (ready for review)
- ✅ Blocked by dependency (waiting on another agent)
- ✅ Found issue/conflict
- ✅ Major milestone reached

**When agents can self-coordinate:**
- Code questions (comment on PR)
- Merge conflicts (resolve and push)
- Testing results (document in PR)

---

## 🎯 Success Metrics

After all PRs merged:
- [ ] 5 branches merged cleanly
- [ ] 15 issues closed
- [ ] 0 merge conflicts remaining
- [ ] All tests passing
- [ ] Project board shows 15 tasks complete
- [ ] `git log` shows clean, sequential merges
- [ ] Main branch deployable

---

**This workflow transforms chaos into coordination.** 🚀

Each agent knows:
- What branch to work on
- When they can start
- What they're building
- How to submit work
- When to wait for others

You control the merge order and quality through PR reviews.
