"use client";

import { Card, ProgressBar, Badge, Text } from "@tremor/react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import { Users, FileText, DollarSign, Mail, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

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

interface ProjectListCardProps {
  project: Project;
}

// Phase order for progress calculation
const PHASE_ORDER = [
  "Mobilization",
  "Concept Design",
  "Schematic Design",
  "Design Development",
  "Construction Documents",
  "Construction Observation"
];

function getPhaseIndex(phaseName: string): number {
  const lower = phaseName.toLowerCase();
  for (let i = 0; i < PHASE_ORDER.length; i++) {
    if (lower.includes(PHASE_ORDER[i].toLowerCase())) {
      return i;
    }
  }
  return -1;
}

export function ProjectListCard({ project }: ProjectListCardProps) {
  const router = useRouter();
  const projectCode = project.project_code;

  // Fetch phases
  const phasesQuery = useQuery({
    queryKey: ["project-phases", projectCode],
    queryFn: () => api.getProjectPhases(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  // Fetch team info
  const teamQuery = useQuery({
    queryKey: ["project-schedule-team", projectCode],
    queryFn: async () => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/projects/${projectCode}/schedule-team`);
      if (!res.ok) return { team: [], schedule: [] };
      return res.json();
    },
    staleTime: 1000 * 60 * 5,
  });

  const phases = phasesQuery.data?.phases ?? [];
  const team = teamQuery.data?.team ?? [];

  // Calculate phase progress
  const completedPhases = phases.filter((p: { status: string }) => p.status === 'completed').length;
  const currentPhase = phases.find((p: { status: string }) => p.status === 'in_progress');
  const currentPhaseIndex = currentPhase ? getPhaseIndex(currentPhase.phase_name) : -1;

  // Progress as percentage through the pipeline
  const totalSteps = PHASE_ORDER.length;
  const currentStep = currentPhaseIndex >= 0 ? currentPhaseIndex + 1 : completedPhases;
  const progressPercent = (currentStep / totalSteps) * 100;

  // Get current phase short name
  const getShortPhaseName = (name: string): string => {
    if (name.toLowerCase().includes("concept")) return "Concept";
    if (name.toLowerCase().includes("schematic")) return "SD";
    if (name.toLowerCase().includes("design dev")) return "DD";
    if (name.toLowerCase().includes("construction doc")) return "CD";
    if (name.toLowerCase().includes("construction obs") || name.toLowerCase().includes("admin")) return "CA";
    if (name.toLowerCase().includes("mobil")) return "Mobilization";
    return name.substring(0, 10);
  };

  const projectName = project.project_title || project.project_name || project.client_name || projectCode;
  const contractValue = project.total_fee_usd || project.contract_value || 0;

  const handleClick = () => {
    router.push(`/projects/${encodeURIComponent(projectCode)}`);
  };

  return (
    <Card
      className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:border-teal-300"
      onClick={handleClick}
    >
      {/* Header: Project Name + PM */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="min-w-0 flex-1">
          <Text className="text-lg font-semibold text-slate-900 truncate">
            {projectName}
          </Text>
          <Text className="text-sm text-slate-500">
            {projectCode} {project.country && `• ${project.country}`}
          </Text>
        </div>
        {project.pm_name && (
          <Badge color="slate" size="sm">
            PM: {project.pm_name}
          </Badge>
        )}
      </div>

      {/* Phase Progress Pipeline */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <Text className="text-xs font-medium text-slate-600">Phase Progress</Text>
          <Badge color="teal" size="sm">
            {currentPhase ? getShortPhaseName(currentPhase.phase_name) : (completedPhases === phases.length && phases.length > 0 ? "Complete" : "—")}
          </Badge>
        </div>

        {/* Phase dots */}
        <div className="flex items-center gap-1 mb-2">
          {PHASE_ORDER.map((phase, idx) => {
            const isCompleted = idx < currentStep;
            const isCurrent = idx === currentStep - 1 && currentPhase;
            return (
              <div
                key={phase}
                className={cn(
                  "flex-1 h-2 rounded-full transition-colors",
                  isCompleted ? "bg-teal-500" : isCurrent ? "bg-teal-300" : "bg-slate-200"
                )}
                title={phase}
              />
            );
          })}
        </div>

        {/* Phase labels */}
        <div className="flex justify-between text-[10px] text-slate-400">
          <span>Concept</span>
          <span>SD</span>
          <span>DD</span>
          <span>CD</span>
          <span>CA</span>
        </div>
      </div>

      {/* Stats Row */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-100">
        {/* Team */}
        <div className="flex items-center gap-1.5 text-slate-600">
          <Users className="h-4 w-4" />
          <span className="text-sm">{team.length || "—"}</span>
        </div>

        {/* Deliverables placeholder */}
        <div className="flex items-center gap-1.5 text-slate-600">
          <FileText className="h-4 w-4" />
          <span className="text-sm">—</span>
        </div>

        {/* Contract Value */}
        <div className="flex items-center gap-1.5 text-slate-600">
          <DollarSign className="h-4 w-4" />
          <span className="text-sm font-medium">
            {contractValue >= 1000000
              ? `$${(contractValue / 1000000).toFixed(1)}M`
              : contractValue >= 1000
                ? `$${Math.round(contractValue / 1000)}K`
                : `$${contractValue.toLocaleString()}`
            }
          </span>
        </div>
      </div>
    </Card>
  );
}

// Skeleton loader
export function ProjectListCardSkeleton() {
  return (
    <Card className="animate-pulse">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex-1">
          <div className="h-5 bg-slate-200 rounded w-3/4 mb-2" />
          <div className="h-4 bg-slate-200 rounded w-1/2" />
        </div>
        <div className="h-6 bg-slate-200 rounded w-20" />
      </div>
      <div className="mb-4">
        <div className="h-3 bg-slate-200 rounded w-24 mb-2" />
        <div className="flex gap-1">
          {[1,2,3,4,5,6].map(i => (
            <div key={i} className="flex-1 h-2 bg-slate-200 rounded-full" />
          ))}
        </div>
      </div>
      <div className="flex justify-between pt-3 border-t border-slate-100">
        <div className="h-4 bg-slate-200 rounded w-12" />
        <div className="h-4 bg-slate-200 rounded w-12" />
        <div className="h-4 bg-slate-200 rounded w-16" />
      </div>
    </Card>
  );
}
