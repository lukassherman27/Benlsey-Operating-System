# Executive Dashboard Agent - Bill/Brian Self-Serve View

> Issue: #319 | Priority: P1 | Branch: `feat/executive-dashboard-319`

---

## CONTEXT

Bill Bensley is the **CONSUMER** of this system, not a data producer. He needs:
- Pipeline health visible in <5 seconds
- AI-curated "Needs Attention" list
- 1-click actions (Won/Lost/Follow-up)
- No operational clutter (emails, files, schedule)

From Lukas:
> "The system needs to have all that information so Bill/Brian can always check, always see, whenever they want."

---

## PHASE 1: UNDERSTAND (Research First)

### Required Research
```bash
# Check what dashboard components exist
find frontend/src/components/dashboard -name "*.tsx" | head -20

# Check current dashboard page structure
cat frontend/src/app/\(dashboard\)/page.tsx | head -50

# Check existing stats endpoints
grep -r "dashboard" backend/api/routers/*.py | head -20

# Check proposal quick actions (already built)
grep -r "quick-action\|Won\|Lost" frontend/src --include="*.tsx" | head -10
```

### Questions to Answer
1. What widgets exist vs what Bill actually needs?
2. Is there already a "needs attention" or similar endpoint?
3. How are proposal quick actions implemented?
4. What's the current tab structure on dashboard?

### Files to Read
- `frontend/src/app/(dashboard)/page.tsx` - Current dashboard
- `frontend/src/components/dashboard/overview-tab.tsx` - What's in overview?
- `backend/api/routers/dashboard.py` - Available endpoints
- `backend/api/routers/proposals.py` - Quick action endpoints

**STOP HERE** until you understand what already exists.

---

## PHASE 2: THINK HARD (Planning)

### Design Decisions
1. **New page or modify existing?** Create `/executive` or role-based `/`?
2. **Widget selection** Which existing widgets to reuse vs build new?
3. **Mobile-first?** Bill uses iPad - responsive design critical

### Web Research
```
Search: "executive dashboard design patterns 2025"
Search: "CEO dashboard KPI best practices"
```

### Target Layout (from audit)
```
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTIVE DASHBOARD                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PIPELINE     │  │ ACTIVE       │  │ OUTSTANDING  │          │
│  │ $42.5M       │  │ PROJECTS     │  │ INVOICES     │          │
│  │ 47 proposals │  │ 23 active    │  │ $2.1M        │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ NEEDS YOUR ATTENTION (AI-Curated)                    [View]││
│  │ 1. Nusa Dua - No response in 21 days          [Follow Up] ││
│  │ 2. La Vie - Contract ready for signature      [View]      ││
│  │ 3. Invoice #1234 - 95 days outstanding        [Escalate]  ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │ PROPOSAL PIPELINE       │  │ THIS WEEK'S ACTIVITY        │  │
│  │ First Contact    12    │  │ Mon: 3 meetings, 2 proposals │  │
│  │ Proposal Sent    18    │  │ Tue: Site visit             │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Write Your Plan
1. Audit existing dashboard components - what to reuse
2. Create `NeedsAttentionWidget` component
3. Create `ExecutiveDashboard` layout
4. Add backend endpoint for AI-curated attention items
5. Wire up quick actions to existing endpoints
6. Test on desktop and iPad

---

## PHASE 3: IMPLEMENT

### Backend - Needs Attention Endpoint
Add to `backend/api/routers/dashboard.py`:
```python
@router.get("/dashboard/needs-attention")
async def get_needs_attention():
    """
    AI-curated list combining:
    - Proposals with no activity in 14+ days
    - Invoices 90+ days outstanding
    - Pending AI suggestions (high confidence)
    - Upcoming contract expirations
    """
```

### Frontend - Executive Dashboard
Create `frontend/src/components/executive/executive-dashboard.tsx`:
- 3 KPI cards at top
- NeedsAttention widget (prominent)
- Pipeline breakdown (left)
- Week activity (right)

### Frontend - Needs Attention Widget
Create `frontend/src/components/executive/needs-attention-widget.tsx`:
- Fetch from `/api/dashboard/needs-attention`
- Each item: description, urgency, action button
- Actions: Follow Up, View, Escalate

### Files to Create/Modify
| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/components/executive/executive-dashboard.tsx` | Create | Main layout |
| `frontend/src/components/executive/needs-attention-widget.tsx` | Create | AI-curated list |
| `backend/api/routers/dashboard.py` | Modify | Add endpoint |
| `frontend/src/app/(dashboard)/page.tsx` | Modify | Render executive view |

---

## PHASE 4: VERIFY

### Testing Checklist
- [ ] Dashboard loads without errors
- [ ] KPI cards show correct numbers
- [ ] Needs Attention widget displays items
- [ ] Quick action buttons work
- [ ] Responsive on iPad (768px)

### Verification Commands
```bash
cd frontend && npm run build
curl http://localhost:8000/api/dashboard/needs-attention | python -m json.tool
```

### Success Criteria
- Bill can see pipeline health in <5 seconds
- "Needs Attention" shows actionable items
- 1-click actions work
- Works on iPad Safari

---

## PHASE 5: COMPLETE

### Commit Format
```bash
git commit -m "feat(dashboard): add executive dashboard with needs-attention widget (#319)

- Add NeedsAttention widget with AI-curated items
- Add KPI cards (pipeline, projects, invoices)
- Add /api/dashboard/needs-attention endpoint
- Integrate quick actions

Fixes #319"
```

---

## CONSTRAINTS

- **Don't remove existing dashboard** - add executive view alongside
- **Reuse existing components** - don't rebuild stats cards
- **iPad first** - Bill uses iPad, test at 768px
- **Keep it simple** - fewer widgets = better

---

## RESOURCES

- `.claude/plans/system-architecture-ux.md` - Section 4: Executive Dashboard Design
- Issue #319 for acceptance criteria
- Existing `/tracker` page for quick action patterns
