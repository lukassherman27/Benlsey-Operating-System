# Agent 3: Dashboard Widgets & Metrics Fixes

## Your Mission
You are responsible for fixing dashboard widgets, metrics calculations, and adding the meetings widget.

## Context
- **Codebase**: Bensley Design Studio Operations Platform
- **Backend**: FastAPI (Python) at `backend/api/main.py` and `backend/services/financial_service.py`
- **Frontend**: Next.js 15 at `frontend/src/components/dashboard/`
- **Database**: SQLite at `database/bensley_master.db`

## Current State & Problems

### Problem 1: Invoice Aging vs Outstanding Discrepancy
**Issue**: Two numbers don't match
- Invoice aging: 4.299
- Outstanding invoice: 4.64
**Need**: Investigate why different, fix to show same number

### Problem 2: Recent Payments Widget Wrong
**File**: `frontend/src/components/dashboard/recent-activity-widget.tsx` (or similar)
**Current display**:
```
Sep 4  | I24-078 | $3,578   | general
Oct 22 | I24-080 | $351     | general
Oct 22 | I25-001 | $2,057   | general
```

**Problems**:
- Shows "general" instead of phase/discipline (should show "Landscape Concept Design" or "Interior Design Development")
- No project name (need to add)
- Invoice number too big

**Expected**:
```
Project Name              | Phase/Discipline              | Amount    | Date
-------------------------------------------------------------------------
Wynn Marjan              | Interior Design Development   | $3,578    | Sep 4
Mandarin Oriental Bali   | Landscape Concept Design      | $351      | Oct 22
```

### Problem 3: Top 5 Projects by Outstanding
**Issue**: Shows "$X outstanding" but "0 overdue invoices" for all projects
**File**: Likely in `financial-dashboard.tsx` or similar
**Fix**: API call incorrect - need to count invoices where due_date < TODAY

### Problem 4: Aging Invoices Widget
**Issues**:
- Invoices 600-900 days old should be RED
- Need to show phase/scope (e.g., "Interior Design Development for Restaurant")
- Invoice number too big
- Need project name

**Example output wanted**:
```
Project Name       | Phase/Scope                      | Days Old | Amount
---------------------------------------------------------------------------
Art Deco [RED]     | Interior / Sale Center / Concept | 612 days | $50,000
Ultra Luxury [RED] | Landscape / Mobilization         | 890 days | $400,000
```

### Problem 5: Uninvoiced Work Widget
**Issue**: Shows "0% invoiced" for all projects
**Cause**: Related to Agent 2's critical bug - API not calculating correctly
**Fix**: Use correct invoice totals

### Problem 6: NO MEETINGS WIDGET
**Need**: Extract meeting info from emails and display today's meetings
**Data source**: Email content (extract meeting dates/times using AI)

## Your Tasks

### Task 1: Investigate Invoice Aging Discrepancy
1. Find where "4.299" and "4.64" are calculated
2. Check SQL queries in `financial_service.py`
3. Determine which is correct
4. Fix the incorrect one to match

### Task 2: Fix Recent Payments Widget
1. Find recent payments component in `frontend/src/components/dashboard/`
2. Update to fetch breakdown data:
```python
# Backend query
SELECT
    p.project_title,
    i.invoice_number,
    i.payment_amount,
    i.payment_date,
    pfb.discipline,
    pfb.phase,
    pfb.scope
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
LEFT JOIN project_fee_breakdown pfb ON i.breakdown_id = pfb.breakdown_id
WHERE i.payment_date IS NOT NULL
ORDER BY i.payment_date DESC
LIMIT 5
```

3. Update frontend display:
   - Add project_title column
   - Show phase/discipline/scope instead of "general"
   - Reduce invoice_number font size
   - Format: "Discipline - Phase" or "Discipline / Scope / Phase"

### Task 3: Fix Top 5 Projects by Outstanding
1. Find the widget (likely `invoice-aging-widget.tsx`)
2. Fix overdue calculation:
```python
SELECT
    p.project_title,
    p.project_code,
    SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)) as outstanding,
    COUNT(CASE WHEN i.due_date < DATE('now') AND i.status != 'paid' THEN 1 END) as overdue_count
FROM projects p
JOIN invoices i ON p.project_id = i.project_id
WHERE p.is_active_project = 1
GROUP BY p.project_id
ORDER BY outstanding DESC
LIMIT 5
```

