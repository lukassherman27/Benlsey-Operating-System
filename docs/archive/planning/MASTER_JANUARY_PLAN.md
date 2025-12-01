# BDS Operations Platform: Master Plan to January Launch

**Created:** November 26, 2025
**Target Launch:** January 15, 2026
**Status:** Active Development

---

## Executive Summary

Transform the BDS database into a fully operational "Bensley Machine" that:
1. Shows Bill everything about proposals and projects in one place
2. Auto-transcribes meetings and links them to projects
3. Tracks RFIs, invoices, and milestones
4. Answers natural language questions about project history
5. Runs on a server accessible from anywhere

---

## Timeline Overview

```
Nov 26 ─────────── Dec 15 ─────────── Jan 1 ─────────── Jan 15
   │                   │                  │                 │
   │ HEAVY DEV         │ POLISH           │ FINAL PUSH      │
   │ (3 weeks)         │ (2 weeks)        │ (2 weeks)       │
   │                   │                  │                 │
   ▼                   ▼                  ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Week 1-3: Features    Week 4-5: Testing    Week 6-7: Launch│
│ - Unified Timeline    - User testing       - Final bugs    │
│ - Meeting Transcripts - Mobile polish      - Deployment    │
│ - RFI/Milestone UI    - Performance        - Bill training │
│ - Deployment Setup    - Data cleanup       - Go Live!      │
└─────────────────────────────────────────────────────────────┘
```

---

## Parallel Agent Workstreams

### Why Parallel Agents?
- **5 independent workstreams** that don't block each other
- Each agent owns specific files/directories
- Clear handoff points between agents
- Run in separate Claude terminal windows

### Agent Overview

| Agent | Focus | Files Owned | Dependencies |
|-------|-------|-------------|--------------|
| **Agent 1: Backend API** | New endpoints | `backend/api/`, `backend/services/` | None (start first) |
| **Agent 2: Frontend** | Dashboard UI | `frontend/src/` | Needs APIs from Agent 1 |
| **Agent 3: Deployment** | Vercel + Railway | `vercel.json`, `railway.json`, configs | Needs working app |
| **Agent 4: Data Pipeline** | Email imports, transcriber | `scripts/`, `voice_transcriber/` | Database access |
| **Agent 5: Intelligence** | Query interface, RAG prep | `scripts/core/query_brain.py` | Phase 2 prep |

### Coordination Rules
1. **Don't edit files you don't own** - ask coordinator to reassign
2. **Check in before major changes** - update this doc or ask
3. **Test your changes** - don't break other agents' work
4. **Document new endpoints/components** - update CODEBASE_INDEX.md

### Support Agents
| Agent | Role | Invoke When |
|-------|------|-------------|
| **Organizer** | File finding, structure, archiving | "Where is X?", cleanup needed |
| **Coordinator** | Cross-agent planning, conflicts | Blocked, need reassignment |

Organizer prompt: `.claude/agents/organizer.md`

---

## Coordination Tools

| Command | Purpose |
|---------|---------|
| `make health-check` | Verify codebase (28 checks) - RUN BEFORE COMMITS |
| `make todos` | See all code TODOs |
| `make test` | Run pytest |
| `make db-stats` | Show data counts |

### Files to Update When Working
- `TODO.md` - Mark your agent's items complete
- `.claude/CODEBASE_INDEX.md` - Add new endpoints/components

### Shared Files (Coordinate Before Editing)
| File | Owner | Others Request Changes |
|------|-------|------------------------|
| `backend/api/main.py` | Agent 1 | via Coordinator |
| `frontend/src/lib/api.ts` | Agent 2 | via Coordinator |
| `database/migrations/` | Agent 4 | via Coordinator |

---

## Daily Sync Process

**End of each day:**
1. Each agent updates their section in `TODO.md`
2. Run `make health-check` - must stay at 100%
3. Note blockers in commit messages
4. Coordinator reviews overnight

---

## Phase 1: Heavy Development (Nov 26 - Dec 15)

### Week 1 (Nov 26 - Dec 2): Core Features

