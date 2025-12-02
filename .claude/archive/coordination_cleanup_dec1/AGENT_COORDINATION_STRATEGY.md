# Agent Coordination Strategy
## Making AI Agents Work Together Like a Neural Network

**Created:** 2025-11-27
**Purpose:** Solve the "disconnected building" problem where agents work in isolation

---

## The Core Problem You Described

> "I can start building something and it'll work and it'll be nice. But then it doesn't start to really get to that point where it's feeding off each other."

The issue isn't organization (you're at 9/10). The issue is **live state synchronization** between agents.

---

## The Solution: 4-Layer Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LAYER 1: BRAIN AGENT                         │
│                    (Strategic Direction & Planning)                 │
│  - Reads all planning/architecture docs                             │
│  - Decides WHAT should be built this week                           │
│  - Creates actionable task breakdowns                               │
│  - Reviews against long-term vision                                 │
│  OUTPUT: Updated CURRENT_SPRINT.md + task assignments               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LAYER 2: ORGANIZER AGENT                       │
│                   (Codebase Knowledge & Routing)                    │
│  - Knows WHERE every feature lives                                  │
│  - Routes tasks to correct files/services                           │
│  - Updates CODEBASE_INDEX after changes                             │
│  - Prevents duplicate/conflicting work                              │
│  OUTPUT: Task + exact file paths + dependencies                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LAYER 3: BUILDER AGENTS                        │
│                     (Specialized Implementation)                    │
│  - Agent 1: Backend (FastAPI, services, database)                   │
│  - Agent 2: Frontend (React, Next.js, UI)                           │
│  - Agent 3: Data Pipeline (imports, scripts, processing)            │
│  - Agent 4: Intelligence (AI, queries, learning)                    │
│  OUTPUT: Working code + SESSION_LOG entry                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LAYER 4: SYNC AGENT                            │
│                  (State Management & Coordination)                  │
│  - Runs AFTER every builder session                                 │
│  - Updates all context files                                        │
│  - Logs what changed                                                │
│  - Commits to git with structured messages                          │
│  - Prepares context for next agent                                  │
│  OUTPUT: Updated context files, git commit, next-agent briefing     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The Critical Missing Piece: LIVE_STATE.md

This is the file that ALL agents read at the start and the SYNC agent updates at the end:

```markdown
# LIVE_STATE.md - Agent Coordination Hub

**Last Updated:** 2025-11-27 14:32:00
**Updated By:** Sync Agent (after Backend session)

## Current Sprint (Nov 27 - Dec 11)
**Goal:** Complete Email Intelligence System + Admin UI

## What Was Just Completed
- [2025-11-27 14:30] Backend: Added GET /api/emails/suggestions endpoint
- [2025-11-27 14:30] Backend: Fixed email_project_links table schema
- [2025-11-27 12:00] Data Pipeline: Linked 847 additional emails (total: 3,137/3,356)

## What's In Progress
- Frontend: Admin suggestion review UI (BLOCKED - waiting for endpoint)
- Intelligence: Query context aggregation (25% complete)

## What's Blocked
- [ ] Frontend admin UI - UNBLOCKED as of 14:30, endpoint ready
- [ ] Invoice reconciliation - Waiting for finance team Excel

## Next Up (Ready to Build)
1. **Frontend** - Admin suggestion review UI
   - Files: `frontend/src/app/admin/suggestions/page.tsx`
   - API: `GET /api/emails/suggestions` (NOW READY)
   - Dependencies: None remaining

2. **Intelligence** - Complete context aggregation
   - Files: `backend/services/context_service.py`
   - Depends on: Email linking (91% done, proceed)

## Database State
- Emails: 3,356 total, 3,137 linked (93.5%)
- Suggestions: 801 pending review
- Projects: 54 active
- Last migration: 070_add_suggestion_columns.sql

## API Endpoints Changed Today
- NEW: GET /api/emails/suggestions
- NEW: POST /api/emails/suggestions/{id}/approve
- MODIFIED: GET /api/emails - added `has_suggestion` filter

## Files Changed Today
- backend/api/main.py (lines 4521-4650)
- backend/services/email_intelligence_service.py (new methods)
- database/migrations/070_add_suggestion_columns.sql
```

---

## How This Works in Practice

### Starting a Session (ANY Agent)

