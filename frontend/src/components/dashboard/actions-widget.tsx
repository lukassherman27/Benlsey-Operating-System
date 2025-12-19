"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle,
  Clock,
  FileText,
  Mail,
  MessageSquare,
  RefreshCw,
  Send,
  Target,
  Zap,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";

const typeConfig: Record<string, { icon: typeof Zap; label: string; color: string }> = {
  proposal_action: { icon: Target, label: "Ball with us", color: "text-amber-600" },
  follow_up: { icon: Clock, label: "Follow up", color: "text-blue-600" },
  email_action: { icon: Mail, label: "Email", color: "text-purple-600" },
  rfi: { icon: MessageSquare, label: "RFI", color: "text-cyan-600" },
  commitment: { icon: CheckCircle, label: "Commitment", color: "text-emerald-600" },
  task: { icon: FileText, label: "Task", color: "text-slate-600" },
  proposal_send: { icon: Send, label: "Send proposal", color: "text-indigo-600" },
};

const urgencyStyles: Record<string, string> = {
  critical: "bg-red-100 text-red-800 border-red-200",
  high: "bg-amber-100 text-amber-800 border-amber-200",
  medium: "bg-blue-100 text-blue-800 border-blue-200",
  low: "bg-slate-100 text-slate-700 border-slate-200",
};

interface ActionsWidgetProps {
  limit?: number;
  showHeader?: boolean;
  compact?: boolean;
}

export function ActionsWidget({ limit = 10, showHeader = true, compact = false }: ActionsWidgetProps) {
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ["dashboard-actions"],
    queryFn: api.getDashboardActions,
    refetchInterval: 1000 * 60 * 5, // Refresh every 5 minutes
    staleTime: 1000 * 60 * 2,
  });

  if (isLoading) {
    return (
      <Card>
        {showHeader && (
          <CardHeader className="pb-2">
            <Skeleton className="h-6 w-48" />
          </CardHeader>
        )}
        <CardContent className={compact ? "pt-2" : ""}>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !data?.success) {
    return (
      <Card className="border-amber-200 bg-amber-50">
        {showHeader && (
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              What Needs Attention
            </CardTitle>
          </CardHeader>
        )}
        <CardContent>
          <p className="text-sm text-amber-700">Unable to load action items</p>
        </CardContent>
      </Card>
    );
  }

  const actions = data.actions.slice(0, limit);
  const { summary } = data;

  return (
    <Card className="border-slate-200">
      {showHeader && (
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-lg">
              <Zap className="h-5 w-5 text-amber-500" />
              What Needs Attention
              {summary.critical > 0 && (
                <Badge className="bg-red-500 text-white ml-2">
                  {summary.critical} critical
                </Badge>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
              className="text-slate-400 hover:text-slate-600"
            >
              <RefreshCw className={cn("h-4 w-4", isFetching && "animate-spin")} />
            </Button>
          </CardTitle>
          {/* Summary badges */}
          <div className="flex flex-wrap gap-2 mt-2">
            {Object.entries(summary.by_type).map(([type, count]) => {
              const config = typeConfig[type];
              if (!config) return null;
              const Icon = config.icon;
              return (
                <Badge key={type} variant="outline" className="text-xs gap-1">
                  <Icon className={cn("h-3 w-3", config.color)} />
                  {count} {config.label}
                </Badge>
              );
            })}
          </div>
        </CardHeader>
      )}
      <CardContent className={compact ? "pt-2" : ""}>
        {actions.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="mx-auto h-12 w-12 text-emerald-400 mb-3" />
            <p className="text-slate-600 font-medium">All caught up!</p>
            <p className="text-sm text-slate-400">No urgent items need your attention</p>
          </div>
        ) : (
          <div className="space-y-2">
            {actions.map((action, i) => {
              const config = typeConfig[action.type] || { icon: AlertTriangle, label: action.type, color: "text-slate-600" };
              const Icon = config.icon;

              return (
                <div
                  key={`${action.type}-${action.project_code}-${i}`}
                  className={cn(
                    "p-3 rounded-lg border transition-all hover:shadow-md",
                    action.urgency === "critical" && "border-red-200 bg-red-50/50",
                    action.urgency === "high" && "border-amber-200 bg-amber-50/30",
                    action.urgency === "medium" && "border-slate-200 bg-white",
                    action.urgency === "low" && "border-slate-100 bg-slate-50/50"
                  )}
                >
                  <div className="flex items-start gap-3">
                    {/* Icon */}
                    <div className={cn(
                      "p-2 rounded-lg",
                      action.urgency === "critical" ? "bg-red-100" :
                      action.urgency === "high" ? "bg-amber-100" :
                      "bg-slate-100"
                    )}>
                      <Icon className={cn("h-4 w-4", config.color)} />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge className={cn("text-xs", urgencyStyles[action.urgency])}>
                          {action.urgency}
                        </Badge>
                        <span className="text-xs text-slate-400">{config.label}</span>
                        {action.days_waiting && action.days_waiting > 0 && (
                          <span className="text-xs text-slate-400">
                            • {action.days_waiting}d waiting
                          </span>
                        )}
                        {action.days_overdue && action.days_overdue > 0 && (
                          <span className="text-xs text-red-500 font-medium">
                            • {action.days_overdue}d overdue
                          </span>
                        )}
                      </div>

                      <p className="font-medium text-sm text-slate-900 mt-1 truncate">
                        {action.project_name || action.title}
                      </p>

                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">
                        {action.description}
                      </p>

                      {/* Action row */}
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs font-medium text-slate-600 flex items-center gap-1">
                          <ArrowRight className="h-3 w-3" />
                          {action.action}
                        </span>
                        {action.link && (
                          <Link href={action.link}>
                            <Button variant="ghost" size="sm" className="h-6 px-2 text-xs gap-1 text-slate-500 hover:text-slate-700">
                              View
                              <ChevronRight className="h-3 w-3" />
                            </Button>
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Show more link */}
        {data.actions.length > limit && (
          <div className="mt-4 pt-3 border-t text-center">
            <Button variant="outline" size="sm" asChild>
              <Link href="/my-day">
                View all {data.actions.length} items
                <ExternalLink className="h-3 w-3 ml-1" />
              </Link>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
