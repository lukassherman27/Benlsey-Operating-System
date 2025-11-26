# Recent Emails Widget - Usage Guide

## 📧 Component: RecentEmailsWidget

**Location:** `frontend/src/components/dashboard/recent-emails-widget.tsx`

**For:** Claude 5 - Overview Dashboard Integration

---

## 🚀 Quick Start

### Import
```tsx
import { RecentEmailsWidget } from "@/components/dashboard/recent-emails-widget";
```

### Basic Usage (Full Mode)
```tsx
// Shows 10 most recent emails with full details
<RecentEmailsWidget />
```

### Compact Mode
```tsx
// Shows 3 most recent emails in compact view
<RecentEmailsWidget limit={3} compact={true} />
```

### Custom Limit
```tsx
// Shows 20 most recent emails
<RecentEmailsWidget limit={20} />
```

---

## 📋 Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `limit` | `number` | `10` | Number of emails to fetch and display |
| `compact` | `boolean` | `false` | Show compact mode (summary view) |

---

## 🎨 Features

### Full Mode (default)
- ✅ Shows configurable number of emails (default: 10)
- ✅ Each email card displays:
  - Subject (bold, truncated)
  - Sender email with icon
  - Date (formatted, relative to current year)
  - Project code badge (if linked)
  - Email snippet/preview (2 lines max)
  - Category badge (if not "general")
  - "New" badge for emails < 24 hours old
- ✅ Click any email → navigates to `/emails?email_id={id}`
- ✅ "View All" button → navigates to `/emails`
- ✅ Footer shows: "Showing X of Y recent emails"
- ✅ Auto-refresh every 2 minutes
- ✅ Hover effects on email cards
- ✅ Color coding: Recent emails (< 24h) have blue background

### Compact Mode
- ✅ Shows only 3 most recent emails
- ✅ Displays total count as large number
- ✅ Each email shows: subject + sender (1 line each)
- ✅ "View All" badge → navigates to `/emails`
- ✅ Perfect for dashboard sidebars or grid layouts

---

## 🎯 Integration Example for Claude 5

### Dashboard Grid Layout
```tsx
export default function DashboardPage() {
  return (
    <div className="p-6 space-y-6">
      {/* Top Row - Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatsCard title="Active Projects" value={12} />
        <StatsCard title="Proposals" value={25} />
        <StatsCard title="Emails" value={3356} />
        <StatsCard title="Revenue" value="$2.4M" />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - 2/3 width */}
        <div className="lg:col-span-2 space-y-6">
          <RevenueChart />
          <ActiveProjectsWidget />
        </div>

        {/* Right Column - 1/3 width */}
        <div className="space-y-6">
          {/* Recent Emails - Compact Mode */}
          <RecentEmailsWidget limit={5} compact={true} />

          {/* Invoice Aging - Compact Mode */}
          <InvoiceAgingWidget compact={true} />

          {/* Quick Actions */}
          <QuickActionsWidget />
        </div>
      </div>

      {/* Bottom Row - Full Width Widgets */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Emails - Full Mode */}
        <RecentEmailsWidget limit={10} />

        {/* Proposal Tracker */}
        <ProposalTrackerWidget />
      </div>
    </div>
  );
}
```

### Sidebar Layout
```tsx
<div className="flex gap-6">
  {/* Main Content */}
  <div className="flex-1">
    <MainDashboard />
  </div>

  {/* Sidebar */}
  <div className="w-80 space-y-4">
    <RecentEmailsWidget compact={true} />
    <QuickStats />
  </div>
</div>
```

---

## 🔧 API Integration

The widget uses the backend API:
```
GET /api/emails/recent?limit={limit}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "email_id": 2024672,
      "subject": "Project Update",
      "sender_email": "client@example.com",
      "date": "Wed, 9 Jul 2025 20:56:05 +0700",
      "project_code": "BK-044",
      "category": "project_update",
      "snippet": "Email preview text..."
    }
  ],
  "count": 3356
}
```

---

## 🎨 Styling

The widget matches the design system:
- Uses shadcn/ui components (`Card`, `Badge`)
- Lucide React icons (`Mail`, `User`, `Calendar`, `ExternalLink`)
- Tailwind CSS for styling
- Consistent with `invoice-aging-widget.tsx` style
- Responsive design (mobile-friendly)
- Smooth hover transitions

---

## ✅ States Handled

1. **Loading:** Shows "Loading recent emails..."
2. **Error:** Shows error message with details
3. **Empty:** Shows "No recent emails found"
4. **Success:** Displays email list

---

## 📝 Notes for Claude 5

- Widget is fully self-contained (no external dependencies needed)
- Auto-refreshes data every 2 minutes
- Click handlers navigate to `/emails` page
- Project codes shown as badges when available
- "New" badge for emails < 24 hours old (blue highlight)
- Categories displayed (except "general")
- Responsive and mobile-friendly
- Matches existing dashboard component style

**Ready to integrate into overview dashboard!** 🚀
