# Task Pack: Build Missing Frontend Pages

**Created:** 2025-11-28
**Assigned To:** Frontend Builder Agent
**Priority:** P1 - After polish sprint
**Estimated:** 6-8 hours total

---

## Objective

Create frontend pages for 6 API areas that have working backends but no UI.
These are lower priority than the polish sprint but should be done after.

---

## Context to Read First

- [ ] `docs/planning/2_WEEK_SPRINT_DEC_2025.md` - Design guardrails
- [ ] `docs/tasks/ux-design-system.md` - Bensley aesthetic (BLACK/WHITE + color pops)
- [ ] `docs/context/backend.md` - API reference
- [ ] `frontend/src/lib/design-system.ts` - Design tokens

---

## Missing Pages Overview

| API Area | Endpoints | Suggested Route | Priority | Est. Time |
|----------|-----------|-----------------|----------|-----------|
| Calendar/Meetings | `/api/meetings`, `/api/calendar/*` | `/meetings` | P1 | 2h |
| Meeting Transcripts | `/api/meeting-transcripts/*` | `/transcripts` | P2 | 1.5h |
| Contracts | `/api/contracts/*` | `/contracts` | P2 | 1.5h |
| RFI Dashboard | `/api/rfis/*` | `/rfis` | P1 | 2h |
| Audit System | `/api/audit/*` | `/admin/audit` | P3 | 1h |
| Analytics | Multiple aggregate endpoints | `/analytics` | P2 | 2h |

**Total:** 6 pages, ~10 hours

---

## Page 1: Meetings & Calendar (`/meetings`)

### APIs Available
```
GET /api/meetings - List all meetings
GET /api/meetings/{id} - Single meeting
GET /api/calendar/events - Calendar events
POST /api/meetings - Create meeting
```

### UI Components Needed
- Calendar view (week/month toggle)
- Meeting list with upcoming/past tabs
- Meeting detail modal
- Quick add meeting button

### Design Notes (Bensley Aesthetic)
```
Layout: Full-width calendar, sidebar for meeting list
Colors: Black headers, white cards, teal for "today" indicator
        Status badges: green (completed), amber (upcoming), silver (cancelled)
Typography: Meeting titles in charcoal, times in silver
```

### File to Create
```
frontend/src/app/(dashboard)/meetings/page.tsx
frontend/src/components/meetings/calendar-view.tsx
frontend/src/components/meetings/meeting-card.tsx
```

---

## Page 2: Meeting Transcripts (`/transcripts`)

### APIs Available
```
GET /api/meeting-transcripts - List transcripts
GET /api/meeting-transcripts/{id} - Single transcript
GET /api/meeting-transcripts/{id}/summary - AI summary
```

### UI Components Needed
- Transcript list with search
- Transcript viewer with timestamps
- AI summary panel
- Link to related meeting

### Design Notes
```
Layout: Two-column - list on left, viewer on right
Colors: Monochrome text, teal highlights for key points
        Speaker names in charcoal, timestamps in silver
```

### File to Create
```
frontend/src/app/(dashboard)/transcripts/page.tsx
frontend/src/components/transcripts/transcript-viewer.tsx
```

---

## Page 3: Contracts (`/contracts`)

### APIs Available
```
GET /api/contracts - List contracts
GET /api/contracts/{id} - Single contract
GET /api/contracts/expiring - Contracts expiring soon
POST /api/contracts - Create contract
```

### UI Components Needed
- Contract list table with status filters
- Contract detail view
- Expiring contracts alert banner
- Link to parent project

### Design Notes
```
Layout: Table view with expandable rows
Colors: Status badges only - green (active), amber (expiring), red (expired), silver (draft)
        Currency in black, dates in charcoal
```

### File to Create
```
frontend/src/app/(dashboard)/contracts/page.tsx
frontend/src/components/contracts/contract-table.tsx
```

---

## Page 4: RFI Dashboard (`/rfis`)

### APIs Available
```
GET /api/rfis - List RFIs
GET /api/rfis/{id} - Single RFI
GET /api/rfis/pending - Pending RFIs
GET /api/rfis/by-project/{code} - RFIs for project
POST /api/rfis - Create RFI
PATCH /api/rfis/{id}/respond - Respond to RFI
```

### UI Components Needed
- RFI list with status filters (pending, responded, closed)
- RFI detail with response thread
- Create RFI form
- Stats cards (pending count, avg response time)

### Design Notes
```
Layout: Table with expandable response thread
Colors: Pending = amber badge, Responded = teal, Closed = silver
        Urgent RFIs get red dot indicator
Stats: Black numbers on white cards, silver labels
```

### File to Create
```
frontend/src/app/(dashboard)/rfis/page.tsx
frontend/src/components/rfis/rfi-table.tsx
frontend/src/components/rfis/rfi-thread.tsx
```

---

## Page 5: Audit System (`/admin/audit`)

### APIs Available
```
GET /api/audit/logs - Audit log entries
GET /api/audit/logs/{id} - Single entry
GET /api/audit/stats - Audit statistics
GET /api/audit/by-user/{user_id} - User's actions
```

### UI Components Needed
- Audit log table with filters (user, action type, date)
- Log detail modal
- User activity timeline
- Export to CSV button

### Design Notes
```
Layout: Dense table view, admin-focused
Colors: Mostly grayscale - this is a utility page
        Action types: Create = teal, Update = blue, Delete = red
        Timestamps in silver
```

