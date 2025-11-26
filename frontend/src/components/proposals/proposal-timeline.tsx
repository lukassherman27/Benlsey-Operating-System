"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import {
  Clock,
  CheckCircle2,
  Circle,
  XCircle,
  PauseCircle,
  AlertCircle,
} from "lucide-react";

interface TimelineEvent {
  history_id: number;
  old_status: string | null;
  new_status: string;
  status_date: string;
  changed_by: string;
  notes: string | null;
  source: string;
  created_at: string;
}

interface ProposalTimelineProps {
  projectCode: string;
  compact?: boolean;
}

const STATUS_CONFIG = {
  proposal: {
    label: "Proposal",
    color: "bg-blue-100 text-blue-800 border-blue-300",
    icon: Circle,
  },
  won: {
    label: "Won",
    color: "bg-green-100 text-green-800 border-green-300",
    icon: CheckCircle2,
  },
  lost: {
    label: "Lost",
    color: "bg-red-100 text-red-800 border-red-300",
    icon: XCircle,
  },
  on_hold: {
    label: "On Hold",
    color: "bg-yellow-100 text-yellow-800 border-yellow-300",
    icon: PauseCircle,
  },
  cancelled: {
    label: "Cancelled",
    color: "bg-gray-100 text-gray-800 border-gray-300",
    icon: XCircle,
  },
  pending: {
    label: "Pending",
    color: "bg-purple-100 text-purple-800 border-purple-300",
    icon: Clock,
  },
};

const getStatusConfig = (status: string) => {
  const normalized = status.toLowerCase().replace(/\s+/g, "_");
  return (
    STATUS_CONFIG[normalized as keyof typeof STATUS_CONFIG] || {
      label: status,
      color: "bg-slate-100 text-slate-800 border-slate-300",
      icon: AlertCircle,
    }
  );
};

const formatDate = (dateStr: string) => {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
};

export function ProposalTimeline({
  projectCode,
  compact = false,
}: ProposalTimelineProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["proposalHistory", projectCode],
    queryFn: async () => {
      const response = await fetch(
        `http://localhost:8000/api/proposals/${encodeURIComponent(
          projectCode
        )}/history`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch proposal history");
      }
      return response.json();
    },
  });

  if (isLoading) {
    return (
      <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
        <CardHeader>
          <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
            Status Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex gap-4">
                <Skeleton className="h-12 w-12 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-full" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50")}>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-red-800">
            <AlertCircle className="h-5 w-5" />
            <p className={ds.typography.body}>
              Failed to load timeline. Please try again.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const timeline = data?.history || [];
  const currentStatus = data?.current_status || "Unknown";

  if (timeline.length === 0) {
    return (
      <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
        <CardHeader>
          <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
            Status Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Clock className="h-12 w-12 text-slate-300 mx-auto mb-3" />
            <p className={cn(ds.typography.body, ds.textColors.secondary)}>
              No status changes recorded yet
            </p>
            <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mt-1")}>
              Current status: <strong>{currentStatus}</strong>
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
            Status Timeline
          </CardTitle>
          <Badge variant="outline" className={getStatusConfig(currentStatus).color}>
            Current: {getStatusConfig(currentStatus).label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-200" />

          {/* Timeline events */}
          <div className="space-y-6">
            {timeline.map((event: TimelineEvent, index: number) => {
              const statusConfig = getStatusConfig(event.new_status);
              const StatusIcon = statusConfig.icon;
              const isFirst = index === 0;

              return (
                <div key={event.history_id} className="relative flex gap-4">
                  {/* Icon */}
                  <div
                    className={cn(
                      "relative z-10 flex h-12 w-12 items-center justify-center rounded-full border-2",
                      statusConfig.color,
                      isFirst && "ring-4 ring-blue-100"
                    )}
                  >
                    <StatusIcon className="h-5 w-5" />
                  </div>

                  {/* Content */}
                  <div className="flex-1 pb-6">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4
                            className={cn(
                              ds.typography.bodyBold,
                              ds.textColors.primary
                            )}
                          >
                            {event.old_status ? (
                              <>
                                {getStatusConfig(event.old_status).label}
                                <span className="mx-2 text-slate-400">→</span>
                                {statusConfig.label}
                              </>
                            ) : (
                              <>Initial Status: {statusConfig.label}</>
                            )}
                          </h4>
                          {isFirst && (
                            <Badge
                              variant="outline"
                              className="bg-blue-50 text-blue-700 border-blue-200 text-xs"
                            >
                              Latest
                            </Badge>
                          )}
                        </div>

                        <div className="flex items-center gap-3 mb-2">
                          <p
                            className={cn(
                              ds.typography.caption,
                              ds.textColors.secondary
                            )}
                          >
                            <Clock className="inline h-3 w-3 mr-1" />
                            {formatDate(event.status_date)}
                          </p>
                          <span className={cn(ds.typography.caption, "text-slate-300")}>
                            •
                          </span>
                          <p
                            className={cn(
                              ds.typography.caption,
                              ds.textColors.secondary
                            )}
                          >
                            by {event.changed_by}
                          </p>
                          {event.source !== "manual" && (
                            <>
                              <span
                                className={cn(ds.typography.caption, "text-slate-300")}
                              >
                                •
                              </span>
                              <Badge
                                variant="outline"
                                className="text-xs bg-slate-50 text-slate-600 border-slate-200"
                              >
                                {event.source}
                              </Badge>
                            </>
                          )}
                        </div>

                        {event.notes && (
                          <p
                            className={cn(
                              ds.typography.body,
                              ds.textColors.secondary,
                              "mt-2 p-3 bg-slate-50 rounded-md border border-slate-200"
                            )}
                          >
                            {event.notes}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Summary */}
        <div
          className={cn(
            "mt-6 pt-4 border-t border-slate-200",
            "flex items-center justify-between"
          )}
        >
          <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
            {timeline.length} status {timeline.length === 1 ? "change" : "changes"}{" "}
            recorded
          </p>
          <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
            Last updated: {formatDate(timeline[0]?.created_at)}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
