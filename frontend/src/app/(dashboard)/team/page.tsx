"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Users,
  FolderOpen,
  ListTodo,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  RefreshCw,
  UserPlus,
} from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { ds } from "@/lib/design-system";

// Health status badge component
function HealthBadge({ status }: { status: 'on_track' | 'warning' | 'at_risk' }) {
  const config = {
    on_track: {
      icon: CheckCircle2,
      label: 'On Track',
      className: 'bg-green-100 text-green-700 border-green-200',
    },
    warning: {
      icon: AlertCircle,
      label: 'Warning',
      className: 'bg-amber-100 text-amber-700 border-amber-200',
    },
    at_risk: {
      icon: AlertTriangle,
      label: 'At Risk',
      className: 'bg-red-100 text-red-700 border-red-200',
    },
  };

  const { icon: Icon, label, className } = config[status];

  return (
    <Badge variant="outline" className={cn("gap-1", className)}>
      <Icon className="h-3 w-3" />
      {label}
    </Badge>
  );
}

export default function TeamPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [selectedPM, setSelectedPM] = useState<number | null>(null);
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [projectToAssign, setProjectToAssign] = useState<string | null>(null);
  const [selectedPMForAssign, setSelectedPMForAssign] = useState<string>("");

  // Queries
  const workloadQuery = useQuery({
    queryKey: ["pm-workload"],
    queryFn: () => api.getPMWorkload(),
    staleTime: 1000 * 60 * 2,
  });

  const unassignedQuery = useQuery({
    queryKey: ["unassigned-projects"],
    queryFn: () => api.getUnassignedProjects(),
    staleTime: 1000 * 60 * 2,
  });

  const pmsQuery = useQuery({
    queryKey: ["pms"],
    queryFn: () => api.getPMs(),
    staleTime: 1000 * 60 * 5,
  });

  const pmProjectsQuery = useQuery({
    queryKey: ["pm-projects", selectedPM],
    queryFn: () => api.getProjectsByPM(selectedPM!),
    enabled: !!selectedPM,
    staleTime: 1000 * 60 * 2,
  });

  // Mutation for assigning PM
  const assignMutation = useMutation({
    mutationFn: ({ projectCode, pmId }: { projectCode: string; pmId: number }) =>
      api.assignPMToProject(projectCode, pmId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pm-workload"] });
      queryClient.invalidateQueries({ queryKey: ["unassigned-projects"] });
      queryClient.invalidateQueries({ queryKey: ["pm-projects"] });
      setAssignDialogOpen(false);
      setProjectToAssign(null);
      setSelectedPMForAssign("");
    },
  });

  const pmWorkloads = workloadQuery.data?.data ?? [];
  const unassignedProjects = unassignedQuery.data?.data ?? [];
  const pms = pmsQuery.data?.data ?? [];

  // Calculate totals
  const totals = useMemo(() => ({
    totalPMs: pmWorkloads.length,
    totalProjects: pmWorkloads.reduce((sum, pm) => sum + pm.project_count, 0),
    totalOpenTasks: pmWorkloads.reduce((sum, pm) => sum + pm.open_task_count, 0),
    totalOverdue: pmWorkloads.reduce((sum, pm) => sum + pm.overdue_count, 0),
    unassigned: unassignedProjects.length,
  }), [pmWorkloads, unassignedProjects]);

  const handleAssignClick = (projectCode: string) => {
    setProjectToAssign(projectCode);
    setAssignDialogOpen(true);
  };

  const handleAssignConfirm = () => {
    if (projectToAssign && selectedPMForAssign) {
      assignMutation.mutate({
        projectCode: projectToAssign,
        pmId: parseInt(selectedPMForAssign, 10),
      });
    }
  };

  const isLoading = workloadQuery.isLoading || unassignedQuery.isLoading;

  return (
    <div className={cn(ds.gap.loose, "space-y-6 w-full max-w-full overflow-x-hidden")}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            PM Workload
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Project distribution across project managers
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            workloadQuery.refetch();
            unassignedQuery.refetch();
          }}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="border-slate-200">
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide flex items-center gap-1">
              <Users className="h-3 w-3" /> Project Managers
            </p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{totals.totalPMs}</p>
          </CardContent>
        </Card>

        <Card className="border-blue-200 bg-blue-50/30">
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-blue-600 uppercase tracking-wide flex items-center gap-1">
              <FolderOpen className="h-3 w-3" /> Assigned Projects
            </p>
            <p className="text-2xl font-bold text-blue-700 mt-1">{totals.totalProjects}</p>
          </CardContent>
        </Card>

        <Card className="border-teal-200 bg-teal-50/30">
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-teal-600 uppercase tracking-wide flex items-center gap-1">
              <ListTodo className="h-3 w-3" /> Open Tasks
            </p>
            <p className="text-2xl font-bold text-teal-700 mt-1">{totals.totalOpenTasks}</p>
          </CardContent>
        </Card>

        <Card className="border-red-200 bg-red-50/30">
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-red-600 uppercase tracking-wide flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" /> Overdue
            </p>
            <p className="text-2xl font-bold text-red-700 mt-1">{totals.totalOverdue}</p>
          </CardContent>
        </Card>

        <Card className={cn(
          "border-amber-200 bg-amber-50/30",
          totals.unassigned > 0 && "ring-2 ring-amber-400"
        )}>
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-amber-600 uppercase tracking-wide flex items-center gap-1">
              <AlertCircle className="h-3 w-3" /> Unassigned
            </p>
            <p className="text-2xl font-bold text-amber-700 mt-1">{totals.unassigned}</p>
          </CardContent>
        </Card>
      </div>

      {/* PM Workload Table */}
      <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
        <CardHeader>
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Users className="h-5 w-5 text-slate-600" />
            Project Manager Workload
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <Skeleton className="h-10 flex-1" />
                  <Skeleton className="h-10 w-20" />
                  <Skeleton className="h-10 w-20" />
                  <Skeleton className="h-10 w-24" />
                </div>
              ))}
            </div>
          ) : pmWorkloads.length === 0 ? (
            <div className="py-12 text-center">
              <Users className="mx-auto h-16 w-16 text-slate-300 mb-4" />
              <p className="text-lg font-medium text-slate-700 mb-2">No PMs Found</p>
              <p className="text-sm text-slate-500">
                Add staff members with role &quot;Management&quot; to see them here
              </p>
            </div>
          ) : (
            <div className={cn("rounded-md border border-slate-200 overflow-x-auto", ds.borderRadius.card)}>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[200px]">PM</TableHead>
                    <TableHead className="text-center">Projects</TableHead>
                    <TableHead className="text-center">Open Tasks</TableHead>
                    <TableHead className="text-center">Overdue</TableHead>
                    <TableHead className="text-center">Status</TableHead>
                    <TableHead className="w-[40px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pmWorkloads.map((pm) => (
                    <TableRow
                      key={pm.pm_id}
                      className={cn(
                        "cursor-pointer hover:bg-slate-50 transition-colors",
                        selectedPM === pm.pm_id && "bg-blue-50"
                      )}
                      onClick={() => setSelectedPM(selectedPM === pm.pm_id ? null : pm.pm_id)}
                    >
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="h-9 w-9 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center shadow-sm">
                            <span className="text-sm font-bold text-white">
                              {pm.pm_name.slice(0, 2).toUpperCase()}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium text-slate-900">{pm.pm_name}</p>
                            {pm.office && (
                              <p className="text-xs text-slate-500">{pm.office}</p>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="secondary" className="font-semibold">
                          {pm.project_count}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="font-medium text-slate-700">{pm.open_task_count}</span>
                      </TableCell>
                      <TableCell className="text-center">
                        {pm.overdue_count > 0 ? (
                          <Badge variant="destructive" className="gap-1">
                            <AlertTriangle className="h-3 w-3" />
                            {pm.overdue_count}
                          </Badge>
                        ) : (
                          <span className="text-slate-400">0</span>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        <HealthBadge status={pm.health_status} />
                      </TableCell>
                      <TableCell>
                        <ChevronRight className={cn(
                          "h-4 w-4 text-slate-400 transition-transform",
                          selectedPM === pm.pm_id && "rotate-90"
                        )} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Selected PM's Projects */}
      {selectedPM && pmProjectsQuery.data && (
        <Card className={cn(ds.borderRadius.card, "border-blue-200 bg-blue-50/20")}>
          <CardHeader>
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <FolderOpen className="h-5 w-5 text-blue-600" />
              {pmProjectsQuery.data.pm.display_name}&apos;s Projects
              <Badge variant="secondary" className="ml-2">
                {pmProjectsQuery.data.count} projects
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {pmProjectsQuery.isLoading ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : pmProjectsQuery.data.data.length === 0 ? (
              <p className="text-center py-8 text-slate-500">No projects assigned</p>
            ) : (
              <div className={cn("rounded-md border border-slate-200 overflow-x-auto", ds.borderRadius.card)}>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Project</TableHead>
                      <TableHead className="text-center">Phase</TableHead>
                      <TableHead className="text-center">Architects</TableHead>
                      <TableHead className="text-center">Tasks</TableHead>
                      <TableHead className="text-center">Overdue</TableHead>
                      <TableHead className="text-right">Value</TableHead>
                      <TableHead className="text-center">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pmProjectsQuery.data.data.map((project) => (
                      <TableRow
                        key={project.project_code}
                        className="cursor-pointer hover:bg-white transition-colors"
                        onClick={() => router.push(`/projects/${encodeURIComponent(project.project_code)}`)}
                      >
                        <TableCell>
                          <div>
                            <Badge variant="outline" className="font-mono text-xs mb-1">
                              {project.project_code}
                            </Badge>
                            <p className="font-medium text-slate-900 text-sm">
                              {project.project_title || project.client_name}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="secondary" className="text-xs">
                            {project.current_phase || 'N/A'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          {project.architect_count > 0 ? (
                            <Badge variant="outline" className="bg-blue-50 text-blue-700">
                              <Users className="h-3 w-3 mr-1" />
                              {project.architect_count}
                            </Badge>
                          ) : (
                            <span className="text-slate-400">-</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          <span className="font-medium">{project.open_tasks}</span>
                          <span className="text-slate-400 text-xs">/{project.total_tasks}</span>
                        </TableCell>
                        <TableCell className="text-center">
                          {project.overdue_tasks > 0 ? (
                            <Badge variant="destructive">{project.overdue_tasks}</Badge>
                          ) : (
                            <span className="text-slate-400">0</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {project.contract_value ? formatCurrency(project.contract_value) : '-'}
                        </TableCell>
                        <TableCell className="text-center">
                          <HealthBadge status={project.health_status} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Unassigned Projects */}
      {unassignedProjects.length > 0 && (
        <Card className={cn(ds.borderRadius.card, "border-amber-200 bg-amber-50/20")}>
          <CardHeader>
            <CardTitle className="text-lg font-semibold flex items-center gap-2 text-amber-700">
              <AlertCircle className="h-5 w-5" />
              Projects Without PM Assignment
              <Badge variant="secondary" className="ml-2 bg-amber-100 text-amber-700">
                {unassignedProjects.length} projects
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={cn("rounded-md border border-amber-200 overflow-x-auto", ds.borderRadius.card)}>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Project</TableHead>
                    <TableHead>Client</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-[120px]">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {unassignedProjects.map((project) => (
                    <TableRow key={project.project_code}>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-xs">
                          {project.project_code}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <p className="font-medium text-slate-900">
                          {project.project_title || project.client_name || 'Unknown'}
                        </p>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{project.status || 'Active'}</Badge>
                      </TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant="outline"
                          className="gap-1"
                          onClick={() => handleAssignClick(project.project_code)}
                        >
                          <UserPlus className="h-3 w-3" />
                          Assign PM
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Assign PM Dialog */}
      <Dialog open={assignDialogOpen} onOpenChange={setAssignDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assign Project Manager</DialogTitle>
            <DialogDescription>
              Assign a PM to project {projectToAssign}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Select value={selectedPMForAssign} onValueChange={setSelectedPMForAssign}>
              <SelectTrigger>
                <SelectValue placeholder="Select a PM" />
              </SelectTrigger>
              <SelectContent>
                {pms.map((pm) => (
                  <SelectItem key={pm.staff_id} value={String(pm.staff_id)}>
                    <div className="flex items-center gap-2">
                      <div className="h-6 w-6 rounded-full bg-blue-100 flex items-center justify-center">
                        <span className="text-xs font-bold text-blue-600">
                          {(pm.nickname || pm.first_name).slice(0, 2).toUpperCase()}
                        </span>
                      </div>
                      {pm.nickname || pm.first_name}
                      {pm.office && <span className="text-slate-400 text-xs">({pm.office})</span>}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAssignDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleAssignConfirm}
              disabled={!selectedPMForAssign || assignMutation.isPending}
            >
              {assignMutation.isPending ? 'Assigning...' : 'Assign PM'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
