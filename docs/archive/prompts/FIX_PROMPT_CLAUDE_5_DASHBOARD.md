# URGENT FIXES - Claude 5 (Dashboard)

**Your Task:** Fix KPI calculations showing wrong values
**Time:** 1 hour
**Priority:** URGENT - Shows 0s everywhere, breaks trust

---

## 🚨 BILL'S FEEDBACK

**Current Dashboard Shows:**
- Active Proposals: **0** ❌ (Should show ~12)
- Outstanding Invoices: **$0** ❌ (Should show $4.87M!)

**Quote:** "Active proposals right now is currently saying zero. And to the right of it, it's also saying 0 for outstanding, unpaid invoices. It doesn't make sense because then we have a widget below that that also has outstanding invoices, which says 4,874,000."

**Impact:** Contradictory data destroys user trust

---

## 🛠️ FIX #1: Backend KPI Endpoint

**Problem:** KPIs are hardcoded in frontend, not using real data

**Solution:** Create proper backend endpoint

**File:** `backend/api/main.py`

**Add this endpoint:**
```python
from datetime import datetime

@app.get("/api/dashboard/kpis")
def get_dashboard_kpis():
    """
    Get real-time KPI metrics for dashboard
    Returns actual counts/values from database
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Active Projects
        cursor.execute("""
            SELECT COUNT(*)
            FROM projects
            WHERE status = 'active'
        """)
        active_projects = cursor.fetchone()[0]

        # 2. Active Proposals (NOT ZERO!)
        cursor.execute("""
            SELECT COUNT(*)
            FROM proposals
            WHERE status IN ('active', 'sent', 'follow_up', 'drafting', 'first_contact')
            AND (on_hold = 0 OR on_hold IS NULL)
        """)
        active_proposals = cursor.fetchone()[0]

        # 3. Total Remaining Contract Value
        # (Total contracts minus what's been invoiced)
        cursor.execute("""
            SELECT
                COALESCE(SUM(CAST(p.total_fee AS REAL)), 0) as total_contract_value,
                COALESCE(SUM(CAST(i.invoice_amount AS REAL)), 0) as total_invoiced
            FROM projects p
            LEFT JOIN invoices i ON p.code = i.project_code AND i.paid_date IS NOT NULL
            WHERE p.status = 'active'
        """)
        row = cursor.fetchone()
        total_contracts = row[0] if row else 0
        total_invoiced = row[1] if row else 0
        remaining_contract_value = total_contracts - total_invoiced

        # 4. Outstanding Invoices (NOT ZERO!)
        cursor.execute("""
            SELECT COALESCE(SUM(CAST(invoice_amount AS REAL)), 0)
            FROM invoices
            WHERE paid_date IS NULL OR paid_date = ''
        """)
        outstanding_invoices = cursor.fetchone()[0]

        # 5. Total Revenue YTD
        cursor.execute("""
            SELECT COALESCE(SUM(CAST(invoice_amount AS REAL)), 0)
            FROM invoices
            WHERE paid_date IS NOT NULL
            AND strftime('%Y', paid_date) = strftime('%Y', 'now')
        """)
        revenue_ytd = cursor.fetchone()[0]

        conn.close()

        return {
            "active_projects": active_projects,
            "active_proposals": active_proposals,
            "remaining_contract_value": round(remaining_contract_value, 2),
            "outstanding_invoices": round(outstanding_invoices, 2),
            "revenue_ytd": round(revenue_ytd, 2),
            "timestamp": datetime.now().isoformat(),
            "currency": "USD"
        }

    except Exception as e:
        logger.error(f"Error calculating KPIs: {e}", exc_info=True)
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to calculate KPIs: {str(e)}")
```

