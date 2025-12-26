"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { Calendar, CheckCircle2, Clock, Circle } from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

interface PhaseTimelineProps {
  projectCode: string;
}

interface Phase {
  phase_id: number;
  phase_name: string;
  discipline: string;
  status: string;
  phase_fee_usd: number | null;
  start_date: string | null;
  expected_completion_date: string | null;
  actual_completion_date: string | null;
}

// Standard project phases in order
const PHASE_ORDER = [
  "Mobilization",
  "Concept",
  "Schematic Design",
  "SD",
  "Design Development",
  "DD",
  "Contract Documents",
  "CD",
  "Construction Administration",
  "CA",
];

function getPhaseOrder(phaseName: string): number {
  const idx = PHASE_ORDER.findIndex(
    (p) => phaseName.toLowerCase().includes(p.toLowerCase())
  );
  return idx >= 0 ? idx : 999;
}

function getStatusColor(status: string) {
  switch (status?.toLowerCase()) {
    case "completed":
      return "bg-emerald-500";
    case "in_progress":
    case "active":
      return "bg-blue-500";
    case "pending":
    default:
      return "bg-slate-300";
  }
}

function getStatusIcon(status: string) {
  switch (status?.toLowerCase()) {
    case "completed":
      return <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
    case "in_progress":
    case "active":
      return <Clock className="h-4 w-4 text-blue-600" />;
    default:
      return <Circle className="h-4 w-4 text-slate-400" />;
  }
}

export function PhaseTimeline({ projectCode }: PhaseTimelineProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["project-phases", projectCode],
    queryFn: () => api.getProjectPhases(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  if (isLoading) {
    return (
      <Card className={ds.cards.default}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-teal-600" />
            Project Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-slate-100 rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const phases = (data?.phases ?? []) as Phase[];

  if (phases.length === 0) {
    return (
      <Card className={ds.cards.default}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-teal-600" />
            Project Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-sm text-slate-500">
            No phases defined for this project
          </div>
        </CardContent>
      </Card>
    );
  }

  // Group phases by discipline
  const disciplineGroups = new Map<string, Phase[]>();
  phases.forEach((phase) => {
    const discipline = phase.discipline || "General";
    if (!disciplineGroups.has(discipline)) {
      disciplineGroups.set(discipline, []);
    }
    disciplineGroups.get(discipline)!.push(phase);
  });

  // Sort phases within each group
  disciplineGroups.forEach((phases) => {
    phases.sort((a, b) => getPhaseOrder(a.phase_name) - getPhaseOrder(b.phase_name));
  });

  // Calculate progress
  const completedCount = phases.filter((p) => p.status === "completed").length;
  const inProgressCount = phases.filter(
    (p) => p.status === "in_progress" || p.status === "active"
  ).length;
  const progressPercent = phases.length > 0 ? (completedCount / phases.length) * 100 : 0;

  return (
    <Card className={ds.cards.default}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-teal-600" />
            Project Timeline
          </CardTitle>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
              {completedCount} complete
            </Badge>
            {inProgressCount > 0 && (
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                {inProgressCount} active
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Overall Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-slate-500 mb-1">
            <span>Overall Progress</span>
            <span>{Math.round(progressPercent)}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-gradient-to-r from-teal-500 to-emerald-500 transition-all"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Timeline by Discipline */}
        <div className="space-y-6">
          {Array.from(disciplineGroups.entries()).map(([discipline, disciplinePhases]) => (
            <div key={discipline}>
              <h4 className="text-sm font-semibold text-slate-700 mb-3">{discipline}</h4>
              <div className="relative">
                {/* Timeline line */}
                <div className="absolute left-[7px] top-3 bottom-3 w-0.5 bg-slate-200" />

                <div className="space-y-3">
                  {disciplinePhases.map((phase) => (
                    <div key={phase.phase_id} className="flex items-start gap-4 relative">
                      {/* Status dot */}
                      <div
                        className={cn(
                          "w-4 h-4 rounded-full border-2 border-white shadow-sm z-10",
                          getStatusColor(phase.status)
                        )}
                      />

                      {/* Phase info */}
                      <div className="flex-1 pb-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-slate-900">
                              {phase.phase_name}
                            </span>
                            {getStatusIcon(phase.status)}
                          </div>
                          {phase.phase_fee_usd && (
                            <span className="text-sm text-slate-500">
                              ${(phase.phase_fee_usd / 1000).toFixed(0)}K
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {phase.status === "completed"
                            ? "Completed"
                            : phase.status === "in_progress"
                            ? "In Progress"
                            : "Pending"}
                          {phase.expected_completion_date && (
                            <span> • Due: {phase.expected_completion_date}</span>
                          )}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
