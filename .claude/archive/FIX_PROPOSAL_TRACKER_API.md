# Agent: Fix Proposal Tracker API & Frontend

## Your Mission
Update the proposal tracker backend API and frontend to display the new tracking fields that were just imported from the dashboard sheet.

## Context
We just imported tracking data from "Proposal dashboard " sheet:
- `current_status` (On hold, Proposal Sent, First Contact, Contract signed, Drafting, n.a)
- `days_in_current_status`
- `first_contact_date`
- `proposal_sent_date`
- `last_week_status`
- `days_in_drafting`
- `days_in_review`
- `num_proposals_sent`
- `phase`
- `remarks`

**Current Problem:** Frontend proposal tracker is still showing old `status` field instead of new `current_status` field.

## Task 1: Update Backend API

**File:** `backend/api/main.py`

Find the proposals API endpoints (around line 940-6755) and update them to return the new tracking fields:

### Main endpoint: `/api/proposals` (line 940)
Add these fields to the SELECT:
```sql
SELECT
    p.proposal_id,
    p.project_code,
    p.project_name,
    p.client_company,
    p.contact_person,
    p.contact_email,
    p.contact_phone,
    p.project_value,
    p.status,
    p.current_status,          -- NEW
    p.days_in_current_status,  -- NEW
    p.first_contact_date,      -- NEW
    p.proposal_sent_date,      -- NEW
    p.last_week_status,        -- NEW
    p.days_in_drafting,        -- NEW
    p.days_in_review,          -- NEW
    p.country,
    p.location,
    p.currency
FROM proposals p
WHERE p.project_code LIKE '25 BK-%'
ORDER BY p.project_code
```

### Also update:
- `/api/proposal-tracker/list` (line 6663)
- `/api/proposal-tracker/{project_code}` (line 6695)
- `/api/proposals/{identifier}` (line 1325)

## Task 2: Update Frontend Proposal Tracker

**File:** Find the proposal tracker component (likely in `frontend/src/components/proposals/` or `frontend/src/app/(dashboard)/tracker/`)

### Display these NEW fields:
1. **Current Status** - Use `current_status` instead of `status`
2. **Days in Status** - Show `days_in_current_status` (e.g., "271 days")
3. **First Contact Date** - Show `first_contact_date`
4. **Proposal Sent Date** - Show `proposal_sent_date`
5. **Status Badge** - Color-code by status:
   - "On hold" = gray
   - "Proposal Sent" = blue
   - "First Contact" = green
   - "Contract signed" = purple
   - "Drafting" = yellow
   - "n.a" = gray

### Add "Days in Current Status" column
```tsx
<td className="text-sm text-gray-600">
  {proposal.days_in_current_status
    ? `${proposal.days_in_current_status} days`
    : '-'}
</td>
```

### Status Badge Component
```tsx
function getStatusColor(status: string) {
  switch (status?.toLowerCase()) {
    case 'on hold': return 'bg-gray-100 text-gray-700';
    case 'proposal sent': return 'bg-blue-100 text-blue-700';
    case 'first contact': return 'bg-green-100 text-green-700';
    case 'contract signed': return 'bg-purple-100 text-purple-700';
    case 'drafting': return 'bg-yellow-100 text-yellow-700';
    default: return 'bg-gray-100 text-gray-600';
  }
}
```

## Task 3: Fix Stats Display

Update the stats at top to show:
- Total proposals by current_status (not old status)
- Average days in current status
- Proposals needing follow-up (>30 days in same status)

## Testing

1. Navigate to http://localhost:3002/tracker
2. Verify columns show:
   - Project Code
   - Project Name
   - Country
   - **Current Status** (not generic "proposal")
   - **Days in Status**
   - First Contact Date
   - Proposal Sent Date
3. Verify status badges have colors
4. Verify stats are correct

## Success Criteria
- ✅ No more "81 proposals" showing same status
- ✅ Shows real statuses: On hold (33), Proposal Sent (19), etc.
- ✅ Days in status displayed
- ✅ Dates visible
- ✅ Color-coded status badges

---
**Status:** READY TO START