#### Agent 1: Backend API
| Priority | Task | Endpoint | Time Est |
|----------|------|----------|----------|
| P0 | Meeting transcripts API | `GET /api/meeting-transcripts` | 2h |
| P0 | Unified timeline API | `GET /api/projects/{code}/unified-timeline` | 3h |
| P1 | RFI list improvements | `GET /api/rfis` (add filters) | 1h |
| P1 | Milestones with dates | `GET /api/milestones` (add date filters) | 1h |
| P2 | Finance KPI endpoint | `GET /api/finance/kpis` (live data) | 2h |

#### Agent 2: Frontend Dashboard
| Priority | Task | Component | Time Est |
|----------|------|-----------|----------|
| P0 | Unified Timeline component | `unified-timeline.tsx` | 4h |
| P0 | Meeting Transcript viewer | `transcript-viewer.tsx` | 3h |
| P1 | RFI Tracker widget | `rfi-tracker-widget.tsx` | 2h |
| P1 | Milestones widget | `milestones-widget.tsx` | 2h |
| P2 | Projects page summary cards | Update `projects/page.tsx` | 2h |

#### Agent 3: Deployment
| Priority | Task | Details | Time Est |
|----------|------|---------|----------|
| P0 | Deploy frontend to Vercel | Setup, configure, deploy | 2h |
| P0 | Deploy backend to Railway | Setup, configure, deploy | 3h |
| P1 | Database strategy | SQLite on Railway or Turso | 2h |
| P1 | Environment variables | API keys, URLs | 1h |
| P2 | Custom domain (optional) | bensley-ops.vercel.app | 1h |

#### Agent 4: Data Pipeline
| Priority | Task | Script | Time Est |
|----------|------|--------|----------|
| P0 | Verify transcriber running | `voice_transcriber/transcriber.py` | 1h |
| P1 | Check email import status | `backend/services/email_importer.py` | 1h |
| P1 | RFI data quality check | SQL queries, fix data | 2h |
| P2 | Milestone data backfill | Add planned_date to milestones | 2h |

#### Agent 5: Intelligence
| Priority | Task | Details | Time Est |
|----------|------|---------|----------|
| P1 | Add transcripts to query context | Update `query_brain.py` | 2h |
| P2 | Test query with project history | "What did client say about X?" | 1h |
| P2 | Document RAG requirements | For Phase 2 | 2h |

### Week 2 (Dec 3 - Dec 9): Integration & Polish

#### Agent 1: Backend API
- Wire up unified timeline to communication_log
- Add action items endpoint from transcripts
- Performance optimization (indexes, caching)

#### Agent 2: Frontend Dashboard
- Integrate unified timeline into Project Detail page
- Add query box to project pages
- Mobile responsiveness fixes
- Loading states and error handling

#### Agent 3: Deployment
- Test deployed app end-to-end
- Fix any deployment-specific bugs
- Set up monitoring/logs
- Document deployment process

#### Agent 4: Data Pipeline
- Import any pending emails
- Verify all transcripts linked to projects
- Data quality report

#### Agent 5: Intelligence
- Test query interface with real questions
- Improve prompt for better answers
- Log all queries for training data

### Week 3 (Dec 10 - Dec 15): User Testing & Iteration

**All Agents:** Support user testing with Bill
- Collect feedback
- Fix critical bugs
- Don't add new features (stabilize)

---

## Phase 2: Polish & Data Collection (Dec 16 - Jan 1)

### Holiday Period Focus
- **Light development** - bug fixes only
- **Data collection** - ensure transcriber/email import running
- **Documentation** - update all docs
- **RAG prep** - plan embeddings, test ChromaDB locally

### Tasks by Agent

#### Agent 1: Backend API
- [ ] Bug fixes from user testing
- [ ] Add any missing filters/sorts
- [ ] Optimize slow queries

#### Agent 2: Frontend
- [ ] Bug fixes from user testing
- [ ] Final mobile polish
- [ ] Add "last updated" timestamps

#### Agent 3: Deployment
- [ ] Monitor uptime
- [ ] Set up backup strategy
- [ ] Document recovery process

#### Agent 4: Data Pipeline
- [ ] Ensure continuous data import
- [ ] Weekly data quality checks
- [ ] Backfill any missing data

#### Agent 5: Intelligence
- [ ] Install Ollama locally (test)
- [ ] Test ChromaDB with sample data
- [ ] Document Phase 2 implementation plan

---

