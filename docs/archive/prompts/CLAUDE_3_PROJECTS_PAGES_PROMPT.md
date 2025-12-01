# Claude 3: Complete Projects Pages & RLHF Integration

## Context
You previously built the **invoice-aging-widget.tsx** (331 lines, production-ready) and backend invoice aging methods. Now complete the projects pages to make this widget accessible to users.

## Your Previous Work
- ✅ `backend/services/invoice_service.py` - Aging calculation methods
- ✅ `frontend/src/components/dashboard/invoice-aging-widget.tsx` - Beautiful widget
- ✅ Backend API: 4 invoice aging endpoints working

## What You Need to Build Now

### 1. Projects List Page (`/projects`)

**File:** `frontend/src/app/(dashboard)/projects/page.tsx`

**Requirements:**
- Show all active projects in a table/grid
- Display key info: Project code, name, client, status, total fee, outstanding balance
- Add filters: Status (active/completed), Client dropdown, Search by code/name
- Integrate your **InvoiceAgingWidget** at the top (full mode, not compact)
- Add "View Details" button for each project → links to `/projects/[code]`

**Data Source:**
- Backend: `GET /api/projects` (already exists)
- Use React Query: `useQuery(['projects'], () => api.get('/api/projects'))`

**Design:**
- Follow Claude 5's overview dashboard style
- Use shadcn/ui Table or Card components
- Mobile responsive (stack on small screens)

---

### 2. Project Detail Page (`/projects/[code]`)

**File:** `frontend/src/app/(dashboard)/projects/[code]/page.tsx`

**Requirements:**

#### Section A: Project Summary
- Project name, code, client
- Total fee, paid amount, outstanding balance
- Status badge (active/completed/on-hold)
- Contract dates (start, end, duration)

#### Section B: Invoice Aging Breakdown
- Show invoices for THIS project only
- Table: Invoice number, date, amount, due date, aging (days), status
- Color-code by aging: <30 days (green), 30-90 (yellow), >90 (red)
- Total outstanding for this project

#### Section C: Email Feed
**CRITICAL:** Integrate Claude 1's email system
- Show emails linked to this project
- Use: `GET /api/emails/by-project/${projectCode}` (Claude 1 built this)
- Display: Date, subject, from, category badge
- Link to full email view
- Show last 10 emails with "View All" link to `/emails?project=${code}`

#### Section D: Recent Activity
- Contract milestones (if available)
- Invoice payment history
- Status changes

**Data Sources:**
- `GET /api/projects/${code}` (project details)
- `GET /api/invoices?project_code=${code}` (invoices)
- `GET /api/emails/by-project/${code}` (emails from Claude 1)

---

### 3. Add RLHF Feedback Integration

**Use Claude 2's Infrastructure:**
```typescript
import { FeedbackButtons } from '@/components/ui/feedback-buttons'
import { api } from '@/lib/api'
```

**Add Feedback to:**

#### A. Invoice Flags (Detail Page)
```typescript
// Next to each invoice in the detail page
<FeedbackButtons
  featureType="invoice_flag"
  featureId={invoice.invoice_id}
  type="helpful"
  onFeedback={(helpful) => {
    api.logFeedback({
      feature_type: 'invoice_flag',
      feature_id: invoice.invoice_id,
      helpful,
      context: { project_code: projectCode, invoice_amount: invoice.amount }
    })
  }}
/>
```

#### B. Project Status (Detail Page)
```typescript
// Next to project status badge
<FeedbackButtons
  featureType="project_status"
  featureId={projectCode}
  originalValue={project.status}
  type="correction"
  options={['active', 'completed', 'on_hold', 'cancelled']}
  onCorrectionSubmit={(newStatus) => {
    api.logFeedback({
      feature_type: 'project_status',
      feature_id: projectCode,
      original_value: project.status,
      corrected_value: newStatus
    })
    // Optionally update project status via API
  }}
/>
```

#### C. Outstanding Balance Accuracy (List Page)
```typescript
// Add "Flag incorrect amount" button
<Button
  variant="ghost"
  size="sm"
  onClick={() => {
    api.logFeedback({
      feature_type: 'outstanding_balance',
      feature_id: project.code,
      helpful: false,
      feedback_text: 'User flagged as incorrect'
    })
  }}
>
  Flag Issue
</Button>
```

---

## Technical Details

### API Endpoints You Can Use

**From your work:**
```
GET /api/invoices/aging/last-paid?limit=5
GET /api/invoices/aging/largest-outstanding?limit=10
GET /api/invoices/aging/breakdown
GET /api/invoices/summary
```

**From existing backend:**
```
GET /api/projects - All projects
GET /api/projects/${code} - Single project
GET /api/invoices?project_code=${code} - Project invoices
```

**From Claude 1 (emails):**
```
GET /api/emails/by-project/${code} - Emails linked to project
GET /api/emails/${id} - Single email detail
```

