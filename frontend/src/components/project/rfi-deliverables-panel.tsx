"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FileQuestion,
  Package,
  Clock,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
} from "lucide-react";
import { formatDistanceToNow, format, isPast, isToday } from "date-fns";

interface RFI {
  rfi_id: number;
  rfi_number?: string;
  subject: string;
  status: "open" | "answered" | "closed";
  submitted_date: string;
  response_date?: string | null;
  days_open?: number;
}

interface Deliverable {
  deliverable_id: number;
  name: string;
  status: "pending" | "in_progress" | "delivered" | "approved";
  due_date: string | null;
  delivered_date?: string | null;
  responsible_party?: string;
}

interface RFIDeliverablesPanelProps {
  rfis: RFI[];
  deliverables: Deliverable[];
  projectCode: string;
  onMarkRFIAnswered?: (rfiId: number) => void;
  onMarkDelivered?: (deliverableId: number) => void;
  className?: string;
}

const rfiStatusConfig = {
  open: {
    label: "Open",
    color: "bg-amber-100 text-amber-800 border-amber-200",
    icon: Clock,
  },
  answered: {
    label: "Answered",
    color: "bg-blue-100 text-blue-800 border-blue-200",
    icon: CheckCircle2,
  },
  closed: {
    label: "Closed",
    color: "bg-slate-100 text-slate-600 border-slate-200",
    icon: CheckCircle2,
  },
};

const deliverableStatusConfig = {
  pending: {
    label: "Pending",
    color: "bg-slate-100 text-slate-600 border-slate-200",
    icon: Clock,
  },
  in_progress: {
    label: "In Progress",
    color: "bg-blue-100 text-blue-800 border-blue-200",
    icon: Clock,
  },
  delivered: {
    label: "Delivered",
    color: "bg-emerald-100 text-emerald-800 border-emerald-200",
    icon: CheckCircle2,
  },
  approved: {
    label: "Approved",
    color: "bg-emerald-100 text-emerald-800 border-emerald-200",
    icon: CheckCircle2,
  },
};