1. **Read LIVE_STATE.md first** - Know what just happened
2. **Read your agent file** - Know your responsibilities
3. **Check blockers** - Can you proceed?
4. **Check "Next Up"** - What's ready for you?

### During a Session

1. Work on your assigned task
2. Don't touch files you don't own
3. If you need something from another agent, note it in your work

### Ending a Session

1. **Log what you did** in SESSION_LOG format
2. **Call the Sync Agent** (or do it yourself)
3. **Sync Agent updates:**
   - LIVE_STATE.md
   - CODEBASE_INDEX.md (if files added)
   - Git commit with structured message

---

## The Sync Protocol

After EVERY builder session, run this sync:

```bash
# In Claude Code, the Sync Agent does:

1. Read git diff to see what changed
2. Update LIVE_STATE.md:
   - Move "In Progress" items to "Completed"
   - Update "Database State" if schema changed
   - Update "API Endpoints Changed" if routes added
   - Add to "Files Changed Today"
   - Check if anything is now unblocked
3. Update CODEBASE_INDEX.md if new files/features added
4. Git commit with message format:
   "feat(agent-backend): Add email suggestions API

   - GET /api/emails/suggestions endpoint
   - POST /api/emails/suggestions/{id}/approve
   - Migration 070 for suggestion columns

   Unblocks: Frontend admin UI
   Next: Frontend can now build suggestion review"
```

---

## Your Meeting Transcription Example

You mentioned wanting meeting transcriptions to automatically update context. Here's how:

```
┌────────────────────────────────────────────────────────┐
│ You transcribe meeting with Sarah (project manager)    │
└────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ Data Pipeline Agent processes transcript               │
│ - Extracts: mentions of other projects                 │
│ - Extracts: relationship info about Sarah              │
│ - Extracts: action items for BK-070 project            │
└────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ Intelligence Agent categorizes & routes                │
│ - Project-specific items → project_meetings table      │
│ - Relationship info → contact_notes table              │
│ - Cross-project opportunities → separate tracking      │
└────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ Sync Agent updates context                             │
│ - Sarah's contact record: "Has other projects to discuss" │
│ - BK-070 context: "Meeting held Nov 27, next steps..." │
│ - LIVE_STATE: "New meeting context available"          │
└────────────────────────────────────────────────────────┘
```

---

## Practical Implementation: What to Do Now

### Step 1: Create LIVE_STATE.md (Today)

Create `.claude/LIVE_STATE.md` with current system state.

### Step 2: Create the Sync Agent (Today)

Add `.claude/agents/sync-agent.md` with sync protocol.

### Step 3: Create Brain Agent Prompt (Today)

Add `.claude/agents/brain-agent.md` for strategic planning.

### Step 4: Update Your Workflow

**Before EVERY Claude Code session:**
```bash
# Start with this command:
"Read .claude/LIVE_STATE.md and tell me what needs to be done next"
```

**After EVERY Claude Code session:**
```bash
# End with this command:
"Act as the Sync Agent. Update LIVE_STATE.md, CODEBASE_INDEX.md, and commit changes."
```

### Step 5: Weekly Brain Agent Session

Once per week:
```bash
"Act as the Brain Agent. Review all planning docs, current progress, and create next week's CURRENT_SPRINT.md"
```

---

## Why This Will Work

1. **Single Source of Truth**: LIVE_STATE.md is always current
2. **Automatic Routing**: Organizer knows where everything goes
3. **No Isolation**: Every agent sees what others did
4. **Git as Memory**: Structured commits preserve context
5. **Unblock Detection**: Sync agent identifies when blockers clear

---

## What You DON'T Need

1. **Complex orchestration software** - Claude Code + files is enough
2. **Multiple windows simultaneously** - Sequential is fine with good state
3. **External databases for coordination** - .md files are perfect
4. **Fancy tooling** - You just need discipline + the right files

---

## The Key Insight

Your agents don't need to talk to each other in real-time. They need to:
1. **Read state** before starting
2. **Write state** after finishing
3. **Trust the state** is accurate

That's it. That's the whole system.

---

## Next Steps

1. I'll create LIVE_STATE.md with your current state
2. I'll create the Brain Agent prompt
3. I'll create the Sync Agent prompt
4. I'll update the Organizer Agent to use LIVE_STATE
5. You try it with your next session

Ready to implement?
