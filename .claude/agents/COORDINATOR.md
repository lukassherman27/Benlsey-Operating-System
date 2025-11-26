# Agent Coordinator Guide

**How to run the parallel agent system for BDS Operations Platform**

---

## Quick Start: Launch All Agents

Open **5 separate Claude terminal windows** and paste the appropriate instruction file into each.

### Terminal 1: Backend API Agent
```bash
# Copy-paste the contents of:
cat .claude/agents/agent1-backend-api.md
```

### Terminal 2: Frontend Agent
```bash
# Copy-paste the contents of:
cat .claude/agents/agent2-frontend.md
```

### Terminal 3: Deployment Agent
```bash
# Copy-paste the contents of:
cat .claude/agents/agent3-deployment.md
```

### Terminal 4: Data Pipeline Agent
```bash
# Copy-paste the contents of:
cat .claude/agents/agent4-data-pipeline.md
```

### Terminal 5: Intelligence Agent
```bash
# Copy-paste the contents of:
cat .claude/agents/agent5-intelligence.md
```

---

## Agent Dependencies & Execution Order

```
┌──────────────────────────────────────────────────────────────────┐
│                    PARALLEL EXECUTION                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Agent 1 (Backend) ─────────┐                                     │
│     P0: Transcript API      │                                     │
│     P0: Unified Timeline    ├──▶ Agent 2 (Frontend)               │
│     P1: RFI/Milestone APIs  │       WAITS for APIs, then:         │
│                             │       P0: Unified Timeline UI       │
│                             │       P0: Transcript Viewer         │
│                             │                                     │
│  Agent 3 (Deployment) ──────┼──▶ PARALLEL: Can start immediately  │
│     Setup Vercel/Railway    │    Just needs working app to deploy │
│                             │                                     │
│  Agent 4 (Data Pipeline) ───┼──▶ PARALLEL: Start immediately      │
│     Check transcriber       │    No code dependencies             │
│     Data quality            │                                     │
│                             │                                     │
│  Agent 5 (Intelligence) ────┴──▶ WAITS for Agent 1's transcript   │
│     Add transcripts to          API, then enhances query system   │
│     query context               │                                 │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Recommended Launch Order

1. **Start immediately (parallel):**
   - Agent 1: Backend API
   - Agent 3: Deployment
   - Agent 4: Data Pipeline

2. **Start after Agent 1 completes P0 tasks:**
   - Agent 2: Frontend (needs APIs)
   - Agent 5: Intelligence (needs transcript API)

---

## Coordination Checkpoints

### Checkpoint 1: APIs Ready (Day 1-2)
Agent 1 announces: "Meeting transcript and unified timeline APIs are ready"
- Agent 2 can begin frontend work
- Agent 5 can begin intelligence work

### Checkpoint 2: Deployment Ready (Day 1-3)
Agent 3 announces: "Frontend at [URL], Backend at [URL]"
- Everyone can test on deployed version
- Bill can start using

### Checkpoint 3: Data Quality Check (Day 2-3)
Agent 4 reports: "Data quality report attached, issues found: [list]"
- Other agents know about data limitations
- Plan workarounds if needed

### Checkpoint 4: Feature Complete (Day 5-7)
All agents report: "P0 and P1 tasks complete"
- Begin integration testing
- Schedule user testing with Bill

---

## File Ownership Quick Reference

| Agent | Owns | Do NOT Touch |
|-------|------|--------------|
| 1 Backend | `backend/` | frontend, scripts |
| 2 Frontend | `frontend/src/` | backend, database |
| 3 Deployment | configs, `.env` | app code |
| 4 Data Pipeline | `scripts/`, `voice_transcriber/`, migrations | API, frontend |
| 5 Intelligence | `query_brain.py`, AI services | core data pipeline |

---

## Communication Protocol

### When to Ask Coordinator
- Need to edit a file you don't own
- Blocked on another agent's work
- Found a bug in shared code
- Major architectural decision

### How to Communicate
- Announce completions clearly
- List any blockers immediately
- Update status in this doc or master plan

---

## Master Documents

- **Master Plan:** `docs/planning/MASTER_JANUARY_PLAN.md`
- **Sprint Plan:** `docs/planning/2_WEEK_SPRINT_DEC_2025.md`
- **Codebase Index:** `.claude/CODEBASE_INDEX.md`
- **Project Context:** `.claude/PROJECT_CONTEXT.md`

---

## Emergency Contacts

If agents conflict or system breaks:
1. Stop all work
2. Check git status
3. Identify which agent caused issue
4. Revert if needed
5. Re-coordinate

---

## Success Metrics

**By Dec 15:**
- [ ] All P0 tasks complete across all agents
- [ ] Bill has working URL to access
- [ ] Unified timeline shows real data
- [ ] Query includes meeting transcripts

**By Jan 15:**
- [ ] Production stable
- [ ] Bill using daily
- [ ] All P1 tasks complete
- [ ] RAG prep documentation done

---

**Created:** 2025-11-26
**Last Updated:** 2025-11-26