## Phase 3: Final Push & Launch (Jan 1 - Jan 15)

### Week 6 (Jan 1 - Jan 7): Final Features

#### Agent 1: Backend API
- [ ] Any remaining endpoint requests from Bill
- [ ] Performance final pass
- [ ] Security review

#### Agent 2: Frontend
- [ ] Final UI polish
- [ ] Add help/tooltips
- [ ] Accessibility check

#### Agent 3: Deployment
- [ ] Production hardening
- [ ] Set up alerts
- [ ] Backup verification

#### Agent 4: Data Pipeline
- [ ] Final data import push
- [ ] Data quality final check
- [ ] Document data sources

#### Agent 5: Intelligence
- [ ] Query interface improvements
- [ ] Begin RAG implementation (if time)

### Week 7 (Jan 8 - Jan 15): Launch

- [ ] Final testing with Bill
- [ ] Training session for Bill
- [ ] Go Live announcement
- [ ] Monitor first week of usage
- [ ] Fix any critical issues

---

## Current System State (Reference)

### Database Tables
| Table | Records | Status |
|-------|---------|--------|
| projects | 54 | Good |
| proposals | 89 | Good |
| invoices | 253 | Good |
| emails | 3,356 | Good |
| meeting_transcripts | 10 | Growing |
| communication_log | 321 | Good |
| rfis | 3 | Sparse |
| project_milestones | 110 | Need dates |

### API Endpoints
- **93+ endpoints** already built
- Missing: `/api/meeting-transcripts`, `/api/unified-timeline`

### Frontend Pages
| Page | Status |
|------|--------|
| Main Dashboard `/` | 95% |
| Proposal Tracker `/tracker` | 100% |
| Projects `/projects` | 80% |
| Finance `/finance` | 60% |
| Project Detail `/projects/[code]` | 85% |

### Voice Transcriber
- **Location:** `voice_transcriber/transcriber.py`
- **Status:** Working, 10 transcripts processed
- **Features:** Whisper + Claude, auto-links to projects

---

## Success Metrics

### By Dec 15 (End of Phase 1):
- [ ] Bill can access dashboards from URL (not localhost)
- [ ] Unified timeline shows emails + meetings + RFIs
- [ ] Query "What happened with project X?" works
- [ ] Mobile-friendly

### By Jan 1 (End of Phase 2):
- [ ] 50+ meeting transcripts in database
- [ ] Zero critical bugs
- [ ] Data quality >90%
- [ ] RAG system designed

### By Jan 15 (Launch):
- [ ] Bill uses daily without issues
- [ ] Saves 5-10 hours/week vs old workflow
- [ ] All project history queryable
- [ ] System runs reliably 24/7

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Finance data never arrives | Ship with current data, add disclaimer |
| RFI/Milestone data sparse | Build UI anyway, data backfills later |
| Deployment issues | Start deployment Week 1, not Week 3 |
| Bill has major UX concerns | User test early (Dec 7), iterate |
| Performance problems | Add indexes, test with real data |

---

## Quick Reference: File Ownership

### Agent 1: Backend API
```
backend/api/main.py
backend/services/*.py
backend/models/*.py
```

### Agent 2: Frontend
```
frontend/src/app/
frontend/src/components/
frontend/src/lib/
```

### Agent 3: Deployment
```
frontend/vercel.json (create)
backend/railway.json (create)
backend/Procfile (create)
.env files
```

### Agent 4: Data Pipeline
```
voice_transcriber/
scripts/core/
scripts/imports/
database/migrations/
```

### Agent 5: Intelligence
```
scripts/core/query_brain.py
scripts/core/smart_email_brain.py
backend/services/ai_*.py
```

---

## Next Steps

1. **Read your agent instructions** in `.claude/agents/`
2. **Start with P0 tasks** - don't skip to fun stuff
3. **Check in when blocked** - don't spin
4. **Test your changes** - don't break others

---

**See individual agent files for detailed instructions:**
- `.claude/agents/agent1-backend-api.md`
- `.claude/agents/agent2-frontend.md`
- `.claude/agents/agent3-deployment.md`
- `.claude/agents/agent4-data-pipeline.md`
- `.claude/agents/agent5-intelligence.md`

---

**Last Updated:** 2025-11-26
**Status:** Ready for parallel execution
