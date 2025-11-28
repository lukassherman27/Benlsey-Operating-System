# Phase 2 Dashboard Widgets – Data Contracts (Nov 16, 2025)

## 1. Financial Widgets

### Outstanding Invoices (Overview)
- **Source:** `/api/dashboard/decision-tiles` → `invoices_awaiting_payment`
- **Needed fields:** `total_amount`, `count`, list of `{project_code, project_name, amount_due, due_date}`
- **Usage:** Hero metric showing total unpaid + invoice count; drilldown panel later.

### Upcoming / Projected Invoices
- **Endpoint to build:** `GET /api/projects/{code}/timeline` (phase milestones) + contract fee breakdown.
- **Needed fields per upcoming milestone:** `{project_code, project_name, phase, presentation_date, projected_fee_usd, scope}`
- **Purpose:** display next 3–5 invoicing events inferred from presentations/phase completions.

### Recently Paid Invoices
- **Endpoint:** (Future) `GET /api/finance/recent-payments?limit=5`
- **Fields:** `{project_code, project_name, discipline/scope, amount_usd, paid_on}`
- **Usage:** reassure Bill of recent cash inflow; also helpful for audit trail.

## 2. RFI Status
- **Current data:** `decisionTiles.unanswered_rfis.items`
- **Enhancements needed:** include `status` (open/late), `due_date`, `owner`, `project_name`.
- **Widget behavior:** show counts + top 3 RFIs with due dates.

## 3. Studio Schedule / Staffing
- **Future endpoint:** `GET /api/studio/schedule?week=YYYY-WW`
- **Fields:** `{project_code, project_name, discipline, team_size, week_start, week_end}`
- **Use case:** preview staffing per discipline to plan workload and correlate with invoices.

## 4. AI Weekly Summary
- **Input:** combination of `/api/briefing/daily.insights`, `/api/proposals/recent-activity`, `/api/analytics/dashboard`.
- **Future enhancement:** dedicated endpoint (e.g., `/api/briefing/weekly`) summarizing top developments, newly signed proposals, major risks.
- **Widget:** shows headline + two supporting bullets, timestamped.

## 5. Documentation
- Keep this file updated whenever new widgets are added or data contracts change.
- Backend should reference this when exposing new endpoints; frontend will mirror the shapes in `src/lib/types.ts`.
