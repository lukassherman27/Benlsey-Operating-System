# Project Status View Implementation Plan

**Issue:** #197 - Complete project status view with all linked data
**Author:** Claude
**Date:** 2025-12-31

---

## Executive Summary

**Good news: The project detail page is already ~85% complete!**

After reviewing the existing code and comparing it to Issue #197 requirements, the current implementation at `/projects/[projectCode]/page.tsx` already includes most features requested:

| Feature | Status | Notes |
|---------|--------|-------|
| Hero Card (name, code, status, PM, client) | Done | Has project info, badges, financial summary |
| Financial Summary Card | Done | Contract value, invoiced, paid, outstanding with progress bars |
| Health Score Banner | Done | Client-side calculation with color-coded issues |
| Unified Timeline | Done | Emails, meetings, invoices, RFIs merged with filtering |
| Emails Tab | Done | ProjectEmailsCard in Overview tab |
| Meetings Tab | Done | ProjectMeetingsCard in Overview tab |
| Invoices View | Partial | In Finance tab, but no dedicated list with filters |
| RFIs Tab | Done | RFIDeliverablesPanel in Tasks tab |
| Team Tab | Done | BensleyTeamCard + ProjectContactsCard |
| Documents Tab | Missing | No OneDrive integration |
| Health API Endpoint | Missing | Calculated client-side, no dedicated endpoint |

---

## Gap Analysis

### What's Missing from Issue #197:

1. **Documents Tab** - Issue shows `[Documents]` tab for linked files from OneDrive
2. **Dedicated Health Endpoint** - `GET /api/projects/{code}/health`
3. **Invoices Detailed List** - A filterable invoices section (currently buried in Finance tab)

### What Already Exists (No Changes Needed):

- Hero card with project name, code, status, financial summary
- 7-tab layout: Overview, Phases, Daily Work, Deliverables, Team, Tasks, Finance
- UnifiedTimeline with type filtering, person filtering, email category filtering
- Health calculation with issues display
- Financial progress bars and stats
- Team assignments with roles
- Email and meeting previews
- Phase progress tracking

---

## Recommended Implementation

Given the page is largely complete, I recommend **minimal focused enhancements**:

### Option A: Quick Wins (Recommended)

1. **Add Health API Endpoint** - 2 hours
   - Create `GET /api/projects/{code}/health`
   - Move client-side calculation to backend
   - Return health score + issues array

2. **Add Invoices Card to Overview Tab** - 2 hours
   - New `ProjectInvoicesCard` component
   - Show last 5 invoices with status badges
   - Click to expand in Finance tab

3. **Improve Tab Organization** - 1 hour
   - Consider moving RFIs from Tasks to Overview
   - Group related items better

**Total: ~5 hours**

### Option B: Full Documents Integration (Larger Scope)

Everything in Option A, plus:

4. **Add Documents Tab** - 8-16 hours
   - Create `project_documents` or `documents` table linkage
   - Build OneDrive API integration (if not exists)
   - Create `ProjectDocumentsCard` component
   - New API endpoint `GET /api/projects/{code}/documents`

**Total: ~13-21 hours**

---

## Technical Implementation Details

### 1. Health API Endpoint

**File:** `backend/api/routers/projects.py`

```python
@router.get("/projects/{project_code}/health")
async def get_project_health(project_code: str):
    """
    Calculate and return project health score.

    Health = weighted average of:
    - Invoice payment status (30%)
    - RFI response time (20%)
    - Email recency (20%)
    - Deliverable status (30%)
    """
    # Implementation details...
```

**Response Schema:**
```json
{
  "success": true,
  "project_code": "25 BK-033",
  "health_score": 75,
  "status": "warning",  // "healthy" | "warning" | "critical"
  "issues": [
    {"type": "overdue_invoice", "message": "2 invoices overdue ($45,000)", "severity": "high"},
    {"type": "open_rfi", "message": "3 RFIs pending > 14 days", "severity": "medium"}
  ],
  "metrics": {
    "invoice_health": 60,
    "rfi_health": 80,
    "activity_health": 90,
    "deliverable_health": 70
  }
}
```

