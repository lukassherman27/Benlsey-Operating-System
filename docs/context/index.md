# Context Index - Single Source of Truth

**Owner:** Organizer Agent
**Last Updated:** 2025-12-01
**Purpose:** Quick pointers to all context bundles and key files

---

## ⚠️ DO NOT CREATE NEW FILES

**All agents MUST follow these rules:**

1. **NEVER create new planning/architecture/session docs** → Update `docs/roadmap.md`
2. **NEVER create new context docs** → Update existing `docs/context/*.md`
3. **NEVER create new agent docs** → Update `docs/agents/registry.md`
4. **Historical/completed work** → Archive to `docs/archive/`

**Allowed files outside archive:**
- `docs/roadmap.md` - Sprint goals & priorities
- `docs/context/*.md` - These 8 context bundles
- `docs/agents/registry.md` + `task-pack-template.md`
- `docs/guides/DESIGN_SYSTEM.md`
- `docs/processes/runbooks.md`
- `docs/tasks/*.md` - Active task packs only
- `.claude/STATUS.md` + `.claude/commands/*.md`

**If you find stale info:** Fix it in place, don't create a new file.

---

## Context Bundles

| Bundle | Path | Description | Last Updated |
|--------|------|-------------|--------------|
| **Business** | `docs/context/business.md` | **Bensley studio overview, services, voice/tone** | 2025-11-30 |
| **Workspaces** | `docs/context/workspaces.md` | **Multi-context OS: BDS, Shinta Mani, Personal** | 2025-11-30 |
| Architecture | `docs/context/architecture.md` | System diagram, data flows, tech decisions | 2025-11-27 |
| Backend | `docs/context/backend.md` | API endpoints, services, models | 2025-11-27 |
| Frontend | `docs/context/frontend.md` | Pages, components, state management | 2025-11-27 |
| AI/Agents | `docs/context/ai_agents.md` | OpenAI integration, suggestion handlers | 2025-12-01 |
| Data | `docs/context/data.md` | DB schema (115 tables), migrations | 2025-12-01 |

---

## Key Files Quick Reference

### Configuration
| File | Purpose |
|------|---------|
| `.env` | Environment variables (secrets) |
| `.env.example` | Template for .env |
| `Makefile` | Build/run commands |
| `docker-compose.yml` | Container orchestration |

### Backend
| File | Purpose |
|------|---------|
| `backend/api/main.py` | Main API entry (255 lines, 28 routers) |
| `backend/services/*.py` | Business logic (46 services) |
| `backend/core/bensley_brain.py` | Unified AI context |

### Frontend
| File | Purpose |
|------|---------|
| `frontend/src/app/(dashboard)/` | Dashboard pages |
| `frontend/src/components/` | React components |
| `frontend/src/lib/api.ts` | API client |
| `frontend/src/lib/types.ts` | TypeScript types |

### Database
| File | Purpose |
|------|---------|
| `database/bensley_master.db` | SQLite master (107MB) |
| `database/migrations/*.sql` | 72 migrations |
| `database/schema.sql` | Initial schema |

### Scripts
| File | Purpose |
|------|---------|
| `scripts/core/smart_email_brain.py` | Email AI processor |
| `scripts/core/query_brain.py` | Natural language queries |
| `scripts/core/email_linker.py` | Email-project linking |
| `scripts/core/contact_project_linker.py` | Contact→project suggestion generator |
| `scripts/core/transcript_linker.py` | Transcript→proposal suggestion generator |

### Documentation
| File | Purpose |
|------|---------|
| `docs/roadmap.md` | Current sprint & priorities |
| `docs/agents/registry.md` | Agent definitions |
| `docs/processes/runbooks.md` | How-to guides |
| `CLAUDE.md` | AI assistant context |

---

## Task Packs (Active Work)

