# ⚡ Quick Start: GitHub + 5 Agents

**Goal:** Get your 5 agents building email-proposal integration using GitHub for coordination

---

## 📦 What You Have Now

✅ **EMAIL_PROPOSAL_BUILD_PLAN.md** - Complete code for all 15 tasks
✅ **GITHUB_WORKFLOW_STRATEGY.md** - Branch strategy, PR workflow, merge order
✅ **`.github/PULL_REQUEST_TEMPLATE.md`** - Standardized PR template
✅ **AGENT_DEPLOYMENT_PLAN.md** - Multi-agent coordination plan

---

## 🚀 Setup (5 Minutes)

### 1. Push Workflow Files to GitHub

```bash
# Add and commit workflow files
git add .github/ EMAIL_PROPOSAL_BUILD_PLAN.md GITHUB_WORKFLOW_STRATEGY.md .claude/AGENT_DEPLOYMENT_PLAN.md

git commit -m "$(cat <<'EOF'
Add multi-agent GitHub workflow for email-proposal integration

- Complete build plan with all code specs
- GitHub workflow strategy (branches, PRs, merge order)
- PR template for standardized reviews
- Agent deployment plan

🤖 Generated with Claude Code
EOF
)"

git push origin claude/bensley-operations-platform-011CV3dp9CnqP1L5Rkjm6NYm
```

### 2. Merge to Main (Create PR or Direct Merge)

**Option A: Via PR** (Recommended - keeps main clean)
```bash
# On GitHub.com:
# 1. Go to Pull Requests
# 2. Click "New Pull Request"
# 3. Compare: claude/bensley-operations-platform... → main
# 4. Create PR with title: "Add multi-agent workflow strategy"
# 5. Merge PR
```

**Option B: Direct Merge** (If you own the repo)
```bash
git checkout main
git merge claude/bensley-operations-platform-011CV3dp9CnqP1L5Rkjm6NYm
git push origin main
```

### 3. Protect Main Branch

On GitHub.com:
1. Go to **Settings** → **Branches**
2. Click **Add rule** (or **Add branch protection rule**)
3. Branch name pattern: `main`
4. Check these boxes:
   - ✅ **Require a pull request before merging**
   - ✅ **Require approvals** (set to 1)
   - ✅ **Dismiss stale pull request approvals when new commits are pushed**
5. Click **Create** or **Save changes**

### 4. Create GitHub Project Board (Optional but Recommended)

On GitHub.com:
1. Go to **Projects** tab
2. Click **New project**
3. Select **Board** view
4. Name: "Email-Proposal Integration"
5. Add columns:
   - 📋 Backlog
   - 🏃 In Progress
   - 👀 In Review
   - ✅ Complete
   - 🚫 Blocked

### 5. Create Issues (15 Total)

Quick way: Use GitHub CLI
```bash
# Install GitHub CLI if needed
brew install gh

# Authenticate
gh auth login

# Create issues
gh issue create --title "[Agent 1] Email Content Population Script" --body "Process 3,334 emails with AI analysis. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 1.1"

gh issue create --title "[Agent 1] Email Thread Builder" --body "Build conversation threads from message headers. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 1.2"

gh issue create --title "[Agent 1] Proposal Status History Backfill" --body "Infer historical status changes. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 1.3"

gh issue create --title "[Agent 2] Database Schema Migration" --body "Schema unification and indexes. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 2.1"

gh issue create --title "[Agent 3] Email Detail API Endpoint" --body "Full email with AI insights. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 3.1"

gh issue create --title "[Agent 3] Email Thread API Endpoint" --body "Conversation thread endpoint. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 3.2"

gh issue create --title "[Agent 3] Email Search API Endpoint" --body "Full-text search with filters. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 3.3"

gh issue create --title "[Agent 3] Bulk Operations API" --body "Batch email operations. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 3.4"

gh issue create --title "[Agent 3] Email Linking APIs" --body "Link/unlink management. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 3.5"

gh issue create --title "[Agent 4] Email Detail Modal Component" --body "Full email view modal. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 4.1"

gh issue create --title "[Agent 4] Email Thread Viewer Component" --body "Gmail-style thread view. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 4.2"

gh issue create --title "[Agent 4] Email List Component" --body "Reusable email list with search. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 4.3"

gh issue create --title "[Agent 4] Email Activity Widget" --body "Activity summary widget. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 4.4"

gh issue create --title "[Agent 5] Enhance Proposal Email Tab" --body "Integrate email list into proposal page. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 5.1"

gh issue create --title "[Agent 5] Create Email Search Page" --body "Global email search page. See EMAIL_PROPOSAL_BUILD_PLAN.md Task 5.2"
```