**Test the endpoint:**
```bash
# Restart backend
cd backend
uvicorn api.main:app --reload --port 8000

# Test in browser or curl:
curl http://localhost:8000/api/dashboard/kpis

# Should return:
{
  "active_projects": 49,
  "active_proposals": 12,  # NOT 0!
  "remaining_contract_value": 15234567.89,
  "outstanding_invoices": 4874000.00,  # NOT 0!
  "revenue_ytd": 8500000.00,
  "timestamp": "2025-11-25T...",
  "currency": "USD"
}
```

---

## 🛠️ FIX #2: Frontend - Use API Instead of Hardcoded

**File:** `frontend/src/components/dashboard/kpi-cards.tsx`

**BEFORE (Hardcoded - WRONG):**
```typescript
const kpiData = {
  activeRevenue: 4234567.89,  // Hardcoded!
  activeProjects: 23,          // Hardcoded!
  activeProposals: 12,         // Hardcoded!
  outstandingInvoices: 987654.32  // Hardcoded!
}
```

**AFTER (API - CORRECT):**
```typescript
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function KPICards() {
  const { data: kpis, isLoading, error } = useQuery({
    queryKey: ['dashboard-kpis'],
    queryFn: () => api.get('/api/dashboard/kpis'),
    refetchInterval: 5 * 60 * 1000  // Refresh every 5 minutes
  })

  if (isLoading) {
    return <KPICardsSkeleton />
  }

  if (error) {
    return <div>Error loading KPIs</div>
  }

  return (
    <div className="grid grid-cols-4 gap-6">
      <KPICard
        title="Active Projects"
        value={kpis.active_projects}
        icon={<FolderIcon />}
      />
      <KPICard
        title="Active Proposals"
        value={kpis.active_proposals}  // Real data!
        icon={<FileTextIcon />}
      />
      <KPICard
        title="Remaining Contract Value"
        value={formatCurrency(kpis.remaining_contract_value)}
        icon={<DollarSignIcon />}
      />
      <KPICard
        title="Outstanding Invoices"
        value={formatCurrency(kpis.outstanding_invoices)}  // Real data!
        icon={<AlertCircleIcon />}
      />
    </div>
  )
}
```

---

## 🎯 BILL'S REQUESTED KPI CHANGES

Bill wants different KPIs than what's currently there:

### Current KPIs (Wrong):
```
[Active Revenue] [Active Projects] [Active Proposals] [Outstanding]
```

### Bill's Requested KPIs (Correct):
```
[Total Remaining Contract Value] [Active Projects & Proposals] [Total Invoiced (Year)] [Unpaid Invoices]
```

### Updated KPI Structure:

```typescript
<div className="grid grid-cols-4 gap-6">
  {/* KPI #1: Total Remaining Contract Value */}
  <KPICard
    title="Remaining Contract Value"
    subtitle="Signed but not yet invoiced"
    value={formatCurrency(kpis.remaining_contract_value)}
    trend={calculateTrend(kpis.remaining_contract_value, previousMonth)}
    icon={<TrendingUpIcon />}
  />

  {/* KPI #2: Active Projects */}
  <KPICard
    title="Active Projects"
    subtitle={`${kpis.active_proposals} active proposals`}
    value={kpis.active_projects}
    icon={<FolderIcon />}
  />

  {/* KPI #3: Total Invoiced (Year) */}
  <KPICard
    title="Revenue (YTD)"
    subtitle="Total invoiced this year"
    value={formatCurrency(kpis.revenue_ytd)}
    trend={calculateYoYTrend(kpis.revenue_ytd)}
    icon={<DollarSignIcon />}
  />

  {/* KPI #4: Unpaid Invoices */}
  <KPICard
    title="Outstanding Invoices"
    subtitle="Unpaid invoices"
    value={formatCurrency(kpis.outstanding_invoices)}
    trend={calculateAgingTrend(kpis.outstanding_invoices)}
    trendColor="red"  // Red if increasing!
    icon={<AlertCircleIcon />}
  />
</div>
```

---

## 🎨 ADD TREND INDICATORS (Bill Loves These!)

