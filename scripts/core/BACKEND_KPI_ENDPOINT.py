# Backend KPI Endpoint - Add to backend/api/main.py

"""
This endpoint calculates real-time KPI metrics for the dashboard.
Currently, Claude 5's dashboard has hardcoded KPI values.
This endpoint provides real data from the database.

Add this to: backend/api/main.py
"""

@app.get("/api/dashboard/kpis")
def get_dashboard_kpis():
    """
    Get real-time KPI metrics for dashboard

    Returns:
    - active_revenue: Total fees for active projects
    - active_projects: Count of active projects
    - active_proposals: Count of proposals in active/follow_up status
    - outstanding_invoices: Total unpaid invoice amount
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Active Revenue (sum of fees for active projects)
        cursor.execute("""
            SELECT COALESCE(SUM(CAST(total_fee AS REAL)), 0)
            FROM projects
            WHERE status = 'active'
        """)
        active_revenue = cursor.fetchone()[0]

        # 2. Active Projects Count
        cursor.execute("""
            SELECT COUNT(*)
            FROM projects
            WHERE status = 'active'
        """)
        active_projects = cursor.fetchone()[0]

        # 3. Active Proposals Count
        # Note: Check what status values exist in your proposals table
        # Common: 'active', 'follow_up', 'pending', 'in_progress'
        cursor.execute("""
            SELECT COUNT(*)
            FROM proposals
            WHERE status IN ('active', 'follow_up', 'pending')
        """)
        active_proposals = cursor.fetchone()[0]

        # 4. Outstanding Invoices (unpaid amount)
        cursor.execute("""
            SELECT COALESCE(SUM(CAST(invoice_amount AS REAL)), 0)
            FROM invoices
            WHERE paid_date IS NULL OR paid_date = ''
        """)
        outstanding_invoices = cursor.fetchone()[0]

        # 5. Additional useful metrics (optional)

        # Overdue invoices (>30 days past due)
        cursor.execute("""
            SELECT COUNT(*)
            FROM invoices
            WHERE (paid_date IS NULL OR paid_date = '')
            AND julianday('now') - julianday(date_issued) > 30
        """)
        overdue_count = cursor.fetchone()[0]

        # Total revenue YTD (Year To Date)
        cursor.execute("""
            SELECT COALESCE(SUM(CAST(invoice_amount AS REAL)), 0)
            FROM invoices
            WHERE paid_date IS NOT NULL
            AND strftime('%Y', paid_date) = strftime('%Y', 'now')
        """)
        revenue_ytd = cursor.fetchone()[0]

        return {
            "active_revenue": round(active_revenue, 2),
            "active_projects": active_projects,
            "active_proposals": active_proposals,
            "outstanding_invoices": round(outstanding_invoices, 2),

            # Additional metrics
            "overdue_invoices_count": overdue_count,
            "revenue_ytd": round(revenue_ytd, 2),

            # Metadata
            "timestamp": datetime.now().isoformat(),
            "currency": "USD"
        }

    except Exception as e:
        print(f"Error calculating KPIs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate KPIs: {str(e)}")

    finally:
        conn.close()


# Optional: Add caching to reduce database load
# This caches KPI results for 5 minutes

from functools import lru_cache
from datetime import datetime, timedelta

_kpi_cache = {"data": None, "timestamp": None}

@app.get("/api/dashboard/kpis")
def get_dashboard_kpis(force_refresh: bool = False):
    """Get KPIs with 5-minute caching"""

    # Check cache
    if not force_refresh and _kpi_cache["data"] and _kpi_cache["timestamp"]:
        age = datetime.now() - _kpi_cache["timestamp"]
        if age < timedelta(minutes=5):
            return _kpi_cache["data"]

    # Calculate fresh KPIs (same code as above)
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COALESCE(SUM(CAST(total_fee AS REAL)), 0)
            FROM projects
            WHERE status = 'active'
        """)
        active_revenue = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM projects
            WHERE status = 'active'
        """)
        active_projects = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM proposals
            WHERE status IN ('active', 'follow_up', 'pending')
        """)
        active_proposals = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(SUM(CAST(invoice_amount AS REAL)), 0)
            FROM invoices
            WHERE paid_date IS NULL OR paid_date = ''
        """)
        outstanding_invoices = cursor.fetchone()[0]

        result = {
            "active_revenue": round(active_revenue, 2),
            "active_projects": active_projects,
            "active_proposals": active_proposals,
            "outstanding_invoices": round(outstanding_invoices, 2),
            "timestamp": datetime.now().isoformat(),
            "currency": "USD"
        }

        # Update cache
        _kpi_cache["data"] = result
        _kpi_cache["timestamp"] = datetime.now()

        return result

    except Exception as e:
        print(f"Error calculating KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# ============================================
# FRONTEND UPDATE
# ============================================

"""
Update Claude 5's KPI Cards component:

File: frontend/src/components/dashboard/kpi-cards.tsx

Change from hardcoded:
  const kpiData = {
    activeRevenue: 4234567.89,
    activeProjects: 23,
    activeProposals: 12,
    outstandingInvoices: 987654.32
  }

To API call:
  const { data: kpiData } = useQuery(
    ['dashboard-kpis'],
    () => api.get('/api/dashboard/kpis'),
    { refetchInterval: 5 * 60 * 1000 } // Refresh every 5 minutes
  )
"""


# ============================================
# TESTING
# ============================================

"""
Test the endpoint:

1. Start backend:
   cd backend
   uvicorn api.main:app --reload --port 8000

2. Test in browser:
   http://localhost:8000/api/dashboard/kpis

3. Expected response:
   {
     "active_revenue": 4234567.89,
     "active_projects": 23,
     "active_proposals": 12,
     "outstanding_invoices": 987654.32,
     "overdue_invoices_count": 5,
     "revenue_ytd": 12345678.90,
     "timestamp": "2025-11-25T01:30:00",
     "currency": "USD"
   }

4. Test with curl:
   curl http://localhost:8000/api/dashboard/kpis

5. Verify in frontend:
   - Open http://localhost:3002
   - Check Network tab -> should see /api/dashboard/kpis call
   - KPI cards should show real data
"""


# ============================================
# DATABASE SCHEMA VERIFICATION
# ============================================

"""
Before adding, verify your schema has these columns:

Projects table:
- status (text)
- total_fee (text or real)

Proposals table:
- status (text)

Invoices table:
- invoice_amount (text or real)
- paid_date (text or date)
- date_issued (text or date)

If column names are different, adjust SQL accordingly.

Check with:
  sqlite3 database/bensley_master.db ".schema projects"
  sqlite3 database/bensley_master.db ".schema proposals"
  sqlite3 database/bensley_master.db ".schema invoices"
"""