export function RFIDeliverablesPanel({
  rfis,
  deliverables,
  projectCode,
  onMarkRFIAnswered,
  onMarkDelivered,
  className,
}: RFIDeliverablesPanelProps) {
  // Filter to show only actionable items
  const openRfis = rfis.filter((r) => r.status === "open");
  const pendingDeliverables = deliverables.filter(
    (d) => d.status === "pending" || d.status === "in_progress"
  );

  // Sort deliverables by due date (soonest first)
  const sortedDeliverables = [...pendingDeliverables].sort((a, b) => {
    if (!a.due_date) return 1;
    if (!b.due_date) return -1;
    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
  });

  const formatDueDate = (dateStr: string | null) => {
    if (!dateStr) return "No date";
    try {
      const date = new Date(dateStr);
      if (isToday(date)) return "Today";
      if (isPast(date)) {
        return `${formatDistanceToNow(date)} overdue`;
      }
      return format(date, "MMM d");
    } catch {
      return dateStr;
    }
  };

  const isDueDateUrgent = (dateStr: string | null) => {
    if (!dateStr) return false;
    try {
      const date = new Date(dateStr);
      return isPast(date) || isToday(date);
    } catch {
      return false;
    }
  };

  if (openRfis.length === 0 && sortedDeliverables.length === 0) {
    return (
      <div
        className={cn(
          "rounded-xl border border-slate-200 bg-slate-50 p-6 text-center",
          className
        )}
      >
        <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto mb-2" />
        <p className="text-sm font-medium text-slate-700">All Clear</p>
        <p className="text-xs text-slate-500 mt-1">
          No pending RFIs or deliverables
        </p>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "rounded-xl border border-slate-200 bg-white overflow-hidden",
        className
      )}
    >
      {/* Two Column Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-200">
        {/* RFIs Column */}
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <FileQuestion className="h-4 w-4 text-amber-600" />
              <h4 className="font-semibold text-sm text-slate-800">
                Open RFIs
              </h4>
            </div>
            <Badge
              variant="outline"
              className={cn(
                "text-xs",
                openRfis.length > 0
                  ? "bg-amber-50 text-amber-700 border-amber-200"
                  : "bg-slate-50 text-slate-500"
              )}
            >
              {openRfis.length}
            </Badge>
          </div>

          {openRfis.length === 0 ? (
            <p className="text-xs text-slate-500 py-4 text-center">
              No open RFIs
            </p>
          ) : (
            <div className="space-y-2 max-h-[200px] overflow-y-auto">
              {openRfis.map((rfi) => {
                const config = rfiStatusConfig[rfi.status];
                const StatusIcon = config.icon;
                return (
                  <div
                    key={rfi.rfi_id}
                    className="p-2.5 rounded-lg border border-slate-100 hover:border-slate-200 transition-colors bg-slate-50/50"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          {rfi.rfi_number && (
                            <span className="text-xs font-mono text-slate-500">
                              {rfi.rfi_number}
                            </span>
                          )}
                          <span className="text-sm font-medium text-slate-700 truncate">
                            {rfi.subject}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge
                            variant="outline"
                            className={cn("text-xs h-5", config.color)}
                          >
                            <StatusIcon className="h-3 w-3 mr-1" />
                            {rfi.days_open != null
                              ? `${rfi.days_open}d open`
                              : config.label}
                          </Badge>
                        </div>
                      </div>
                      {onMarkRFIAnswered && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs shrink-0"
                          onClick={() => onMarkRFIAnswered(rfi.rfi_id)}
                        >
                          Answer
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Deliverables Column */}
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Package className="h-4 w-4 text-blue-600" />
              <h4 className="font-semibold text-sm text-slate-800">
                Deliverables
              </h4>
            </div>
            <Badge
              variant="outline"
              className={cn(
                "text-xs",
                sortedDeliverables.length > 0
                  ? "bg-blue-50 text-blue-700 border-blue-200"
                  : "bg-slate-50 text-slate-500"
              )}
            >
              {sortedDeliverables.length}
            </Badge>
          </div>

          {sortedDeliverables.length === 0 ? (
            <p className="text-xs text-slate-500 py-4 text-center">
              No pending deliverables
            </p>
          ) : (
            <div className="space-y-2 max-h-[200px] overflow-y-auto">
              {sortedDeliverables.map((del) => {
                const config = deliverableStatusConfig[del.status];
                const StatusIcon = config.icon;
                const isUrgent = isDueDateUrgent(del.due_date);
                return (
                  <div
                    key={del.deliverable_id}
                    className={cn(
                      "p-2.5 rounded-lg border transition-colors",
                      isUrgent
                        ? "border-amber-200 bg-amber-50/50"
                        : "border-slate-100 bg-slate-50/50 hover:border-slate-200"
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <span className="text-sm font-medium text-slate-700 line-clamp-1">
                          {del.name}
                        </span>
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          <Badge
                            variant="outline"
                            className={cn("text-xs h-5", config.color)}
                          >
                            <StatusIcon className="h-3 w-3 mr-1" />
                            {config.label}
                          </Badge>
                          {del.due_date && (
                            <span
                              className={cn(
                                "text-xs flex items-center gap-1",
                                isUrgent
                                  ? "text-amber-700 font-medium"
                                  : "text-slate-500"
                              )}
                            >
                              {isUrgent && (
                                <AlertCircle className="h-3 w-3" />
                              )}
                              {formatDueDate(del.due_date)}
                            </span>
                          )}
                        </div>
                      </div>
                      {onMarkDelivered &&
                        (del.status === "pending" ||
                          del.status === "in_progress") && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 text-xs shrink-0"
                            onClick={() => onMarkDelivered(del.deliverable_id)}
                          >
                            Deliver
                          </Button>
                        )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Footer - View All Links */}
      <div className="border-t border-slate-100 px-4 py-2 bg-slate-50/50 flex justify-between">
        <Button
          variant="ghost"
          size="sm"
          className="text-xs h-7 text-slate-600"
          asChild
        >
          <a href={`/projects/${encodeURIComponent(projectCode)}#rfis`}>
            View all RFIs
            <ChevronRight className="h-3 w-3 ml-1" />
          </a>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="text-xs h-7 text-slate-600"
          asChild
        >
          <a href={`/projects/${encodeURIComponent(projectCode)}#deliverables`}>
            View all deliverables
            <ChevronRight className="h-3 w-3 ml-1" />
          </a>
        </Button>
      </div>
    </div>
  );
}