**Bill's Quote:** "I do like the little top right of the widget where it has like the +8.2%. I know right now it's probably a placeholder. But having that kind of trend analysis, so we know kind of where we're headed on an overview level, is quite good."

**Add trend calculation:**
```typescript
function calculateTrend(current: number, previous: number): {
  percentage: number
  direction: 'up' | 'down' | 'neutral'
} {
  if (!previous || previous === 0) return { percentage: 0, direction: 'neutral' }

  const change = ((current - previous) / previous) * 100

  return {
    percentage: Math.abs(change),
    direction: change > 0 ? 'up' : change < 0 ? 'down' : 'neutral'
  }
}

// Usage in KPICard:
<div className="flex items-center gap-2">
  <span className="text-2xl font-bold">{value}</span>
  {trend && (
    <span className={cn(
      "text-sm font-medium",
      trend.direction === 'up' ? 'text-green-600' : 'text-red-600'
    )}>
      {trend.direction === 'up' ? '↗' : '↘'} {trend.percentage.toFixed(1)}%
    </span>
  )}
</div>
```

---

## 🧪 TESTING CHECKLIST

- [ ] Backend endpoint `/api/dashboard/kpis` returns real data
- [ ] Active Proposals shows actual count (NOT 0)
- [ ] Outstanding Invoices shows actual amount (NOT $0)
- [ ] Values match what's in database
- [ ] Values update when data changes
- [ ] Trend indicators show (+/- %)
- [ ] No console errors
- [ ] Auto-refreshes every 5 minutes

**Manual Test:**
```sql
-- Verify counts in database:
SELECT COUNT(*) FROM proposals WHERE status IN ('active', 'sent', 'follow_up');
-- Should match "Active Proposals" KPI

SELECT SUM(CAST(invoice_amount AS REAL)) FROM invoices WHERE paid_date IS NULL;
-- Should match "Outstanding Invoices" KPI (e.g., 4874000.00)
```

---

## 📊 DEBUG IF STILL SHOWING 0

If KPIs still show 0 after fix:

1. **Check backend logs:**
```bash
cd backend
uvicorn api.main:app --reload --port 8000
# Watch for errors when endpoint is called
```

2. **Check browser console:**
- Open http://localhost:3002
- F12 → Network tab
- Look for `/api/dashboard/kpis` request
- Check response data

3. **Check database:**
```bash
sqlite3 database/bensley_master.db

SELECT COUNT(*) as active_proposals FROM proposals
WHERE status IN ('active', 'sent', 'follow_up');

SELECT SUM(CAST(invoice_amount AS REAL)) as outstanding
FROM invoices WHERE paid_date IS NULL;
```

---

## 🎯 SUCCESS CRITERIA

✅ Active Proposals shows real count (e.g., 12, NOT 0)
✅ Outstanding Invoices shows real amount (e.g., $4.87M, NOT $0)
✅ KPIs match database values
✅ Trend indicators visible and accurate
✅ Dashboard auto-refreshes every 5 minutes
✅ No more contradictory data between widgets

---

## 📝 REPORT BACK

When done, update COORDINATION_MASTER.md:

```markdown
### Claude 5: Dashboard KPIs - URGENT FIXES
Status: ✅ FIXED
Date: 2025-11-25

Bugs Fixed:
1. ✅ Active Proposals now shows real count (was 0)
2. ✅ Outstanding Invoices shows real amount (was $0)
3. ✅ Added backend /api/dashboard/kpis endpoint
4. ✅ Trend indicators added to all KPIs

Files Modified:
- backend/api/main.py (new endpoint)
- frontend/src/components/dashboard/kpi-cards.tsx (use API)

Testing: All KPIs show correct values, auto-refresh working
```

---

**TIME ESTIMATE:** 1 hour

**PRIORITY:** URGENT - Wrong data destroys trust

**Bill's Impact:** "It doesn't make sense" → Fix this first!
