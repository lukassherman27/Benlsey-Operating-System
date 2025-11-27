# Agent: Fix Active Projects Invoice Display

## Your Mission
Fix the invoice/phase display structure in active projects page.

## Context
User said: "This is almost there, but..."

**Current Issues:**
1. Phase ordering wrong (should be: Mobilization → Concept → DD → CD → CO)
2. Payment dates shown at top (should be in invoice details)
3. Missing summary bar at top
4. Spacing issues

## Task 1: Fix Phase Ordering

**File:** Find active projects component (likely `frontend/src/app/(dashboard)/projects/`)

Ensure phases display in this order:
```tsx
const PHASE_ORDER = {
  'mobilization': 1,
  'master plan and preconcept': 2,
  'concept design': 3,
  'schematic design': 4,
  'design development': 5,
  'construction documents': 6,
  'construction observation': 7,
};

// Sort breakdowns by phase
breakdowns.sort((a, b) => {
  const orderA = PHASE_ORDER[a.phase.toLowerCase()] || 999;
  const orderB = PHASE_ORDER[b.phase.toLowerCase()] || 999;
  return orderA - orderB;
});
```

## Task 2: Add Summary Bar at Top

Before showing breakdown details, add:
```tsx
<div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
  <div className="grid grid-cols-4 gap-4">
    <div>
      <div className="text-xs text-gray-500">Contract Value</div>
      <div className="text-lg font-bold text-gray-900">
        ${project.contract_value.toLocaleString()}
      </div>
    </div>
    <div>
      <div className="text-xs text-gray-500">Amount Paid</div>
      <div className="text-lg font-bold text-green-600">
        ${project.paid_to_date_usd.toLocaleString()}
      </div>
    </div>
    <div>
      <div className="text-xs text-gray-500">Amount Due</div>
      <div className="text-lg font-bold text-orange-600">
        ${project.outstanding_usd.toLocaleString()}
      </div>
    </div>
    <div>
      <div className="text-xs text-gray-500">Uninvoiced</div>
      <div className="text-lg font-bold text-gray-600">
        ${(project.contract_value - project.total_invoiced).toLocaleString()}
      </div>
    </div>
  </div>
</div>
```

## Task 3: Move Payment Dates Into Invoice Details

**Current:** Payment dates shown in separate section at top
**Need:** Include in each invoice row

```tsx
{breakdown.invoices.map(invoice => (
  <div key={invoice.invoice_id} className="py-2 border-b last:border-0">
    <div className="flex justify-between items-start">
      <div>
        <div className="font-medium">{invoice.invoice_number}</div>
        <div className="text-xs text-gray-500">
          Invoiced: {formatDate(invoice.invoice_date)}
          {invoice.payment_date && (
            <> • Paid: {formatDate(invoice.payment_date)}</>
          )}
        </div>
      </div>
      <div className="text-right">
        <div className="font-semibold">
          ${invoice.invoice_amount.toLocaleString()}
        </div>
        <div className={`text-xs ${invoice.status === 'paid' ? 'text-green-600' : 'text-orange-600'}`}>
          {invoice.status}
        </div>
      </div>
    </div>
  </div>
))}
```

## Task 4: Improve Spacing

Add breathing room:
```tsx
// Between disciplines
<div className="mb-6">  {/* was mb-4 */}

// Between phases within discipline
<div className="mt-4 space-y-2">  {/* clearer separation */}

// Invoice list
<div className="mt-2 ml-4 space-y-1">  {/* better hierarchy */}
```

## Task 5: Remove Duplicate Invoice List at Top

Remove the invoice summary section that shows all invoices flat. User said: "I don't need the list of all of the invoices first"

## Visual Hierarchy Should Be:

```
Project Name
├─ Summary Bar (Contract Value | Paid | Due | Uninvoiced)
├─ Architectural
│  ├─ Mobilization - $100K (80% paid)
│  │  ├─ Invoice I25-001 - $50K (Paid 2025-01-15)
│  │  └─ Invoice I25-002 - $50K (Outstanding)
│  ├─ Concept Design - $200K (50% paid)
│  │  └─ Invoice I25-003 - $100K (Paid 2025-03-01)
│  └─ Design Development - $300K (0% paid)
├─ Landscape
│  ├─ Mobilization - $80K (100% paid)
│  └─ ...
```

## Testing

1. Open http://localhost:3002/projects
2. Click on a project (e.g., 25 BK-033 Ritz Carlton)
3. Verify:
   - ✅ Summary bar at top
   - ✅ Phases in correct order (Mobilization first)
   - ✅ Payment dates in invoice details (not separate section)
   - ✅ Good spacing/hierarchy
   - ✅ No duplicate invoice list at top

## Success Criteria
- ✅ "This looks pretty good" from user
- ✅ Easy to see financial status at a glance
- ✅ Clear phase progression
- ✅ Invoice details include payment dates

---
**Status:** READY TO START
