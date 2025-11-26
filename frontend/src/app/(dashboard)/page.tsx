"use client";

import { KPICards } from "@/components/dashboard/kpi-cards";
import { InvoiceAgingWidget } from "@/components/dashboard/invoice-aging-widget";
import { RecentEmailsWidget } from "@/components/dashboard/recent-emails-widget";
import { ProposalTrackerWidget } from "@/components/dashboard/proposal-tracker-widget";
import { QuickActionsWidget } from "@/components/dashboard/quick-actions-widget";
import { TopOutstandingInvoicesWidget } from "@/components/dashboard/top-outstanding-invoices-widget";
import { AllInvoicesList } from "@/components/dashboard/all-invoices-list";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

export default function DashboardPage() {
  return (
    <div className={cn("container mx-auto", ds.spacing.spacious, "space-y-6")}>
      {/* Page Header */}
      <div>
        <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
          Operations Dashboard
        </h1>
        <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-2")}>
          Real-time overview of proposals, projects, invoices, and communications
        </p>
      </div>

      {/* KPI Cards Row */}
      <KPICards />

      {/* Main Content Grid - 2 Columns on Large Screens */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LEFT COLUMN */}
        <div className="space-y-6">
          {/* Invoice Aging Widget - From Claude 3 */}
          <InvoiceAgingWidget compact={true} />

          {/* Recent Emails Widget - From Claude 1 */}
          <RecentEmailsWidget limit={5} compact={true} />
        </div>

        {/* RIGHT COLUMN */}
        <div className="space-y-6">
          {/* Proposal Pipeline Widget - From Claude 4 */}
          <ProposalTrackerWidget compact={true} />

          {/* Query Widget Placeholder - From Claude 2 */}
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 border border-slate-200 rounded-lg p-6">
            <h3 className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
              Quick Query
            </h3>
            <p className={cn(ds.typography.caption, ds.textColors.secondary, "mb-4")}>
              Ask questions about your data in natural language
            </p>
            <a
              href="/query"
              className={cn(
                "inline-flex items-center gap-2 px-4 py-2 rounded-lg",
                "bg-blue-600 text-white hover:bg-blue-700 transition-colors",
                "text-sm font-medium"
              )}
            >
              Open Query Interface →
            </a>
          </div>
        </div>
      </div>

      {/* Bottom Row - Quick Actions */}
      <QuickActionsWidget />

      {/* Invoice Management Section - Full Width */}
      <div className="space-y-6">
        <h2 className={cn(ds.typography.heading2, ds.textColors.primary)}>
          Invoice Management
        </h2>

        {/* Top 10 Outstanding Invoices */}
        <TopOutstandingInvoicesWidget />

        {/* All Outstanding Invoices with Filter */}
        <AllInvoicesList />
      </div>
    </div>
  );
}
