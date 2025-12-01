# AUDIT AGENT - Deep System Investigation Prompt

**Copy this entire file and paste to a new Claude instance**

---

## YOUR ROLE

You are the AUDIT AGENT for the Bensley Operating System. Your job is to conduct a DEEP, THOROUGH investigation of the entire system. Use as many tokens as needed - be exhaustive.

You are NOT here to just verify issues. You are here to:
1. **Investigate root causes** - WHY are things broken?
2. **Find hidden problems** - What did we miss?
3. **Question the approach** - Is this architecture stupid? Is this the right way to build this?
4. **Provide strategic feedback** - Should we pivot? Rebuild? Continue?
5. **Create actionable recommendations** - Specific fixes with file paths

---

## THE USER'S VISION

**What Bill Bensley wants (the user):**

1. **Email Feedback Loop**
   - Import emails from IMAP
   - Categorize them automatically
   - Link them to proposals/projects
   - Learn from manual corrections
   - Build context over time

2. **Contact Intelligence**
   - Extract contacts from emails
   - Link contacts to projects
   - Know who's who on each project
   - Use contacts for better email parsing

3. **AI Training Interface**
   - Review AI suggestions
   - Approve/reject/correct
   - System learns from feedback
   - Gets smarter over time

4. **Weekly Reports with Full Context**
   - Proposal status reports for Bill
   - Include: emails, transcripts, contacts per proposal
   - Timeline of all interactions
   - Actionable insights

5. **Eventually: Vector stores + RAG**
   - Bensley chatbot with full context
   - Query anything about any project
   - NOT the priority now

**The Problem:** System is stuck. Many things appear "done" but don't actually work.

---

## WHAT THE COORDINATOR FOUND (39 Issues)

### Summary by Category
| Category | Issues | Critical |
|----------|--------|----------|
| Dashboard/KPIs | 3 | 1 |
| Proposals | 5 | 1 |
| Projects/Finance | 12 | 3 |
| Tasks | 1 | 0 |
| Meetings | 1 | 0 |
| RFIs | 3 | 1 |
| Contacts | 4 | 2 |
| Query | 1 | 1 |
| Admin/Navigation | 6 | 2 |
| Email Categorization | 3 | 2 |

### Critical Issues (Wave 1)
1. **E1** - Email categorization rules don't match actual data
2. **Q1** - Query/Brain fails with [object Object] error
3. **A2** - AI Intelligence page is 404
4. **C1** - Contacts showing UTF-8 garbage (encoded strings)
5. **F3** - Financial phase order wrong
6. **F7** - Wrong status labels (archived, proposal) on active projects
7. **R1** - RFI-undefined showing in table

### What We Thought Was Done vs Reality
| Feature | Thought | Reality |
|---------|---------|---------|
| Email categorization | ✅ DONE | ❌ 0% working |
| Query/Brain | ✅ DONE | ❌ Broken |
| Contacts page | ✅ DONE | ❌ Encoding garbage |
| AI Intelligence | ✅ DONE | ❌ 404 |
| Audit Log | ✅ DONE | ❌ 404 |
| Timeline | ✅ DONE | ❌ "Failed to load" |

---

## WHAT THE ORGANIZER FOUND (File Paths)

### E1 - Email Categorization Rules
- **Location:** `database/migrations/050_email_category_system.sql` (lines 103-135)
- **Table:** `email_category_rules`
- **Issue:** Rule #1 uses `@bensleydesign.com` but emails are from `@bensley.com`
- **Status:** Supposedly fixed by Worker B

### Q1 - Query [object Object] Error
- **Frontend:** `frontend/src/components/query-interface.tsx` (line 216)
- **Backend:** `backend/api/routers/query.py`, `backend/services/query_service.py`
- **Issue:** Error not properly stringified in catch block

### A2/A3 - Missing Admin Pages
- **AI Intelligence:** `frontend/src/app/(dashboard)/admin/intelligence/` - NEVER CREATED
- **Audit Log:** `frontend/src/app/(dashboard)/admin/audit-log/` - NEVER CREATED
- **Dead links in:** `admin/layout.tsx:39`, `admin/page.tsx:152`

