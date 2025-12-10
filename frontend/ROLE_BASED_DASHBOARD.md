# Role-Based Dashboard Implementation

## Overview

Implemented role-based dashboard components with three role views:
- **Executive (Bill)**: Pipeline value, active projects, outstanding invoices
- **PM**: My projects, deliverables due, open RFIs
- **Finance**: Outstanding invoices with aging breakdowns (30/60/90+ days)

## Components Created

### 1. KPICard Component
**Location**: `frontend/src/components/dashboard/kpi-card.tsx`

A reusable card component for displaying key performance indicators with:
- Large number display with formatting
- Label and subtitle text
- Optional trend indicator (up/down arrow + percentage)
- Color variants (default, success, warning, danger)
- Icon support
- Format helper: `formatLargeNumber()` for $87.5M style formatting

**Usage**:
```tsx
<KPICard
  label="Pipeline Value"
  value={formatLargeNumber(87500000)}
  subtitle="Active proposals"
  icon={<TrendingUp className="h-5 w-5" />}
  variant="default"
/>
```

### 2. RoleSwitcher Component
**Location**: `frontend/src/components/dashboard/role-switcher.tsx`

A tab-based role switcher with:
- Three tabs: Executive, PM, Finance
- localStorage persistence (key: 'dashboard_role')
- Default to 'bill' if not set
- Exports `useDashboardRole()` hook for easy integration

**Usage**:
```tsx
<RoleSwitcher onRoleChange={setRole} defaultRole={role} />
```

### 3. Updated Dashboard Page
**Location**: `frontend/src/app/(dashboard)/page.tsx`

- Integrates RoleSwitcher and KPICard components
- Fetches role-specific stats from `/api/dashboard/stats?role={role}`
- Shows different KPI cards based on selected role
- Maintains existing widgets (Hot Items, Follow-up, Calendar, etc.)

## Backend API

### Endpoint
`GET /api/dashboard/stats?role={bill|pm|finance}`

**Implemented in**: `backend/api/routers/dashboard.py`

### Response Examples

**Bill (Executive)**:
```json
{
  "role": "bill",
  "pipeline_value": 87473800.0,
  "active_projects_count": 59,
  "outstanding_invoices_total": 4843573.75,
  "overdue_invoices_count": 0
}
```

**PM**:
```json
{
  "role": "pm",
  "my_projects_count": 59,
  "deliverables_due_this_week": 0,
  "open_rfis_count": 3
}
```

**Finance**:
```json
{
  "role": "finance",
  "total_outstanding": 4843573.75,
  "overdue_30_days": 0,
  "overdue_60_days": 0,
  "overdue_90_plus": 0,
  "recent_payments_7_days": 0
}
```

## Design System Compliance

All components follow the Bensley Design System:
- Uses `@/lib/design-system` (ds object)
- Consistent spacing, typography, colors
- Border radius from `ds.borderRadius`
- Text colors from `ds.textColors`
- Card styles from `ds.cards`
- Icons from lucide-react

## Features

### State Management
- Role state stored in localStorage
- Persists across page refreshes
- useQuery with 5-minute refetch interval
- Automatic loading and error states

### Responsive Design
- Mobile-first grid layouts
- 1 column on mobile, 2-3 on tablet, 4 on desktop
- Executive view: 4 KPIs
- PM view: 3 KPIs
- Finance view: 4 KPIs (aging buckets)

### Number Formatting
- Large numbers shown as $87.5M instead of $87,500,000
- Uses formatLargeNumber() helper
- Rounds to 1 decimal for millions
- No decimals for thousands

## Testing

### Frontend Build
```bash
cd frontend
npm run build
```
✅ Build completes successfully with no errors

### Backend Test
```bash
cd backend
python -c "
from api.routers.dashboard import get_role_based_stats
import asyncio
asyncio.run(get_role_based_stats('bill'))
"
```
✅ Returns correct data for all roles

### Manual Testing Checklist
- [ ] Navigate to http://localhost:3002
- [ ] Verify role switcher displays three tabs
- [ ] Click Executive tab - see 4 KPIs (Pipeline, Active Projects, Outstanding, Overdue)
- [ ] Click PM tab - see 3 KPIs (My Projects, Deliverables Due, Open RFIs)
- [ ] Click Finance tab - see 4 KPIs (Outstanding + 30/60/90+ aging)
- [ ] Refresh page - verify selected role persists
- [ ] Check localStorage has 'dashboard_role' key
- [ ] Verify numbers format correctly ($87.5M not $87500000)
- [ ] Check loading states appear briefly
- [ ] Verify error handling if backend is down

## Future Enhancements

1. **Trend Data**: Backend could return trend information for KPIs
2. **PM Filtering**: Filter by specific PM name
3. **Finance Drill-down**: Click KPI to see detailed invoice list
4. **Recent Payments**: Add to Finance view (already in backend)
5. **Export**: CSV/PDF export of current view
6. **Alerts**: Visual alerts for critical thresholds (e.g., overdue > 10)

## Files Modified

- ✅ Created: `frontend/src/components/dashboard/kpi-card.tsx`
- ✅ Created: `frontend/src/components/dashboard/role-switcher.tsx`
- ✅ Updated: `frontend/src/app/(dashboard)/page.tsx`
- ✅ Created: `frontend/ROLE_BASED_DASHBOARD.md` (this file)

## Dependencies

All required dependencies already installed:
- @tanstack/react-query (for data fetching)
- lucide-react (for icons)
- @radix-ui/react-tabs (for tab component)
- date-fns (for date formatting)

No new dependencies needed!

## Architecture Notes

### Why Not Use api.ts getDashboardStats()?

The existing `api.getDashboardStats()` in `frontend/src/lib/api.ts` doesn't accept a role parameter. Rather than modify it and risk breaking existing usages, we:

1. Use direct fetch() with role parameter
2. Keep it simple and explicit
3. Can refactor later to extend api.ts if needed

### localStorage vs URL State

Using localStorage instead of URL params because:
- Simpler implementation
- Persists across all dashboard pages
- No need to update URLs
- User preference should be sticky

Could migrate to URL params later if needed for sharing links.

## Support

For issues or questions:
1. Check console for errors
2. Verify backend is running on port 8000
3. Check localStorage for 'dashboard_role' key
4. Inspect network tab for API call to /api/dashboard/stats
