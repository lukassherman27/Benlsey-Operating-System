# Dashboard Component Specs

All components are React (TypeScript) with Tailwind + shadcn/ui primitives.

## Shell & Navigation
- **AppShell**
  - Layout with sidebar, topbar, content area.
  - Props: `user`, `navItems`.
  - Provides React Query providers, theme context, toaster.

- **SidebarNav**
  - Renders sections: Overview, Proposals, Financials, Operations, Query.
  - Highlights active route; supports nested links.

## Dashboard Widgets (Current Apple-style layout)
- **Hero Overview**
  - Four cards: Today’s Focus, Payments & Fees, Business Health, Next Meeting.
  - Props: `needsOutreachCount`, `focusProject`, `paymentsSummary`, `businessHealthScore`, `meeting`.
  - Includes action buttons (Provide context, Review email queue).

- **RevenueWidget**
  - Props: `series` (revenue vs cost), `delta`.
  - Displays custom dual bar chart (no external lib), shows current value + change vs last period.

- **SignalsWidget**
  - Props: `signals[]` combining urgent manual overrides + delayed milestones.
  - Shows up to 3 cards with description; empty state text when calm.

- **CashOutlookCard**
  - Props: `totalOutstanding`, `paidToDate`, `nextDue`, `chartSeries`.
  - Embeds `RevenueBar` for quick trend view.

- **OutstandingInvoicesList**
  - Props: `invoices[]` ordered by newest, each with `project`, `amount`, `due_date`.
  - Intended for quick scanning + deep link into invoices view later.

- **UpcomingPresentationsWidget**
  - Props: `calendarDays[]` (label, dayNumber, hasEvent), `milestones[]`.
  - Renders pill calendar plus milestone list (project + date).

- **ManualOverridesPanel**
  - Props: `overrides[]`, `onCreateNote`.
  - Shows instructions, urgency badge, author, created date; “New note” button opens modal.

- **ProposalFlowWidget**
  - Props: counts per status (`active`, `won`, `lost`, `pending`).
  - Stacked progress bars with inline counts.

- **DeadlinePressureWidget**
  - Props: `delayedCount`, `totalMilestones`.
  - Displays conic gauge + explanatory text about schedule risk.

- **AtRiskPanel**
  - Props: `proposals[]` below health threshold; reuses `HealthBadge`.

- **ManualOverrideModal**
  - Textarea + scope/urgency selects; persists via `/api/manual-overrides`.
  - Props: `defaultScope`, `defaultAuthor`, `onSubmit`, `loading`.

## Proposal Tracker (Phase 1)
- **ProposalTable**
  - Props: `data: ProposalRow[]`, `isLoading`, `filters`.
  - Columns: code, project/client, status, PM, health, next action, last contact.
  - Supports sorting, inline health badges.

- **ProposalDetailDrawer**
  - Props: `proposal`, `onClose`.
  - Contains tabs for Overview, Emails, Documents, Timeline, Query.

- **HealthGauge + Breakdown**
  - Gauge shows score + risk badge; “View breakdown” button opens modal.
  - Props: `score`, `risk`, `factors`, `risks`, `recommendation`.
  - Modal lists each factor (e.g., days since contact) and recommended action.

- **TimelineRail**
  - Props: `events[]` with `timestamp`, `type`, `summary`, `link`.
  - Displays stacked markers with tooltips.

- **EmailCategoryTabs**
  - Props: `categories[]`, `activeCategory`, `onSelect`.
  - Shows counts and badge for unread/action required.

- **EmailList**
  - Props: `emails[]` (subject, sender, importance, followUp).
  - Integrates with virtualization for performance.

- **EmailDetailPanel**
  - Props: `email`, `onClose`.
  - Shows AI summary, tags, action buttons.

- **DocumentList**
  - Props: `documents[]`, `view` (grid/list).
  - Display file type badge, version, linked proposals.

- **QueryConsole**
  - Props: `history[]`, `onSubmit(query)`, `response`.
  - Contains editor input, run button, streaming output, source list.

## Financial Components
- **InvoiceTable**
  - Props: `invoices[]`, `viewMode` (list/kanban).
  - Includes status pill (due soon, overdue, paid).

- **PaymentTimeline**
  - Props: `payments[]` sorted chronologically.

- **MilestoneProgress**
  - Props: `milestones[]` with completion %, invoice references.

## Operations Components
- **MeetingAgenda**
  - Props: `meetings[]`, `dateRange`.

- **StaffLoadChart**
  - Props: `staff[]` with allocation percentages.
  - Visual: stacked bar or radial gauge per member.

- **RFIStatusBoard**
  - Props: `rfis[]` grouped by status.

- **DeliverableList**
  - Props: `deliverables[]`, highlight upcoming deadlines.

## Shared Utilities
- **DataFilterBar**
  - Props: filter config array, emits new filter state.

- **StatBadge**
  - Tiny badge for counts or statuses.

- **AsyncStateWrapper**
  - Handles loading/empty/error states with consistent UI.

- **EntityAvatar**
  - Shows staff initials or client logos.

---

Each component will initially consume mock data (Phase 1 build) and later point to services generated from React Query hooks (`useProposals`, `useEmails`, etc.) backed by the documented API contracts.