### C1 - Contact UTF-8 Encoding
- **Root cause:** RFC 2047 MIME-encoded strings in database
- **Importer:** `backend/services/email_importer.py` (line 168-182)
- **Function:** `decode_header_value()` exists but NOT applied to contact names

### F3 - Phase Ordering
- **Frontend:** `frontend/src/app/(dashboard)/projects/[projectCode]/page.tsx` (lines 455-482)
- **Issue:** `PHASE_ORDER` constant correct, but DB data may have different names

### F7 - Status Labels
- **StatusBadge:** `frontend/src/app/(dashboard)/projects/page.tsx` (lines 1058-1076)
- **DB Issue:** Mixed case - `archived` and `proposal` lowercase, others capitalized

### R1 - RFI-undefined
- **Database:** 2 rows in `rfis` table have NULL `rfi_number`

---

## YOUR INVESTIGATION TASKS

### 1. EMAIL SYSTEM - Deep Dive
The email system is supposed to be the CORE of this platform. Investigate:

```bash
# Questions to answer:
- How many emails total in database?
- How many are categorized? (should be close to 100% if working)
- How many are linked to proposals?
- How many are linked to projects?
- What % have ANY context attached?

# Check these tables:
- emails
- email_content
- email_categories
- email_category_rules
- email_proposal_links
- email_project_links
- uncategorized_emails

# Check these services:
- backend/services/email_importer.py
- backend/services/email_service.py
- backend/services/email_category_service.py
- backend/services/email_orchestrator.py
- backend/services/ai_learning_service.py
```

**Key Question:** Is the email→categorization→linking→learning pipeline actually connected end-to-end? Or are there broken links?

### 2. SUGGESTION/LEARNING SYSTEM - Deep Dive
The AI suggestion system is supposed to learn from feedback. Investigate:

```bash
# Questions to answer:
- How many suggestions exist?
- How many are pending vs approved vs rejected?
- When suggestions are approved, does ANYTHING actually happen?
- Are the 7 handlers actually being used?

# Check these:
- ai_suggestions table
- backend/services/suggestion_handlers/*.py
- backend/api/routers/suggestions.py
```

**Key Question:** When a user approves a suggestion, does the system actually learn? Or is it just marking as "approved" with no effect?

### 3. CONTACTS SYSTEM - Deep Dive
Contacts should help with email parsing and context. Investigate:

```bash
# Questions to answer:
- How many contacts have garbage names (=?UTF-8...)?
- How many contacts are linked to ANY project?
- Is contact extraction from emails working?
- Can you trace: Contact → Project → Emails?

# Check these:
- contacts table
- project_contact_links table
- backend/services/contact_service.py (if exists)
```

**Key Question:** Is the contact system providing ANY value right now? Or is it just broken data?

### 4. QUERY/BRAIN SYSTEM - Deep Dive
The "Bensley Brain" should answer questions. Investigate:

```bash
# Questions to answer:
- What happens when you call /api/query/ask?
- Is OpenAI API key configured?
- What context does it have access to?
- Why does it return [object Object]?

# Check these:
- backend/api/routers/query.py
- backend/services/query_service.py
- .env or environment config
```

**Key Question:** Has the Brain EVER worked? Or was it always broken?

### 5. ADMIN/NAVIGATION - Deep Dive
Multiple admin pages and confusing navigation. Investigate:

```bash
# Questions to answer:
- List ALL files in frontend/src/app/(dashboard)/admin/
- What does the sidebar navigation reference?
- What does the Admin Tools header reference?
- Are there orphaned/archived pages anywhere?

# Check these:
- frontend/src/components/layout/app-shell.tsx (sidebar)
- frontend/src/app/(dashboard)/admin/layout.tsx
- frontend/src/app/(dashboard)/admin/page.tsx
```

**Key Question:** Why are there TWO different navigation structures? Was one supposed to replace the other?

### 6. FINANCIAL DATA - Deep Dive
KPIs showing wrong values. Investigate:

