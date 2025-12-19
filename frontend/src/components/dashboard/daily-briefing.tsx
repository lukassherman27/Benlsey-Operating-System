"use client";

import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Calendar,
  FileText,
  Target,
  TrendingUp,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";
import { format } from "date-fns";
import { ProposalLink, ProjectLink } from "@/components/cross-link/entity-link";

interface DailyBriefingProps {
  userName?: string;
  className?: string;
}

type HealthStatus = "critical" | "needs_attention" | "healthy";

const healthConfig: Record<
  HealthStatus,
  {
    bgGradient: string;
    borderColor: string;
    textColor: string;
    icon: typeof AlertTriangle;
    iconColor: string;
    greeting: string;
  }
> = {
  critical: {
    bgGradient: "from-red-50 to-orange-50",
    borderColor: "border-red-200",
    textColor: "text-red-900",
    icon: AlertTriangle,
    iconColor: "text-red-600",
    greeting: "needs your attention today",
  },
  needs_attention: {
    bgGradient: "from-amber-50 to-yellow-50",
    borderColor: "border-amber-200",
    textColor: "text-amber-900",
    icon: Clock,
    iconColor: "text-amber-600",
    greeting: "has a few things to review",
  },
  healthy: {
    bgGradient: "from-emerald-50 to-teal-50",
    borderColor: "border-emerald-200",
    textColor: "text-emerald-900",
    icon: CheckCircle2,
    iconColor: "text-emerald-600",
    greeting: "is running smoothly",
  },
};

export function DailyBriefing({ userName = "Bill", className }: DailyBriefingProps) {
  const { data: briefing, isLoading, error } = useQuery({
    queryKey: ["daily-briefing"],
    queryFn: () => api.getDailyBriefing(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  if (isLoading) {
    return (
      <div className={cn("rounded-xl border bg-white p-6", className)}>
        <Skeleton className="h-6 w-48 mb-4" />
        <Skeleton className="h-4 w-64 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
      </div>
    );
  }

  if (error || !briefing) {
    return null; // Silently fail - dashboard still works without briefing
  }

  // Determine health status from briefing data
  const urgentCount = briefing.urgent?.length ?? 0;
  const attentionCount = briefing.needs_attention?.length ?? 0;

  let healthStatus: HealthStatus = "healthy";
  if (urgentCount > 0) {
    healthStatus = "critical";
  } else if (attentionCount > 0) {
    healthStatus = "needs_attention";
  }

  const config = healthConfig[healthStatus];
  const StatusIcon = config.icon;
  const today = format(new Date(), "EEEE, MMMM d");

  // Calculate total action items
  const totalActions = urgentCount + attentionCount;

  return (
    <div
      className={cn(
        "rounded-xl border-2 overflow-hidden",
        `bg-gradient-to-br ${config.bgGradient}`,
        config.borderColor,
        className
      )}
    >
      {/* Header */}
      <div className="p-5 pb-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-slate-500 mb-1">{today}</p>
            <h2 className="text-xl font-bold text-slate-800">
              Good morning, {userName}.{" "}
              <span className={config.textColor}>
                {totalActions > 0
                  ? `${totalActions} item${totalActions === 1 ? "" : "s"} need${totalActions === 1 ? "s" : ""} your attention.`
                  : "Everything looks good."}
              </span>
            </h2>
            {briefing.business_health?.summary && (
              <p className="text-sm text-slate-600 mt-2">
                {briefing.business_health.summary}
              </p>
            )}
          </div>
          <div className={cn("p-2 rounded-lg", config.borderColor, "bg-white/50")}>
            <StatusIcon className={cn("h-6 w-6", config.iconColor)} />
          </div>
        </div>
      </div>

      {/* Action Items */}
      {totalActions > 0 && (
        <div className="px-5 pb-4 space-y-2">
          {/* Urgent Items */}
          {briefing.urgent?.map((item, index) => (
            <div
              key={`urgent-${index}`}
              className="flex items-center gap-3 p-3 rounded-lg bg-white border border-red-200 shadow-sm"
            >
              <div className="p-1.5 rounded-lg bg-red-100">
                <AlertTriangle className="h-4 w-4 text-red-600" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Badge variant="destructive" className="text-xs">
                    Urgent
                  </Badge>
                  {item.project_code && item.project_name && (
                    <ProposalLink
                      projectCode={item.project_code}
                      label={item.project_name}
                      showIcon={false}
                      className="text-xs"
                    />
                  )}
                </div>
                <p className="text-sm font-medium text-slate-800 mt-0.5">
                  {item.action}
                </p>
                {item.context && (
                  <p className="text-xs text-slate-500">{item.context}</p>
                )}
              </div>
              <Button size="sm" variant="ghost" className="shrink-0">
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          ))}

          {/* Attention Items */}
          {briefing.needs_attention?.map((item, index) => (
            <div
              key={`attention-${index}`}
              className="flex items-center gap-3 p-3 rounded-lg bg-white/80 border border-amber-200"
            >
              <div className="p-1.5 rounded-lg bg-amber-100">
                <Clock className="h-4 w-4 text-amber-600" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className="text-xs bg-amber-50 text-amber-700 border-amber-200"
                  >
                    {item.type || "Attention"}
                  </Badge>
                  {item.project_code && item.project_name && (
                    <ProposalLink
                      projectCode={item.project_code}
                      label={item.project_name}
                      showIcon={false}
                      className="text-xs"
                    />
                  )}
                </div>
                <p className="text-sm font-medium text-slate-700 mt-0.5">
                  {item.action}
                </p>
                {item.context && (
                  <p className="text-xs text-slate-500">{item.context}</p>
                )}
              </div>
              <Button size="sm" variant="ghost" className="shrink-0">
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Stats Footer */}
      <div className="px-5 py-3 bg-white/50 border-t border-slate-200/50 flex flex-wrap items-center gap-4 text-xs text-slate-600">
        <div className="flex items-center gap-1.5">
          <Calendar className="h-3.5 w-3.5" />
          <span>Today: 2 meetings | 4 tasks</span>
        </div>
        {briefing.insights && briefing.insights.length > 0 && (
          <div className="flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-purple-500" />
            <span className="text-purple-700">
              {briefing.insights[0]}
            </span>
          </div>
        )}
      </div>

      {/* Wins Section (if any) */}
      {briefing.wins && briefing.wins.length > 0 && (
        <div className="px-5 py-3 bg-emerald-50 border-t border-emerald-200">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-emerald-600" />
            <span className="text-sm font-medium text-emerald-800">
              Recent Win:
            </span>
            <span className="text-sm text-emerald-700">
              {briefing.wins[0].title || briefing.wins[0].project_name}
              {briefing.wins[0].amount_usd && (
                <span className="font-semibold">
                  {" "}
                  (${(briefing.wins[0].amount_usd / 1000000).toFixed(1)}M)
                </span>
              )}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
