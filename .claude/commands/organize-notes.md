# Organize Notes

Parse unstructured notes/thoughts and organize them into the appropriate SSOT files in the Bensley Operating System.

## How to Use

1. Paste your notes/thoughts after this command is invoked
2. I will parse and categorize each item
3. You'll see a preview of proposed changes
4. Reply "yes" to confirm, or specify which items to skip/modify

## What This Does

Parses unstructured input to identify:
- **Tasks** - Action items, TODOs, work to be done → `docs/roadmap.md`
- **Bugs** - Things that are broken, errors, issues → `.claude/STATUS.md`
- **Features** - Ideas for new capabilities → `docs/roadmap.md` (Backlog)
- **Context Updates** - New info about business, architecture, data → `docs/context/*.md`
- **Questions** - Items needing clarification → I'll ask you

## Classification Rules

| Signal | Type | Destination |
|--------|------|-------------|
| "TODO", "need to", "should", action verbs | Task | `docs/roadmap.md` → Backlog |
| "broken", "error", "bug", "doesn't work" | Bug | `.claude/STATUS.md` → What's Broken |
| "would be nice", "idea:", "feature:" | Feature | `docs/roadmap.md` → Backlog (labeled) |
| Facts about business, architecture, data | Context | Appropriate `docs/context/*.md` |
| "?", "what is", "how does", unclear | Question | Ask for clarification |

## Context Routing

| Signal | Route To |
|--------|----------|
| API, endpoint, service, backend, FastAPI | `docs/context/backend.md` |
| Page, component, UI, frontend, React, Next.js | `docs/context/frontend.md` |
| Database, table, migration, SQL, data quality | `docs/context/data.md` |
| AI, suggestion, learning, OpenAI, intelligence | `docs/context/ai_agents.md` |
| Bensley, Bill, studio, client, voice, tone | `docs/context/business.md` |
| System, architecture, tech stack, deployment | `docs/context/architecture.md` |

## Priority Rules

| Signal | Priority |
|--------|----------|
| "urgent", "blocking", "critical", "ASAP" | P0 (Current Sprint) |
| "important", "soon", "this sprint" | P1 (Backlog - high) |
| "eventually", "nice to have", "backlog" | P2 (Backlog - low) |
| No signal | P1 (default) |

## Instructions for Claude

When the user pastes their notes:

1. **Parse** each distinct item (separated by newlines, bullets, or natural breaks)

2. **Classify** each item:
   - Determine type (task/bug/feature/context/question)
   - Determine priority (P0/P1/P2)
   - Determine destination file and section

3. **Check for duplicates**:
   - If similar info already exists in SSOT, note it
   - Don't create duplicate entries

4. **Present findings** in this format:

```
## Parsed Notes Summary

### Tasks Found (X items)
1. **[P0]** [Task description] → `docs/roadmap.md` (Current Sprint)
2. **[P1]** [Task description] → `docs/roadmap.md` (Backlog)

### Bugs Found (X items)
1. [Bug description] → `.claude/STATUS.md` (What's Broken)

### Context Updates (X items)
1. [Info] → `docs/context/backend.md` (Section: [name])

### Feature Ideas (X items)
1. [Feature] → `docs/roadmap.md` (Backlog - Feature)

### Questions (need clarification)
1. [Question] - Please clarify: [what's unclear]

---

## Proposed Changes

### File: `docs/roadmap.md`
**Section:** Backlog
**Action:** Add items
```markdown
[exact markdown to add]
```

### File: `.claude/STATUS.md`
**Section:** What's Broken / Needs Work
**Action:** Add rows
```markdown
| [Issue] | [Impact/Notes] |
```

[...repeat for each file...]

---

**Ready to apply these changes?** Reply "yes" to confirm, or specify which items to skip/modify.
```

5. **Wait for user confirmation** before making any edits

6. **After confirmation**, apply edits to each file in sequence

## Example

**User input:**
```
Random notes from today:

- Email sync is broken again, IMAP LOGIN error keeps happening
- Need to add a calendar page to the frontend
- Bill mentioned we should track Shinta Mani Foundation separately from design projects
- TODO: fix the contact extraction to handle emails with no display name
- the suggestion approval UI could show a preview of what will change (idea)
- what's the difference between proposals and projects again?
- learned that invoice codes follow format I24-XXX where 24 is the year
```

**Expected output:**
- 2 Tasks → roadmap.md Backlog
- 1 Bug → STATUS.md
- 1 Feature → roadmap.md Backlog
- 1 Context update → business.md or data.md
- 1 Question → Answer immediately (already documented)
- 1 Already documented → Skip

## User Input

[User pastes their unstructured notes here]
