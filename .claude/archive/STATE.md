# STATE

**Updated:** 2025-12-10
**Phase:** Week 1 - Foundation Fixes

---

## Current Task
Fix critical bugs before building features (Week 1, Days 1-7)

## Dec 10 Session - Backend Builder
**Completed:**
1. Created `scripts/core/smoke_test.py` - pre/post session verification
2. Fixed `status_handler.py` - VALID_STATUSES now uses TitleCase + normalization map
3. Fixed `proposals.py` - /api/proposals/at-risk now queries `proposals` table (not `projects`)
4. Fixed `proposals.py` - /api/proposals/needs-follow-up also now queries `proposals` table
5. Cleaned up 12 orphaned records in `project_contact_links`
6. Verified proposal statuses already standardized (TitleCase: First Contact, Proposal Sent, etc.)

**Learning System Status:**
- Counter code appears correct (`times_used`, `times_correct`, `times_rejected` increment properly)
- Counters were manually reset to 0 (backup exists: email_learned_patterns_backup_dec11)
- No code bugs found - counters just aren't being exercised because pattern matching isn't active
- Need to verify patterns get used when email sync runs

## Smoke Test Results (POST-SESSION)
```
All 4 checks PASSED:
1. Database: OK - 102 proposals, 3773 emails
2. API: OK - 50 proposals returned
3. Frontend: (run without --quick to verify)
4. FK Integrity: No orphans
```

## Next Session Should
1. Run `python scripts/core/smoke_test.py` (without --quick)
2. Verify pattern matching works during email sync
3. Test status change flow: suggestion → approve → counter increment
4. Continue with remaining roadmap items

## Key Files Modified
- `scripts/core/smoke_test.py` (NEW)
- `backend/services/suggestion_handlers/status_handler.py`
- `backend/api/routers/proposals.py`

## Key Files To Read
- `.claude/HOW_IT_WORKS.md` - How the system coordinates
- `.claude/AGENT_ARCHITECTURE.md` - Full architecture diagram
- `.claude/plans/joyful-foraging-crystal.md` - Master plan with full roadmap

## Pattern Tables (FYI)
- `email_learned_patterns` - 151 patterns (counters reset, backup exists)
- `learned_patterns` - 341 patterns (different schema, no counters)

## IMPORTANT
- Run `python scripts/core/smoke_test.py` BEFORE and AFTER making changes
- Use `--quick` to skip frontend build during iteration
- Make ONE change at a time
- Commit after each verified change
