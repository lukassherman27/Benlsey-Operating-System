"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Loader2,
  ChevronRight,
  Edit2,
  ChartBar,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Phase {
  phase_id: number;
  phase: string;
  phase_name: string;
  phase_order: number;
  progress_percent: number;
  tasks_total: number;
  tasks_completed: number;
  deliverables_total: number;
  deliverables_completed: number;
  hours_logged: number;
  start_date?: string;
  end_date?: string;
  target_end_date?: string;
  status?: string;
  timeline_status: "on_track" | "behind" | "ahead";
  days_variance: number;
  fee_percent: number;
}

interface ProgressData {
  success: boolean;
  project_code: string;
  project_title?: string;
  overall_progress: number;
  phases: Phase[];
  current_phase?: string;
  timeline_status: "on_track" | "behind" | "ahead";
  days_behind: number;
  total_phases: number;
}

interface PhaseProgressProps {
  projectCode: string;
  showDetails?: boolean;
  className?: string;
}

const TIMELINE_STATUS_CONFIG = {
  on_track: {
    label: "On Track",
    color: "text-emerald-600 bg-emerald-50",
    icon: CheckCircle2,
  },
  behind: {
    label: "Behind",
    color: "text-red-600 bg-red-50",
    icon: AlertTriangle,
  },
  ahead: {
    label: "Ahead",
    color: "text-blue-600 bg-blue-50",
    icon: TrendingUp,
  },
};

