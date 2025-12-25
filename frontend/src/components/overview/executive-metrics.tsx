"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, cn } from "@/lib/utils";
import { ProposalTrackerItem } from "@/lib/types";
import {
  DollarSign,
  TrendingUp,
  Clock,
  AlertTriangle,
  Target,
} from "lucide-react";

interface ExecutiveMetricsProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  stats: any;
  proposals: ProposalTrackerItem[];
  isLoading: boolean;
}

export function ExecutiveMetrics({ stats, proposals, isLoading }: ExecutiveMetricsProps) {
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  // Calculate metrics
  const activeProposals = proposals.filter(p =>
    !["Contract Signed", "Lost", "Declined", "Dormant"].includes(p.current_status)
  );

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const overdueItems = activeProposals.filter(p =>
    p.action_due && new Date(p.action_due) < today
  );

  const atRiskValue = overdueItems.reduce((sum, p) => sum + (p.project_value || 0), 0);

  // Calculate win rate from closed deals
  const wonDeals = proposals.filter(p => p.current_status === "Contract Signed");
  const lostDeals = proposals.filter(p =>
    ["Lost", "Declined"].includes(p.current_status)
  );
  const closedDeals = wonDeals.length + lostDeals.length;
  const winRate = closedDeals > 0 ? Math.round((wonDeals.length / closedDeals) * 100) : 0;

  // Average days to close for won deals
  const avgCycle = Math.round(stats?.avg_days_in_status || 0);

  // Top opportunities by win probability
  const topOpportunities = [...activeProposals]
    .filter(p => p.win_probability != null)
    .sort((a, b) => (b.win_probability || 0) - (a.win_probability || 0))
    .slice(0, 5);

  // Pipeline funnel data
  const funnelData = [
    { status: "First Contact", label: "First Contact" },
    { status: "Proposal Prep", label: "Proposal Prep" },
    { status: "Proposal Sent", label: "Proposal Sent" },
    { status: "Negotiation", label: "Negotiation" },
  ].map(({ status, label }) => {
    const items = activeProposals.filter(p => p.current_status === status);
    return {
      label,
      count: items.length,
      value: items.reduce((sum, p) => sum + (p.project_value || 0), 0),
    };
  });

  return (
    <div className="space-y-6">
      {/* Top Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="h-4 w-4 text-slate-400" />
              <span className="text-xs font-medium text-slate-500 uppercase">Pipeline</span>
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {formatCurrency(stats?.active_proposals_value || 0)}
            </p>
            <p className="text-sm text-slate-500">
              {stats?.active_proposals_count || 0} active proposals
            </p>
          </CardContent>
        </Card>

        <Card className="border-emerald-200 bg-emerald-50/30">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-2">
              <Target className="h-4 w-4 text-emerald-500" />
              <span className="text-xs font-medium text-emerald-600 uppercase">Win Rate</span>
            </div>
            <p className="text-2xl font-bold text-emerald-700">{winRate}%</p>
            <p className="text-sm text-emerald-600">
              {wonDeals.length} won / {closedDeals} closed
            </p>
          </CardContent>
        </Card>

        <Card className="border-blue-200 bg-blue-50/30">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="h-4 w-4 text-blue-500" />
              <span className="text-xs font-medium text-blue-600 uppercase">Avg Cycle</span>
            </div>
            <p className="text-2xl font-bold text-blue-700">{avgCycle} days</p>
            <p className="text-sm text-blue-600">average time in stage</p>
          </CardContent>
        </Card>

        <Card className="border-red-200 bg-red-50/30">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <span className="text-xs font-medium text-red-600 uppercase">At Risk</span>
            </div>
            <p className="text-2xl font-bold text-red-700">
              {overdueItems.length}
            </p>
            <p className="text-sm text-red-600">
              {formatCurrency(atRiskValue)} value
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pipeline Funnel */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Pipeline Funnel
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {funnelData.map(({ label, count, value }) => {
              const maxValue = Math.max(...funnelData.map(d => d.value));
              const widthPercent = maxValue > 0 ? Math.max((value / maxValue) * 100, 10) : 10;

              return (
                <div key={label} className="flex items-center gap-3">
                  <span className="w-28 text-sm font-medium text-slate-600">{label}</span>
                  <div className="flex-1 h-8 bg-slate-100 rounded overflow-hidden">
                    <div
                      className="h-full bg-blue-400 flex items-center justify-between px-2 transition-all"
                      style={{ width: `${widthPercent}%` }}
                    >
                      <span className="text-white text-xs font-bold">{count}</span>
                      {value > 0 && (
                        <span className="text-white text-xs">{formatCurrency(value)}</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Top Opportunities */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 flex items-center gap-2">
              <Target className="h-4 w-4" />
              Top Opportunities
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {topOpportunities.length === 0 ? (
              <p className="text-sm text-slate-400 py-4 text-center">
                No opportunities with win probability calculated
              </p>
            ) : (
              topOpportunities.map((p, idx) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={cn(
                        "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold",
                        idx === 0 ? "bg-amber-100 text-amber-700" :
                        idx === 1 ? "bg-slate-100 text-slate-600" :
                        idx === 2 ? "bg-orange-100 text-orange-700" :
                        "bg-slate-50 text-slate-500"
                      )}
                    >
                      {idx + 1}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-slate-900 truncate max-w-[180px]">
                        {p.project_name}
                      </p>
                      <p className="text-xs text-slate-500">
                        {formatCurrency(p.project_value)}
                      </p>
                    </div>
                  </div>
                  <div
                    className={cn(
                      "text-sm font-bold",
                      (p.win_probability || 0) >= 60 ? "text-emerald-600" :
                      (p.win_probability || 0) >= 30 ? "text-amber-600" :
                      "text-slate-400"
                    )}
                  >
                    {p.win_probability}%
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
