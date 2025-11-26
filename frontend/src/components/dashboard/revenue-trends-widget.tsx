"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

export function RevenueTrendsWidget() {
  const metricsQuery = useQuery({
    queryKey: ["dashboard-financial-metrics"],
    queryFn: api.getDashboardFinancialMetrics,
    refetchInterval: 1000 * 60 * 5,
  });

  const proposalStatsQuery = useQuery({
    queryKey: ["proposalTrackerStats"],
    queryFn: api.getProposalTrackerStats,
    refetchInterval: 1000 * 60 * 5,
  });

  const metrics = metricsQuery.data?.metrics;
  const proposalStats = proposalStatsQuery.data?.stats;

  const totalContractValue = metrics?.total_contract_value || 0;
  const totalInvoiced = metrics?.total_invoiced || 0;
  const totalPaid = metrics?.total_paid || 0;
  const pipelineValue = proposalStats?.total_pipeline_value || 0;

  const invoicedPercentage = totalContractValue > 0
    ? (totalInvoiced / totalContractValue) * 100
    : 0;
  const paidPercentage = totalInvoiced > 0
    ? (totalPaid / totalInvoiced) * 100
    : 0;

  const revenueMetrics = [
    {
      label: "Active Contracts",
      value: formatCurrency(totalContractValue),
      subtitle: `${metrics?.active_project_count || 0} projects`,
      trend: "neutral" as const,
      percentage: null,
    },
    {
      label: "Invoiced",
      value: formatCurrency(totalInvoiced),
      subtitle: `${invoicedPercentage.toFixed(1)}% of contracts`,
      trend: invoicedPercentage > 50 ? "positive" : "neutral" as const,
      percentage: invoicedPercentage,
    },
    {
      label: "Collected",
      value: formatCurrency(totalPaid),
      subtitle: `${paidPercentage.toFixed(1)}% of invoices`,
      trend: paidPercentage > 80 ? "positive" : paidPercentage > 60 ? "neutral" : "negative" as const,
      percentage: paidPercentage,
    },
    {
      label: "Pipeline",
      value: formatCurrency(pipelineValue),
      subtitle: `${proposalStats?.total_proposals || 0} active proposals`,
      trend: pipelineValue > 0 ? "positive" : "neutral" as const,
      percentage: null,
    },
  ];

  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <p className={cn(ds.typography.label, ds.textColors.muted)}>
              Revenue Overview
            </p>
            <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
              Financial Snapshot
            </CardTitle>
          </div>
          <Badge variant="secondary" className={cn(ds.borderRadius.badge, ds.gap.tight)}>
            <TrendingUp className="h-3.5 w-3.5" />
            Live
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {metricsQuery.isLoading ? (
          <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
            Loading revenue data...
          </p>
        ) : (
          <div className={cn(ds.gap.normal, "space-y-4")}>
            {/* Revenue flow visualization - RESPONSIVE */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {revenueMetrics.map((metric, idx) => {
                const getTrendIcon = () => {
                  if (metric.trend === "positive") return <ArrowUpRight className={cn("h-4 w-4", ds.status.success.icon)} />;
                  if (metric.trend === "negative") return <ArrowDownRight className={cn("h-4 w-4", ds.status.danger.icon)} />;
                  return null;
                };

                const getTrendClasses = () => {
                  if (metric.trend === "positive") return cn(ds.status.success.bg, ds.status.success.border);
                  if (metric.trend === "negative") return cn(ds.status.danger.bg, ds.status.danger.border);
                  return cn(ds.status.neutral.bg, ds.status.neutral.border);
                };

                const getBarColor = () => {
                  if (metric.trend === "positive") return "bg-green-500";
                  if (metric.trend === "negative") return "bg-red-500";
                  return "bg-slate-400";
                };

                return (
                  <div
                    key={idx}
                    className={cn(
                      ds.borderRadius.card,
                      "border p-4 transition-shadow",
                      getTrendClasses(),
                      ds.hover.card
                    )}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <p className={cn(ds.typography.label, ds.textColors.secondary, "text-[10px]")}>
                        {metric.label}
                      </p>
                      {getTrendIcon()}
                    </div>
                    <p className={cn(ds.typography.heading2, ds.textColors.primary, "mb-1")}>
                      {metric.value}
                    </p>
                    <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                      {metric.subtitle}
                    </p>
                    {metric.percentage !== null && (
                      <div className="mt-3">
                        <div className="w-full bg-white rounded-full h-1.5 overflow-hidden">
                          <div
                            className={cn("h-full transition-all duration-500", getBarColor())}
                            style={{ width: `${Math.min(metric.percentage, 100)}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Summary insights */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className={cn(
                ds.borderRadius.card,
                "bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200",
                ds.spacing.normal
              )}>
                <p className={cn(ds.typography.captionBold, "text-blue-900 mb-1")}>
                  Collection Rate
                </p>
                <p className={cn(ds.typography.heading2, "text-blue-900")}>
                  {paidPercentage.toFixed(1)}%
                </p>
                <p className={cn(ds.typography.tiny, "text-blue-700 mt-1")}>
                  of invoiced amount collected
                </p>
              </div>
              <div className={cn(
                ds.borderRadius.card,
                "bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200",
                ds.spacing.normal
              )}>
                <p className={cn(ds.typography.captionBold, "text-purple-900 mb-1")}>
                  Total Pipeline
                </p>
                <p className={cn(ds.typography.heading2, "text-purple-900")}>
                  {formatCurrency(totalContractValue + pipelineValue)}
                </p>
                <p className={cn(ds.typography.tiny, "text-purple-700 mt-1")}>
                  active + proposals combined
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