### 2. Invoices Card Component

**File:** `frontend/src/components/project/project-invoices-card.tsx`

```tsx
interface ProjectInvoicesCardProps {
  projectCode: string;
  limit?: number;
}

// Show recent invoices with:
// - Invoice number
// - Amount
// - Status badge (paid/pending/overdue)
// - Due date
// - Click to view in Finance tab
```

### 3. Tab Layout Improvements

Current tabs: `Overview | Phases | Daily Work | Deliverables | Team | Tasks | Finance`

Suggested reorganization:
- Move communication items (Emails, Meetings preview) to be more prominent in Overview
- Consider adding an "Invoices" quick summary card to Overview
- Keep detailed Finance tab for drill-down

---

## Database Queries

### Health Score Calculation Query

```sql
-- Get health metrics for a project
SELECT
    -- Overdue invoices
    (SELECT COUNT(*) FROM invoices i
     JOIN projects p ON i.project_id = p.project_id
     WHERE p.project_code = ? AND i.status != 'paid'
     AND i.due_date < date('now')) as overdue_invoices,

    -- Overdue amount
    (SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0)
     FROM invoices i JOIN projects p ON i.project_id = p.project_id
     WHERE p.project_code = ? AND i.status != 'paid'
     AND i.due_date < date('now')) as overdue_amount,

    -- Open RFIs
    (SELECT COUNT(*) FROM rfis r
     JOIN projects p ON r.project_id = p.project_id
     WHERE p.project_code = ? AND r.status = 'open') as open_rfis,

    -- Days since last email
    (SELECT JULIANDAY('now') - JULIANDAY(MAX(e.date))
     FROM emails e
     JOIN email_project_links epl ON e.email_id = epl.email_id
     WHERE epl.project_code = ?) as days_since_email
```

---

## Files to Modify/Create

### Backend
- [ ] `backend/api/routers/projects.py` - Add `/health` endpoint

### Frontend
- [ ] `frontend/src/components/project/project-invoices-card.tsx` - New component
- [ ] `frontend/src/app/(dashboard)/projects/[projectCode]/page.tsx` - Add invoices card to Overview

---

## Success Criteria (from Issue #197)

- [x] One page shows EVERYTHING about a project - **Already achieved**
- [x] Financial summary is accurate - **Already achieved**
- [x] All linked data accessible without navigation - **Mostly achieved (tabs)**
- [ ] PMs can answer any project question from this view - **Needs health endpoint**
- [x] Page loads in <2 seconds - **Already fast with react-query**

---

## Recommendation

**I recommend Option A (Quick Wins)** because:

1. The page is already very comprehensive
2. Documents integration is a larger scope (OneDrive API)
3. The main value add is the Health API endpoint
4. Adding invoices preview improves Overview tab completeness

---

## Questions for User

1. **Is the current tab structure acceptable?** The page has 7 tabs which follows UX best practices (7-8 elements max).

2. **Do you need the Documents tab?** This requires OneDrive integration which is a bigger project.

3. **Should the health calculation move to backend?** Currently calculated client-side - moving to API allows caching and consistency.

4. **Priority: Health endpoint vs Invoices card?** Which would you like first?

---

## UX Research Applied

Based on dashboard design best practices research:

1. **Clarity and Focus** - The current page focuses on what PMs need
2. **Visual Consistency** - Uses consistent card layouts and color schemes
3. **Limit Visual Elements** - 7 tabs + ~4 cards per tab follows the 7-8 element rule
4. **Smart Filtering** - UnifiedTimeline has type/person/category filters
5. **Actionable Insights** - Health banner shows issues with severity
6. **Contextual Information** - Progress bars show % invoiced/collected

Sources:
- [UXPin Dashboard Design Principles](https://www.uxpin.com/studio/blog/dashboard-design-principles/)
- [Pipedrive 360 Customer View](https://www.pipedrive.com/en/blog/360-customer-view)
- [Confluence Project Status Template](https://www.atlassian.com/software/confluence/templates/project-status)
