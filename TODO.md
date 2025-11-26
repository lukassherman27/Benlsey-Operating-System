# TODO Tracker

**Auto-generated: 2025-11-26** | Run `make todos` to refresh

**Master Plan:** `docs/planning/MASTER_JANUARY_PLAN.md`

---

## 📊 Summary

| Agent | TODOs | Priority | Plan Reference |
|-------|-------|----------|----------------|
| Agent 1: Backend API | 4 | High | Week 1 P0 tasks |
| Agent 2: Frontend | 4 | High | Week 1 P0 tasks |
| Agent 3: Deployment | 0 | Week 1 | New work |
| Agent 4: Data Pipeline | 1 | Medium | Ongoing |
| Agent 5: Intelligence | 0 | Week 1-2 | New work |
| Organizer | 0 | Ongoing | Maintenance |

**Total: 9 code TODOs + Plan tasks**

---

## Agent 1: Backend API

**Prompt:** `.claude/agents/agent1-backend-api.md`
**Owns:** `backend/`

### Code TODOs
| File | Line | TODO | Priority |
|------|------|------|----------|
| `backend/api/main.py` | 412 | Add logic for detecting wins from emails/payments | P1 |
| `backend/api/main.py` | 3496 | Implement payment schedule | P2 |
| `backend/api/main.py` | 3502 | Implement blockers tracking | P2 |
| `backend/api/main.py` | 3503 | Implement task tracking | P2 |

### Plan Tasks (Week 1)
- [ ] P0: Meeting transcripts API (`GET /api/meeting-transcripts`)
- [ ] P0: Unified timeline API (`GET /api/projects/{code}/unified-timeline`)
- [ ] P1: RFI list improvements (add filters)
- [ ] P1: Milestones with date filters
- [ ] P2: Finance KPI endpoint (live data)

---

## Agent 2: Frontend

**Prompt:** `.claude/agents/agent2-frontend.md`
**Owns:** `frontend/src/`

### Code TODOs
| File | Line | TODO | Priority |
|------|------|------|----------|
| `frontend/src/components/dashboard/dashboard-page.tsx` | 67 | Replace with proper empty states and error handling | P1 |
| `frontend/src/components/dashboard/invoice-quick-actions.tsx` | 21 | Hook these up to actual functions | P1 |
| `frontend/src/components/dashboard/payment-velocity-widget.tsx` | 13 | Hook this up to real API endpoint | P2 |
| `frontend/src/components/proposal-quick-edit-dialog.tsx` | 164 | Replace with actual user from auth system | Phase 3 |

### Plan Tasks (Week 1)
- [ ] P0: Unified Timeline component (`unified-timeline.tsx`)
- [ ] P0: Meeting Transcript viewer (`transcript-viewer.tsx`)
- [ ] P1: RFI Tracker widget
- [ ] P1: Milestones widget
- [ ] P2: Projects page summary cards

---

## Agent 3: Deployment

**Prompt:** `.claude/agents/agent3-deployment.md`
**Owns:** Deployment configs, CI/CD

### Code TODOs
None - new work

### Plan Tasks (Week 1)
- [ ] P0: Deploy frontend to Vercel
- [ ] P0: Deploy backend to Railway
- [ ] P1: Database strategy (SQLite on Railway or Turso)
- [ ] P1: Environment variables setup
- [ ] P2: Custom domain (optional)

---

## Agent 4: Data Pipeline

**Prompt:** `.claude/agents/agent4-data-pipeline.md`
**Owns:** `scripts/`, `voice_transcriber/`, `database/migrations/`

### Code TODOs
| File | Line | TODO | Priority |
|------|------|------|----------|
| `backend/services/schedule_email_parser.py` | 277 | Match nickname to member_id from team_members table | P2 |

### Plan Tasks (Week 1)
- [ ] P0: Verify transcriber running
- [ ] P1: Check email import status
- [ ] P1: RFI data quality check
- [ ] P2: Milestone data backfill (add planned_date)

---

## Agent 5: Intelligence

**Prompt:** `.claude/agents/agent5-intelligence.md`
**Owns:** `scripts/core/query_brain.py`, `backend/services/ai_*.py`

### Code TODOs
| File | Line | TODO | Priority |
|------|------|------|----------|
| `backend/services/training_data_service.py` | 71 | Get from auth context (hardcoded 'bill') | Phase 3 |

### Plan Tasks (Week 1-2)
- [ ] P1: Add transcripts to query context
- [ ] P2: Test query with project history
- [ ] P2: Document RAG requirements for Phase 2

---

## 🗂️ Organizer Agent

**Prompt:** `.claude/agents/organizer.md`
**Owns:** File structure, archives, cleanup

### Ongoing Tasks
- [ ] Weekly: Run `make health-check`
- [ ] Weekly: Update this TODO.md
- [ ] After each sprint: Archive completed agent files
- [ ] Monthly: Review unused scripts for archival

### Completed
- [x] Archive old agent files to `.claude/agents/archive/`
- [x] Archive old docs/agents files to `docs/agents/archive/`
- [x] Update CODEBASE_INDEX.md with agent references

---

## Quick Commands

```bash
make todos          # Scan codebase for TODOs
make health-check   # Run 28 automated checks
make test           # Run pytest
cat TODO.md         # See this file
```

---

## Adding New TODOs

When adding TODOs to code, use this format:
```python
# TODO(agent-1): Description of what needs to be done
# TODO(agent-2): Frontend task
```

Filter by agent:
```bash
grep -rn "TODO(agent-1)" backend/
grep -rn "TODO(agent-2)" frontend/
```

---

## Completed TODOs

*Move items here when done, with date and agent*

| Date | Agent | Description |
|------|-------|-------------|
| 2025-11-26 | Organizer | Archive old agent files |
| 2025-11-26 | Organizer | Create TODO.md tracker |

---

**Last Updated:** 2025-11-26
**Next Review:** End of Week 1 (Dec 2)
