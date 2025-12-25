# System Status

**Updated:** 2025-12-25 (End of Session)
**Backend:** localhost:8000 | **Frontend:** localhost:3002
**Phase:** Operations - Proposals & Email Linking

---

## Current State

### Live Numbers

| Entity | Count |
|--------|-------|
| Emails | 3,879 |
| Proposals | 108 |
| Projects | 67 |
| Contacts | 467 |
| Invoices | 436 |
| Patterns | 153 |

### Email Linking Stats

| Metric | Count |
|--------|-------|
| Linked emails | 2,095 (54%) |
| Unlinked (linkable) | 515 |
| Unlinked (standalone) | 1,269 (correctly not linked) |
| Pending suggestions | 0 |

### Pipeline Summary

| Metric | Value |
|--------|-------|
| **Active Pipeline** | $41.97M (35 proposals) |
| **Contract Signed** | $25.58M (18 proposals) |
| **Declined/Lost** | 26 proposals |
| **Dormant** | 24 proposals |

---

## Session Work (Dec 25)

### Issues Fixed Today
| Issue | PR | Description |
|-------|-----|-------------|
| #93 | - | sender_category (already existed) |
| #94 | #97 | Auto ball_in_court trigger |
| #95 | #106 | Action owner tracking |
| #99 | #104 | Pattern feedback loop |
| #102 | #105 | Skill category filtering |
| #81 | - | Closed as duplicate |
| #17, #13, #18, #15, #39 | #92 | Nav fixes, data quality |

### Key Improvements
1. **Pattern Learning Loop** - Now records times_correct/times_rejected
2. **Action Owner Tracking** - action_owner field on proposals
3. **Ball In Court Trigger** - Auto-updates on email link
4. **Correct Unlinked Count** - 515 actual (not 1,784)
5. **Cross-Agent Coordination** - CODEOWNERS, PR template

---

## Open Issues (9)

### Data Cleanup
- #100: Legacy category column
- #101: Normalize match_method values

### Features
- #14: PM dashboard (blocked - needs PM data)
- #7: Claude CLI email workflow

### Automation (Phase 2)
- #19: Contact research
- #20: Follow-up drafting

### Business Decisions
- #60: $0.9M invoices >90 days
- #61: Empty tables (Phase 2)

### Infrastructure
- #22: OneDrive cleanup

---

## What's Working

| Feature | Status | Notes |
|---------|--------|-------|
| Proposal Tracker | Live | action_owner tracking added |
| Email Linking | Live | 54% linked, 515 to process |
| Pattern Learning | Live | 153 patterns, feedback working |
| Ball In Court | Live | Auto-updates via trigger |
| Project Pages | Live | |
| Finance Dashboard | Live | |
| Meeting Transcripts | Live | |

---

## Database Changes Today

```sql
-- Migration 093: Auto ball_in_court trigger
CREATE TRIGGER trg_auto_ball_in_court
AFTER INSERT ON email_proposal_links ...

-- Migration 094: Action owner tracking
ALTER TABLE proposals ADD COLUMN action_owner TEXT;
ALTER TABLE proposals ADD COLUMN action_source TEXT;
```

---

## Quick Commands

```bash
# Start servers
cd backend && uvicorn api.main:app --reload --port 8000
cd frontend && npm run dev

# Email sync
python scripts/core/scheduled_email_sync.py

# Check stats
sqlite3 database/bensley_master.db "SELECT 'emails', COUNT(*) FROM emails;"
```

---

## For Full Context
- `CLAUDE.md` - Workflow rules
- `.claude/HANDOFF.md` - Business context
- `docs/ARCHITECTURE.md` - System design
- `docs/roadmap.md` - Vision and phases
