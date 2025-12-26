"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, Title, Text, TextInput, Select, SelectItem, Grid } from "@tremor/react";
import { ProjectKPICards } from "@/components/project/project-kpi-cards";
import { ProjectListCard, ProjectListCardSkeleton } from "@/components/project/project-list-card";
import { Search, FolderOpen } from "lucide-react";

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
}

export default function ProjectsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [phaseFilter, setPhaseFilter] = useState("all");
  const [pmFilter, setPmFilter] = useState("all");

  const activeProjectsQuery = useQuery({
    queryKey: ["projects", "active"],
    queryFn: () => api.getActiveProjects(),
    staleTime: 1000 * 60 * 5,
  });

  const projects: Project[] = activeProjectsQuery.data?.data ?? [];

  // Get unique PMs for filter
  const uniquePMs = [...new Set(projects.map(p => p.pm_name).filter(Boolean))].sort();

  // Filter projects
  const filteredProjects = projects.filter(project => {
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const name = (project.project_title || project.project_name || "").toLowerCase();
      const code = project.project_code.toLowerCase();
      const client = (project.client_name || "").toLowerCase();
      if (!name.includes(query) && !code.includes(query) && !client.includes(query)) {
        return false;
      }
    }

    // PM filter
    if (pmFilter !== "all" && project.pm_name !== pmFilter) {
      return false;
    }

    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50 w-full max-w-full overflow-x-hidden">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Title className="text-3xl font-bold text-slate-900">Projects</Title>
          <Text className="mt-2 text-slate-600">
            Track progress, teams, and deliverables across all active contracts
          </Text>
        </div>

        {/* KPI Cards */}
        <div className="mb-8">
          <ProjectKPICards />
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <div className="flex flex-wrap items-center gap-4">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <TextInput
                icon={Search}
                placeholder="Search projects..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Phase Filter */}
            <Select
              value={phaseFilter}
              onValueChange={setPhaseFilter}
              placeholder="All Phases"
              className="w-[150px]"
            >
              <SelectItem value="all">All Phases</SelectItem>
              <SelectItem value="concept">Concept</SelectItem>
              <SelectItem value="sd">Schematic Design</SelectItem>
              <SelectItem value="dd">Design Development</SelectItem>
              <SelectItem value="cd">Construction Docs</SelectItem>
              <SelectItem value="ca">Contract Admin</SelectItem>
            </Select>

            {/* PM Filter */}
            <Select
              value={pmFilter}
              onValueChange={setPmFilter}
              placeholder="All PMs"
              className="w-[180px]"
            >
              <SelectItem value="all">All PMs</SelectItem>
              {uniquePMs.map(pm => (
                <SelectItem key={pm} value={pm!}>{pm}</SelectItem>
              ))}
            </Select>

            {/* Results count */}
            <Text className="text-sm text-slate-500">
              {filteredProjects.length} of {projects.length} projects
            </Text>
          </div>
        </Card>

        {/* Projects Grid */}
        {activeProjectsQuery.isLoading ? (
          <Grid numItemsSm={1} numItemsMd={2} numItemsLg={3} className="gap-4">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <ProjectListCardSkeleton key={i} />
            ))}
          </Grid>
        ) : filteredProjects.length === 0 ? (
          <Card className="py-16 text-center">
            <FolderOpen className="mx-auto h-16 w-16 text-slate-300 mb-4" />
            <Title className="text-slate-600">No projects found</Title>
            <Text className="mt-2 text-slate-500">
              {searchQuery || pmFilter !== "all" || phaseFilter !== "all"
                ? "Try adjusting your filters"
                : "Projects will appear here once contracts are signed"
              }
            </Text>
          </Card>
        ) : (
          <Grid numItemsSm={1} numItemsMd={2} numItemsLg={3} className="gap-4">
            {filteredProjects.map((project) => (
              <ProjectListCard key={project.project_code} project={project} />
            ))}
          </Grid>
        )}
      </div>
    </div>
  );
}
