"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp,
  DollarSign,
  FileText,
  CheckCircle2,
  Clock,
  AlertCircle,
  Wallet,
} from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { ProposalTrackerWidget } from "./proposal-tracker-widget";
import { InvoiceAgingWidget } from "./invoice-aging-widget";
import { RevenueTrendsWidget } from "./revenue-trends-widget";
import { RecentActivityWidget } from "./recent-activity-widget";
import { QuickActionsWidget } from "./quick-actions-widget";
import { Skeleton } from "@/components/ui/skeleton";

export default function FinancialDashboard() {
  // Fetch dashboard metrics
  const metricsQuery = useQuery({
    queryKey: ["dashboard-financial-metrics"],
    queryFn: api.getDashboardFinancialMetrics,
    refetchInterval: 1000 * 60 * 5, // Refetch every 5 minutes
  });

  // Fetch insight widgets data
  const recentPaymentsQuery = useQuery({
    queryKey: ["recent-payments"],
    queryFn: () => api.getRecentPayments(5),
    staleTime: 1000 * 60 * 10,
  });

  const projectsByOutstandingQuery = useQuery({
    queryKey: ["projects-by-outstanding"],
    queryFn: () => api.getProjectsByOutstanding(5),
    staleTime: 1000 * 60 * 10,
  });

  const oldestUnpaidQuery = useQuery({
    queryKey: ["oldest-unpaid-invoices"],
    queryFn: () => api.getOldestUnpaidInvoices(5),
    staleTime: 1000 * 60 * 10,
  });

  const projectsByRemainingQuery = useQuery({
    queryKey: ["projects-by-remaining"],
    queryFn: () => api.getProjectsByRemaining(5),
    staleTime: 1000 * 60 * 10,
  });

  const metrics = metricsQuery.data?.metrics;

  return (
    <div className={cn(ds.gap.loose, "space-y-6")}>
      {/* Header Section with Key Metrics - RESPONSIVE */}
      <div className="grid gap-4 grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
        <MetricCard
          label="Total Contract Value"
          value={formatCurrency(metrics?.total_contract_value || 0)}
          subtitle={`${metrics?.active_project_count || 0} active projects`}
          icon={<DollarSign className={cn("h-4 w-4", ds.status.info.icon)} />}
          trend="neutral"
        />
        <MetricCard
          label="Total Invoiced"
          value={formatCurrency(metrics?.total_invoiced || 0)}
          subtitle={
            metrics?.total_contract_value
              ? `${((metrics.total_invoiced / metrics.total_contract_value) * 100).toFixed(1)}% of contracts`
              : "0% of contracts"
          }
          icon={<FileText className={cn("h-4 w-4", ds.status.info.icon)} />}
          trend="neutral"
        />
        <MetricCard
          label="Total Paid"
          value={formatCurrency(metrics?.total_paid || 0)}
          subtitle={
            metrics?.total_invoiced
              ? `${((metrics.total_paid / metrics.total_invoiced) * 100).toFixed(1)}% of invoices`
              : "0% of invoices"
          }
          icon={<CheckCircle2 className={cn("h-4 w-4", ds.status.success.icon)} />}
          trend="positive"
        />
        <MetricCard
          label="Outstanding"
          value={formatCurrency(metrics?.total_outstanding || 0)}
          subtitle="Not yet due"
          icon={<Clock className={cn("h-4 w-4", ds.status.warning.icon)} />}
          trend="neutral"
        />
        <MetricCard
          label="Overdue"
          value={formatCurrency(metrics?.total_overdue || 0)}
          subtitle="Past due date"
          icon={<AlertCircle className={cn("h-4 w-4", ds.status.danger.icon)} />}
          trend={metrics?.total_overdue && metrics.total_overdue > 0 ? "negative" : "neutral"}
        />
        <MetricCard
          label="Remaining to Invoice"
          value={formatCurrency(metrics?.total_remaining || 0)}
          subtitle="Uninvoiced work"
          icon={<Wallet className={cn("h-4 w-4", ds.textColors.secondary)} />}
          trend="neutral"
        />
      </div>

      {/* Primary Insights Row - Revenue and Aging */}
      <div className="grid gap-6 lg:grid-cols-2">
        <RevenueTrendsWidget />
        <InvoiceAgingWidget />
      </div>

      {/* Secondary Insights Row - Activity and Quick Actions */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <RecentActivityWidget />
        </div>
        <QuickActionsWidget />
      </div>

      {/* Proposal Tracker Section */}
      <div>
        <h2 className={cn(ds.typography.heading2, ds.textColors.primary, "mb-4")}>
          Proposal Pipeline
        </h2>
        <ProposalTrackerWidget />
      </div>

      {/* Detailed Financial Widgets */}
      <div>
        <h2 className={cn(ds.typography.heading2, ds.textColors.primary, "mb-4")}>
          Detailed Financials
        </h2>
        <div className="grid gap-6 md:grid-cols-2">
          {/* Widget 1: Recent Payments */}
          <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted)}>
                    Recent Payments
                  </p>
                  <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
                    Last 5 Payments Received
                  </CardTitle>
                </div>
                <Badge variant="secondary" className={cn(ds.borderRadius.badge, ds.gap.tight)}>
                  <TrendingUp className="h-3.5 w-3.5" />
                  Updated
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {recentPaymentsQuery.isLoading ? (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-5 w-3/4" />
                        <Skeleton className="h-4 w-1/2" />
                      </div>
                      <Skeleton className="h-6 w-24" />
                    </div>
                  ))}
                </div>
              ) : recentPaymentsQuery.isError ? (
                <p className={cn(ds.typography.caption, ds.status.danger.text)}>
                  Unable to load payments
                </p>
              ) : !recentPaymentsQuery.data?.payments ||
                recentPaymentsQuery.data.payments.length === 0 ? (
                <div className="py-12 text-center">
                  <CheckCircle2 className="mx-auto h-12 w-12 text-slate-300 mb-3" aria-hidden="true" />
                  <p className={cn(ds.typography.bodyBold, ds.textColors.secondary, "mb-1")}>
                    No payments yet
                  </p>
                  <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                    Payments will appear here once invoices are paid
                  </p>
                </div>
              ) : (
                <div className={cn(ds.gap.normal, "space-y-3")}>
                  {recentPaymentsQuery.data.payments.map((payment, idx) => (
                    <div
                      key={`${payment.invoice_id}-${idx}`}
                      className={cn(
                        "flex items-center justify-between",
                        ds.borderRadius.card,
                        "border border-slate-100 p-4",
                        ds.hover.card,
                        "cursor-pointer"
                      )}
                    >
                      <div className="flex-1">
                        <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                          {payment.project_name || payment.project_code}
                        </p>
                        <p className={cn(ds.typography.tiny, ds.textColors.tertiary)}>
                          {payment.paid_on
                            ? new Date(payment.paid_on).toLocaleDateString()
                            : "Date unknown"}{" "}
                          {payment.discipline && `• ${payment.discipline}`}
                        </p>
                      </div>
                      <p className={cn(ds.typography.bodyBold, ds.status.success.text)}>
                        {formatCurrency(payment.amount_usd)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Widget 2: Projects by Outstanding */}
          <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted)}>
                    Outstanding Fees
                  </p>
                  <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
                    Top 5 Projects by Outstanding
                  </CardTitle>
                </div>
                <Badge variant="outline" className={cn(ds.borderRadius.badge, ds.typography.tiny)}>
                  {projectsByOutstandingQuery.data?.count || 0} projects
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {projectsByOutstandingQuery.isLoading ? (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-5 w-3/4" />
                        <Skeleton className="h-4 w-1/2" />
                      </div>
                      <Skeleton className="h-6 w-24" />
                    </div>
                  ))}
                </div>
              ) : projectsByOutstandingQuery.isError ? (
                <p className={cn(ds.typography.caption, ds.status.danger.text)}>
                  Unable to load projects
                </p>
              ) : !projectsByOutstandingQuery.data?.projects ||
                projectsByOutstandingQuery.data.projects.length === 0 ? (
                <div className="py-12 text-center">
                  <CheckCircle2 className="mx-auto h-12 w-12 text-green-300 mb-3" aria-hidden="true" />
                  <p className={cn(ds.typography.bodyBold, ds.textColors.secondary, "mb-1")}>
                    All caught up!
                  </p>
                  <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                    No outstanding invoices at the moment
                  </p>
                </div>
              ) : (
                <div className={cn(ds.gap.normal, "space-y-3")}>
                  {projectsByOutstandingQuery.data.projects.map((project, idx) => (
                    <div
                      key={`${project.project_code as string}-${idx}`}
                      className={cn(
                        "flex items-center justify-between",
                        ds.borderRadius.card,
                        "border border-slate-100 p-4",
                        ds.hover.card,
                        "cursor-pointer"
                      )}
                    >
                      <div className="flex-1">
                        <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                          {(project.project_title as string) || (project.project_code as string)}
                        </p>
                        <p className={cn(ds.typography.tiny, ds.textColors.tertiary)}>
                          {(project.overdue_amount as number) > 0
                            ? `${formatCurrency(project.overdue_amount as number)} overdue`
                            : `${(project.overdue_invoice_count as number) || 0} overdue invoices`}
                        </p>
                      </div>
                      <p className={cn(ds.typography.bodyBold, ds.status.warning.text)}>
                        {formatCurrency(project.outstanding_usd as number)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Widget 3: Oldest Unpaid Invoices */}
          <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted)}>
                    Aging Invoices
                  </p>
                  <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
                    Oldest Unpaid Invoices
                  </CardTitle>
                </div>
                <Badge variant="outline" className={cn(ds.borderRadius.badge, ds.typography.tiny)}>
                  By days outstanding
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {oldestUnpaidQuery.isLoading ? (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-5 w-3/4" />
                        <Skeleton className="h-4 w-1/2" />
                      </div>
                      <div className="space-y-2 text-right">
                        <Skeleton className="h-6 w-24 ml-auto" />
                        <Skeleton className="h-5 w-16 ml-auto" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : oldestUnpaidQuery.isError ? (
                <p className={cn(ds.typography.caption, ds.status.danger.text)}>
                  Unable to load invoices
                </p>
              ) : !oldestUnpaidQuery.data?.invoices ||
                oldestUnpaidQuery.data.invoices.length === 0 ? (
                <div className="py-12 text-center">
                  <CheckCircle2 className="mx-auto h-12 w-12 text-green-300 mb-3" aria-hidden="true" />
                  <p className={cn(ds.typography.bodyBold, ds.textColors.secondary, "mb-1")}>
                    All invoices paid
                  </p>
                  <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                    Great work! All invoices have been paid
                  </p>
                </div>
              ) : (
                <div className={cn(ds.gap.normal, "space-y-3")}>
                  {oldestUnpaidQuery.data.invoices.map((invoice, idx) => (
                    <div
                      key={`${invoice.invoice_id as string}-${idx}`}
                      className={cn(
                        "flex items-center justify-between",
                        ds.borderRadius.card,
                        "border border-slate-100 p-4",
                        ds.hover.card,
                        "cursor-pointer"
                      )}
                    >
                      <div className="flex-1">
                        <p className={cn("font-semibold text-lg", ds.textColors.primary)}>
                          {(invoice.project_title as string) || (invoice.project_code as string)}
                        </p>
                        <p className={cn(
                          "text-sm",
                          (invoice.days_outstanding as number) >= 600 ? "text-red-600 font-bold" :
                          (invoice.days_outstanding as number) >= 180 ? "text-orange-600" :
                          (invoice.days_outstanding as number) >= 90 ? "text-yellow-600" :
                          "text-gray-600"
                        )}>
                          {invoice.days_outstanding as number} days old
                        </p>
                        <p className={cn(ds.typography.tiny, "text-gray-400")}>
                          {invoice.project_code as string} • Invoice {invoice.invoice_number as string}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                          {formatCurrency(invoice.amount_outstanding as number)}
                        </p>
                        <Badge
                          variant={(invoice.aging_bucket as string) === "90+ days" ? "destructive" : "outline"}
                          className={cn("mt-1", ds.typography.tiny)}
                        >
                          {invoice.aging_bucket as string}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Widget 4: Remaining Contract Value */}
          <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted)}>
                    Future Revenue
                  </p>
                  <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
                    Top 5 by Remaining Value
                  </CardTitle>
                </div>
                <Badge variant="outline" className={cn(ds.borderRadius.badge, ds.typography.tiny)}>
                  Uninvoiced work
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {projectsByRemainingQuery.isLoading ? (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-5 w-3/4" />
                        <Skeleton className="h-4 w-1/2" />
                      </div>
                      <Skeleton className="h-6 w-24" />
                    </div>
                  ))}
                </div>
              ) : projectsByRemainingQuery.isError ? (
                <p className={cn(ds.typography.caption, ds.status.danger.text)}>
                  Unable to load projects
                </p>
              ) : !projectsByRemainingQuery.data?.projects ||
                projectsByRemainingQuery.data.projects.length === 0 ? (
                <div className="py-12 text-center">
                  <Wallet className="mx-auto h-12 w-12 text-slate-300 mb-3" aria-hidden="true" />
                  <p className={cn(ds.typography.bodyBold, ds.textColors.secondary, "mb-1")}>
                    No uninvoiced work
                  </p>
                  <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                    All contract work has been invoiced
                  </p>
                </div>
              ) : (
                <div className={cn(ds.gap.normal, "space-y-3")}>
                  {projectsByRemainingQuery.data.projects.map((project, idx) => (
                    <div
                      key={`${project.project_code as string}-${idx}`}
                      className={cn(
                        "flex items-center justify-between",
                        ds.borderRadius.card,
                        "border border-slate-100 p-4",
                        ds.hover.card,
                        "cursor-pointer"
                      )}
                    >
                      <div className="flex-1">
                        <p className={cn("font-semibold text-lg", ds.textColors.primary)}>
                          {(project.project_title as string) || (project.project_code as string)}
                        </p>
                        <p className={cn("text-sm", "text-gray-600")}>
                          ${(project.total_remaining_usd as number).toLocaleString()} remaining •{" "}
                          {(project.percent_invoiced as number)?.toFixed(1)}% invoiced
                        </p>
                        <p className={cn(ds.typography.tiny, "text-gray-400")}>
                          {project.project_code as string}
                        </p>
                      </div>
                      <p className={cn(ds.typography.bodyBold, ds.status.info.text)}>
                        {formatCurrency(project.total_remaining_usd as number)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  subtitle,
  icon,
  trend = "neutral",
}: {
  label: string;
  value: string;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: "positive" | "negative" | "neutral";
}) {
  const getTrendClasses = () => {
    if (trend === "positive") return cn(ds.status.success.bg, ds.status.success.border);
    if (trend === "negative") return cn(ds.status.danger.bg, ds.status.danger.border);
    return cn(ds.status.neutral.bg, ds.status.neutral.border);
  };

  return (
    <Card className={cn(ds.borderRadius.card, "border", getTrendClasses())}>
      <CardContent className={ds.spacing.normal}>
        <div className="flex items-center justify-between mb-2">
          <p className={cn(ds.typography.label, ds.textColors.muted)}>{label}</p>
          {icon && (
            <div className={cn(ds.borderRadius.input, "bg-white p-2", ds.shadows.sm)}>
              {icon}
            </div>
          )}
        </div>
        <p
          className={cn(
            ds.typography.metricValue,
            "break-words",
            ds.textColors.primary
          )}
          title={value}
        >
          {value}
        </p>
        {subtitle && (
          <p className={cn("mt-1", ds.typography.tiny, ds.textColors.tertiary)}>{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
}
