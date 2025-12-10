# Role-Based Dashboard Stats Implementation

## Overview

Implemented role-based dashboard statistics endpoint that returns different KPIs based on user role (Executive, PM, Finance).

## Endpoint

**URL:** `GET /api/dashboard/stats`

**Query Parameters:**
- `role` (optional): Role filter - `bill`, `pm`, or `finance`

## Implementation Details

### File Modified
- `/backend/api/routers/dashboard.py`

### Changes Made

1. **Added `get_role_based_stats()` helper function** (lines 33-185)
   - Handles role-specific KPI calculations
   - Returns tailored metrics for each role
   - Proper database connection management with try/finally

2. **Updated `get_dashboard_stats()` endpoint** (lines 192-233)
   - Added optional `role` query parameter
   - Routes to role-specific function if role is provided
   - Maintains backward compatibility (returns legacy stats if no role)

### Role-Specific KPIs

#### Bill (Executive) - `?role=bill`
```json
{
  "role": "bill",
  "pipeline_value": float,              // SUM of active proposals (from proposals table)
  "active_projects_count": int,         // COUNT of active projects
  "outstanding_invoices_total": float,  // SUM of unpaid invoice amounts
  "overdue_invoices_count": int        // COUNT of overdue invoices
}
```

**Queries:**
- Pipeline: Active proposals (is_active_project=0, not completed/lost/declined)
- Projects: status='Active' OR is_active_project=1
- Outstanding: invoices where (invoice_amount - payment_amount) > 0
- Overdue: outstanding invoices where due_date < today

#### PM (Project Manager) - `?role=pm`
```json
{
  "role": "pm",
  "my_projects_count": int,             // COUNT of active projects
  "deliverables_due_this_week": int,    // COUNT from project_milestones
  "open_rfis_count": int               // COUNT of open RFIs
}
```

**Queries:**
- Projects: status='Active' OR is_active_project=1
- Deliverables: project_milestones where planned_date in next 7 days, status not completed/cancelled
- RFIs: rfis table where status='open'

#### Finance - `?role=finance`
```json
{
  "role": "finance",
  "total_outstanding": float,           // Total unpaid invoices
  "overdue_30_days": float,            // Overdue 30+ days
  "overdue_60_days": float,            // Overdue 60+ days
  "overdue_90_plus": float,            // Overdue 90+ days
  "recent_payments_7_days": float      // Payments in last 7 days
}
```

**Queries:**
- Total Outstanding: All unpaid invoice amounts
- Overdue buckets: Outstanding invoices grouped by due_date age
- Recent Payments: SUM of payment_amount where payment_date in last 7 days

## Database Tables Used

| Table | Purpose |
|-------|---------|
| `proposals` | Pipeline value calculation |
| `projects` | Active project counts |
| `invoices` | Outstanding/overdue amounts, recent payments |
| `project_milestones` | Upcoming deliverables |
| `rfis` | Open RFI count |

## Testing

### Manual Testing with curl

```bash
# Start backend
cd backend && uvicorn api.main:app --reload --port 8000

# Test each role
curl http://localhost:8000/api/dashboard/stats?role=bill
curl http://localhost:8000/api/dashboard/stats?role=pm
curl http://localhost:8000/api/dashboard/stats?role=finance

# Test legacy endpoint (backward compatibility)
curl http://localhost:8000/api/dashboard/stats
```

### Automated Testing

```bash
# Run test script
cd backend
python test_dashboard_stats.py
```

## Current Data (as of implementation)

Based on database queries:
- **Proposals:** 102 total, ~$176.6M pipeline value
- **Projects:** 60 total, 52 active
- **Invoices:** 420 total, ~$4.8M outstanding
- **RFIs:** 3 open
- **Milestones:** Available in project_milestones table

## Error Handling

- Returns 400 if invalid role is provided
- Returns 500 with error message if database query fails
- Proper connection cleanup in finally block
- Rounds currency values to 2 decimal places

## Backward Compatibility

- Original `/api/dashboard/stats` endpoint still works without role parameter
- Returns comprehensive stats using existing services (proposal_service, email_service, etc.)
- No breaking changes to existing API consumers

## API Documentation

The endpoint is automatically documented in FastAPI's OpenAPI docs:
- http://localhost:8000/docs
- http://localhost:8000/redoc

## Next Steps

1. Start backend server
2. Run test script to verify all endpoints
3. Integrate with frontend dashboard components
4. Add user authentication to automatically determine role
5. Consider caching for frequently accessed KPIs

## Notes

- All values rounded to 2 decimal places for currency
- Date calculations use SQLite's date() functions
- Active projects determined by: status='Active' OR is_active_project=1
- Pipeline excludes: completed, lost, declined, cancelled, archived statuses
