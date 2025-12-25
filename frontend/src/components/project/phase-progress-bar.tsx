"use client";

import { cn } from "@/lib/utils";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// Standard Bensley design phases
const STANDARD_PHASES = [
  { key: "mobilization", label: "Mob", fullName: "Mobilization" },
  { key: "concept", label: "Concept", fullName: "Conceptual Design" },
  { key: "schematic", label: "SD", fullName: "Schematic Design" },
  { key: "dd", label: "DD", fullName: "Design Development" },
  { key: "cd", label: "CD", fullName: "Construction Documents" },
  { key: "ca", label: "CA", fullName: "Construction Administration" },
];

interface PhaseData {
  phase_name: string;
  status: "pending" | "in_progress" | "completed";
  phase_fee_usd?: number;
  invoiced_amount_usd?: number;
  paid_amount_usd?: number;
  start_date?: string;
  expected_completion_date?: string;
  actual_completion_date?: string;
}

interface PhaseProgressBarProps {
  phases: PhaseData[];
  discipline?: string;
  compact?: boolean;
  className?: string;
}

// Normalize phase name to standard key
function normalizePhaseKey(phaseName: string): string {
  const lower = phaseName.toLowerCase();

  if (lower.includes("mobil")) return "mobilization";
  if (lower.includes("concept")) return "concept";
  if (lower.includes("schematic") || lower === "sd") return "schematic";
  if (lower.includes("design dev") || lower === "dd") return "dd";
  if (lower.includes("construction doc") || lower === "cd") return "cd";
  if (lower.includes("construction admin") || lower.includes("observation") || lower === "ca") return "ca";

  return lower;
}

// Get phase status from data
function getPhaseStatus(
  phaseKey: string,
  phases: PhaseData[]
): { status: "pending" | "in_progress" | "completed"; data?: PhaseData } {
  const matchingPhase = phases.find(
    (p) => normalizePhaseKey(p.phase_name) === phaseKey
  );

  if (!matchingPhase) {
    return { status: "pending" };
  }

  return { status: matchingPhase.status, data: matchingPhase };
}

// Calculate percentage complete for a phase
function calculatePhaseProgress(phase: PhaseData): number {
  if (phase.status === "completed") return 100;
  if (phase.status === "pending") return 0;

  // For in_progress, estimate based on invoicing if available
  if (phase.phase_fee_usd && phase.invoiced_amount_usd) {
    return Math.min(
      Math.round((phase.invoiced_amount_usd / phase.phase_fee_usd) * 100),
      99
    );
  }

  return 50; // Default to 50% if in progress
}

// Format currency
function formatCurrency(value?: number): string {
  if (!value) return "$0";
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
  return `$${value.toLocaleString()}`;
}

