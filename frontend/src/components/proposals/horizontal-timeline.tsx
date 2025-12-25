"use client";

import { cn } from "@/lib/utils";
import { Check, Circle, ArrowRight } from "lucide-react";

interface TimelineStage {
  id: string;
  label: string;
  date?: string | null;
}

interface HorizontalTimelineProps {
  currentStatus: string;
  firstContactDate?: string | null;
  proposalSentDate?: string | null;
  contractSignedDate?: string | null;
}

const STAGES: TimelineStage[] = [
  { id: "First Contact", label: "First Contact" },
  { id: "Proposal Prep", label: "Preparing" },
  { id: "Proposal Sent", label: "Sent" },
  { id: "Negotiation", label: "Negotiating" },
  { id: "Contract Signed", label: "Signed" },
];

const CLOSED_STATUSES = ["Lost", "Declined", "Dormant"];

export function HorizontalTimeline({
  currentStatus,
  firstContactDate,
  proposalSentDate,
  contractSignedDate,
}: HorizontalTimelineProps) {
  // Handle closed/lost status
  if (CLOSED_STATUSES.includes(currentStatus)) {
    return (
      <div className="flex items-center justify-center p-4 bg-slate-50 rounded-lg">
        <span className="text-sm text-slate-500">
          Proposal closed: {currentStatus}
        </span>
      </div>
    );
  }

  // Find current stage index
  const currentIndex = STAGES.findIndex(s => s.id === currentStatus);
  const effectiveIndex = currentIndex >= 0 ? currentIndex : 0;

  // Build stages with dates
  const stagesWithDates = STAGES.map((stage, idx) => {
    let date: string | null = null;
    if (stage.id === "First Contact" && firstContactDate) {
      date = firstContactDate;
    } else if (stage.id === "Proposal Sent" && proposalSentDate) {
      date = proposalSentDate;
    } else if (stage.id === "Contract Signed" && contractSignedDate) {
      date = contractSignedDate;
    }

    return {
      ...stage,
      date,
      isCompleted: idx < effectiveIndex,
      isCurrent: idx === effectiveIndex,
      isFuture: idx > effectiveIndex,
    };
  });

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="relative py-4 px-2 overflow-x-auto">
      <div className="flex items-center justify-between min-w-[400px]">
        {stagesWithDates.map((stage, idx) => (
          <div key={stage.id} className="flex items-center flex-1">
            {/* Stage Node */}
            <div className="flex flex-col items-center relative z-10">
              {/* Circle/Check */}
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all",
                  stage.isCompleted && "bg-emerald-500 border-emerald-500",
                  stage.isCurrent && "bg-blue-500 border-blue-500 ring-4 ring-blue-100 animate-pulse",
                  stage.isFuture && "bg-white border-slate-300"
                )}
              >
                {stage.isCompleted ? (
                  <Check className="h-4 w-4 text-white" />
                ) : stage.isCurrent ? (
                  <Circle className="h-3 w-3 text-white fill-white" />
                ) : (
                  <Circle className="h-3 w-3 text-slate-300" />
                )}
              </div>

              {/* Label */}
              <div className="mt-2 text-center">
                <p
                  className={cn(
                    "text-xs font-medium whitespace-nowrap",
                    stage.isCompleted && "text-emerald-700",
                    stage.isCurrent && "text-blue-700 font-semibold",
                    stage.isFuture && "text-slate-400"
                  )}
                >
                  {stage.label}
                </p>
                {stage.date && (
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    {formatDate(stage.date)}
                  </p>
                )}
              </div>
            </div>

            {/* Connector Line */}
            {idx < stagesWithDates.length - 1 && (
              <div className="flex-1 h-0.5 mx-1 relative">
                <div className="absolute inset-0 bg-slate-200" />
                <div
                  className={cn(
                    "absolute inset-y-0 left-0 bg-emerald-500 transition-all",
                    stage.isCompleted && "w-full",
                    stage.isCurrent && "w-0"
                  )}
                />
                {stage.isCurrent && (
                  <ArrowRight className="absolute right-0 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-300" />
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
