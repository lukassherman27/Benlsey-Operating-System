"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Users, FileCheck, Calendar, TrendingUp, CheckCircle2, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { formatCurrency } from "@/lib/utils";

interface ProjectKPICardsProps {
  projectCode?: string; // If provided, shows single project KPIs. If not, shows portfolio summary.
}

export function ProjectKPICards({ projectCode }: ProjectKPICardsProps) {
  // Portfolio-level queries (when no projectCode)
  const activeProjectsQuery = useQuery({
    queryKey: ["projects", "active"],
    queryFn: () => api.getActiveProjects(),
    staleTime: 1000 * 60 * 5,
    enabled: !projectCode,
  });

  const deliverablesQuery = useQuery({
    queryKey: ["deliverables", "pm-list"],
    queryFn: () => api.getPMDeliverables(),
    staleTime: 1000 * 60 * 5,
    enabled: !projectCode,
  });

  // Project-level query (when projectCode provided)
  const projectPhasesQuery = useQuery({
    queryKey: ["project-phases", projectCode],
    queryFn: () => api.getProjectPhases(projectCode!),
    staleTime: 1000 * 60 * 5,
    enabled: !!projectCode,
  });

  const projectTeamQuery = useQuery({
    queryKey: ["project-schedule-team", projectCode],
    queryFn: () => api.getProjectScheduleTeam(projectCode!),
    staleTime: 1000 * 60 * 5,
    enabled: !!projectCode,
  });

  if (projectCode) {
    // Single project view
    const phases = projectPhasesQuery.data?.phases ?? [];
    const team = projectTeamQuery.data?.team ?? [];

    // Calculate phase progress
    const completedPhases = phases.filter((p: { status: string }) => p.status === 'completed').length;
    const totalPhases = phases.length;
    const currentPhase = phases.find((p: { status: string }) => p.status === 'in_progress');
    const phaseProgress = totalPhases > 0 ? (completedPhases / totalPhases) * 100 : 0;

    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Current Phase */}
        <Card className="border-l-4 border-l-teal-500">
          <CardContent className="pt-4">
            <div className="flex items-start justify-between">
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.secondary)}>Current Phase</p>
                <p className="text-xl font-bold text-slate-900 mt-1">
                  {currentPhase?.phase_name || (completedPhases === totalPhases && totalPhases > 0 ? "Complete" : "Not Started")}
                </p>
              </div>
              <Badge variant={phaseProgress >= 50 ? "default" : "secondary"} className="bg-teal-100 text-teal-700">
                {phaseProgress.toFixed(0)}%
              </Badge>
            </div>
            <Progress value={phaseProgress} className="mt-3 h-2" />
            <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mt-2")}>
              {completedPhases} of {totalPhases} phases complete
            </p>
          </CardContent>
        </Card>

        {/* Team Size */}
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="pt-4">
            <div className="flex items-start justify-between">
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.secondary)}>Team Members</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{team.length}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500" />
            </div>
            <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mt-2")}>
              {team.slice(0, 3).map((t: { staff_name: string }) => t.staff_name).join(", ")}
              {team.length > 3 && ` +${team.length - 3} more`}
            </p>
          </CardContent>
        </Card>

        {/* Deliverables placeholder */}
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="pt-4">
            <div className="flex items-start justify-between">
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.secondary)}>Deliverables</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">—</p>
              </div>
              <FileCheck className="h-8 w-8 text-amber-500" />
            </div>
            <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mt-2")}>
              Project deliverables tracking
            </p>
          </CardContent>
        </Card>

        {/* Next Milestone placeholder */}
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="pt-4">
            <div className="flex items-start justify-between">
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.secondary)}>Next Milestone</p>
                <p className="text-lg font-bold text-slate-900 mt-1">—</p>
              </div>
              <Calendar className="h-8 w-8 text-purple-500" />
            </div>
            <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mt-2")}>
              Upcoming deadline
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Portfolio view (all projects)
  const projects = activeProjectsQuery.data?.data ?? [];
  const deliverables = deliverablesQuery.data?.deliverables ?? [];

  const totalProjects = projects.length;
  const overdueDeliverables = deliverables.filter((d: { status: string }) => d.status === 'overdue').length;
  const upcomingDeliverables = deliverables.filter((d: { status: string }) => d.status === 'upcoming').length;
  const pipelineValue = projects.reduce((sum: number, p: { total_fee_usd?: number; contract_value?: number }) =>
    sum + (p.total_fee_usd || p.contract_value || 0), 0);

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Active Projects */}
      <Card className="border-teal-200 bg-teal-50/50">
        <CardContent className="pt-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-teal-600 uppercase tracking-wide flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" /> Active Projects
              </p>
              <p className="text-2xl font-bold text-teal-700 mt-1">{totalProjects}</p>
            </div>
          </div>
          <p className="text-sm text-teal-600">Across all phases</p>
        </CardContent>
      </Card>

      {/* Pipeline Value */}
      <Card className="border-blue-200 bg-blue-50/50">
        <CardContent className="pt-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-blue-600 uppercase tracking-wide flex items-center gap-1">
                <TrendingUp className="h-3 w-3" /> Pipeline Value
              </p>
              <p className="text-2xl font-bold text-blue-700 mt-1">
                {formatCurrency(pipelineValue)}
              </p>
            </div>
          </div>
          <p className="text-sm text-blue-600">Total contract value</p>
        </CardContent>
      </Card>

      {/* Deliverables Needing Attention */}
      <Card className={cn(
        overdueDeliverables > 0 ? "border-red-200 bg-red-50/50" : "border-emerald-200 bg-emerald-50/50"
      )}>
        <CardContent className="pt-4">
          <div className="flex items-start justify-between">
            <div>
              <p className={cn(
                "text-xs font-medium uppercase tracking-wide flex items-center gap-1",
                overdueDeliverables > 0 ? "text-red-600" : "text-emerald-600"
              )}>
                <AlertTriangle className="h-3 w-3" /> Needs Attention
              </p>
              <p className={cn(
                "text-2xl font-bold mt-1",
                overdueDeliverables > 0 ? "text-red-700" : "text-emerald-700"
              )}>
                {overdueDeliverables}
              </p>
            </div>
            <Badge variant={overdueDeliverables > 0 ? "destructive" : "secondary"}>
              {overdueDeliverables > 0 ? "Overdue" : "On Track"}
            </Badge>
          </div>
          <p className={cn(
            "text-sm",
            overdueDeliverables > 0 ? "text-red-600" : "text-emerald-600"
          )}>
            {upcomingDeliverables} upcoming this week
          </p>
        </CardContent>
      </Card>

      {/* Team Overview */}
      <Card className="border-purple-200 bg-purple-50/50">
        <CardContent className="pt-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-purple-600 uppercase tracking-wide flex items-center gap-1">
                <Users className="h-3 w-3" /> Project Managers
              </p>
              <p className="text-2xl font-bold text-purple-700 mt-1">
                {[...new Set(projects.map((p: { pm_name?: string }) => p.pm_name).filter(Boolean))].length}
              </p>
            </div>
          </div>
          <p className="text-sm text-purple-600">Active PMs</p>
        </CardContent>
      </Card>
    </div>
  );
}
