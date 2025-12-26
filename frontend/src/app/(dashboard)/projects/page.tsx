"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Search,
  Filter,
  FolderOpen,
  TrendingUp,
  Users,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { PhaseProgressCompact, getCurrentPhaseSummary } from "@/components/project/phase-progress-bar";

interface Project {
  project_id?: number;
  project_code: string;
  project_title?: string;
  project_name?: string;
  client_name?: string;
  status?: string;
  pm_name?: string;
  total_fee_usd?: number;
  contract_value?: number;
  country?: string;
  current_phase?: string;
  paid_to_date_usd?: number;
  outstanding_usd?: number;
  remaining_value?: number;
}

export default function ProjectsPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [pmFilter, setPmFilter] = useState("all");

  const activeProjectsQuery = useQuery({
    queryKey: ["projects", "active"],
    queryFn: () => api.getActiveProjects(),
    staleTime: 1000 * 60 * 5,
  });

  const projects: Project[] = activeProjectsQuery.data?.data ?? [];

  // Get unique PMs for filter
  const uniquePMs = useMemo(() =>
    [...new Set(projects.map(p => p.pm_name).filter(Boolean))].sort(),
    [projects]
  );

  // Calculate stats
  const stats = useMemo(() => {
    const totalValue = projects.reduce((sum, p) => sum + (p.total_fee_usd || p.contract_value || 0), 0);
    const totalPaid = projects.reduce((sum, p) => sum + (p.paid_to_date_usd || 0), 0);
    const outstanding = projects.reduce((sum, p) => sum + (p.outstanding_usd || 0), 0);
    const remaining = totalValue - totalPaid;
    return { totalProjects: projects.length, totalValue, totalPaid, outstanding, remaining, pmCount: uniquePMs.length };
  }, [projects, uniquePMs]);

  // Filter projects
  const filteredProjects = useMemo(() => {
    return projects.filter(project => {
      if (search) {
        const query = search.toLowerCase();
        const name = (project.project_title || project.project_name || "").toLowerCase();
        const code = project.project_code.toLowerCase();
        const client = (project.client_name || "").toLowerCase();
        if (!name.includes(query) && !code.includes(query) && !client.includes(query)) {
          return false;
        }
      }
      if (pmFilter !== "all" && project.pm_name !== pmFilter) {
        return false;
      }
      return true;
    });
  }, [projects, search, pmFilter]);

  const isLoading = activeProjectsQuery.isLoading;

  return (
    <div className={cn(ds.gap.loose, "space-y-6 w-full max-w-full overflow-x-hidden")}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            Active Projects
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Track progress, teams, and deliverables across all contracts
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200">
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Active Projects</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{stats.totalProjects}</p>
          </CardContent>
        </Card>

        <Card className="border-teal-200 bg-teal-50/50">
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-teal-600 uppercase tracking-wide flex items-center gap-1">
              <TrendingUp className="h-3 w-3" /> Remaining Value
            </p>
            <p className="text-2xl font-bold text-teal-700 mt-1">{formatCurrency(stats.remaining)}</p>
            <p className="text-xs text-teal-600 mt-0.5">of {formatCurrency(stats.totalValue)} total</p>
          </CardContent>
        </Card>

        <Card className="border-blue-200 bg-blue-50/50">
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-blue-600 uppercase tracking-wide flex items-center gap-1">
              <Users className="h-3 w-3" /> Project Managers
            </p>
            <p className="text-2xl font-bold text-blue-700 mt-1">{stats.pmCount}</p>
          </CardContent>
        </Card>

        <Card className="border-emerald-200 bg-emerald-50/50">
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-emerald-600 uppercase tracking-wide flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" /> Collected
            </p>
            <p className="text-2xl font-bold text-emerald-700 mt-1">{formatCurrency(stats.totalPaid)}</p>
            <p className="text-xs text-emerald-600 mt-0.5">{Math.round((stats.totalPaid / stats.totalValue) * 100)}% of total</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
        <CardContent className={ds.spacing.spacious}>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className={cn(
                "absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4",
                ds.textColors.tertiary
              )} />
              <Input
                placeholder="Search by project code, name, or client..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className={cn("pl-10", ds.borderRadius.input)}
              />
            </div>

            <Select value={pmFilter} onValueChange={setPmFilter}>
              <SelectTrigger className={cn("w-[180px]", ds.borderRadius.input)}>
                <Filter className={cn("h-4 w-4 mr-2", ds.textColors.tertiary)} />
                <SelectValue placeholder="All PMs" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All PMs</SelectItem>
                {uniquePMs.map(pm => (
                  <SelectItem key={pm} value={pm!}>{pm}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Projects Table */}
      <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
        <CardContent className={ds.spacing.spacious}>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-12 w-24" />
                  <Skeleton className="h-12 flex-1" />
                  <Skeleton className="h-12 w-40" />
                  <Skeleton className="h-12 w-24" />
                </div>
              ))}
            </div>
          ) : filteredProjects.length === 0 ? (
            <div className="py-16 text-center">
              <FolderOpen className="mx-auto h-16 w-16 text-slate-300 mb-4" />
              <p className={cn(ds.typography.cardHeader, ds.textColors.primary, "mb-2")}>
                No projects found
              </p>
              <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                {search || pmFilter !== "all"
                  ? "Try adjusting your filters"
                  : "Projects will appear here once contracts are signed"
                }
              </p>
            </div>
          ) : (
            <div className={cn("rounded-md border border-slate-200 overflow-x-auto", ds.borderRadius.card)}>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[100px]">Code</TableHead>
                    <TableHead className="min-w-[200px]">Project</TableHead>
                    <TableHead className="w-[100px]">PM</TableHead>
                    <TableHead className="w-[200px]">Phase Progress</TableHead>
                    <TableHead className="w-[80px] text-center">Team</TableHead>
                    <TableHead className="text-right w-[120px]">Contract Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredProjects.map((project) => (
                    <ProjectRow
                      key={project.project_code}
                      project={project}
                      onClick={() => router.push(`/projects/${encodeURIComponent(project.project_code)}`)}
                    />
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ProjectRow({ project, onClick }: { project: Project; onClick: () => void }) {
  const projectCode = project.project_code;

  // Fetch phases for this project
  const phasesQuery = useQuery({
    queryKey: ["project-phases", projectCode],
    queryFn: () => api.getProjectPhases(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  // Fetch team for this project
  const teamQuery = useQuery({
    queryKey: ["project-team", projectCode],
    queryFn: () => api.getProjectTeam(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const phases = phasesQuery.data?.phases ?? [];
  const teamCount = teamQuery.data?.count ?? 0;
  const currentPhase = getCurrentPhaseSummary(
    phases.map((p: { phase_name: string; status: string }) => ({
      phase_name: p.phase_name,
      status: p.status,
    }))
  );

  const projectName = project.project_title || project.project_name || project.client_name || projectCode;
  const contractValue = project.total_fee_usd || project.contract_value || 0;

  return (
    <TableRow
      className={cn("cursor-pointer group", ds.hover.subtle)}
      onClick={onClick}
    >
      <TableCell className="font-mono text-sm">
        <div className="flex items-center gap-2">
          <ExternalLink className="h-3.5 w-3.5 text-slate-400 group-hover:text-teal-600" />
          {projectCode}
        </div>
      </TableCell>
      <TableCell>
        <div>
          <p className={cn(ds.typography.body, ds.textColors.primary, "group-hover:text-teal-700")}>
            {projectName}
          </p>
          {project.country && (
            <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
              {project.country}
            </p>
          )}
        </div>
      </TableCell>
      <TableCell className={cn("text-sm", ds.textColors.secondary)}>
        {project.pm_name || "—"}
      </TableCell>
      <TableCell>
        {phasesQuery.isLoading ? (
          <Skeleton className="h-6 w-full" />
        ) : phases.length > 0 ? (
          <div className="space-y-1">
            <PhaseProgressCompact
              phases={phases.map((p: { phase_name: string; status: string }) => ({
                phase_name: p.phase_name,
                status: p.status,
              }))}
            />
            <p className="text-xs text-teal-600 font-medium text-center">
              {currentPhase}
            </p>
          </div>
        ) : (
          <p className={cn(ds.typography.caption, ds.textColors.tertiary, "text-center")}>
            No phases
          </p>
        )}
      </TableCell>
      <TableCell className="text-center">
        {teamQuery.isLoading ? (
          <Skeleton className="h-5 w-8 mx-auto" />
        ) : teamCount > 0 ? (
          <div className="flex items-center justify-center gap-1">
            <Users className="h-3.5 w-3.5 text-blue-500" />
            <span className="text-sm font-medium text-slate-700">{teamCount}</span>
          </div>
        ) : (
          <span className={cn(ds.typography.caption, ds.textColors.tertiary)}>—</span>
        )}
      </TableCell>
      <TableCell className="text-right">
        <p className={cn(ds.typography.body, ds.textColors.primary, "font-medium")}>
          {formatCurrency(contractValue)}
        </p>
      </TableCell>
    </TableRow>
  );
}