```bash
# Questions to answer:
- What's the actual sum of payments this month?
- What's the actual outstanding invoice total?
- Are the SQL queries correct?
- Is there data integrity issues?

# Check these:
- backend/api/routers/dashboard.py
- backend/services/financial_service.py
- invoices table
- payments table (if exists)
```

**Key Question:** Is the data wrong, or are the calculations wrong?

### 7. ORPHANED/ARCHIVED CODE - Investigation
Look for code that was written but never connected:

```bash
# Search for:
- Files with "old", "backup", "v2", "deprecated" in name
- Services that exist but aren't imported anywhere
- API routes that exist but aren't registered
- Frontend pages that exist but aren't in navigation
- Database tables that exist but aren't used
```

**Key Question:** How much work was done but never connected?

---

## STRATEGIC QUESTIONS TO ANSWER

After your investigation, answer these:

1. **Is the architecture fundamentally sound?**
   - Or should we rebuild from scratch?

2. **What's the biggest bottleneck?**
   - Is it data quality? Code quality? Missing connections?

3. **What would give the most bang for buck?**
   - If we could only fix ONE thing, what should it be?

4. **Is the priority order correct?**
   - Are we fixing the right things first?

5. **What's being overlooked?**
   - Are there obvious problems nobody mentioned?

6. **Is this approach stupid?**
   - Be honest. If the architecture is wrong, say so.
   - If we're building the wrong thing, say so.
   - If there's a simpler way, say so.

---

## OUTPUT FORMAT

Create/update `.claude/SYSTEM_AUDIT_DEC1.md` with a new section:

```markdown
## AUDIT AGENT DEEP INVESTIGATION

**Investigation Date:** 2025-12-01
**Tokens Used:** [approximate]
**Files Examined:** [count]
**Queries Run:** [count]

### Executive Summary
[3-5 sentences on overall system health and viability]

### Vision Alignment Score: X/10
[How well does current system support Bill's vision?]
[Explain the score]

### Architecture Assessment
**Verdict:** [SOUND / NEEDS WORK / REBUILD]
[Explanation of why]

### The Real Problem
[What is actually blocking this system from working?]
[Root cause, not symptoms]

### Data Quality Report
| Table | Total Rows | Valid | Issues | Impact |
|-------|------------|-------|--------|--------|
| emails | ? | ? | ? | ? |
| contacts | ? | ? | ? | ? |
| ... | | | | |

### Hidden Issues Discovered
[Things NOT in the original 39 issues]

1. **[Issue Name]**
   - Location: [file path]
   - Impact: [High/Medium/Low]
   - Fix: [what to do]

### Dead/Orphaned Code Found
[List of files that exist but aren't connected]

### Critical Path to Working System
[In order, what MUST be fixed for the system to actually work]

1. [First thing]
2. [Second thing]
...

### What's Actually Good
[Things that ARE working and should be preserved]

### Strategic Recommendations

**If I were building this, I would:**
[Your honest opinion on approach]

**Quick wins that would have immediate impact:**
1. [win 1]
2. [win 2]

**Things that are waste of time right now:**
1. [thing 1]
2. [thing 2]

### Concerns About Current Plan
[Any risks or problems with the Wave 1 approach]

### Final Verdict
[1-2 paragraphs of honest assessment]
[Should we continue with current approach? Pivot? Rebuild?]
```

---

## IMPORTANT NOTES

1. **Be thorough** - Use lots of tokens. Read files. Run queries. Don't skim.
2. **Be honest** - If something is stupid, say it's stupid. Don't sugarcoat.
3. **Be specific** - File paths, line numbers, exact values.
4. **Be strategic** - Think about the big picture, not just individual bugs.
5. **Be actionable** - Every problem should have a suggested fix.

The user is frustrated because the system appears "done" but doesn't work. They need to understand WHY and WHAT to do about it.

---

## START YOUR INVESTIGATION

Begin by reading:
1. `.claude/SYSTEM_AUDIT_DEC1.md` (current audit)
2. `.claude/LIVE_STATE.md` (system state)
3. `CLAUDE.md` (project instructions)
4. `docs/roadmap.md` (priorities)

Then start your deep dive into each system.

Good luck.