Or create manually on GitHub.com (Issues tab → New issue)

---

## 👥 Agent Instructions (Copy-Paste to Each Terminal)

### Terminal 1 - Agent 1 (Data Processing)

```bash
# Pull latest main
git checkout main && git pull origin main

# Create branch
git checkout -b phase1/agent1-email-processing

# Read the build plan
cat EMAIL_PROPOSAL_BUILD_PLAN.md | grep -A 200 "Agent 1"

# Start work on Task 1.1 (Email Content Population)
# Follow the code in EMAIL_PROPOSAL_BUILD_PLAN.md

# Commit regularly
git add scripts/process_email_backlog.py
git commit -m "feat: email content processor - closes #1"
git push origin phase1/agent1-email-processing

# When done, create PR on GitHub.com
```

### Terminal 2 - Agent 2 (Database Schema)

```bash
# Pull latest main
git checkout main && git pull origin main

# Create branch
git checkout -b phase1/agent2-database-schema

# Read the build plan
cat EMAIL_PROPOSAL_BUILD_PLAN.md | grep -A 100 "Agent 2"

# Start work on Task 2.1 (Schema Migration)
# Follow the SQL in EMAIL_PROPOSAL_BUILD_PLAN.md

# Test migration
sqlite3 database/bensley_master.db < database/migrations/026_email_proposal_unification.sql

# Commit
git add database/migrations/026_email_proposal_unification.sql
git commit -m "feat: database schema unification migration - closes #4"
git push origin phase1/agent2-database-schema

# Create PR on GitHub.com
# This should be MERGED FIRST (others may need the schema)
```

### Terminal 3 - Agent 3 (Backend APIs)

```bash
# WAIT for Agent 1 PR to be merged first!
# Check: gh pr list (should see Agent 1 PR merged)

# Pull latest main (includes Agent 1's work)
git checkout main && git pull origin main

# Create branch from updated main
git checkout -b phase2/agent3-backend-apis

# Read the build plan
cat EMAIL_PROPOSAL_BUILD_PLAN.md | grep -A 500 "Agent 3"

# Start work on Tasks 3.1-3.5 (API Endpoints)
# Follow the code in EMAIL_PROPOSAL_BUILD_PLAN.md

# Test each endpoint as you build
curl http://localhost:8000/api/emails/123/detail

# Commit
git add backend/api/main.py
git commit -m "feat: email detail and search APIs - closes #5 #6 #7"
git push origin phase2/agent3-backend-apis

# Create PR, mark dependency on Agent 1
```

### Terminal 4 - Agent 4 (UI Components)

```bash
# WAIT for Agent 3 PR to be merged!
# Check: gh pr list

# Pull latest main
git checkout main && git pull origin main

# Create branch
git checkout -b phase3/agent4-ui-components

# Read the build plan
cat EMAIL_PROPOSAL_BUILD_PLAN.md | grep -A 800 "Agent 4"

# Start work on Tasks 4.1-4.4 (Components)
# Follow the React/TSX code in EMAIL_PROPOSAL_BUILD_PLAN.md

# Test components in dev mode
cd frontend && npm run dev

# Commit
git add frontend/src/components/emails/
git commit -m "feat: email UI components - closes #10 #11 #12 #13"
git push origin phase3/agent4-ui-components

# Create PR
```

### Terminal 5 - Agent 5 (Integration)

