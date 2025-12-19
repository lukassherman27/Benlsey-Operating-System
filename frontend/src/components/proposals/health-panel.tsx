"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileQuestion,
} from "lucide-react";

interface HealthPanelProps {
  healthScore: number;
  winProbability?: number | null;
  winProbabilityChange?: number | null;
  risks?: string[];
  className?: string;
}

export function HealthPanel({
  healthScore,
  winProbability,
  winProbabilityChange,
  risks = [],
  className,
}: HealthPanelProps) {
  // Health score thresholds
  const getHealthConfig = (score: number) => {
    if (score >= 80) {
      return {
        label: "Excellent",
        color: "text-emerald-600",
        bgColor: "bg-emerald-50",
        borderColor: "border-emerald-200",
        barColor: "bg-emerald-500",
      };
    }
    if (score >= 60) {
      return {
        label: "Good",
        color: "text-emerald-600",
        bgColor: "bg-emerald-50/50",
        borderColor: "border-emerald-200",
        barColor: "bg-emerald-400",
      };
    }
    if (score >= 40) {
      return {
        label: "Fair",
        color: "text-amber-600",
        bgColor: "bg-amber-50",
        borderColor: "border-amber-200",
        barColor: "bg-amber-500",
      };
    }
    return {
      label: "At Risk",
      color: "text-red-600",
      bgColor: "bg-red-50",
      borderColor: "border-red-200",
      barColor: "bg-red-500",
    };
  };

  const healthConfig = getHealthConfig(healthScore);

  // Win probability trend icon
  const TrendIcon =
    (winProbabilityChange ?? 0) > 0
      ? TrendingUp
      : (winProbabilityChange ?? 0) < 0
      ? TrendingDown
      : Minus;

  const trendColor =
    (winProbabilityChange ?? 0) > 0
      ? "text-emerald-600"
      : (winProbabilityChange ?? 0) < 0
      ? "text-red-600"
      : "text-slate-400";

  return (
    <div
      className={cn(
        "rounded-xl border p-4",
        healthConfig.bgColor,
        healthConfig.borderColor,
        className
      )}
    >
      <div className="space-y-4">
        {/* Health Score */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
              Health Score
            </span>
            <Badge
              variant="outline"
              className={cn("text-xs", healthConfig.color)}
            >
              {healthConfig.label}
            </Badge>
          </div>

          {/* Progress Bar */}
          <div className="relative">
            <div className="h-3 bg-slate-200 rounded-full overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-500",
                  healthConfig.barColor
                )}
                style={{ width: `${Math.min(100, Math.max(0, healthScore))}%` }}
              />
            </div>
            <div className="flex items-center justify-between mt-1">
              <span
                className={cn("text-2xl font-bold", healthConfig.color)}
              >
                {healthScore}
              </span>
              <span className="text-xs text-slate-400">/100</span>
            </div>
          </div>
        </div>

        {/* Win Probability (if available) */}
        {winProbability !== null && winProbability !== undefined && (
          <div className="pt-3 border-t border-slate-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Win Probability
              </span>
              <div className="flex items-center gap-1">
                <span className="text-lg font-bold text-slate-700">
                  {winProbability}%
                </span>
                {winProbabilityChange !== null &&
                  winProbabilityChange !== undefined && (
                    <div
                      className={cn(
                        "flex items-center text-xs font-medium",
                        trendColor
                      )}
                    >
                      <TrendIcon className="h-3 w-3" />
                      {winProbabilityChange > 0 ? "+" : ""}
                      {winProbabilityChange}%
                    </div>
                  )}
              </div>
            </div>
            {winProbabilityChange !== null &&
              winProbabilityChange !== undefined && (
                <p className="text-xs text-slate-400 mt-1">vs last week</p>
              )}
          </div>
        )}

        {/* Risks */}
        {risks.length > 0 && (
          <div className="pt-3 border-t border-slate-200">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500 mb-2">
              Risks
            </p>
            <ul className="space-y-1.5">
              {risks.map((risk, index) => (
                <li
                  key={index}
                  className="flex items-start gap-2 text-sm text-slate-600"
                >
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-500 mt-0.5 shrink-0" />
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* No Risks - Healthy */}
        {risks.length === 0 && healthScore >= 70 && (
          <div className="pt-3 border-t border-slate-200">
            <div className="flex items-center gap-2 text-sm text-emerald-600">
              <CheckCircle2 className="h-4 w-4" />
              <span>No active risks identified</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Helper function to calculate risks from proposal data
export function calculateRisks(proposal: {
  days_since_contact?: number | null;
  ball_in_court?: string | null;
  status?: string | null;
  next_action?: string | null;
  waiting_for?: string | null;
}): string[] {
  const risks: string[] = [];

  // Days since contact risks
  const days = proposal.days_since_contact ?? 0;
  if (days > 30) {
    risks.push(`${days} days since last contact (critical)`);
  } else if (days > 14) {
    risks.push(`${days} days since last contact`);
  }

  // Ball in court risks
  if (proposal.ball_in_court === "us" && days > 7) {
    risks.push("Ball in our court for over a week");
  }

  // Status-based risks
  if (proposal.status === "stalled" || proposal.status === "at_risk") {
    risks.push("Proposal marked as " + proposal.status);
  }

  // No next action
  if (!proposal.next_action && !proposal.waiting_for) {
    risks.push("No clear next action defined");
  }

  return risks;
}

// Helper function to calculate health score from proposal data
export function calculateHealthScore(proposal: {
  days_since_contact?: number | null;
  ball_in_court?: string | null;
  status?: string | null;
  email_count?: number;
}): number {
  let score = 100;

  // Days since contact penalty
  const days = proposal.days_since_contact ?? 0;
  if (days > 30) score -= 40;
  else if (days > 14) score -= 20;
  else if (days > 7) score -= 10;

  // Ball in court penalty
  if (proposal.ball_in_court === "us" && days > 7) {
    score -= 15;
  }

  // Status penalty
  if (proposal.status === "stalled") score -= 20;
  if (proposal.status === "at_risk") score -= 30;
  if (proposal.status === "lost") score -= 50;

  // Low communication penalty
  if ((proposal.email_count ?? 0) < 3) {
    score -= 10;
  }

  return Math.max(0, Math.min(100, score));
}
