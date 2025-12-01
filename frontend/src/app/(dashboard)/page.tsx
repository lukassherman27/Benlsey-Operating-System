"use client";

import { useState } from "react";
import { KPICards } from "@/components/dashboard/kpi-cards";
import { HotItemsWidget } from "@/components/dashboard/hot-items-widget";
import { CalendarWidget } from "@/components/dashboard/calendar-widget";
import { InvoiceAgingWidget } from "@/components/dashboard/invoice-aging-widget";
import { RecentEmailsWidget } from "@/components/dashboard/recent-emails-widget";
import { ProposalTrackerWidget } from "@/components/dashboard/proposal-tracker-widget";
import { QuickActionsWidget } from "@/components/dashboard/quick-actions-widget";
import { ImportSummaryWidget } from "@/components/dashboard/import-summary-widget";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { Clock, RefreshCw } from "lucide-react";
import { format } from "date-fns";

export default function DashboardPage() {
  const [period, setPeriod] = useState("all_time");
  const [lastUpdated] = useState(new Date());

  return (
    <div className={cn("w-full max-w-full", ds.spacing.spacious, "space-y-6")}>
      {/* Row 1: Header with Last Updated */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            Operations Dashboard
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Real-time overview of proposals, projects, and communications
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Clock className="h-4 w-4" />
          <span>Updated {format(lastUpdated, "h:mm a")}</span>
          <button
            onClick={() => window.location.reload()}
            className="p-1 hover:bg-slate-100 rounded"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Row 2: KPI Cards with Period Selector */}
      <KPICards period={period} onPeriodChange={setPeriod} />

      {/* Row 3: Hot Items Strip */}
      <HotItemsWidget />

      {/* Row 4: Two Columns - Calendar & Quick Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Calendar Widget */}
        <CalendarWidget />

        {/* Right: Quick Actions / Query */}
        <div className={cn(ds.cards.default, ds.spacing.spacious)}>
          <h3 className={cn(ds.typography.cardHeader, ds.textColors.primary, "mb-2")}>
            Quick Query
          </h3>
          <p className={cn(ds.typography.caption, ds.textColors.secondary, "mb-4")}>
            Ask questions about your data in natural language
          </p>
          <div className="space-y-2">
            <a
              href="/query"
              className={cn(ds.buttons.primary, "inline-flex items-center gap-2 w-full justify-center")}
            >
              Open Query Interface →
            </a>
            <div className="text-xs text-slate-500 mt-3">
              <p className="font-medium mb-1">Try asking:</p>
              <ul className="space-y-1 text-slate-400">
                <li>&quot;What invoices are overdue?&quot;</li>
                <li>&quot;Show contracts signed this month&quot;</li>
                <li>&quot;Which projects have outstanding payments?&quot;</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Row 5: Main Content Grid - 2 Columns on Large Screens */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LEFT COLUMN */}
        <div className="space-y-6">
          {/* Invoice Aging Widget - Visual summary */}
          <InvoiceAgingWidget compact={true} />

          {/* Recent Emails Widget */}
          <RecentEmailsWidget limit={5} compact={true} />
        </div>

        {/* RIGHT COLUMN */}
        <div className="space-y-6">
          {/* Import Summary Widget */}
          <ImportSummaryWidget compact={true} />

          {/* Proposal Pipeline Widget */}
          <ProposalTrackerWidget compact={true} />

          {/* Quick Actions */}
          <QuickActionsWidget />
        </div>
      </div>
    </div>
  );
}
