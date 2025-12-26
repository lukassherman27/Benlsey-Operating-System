"use client";

import { Card, Metric, Text, Flex, ProgressBar, BadgeDelta, Grid } from "@tremor/react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Users, FileCheck, Calendar, TrendingUp } from "lucide-react";

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
    queryFn: async () => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/projects/${projectCode}/schedule-team`);
      if (!res.ok) return { team: [], schedule: [] };
      return res.json();
    },
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
      <Grid numItemsSm={2} numItemsLg={4} className="gap-4">
        {/* Current Phase */}
        <Card decoration="top" decorationColor="teal">
          <Flex alignItems="start">
            <div>
              <Text>Current Phase</Text>
              <Metric className="mt-1">
                {currentPhase?.phase_name || (completedPhases === totalPhases && totalPhases > 0 ? "Complete" : "Not Started")}
              </Metric>
            </div>
            <BadgeDelta deltaType={phaseProgress >= 50 ? "increase" : "unchanged"}>
              {phaseProgress.toFixed(0)}%
            </BadgeDelta>
          </Flex>
          <ProgressBar value={phaseProgress} color="teal" className="mt-3" />
          <Text className="mt-2 text-xs">
            {completedPhases} of {totalPhases} phases complete
          </Text>
        </Card>

        {/* Team Size */}
        <Card decoration="top" decorationColor="blue">
          <Flex alignItems="start">
            <div>
              <Text>Team Members</Text>
              <Metric className="mt-1">{team.length}</Metric>
            </div>
            <Users className="h-8 w-8 text-blue-500" />
          </Flex>
          <Text className="mt-2 text-xs">
            {team.slice(0, 3).map((t: { staff_name: string }) => t.staff_name).join(", ")}
            {team.length > 3 && ` +${team.length - 3} more`}
          </Text>
        </Card>

        {/* Deliverables placeholder - would need project-specific API */}
        <Card decoration="top" decorationColor="amber">
          <Flex alignItems="start">
            <div>
              <Text>Deliverables</Text>
              <Metric className="mt-1">—</Metric>
            </div>
            <FileCheck className="h-8 w-8 text-amber-500" />
          </Flex>
          <Text className="mt-2 text-xs">
            Project deliverables tracking
          </Text>
        </Card>

        {/* Next Milestone placeholder */}
        <Card decoration="top" decorationColor="purple">
          <Flex alignItems="start">
            <div>
              <Text>Next Milestone</Text>
              <Metric className="mt-1 text-lg">—</Metric>
            </div>
            <Calendar className="h-8 w-8 text-purple-500" />
          </Flex>
          <Text className="mt-2 text-xs">
            Upcoming deadline
          </Text>
        </Card>
      </Grid>
    );
  }

  // Portfolio view (all projects)
  const projects = activeProjectsQuery.data?.data ?? [];
  const deliverables = deliverablesQuery.data?.deliverables ?? [];

  const totalProjects = projects.length;
  const overdueDeliverables = deliverables.filter((d: { status: string }) => d.status === 'overdue').length;
  const upcomingDeliverables = deliverables.filter((d: { status: string }) => d.status === 'upcoming').length;

  // Count projects by phase (would need better data structure)
  const projectsByPhase = {
    concept: 0,
    sd: 0,
    dd: 0,
    cd: 0,
    ca: 0,
  };

  return (
    <Grid numItemsSm={2} numItemsLg={4} className="gap-4">
      {/* Total Active Projects */}
      <Card decoration="top" decorationColor="teal">
        <Flex alignItems="start">
          <div>
            <Text>Active Projects</Text>
            <Metric className="mt-1">{totalProjects}</Metric>
          </div>
          <BadgeDelta deltaType="increase">Active</BadgeDelta>
        </Flex>
        <Text className="mt-2 text-xs">
          Across all phases
        </Text>
      </Card>

      {/* Projects in DD Phase */}
      <Card decoration="top" decorationColor="blue">
        <Flex alignItems="start">
          <div>
            <Text>In Design Dev</Text>
            <Metric className="mt-1">{projectsByPhase.dd || "—"}</Metric>
          </div>
          <TrendingUp className="h-8 w-8 text-blue-500" />
        </Flex>
        <Text className="mt-2 text-xs">
          Most active phase
        </Text>
      </Card>

      {/* Deliverables Needing Attention */}
      <Card decoration="top" decorationColor={overdueDeliverables > 0 ? "red" : "emerald"}>
        <Flex alignItems="start">
          <div>
            <Text>Needs Attention</Text>
            <Metric className="mt-1">{overdueDeliverables}</Metric>
          </div>
          <BadgeDelta deltaType={overdueDeliverables > 0 ? "decrease" : "unchanged"}>
            {overdueDeliverables > 0 ? "Overdue" : "On Track"}
          </BadgeDelta>
        </Flex>
        <Text className="mt-2 text-xs">
          {upcomingDeliverables} upcoming this week
        </Text>
      </Card>

      {/* Pipeline Value */}
      <Card decoration="top" decorationColor="purple">
        <Flex alignItems="start">
          <div>
            <Text>Pipeline Value</Text>
            <Metric className="mt-1">
              ${((projects.reduce((sum: number, p: { total_fee_usd?: number; contract_value?: number }) =>
                sum + (p.total_fee_usd || p.contract_value || 0), 0)) / 1000000).toFixed(1)}M
            </Metric>
          </div>
          <TrendingUp className="h-8 w-8 text-purple-500" />
        </Flex>
        <Text className="mt-2 text-xs">
          Total contract value
        </Text>
      </Card>
    </Grid>
  );
}
