# Roadmap - Single Source of Truth

**Owner:** Brain/Planner Agent
**Last Updated:** 2025-12-01 18:00
**Update Frequency:** Twice weekly minimum

---

## Vision (3-Month)

Build an AI-powered operations platform for Bensley Design Studios that:
- Tracks proposals (sales) and projects (delivery) in unified dashboards
- Enables natural language queries ("What's happening with BK-070?")
- Automates data entry via email/meeting intelligence
- Reduces Bill's manual tracking by 10+ hours/week

---

## Current Phase

**Phase 1.5:** Integration & Data Quality (Nov 27 - Dec 15)
**Status:** 95% backend working, 90% frontend connected

---

## This Sprint: Dec 1-15 - "Proposal Intelligence for Bill"

### Sprint Goal
Generate weekly proposal status reports for Bill using linked data

**Focus:** Data linking (transcripts→proposals, emails→proposals) + report generation - NOT fancy AI

### Agents

| Agent | Responsibility | Pages |
|-------|----------------|-------|
| UX Architect | Design system, tokens, standards | All |
| Frontend Builder 1 | Proposals polish | /tracker, / |
| Frontend Builder 2 | Projects polish | /projects |
| Frontend Builder 3 | Suggestions polish | /suggestions, /admin/* |
| Backend Integrator | API contracts, consistency | All APIs |
| Organizer | Context updates | docs/ |

### Priorities (in order)

| # | Task | Owner | Status | Target |
|---|------|-------|--------|--------|
| 1 | Rebuild email→proposal links | Data Pipeline | ✅ DONE | Dec 1 |
| 2 | Rebuild email→project links | Data Pipeline | ✅ DONE | Dec 1 |
| 3 | Generate weekly proposal status report | Intelligence | ✅ DONE | Dec 1 |
| 4 | AI Suggestions handler framework | Backend | ✅ Week 1 DONE | Dec 1 |
| 5 | AI Suggestions handler integration + learning loop | Backend | ✅ Week 2 DONE | Dec 1 |
| 6 | Link transcripts → proposals (via suggestions) | Data Pipeline | Not Started | Day 5 |
| 7 | Extract contacts from emails/transcripts | Data Pipeline | 🔄 89 suggestions | Day 7 |
| 8 | Draft follow-up email with context | Intelligence | Not Started | Day 12 |

### Acceptance Criteria
- [ ] Transcripts linked to proposals via suggestions (never auto-link)
- [ ] 90%+ emails linked to proposals
- [ ] Contacts extracted and enriched from email/transcript data
- [ ] Weekly proposal report generates with full context
- [ ] Can draft follow-up email for any proposal with context
- [ ] Can draft contract based on existing templates + proposal data
- [ ] Bill gets useful weekly report that saves him time

**Detailed Plan:** `docs/planning/2_WEEK_SPRINT_DEC_2025.md`

---

## Current Blockers

| Blocker | Impact | Owner | Action | ETA |
|---------|--------|-------|--------|-----|
| Finance team Excel | Can't reconcile invoices | Lukas | Send reminder | Unknown |
| IMAP LOGIN error | No new email import | Data | Debug tmail connection | Dec 1 |

---

## Backlog (Next Sprint)

1. Natural language query improvements
2. Meeting transcript → action item extraction
3. Proposal follow-up automation
4. Financial dashboard polish

---

## Done (Last 2 Weeks)

- [x] Database consolidated to OneDrive (Nov 24)
- [x] Bensley Brain context system (Nov 26)
- [x] Multi-agent sprint structure (Nov 26)
- [x] Alignment audit completed (Nov 27)
- [x] Agent coordination system designed (Nov 27)
- [x] Backend router refactor (main.py 11,719 → 237 lines) (Nov 28)
- [x] 3 critical bugs fixed: contracts, invoices stats, Switch component (Nov 29)
- [x] All frontend pages functional (Nov 30)
- [x] **Phase A: Infrastructure verified** (Dec 1) - 9 paths fixed, 27 routers tested
- [x] **Phase B: Data audit** (Dec 1) - Found 100% orphaned links
- [x] **Phase D: Link tables rebuilt** (Dec 1) - 660 proposal + 200 project links, 100% FK integrity
- [x] **E3 Week 1: Handler framework** (Dec 1) - Base class, registry, 3 handlers
- [x] **E5: Weekly report** (Dec 1) - Generates with email counts (18 proposals, 418 emails)
- [x] **Contact→Project linking pipeline** (Dec 1) - 89 contact_link suggestions created
- [x] **TARC data merge** (Dec 1) - 25 BK-008 → 25 BK-017, fixed proposal/project status consistency
- [x] **Email learning loop** (Dec 1) - System learns from approved email_link suggestions, boosts future confidence

---

## Phase Milestones

| Phase | Target | Key Deliverable | Status |
|-------|--------|-----------------|--------|
| 1.0 | Nov 24 | Data foundation + API | Done |
| 1.5 | Dec 15 | Integration + Data Quality | In Progress |
| 2.0 | Jan 15 | Intelligence Layer | Not Started |
| 3.0 | Feb 15 | Multi-user + Production | Not Started |

---

## Metrics to Track

| Metric | Current | Target |
|--------|---------|--------|
| Backend-to-API coverage | 95% | 95% |
| API-to-Frontend coverage | 90% | 80% |
| email_proposal_links | 660 valid (100% FK) | ✅ |
| email_project_links | 200 valid (100% FK) | ✅ |
| Pending suggestions | 566 | <50 |
| Handlers registered | 9 | 10 |
| Page load time | ~2s | <2s |

---

## Notes for Brain Agent

When updating this file:
1. Move completed items to "Done" section
2. Update metrics weekly
3. Reprioritize backlog based on blockers
4. Add new blockers immediately when discovered
5. Keep sprint scope realistic (3-5 main items)
