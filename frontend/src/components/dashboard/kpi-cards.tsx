"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DollarSign, Briefcase, TrendingUp, TrendingDown, AlertCircle } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { FeedbackButtons } from "@/components/ui/feedback-buttons";

export function KPICards() {
  const { data: kpis, isLoading, error } = useQuery({
    queryKey: ["dashboard-kpis"],
    queryFn: api.getDashboardKPIs,
    refetchInterval: 1000 * 60 * 5, // Refresh every 5 minutes
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground">Loading...</p>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error || !kpis) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-red-600">Error loading KPIs</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* KPI #1: Remaining Contract Value */}
      <KPICard
        title="Remaining Contract Value"
        subtitle="Signed but not yet invoiced"
        value={formatCurrency(kpis.remaining_contract_value.value)}
        trend={kpis.remaining_contract_value.trend}
        icon={<TrendingUp className="h-5 w-5" />}
        trendPositive={true}
        trendPeriodDays={kpis.trend_period_days}
      />

      {/* KPI #2: Active Projects & Proposals */}
      <KPICard
        title="Active Projects"
        subtitle={`${kpis.active_proposals.value} active proposals`}
        value={kpis.active_projects.value.toString()}
        trend={kpis.active_projects.trend}
        icon={<Briefcase className="h-5 w-5" />}
        trendPositive={true}
        trendPeriodDays={kpis.trend_period_days}
      />

      {/* KPI #3: Revenue YTD */}
      <KPICard
        title="Revenue (YTD)"
        subtitle="Total invoiced this year"
        value={formatCurrency(kpis.revenue_ytd.value)}
        trend={kpis.revenue_ytd.trend}
        icon={<DollarSign className="h-5 w-5" />}
        trendPositive={true}
        trendPeriodDays={kpis.trend_period_days}
      />

      {/* KPI #4: Outstanding Invoices */}
      <KPICard
        title="Outstanding Invoices"
        subtitle="Unpaid invoices"
        value={formatCurrency(kpis.outstanding_invoices.value)}
        trend={kpis.outstanding_invoices.trend}
        icon={<AlertCircle className="h-5 w-5" />}
        trendPositive={false} // For outstanding, down is good!
        trendPeriodDays={kpis.trend_period_days}
      />
    </div>
  );
}

interface TrendData {
  value: number;
  direction: "up" | "down" | "neutral";
  label: string;
}

interface KPICardProps {
  title: string;
  subtitle: string;
  value: string;
  trend: TrendData;
  icon: React.ReactNode;
  trendPositive: boolean; // Whether upward trend is good or bad
  trendPeriodDays?: number;
}

function KPICard({ title, subtitle, value, trend, icon, trendPositive, trendPeriodDays = 30 }: KPICardProps) {
  const hasTrend = trend.direction !== "neutral" && trend.value !== 0;

  // Determine color based on direction and whether up is good
  const isGoodTrend = trend.direction === "up" ? trendPositive : !trendPositive;
  const trendColor = isGoodTrend ? "text-green-600" : "text-red-600";

  // Generate feature ID for feedback
  const featureId = title.toLowerCase().replace(/\s+/g, "_");

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="flex flex-row items-start justify-between pb-2">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
            {icon}
          </div>
        </div>
        {hasTrend && (
          <div
            className={`flex items-center gap-1 text-sm font-medium ${trendColor} cursor-help`}
            title={`${trendPeriodDays}-day change (vs. ${trendPeriodDays} days ago)`}
          >
            {trend.direction === "up" ? (
              <TrendingUp className="h-4 w-4" />
            ) : (
              <TrendingDown className="h-4 w-4" />
            )}
            <span>{trend.label}</span>
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-3 pb-4">
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">
            {title}
          </p>
          <p className="text-2xl font-bold text-gray-900">
            {value}
          </p>
          <p className="text-xs text-muted-foreground">
            {subtitle}
          </p>
        </div>

        {/* RLHF: Data Quality Feedback */}
        <div className="pt-2 border-t">
          <FeedbackButtons
            featureType="kpi"
            featureId={featureId}
            currentValue={value}
            compact
          />
        </div>
      </CardContent>
    </Card>
  );
}
