"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import Link from "next/link";
import {
  AlertTriangle,
  ChevronRight,
  Mail,
  FileText,
  HelpCircle,
  Phone,
  Calendar,
  ExternalLink,
} from "lucide-react";

interface ActionItem {
  type: string;
  urgency: "critical" | "high" | "medium" | "low";
  project_code?: string;
  project_name?: string;
  title: string;
  description: string;
  days_waiting?: number;
  days_overdue?: number;
  action?: string;
  due_date?: string;
  link?: string;
  from?: string;
}

interface ActionsResponse {
  success: boolean;
  actions: ActionItem[];
  summary: {
    total: number;
    critical: number;
    high: number;
    by_type: Record<string, number>;
  };
}

const urgencyStyles = {
  critical: "border-red-300 bg-red-50",
  high: "border-amber-300 bg-amber-50",
  medium: "border-blue-200 bg-blue-50",
  low: "border-slate-200 bg-slate-50",
};

const urgencyBadgeStyles = {
  critical: "bg-red-100 text-red-800 border-red-200",
  high: "bg-amber-100 text-amber-800 border-amber-200",
  medium: "bg-blue-100 text-blue-800 border-blue-200",
  low: "bg-slate-100 text-slate-600 border-slate-200",
};

const typeIcons: Record<string, React.ReactNode> = {
  proposal_action: <FileText className="h-4 w-4" />,
  follow_up: <Phone className="h-4 w-4" />,
  email_action: <Mail className="h-4 w-4" />,
  rfi: <HelpCircle className="h-4 w-4" />,
  commitment: <Calendar className="h-4 w-4" />,
  task: <FileText className="h-4 w-4" />,
  proposal_send: <FileText className="h-4 w-4" />,
};

function ActionItemRow({ item }: { item: ActionItem }) {
  const Icon = typeIcons[item.type] || <FileText className="h-4 w-4" />;

  return (
    <div
      className={cn(
        "p-4 rounded-lg border transition-all hover:shadow-sm",
        urgencyStyles[item.urgency]
      )}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div
          className={cn(
            "p-2 rounded-full flex-shrink-0",
            item.urgency === "critical"
              ? "bg-red-100 text-red-600"
              : item.urgency === "high"
                ? "bg-amber-100 text-amber-600"
                : "bg-blue-100 text-blue-600"
          )}
        >
          {item.urgency === "critical" || item.urgency === "high" ? (
            <AlertTriangle className="h-4 w-4" />
          ) : (
            Icon
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="font-medium text-slate-900 truncate">{item.title}</p>
              {item.project_name && (
                <p className="text-sm text-slate-600 truncate">
                  {item.project_code} - {item.project_name}
                </p>
              )}
            </div>
            <Badge
              variant="outline"
              className={cn("flex-shrink-0 text-xs", urgencyBadgeStyles[item.urgency])}
            >
              {item.urgency === "critical"
                ? "Critical"
                : item.urgency === "high"
                  ? "Urgent"
                  : "Action"}
            </Badge>
          </div>

          <p className="text-sm text-slate-500 mt-1 line-clamp-2">{item.description}</p>

          {/* Days indicator */}
          {(item.days_waiting || item.days_overdue) && (
            <p className="text-xs text-slate-400 mt-1">
              {item.days_overdue
                ? `${item.days_overdue} days overdue`
                : item.days_waiting
                  ? `${item.days_waiting} days waiting`
                  : ""}
            </p>
          )}

          {/* Action button */}
          <div className="flex items-center gap-2 mt-3">
            {item.link ? (
              <Link href={item.link}>
                <Button size="sm" variant="outline" className="h-8 text-xs gap-1.5">
                  {item.type === "follow_up" || item.type === "proposal_action" ? (
                    <>
                      <Phone className="h-3 w-3" />
                      Follow Up
                    </>
                  ) : item.type === "email_action" ? (
                    <>
                      <Mail className="h-3 w-3" />
                      View Email
                    </>
                  ) : (
                    <>
                      <ExternalLink className="h-3 w-3" />
                      View
                    </>
                  )}
                </Button>
              </Link>
            ) : (
              <Button size="sm" variant="outline" className="h-8 text-xs" disabled>
                {item.action || "Action Required"}
              </Button>
            )}

            {item.link && (
              <Link href={item.link}>
                <Button size="sm" variant="ghost" className="h-8 text-xs gap-1">
                  Details <ChevronRight className="h-3 w-3" />
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

interface NeedsAttentionWidgetProps {
  maxItems?: number;
  className?: string;
}

export function NeedsAttentionWidget({ maxItems = 10, className }: NeedsAttentionWidgetProps) {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["dashboard-actions"],
    queryFn: () => api.getDashboardActions() as Promise<ActionsResponse>,
    staleTime: 1000 * 60 * 2, // 2 minutes
    refetchInterval: 1000 * 60 * 5, // Refetch every 5 minutes
  });

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Needs Your Attention
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Needs Your Attention
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-slate-500">
            <p className="text-sm">Unable to load items</p>
            <Button variant="ghost" size="sm" className="mt-2" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const actions = data?.actions || [];
  const displayActions = actions.slice(0, maxItems);
  const summary = data?.summary;

  if (actions.length === 0) {
    return (
      <Card className={cn("border-emerald-200 bg-emerald-50/30", className)}>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2 text-emerald-700">
            <AlertTriangle className="h-5 w-5" />
            All Caught Up!
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-emerald-600">No urgent items need your attention.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Needs Your Attention
          </CardTitle>
          <div className="flex items-center gap-2">
            {summary?.critical && summary.critical > 0 && (
              <Badge variant="outline" className="bg-red-100 text-red-800 border-red-200">
                {summary.critical} Critical
              </Badge>
            )}
            {summary?.high && summary.high > 0 && (
              <Badge variant="outline" className="bg-amber-100 text-amber-800 border-amber-200">
                {summary.high} Urgent
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {displayActions.map((item, idx) => (
          <ActionItemRow key={`${item.type}-${item.project_code || idx}`} item={item} />
        ))}

        {actions.length > maxItems && (
          <div className="text-center pt-2">
            <Link href="/tracker?filter=needs-attention">
              <Button variant="ghost" size="sm" className="text-xs">
                View all {actions.length} items <ChevronRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
