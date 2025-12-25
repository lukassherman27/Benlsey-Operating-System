"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ProjectCard, ProjectCardSkeleton } from "@/components/project/project-card";
import { InvoiceAgingWidget } from "@/components/dashboard/invoice-aging-widget";
import { TopOutstandingInvoicesWidget } from "@/components/dashboard/top-outstanding-invoices-widget";
import { AllInvoicesList } from "@/components/dashboard/all-invoices-list";
import { RFITrackerWidget } from "@/components/dashboard/rfi-tracker-widget";
import { MilestonesWidget } from "@/components/dashboard/milestones-widget";
import {
  Search,
  LayoutGrid,
  List,
  FolderOpen,
  TrendingUp,
  DollarSign,
  Users,
  Building2,
} from "lucide-react";
import { useState, useMemo } from "react";
import { cn } from "@/lib/utils";
import { ds, bensleyVoice } from "@/lib/design-system";

type ViewMode = "grid" | "list";
type PhaseFilter = "all" | "concept" | "sd" | "dd" | "cd" | "ca";

export default function ProjectsPage() {
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [searchQuery, setSearchQuery] = useState("");
  const [phaseFilter, setPhaseFilter] = useState<PhaseFilter>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const activeProjectsQuery = useQuery({
    queryKey: ["projects", "active"],
    queryFn: () => api.getActiveProjects(),
    staleTime: 1000 * 60 * 5,
  });

  const activeProjects = useMemo(
    () => activeProjectsQuery.data?.data ?? [],
    [activeProjectsQuery.data?.data]
  );

  // Filter projects based on search and filters
  const filteredProjects = useMemo(() => {
    return activeProjects.filter((project: Record<string, unknown>) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const name = ((project.project_title as string) || (project.project_name as string) || "").toLowerCase();
        const code = ((project.project_code as string) || "").toLowerCase();
        const client = ((project.client_name as string) || "").toLowerCase();
        if (!name.includes(query) && !code.includes(query) && !client.includes(query)) {
          return false;
        }
      }

      // Status filter
      if (statusFilter !== "all") {
        const status = ((project.status as string) || "active").toLowerCase();
        if (status !== statusFilter.toLowerCase()) {
          return false;
        }
      }

      return true;
    });
  }, [activeProjects, searchQuery, statusFilter]);

  // Calculate stats
  const totalValue = activeProjects.reduce(
    (sum: number, p: Record<string, unknown>) =>
      sum + ((p.total_fee_usd as number) || (p.contract_value as number) || 0),
    0
  );

  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `$${Math.round(value / 1000)}K`;
    return `$${value.toLocaleString()}`;
  };

  return (
    <div className="min-h-screen bg-slate-50 w-full max-w-full overflow-x-hidden">
      <div className="mx-auto max-w-full px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className={ds.typography.pageTitle}>
                {bensleyVoice.sectionHeaders.projects}
              </h1>
              <p className={cn(ds.typography.bodySmall, "mt-2")}>
                Track project phases, teams, and deliverables
              </p>
            </div>
            <Badge variant="secondary" className={ds.badges.default}>
              <TrendingUp className="h-3.5 w-3.5 mr-1" />
              {activeProjects.length} active
            </Badge>
          </div>
        </div>

        {/* Quick Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-white border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-teal-50">
                  <Building2 className="h-5 w-5 text-teal-600" />
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Active Projects</p>
                  <p className="text-2xl font-bold text-slate-900">{activeProjects.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-50">
                  <DollarSign className="h-5 w-5 text-emerald-600" />
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Total Value</p>
                  <p className="text-2xl font-bold text-slate-900">{formatCurrency(totalValue)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-50">
                  <Users className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Team Members</p>
                  <p className="text-2xl font-bold text-slate-900">100</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-amber-50">
                  <TrendingUp className="h-5 w-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Disciplines</p>
                  <p className="text-2xl font-bold text-slate-900">3</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs defaultValue="projects" className="space-y-6">
          <TabsList className="bg-white border">
            <TabsTrigger value="projects" className="data-[state=active]:bg-teal-50">
              <Building2 className="h-4 w-4 mr-2" />
              Projects
            </TabsTrigger>
            <TabsTrigger value="finance" className="data-[state=active]:bg-teal-50">
              <DollarSign className="h-4 w-4 mr-2" />
              Finance
            </TabsTrigger>
            <TabsTrigger value="tracking" className="data-[state=active]:bg-teal-50">
              <TrendingUp className="h-4 w-4 mr-2" />
              RFIs & Milestones
            </TabsTrigger>
          </TabsList>

          {/* Projects Tab */}
          <TabsContent value="projects" className="space-y-6">
            {/* Filters */}
            <Card className="bg-white">
              <CardContent className="p-4">
                <div className="flex flex-wrap items-center gap-4">
                  {/* Search */}
                  <div className="relative flex-1 min-w-[200px]">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                      placeholder="Search projects..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>

                  {/* Phase Filter */}
                  <Select value={phaseFilter} onValueChange={(v) => setPhaseFilter(v as PhaseFilter)}>
                    <SelectTrigger className="w-[160px]">
                      <SelectValue placeholder="Phase" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Phases</SelectItem>
                      <SelectItem value="concept">Concept</SelectItem>
                      <SelectItem value="sd">Schematic Design</SelectItem>
                      <SelectItem value="dd">Design Development</SelectItem>
                      <SelectItem value="cd">Construction Docs</SelectItem>
                      <SelectItem value="ca">Construction Admin</SelectItem>
                    </SelectContent>
                  </Select>

                  {/* Status Filter */}
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="on_hold">On Hold</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                    </SelectContent>
                  </Select>

                  {/* View Toggle */}
                  <div className="flex items-center gap-1 border rounded-lg p-1">
                    <Button
                      variant={viewMode === "grid" ? "secondary" : "ghost"}
                      size="sm"
                      onClick={() => setViewMode("grid")}
                      className="h-8 w-8 p-0"
                    >
                      <LayoutGrid className="h-4 w-4" />
                    </Button>
                    <Button
                      variant={viewMode === "list" ? "secondary" : "ghost"}
                      size="sm"
                      onClick={() => setViewMode("list")}
                      className="h-8 w-8 p-0"
                    >
                      <List className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Projects Grid/List */}
            {activeProjectsQuery.isLoading ? (
              <div className={cn(
                viewMode === "grid"
                  ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
                  : "space-y-3"
              )}>
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <ProjectCardSkeleton key={i} />
                ))}
              </div>
            ) : filteredProjects.length === 0 ? (
              <Card className="bg-white">
                <CardContent className="py-16 text-center">
                  <FolderOpen className="mx-auto h-16 w-16 text-slate-300 mb-4" />
                  <h3 className="text-lg font-semibold text-slate-700">
                    {searchQuery || statusFilter !== "all"
                      ? "No projects match your filters"
                      : bensleyVoice.emptyStates.projects}
                  </h3>
                  <p className="text-sm text-slate-500 mt-2">
                    {searchQuery || statusFilter !== "all"
                      ? "Try adjusting your search or filters"
                      : "Projects will appear here once contracts are signed"}
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className={cn(
                viewMode === "grid"
                  ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
                  : "space-y-3"
              )}>
                {filteredProjects.map((project: Record<string, unknown>) => (
                  <ProjectCard
                    key={String(project.project_id || project.project_code)}
                    project={{
                      project_id: project.project_id as number,
                      project_code: project.project_code as string,
                      project_title: project.project_title as string,
                      project_name: project.project_name as string,
                      client_name: project.client_name as string,
                      status: project.status as string,
                      pm_staff_id: project.pm_staff_id as number,
                      pm_name: project.pm_name as string,
                      total_fee_usd: project.total_fee_usd as number,
                      contract_value: project.contract_value as number,
                      team_count: project.team_count as number,
                      deliverables_due: project.deliverables_due as number,
                      deliverables_overdue: project.deliverables_overdue as number,
                    }}
                  />
                ))}
              </div>
            )}
          </TabsContent>

          {/* Finance Tab */}
          <TabsContent value="finance" className="space-y-6">
            {/* Invoice Aging Widget */}
            <InvoiceAgingWidget />

            {/* Top Outstanding */}
            <TopOutstandingInvoicesWidget />

            {/* All Invoices */}
            <AllInvoicesList />
          </TabsContent>

          {/* RFIs & Milestones Tab */}
          <TabsContent value="tracking" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RFITrackerWidget />
              <MilestonesWidget />
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
