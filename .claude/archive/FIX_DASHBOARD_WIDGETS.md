# Agent: Fix Dashboard Widgets - Project Names

## Your Mission
Replace ALL instances of project CODES with project NAMES in dashboard widgets.

## Context
**User Complaint:** "Bill doesn't give a shit about project codes. We need PROJECT NAMES everywhere!"

## Affected Widgets

### 1. Recent Payments Widget
**Current:** Shows project code (25 BK-033) and invoice number prominently
**Need:** Show PROJECT NAME big, invoice number/code small

**File:** Find in `frontend/src/components/dashboard/`

Change from:
```tsx
<div className="font-semibold">{payment.project_code}</div>
<div className="text-sm text-gray-500">Invoice {payment.invoice_number}</div>
```

To:
```tsx
<div className="font-semibold text-lg">{payment.project_title}</div>
<div className="text-xs text-gray-400">
  {payment.project_code} • Invoice {payment.invoice_number}
</div>
```

### 2. Top 5 Outstanding Projects
**Current:** Shows project code prominently
**Need:** PROJECT NAME big, with "over 30 days overdue" label

Change to:
```tsx
<div className="font-semibold text-lg">{project.project_title}</div>
<div className="text-sm text-red-600">
  ${project.outstanding_usd.toLocaleString()} overdue
  {project.avg_days_overdue && ` • Avg ${project.avg_days_overdue} days`}
</div>
<div className="text-xs text-gray-400">{project.project_code}</div>
```

### 3. Oldest Unpaid Invoices Widget
**Current:** No color coding for 600+ days
**Need:** RED for 600+ days, PROJECT NAMES

```tsx
function getDaysColor(days: number) {
  if (days >= 600) return 'text-red-600 font-bold';
  if (days >= 180) return 'text-orange-600';
  if (days >= 90) return 'text-yellow-600';
  return 'text-gray-600';
}

<div className="font-semibold">{invoice.project_title}</div>
<div className={`text-sm ${getDaysColor(invoice.days_old)}`}>
  {invoice.days_old} days old
</div>
<div className="text-xs text-gray-400">{invoice.project_code}</div>
```

### 4. Top 5 Remaining by Value
**Current:** Shows project code and 0% invoiced (probably wrong data)
**Need:** PROJECT NAME big, verify % is correct

```tsx
<div className="font-semibold text-lg">{project.project_title}</div>
<div className="text-sm text-gray-600">
  ${project.remaining_value.toLocaleString()} remaining •
  {project.percentage_invoiced}% invoiced
</div>
<div className="text-xs text-gray-400">{project.project_code}</div>
```

## Task 2: Fix Invoice Aging Bar Y-Axis

**File:** Find invoice aging chart component

Change Y-axis to increments of 0.5M:
```tsx
yAxis={{
  domain: [0, 'auto'],
  ticks: [0, 500000, 1000000, 1500000, 2000000], // 0, 0.5M, 1M, 1.5M, 2M
  tickFormatter: (value) => `$${(value / 1000000).toFixed(1)}M`
}}
```

## Task 3: Add "Over 30 Days" Label

For outstanding invoices, add clarification:
```tsx
<div className="text-sm text-gray-500">
  Outstanding: ${outstanding.toLocaleString()}
  <span className="ml-2 text-xs text-gray-400">(over 30 days)</span>
</div>
```

## Backend Updates Needed

Check if these endpoints return `project_title`:
- `/api/dashboard/recent-payments`
- `/api/dashboard/top-outstanding`
- `/api/dashboard/oldest-invoices`
- `/api/dashboard/top-remaining`

If not, update backend queries to include:
```sql
SELECT
    i.*,
    p.project_title  -- ADD THIS
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
```

## Testing

1. Open http://localhost:3002
2. Check each widget:
   - ✅ Project NAMES visible (not codes)
   - ✅ Codes shown small/gray underneath
   - ✅ Invoice aging bar has 0.5M increments
   - ✅ 600+ day invoices are RED
   - ✅ "over 30 days" label on outstanding

## Success Criteria
- ✅ USER CAN READ PROJECT NAMES WITHOUT SQUINTING
- ✅ Codes are de-emphasized
- ✅ Color coding works
- ✅ Chart scales correctly

---
**Status:** READY TO START
