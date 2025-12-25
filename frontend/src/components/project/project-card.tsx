"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";
import {
  Users,
  FileText,
  AlertTriangle,
  Calendar,
  DollarSign,
} from "lucide-react";
import { PhaseProgressCompact, getCurrentPhaseSummary } from "./phase-progress-bar";

interface ProjectCardProps {
  project: {
    project_id?: number;
    project_code: string;
    project_title?: string;
    project_name?: string;
    client_name?: string;
    status?: string;
    pm_staff_id?: number;
    pm_name?: string;
    total_fee_usd?: number;
    contract_value?: number;
    team_count?: number;
    deliverables_due?: number;
    deliverables_overdue?: number;
  };
  className?: string;
}

// Format currency compactly
function formatCurrency(value?: number | null): string {
  if (!value) return "$0";
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `$${Math.round(value / 1000)}K`;
  return `$${value.toLocaleString()}`;
}

export function ProjectCard({ project, className }: ProjectCardProps) {
  const router = useRouter();
  const projectCode = project.project_code;

  // Fetch phases for this project
  const phasesQuery = useQuery({
    queryKey: ["project-phases", projectCode],
    queryFn: () => api.getProjectPhases(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const phases = phasesQuery.data?.phases ?? [];
  const currentPhase = getCurrentPhaseSummary(
    phases.map((p) => ({
      phase_name: p.phase_name,
      status: p.status,
      phase_fee_usd: p.phase_fee_usd ?? undefined,
      invoiced_amount_usd: p.invoiced_amount_usd ?? undefined,
      paid_amount_usd: p.paid_amount_usd ?? undefined,
    }))
  );

  const contractValue = project.total_fee_usd || project.contract_value || 0;
  const projectName = project.project_title || project.project_name || project.client_name || projectCode;
  const hasOverdue = (project.deliverables_overdue ?? 0) > 0;

  const handleClick = () => {
    router.push(`/projects/${encodeURIComponent(projectCode)}`);
  };

  return (
    <Card
      className={cn(
        "group cursor-pointer transition-all hover:shadow-md hover:border-teal-200",
        hasOverdue && "border-l-4 border-l-red-400",
        className
      )}
      onClick={handleClick}
    >
      <div className="p-4 space-y-3">
        {/* Header: Project name + PM */}
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-slate-900 truncate group-hover:text-teal-700 transition-colors">
              {projectName}
            </h3>
            <p className="text-xs text-slate-500 font-mono">{projectCode}</p>
          </div>
          {project.pm_name && (
            <Badge variant="outline" className="text-xs shrink-0">
              PM: {project.pm_name}
            </Badge>
          )}
        </div>

        {/* Phase Progress */}
        <div className="py-2">
          {phasesQuery.isLoading ? (
            <Skeleton className="h-10 w-full" />
          ) : phases.length > 0 ? (
            <PhaseProgressCompact
              phases={phases.map((p) => ({
                phase_name: p.phase_name,
                status: p.status,
                phase_fee_usd: p.phase_fee_usd ?? undefined,
                invoiced_amount_usd: p.invoiced_amount_usd ?? undefined,
                paid_amount_usd: p.paid_amount_usd ?? undefined,
              }))}
            />
          ) : (
            <div className="text-xs text-slate-400 text-center py-2">
              No phases defined
            </div>
          )}
        </div>

        {/* Current phase label */}
        {phases.length > 0 && (
          <div className="text-center">
            <span className="text-xs font-medium text-teal-600">
              {currentPhase}
            </span>
          </div>
        )}

        {/* Stats row */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100">
          {/* Deliverables */}
          <div className="flex items-center gap-1">
            {hasOverdue ? (
              <AlertTriangle className="h-3.5 w-3.5 text-red-500" />
            ) : (
              <FileText className="h-3.5 w-3.5 text-slate-400" />
            )}
            <span
              className={cn(
                "text-xs",
                hasOverdue ? "text-red-600 font-medium" : "text-slate-500"
              )}
            >
              {hasOverdue
                ? `${project.deliverables_overdue} overdue`
                : project.deliverables_due
                ? `${project.deliverables_due} due`
                : "No deliverables"}
            </span>
          </div>

          {/* Team */}
          {project.team_count !== undefined && project.team_count > 0 && (
            <div className="flex items-center gap-1">
              <Users className="h-3.5 w-3.5 text-slate-400" />
              <span className="text-xs text-slate-500">
                {project.team_count} team
              </span>
            </div>
          )}

          {/* Contract value */}
          <div className="flex items-center gap-1">
            <DollarSign className="h-3.5 w-3.5 text-slate-400" />
            <span className="text-xs font-medium text-slate-700">
              {formatCurrency(contractValue)}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
}

// Loading skeleton for project card
export function ProjectCardSkeleton() {
  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-3 w-1/4" />
        </div>
        <Skeleton className="h-5 w-16" />
      </div>
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-4 w-1/3 mx-auto" />
      <div className="flex justify-between pt-2 border-t">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-16" />
      </div>
    </Card>
  );
}