**From Claude 2 (RLHF):**
```
POST /api/training/feedback - Log user feedback
```

### Data Flow Example

```typescript
// projects/[code]/page.tsx

'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { InvoiceAgingWidget } from '@/components/dashboard/invoice-aging-widget'
import { FeedbackButtons } from '@/components/ui/feedback-buttons'

export default function ProjectDetailPage({ params }: { params: { code: string } }) {
  const { data: project } = useQuery(
    ['project', params.code],
    () => api.get(`/api/projects/${params.code}`)
  )

  const { data: invoices } = useQuery(
    ['invoices', params.code],
    () => api.get(`/api/invoices?project_code=${params.code}`)
  )

  const { data: emails } = useQuery(
    ['emails', params.code],
    () => api.get(`/api/emails/by-project/${params.code}`)
  )

  return (
    <div className="container mx-auto p-6">
      {/* Project Summary */}
      <div className="mb-8">
        <h1>{project.name}</h1>
        <div className="flex items-center gap-2">
          <Badge>{project.status}</Badge>
          <FeedbackButtons
            featureType="project_status"
            featureId={params.code}
            originalValue={project.status}
            type="correction"
          />
        </div>
      </div>

      {/* Invoice Aging */}
      <section className="mb-8">
        <h2>Invoice Aging</h2>
        {/* Use your widget or custom table */}
        <InvoiceTable invoices={invoices} projectCode={params.code} />
      </section>

      {/* Email Feed */}
      <section className="mb-8">
        <h2>Recent Emails</h2>
        <EmailList emails={emails} limit={10} />
      </section>
    </div>
  )
}
```

---

## File Structure to Create

```
frontend/src/app/(dashboard)/projects/
├── page.tsx                    # Projects list page
└── [code]/
    └── page.tsx                # Project detail page

frontend/src/components/projects/  (optional, if you want to break out components)
├── project-card.tsx
├── project-table.tsx
├── invoice-table.tsx
└── email-feed.tsx
```

---

## Testing Checklist

After building, test:

- [ ] Can access `/projects` page
- [ ] Projects list loads and displays correctly
- [ ] Filters work (status, client, search)
- [ ] Invoice aging widget shows on projects list page
- [ ] Can click "View Details" → navigates to `/projects/[code]`
- [ ] Detail page loads project info
- [ ] Invoices for project display with aging colors
- [ ] Email feed shows project emails (from Claude 1)
- [ ] Feedback buttons work and log to training_data
- [ ] Mobile responsive (test on small screens)
- [ ] No console errors

---

## Dependencies Already Available

**Backend Services:**
- `invoice_service.py` (your work) ✅
- `email_service.py` (Claude 1) ✅
- `training_data_service.py` (Claude 2) ✅

**Frontend Components:**
- `invoice-aging-widget.tsx` (your work) ✅
- `feedback-buttons.tsx` (Claude 2) ✅
- shadcn/ui components (Button, Table, Card, Badge) ✅
- React Query setup ✅

**API Client:**
- `frontend/src/lib/api.ts` (has logFeedback method) ✅

---

## Reference Files

1. **Your context file:** `claude_context_active_projects.md`
2. **Claude 5's dashboard:** `frontend/src/app/(dashboard)/page.tsx` (for design patterns)
3. **Claude 4's tracker:** `frontend/src/app/(dashboard)/tracker/page.tsx` (for table/list patterns)
4. **Claude 1's emails:** `frontend/src/app/(dashboard)/emails/page.tsx` (for email display)
5. **RLHF guide:** `RLHF_IMPLEMENTATION_GUIDE.md` (Claude 2's docs)

---

## Success Criteria

✅ User can browse all projects at `/projects`
✅ User can see invoice aging widget on projects page
✅ User can click into any project → see full details
✅ Project detail shows invoices with aging breakdown
✅ Project detail shows email feed from Claude 1
✅ User can flag incorrect data → logs to training_data
✅ All pages are mobile responsive
✅ Zero TypeScript errors, zero runtime errors

---

## Estimated Time: 3-4 hours

- Projects list page: 1 hour
- Project detail page: 1.5 hours
- RLHF integration: 0.5 hours
- Testing & polish: 1 hour

---

## Questions?

If you encounter issues:
1. Check Claude 1's email API endpoints (`backend/api/main.py` - search "emails")
2. Check Claude 2's feedback API (`backend/api/main.py` - search "training")
3. Reference your own invoice_service.py for data structure
4. Look at Claude 5's dashboard for component patterns

---

## Final Note

This completes your 40% → 100% journey! The invoice aging widget you built is production-ready. Now give it a home where Bill can actually use it.

**After you're done, report back in COORDINATION_MASTER.md:**
- Mark your status as "✅ COMPLETE (100%)"
- List the files you created
- Note any issues or blockers

Good luck! 🚀
