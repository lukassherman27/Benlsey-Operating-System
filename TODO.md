# TODO Tracker

**Auto-generated: 2025-11-26** | Run `make todos` to refresh

---

## 📊 Summary

| Agent | TODOs | Priority |
|-------|-------|----------|
| Agent 1: Email Processing | 1 | Medium |
| Agent 3: Backend APIs | 4 | High |
| Agent 4: Frontend Components | 4 | High |
| Agent 5: Integration | 0 | - |
| Coordinator | 0 | - |
| Organizer | 0 | - |
| 🆕 Auth Agent (Future) | 2 | Phase 3 |
| 🆕 Finance Agent | 2 | Medium |
| Unassigned | 0 | - |

**Total: 13 TODOs**

---

## Agent 1: Email Processing

*Mission: Process emails with AI analysis and build threads*

| File | Line | TODO | Priority |
|------|------|------|----------|
| `backend/services/schedule_email_parser.py` | 277 | Match nickname to member_id from team_members table | Medium |

---

## Agent 2: Database Schema Migration

*Mission: Schema unification and migrations*

✅ **No active TODOs** - Schema work complete

---

## Agent 3: Backend APIs

*Mission: Build FastAPI endpoints*

| File | Line | TODO | Priority |
|------|------|------|----------|
| `backend/api/main.py` | 412 | Add logic for detecting wins from emails/payments | High |
| `backend/api/main.py` | 3496 | Implement payment schedule | Medium |
| `backend/api/main.py` | 3502 | Implement blockers tracking | Medium |
| `backend/api/main.py` | 3503 | Implement task tracking | Medium |

**Notes:**
- Win detection: Could use email sentiment + payment confirmation emails
- Payment schedule: Need finance team data first
- Blockers/tasks: New feature, needs design

---

## Agent 4: Frontend Components

*Mission: Build React components for dashboard*

| File | Line | TODO | Priority |
|------|------|------|----------|
| `frontend/src/components/dashboard/dashboard-page.tsx` | 67 | Replace with proper empty states and error handling | High |
| `frontend/src/components/dashboard/invoice-quick-actions.tsx` | 21 | Hook these up to actual functions | High |
| `frontend/src/components/dashboard/payment-velocity-widget.tsx` | 13 | Hook this up to real API endpoint | Medium |
| `frontend/src/components/proposal-quick-edit-dialog.tsx` | 164 | Replace with actual user from auth system | Phase 3 |

**Notes:**
- Empty states: Use shadcn/ui Skeleton components
- Invoice actions: Wire to existing `/api/invoices/*` endpoints
- Payment velocity: Create new endpoint or use existing finance data

---

## Agent 5: Email Integration

*Mission: Wire up email components to pages*

✅ **No active TODOs** - Integration tasks tracked elsewhere

---

## 🆕 Auth Agent (Phase 3)

*Mission: Authentication and user management*

| File | Line | TODO | Priority |
|------|------|------|----------|
| `frontend/src/components/proposal-quick-edit-dialog.tsx` | 164 | Replace with actual user from auth system | Phase 3 |
| `backend/services/training_data_service.py` | 71 | Get from auth context (currently hardcoded 'bill') | Phase 3 |

**Notes:**
- Defer until Phase 3 multi-user implementation
- Will need: JWT/session, user table, role-based permissions

---

## 🆕 Finance Agent

*Mission: Invoice, payment, and financial features*

| File | Line | TODO | Priority |
|------|------|------|----------|
| `backend/api/main.py` | 3496 | Implement payment schedule | Medium |
| `frontend/src/components/dashboard/payment-velocity-widget.tsx` | 13 | Hook this up to real API endpoint | Medium |

**Notes:**
- Blocked on accounting Excel from finance team
- Payment velocity needs historical payment data

---

## 🗂️ Organizer Agent

*Mission: Codebase maintenance and organization*

✅ **No code TODOs** - Maintenance tasks tracked separately

**Ongoing responsibilities:**
- [ ] Weekly: Run `make health-check`
- [ ] Weekly: Update this TODO.md
- [ ] Monthly: Archive stale files
- [ ] Monthly: Review unused scripts

---

## 🎯 Coordinator Agent

*Mission: Sprint planning and cross-agent coordination*

✅ **No code TODOs** - Planning tracked in `docs/planning/`

---

## Quick Actions

### View all TODOs in code:
```bash
make todos
# or
grep -rn "TODO\|FIXME" --include="*.py" --include="*.ts" --include="*.tsx" backend/ frontend/src/ scripts/
```

### By priority:
```bash
# High priority (dashboard blockers)
grep -rn "TODO" frontend/src/components/dashboard/

# Backend API gaps
grep -rn "TODO" backend/api/main.py
```

---

## Completed TODOs

*Move items here when done*

| Date | Agent | Description |
|------|-------|-------------|
| - | - | - |

---

## Adding New TODOs

When adding TODOs to code, use this format:
```python
# TODO(agent-name): Description of what needs to be done
```

Examples:
```python
# TODO(agent-3): Add pagination to this endpoint
# TODO(finance): Wire up to accounting data when available
# TODO(phase-3): Replace with auth context
```

This makes it easy to filter by agent:
```bash
grep -rn "TODO(agent-3)" backend/
```
