"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Clock,
  Mail,
  Calendar,
  RefreshCw,
  AlertCircle,
} from "lucide-react";

interface BallInCourtProps {
  ballInCourt: "us" | "them" | "mutual" | "on_hold" | string;
  waitingFor?: string | null;
  daysSinceContact?: number | null;
  lastContactDate?: string | null;
  onDraftFollowUp?: () => void;
  onScheduleMeeting?: () => void;
  onUpdateStatus?: () => void;
  className?: string;
}

export function BallInCourt({
  ballInCourt,
  waitingFor,
  daysSinceContact,
  lastContactDate,
  onDraftFollowUp,
  onScheduleMeeting,
  onUpdateStatus,
  className,
}: BallInCourtProps) {
  const normalized = (ballInCourt || "mutual").toLowerCase();

  const config: Record<
    string,
    {
      label: string;
      sublabel: string;
      bgColor: string;
      textColor: string;
      borderColor: string;
      iconBg: string;
    }
  > = {
    us: {
      label: "OUR MOVE",
      sublabel: "Action required",
      bgColor: "bg-amber-50",
      textColor: "text-amber-900",
      borderColor: "border-amber-200",
      iconBg: "bg-amber-100",
    },
    them: {
      label: "THEIR MOVE",
      sublabel: "Awaiting response",
      bgColor: "bg-blue-50",
      textColor: "text-blue-900",
      borderColor: "border-blue-200",
      iconBg: "bg-blue-100",
    },
    mutual: {
      label: "IN PROGRESS",
      sublabel: "Collaborative stage",
      bgColor: "bg-slate-50",
      textColor: "text-slate-700",
      borderColor: "border-slate-200",
      iconBg: "bg-slate-100",
    },
    on_hold: {
      label: "ON HOLD",
      sublabel: "Paused",
      bgColor: "bg-slate-50",
      textColor: "text-slate-500",
      borderColor: "border-slate-200",
      iconBg: "bg-slate-100",
    },
  };

  const current = config[normalized] || config.mutual;
  const isUrgent = normalized === "us" && (daysSinceContact ?? 0) > 7;

  // Format days since contact
  const formatDaysSince = (days: number | null | undefined) => {
    if (days === null || days === undefined) return "Unknown";
    if (days === 0) return "Today";
    if (days === 1) return "Yesterday";
    return `${days} days ago`;
  };

  // Format date
  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return "";
    try {
      return new Date(dateStr).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });
    } catch {
      return "";
    }
  };

  return (
    <div
      className={cn(
        "rounded-xl border-2 p-5",
        current.bgColor,
        current.borderColor,
        isUrgent && "ring-2 ring-amber-400 ring-offset-2",
        className
      )}
    >
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        {/* Left: Status */}
        <div className="flex items-start gap-4">
          {/* Big Status Indicator */}
          <div
            className={cn(
              "flex-shrink-0 w-20 h-20 rounded-xl flex flex-col items-center justify-center",
              current.iconBg,
              current.textColor
            )}
          >
            <span className="text-2xl font-black leading-tight">
              {normalized === "us"
                ? "US"
                : normalized === "them"
                ? "THEM"
                : normalized === "on_hold"
                ? "HOLD"
                : "..."}
            </span>
          </div>

          {/* Status Details */}
          <div className="space-y-2">
            <div>
              <p className="text-xs uppercase tracking-wider text-slate-500 mb-1">
                Ball in Court
              </p>
              <h3 className={cn("text-xl font-bold", current.textColor)}>
                {current.label}
              </h3>
              <p className="text-sm text-slate-600">{current.sublabel}</p>
            </div>

            {/* Waiting For */}
            {waitingFor && (
              <div className="flex items-start gap-2 text-sm">
                <Clock className="h-4 w-4 text-slate-400 mt-0.5 shrink-0" />
                <div>
                  <span className="text-slate-500">Waiting for: </span>
                  <span className="text-slate-700">{waitingFor}</span>
                </div>
              </div>
            )}

            {/* Time Since Contact */}
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-slate-400" />
                <span className={cn(
                  isUrgent ? "text-amber-700 font-medium" : "text-slate-600"
                )}>
                  Since: {formatDaysSince(daysSinceContact)}
                </span>
                {lastContactDate && (
                  <span className="text-slate-400">
                    ({formatDate(lastContactDate)})
                  </span>
                )}
              </div>
              {isUrgent && (
                <Badge variant="destructive" className="text-xs">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  Overdue
                </Badge>
              )}
            </div>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex flex-wrap gap-2 md:flex-col">
          {normalized === "us" && (
            <>
              <Button
                size="sm"
                variant="default"
                className="bg-amber-600 hover:bg-amber-700"
                onClick={onDraftFollowUp}
              >
                <Mail className="h-4 w-4 mr-2" />
                Draft Follow-up
              </Button>
              <Button size="sm" variant="outline" onClick={onScheduleMeeting}>
                <Calendar className="h-4 w-4 mr-2" />
                Schedule Meeting
              </Button>
            </>
          )}
          {normalized === "them" && (
            <Button size="sm" variant="outline" onClick={onUpdateStatus}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Update Status
            </Button>
          )}
          {(normalized === "mutual" || normalized === "on_hold") && (
            <Button size="sm" variant="outline" onClick={onUpdateStatus}>
              <ArrowRight className="h-4 w-4 mr-2" />
              Update Status
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
