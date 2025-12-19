"use client";

import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  DollarSign,
  BarChart3,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";
import type { TopValueProposal } from "@/lib/types";
import { ProposalLink } from "@/components/cross-link/entity-link";

interface AnalyticsInsightsProps {
  className?: string;
}

export function AnalyticsInsights({ className }: AnalyticsInsightsProps) {
  // Fetch pipeline data for analytics
  const { data: stats, isLoading } = useQuery({
    queryKey: ["proposal-stats"],
    queryFn: () => api.getProposalStats(),
    staleTime: 1000 * 60 * 5,
  });

  // Fetch top proposals
  const { data: topProposalsData } = useQuery({
    queryKey: ["top-value-proposals"],
    queryFn: () => api.getTopValueProposals({ limit: 3 }),
    staleTime: 1000 * 60 * 5,
  });

  // Extract the proposals array from the response
  const topProposals = (topProposalsData as { data?: TopValueProposal[] })?.data ?? [];

  if (isLoading) {
    return (
      <div className={cn("rounded-xl border bg-white p-6", className)}>
        <Skeleton className="h-6 w-32 mb-4" />
        <div className="grid grid-cols-2 gap-4">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      </div>
    );
  }

  // Calculate derived metrics
  const totalProposals = stats?.total_proposals ?? 0;
  const activeProjects = stats?.active_projects ?? 0;
  const healthyCount = stats?.healthy ?? 0;
  const winRate = totalProposals > 0 ? Math.round((activeProjects / totalProposals) * 100) : 0;

  // Mock trend data (in a real implementation, this would come from the backend)
  const winRateTrend = 5; // +5% vs last quarter
  const pipelineGrowth = 12; // +12% vs last month

  return (
    <div
      className={cn(
        "rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white overflow-hidden",
        className
      )}
    >
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-purple-600" />
            <h3 className="font-semibold text-slate-800">Business Insights</h3>
          </div>
          <Badge
            variant="outline"
            className="text-xs bg-purple-50 text-purple-700 border-purple-200"
          >
            <Sparkles className="h-3 w-3 mr-1" />
            Analytics
          </Badge>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="p-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Win Rate */}
          <div className="p-4 rounded-lg bg-white border border-slate-100">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
              Win Rate
            </p>
            <div className="flex items-end gap-2">
              <span className="text-2xl font-bold text-slate-800">{winRate}%</span>
              <TrendIndicator value={winRateTrend} />
            </div>
            <p className="text-xs text-slate-400 mt-1">vs 63% last Q</p>
          </div>

          {/* Pipeline Value */}
          <div className="p-4 rounded-lg bg-white border border-slate-100">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
              Pipeline
            </p>
            <div className="flex items-end gap-2">
              <span className="text-2xl font-bold text-slate-800">
                ${((stats as any)?.pipeline_value ?? 0 / 1000000).toFixed(1)}M
              </span>
              <TrendIndicator value={pipelineGrowth} />
            </div>
            <p className="text-xs text-slate-400 mt-1">Active proposals</p>
          </div>

          {/* Active Projects */}
          <div className="p-4 rounded-lg bg-white border border-slate-100">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
              In Delivery
            </p>
            <div className="flex items-end gap-2">
              <span className="text-2xl font-bold text-slate-800">
                {activeProjects}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">Active projects</p>
          </div>

          {/* Health Score */}
          <div className="p-4 rounded-lg bg-white border border-slate-100">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
              Health
            </p>
            <div className="flex items-end gap-2">
              <span className="text-2xl font-bold text-emerald-600">
                {healthyCount}/{totalProposals - activeProjects}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">Proposals healthy</p>
          </div>
        </div>

        {/* Top Proposals */}
        {topProposals && topProposals.length > 0 && (
          <div className="mt-4 p-4 rounded-lg bg-slate-50 border border-slate-100">
            <div className="flex items-center gap-2 mb-3">
              <Target className="h-4 w-4 text-amber-600" />
              <h4 className="text-sm font-medium text-slate-700">
                Top Pipeline Opportunities
              </h4>
            </div>
            <div className="space-y-2">
              {topProposals.map((proposal, index) => (
                <div
                  key={proposal.project_code}
                  className="flex items-center justify-between py-2 border-b border-slate-200 last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold text-slate-400 w-4">
                      {index + 1}
                    </span>
                    <div>
                      <ProposalLink
                        projectCode={proposal.project_code}
                        label={proposal.project_name}
                        showIcon={false}
                        className="text-sm font-medium"
                      />
                      <p className="text-xs text-slate-500">
                        {proposal.client_name || "Unknown client"}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-semibold text-slate-800">
                      ${(proposal.total_fee_usd / 1000000).toFixed(1)}M
                    </span>
                    {proposal.phase && (
                      <Badge variant="outline" className="ml-2 text-xs">
                        {proposal.phase}
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function TrendIndicator({ value }: { value: number }) {
  if (value === 0) {
    return (
      <span className="flex items-center text-xs text-slate-400">
        <Minus className="h-3 w-3" />
      </span>
    );
  }

  const isPositive = value > 0;
  const Icon = isPositive ? TrendingUp : TrendingDown;
  const color = isPositive ? "text-emerald-600" : "text-red-600";

  return (
    <span className={cn("flex items-center text-xs font-medium", color)}>
      <Icon className="h-3 w-3 mr-0.5" />
      {isPositive ? "+" : ""}
      {value}%
    </span>
  );
}
