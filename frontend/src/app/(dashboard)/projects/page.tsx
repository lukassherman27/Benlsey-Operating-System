"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { Badge } from "@/components/ui/badge";
import {
  Search,
  Filter,
  FolderOpen,
  TrendingUp,
  Users,
  CheckCircle2,
  ExternalLink,
  Building2,
  MapPin,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ListTodo,
  Clock,
  AlertTriangle,
  CalendarDays,
  Package,
  RefreshCw,
  Plus,
} from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { PhaseProgressCompact, getCurrentPhaseSummary } from "@/components/project/phase-progress-bar";
import { TaskKanbanBoard } from "@/components/tasks/task-kanban-board";
import { TaskEditModal } from "@/components/tasks/task-edit-modal";

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

interface Task {
  task_id: number;
  title: string;
  description: string | null;
  task_type: string;
  priority: string;
  status: string;
  due_date: string | null;
  project_code: string | null;
  proposal_id: number | null;
  assignee: string | null;
  created_at: string;
  completed_at: string | null;
  category: string | null;
}

// Phase colors for visualization
const PHASE_COLORS: Record<string, { color: string; textColor: string; label: string }> = {
  "Mobilization": { color: "bg-slate-400", textColor: "text-slate-700", label: "Mobilization" },
  "Concept": { color: "bg-blue-400", textColor: "text-blue-700", label: "Concept Design" },
  "SD": { color: "bg-cyan-500", textColor: "text-cyan-700", label: "Schematic Design" },
  "DD": { color: "bg-teal-500", textColor: "text-teal-700", label: "Design Development" },
  "CD": { color: "bg-emerald-500", textColor: "text-emerald-700", label: "Construction Docs" },
  "CA": { color: "bg-green-600", textColor: "text-green-700", label: "Construction Admin" },
};

