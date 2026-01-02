# Audit Agent - Continuous System Health & Issue Discovery

> Type: Ongoing | Schedule: Daily or on-demand | Branch: N/A (audit only)

---

## CONTEXT

This agent continuously audits the codebase, database, and system health. When it finds issues, it creates GitHub issues with proper labels and context.

**Primary function:** Find problems before they become blockers.

---

## AUDIT AREAS

### 1. Code Quality
- TypeScript errors (`npx tsc --noEmit`)
- ESLint errors (`npm run lint`)
- Unused imports/variables
- Dead code / unused functions
- TODO/FIXME comments that need issues

### 2. Database Health
- Orphaned records (FK violations waiting to happen)
- Duplicate data
- NULL values in required fields
- Inconsistent data (e.g., proposal status vs reality)
- Table bloat (unused tables)

### 3. API Consistency
- Endpoints returning errors
- Missing error handling
- Inconsistent response formats
- Missing authentication on protected routes

### 4. Frontend Issues
- Build errors
- Console errors/warnings
- Broken links/routes
- Missing loading states
- Accessibility issues

### 5. Documentation Drift
- CLAUDE.md out of date
- Roadmap not matching reality
- Missing API documentation
- Stale comments in code

### 6. Security
- Hardcoded secrets
- Missing input validation
- SQL injection vectors
- XSS vulnerabilities

---

## WORKFLOW

### Phase 1: Run Checks
```bash
# Code quality
cd frontend && npx tsc --noEmit 2>&1 | head -50
cd frontend && npm run lint 2>&1 | head -50
cd backend && python -m py_compile api/main.py

# Database health
sqlite3 database/bensley_master.db "PRAGMA foreign_key_check;"
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM [table] WHERE [field] IS NULL;"

# API health
curl -s http://localhost:8000/api/health
curl -s http://localhost:8000/api/proposals/stats

# Frontend build
cd frontend && npm run build 2>&1 | tail -30
```

### Phase 2: Triage Findings
```
For each finding:
1. Is this a real issue or false positive?
2. What's the severity? (P0/P1/P2)
3. Is there an existing issue for this?
4. Can it be quick-fixed now (<5 min)?
```

### Phase 3: Create Issues or Fix
```
Quick fix (<5 min):
- Fix it immediately
- Commit with "fix: description"
- No issue needed

Larger issue:
- Create GitHub issue with proper template
- Add labels (bug, area/*, priority:*)
- Reference relevant files/lines
```

---

## ISSUE CREATION TEMPLATE

```bash
gh issue create --title "[AUDIT] Short description" --body "$(cat <<'EOF'
## Found By
Audit Agent - [date]

## What's Wrong
[Clear description of the issue]

## Where
- File: `path/to/file.py:123`
- Table: `table_name`
- Endpoint: `/api/path`

## Impact
[What breaks or could break]

## Suggested Fix
[If known]

## Reproduction
```bash
# Command to reproduce
```

---
**Priority:** P0/P1/P2
**Labels:** bug, area/[area]
EOF
)" --label "bug"
```

---

## COMMON AUDIT QUERIES

### Database
```sql
-- Orphaned records (FK violations)
SELECT 'email_proposal_links' as tbl, COUNT(*)
FROM email_proposal_links
WHERE proposal_id NOT IN (SELECT proposal_id FROM proposals);

-- NULL required fields
SELECT 'proposals without project_code', COUNT(*)
FROM proposals WHERE project_code IS NULL;

-- Duplicates
SELECT invoice_number, COUNT(*) as cnt
FROM invoices
GROUP BY invoice_number
HAVING COUNT(*) > 1;

-- Stale data
SELECT 'proposals no activity 30+ days', COUNT(*)
FROM proposals
WHERE last_contact_date < date('now', '-30 days')
AND status NOT IN ('won', 'lost', 'dormant');
```

### Code
```bash
# Unused exports
grep -r "export function" frontend/src --include="*.tsx" | wc -l

# TODO/FIXME comments
grep -rn "TODO\|FIXME\|HACK\|XXX" backend frontend --include="*.py" --include="*.tsx" --include="*.ts" | head -20

# Console.log in production code
grep -rn "console.log" frontend/src --include="*.tsx" | grep -v "test\|spec" | head -10
```

---

## SEVERITY GUIDELINES

| Severity | Description | Response |
|----------|-------------|----------|
| **P0** | System broken, data loss risk | Fix immediately |
| **P1** | Feature broken, user-facing | Fix this week |
| **P2** | Technical debt, minor issue | Add to backlog |
| **P3** | Improvement suggestion | Document only |

---

## EXAMPLE AUDIT RUN

```bash
# 1. Start audit
echo "=== AUDIT START: $(date) ===" >> .claude/audit.log

# 2. TypeScript check
npx tsc --noEmit 2>&1 | tee -a .claude/audit.log

# 3. Database health
sqlite3 database/bensley_master.db "PRAGMA foreign_key_check;" 2>&1 | tee -a .claude/audit.log

# 4. Check open issues vs reality
gh issue list --state open --limit 50

# 5. Summary
echo "=== AUDIT END ===" >> .claude/audit.log
```

---

## CONSTRAINTS

- **Don't break things** - audit is read-only unless quick-fixing
- **Check existing issues** - don't create duplicates
- **Use proper labels** - all issues must have priority + area
- **Include context** - issues must be actionable without asking questions

---

## ALL AGENTS RULE

> **Every agent should follow this pattern:**
>
> When an agent discovers an issue during its work:
> 1. If quick fix (<5 min) → fix it, commit
> 2. If related to current task → fix it, include in PR
> 3. If unrelated/larger → create GitHub issue with context
> 4. Never ignore problems - document or fix

---

## FILES

- `.claude/audit.log` - Running audit log
- Issues tagged with `audit-found`