3. Display overdue count correctly

### Task 4: Fix Aging Invoices Widget
1. Add color coding:
```typescript
const getAgeColor = (daysOld: number) => {
  if (daysOld > 600) return 'text-red-600 font-bold'
  if (daysOld > 365) return 'text-orange-500'
  if (daysOld > 180) return 'text-yellow-500'
  return 'text-gray-600'
}
```

2. Update query to include phase/scope:
```python
SELECT
    p.project_title,
    i.invoice_number,
    i.invoice_date,
    JULIANDAY('now') - JULIANDAY(i.invoice_date) as days_old,
    i.invoice_amount - COALESCE(i.payment_amount, 0) as outstanding,
    pfb.discipline,
    pfb.phase,
    pfb.scope
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
LEFT JOIN project_fee_breakdown pfb ON i.breakdown_id = pfb.breakdown_id
WHERE i.status != 'paid' AND i.invoice_date IS NOT NULL
ORDER BY days_old DESC
LIMIT 10
```

3. Display format: "Project | Discipline / Scope / Phase | Days (colored) | Amount"

### Task 5: Fix Uninvoiced Work Widget
1. Coordinate with Agent 2's fix for 0% invoiced bug
2. Update query to use correct calculations
3. Show top 5 contracts by remaining value:
```python
SELECT
    p.project_title,
    p.total_fee_usd,
    COALESCE(SUM(i.invoice_amount), 0) as total_invoiced,
    p.total_fee_usd - COALESCE(SUM(i.invoice_amount), 0) as remaining,
    (COALESCE(SUM(i.invoice_amount), 0) / p.total_fee_usd * 100) as percentage_invoiced
FROM projects p
LEFT JOIN invoices i ON p.project_id = i.project_id
WHERE p.is_active_project = 1 AND p.total_fee_usd > 0
GROUP BY p.project_id
ORDER BY remaining DESC
LIMIT 5
```

### Task 6: Create Meetings Widget
1. Create new component: `frontend/src/components/dashboard/meetings-widget.tsx`
2. Create backend service to extract meetings from emails:
   - Use `email_intelligence_service.py` or create new service
   - Use Claude API to extract meeting info from email content:
     - Date/time
     - Attendees
     - Subject/purpose
     - Project link
3. Store in new table `meetings` or extract on-the-fly
4. Display today's meetings:
```
Today's Meetings
----------------
10:00 AM - Client Call - Wynn Marjan Project
2:00 PM - Design Review - Capella Ubud
```

5. Add to main dashboard

## Expected Deliverables

1. **Fixed invoice aging** - numbers match
2. **Updated recent payments widget** with project names, phase/discipline
3. **Fixed top 5 outstanding** with correct overdue counts
4. **Updated aging invoices widget** with red color for 600+ days, phase/scope
5. **Fixed uninvoiced work widget** with correct percentages
6. **New meetings widget** showing today's schedule from emails
7. **All widgets show project names** instead of codes

## Success Criteria

- ✅ Invoice aging = Outstanding invoice (numbers match)
- ✅ Recent payments show phase/discipline (not "general")
- ✅ Overdue invoice counts display correctly
- ✅ Aging invoices show red for 600+ days old
- ✅ Phase/scope visible in all relevant widgets
- ✅ Uninvoiced work shows real percentages (not 0%)
- ✅ Meetings widget displays today's meetings from emails
- ✅ All displays use project names, not codes

## Testing Checklist

- [ ] Check dashboard - numbers are consistent
- [ ] Recent payments - see phase/discipline
- [ ] Top 5 outstanding - see overdue counts
- [ ] Aging invoices - 600+ days are red
- [ ] Uninvoiced work - see real percentages
- [ ] Meetings widget - shows today's meetings

## Notes
- Coordinate with Agent 2 for invoice calculations
- Coordinate with Agent 4 for email-based meeting extraction
- Use consistent formatting across all widgets