export function PhaseProgress({ projectCode, showDetails = true, className }: PhaseProgressProps) {
  const queryClient = useQueryClient();
  const [editingPhaseId, setEditingPhaseId] = React.useState<number | null>(null);
  const [editValue, setEditValue] = React.useState<string>("");

  const { data, isLoading, error } = useQuery<ProgressData>({
    queryKey: ["project-progress", projectCode],
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE}/api/projects/${encodeURIComponent(projectCode)}/progress`
      );
      if (!res.ok) throw new Error("Failed to fetch progress");
      return res.json();
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ phaseId, progress }: { phaseId: number; progress: number }) => {
      const res = await fetch(
        `${API_BASE}/api/projects/${encodeURIComponent(projectCode)}/phases/${phaseId}/progress`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ progress_percent: progress }),
        }
      );
      if (!res.ok) throw new Error("Failed to update");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project-progress", projectCode] });
      setEditingPhaseId(null);
    },
  });

  const handleSaveProgress = (phaseId: number) => {
    const value = parseFloat(editValue);
    if (!isNaN(value) && value >= 0 && value <= 100) {
      updateMutation.mutate({ phaseId, progress: value });
    }
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardContent className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
        </CardContent>
      </Card>
    );
  }

  if (error || !data?.success) {
    return (
      <Card className={className}>
        <CardContent className="p-6 text-center text-slate-500">
          <ChartBar className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No progress data available</p>
        </CardContent>
      </Card>
    );
  }

  const overallConfig = TIMELINE_STATUS_CONFIG[data.timeline_status];
  const OverallIcon = overallConfig.icon;

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <ChartBar className="h-5 w-5 text-teal-600" />
              Project Progress
            </CardTitle>
            <CardDescription>
              {data.current_phase
                ? `Currently in ${data.current_phase} phase`
                : "All phases complete"}
            </CardDescription>
          </div>

          <Badge
            variant="outline"
            className={cn("gap-1 px-3 py-1", overallConfig.color)}
          >
            <OverallIcon className="h-4 w-4" />
            {overallConfig.label}
            {data.days_behind > 0 && ` (${data.days_behind}d)`}
          </Badge>
        </div>

        {/* Overall Progress Bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-slate-600">Overall Progress</span>
            <span className="font-semibold">{data.overall_progress}%</span>
          </div>
          <Progress value={data.overall_progress} className="h-3" />
        </div>
      </CardHeader>

      {showDetails && (
        <CardContent>
          <div className="space-y-4">
            {data.phases.map((phase) => {
              const phaseConfig = TIMELINE_STATUS_CONFIG[phase.timeline_status];
              const PhaseIcon = phaseConfig.icon;
              const isEditing = editingPhaseId === phase.phase_id;
              const isCurrentPhase = data.current_phase === phase.phase;
              const isComplete = phase.progress_percent >= 100;

              return (
                <div
                  key={phase.phase_id}
                  className={cn(
                    "p-4 rounded-lg border transition-colors",
                    isCurrentPhase && "border-teal-300 bg-teal-50/50",
                    isComplete && "bg-emerald-50/50 border-emerald-200",
                    !isCurrentPhase && !isComplete && "bg-slate-50/50"
                  )}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          {phase.phase_name || phase.phase}
                        </span>
                        {isCurrentPhase && (
                          <Badge variant="outline" className="text-xs bg-teal-100 text-teal-700 border-teal-200">
                            Current
                          </Badge>
                        )}
                        {isComplete && (
                          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        )}
                      </div>

                      {/* Progress Bar */}
                      <div className="mt-2">
                        <div className="flex items-center gap-2">
                          {isEditing ? (
                            <div className="flex items-center gap-2">
                              <Input
                                type="number"
                                min="0"
                                max="100"
                                value={editValue}
                                onChange={(e) => setEditValue(e.target.value)}
                                className="w-20 h-7 text-sm"
                              />
                              <span className="text-sm text-slate-500">%</span>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-7 px-2"
                                onClick={() => handleSaveProgress(phase.phase_id)}
                                disabled={updateMutation.isPending}
                              >
                                Save
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-7 px-2"
                                onClick={() => setEditingPhaseId(null)}
                              >
                                Cancel
                              </Button>
                            </div>
                          ) : (
                            <>
                              <Progress
                                value={phase.progress_percent}
                                className="h-2 flex-1"
                              />
                              <span className="text-sm font-medium w-12 text-right">
                                {phase.progress_percent}%
                              </span>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="h-6 w-6 p-0 opacity-50 hover:opacity-100"
                                    onClick={() => {
                                      setEditingPhaseId(phase.phase_id);
                                      setEditValue(phase.progress_percent.toString());
                                    }}
                                  >
                                    <Edit2 className="h-3 w-3" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>Edit progress</TooltipContent>
                              </Tooltip>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Stats Row */}
                      <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                        {phase.tasks_total > 0 && (
                          <span>
                            {phase.tasks_completed}/{phase.tasks_total} tasks
                          </span>
                        )}
                        {phase.deliverables_total > 0 && (
                          <span>
                            {phase.deliverables_completed}/{phase.deliverables_total} deliverables
                          </span>
                        )}
                        {phase.hours_logged > 0 && (
                          <span>{phase.hours_logged}h logged</span>
                        )}
                        {phase.fee_percent > 0 && (
                          <span className="text-slate-400">
                            ({phase.fee_percent}% of fee)
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Timeline Status Indicator */}
                    <Tooltip>
                      <TooltipTrigger>
                        <div
                          className={cn(
                            "flex items-center gap-1 text-xs px-2 py-1 rounded",
                            phaseConfig.color
                          )}
                        >
                          <PhaseIcon className="h-3 w-3" />
                          {phase.timeline_status === "behind" && phase.days_variance > 0 && (
                            <span>{phase.days_variance}d</span>
                          )}
                          {phase.timeline_status === "ahead" && phase.days_variance < 0 && (
                            <span>{Math.abs(phase.days_variance)}d</span>
                          )}
                        </div>
                      </TooltipTrigger>
                      <TooltipContent>
                        {phase.timeline_status === "on_track" && "On schedule"}
                        {phase.timeline_status === "behind" && `${phase.days_variance} days behind schedule`}
                        {phase.timeline_status === "ahead" && `${Math.abs(phase.days_variance)} days ahead of schedule`}
                      </TooltipContent>
                    </Tooltip>
                  </div>
                </div>
              );
            })}
          </div>

          {data.phases.length === 0 && (
            <div className="text-center py-8 text-slate-500">
              <ChartBar className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No phases configured</p>
              <p className="text-sm">Add phases in the Phases tab</p>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}

/**
 * Compact progress bar for use in lists/tables
 */
export function PhaseProgressCompact({ projectCode }: { projectCode: string }) {
  const { data, isLoading } = useQuery<ProgressData>({
    queryKey: ["project-progress", projectCode],
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE}/api/projects/${encodeURIComponent(projectCode)}/progress`
      );
      if (!res.ok) throw new Error("Failed to fetch progress");
      return res.json();
    },
  });

  if (isLoading) {
    return <div className="w-24 h-4 bg-slate-200 rounded animate-pulse" />;
  }

  if (!data?.success) {
    return <span className="text-slate-400 text-sm">--</span>;
  }

  const config = TIMELINE_STATUS_CONFIG[data.timeline_status];

  return (
    <div className="flex items-center gap-2">
      <Progress value={data.overall_progress} className="h-2 w-16" />
      <span className="text-sm font-medium">{data.overall_progress}%</span>
      {data.timeline_status !== "on_track" && (
        <Badge
          variant="outline"
          className={cn("text-xs px-1 py-0", config.color)}
        >
          {data.timeline_status === "behind" ? (
            <TrendingDown className="h-3 w-3" />
          ) : (
            <TrendingUp className="h-3 w-3" />
          )}
        </Badge>
      )}
    </div>
  );
}