| Task Pack | Assigned To | Priority | Status |
|-----------|-------------|----------|--------|
| `docs/tasks/backend-router-refactor.md` | Backend Builder | P0 | Ready |
| `docs/tasks/ux-design-system.md` | UX Architect | P0 | Done |
| `docs/tasks/connect-orphaned-services.md` | Backend Builder | P0 | Ready |
| `docs/tasks/cli-to-api-wrappers.md` | Backend Builder | P0 | Ready |
| `docs/tasks/missing-frontend-pages.md` | Frontend Builder | P1 | Ready |
| `docs/tasks/api-standardization.md` | Backend Builder | P1 | Ready |

**Sprint Goals:** See `docs/roadmap.md`

---

## Where to Find Things

### "How do I..."
- **...run the app?** → `docs/processes/runbooks.md`
- **...add an API endpoint?** → `docs/context/backend.md`
- **...create a frontend page?** → `docs/context/frontend.md`
- **...process emails?** → `docs/context/ai_agents.md`
- **...understand the database?** → `docs/context/data.md`

### "What is the current..."
- **...sprint goal?** → `docs/roadmap.md`
- **...system architecture?** → `docs/context/architecture.md`
- **...database schema?** → `docs/context/data.md`
- **...API surface?** → `docs/context/backend.md`

### "Who handles..."
- **...backend work?** → Backend Builder Agent
- **...frontend work?** → Frontend Builder Agent
- **...data imports?** → Data Pipeline Agent
- **...AI features?** → Intelligence Agent
- **...deployment?** → Ops Agent
- **...planning?** → Brain Agent
- **...file organization?** → Organizer Agent

---

## Recent Changes Log

| Date | File | Change | Agent |
|------|------|--------|-------|
| 2025-12-01 | `scripts/core/contact_project_linker.py` | Contact→project linking pipeline (89 suggestions) | Data Pipeline |
| 2025-12-01 | `backend/services/suggestion_handlers/contact_link_handler.py` | Handler for contact_link suggestions | Backend |
| 2025-12-01 | `backend/services/learning_service.py` | Added email pattern learning loop (learns from approved suggestions) | Intelligence |
| 2025-12-01 | `database/migrations/051_learned_patterns.sql` | New tables: email_learned_patterns, email_pattern_usage_log | Intelligence |
| 2025-12-01 | **SSOT Consolidation** | Archived 250+ files → 20 remain in docs/, 2 in .claude/ | Organizer |
| 2025-12-01 | `CLAUDE.md` | Added SSOT enforcement rules | Organizer |
| 2025-12-01 | `docs/context/index.md` | Added DO NOT CREATE NEW FILES warning | Organizer |
| 2025-11-30 | `docs/context/workspaces.md` | Created multi-context OS documentation | Investigation |
| 2025-11-30 | `docs/context/business.md` | Created Bensley studio context | Business Context |
| 2025-11-28 | `docs/tasks/*.md` | Created 6 task packs | Brain |
| 2025-11-27 | SSOT files | Created: roadmap.md, registry.md, index.md, runbooks.md | Various |

---

## Integration Status

### Backend → Frontend Coverage
| API Area | Endpoints | Has Frontend | Gap |
|----------|-----------|--------------|-----|
| Proposals | 16 | Yes | - |
| Projects | 12 | Partial | Timeline, details |
| Emails | 8 | Partial | Suggestions UI |
| Meetings | 5 | No | Full page needed |
| Calendar | 4 | No | Full page needed |
| Contracts | 6 | No | Full page needed |
| RFIs | 3 | Partial | Dashboard needed |
| Audit | 6 | No | Admin section |
| Training | 4 | No | Admin section |

### Services → API Coverage
| Service | In main.py | Endpoints |
|---------|------------|-----------|
| proposal_tracker_service | Yes | 16 |
| email_service | Yes | 8 |
| query_service | Yes | 5 |
| document_service | **NO** | 0 |
| email_importer | **NO** | 0 |
| project_creator | **NO** | 0 |
| meeting_briefing_service | **NO** | 0 |
| schedule_* (4 files) | **NO** | 0 |
| excel_importer | **NO** | 0 |

---

## Notes for Organizer Agent

When updating this file:
1. Update "Last Updated" date on context bundles when they change
2. Add to "Recent Changes Log" for significant updates
3. Keep "Integration Status" current after API/frontend changes
4. Ensure all new files get added to appropriate section
