"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Clock,
  AlertCircle,
  ArrowUp,
  ArrowDown,
  Percent,
  Calendar,
  Building,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface AnalyticsDashboard {
  total_pipeline_value?: number;
  total_proposals?: number;
  active_proposals?: number;
  contracts_won?: number;
  contracts_won_value?: number;
  conversion_rate?: number;
  avg_deal_size?: number;
  avg_days_to_close?: number;
  revenue_this_month?: number;
  revenue_last_month?: number;
  revenue_change_percent?: number;
  outstanding_invoices?: number;
  outstanding_value?: number;
  overdue_value?: number;
  projects_by_status?: { status: string; count: number }[];
  proposals_by_status?: { status: string; count: number; value: number }[];
  revenue_by_month?: { month: string; revenue: number }[];
  top_clients?: { client: string; revenue: number; projects: number }[];
}

// Fetch analytics
async function fetchAnalytics(): Promise<AnalyticsDashboard> {
  const response = await fetch(`${API_BASE_URL}/api/analytics/dashboard`);
  if (!response.ok) {
    // Return defaults if endpoint doesn't exist
    return {};
  }
  return response.json();
}

// Format currency
function formatCurrency(value?: number): string {
  if (!value) return "$0";
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`;
  }
  return `$${value.toLocaleString()}`;
}

// Format full currency
function formatFullCurrency(value?: number): string {
  if (!value) return "$0";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

// Loading skeleton
function AnalyticsSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className={cn(ds.borderRadius.card, "border-slate-200")}>
            <CardContent className="pt-6">
              <Skeleton className="h-4 w-20 mb-2" />
              <Skeleton className="h-8 w-24" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Error state
function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50")}>
      <CardContent className="py-12 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
        <p className={cn(ds.typography.heading3, "text-red-700 mb-2")}>
          Failed to load analytics
        </p>
        <p className={cn(ds.typography.body, "text-red-600 mb-4")}>
          Crunching numbers is hard. Give it another shot.
        </p>
        <Button onClick={onRetry} variant="outline" className="border-red-200 text-red-700 hover:bg-red-100">
          Try again
        </Button>
      </CardContent>
    </Card>
  );
}

// KPI Card component
function KPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendLabel,
  color = "slate",
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  trend?: number;
  trendLabel?: string;
  color?: "slate" | "teal" | "emerald" | "amber" | "red" | "blue";
}) {
  const colorClasses = {
    slate: { bg: "bg-slate-100", icon: "text-slate-700", border: "border-slate-200" },
    teal: { bg: "bg-teal-100", icon: "text-teal-700", border: "border-teal-200" },
    emerald: { bg: "bg-emerald-100", icon: "text-emerald-700", border: "border-emerald-200" },
    amber: { bg: "bg-amber-100", icon: "text-amber-700", border: "border-amber-200" },
    red: { bg: "bg-red-100", icon: "text-red-700", border: "border-red-200" },
    blue: { bg: "bg-blue-100", icon: "text-blue-700", border: "border-blue-200" },
  };

  const colors = colorClasses[color];

  return (
    <Card className={cn(ds.borderRadius.card, colors.border)}>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div>
            <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>{title}</p>
            <p className={cn(ds.typography.heading2, ds.textColors.primary, "mt-1")}>{value}</p>
            {subtitle && (
              <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mt-1")}>{subtitle}</p>
            )}
            {trend !== undefined && (
              <div className={cn("flex items-center gap-1 mt-2", trend >= 0 ? "text-emerald-600" : "text-red-600")}>
                {trend >= 0 ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                <span className="text-xs font-medium">{Math.abs(trend).toFixed(1)}%</span>
                {trendLabel && <span className="text-xs text-slate-500">{trendLabel}</span>}
              </div>
            )}
          </div>
          <div className={cn("p-2 rounded-lg", colors.bg)}>
            <Icon className={cn("h-5 w-5", colors.icon)} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Simple bar chart component
function SimpleBarChart({
  data,
  valueKey,
  labelKey,
  color = "teal",
}: {
  data: Record<string, unknown>[];
  valueKey: string;
  labelKey: string;
  color?: string;
}) {
  const maxValue = Math.max(...data.map((d) => (d[valueKey] as number) || 0));

  return (
    <div className="space-y-3">
      {data.map((item, i) => {
        const value = (item[valueKey] as number) || 0;
        const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;

        return (
          <div key={i} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className={ds.textColors.secondary}>{item[labelKey] as string}</span>
              <span className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                {typeof value === "number" && value > 1000
                  ? formatCurrency(value)
                  : value}
              </span>
            </div>
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={cn("h-full rounded-full transition-all", `bg-${color}-500`)}
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Funnel visualization
function ProposalFunnel({ data }: { data: { status: string; count: number; value: number }[] }) {
  const statusOrder = ["First Contact", "Drafting", "Proposal Sent", "Contract Signed"];
  const sortedData = statusOrder
    .map((status) => data.find((d) => d.status === status))
    .filter(Boolean) as typeof data;

  const maxCount = Math.max(...sortedData.map((d) => d.count));

  const statusColors: Record<string, string> = {
    "First Contact": "bg-slate-400",
    Drafting: "bg-blue-500",
    "Proposal Sent": "bg-amber-500",
    "Contract Signed": "bg-emerald-500",
  };

  return (
    <div className="space-y-4">
      {sortedData.map((item, _i) => {
        const width = maxCount > 0 ? (item.count / maxCount) * 100 : 0;

        return (
          <div key={item.status} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className={ds.textColors.secondary}>{item.status}</span>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  {item.count}
                </Badge>
                <span className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                  {formatCurrency(item.value)}
                </span>
              </div>
            </div>
            <div className="h-8 bg-slate-100 rounded-lg overflow-hidden flex items-center">
              <div
                className={cn(
                  "h-full rounded-lg transition-all flex items-center justify-end px-2",
                  statusColors[item.status] || "bg-slate-400"
                )}
                style={{ width: `${Math.max(width, 10)}%` }}
              >
                {width > 20 && (
                  <span className="text-white text-xs font-medium">{item.count}</span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState("12m");

  // Fetch analytics
  const { data: analytics, isLoading, error, refetch } = useQuery({
    queryKey: ["analytics", dateRange],
    queryFn: fetchAnalytics,
    staleTime: 1000 * 60 * 5,
  });

  return (
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            The Numbers
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Business intelligence at a glance. Where the truth lives.
          </p>
        </div>
        <Select value={dateRange} onValueChange={setDateRange}>
          <SelectTrigger className="w-[150px]">
            <Calendar className="h-4 w-4 mr-2 text-slate-400" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="3m">Last 3 months</SelectItem>
            <SelectItem value="6m">Last 6 months</SelectItem>
            <SelectItem value="12m">Last 12 months</SelectItem>
            <SelectItem value="ytd">Year to date</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <AnalyticsSkeleton />
      ) : error ? (
        <ErrorState onRetry={() => refetch()} />
      ) : (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPICard
              title="Pipeline Value"
              value={formatCurrency(analytics?.total_pipeline_value)}
              subtitle={`${analytics?.active_proposals || 0} active proposals`}
              icon={DollarSign}
              color="teal"
            />
            <KPICard
              title="Contracts Won"
              value={analytics?.contracts_won || 0}
              subtitle={formatFullCurrency(analytics?.contracts_won_value)}
              icon={Target}
              color="emerald"
            />
            <KPICard
              title="Conversion Rate"
              value={`${(analytics?.conversion_rate || 0).toFixed(1)}%`}
              subtitle="Proposals to contracts"
              icon={Percent}
              color="blue"
            />
            <KPICard
              title="Avg Deal Size"
              value={formatCurrency(analytics?.avg_deal_size)}
              subtitle={`${analytics?.avg_days_to_close || 0} days avg to close`}
              icon={BarChart3}
              color="slate"
            />
          </div>

          {/* Revenue Section */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className={cn(ds.borderRadius.card, "border-emerald-200 bg-emerald-50/30")}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className={cn(ds.typography.caption, "text-emerald-700")}>This Month</p>
                    <p className={cn(ds.typography.heading2, "text-emerald-800 mt-1")}>
                      {formatFullCurrency(analytics?.revenue_this_month)}
                    </p>
                    {analytics?.revenue_change_percent !== undefined && (
                      <div
                        className={cn(
                          "flex items-center gap-1 mt-2",
                          analytics.revenue_change_percent >= 0 ? "text-emerald-600" : "text-red-600"
                        )}
                      >
                        {analytics.revenue_change_percent >= 0 ? (
                          <TrendingUp className="h-4 w-4" />
                        ) : (
                          <TrendingDown className="h-4 w-4" />
                        )}
                        <span className="text-sm font-medium">
                          {Math.abs(analytics.revenue_change_percent).toFixed(1)}% vs last month
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="p-2 rounded-lg bg-emerald-100">
                    <TrendingUp className="h-5 w-5 text-emerald-700" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className={cn(ds.borderRadius.card, "border-amber-200 bg-amber-50/30")}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className={cn(ds.typography.caption, "text-amber-700")}>Outstanding</p>
                    <p className={cn(ds.typography.heading2, "text-amber-800 mt-1")}>
                      {formatFullCurrency(analytics?.outstanding_value)}
                    </p>
                    <p className={cn(ds.typography.caption, "text-amber-600 mt-1")}>
                      {analytics?.outstanding_invoices || 0} invoices pending
                    </p>
                  </div>
                  <div className="p-2 rounded-lg bg-amber-100">
                    <Clock className="h-5 w-5 text-amber-700" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50/30")}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className={cn(ds.typography.caption, "text-red-700")}>Overdue</p>
                    <p className={cn(ds.typography.heading2, "text-red-800 mt-1")}>
                      {formatFullCurrency(analytics?.overdue_value)}
                    </p>
                    <p className={cn(ds.typography.caption, "text-red-600 mt-1")}>
                      Needs immediate attention
                    </p>
                  </div>
                  <div className="p-2 rounded-lg bg-red-100">
                    <AlertCircle className="h-5 w-5 text-red-700" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Proposal Funnel */}
            <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
              <CardHeader>
                <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
                  Proposal Pipeline
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analytics?.proposals_by_status && analytics.proposals_by_status.length > 0 ? (
                  <ProposalFunnel data={analytics.proposals_by_status} />
                ) : (
                  <div className="h-64 flex items-center justify-center">
                    <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                      No pipeline data available
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Revenue by Month */}
            <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
              <CardHeader>
                <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
                  Monthly Revenue
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analytics?.revenue_by_month && analytics.revenue_by_month.length > 0 ? (
                  <SimpleBarChart
                    data={analytics.revenue_by_month}
                    valueKey="revenue"
                    labelKey="month"
                    color="teal"
                  />
                ) : (
                  <div className="h-64 flex items-center justify-center">
                    <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                      No revenue data available
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Top Clients */}
          {analytics?.top_clients && analytics.top_clients.length > 0 && (
            <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
              <CardHeader>
                <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
                  Top Clients
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {analytics.top_clients.map((client, i) => (
                    <Card key={i} className={cn(ds.borderRadius.card, "border-slate-200")}>
                      <CardContent className="pt-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center">
                            <Building className="h-5 w-5 text-slate-600" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={cn(ds.typography.bodyBold, ds.textColors.primary, "truncate")}>
                              {client.client}
                            </p>
                            <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                              {client.projects} project{client.projects !== 1 ? "s" : ""}
                            </p>
                          </div>
                          <p className={cn(ds.typography.bodyBold, "text-emerald-600")}>
                            {formatCurrency(client.revenue)}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
