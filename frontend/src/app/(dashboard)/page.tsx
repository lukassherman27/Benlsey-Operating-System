"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { KPICard, formatLargeNumber } from "@/components/dashboard/kpi-card";
import { RoleSwitcher, DashboardRole } from "@/components/dashboard/role-switcher";
import { HotItemsWidget } from "@/components/dashboard/hot-items-widget";
import { CalendarWidget } from "@/components/dashboard/calendar-widget";
import { InvoiceAgingWidget } from "@/components/dashboard/invoice-aging-widget";
import { RecentEmailsWidget } from "@/components/dashboard/recent-emails-widget";
import { ProposalTrackerWidget } from "@/components/dashboard/proposal-tracker-widget";
import { QuickActionsWidget } from "@/components/dashboard/quick-actions-widget";
import { ImportSummaryWidget } from "@/components/dashboard/import-summary-widget";
import { ActionsWidget } from "@/components/dashboard/actions-widget";
import { DailyBriefing } from "@/components/dashboard/daily-briefing";
import { AnalyticsInsights } from "@/components/dashboard/analytics-insights";
import { PersonalProjectsWidget } from "@/components/dashboard/personal-projects-widget";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import {
  Clock,
  RefreshCw,
  DollarSign,
  Briefcase,
  TrendingUp,
  AlertCircle,
  FileText,
  Calendar,
} from "lucide-react";
import { format } from "date-fns";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [role, setRole] = useState<DashboardRole>("bill");
  const [lastUpdated] = useState(new Date());

  // Fetch role-based stats
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["dashboard-stats", role],
    queryFn: () => api.getDashboardStats(role),
    refetchInterval: 1000 * 60 * 5, // Refetch every 5 minutes
  });

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

      {/* Row 2: Daily Briefing - Context-aware summary */}
      <DailyBriefing userName="Bill" />

      {/* Row 3: Role Switcher */}
      <div>
        <RoleSwitcher onRoleChange={setRole} defaultRole={role} />
      </div>

      {/* Row 4: Role-based KPI Cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-32 bg-slate-200 rounded-xl" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="p-6 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-sm text-red-600">Error loading dashboard stats</p>
        </div>
      ) : stats && role === "bill" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            label="Pipeline Value"
            value={formatLargeNumber(stats.pipeline_value || 0)}
            subtitle="Active proposals"
            icon={<TrendingUp className="h-5 w-5" />}
            variant="default"
          />
          <KPICard
            label="Active Projects"
            value={stats.active_projects_count || 0}
            subtitle="In delivery"
            icon={<Briefcase className="h-5 w-5" />}
            variant="default"
          />
          <KPICard
            label="Outstanding"
            value={formatLargeNumber(stats.outstanding_invoices_total || 0)}
            subtitle="Invoices due"
            icon={<DollarSign className="h-5 w-5" />}
            variant="warning"
          />
          <KPICard
            label="Overdue Invoices"
            value={stats.overdue_invoices_count || 0}
            subtitle="Need attention"
            icon={<AlertCircle className="h-5 w-5" />}
            variant={(stats.overdue_invoices_count ?? 0) > 0 ? "danger" : "default"}
          />
        </div>
      ) : stats && role === "pm" ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <KPICard
            label="My Projects"
            value={stats.my_projects_count || 0}
            subtitle="Active projects"
            icon={<Briefcase className="h-5 w-5" />}
            variant="default"
          />
          <KPICard
            label="Deliverables Due"
            value={stats.deliverables_due_this_week || 0}
            subtitle="This week"
            icon={<Calendar className="h-5 w-5" />}
            variant={(stats.deliverables_due_this_week ?? 0) > 0 ? "warning" : "default"}
          />
          <KPICard
            label="Open RFIs"
            value={stats.open_rfis_count || 0}
            subtitle="Need response"
            icon={<FileText className="h-5 w-5" />}
            variant={(stats.open_rfis_count ?? 0) > 0 ? "warning" : "default"}
          />
        </div>
      ) : stats && role === "finance" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            label="Total Outstanding"
            value={formatLargeNumber(stats.total_outstanding || 0)}
            subtitle="All invoices"
            icon={<DollarSign className="h-5 w-5" />}
            variant="warning"
          />
          <KPICard
            label="30+ Days Overdue"
            value={formatLargeNumber(stats.overdue_30_days || 0)}
            subtitle="Aging invoices"
            icon={<AlertCircle className="h-5 w-5" />}
            variant="danger"
          />
          <KPICard
            label="60+ Days Overdue"
            value={formatLargeNumber(stats.overdue_60_days || 0)}
            subtitle="Urgent follow-up"
            icon={<AlertCircle className="h-5 w-5" />}
            variant="danger"
          />
          <KPICard
            label="90+ Days Overdue"
            value={formatLargeNumber(stats.overdue_90_plus || 0)}
            subtitle="Critical"
            icon={<AlertCircle className="h-5 w-5" />}
            variant="danger"
          />
        </div>
      ) : null}

      {/* Row 4: What Needs Attention - Primary Action Widget */}
      <ActionsWidget limit={10} />

      {/* Row 5: Hot Items Strip */}
      <HotItemsWidget />

      {/* Row 6: Two Columns - Calendar & Quick Stats */}
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
              href="/search"
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

      {/* Row 7: Analytics Insights - Business metrics when healthy */}
      <AnalyticsInsights />

      {/* Row 8: Main Content Grid - 2 Columns on Large Screens */}
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

      {/* Row 9: Personal Projects - Toggle-able */}
      <PersonalProjectsWidget defaultVisible={false} />
    </div>
  );
}