export default function ProjectsPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("projects");
  const [search, setSearch] = useState("");
  const [pmFilter, setPmFilter] = useState("all");
  const [countryFilter, setCountryFilter] = useState("all");
  const [phaseFilter, setPhaseFilter] = useState("all");
  const [sortField, setSortField] = useState<"value" | "name" | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

  // Task modal state
  const [taskModalOpen, setTaskModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [taskModalMode, setTaskModalMode] = useState<"create" | "edit">("create");

  // Queries
  const activeProjectsQuery = useQuery({
    queryKey: ["projects", "active"],
    queryFn: () => api.getActiveProjects(),
    staleTime: 1000 * 60 * 5,
  });

  const tasksQuery = useQuery({
    queryKey: ["tasks"],
    queryFn: () => api.getTasks({ limit: 500 }),
    staleTime: 1000 * 60 * 2,
  });

  const projects: Project[] = activeProjectsQuery.data?.data ?? [];
  const tasks: Task[] = tasksQuery.data?.tasks ?? [];

  // Get unique PMs and countries for filters
  const uniquePMs = useMemo(() =>
    [...new Set(projects.map(p => p.pm_name).filter(Boolean))].sort(),
    [projects]
  );

  const uniqueCountries = useMemo(() =>
    [...new Set(projects.map(p => p.country).filter(Boolean))].sort(),
    [projects]
  );

  // Calculate project stats
  const projectStats = useMemo(() => {
    const totalValue = projects.reduce((sum, p) => sum + (p.total_fee_usd || p.contract_value || 0), 0);
    const totalPaid = projects.reduce((sum, p) => sum + (p.paid_to_date_usd || 0), 0);
    const remaining = totalValue - totalPaid;
    return {
      totalProjects: projects.length,
      totalValue,
      totalPaid,
      remaining,
      pmCount: uniquePMs.length,
      countryCount: uniqueCountries.length,
    };
  }, [projects, uniquePMs, uniqueCountries]);

  // Calculate task stats
  const taskStats = useMemo(() => {
    const today = new Date().toISOString().split("T")[0];
    return {
      total: tasks.length,
      pending: tasks.filter(t => t.status === "pending" || t.status === "in_progress").length,
      overdue: tasks.filter(t => t.due_date && t.due_date < today && t.status !== "completed" && t.status !== "cancelled").length,
      completed: tasks.filter(t => t.status === "completed").length,
    };
  }, [tasks]);

  // Phase distribution
  const phaseDistribution = useMemo(() => {
    const phases = ["Mobilization", "Concept", "SD", "DD", "CD", "CA"];
    const distribution: Record<string, { count: number; value: number }> = {};

    phases.forEach(p => {
      distribution[p] = { count: 0, value: 0 };
    });

    projects.forEach(p => {
      const phase = p.current_phase || "Concept";
      const normalizedPhase = phases.find(ph =>
        phase.toLowerCase().includes(ph.toLowerCase()) ||
        ph.toLowerCase().includes(phase.toLowerCase())
      ) || "Concept";

      if (distribution[normalizedPhase]) {
        distribution[normalizedPhase].count++;
        distribution[normalizedPhase].value += p.total_fee_usd || p.contract_value || 0;
      }
    });

    return distribution;
  }, [projects]);

  // Filter projects
  const filteredProjects = useMemo(() => {
    let result = projects.filter(project => {
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
      if (countryFilter !== "all" && project.country !== countryFilter) {
        return false;
      }
      if (phaseFilter !== "all") {
        const phase = project.current_phase || "Concept";
        if (!phase.toLowerCase().includes(phaseFilter.toLowerCase())) {
          return false;
        }
      }
      return true;
    });

    // Apply sorting
    if (sortField) {
      result = [...result].sort((a, b) => {
        let comparison = 0;
        if (sortField === "value") {
          comparison = (a.total_fee_usd || a.contract_value || 0) - (b.total_fee_usd || b.contract_value || 0);
        } else if (sortField === "name") {
          const nameA = a.project_title || a.project_name || "";
          const nameB = b.project_title || b.project_name || "";
          comparison = nameA.localeCompare(nameB);
        }
        return sortDirection === "asc" ? comparison : -comparison;
      });
    }

    return result;
  }, [projects, search, pmFilter, countryFilter, phaseFilter, sortField, sortDirection]);

  const handleSort = (field: "value" | "name") => {
    if (sortField === field) {
      if (sortDirection === "desc") {
        setSortDirection("asc");
      } else {
        setSortField(null);
      }
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  const getSortIcon = (field: "value" | "name") => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-3 w-3 ml-1 opacity-50" />;
    }
    return sortDirection === "desc"
      ? <ArrowDown className="h-3 w-3 ml-1" />
      : <ArrowUp className="h-3 w-3 ml-1" />;
  };

  const handleCreateTask = () => {
    setSelectedTask(null);
    setTaskModalMode("create");
    setTaskModalOpen(true);
  };

  const handleEditTask = (task: Task) => {
    setSelectedTask(task);
    setTaskModalMode("edit");
    setTaskModalOpen(true);
  };

  const isLoading = activeProjectsQuery.isLoading || tasksQuery.isLoading;

  return (
    <div className={cn(ds.gap.loose, "space-y-6 w-full max-w-full overflow-x-hidden")}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            Project Management
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Track projects, tasks, and deliverables in one place
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              activeProjectsQuery.refetch();
              tasksQuery.refetch();
            }}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button size="sm" onClick={handleCreateTask}>
            <Plus className="h-4 w-4 mr-2" />
            New Task
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-slate-200">
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide flex items-center gap-1">
              <Building2 className="h-3 w-3" /> Active Projects
            </p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{projectStats.totalProjects}</p>
          </CardContent>
        </Card>

        <Card className={cn("border-blue-200 bg-blue-50/30", activeTab === "tasks" && "ring-2 ring-blue-400")}>
          <CardContent className="pt-4 cursor-pointer" onClick={() => setActiveTab("tasks")}>
            <p className="text-xs font-medium text-blue-600 uppercase tracking-wide flex items-center gap-1">
              <ListTodo className="h-3 w-3" /> Pending Tasks
            </p>
            <p className="text-2xl font-bold text-blue-700 mt-1">{taskStats.pending}</p>
          </CardContent>
        </Card>

        <Card className="border-red-200 bg-red-50/30">
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-red-600 uppercase tracking-wide flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" /> Overdue
            </p>
            <p className="text-2xl font-bold text-red-700 mt-1">{taskStats.overdue}</p>
          </CardContent>
        </Card>

        <Card className="border-teal-200 bg-teal-50/30">
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-teal-600 uppercase tracking-wide flex items-center gap-1">
              <TrendingUp className="h-3 w-3" /> Remaining Value
            </p>
            <p className="text-2xl font-bold text-teal-700 mt-1">{formatCurrency(projectStats.remaining)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4 max-w-xl">
          <TabsTrigger value="projects" className="gap-2">
            <Building2 className="h-4 w-4" />
            <span className="hidden sm:inline">Projects</span>
          </TabsTrigger>
          <TabsTrigger value="tasks" className="gap-2">
            <ListTodo className="h-4 w-4" />
            <span className="hidden sm:inline">Tasks</span>
            {taskStats.pending > 0 && (
              <Badge variant="secondary" className="ml-1 text-xs">{taskStats.pending}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="timeline" className="gap-2">
            <CalendarDays className="h-4 w-4" />
            <span className="hidden sm:inline">Timeline</span>
          </TabsTrigger>
          <TabsTrigger value="deliverables" className="gap-2">
            <Package className="h-4 w-4" />
            <span className="hidden sm:inline">Deliverables</span>
          </TabsTrigger>
        </TabsList>

        {/* Projects Tab */}
        <TabsContent value="projects" className="space-y-4">
          {/* Phase Distribution */}
          <Card className="border-slate-200">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-slate-600">Phase Distribution</CardTitle>
                <span className="text-xs text-slate-500">
                  {filteredProjects.length} projects shown
                </span>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {Object.entries(PHASE_COLORS).map(([phase, { color, textColor, label }]) => {
                const data = phaseDistribution[phase] || { count: 0, value: 0 };
                const maxCount = Math.max(...Object.values(phaseDistribution).map(d => d.count), 1);
                const widthPercent = maxCount > 0 ? Math.max((data.count / maxCount) * 100, 8) : 8;

                return (
                  <div
                    key={phase}
                    className={cn(
                      "flex items-center gap-3 cursor-pointer p-2 rounded hover:bg-slate-50 transition-colors",
                      phaseFilter === phase && "bg-slate-100 ring-1 ring-slate-300"
                    )}
                    onClick={() => {
                      setPhaseFilter(phaseFilter === phase ? "all" : phase);
                    }}
                  >
                    <span className={cn("w-40 text-sm font-medium", textColor)}>{label}</span>
                    <div className="flex-1 h-6 bg-slate-100 rounded overflow-hidden">
                      <div
                        className={cn(color, "h-full flex items-center justify-end pr-2 transition-all")}
                        style={{ width: `${widthPercent}%` }}
                      >
                        {data.count > 0 && (
                          <span className="text-white text-xs font-bold">{data.count}</span>
                        )}
                      </div>
                    </div>
                    <span className="w-24 text-right text-sm font-medium text-slate-600">
                      {formatCurrency(data.value)}
                    </span>
                  </div>
                );
              })}
            </CardContent>
          </Card>

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
                    <Users className={cn("h-4 w-4 mr-2", ds.textColors.tertiary)} />
                    <SelectValue placeholder="All PMs" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All PMs ({projectStats.pmCount})</SelectItem>
                    {uniquePMs.map(pm => (
                      <SelectItem key={pm} value={pm!}>{pm}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select value={countryFilter} onValueChange={setCountryFilter}>
                  <SelectTrigger className={cn("w-[180px]", ds.borderRadius.input)}>
                    <MapPin className={cn("h-4 w-4 mr-2", ds.textColors.tertiary)} />
                    <SelectValue placeholder="All Countries" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Countries ({projectStats.countryCount})</SelectItem>
                    {uniqueCountries.map(country => (
                      <SelectItem key={country} value={country!}>{country}</SelectItem>
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
                    {search || pmFilter !== "all" || countryFilter !== "all" || phaseFilter !== "all"
                      ? "Try adjusting your filters"
                      : "Projects will appear here once contracts are signed"
                    }
                  </p>
                </div>
              ) : (
                <div className={cn("rounded-md border border-slate-200 overflow-x-auto", ds.borderRadius.card)}>
                  <Table className="min-w-[800px]">
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[100px]">Code</TableHead>
                        <TableHead
                          className="min-w-[200px] cursor-pointer hover:bg-slate-50 select-none"
                          onClick={() => handleSort("name")}
                        >
                          <span className="flex items-center">
                            Project {getSortIcon("name")}
                          </span>
                        </TableHead>
                        <TableHead className="w-[100px]">PM</TableHead>
                        <TableHead className="w-[100px]">Country</TableHead>
                        <TableHead className="w-[180px]">Phase Progress</TableHead>
                        <TableHead className="w-[80px] text-center">Team</TableHead>
                        <TableHead
                          className="text-right w-[120px] cursor-pointer hover:bg-slate-50 select-none"
                          onClick={() => handleSort("value")}
                        >
                          <span className="flex items-center justify-end">
                            Contract Value {getSortIcon("value")}
                          </span>
                        </TableHead>
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

              {!isLoading && filteredProjects.length > 0 && (
                <div className="mt-4 text-sm text-slate-500">
                  Showing {filteredProjects.length} of {projects.length} projects
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tasks Tab - Kanban Board */}
        <TabsContent value="tasks" className="space-y-4">
          <TaskKanbanBoard
            tasks={tasks}
            categoryFilter={null}
            onEditTask={handleEditTask}
          />
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="space-y-4">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CalendarDays className="h-5 w-5 text-slate-600" />
                Project Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="py-12 text-center">
              <CalendarDays className="mx-auto h-16 w-16 text-slate-300 mb-4" />
              <p className="text-lg font-medium text-slate-700 mb-2">
                Gantt Timeline Coming Soon
              </p>
              <p className="text-sm text-slate-500 max-w-md mx-auto">
                This will show all projects with their milestones and phases in a visual timeline.
                Using wx-react-gantt library which is already installed.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Deliverables Tab */}
        <TabsContent value="deliverables" className="space-y-4">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5 text-slate-600" />
                Deliverables Overview
              </CardTitle>
            </CardHeader>
            <CardContent className="py-12 text-center">
              <Package className="mx-auto h-16 w-16 text-slate-300 mb-4" />
              <p className="text-lg font-medium text-slate-700 mb-2">
                Deliverables Dashboard Coming Soon
              </p>
              <p className="text-sm text-slate-500 max-w-md mx-auto">
                This will show PM workload, deliverables by phase, and status tracking.
                The API endpoints already exist.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Task Edit Modal */}
      <TaskEditModal
        open={taskModalOpen}
        onOpenChange={setTaskModalOpen}
        task={selectedTask}
        mode={taskModalMode}
      />
    </div>
  );
}

function ProjectRow({ project, onClick }: { project: Project; onClick: () => void }) {
  const projectCode = project.project_code;

  const phasesQuery = useQuery({
    queryKey: ["project-phases", projectCode],
    queryFn: () => api.getProjectPhases(projectCode),
    staleTime: 1000 * 60 * 5,
  });

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
          <ExternalLink className="h-3.5 w-3.5 text-slate-400 group-hover:text-teal-600 transition-colors" />
          {projectCode}
        </div>
      </TableCell>
      <TableCell>
        <div>
          <p className={cn(ds.typography.body, ds.textColors.primary, "group-hover:text-teal-700 transition-colors")}>
            {projectName}
          </p>
          {project.client_name && project.client_name !== projectName && (
            <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
              {project.client_name}
            </p>
          )}
        </div>
      </TableCell>
      <TableCell className={cn("text-sm", ds.textColors.secondary)}>
        {project.pm_name || "—"}
      </TableCell>
      <TableCell>
        {project.country ? (
          <span className="inline-flex items-center gap-1 text-xs text-slate-600">
            <MapPin className="h-3 w-3 text-slate-400" />
            {project.country}
          </span>
        ) : (
          <span className="text-slate-400">—</span>
        )}
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
          <div className="inline-flex items-center justify-center gap-1 px-2 py-1 rounded-full bg-blue-50 text-blue-700">
            <Users className="h-3.5 w-3.5" />
            <span className="text-sm font-medium">{teamCount}</span>
          </div>
        ) : (
          <span className={cn(ds.typography.caption, ds.textColors.tertiary)}>—</span>
        )}
      </TableCell>
      <TableCell className="text-right">
        <p className={cn(ds.typography.body, ds.textColors.primary, "font-semibold")}>
          {formatCurrency(contractValue)}
        </p>
      </TableCell>
    </TableRow>
  );
}
