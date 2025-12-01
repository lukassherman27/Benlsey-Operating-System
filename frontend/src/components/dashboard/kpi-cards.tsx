"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { DollarSign, Briefcase, TrendingUp, TrendingDown, AlertCircle, Clock, Trophy, PiggyBank } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { FeedbackButtons } from "@/components/ui/feedback-buttons";

interface KPICardsProps {
  period?: string;
  onPeriodChange?: (period: string) => void;
}

const PERIODS = [
  { value: "this_month", label: "This Month" },
  { value: "last_3_months", label: "Last 3 Months" },
  { value: "this_year", label: "2025" },
  { value: "last_year", label: "2024" },
  { value: "all_time", label: "All Time" },
];

export function KPICards({ period = "all_time", onPeriodChange }: KPICardsProps) {
  const { data: kpis, isLoading, error } = useQuery({
    queryKey: ["dashboard-kpis", period],
    queryFn: () => api.getDashboardKPIs({ period }),
    refetchInterval: 1000 * 60 * 5,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        {onPeriodChange && <PeriodSelector period={period} onPeriodChange={onPeriodChange} />}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="animate-pulse">
                  <div className="h-4 w-24 bg-slate-200 rounded mb-2" />
                  <div className="h-8 w-32 bg-slate-200 rounded" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error || !kpis) {
    return (
      <div className="space-y-4">
        {onPeriodChange && <PeriodSelector period={period} onPeriodChange={onPeriodChange} />}
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-red-600">Error loading KPIs</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const periodLabel = kpis.period_label || "All Time";

  return (
    <div className="space-y-4">
      {onPeriodChange && <PeriodSelector period={period} onPeriodChange={onPeriodChange} />}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI #1: Remaining Contract Value */}
        <KPICard
          title="Remaining Contract Value"
          subtitle="Contract value minus total paid"
          value={formatCurrency(kpis.remaining_contract_value?.value || 0)}
          trend={kpis.remaining_contract_value?.trend}
          icon={<TrendingUp className="h-5 w-5" />}
          trendPositive={true}
        />

        {/* KPI #2: Paid in Period */}
        <KPICard
          title={`Paid (${periodLabel})`}
          subtitle={kpis.paid_in_period?.previous_value
            ? `vs ${formatCurrency(kpis.paid_in_period.previous_value)} prev period`
            : "Payments received"}
          value={formatCurrency(kpis.paid_in_period?.value || kpis.total_paid_to_date?.value || 0)}
          trend={kpis.paid_in_period?.trend || kpis.total_paid_to_date?.trend}
          icon={<DollarSign className="h-5 w-5" />}
          trendPositive={true}
        />

        {/* KPI #3: Contracts Signed */}
        <KPICard
          title={`Contracts Signed (${periodLabel})`}
          subtitle={kpis.contracts_signed?.amount
            ? `Value: ${formatCurrency(kpis.contracts_signed.amount)}`
            : `${kpis.active_projects?.value || 0} active projects total`}
          value={(kpis.contracts_signed?.value || kpis.contracts_signed_2025?.value || 0).toString()}
          trend={kpis.contracts_signed?.trend || kpis.contracts_signed_2025?.trend}
          icon={<Briefcase className="h-5 w-5" />}
          trendPositive={true}
        />

        {/* KPI #4: Outstanding Invoices */}
        <KPICard
          title="Outstanding Invoices"
          subtitle={kpis.outstanding_invoices?.overdue_count
            ? `${kpis.outstanding_invoices.overdue_count} overdue (${formatCurrency(kpis.outstanding_invoices.overdue_amount || 0)})`
            : "Invoiced but not yet paid"}
          value={formatCurrency(kpis.outstanding_invoices?.value || 0)}
          trend={kpis.outstanding_invoices?.trend}
          icon={<AlertCircle className="h-5 w-5" />}
          trendPositive={false}
          highlight={kpis.outstanding_invoices?.overdue_count ? "warning" : undefined}
        />
      </div>

      {/* Secondary KPIs Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MiniKPICard
          title="Avg Days to Payment"
          value={`${kpis.avg_days_to_payment || 0} days`}
          icon={<Clock className="h-4 w-4" />}
        />
        <MiniKPICard
          title="Win Rate"
          value={kpis.win_rate !== null && kpis.win_rate !== undefined ? `${kpis.win_rate}%` : "N/A"}
          icon={<Trophy className="h-4 w-4" />}
        />
        <MiniKPICard
          title="Pipeline Value"
          value={formatCurrency(kpis.pipeline_value || 0)}
          icon={<PiggyBank className="h-4 w-4" />}
        />
        <MiniKPICard
          title="Active Projects"
          value={(kpis.active_projects?.value || 0).toString()}
          icon={<Briefcase className="h-4 w-4" />}
        />
      </div>
    </div>
  );
}

function PeriodSelector({ period, onPeriodChange }: { period: string; onPeriodChange: (p: string) => void }) {
  return (
    <div className="flex flex-wrap gap-2">
      {PERIODS.map((p) => (
        <button
          key={p.value}
          onClick={() => onPeriodChange(p.value)}
          className={cn(
            "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
            period === p.value
              ? "bg-teal-600 text-white"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
          )}
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}

interface TrendData {
  value: number;
  direction: "up" | "down" | "neutral";
  label: string;
  is_positive?: boolean;
}

interface KPICardProps {
  title: string;
  subtitle: string;
  value: string;
  trend?: TrendData;
  icon: React.ReactNode;
  trendPositive: boolean;
  highlight?: "warning" | "danger";
}

function KPICard({ title, subtitle, value, trend, icon, trendPositive, highlight }: KPICardProps) {
  const hasTrend = trend && trend.direction && trend.direction !== "neutral" && trend.value !== 0;

  // Determine color based on direction and whether up is good
  // Use is_positive from backend if available, otherwise calculate
  const isGoodTrend = trend?.is_positive !== undefined
    ? trend.is_positive
    : (trend?.direction === "up" ? trendPositive : !trendPositive);
  const trendColor = isGoodTrend ? "text-green-600" : "text-red-600";

  const featureId = title.toLowerCase().replace(/\s+/g, "_").replace(/[()]/g, "");

  return (
    <Card className={cn(
      "hover:shadow-md transition-shadow",
      highlight === "warning" && "border-amber-300 bg-amber-50/50",
      highlight === "danger" && "border-red-300 bg-red-50/50"
    )}>
      <CardHeader className="flex flex-row items-start justify-between pb-2">
        <div className="flex items-center gap-2">
          <div className={cn(
            "p-2 rounded-lg",
            highlight === "warning" ? "bg-amber-100 text-amber-600" :
            highlight === "danger" ? "bg-red-100 text-red-600" :
            "bg-blue-50 text-blue-600"
          )}>
            {icon}
          </div>
        </div>
        {hasTrend && (
          <div
            className={`flex items-center gap-1 text-sm font-medium ${trendColor}`}
            title="vs previous period"
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

function MiniKPICard({ title, value, icon }: { title: string; value: string; icon: React.ReactNode }) {
  return (
    <Card className="hover:shadow-sm transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-1">
          <div className="text-slate-400">{icon}</div>
          <p className="text-xs font-medium text-slate-500">{title}</p>
        </div>
        <p className="text-lg font-semibold text-slate-900">{value}</p>
      </CardContent>
    </Card>
  );
}