### File to Create
```
frontend/src/app/(dashboard)/admin/audit/page.tsx
frontend/src/components/admin/audit-log-table.tsx
```

---

## Page 6: Analytics (`/analytics`)

### APIs Available
```
GET /api/analytics/proposals - Proposal stats
GET /api/analytics/projects - Project stats
GET /api/analytics/revenue - Revenue metrics
GET /api/analytics/pipeline - Pipeline health
```

### UI Components Needed
- KPI cards row (win rate, avg deal size, pipeline value)
- Proposal funnel chart
- Revenue trend chart
- Project timeline/Gantt
- Filters (date range, discipline, region)

### Design Notes
```
Layout: Dashboard grid with chart cards
Colors: Charts use the semantic palette
        - Teal for primary metrics
        - Emerald for revenue/positive
        - Amber for warnings
        - Keep background white, borders pearl
Typography: Big numbers in black (text-3xl font-bold)
            Labels in silver
```

### File to Create
```
frontend/src/app/(dashboard)/analytics/page.tsx
frontend/src/components/analytics/kpi-cards.tsx
frontend/src/components/analytics/funnel-chart.tsx
frontend/src/components/analytics/revenue-chart.tsx
```

---

## Acceptance Criteria

- [ ] All 6 pages created and accessible via navigation
- [ ] Each page fetches data from real API endpoints
- [ ] Loading skeletons on all pages (no spinners)
- [ ] Empty states with helpful messages
- [ ] Error states with retry buttons
- [ ] Follows Bensley aesthetic (80% grayscale, purposeful color)
- [ ] Mobile responsive (at minimum, not broken)
- [ ] No console errors

---

## Navigation Updates Needed

Add to sidebar in `frontend/src/components/layout/sidebar.tsx`:

```typescript
// Under existing nav items, add:
{ name: 'Meetings', href: '/meetings', icon: CalendarIcon },
{ name: 'Transcripts', href: '/transcripts', icon: DocumentTextIcon },
{ name: 'Contracts', href: '/contracts', icon: DocumentDuplicateIcon },
{ name: 'RFIs', href: '/rfis', icon: QuestionMarkCircleIcon },
{ name: 'Analytics', href: '/analytics', icon: ChartBarIcon },

// In admin section:
{ name: 'Audit Log', href: '/admin/audit', icon: ClipboardDocumentListIcon },
```

---

## Pattern to Follow

Use existing pages as reference:
- `/tracker` for table layouts
- `/projects` for hierarchy/detail views
- `/suggestions` for action-heavy lists

Each page should have:
```typescript
'use client'

import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

export default function PageName() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['endpoint-name'],
    queryFn: () => fetch('/api/endpoint').then(r => r.json())
  })

  if (isLoading) return <PageSkeleton />
  if (error) return <ErrorState onRetry={() => refetch()} />
  if (!data?.length) return <EmptyState />

  return (
    <div className="space-y-6">
      <PageHeader title="Page Title" />
      <StatsCards data={data} />
      <DataTable data={data} />
    </div>
  )
}
```

---

## Definition of Done

- [x] All 6 pages accessible and functional
- [x] Navigation updated with new links
- [x] Each page has loading/empty/error states
- [x] Design matches Bensley aesthetic
- [x] No TypeScript errors
- [x] Handoff note completed

---

## Handoff Note

**Completed By:** Frontend Builder Agent
**Date:** 2025-11-28

### What Changed
- Created 6 new pages with full functionality
- Updated navigation sidebar with all new links
- Added icons for new nav items (Calendar, HelpCircle, FileSignature, MessageSquare)
- Fixed pre-existing TypeScript error in design-system.ts (added 'neutral' badge variant)
- Enabled Analytics page (was previously disabled)

### What Works
- **Meetings** (`/meetings`): Week calendar view, upcoming/past tabs, meeting cards with status badges
- **RFIs** (`/rfis`): Status tabs, expandable rows with response thread, respond dialog, stats cards
- **Contracts** (`/contracts`): Table view with expiry tracking, alerts for expiring contracts, filtering
- **Transcripts** (`/transcripts`): Two-column layout, AI summary display, full transcript viewer
- **Analytics** (`/analytics`): KPI cards, revenue metrics, proposal funnel visualization
- **Audit Log** (`/admin/audit`): Dense table with filters, detail dialog, CSV export

All pages include:
- Loading skeletons (no spinners, per design system)
- Empty states with Bensley voice
- Error states with retry buttons
- Responsive design
- Consistent use of design tokens

### Known Limitations
- Pages fetch from backend APIs that may not all be fully implemented
- Charts use simple bar visualization (no external charting library)
- Calendar view is week-based only (no month view toggle yet)
- Transcript AI summaries depend on backend processing
- Some API endpoints may return empty data until backend is connected

### Files Affected
- `frontend/src/app/(dashboard)/meetings/page.tsx` (NEW)
- `frontend/src/app/(dashboard)/transcripts/page.tsx` (NEW)
- `frontend/src/app/(dashboard)/contracts/page.tsx` (NEW)
- `frontend/src/app/(dashboard)/rfis/page.tsx` (NEW)
- `frontend/src/app/(dashboard)/admin/audit/page.tsx` (NEW)
- `frontend/src/app/(dashboard)/analytics/page.tsx` (NEW)
- `frontend/src/components/layout/app-shell.tsx` (UPDATED - navigation)
- `frontend/src/lib/design-system.ts` (UPDATED - added neutral badge)