```bash
# WAIT for Agent 4 PR to be merged!
# Check: gh pr list

# Pull latest main
git checkout main && git pull origin main

# Create branch
git checkout -b phase3/agent5-integration

# Read the build plan
cat EMAIL_PROPOSAL_BUILD_PLAN.md | grep -A 200 "Agent 5"

# Start work on Tasks 5.1-5.2 (Integration)
# Minimal code changes - mostly wiring up components

# Test full flows
# Open http://localhost:3002/proposals/25BK033
# Click Emails tab, test search, etc.

# Commit
git add frontend/src/app/
git commit -m "feat: integrate email components into pages - closes #14 #15"
git push origin phase3/agent5-integration

# Create PR (FINAL PR!)
```

---

## 📊 Merge Order (YOU Review and Merge)

After each agent creates their PR, review and merge in this order:

### 1. **Merge Agent 2 FIRST** (Database Schema)
```bash
# On GitHub.com:
# Pull Requests → Agent 2's PR
# Review code, test migration
# Click "Merge pull request" → "Squash and merge"
# Delete branch after merge
```

**Verify:**
```bash
git checkout main && git pull
sqlite3 database/bensley_master.db ".indexes emails"
# Should see new indexes
```

### 2. **Merge Agent 1** (Email Processing)
```bash
# Review PR, check test results
# Merge via GitHub.com
```

**Verify:**
```bash
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM email_content"
# Should be 3,356 (not 22!)

sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM email_threads"
# Should be >0
```

### 3. **Merge Agent 3** (Backend APIs)
```bash
# Review PR
# Test APIs with curl
# Merge
```

**Verify:**
```bash
curl http://localhost:8000/api/emails/123/detail | python3 -m json.tool
# Should return full email with AI insights
```

### 4. **Merge Agent 4** (UI Components)
```bash
# Review PR
# Check component code quality
# Merge
```

### 5. **Merge Agent 5** (Integration) - FINAL
```bash
# Review PR
# Full end-to-end test
# Merge
```

**Final Verify:**
```bash
# Open http://localhost:3002/proposals/25BK033
# Click Emails tab
# Test: search, filters, click email, view thread
# All should work!
```

---

## ✅ Success Checklist

After all merges complete:

- [ ] 5 PRs created and merged
- [ ] 15 issues closed
- [ ] 0 merge conflicts
- [ ] All tests passing
- [ ] Email-proposal integration working end-to-end
- [ ] Main branch deployable

---

## 🎯 Quick Commands Reference

### Check PR status
```bash
gh pr list
gh pr list --state merged
```

### View an agent's branch locally
```bash
gh pr checkout 1  # Check out PR #1
```

### Check what's merged to main
```bash
git log --oneline --graph main
```

### See all branches
```bash
git branch -a
```

### Clean up after all merges
```bash
# Delete local branches
git branch -d phase1/agent1-email-processing
git branch -d phase1/agent2-database-schema
git branch -d phase2/agent3-backend-apis
git branch -d phase3/agent4-ui-components
git branch -d phase3/agent5-integration

# Prune remote branches
git fetch --prune
```

---

## 💡 Tips

1. **Agents can start in parallel:** Agent 1 & 2 work simultaneously (no conflicts)
2. **You control quality:** Review each PR before merging
3. **Clear dependencies:** Agent 3 can't start until Agent 1 merges
4. **Communication:** Use PR comments for questions
5. **Checkpoints:** Test after each merge (catch issues early)

---

## 🚨 If Something Goes Wrong

### Merge Conflict
```bash
# Agent's branch
git checkout phase2/agent3-backend-apis
git fetch origin
git merge origin/main
# Resolve conflicts
git add .
git commit -m "merge: resolve conflicts with main"
git push
```

### Bad Merge (Revert)
```bash
# Find the merge commit
git log --oneline

# Revert it
git revert -m 1 <merge-commit-hash>
git push origin main
```

### Agent Stuck
- Check dependencies (did previous agent merge?)
- Check PR comments for blockers
- Review build plan for clarity

---

**Ready to roll!** 🚀

Your 5 agents now have:
- Complete code to implement
- Clear branch strategy
- GitHub workflow for coordination
- Merge order to prevent conflicts

Just follow the Terminal instructions above and let them execute!
