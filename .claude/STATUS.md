# System Status

**Updated:** 2025-12-25
**Backend:** localhost:8000 | **Frontend:** localhost:3002
**Phase:** Operations - Proposals & Email Linking

---

## Current State (Dec 25)

### Live Numbers

| Entity | Count |
|--------|-------|
| Emails | 3,879 |
| Proposals | 108 |
| Projects | 67 |
| Contacts | 467 |
| Invoices | 436 |
| Patterns | 153 |

### Pipeline Summary

| Metric | Value |
|--------|-------|
| **Active Pipeline** | $41.97M (35 proposals) |
| **Contract Signed** | $25.58M (18 proposals) |
| **Declined/Lost** | 26 proposals |
| **Dormant** | 24 proposals |

### Proposal Status Breakdown

| Status | Count |
|--------|-------|
| Dormant | 24 |
| Contract Signed | 18 |
| Declined | 18 |
| Proposal Sent | 16 |
| First Contact | 14 |
| Lost | 8 |
| On Hold | 5 |
| Proposal Prep | 3 |
| Negotiation | 2 |

---

## Open Issues (11)

### Priority 1
- #95: Track Bensley action items not just ball ownership
- #14: PM dashboard view

### Priority 2
- #93: Add sender_category to emails (migrations exist)
- #94: Auto-update ball_in_court based on email direction
- #7/#81: Claude CLI email learning loop
- #20: Follow-up email drafting automation
- #19: Contact research automation
- #22: OneDrive folder cleanup

### Needs Business Decision
- #60: $0.9M invoices >90 days old
- #61: Empty tables (contract_terms, project_financials) - Phase 2

---

## Recent Work (Dec 25)

### Issues Closed Today
- #17: Add email review to admin nav
- #13: Email thread view (already existed)
- #18: Add transcripts to nav
- #15: Project detail page (already existed)
- #39: Data quality issues

### PRs Merged
- #92: Cross-agent coordination (CODEOWNERS, PR template)
- #91: Unified email categories
- #89: API response consistency

---

## What's Working

| Feature | Status |
|---------|--------|
| Proposal Tracker | Live |
| Email Linking | Live (via suggestions) |
| Pattern Learning | Live (153 patterns) |
| Project Pages | Live |
| Finance Dashboard | Live |
| Meeting Transcripts | Live |
| AI Suggestions | Live |

---

## Quick Commands

```bash
# Start backend
cd backend && uvicorn api.main:app --reload --port 8000

# Start frontend
cd frontend && npm run dev

# Run email sync
python scripts/core/scheduled_email_sync.py

# Check database
sqlite3 database/bensley_master.db "SELECT 'emails', COUNT(*) FROM emails UNION SELECT 'proposals', COUNT(*) FROM proposals;"
```

---

## For Full Context
- `CLAUDE.md` - Workflow rules
- `.claude/HANDOFF.md` - Deep business context
- `docs/ARCHITECTURE.md` - System design
- `docs/roadmap.md` - Vision and phases