export function PhaseProgressBar({
  phases,
  discipline,
  compact = false,
  className,
}: PhaseProgressBarProps) {
  // Find current phase (first in_progress or last completed)
  let currentPhaseIndex = -1;
  for (let i = 0; i < STANDARD_PHASES.length; i++) {
    const { status } = getPhaseStatus(STANDARD_PHASES[i].key, phases);
    if (status === "in_progress") {
      currentPhaseIndex = i;
      break;
    }
    if (status === "completed") {
      currentPhaseIndex = i;
    }
  }

  return (
    <TooltipProvider>
      <div className={cn("w-full", className)}>
        {/* Discipline label if provided */}
        {discipline && !compact && (
          <div className="text-xs font-medium text-slate-500 mb-2">
            {discipline}
          </div>
        )}

        {/* Phase progress track */}
        <div className="relative">
          {/* Background track */}
          <div className="absolute top-4 left-0 right-0 h-1 bg-slate-200 rounded-full" />

          {/* Completed track */}
          {currentPhaseIndex >= 0 && (
            <div
              className="absolute top-4 left-0 h-1 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full transition-all duration-500"
              style={{
                width: `${((currentPhaseIndex + 0.5) / STANDARD_PHASES.length) * 100}%`,
              }}
            />
          )}

          {/* Phase nodes */}
          <div className="relative flex justify-between">
            {STANDARD_PHASES.map((phase, index) => {
              const { status, data } = getPhaseStatus(phase.key, phases);
              const progress = data ? calculatePhaseProgress(data) : 0;
              const isCurrent = index === currentPhaseIndex && status === "in_progress";

              return (
                <Tooltip key={phase.key}>
                  <TooltipTrigger asChild>
                    <div
                      className={cn(
                        "flex flex-col items-center cursor-default",
                        compact ? "gap-1" : "gap-2"
                      )}
                    >
                      {/* Node */}
                      <div
                        className={cn(
                          "relative flex items-center justify-center rounded-full border-2 transition-all",
                          compact ? "w-6 h-6" : "w-8 h-8",
                          status === "completed" &&
                            "bg-emerald-500 border-emerald-500 text-white",
                          status === "in_progress" &&
                            "bg-white border-teal-500 text-teal-600",
                          status === "pending" &&
                            "bg-white border-slate-300 text-slate-400",
                          isCurrent && "ring-4 ring-teal-100"
                        )}
                      >
                        {status === "completed" ? (
                          <CheckCircle2 className={compact ? "w-3 h-3" : "w-4 h-4"} />
                        ) : status === "in_progress" ? (
                          <Loader2
                            className={cn(
                              compact ? "w-3 h-3" : "w-4 h-4",
                              "animate-spin"
                            )}
                          />
                        ) : (
                          <Circle className={compact ? "w-3 h-3" : "w-4 h-4"} />
                        )}
                      </div>

                      {/* Label */}
                      <span
                        className={cn(
                          "font-medium text-center",
                          compact ? "text-[10px]" : "text-xs",
                          status === "completed" && "text-emerald-600",
                          status === "in_progress" && "text-teal-600",
                          status === "pending" && "text-slate-400"
                        )}
                      >
                        {phase.label}
                      </span>

                      {/* Progress percentage for current phase */}
                      {isCurrent && !compact && (
                        <span className="text-[10px] text-teal-600 font-medium">
                          {progress}%
                        </span>
                      )}
                    </div>
                  </TooltipTrigger>

                  <TooltipContent side="bottom" className="max-w-xs">
                    <div className="space-y-1">
                      <p className="font-semibold">{phase.fullName}</p>
                      <p className="text-xs text-slate-500">
                        Status:{" "}
                        <span
                          className={cn(
                            "font-medium",
                            status === "completed" && "text-emerald-600",
                            status === "in_progress" && "text-teal-600",
                            status === "pending" && "text-slate-500"
                          )}
                        >
                          {status === "completed"
                            ? "Complete"
                            : status === "in_progress"
                            ? `In Progress (${progress}%)`
                            : "Pending"}
                        </span>
                      </p>
                      {data?.phase_fee_usd && (
                        <p className="text-xs text-slate-500">
                          Fee: {formatCurrency(data.phase_fee_usd)}
                        </p>
                      )}
                      {data?.paid_amount_usd !== undefined && data.paid_amount_usd > 0 && (
                        <p className="text-xs text-emerald-600">
                          Paid: {formatCurrency(data.paid_amount_usd)}
                        </p>
                      )}
                    </div>
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}

// Compact version for list view
export function PhaseProgressCompact({
  phases,
  className,
}: {
  phases: PhaseData[];
  className?: string;
}) {
  return <PhaseProgressBar phases={phases} compact className={className} />;
}

// Get current phase summary text
export function getCurrentPhaseSummary(phases: PhaseData[]): string {
  for (const standardPhase of STANDARD_PHASES) {
    const { status, data } = getPhaseStatus(standardPhase.key, phases);
    if (status === "in_progress") {
      const progress = data ? calculatePhaseProgress(data) : 0;
      return `${standardPhase.fullName} (${progress}%)`;
    }
  }

  // Find last completed
  let lastCompleted = "";
  for (const standardPhase of STANDARD_PHASES) {
    const { status } = getPhaseStatus(standardPhase.key, phases);
    if (status === "completed") {
      lastCompleted = standardPhase.fullName;
    }
  }

  return lastCompleted ? `${lastCompleted} (Complete)` : "Not Started";
}
