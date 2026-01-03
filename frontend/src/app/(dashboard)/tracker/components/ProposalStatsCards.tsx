"use client";

import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle2, XCircle, TrendingUp, AlertTriangle } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";

interface ProposalStats {
  all_proposals_total?: number;
  total_proposals?: number;
  all_proposals_value?: number;
  total_pipeline_value?: number;
  won_count?: number;
  won_value?: number;
  lost_count?: number;
  lost_value?: number;
  active_proposals_count?: number;
  active_proposals_value?: number;
  overdue_count?: number;
  needs_followup?: number;
  ball_with_us_count?: number;
  waiting_on_client?: number;
}

interface ProposalStatsCardsProps {
  stats: ProposalStats | null;
  activeMetric: string | null;
  onMetricClick: (metric: string, status?: string) => void;
}

export function ProposalStatsCards({ stats, activeMetric, onMetricClick }: ProposalStatsCardsProps) {
  if (!stats) return null;

  // Calculate needs attention count (overdue + ball with us)
  const overdueCount = stats.overdue_count || 0;
  const ballWithUsCount = stats.ball_with_us_count || 0;
  const activeCount = stats.active_proposals_count || stats.total_proposals || 0;
  const waitingOnClient = stats.waiting_on_client || 0;
  const followupCount = stats.needs_followup || 0;
  const ballLikelyDefault = ballWithUsCount > 0 && activeCount > 0 && ballWithUsCount >= activeCount && waitingOnClient === 0;
  const attentionBase = overdueCount + (ballLikelyDefault ? 0 : ballWithUsCount);
  const needsAttentionCount = attentionBase > 0 ? attentionBase : followupCount;
  const attentionHint = ballLikelyDefault
    ? `${followupCount} follow-ups`
    : `${overdueCount} overdue · ${ballWithUsCount} our move`;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
      {/* Total Pipeline */}
      <Card
        className={cn(
          "border-slate-200 cursor-pointer transition-all hover:shadow-md",
          activeMetric === "pipeline" && "ring-2 ring-slate-400"
        )}
        onClick={() => onMetricClick("pipeline")}
      >
        <CardContent className="pt-4">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
            Total Pipeline
          </p>
          <p className="text-2xl font-bold text-slate-900 mt-1">
            {stats.all_proposals_total || stats.total_proposals}
          </p>
          <p className="text-sm font-semibold text-slate-600">
            {formatCurrency(stats.all_proposals_value || stats.total_pipeline_value)}
          </p>
        </CardContent>
      </Card>

      {/* Won (Contract Signed) */}
      <Card
        className={cn(
          "border-emerald-200 bg-emerald-50/50 cursor-pointer transition-all hover:shadow-md",
          activeMetric === "signed" && "ring-2 ring-emerald-400"
        )}
        onClick={() => onMetricClick("signed", "Contract Signed")}
      >
        <CardContent className="pt-4">
          <p className="text-xs font-medium text-emerald-600 uppercase tracking-wide flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3" /> Won
          </p>
          <p className="text-2xl font-bold text-emerald-700 mt-1">
            {stats.won_count || 0}
          </p>
          <p className="text-sm font-semibold text-emerald-600">
            {formatCurrency(stats.won_value || 0)}
          </p>
        </CardContent>
      </Card>

      {/* Lost/Declined */}
      <Card
        className={cn(
          "border-red-200 bg-red-50/50 cursor-pointer transition-all hover:shadow-md",
          activeMetric === "lost" && "ring-2 ring-red-400"
        )}
        onClick={() => onMetricClick("lost", "Lost")}
      >
        <CardContent className="pt-4">
          <p className="text-xs font-medium text-red-600 uppercase tracking-wide flex items-center gap-1">
            <XCircle className="h-3 w-3" /> Lost
          </p>
          <p className="text-2xl font-bold text-red-700 mt-1">
            {stats.lost_count || 0}
          </p>
          <p className="text-sm font-semibold text-red-600">
            {formatCurrency(stats.lost_value || 0)}
          </p>
        </CardContent>
      </Card>

      {/* Needs Attention */}
      <Card
        className={cn(
          "border-amber-200 bg-amber-50/50 cursor-pointer transition-all hover:shadow-md",
          activeMetric === "attention" && "ring-2 ring-amber-400"
        )}
        onClick={() => onMetricClick("attention")}
      >
        <CardContent className="pt-4">
          <p className="text-xs font-medium text-amber-600 uppercase tracking-wide flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" /> Needs Attention
          </p>
          <p className="text-2xl font-bold text-amber-700 mt-1">
            {needsAttentionCount}
          </p>
          <p className="text-xs text-amber-600">
            {attentionHint}
          </p>
        </CardContent>
      </Card>

      {/* Still Active */}
      <Card
        className={cn(
          "border-blue-200 bg-blue-50/50 cursor-pointer transition-all hover:shadow-md",
          activeMetric === "active" && "ring-2 ring-blue-400"
        )}
        onClick={() => onMetricClick("active")}
      >
        <CardContent className="pt-4">
          <p className="text-xs font-medium text-blue-600 uppercase tracking-wide flex items-center gap-1">
            <TrendingUp className="h-3 w-3" /> Active
          </p>
          <p className="text-2xl font-bold text-blue-700 mt-1">
            {stats.active_proposals_count}
          </p>
          <p className="text-sm font-semibold text-blue-600">
            {formatCurrency(stats.active_proposals_value)}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
