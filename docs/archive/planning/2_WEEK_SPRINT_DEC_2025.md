# 2-Week Sprint: Beautiful, Connected, Demo-Ready
## Dec 1-15, 2025

**Goal:** Transform the platform into something you're proud to demo
**Database:** `database/bensley_master.db` (REAL DATA ONLY - no mocks)
**Demo Target:** Dec 15 - Show Bill something impressive

---

## The Vision

By Dec 15, anyone looking at this platform should think:
> "This looks like professional software. It's clean, it's clear, it's beautiful."

Not colors for the sake of colors. Every element has purpose.

---

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEB IA/UX ARCHITECT AGENT                     │
│                                                                  │
│  WEEK 1: Design system, page map, API contracts                 │
│  WEEK 2: Polish verification, consistency check                 │
│                                                                  │
│  Owns: Design tokens, component guidelines, page inventory      │
│  Creates: UI spec, color palette, typography, states            │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│ FRONTEND BUILDER  │ │ FRONTEND BUILDER  │ │ FRONTEND BUILDER  │
│    PROPOSALS      │ │  ACTIVE PROJECTS  │ │  AI SUGGESTIONS   │
│                   │ │                   │ │                   │
│ /tracker          │ │ /projects         │ │ /suggestions      │
│ /proposals/[code] │ │ /projects/[code]  │ │ /admin/*          │
└───────────────────┘ └───────────────────┘ └───────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND INTEGRATOR AGENT                      │
│                                                                  │
│  - Audit endpoints for each page                                │
│  - Add pagination, filters, sorting where missing               │
│  - Create view models for charts/summary cards                  │
│  - Ensure consistent response shapes                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ORGANIZER AGENT                             │
│                                                                  │
│  - Updates docs/context/frontend.md with page→endpoint maps     │
│  - Updates docs/context/backend.md with new endpoints           │
│  - Keeps task packs current                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Target Pages (Priority Order)

| Page | Current | Target | Owner | Real Data Source |
|------|---------|--------|-------|------------------|
| `/tracker` (Proposals) | 8/10 | 9.5/10 | Frontend Builder 1 | 89 proposals |
| `/projects` (Active) | 9/10 | 9.8/10 | Frontend Builder 2 | 54 projects, 253 invoices |
| `/suggestions` (AI) | 7/10 | 8.5/10 | Frontend Builder 3 | 801 pending suggestions |
| `/` (Dashboard) | 8/10 | 9.5/10 | Frontend Builder 1 | Aggregate APIs |

---

## Week 1: Design + Contracts + First Wiring

### Day 1-2: UX Architect

**Deliverables:**

1. **Page Map & Navigation**
   - Audit current routes in `frontend/src/app/`
   - Map each page to backend APIs
   - Define primary user journeys
   - Identify dead ends and gaps

2. **Design Token Spec**
   ```
   colors:
     primary:    Action buttons, links, focus rings
     success:    Paid, completed, healthy (green-600)
     warning:    Aging, needs attention (amber-600)
     danger:     Overdue, critical, error (red-600)
     neutral:    Text hierarchy, borders, backgrounds

   typography:
     h1: 30px bold (page titles)
     h2: 24px semibold (section headers)
     h3: 20px semibold (card headers)
     body: 16px normal
     caption: 14px normal
     label: 12px medium uppercase tracking-wide

   spacing:
     xs: 4px    sm: 8px    md: 16px    lg: 24px    xl: 32px

   radius:
     card: 16px    button: 12px    input: 8px    badge: 9999px
   ```

3. **Component Standards**
   - Cards: Consistent padding, borders, shadows
   - Tables: Headers, rows, hover, sort indicators
   - Charts: Same colors across all charts
   - Buttons: Primary, secondary, ghost, danger variants
   - States: Loading skeleton, empty (with CTA), error (with retry)

4. **API Contract Gaps**
   - For each page, list required endpoints
   - Note which exist, which need patches, which are missing

---

### Day 3-4: Backend Integrator

**Tasks:**

1. **Audit for Proposals Page**
   - `/api/proposal-tracker/list` - Add sorting if missing
   - `/api/proposal-tracker/stats` - Verify response shape
   - `/api/proposals/by-code/{code}` - Detail endpoint

2. **Audit for Projects Page**
   - `/api/projects/active` - Verify pagination
   - `/api/projects/{code}/hierarchy` - Check performance
   - `/api/invoices/by-project/{code}` - Ensure consistent dates

3. **Audit for Suggestions Page**
   - `/api/suggestions` - Add filtering by type
   - `/api/suggestions/stats` - Summary counts
   - `/api/suggestions/bulk-approve` - Verify working

4. **Add Missing Endpoints**
   - If any page needs an endpoint that doesn't exist, add it
   - Document in `docs/context/backend.md`

**Response Shape Standard:**
```json
{
  "data": [...],
  "meta": {
    "total": 89,
    "page": 1,
    "per_page": 50
  }
}
```

---

### Day 5-7: Frontend Builders

**Frontend Builder 1: Proposals Page**

Files:
```
frontend/src/app/(dashboard)/tracker/page.tsx
frontend/src/components/proposals/proposals-manager.tsx
frontend/src/components/proposals/proposal-status-timeline.tsx
```

Tasks:
- [ ] Apply new design tokens (colors, typography, spacing)
- [ ] Improve status color coding (purposeful, not decorative)
- [ ] Add loading skeleton (not spinner)
- [ ] Add empty state with helpful message
- [ ] Verify all APIs return real data
- [ ] Add filter by country, discipline, year (verify filters work)
- [ ] Health indicators with clear meaning

**Frontend Builder 2: Active Projects Page**

Files:
```
frontend/src/app/(dashboard)/projects/page.tsx
frontend/src/components/dashboard/active-projects-tab.tsx
frontend/src/components/project/unified-timeline.tsx
```

Tasks:
- [ ] Apply design tokens consistently
- [ ] Smooth expand/collapse animations (200ms ease)
- [ ] Invoice table formatting (right-align numbers, consistent currency)
- [ ] Color-coded status badges (paid=green, outstanding=amber, overdue=red)
- [ ] Performance: Virtual scrolling if >50 projects
- [ ] Loading skeleton for hierarchy expansion

**Frontend Builder 3: Suggestions Page**

Files:
```
frontend/src/app/(dashboard)/suggestions/page.tsx
frontend/src/app/(dashboard)/admin/validation/page.tsx
frontend/src/app/(dashboard)/admin/intelligence/page.tsx
```

Tasks:
- [ ] Unify admin pages with consistent layout
- [ ] Suggestion cards with clear approve/reject actions
- [ ] Bulk selection and bulk approve
- [ ] Show suggestion reasoning/confidence
- [ ] Stats summary at top (pending, approved today, rejected)
- [ ] Empty state: "No pending suggestions - you're all caught up!"

---

## Week 2: Polish + Integration + QA

### Day 8-9: Final UI Polish

**All Frontend Builders:**

- [ ] Every page uses same typography scale
- [ ] Every page uses same color tokens
- [ ] Every table has same styling (headers, rows, hover)
- [ ] Every card has same border-radius, padding, shadow
- [ ] Every button follows the variant system
- [ ] Every loading state uses skeleton (no spinners)
- [ ] Every empty state has helpful message + action
- [ ] Every error state has retry button

**Charts Consistency:**
- [ ] Same blue for primary metrics
- [ ] Same green for positive/paid
- [ ] Same amber for warning/aging
- [ ] Same red for danger/overdue
- [ ] Same tooltip styling across all charts

---

### Day 10-11: Backend Hardening

**Backend Integrator:**

- [ ] All endpoints have proper error responses
- [ ] All endpoints have timeout handling
- [ ] All date formats consistent (ISO 8601)
- [ ] All currency values in cents or with decimal consistency
- [ ] Add caching for heavy aggregates
- [ ] Document any new endpoints in `backend.md`

---

### Day 12-13: Integration Testing

**QA Checklist:**

Per-page verification:
- [ ] `/tracker` - Filters work, data matches database
- [ ] `/projects` - Hierarchy loads, invoices correct
- [ ] `/projects/[code]` - Detail view accurate
- [ ] `/suggestions` - Approve/reject updates database
- [ ] `/` Dashboard - KPIs match actual counts

Cross-cutting:
- [ ] Navigation between all pages works
- [ ] No console errors
- [ ] No broken API calls
- [ ] Labels match data (no "undefined" or "NaN")
- [ ] Numbers formatted correctly
- [ ] Dates formatted consistently

---

### Day 14: Demo Prep & Lockdown

- [ ] Final walkthrough of all pages
- [ ] Fix any last critical issues
- [ ] Update `docs/roadmap.md` with completion status
- [ ] Lock context files (no more changes)
- [ ] Prepare demo script:
  1. Open Dashboard - "Here's your daily overview"
  2. Proposals - "Track every opportunity"
  3. Projects - "See exactly what's outstanding"
  4. Admin - "Manage AI suggestions"

---

## Design Guardrails

### BENSLEY AESTHETIC: Black & White Foundation + Color Pops

**Philosophy:** 80% grayscale, 20% purposeful color. We're a design firm - sophistication over flash.

**Foundation (No Meaning - Structure Only):**
| Color | Hex | Use |
|-------|-----|-----|
| Black | #0A0A0A | Headers, emphasis |
| Charcoal | #1A1A1A | Body text |
| Silver | #666666 | Muted text, captions |
| Pearl | #E5E5E5 | Borders, dividers |
| Snow | #F5F5F5 | Subtle backgrounds |
| White | #FFFFFF | Cards, main background |

**Accents (Color = Information):**
| Color | Hex | When to Use | Examples |
|-------|-----|-------------|----------|
| Teal (primary) | #0D9488 | Actions, interactive | Buttons, links, focus rings |
| Emerald (success) | #059669 | Positive, complete | Paid badges, healthy status |
| Amber (warning) | #D97706 | Needs attention | 30-60 day invoices, stale |
| Red (danger) | #DC2626 | Critical, overdue | 90+ day invoices, errors |
| Blue (info) | #2563EB | Informational | Neutral status, links |

**Rule:** If you can't explain WHY a color is there, it should be grayscale.

### Typography Hierarchy

| Element | Style | Purpose |
|---------|-------|---------|
| Page Title | `text-3xl font-bold` | One per page, top left |
| Section Header | `text-2xl font-semibold` | Major content sections |
| Card Header | `text-xl font-semibold` | Widget/card titles |
| Body Text | `text-base` | Default content |
| Caption | `text-sm text-muted` | Supporting info |
| Label | `text-xs uppercase tracking-wide` | Form labels, badges |

### Table Standards

```
┌────────────────────────────────────────────────────────────┐
│  Project Code ▲   │  Client        │  Outstanding  │  Age │
├────────────────────────────────────────────────────────────┤
│  25-BK-070        │  Grand Hyatt   │    $125,000   │  45d │ ← hover:bg-slate-50
│  25-BK-095        │  Four Seasons  │     $87,500   │  32d │
│  24-BK-040        │  Marriott      │    $245,000   │  87d │ ← text-red-600 (overdue)
└────────────────────────────────────────────────────────────┘

- Headers: text-sm font-medium uppercase text-slate-500
- Numbers: text-right font-mono
- Sortable: Show ▲/▼ indicator
- Hover: bg-slate-50 transition
- Overdue rows: text-red-600
```

### Chart Consistency

All charts use this palette:
```
Primary metric: blue-500
Positive/Paid: green-500
Warning/Aging: amber-500
Danger/Overdue: red-500
Neutral/Other: slate-400
```

Tooltip style: Dark background, white text, rounded-lg shadow-lg

### States (Every Component Needs These)

1. **Loading:** Skeleton animation, same shape as content
2. **Empty:** Helpful message + primary action button
3. **Error:** Error message + "Try Again" button
4. **Success:** Green checkmark + success message (brief)
5. **Partial:** "Showing X of Y" with "Load More" option

---

## Real Data Sources

**No mocks. Everything connects to:**

```
Database: database/bensley_master.db
├── proposals: 89 records
├── projects: 54 active
├── invoices: 253 records
├── emails: 3,356 records (68% linked)
├── contacts: 465 records
├── ai_suggestions: 801 pending
└── email_project_links: 2,290 links
```

**API Base:** `http://localhost:8000`

**If data looks sparse:**
- Show real count: "3 RFIs" not "No data"
- Build the UI correctly - data can grow later
- Never show fake numbers to make it "look better"

---

## Success Metrics

### Visual Checklist (Dec 15)
- [ ] All pages use same header style
- [ ] All pages use same button styles
- [ ] All tables look identical in structure
- [ ] All charts use same color palette
- [ ] All loading states use skeleton
- [ ] All empty states are helpful
- [ ] No console errors anywhere
- [ ] No "undefined" or "NaN" visible
- [ ] Numbers right-aligned and formatted
- [ ] Dates consistent format throughout

### Functional Checklist
- [ ] Can filter proposals by status ✓
- [ ] Can expand project hierarchy ✓
- [ ] Can approve/reject suggestions ✓
- [ ] Can navigate between all pages ✓
- [ ] All data matches database ✓

### Impression Test
When Bill sees it, he should say:
> "Wow, this looks professional. When can I start using it?"

---

## Task Packs to Create

1. `docs/tasks/ux-design-system.md` - UX Architect work
2. `docs/tasks/proposals-page-polish.md` - Frontend Builder 1
3. `docs/tasks/projects-page-polish.md` - Frontend Builder 2
4. `docs/tasks/suggestions-page-polish.md` - Frontend Builder 3
5. `docs/tasks/backend-api-contracts.md` - Backend Integrator

---

## Handoff Protocol

After each session:
1. Update your task pack with completed items
2. Write handoff note: what changed, what's left, gotchas
3. If design changes: Update design-system.ts
4. If API changes: Update docs/context/backend.md
5. Commit: `[polish](agent-name): Brief description`

---

## Don't Do List

- Don't add new features
- Don't build new pages
- Don't refactor backend architecture
- Don't add mock data
- Don't use colors without purpose
- Don't add animations without purpose
- Don't overcomplicate anything
- Don't leave "TODO" comments in UI
- Don't show broken or incomplete sections

---

## Coordinator Responsibility

The Brain/Coordinator ensures:
- All agents read this sprint plan
- No duplicate work between agents
- Design tokens are consistent across all pages
- API contracts match between backend and frontend
- Demo is ready by Dec 15

Update `docs/roadmap.md` with:
- Sprint goal: "Beautiful, connected, demo-ready"
- Daily progress
- Blockers as they arise
- Final sign-off

---

**Created:** 2025-11-27
**Owner:** Brain Agent
**Status:** Ready to Execute
