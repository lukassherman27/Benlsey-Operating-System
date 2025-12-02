# CURATION LOG - Knowledge Evolution Tracking

**Purpose:** Track what learnings have been captured into context files over time.

---

## Curation: 2025-12-01 (End of Day)

### Period Covered
Full day - Phases A, B, D completed

### Key Learnings CAPTURED

#### Data (from Phase B Audit) → `docs/context/data.md`
- [x] FK mismatch pattern - email links used wrong ID ranges
- [x] Project code format: "YY BK-XXX" vs "BK-XXX" inconsistency
- [x] Link rebuild methodology (staging → swap → verify)
- [x] FK constraint enforcement patterns
- [ ] 49.5% of contacts have no names (pending cleanup)
- [ ] Transcripts are chunked - same meeting has multiple entries (pending dedup)

#### Technical (from Phase A) → Already in LIVE_STATE.md
- [x] 9 scripts had hardcoded Desktop paths (FIXED)
- [x] 6 routers had code bugs (FIXED by Backend Worker)
- [x] Rebuild links by project_code, not by ID offset

#### Process
- [x] Parallel agent swarm works well for speed (4 workers completed in ~2 hours)
- [x] Workers need explicit "report to WORKER_REPORTS.md" instruction
- [x] Phase gates prevent building on broken foundations (Phase C skipped correctly)

### Files Created/Updated
- `docs/context/data.md` - NEW - Data quality patterns and rebuild methodology
- `.claude/LIVE_STATE.md` - Updated with all phase completions
- `.claude/TASK_BOARD.md` - Updated with completed tasks
- `.claude/WORKER_REPORTS.md` - 5 worker reports added
- `database/migrations/048_enforce_fk_constraints.sql` - NEW (not run yet)
- `scripts/core/email_project_linker.py` - Fixed path + added FK validation

### Database Changes
- `email_proposal_links` - REBUILT (660 valid links, 100% FK integrity)
- `email_proposal_links_old` - Backup retained (4,872 orphaned records)
- `email_proposal_links_new` - Renamed to main table

### Next Curation Due
After Phase E (Weekly Reports) or email_project_links rebuild

---

## Curation: 2025-12-01 (Initial)

### Period Covered
Sprint start (Dec 1, 2025)

### Status: COMPLETED (see End of Day above)

---

<!-- Future curations go above this line -->
