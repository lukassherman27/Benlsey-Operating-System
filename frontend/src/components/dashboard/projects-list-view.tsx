"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Building2,
  Search,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle2,
  AlertTriangle,
  DollarSign,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { useState, useMemo } from "react";

interface ProjectsListViewProps {
  onSelect?: (projectCode: string) => void;
  selectedCode?: string | null;
  className?: string;
}

interface ProjectData {
  project_code: string;
  project_name?: string;
  project_title?: string;
  client_name?: string;
  status?: string;
  current_phase?: string;
  phase?: string;
  pm_name?: string;
  contract_value_usd?: number;
  total_fee_usd?: number;
  paid_to_date_usd?: number;
  total_invoiced?: number;
  outstanding_amount?: number;
  days_since_activity?: number;
  overdue_invoices_count?: number;
}

// Calculate project health based on financial and activity metrics
function calculateProjectHealth(project: ProjectData): {
  score: number;
  status: "healthy" | "at_risk" | "critical";
  issues: string[];
} {
  let score = 100;
  const issues: string[] = [];

  // Payment collection rate
  const contractValue = project.contract_value_usd || project.total_fee_usd || 0;
  const paidAmount = project.paid_to_date_usd || 0;
  const invoicedAmount = project.total_invoiced || 0;
  const outstanding = project.outstanding_amount || (invoicedAmount - paidAmount);

  // Overdue invoices (major red flag)
  if (project.overdue_invoices_count && project.overdue_invoices_count > 0) {
    score -= project.overdue_invoices_count * 15;
    issues.push(`${project.overdue_invoices_count} overdue invoice${project.overdue_invoices_count > 1 ? 's' : ''}`);
  }

  // Large outstanding amount
  if (outstanding > 100000) {
    score -= 10;
    issues.push(`$${Math.round(outstanding / 1000)}K outstanding`);
  }

  // No activity in 30+ days
  if (project.days_since_activity && project.days_since_activity > 30) {
    score -= 10;
    issues.push(`${project.days_since_activity} days inactive`);
  }

  // Collection rate
  if (invoicedAmount > 0) {
    const collectionRate = paidAmount / invoicedAmount;
    if (collectionRate < 0.5) {
      score -= 15;
      issues.push("Low collection rate");
    }
  }

  score = Math.max(0, Math.min(100, score));

  let status: "healthy" | "at_risk" | "critical" = "healthy";
  if (score < 50) status = "critical";
  else if (score < 75) status = "at_risk";

  return { score, status, issues };
}

// Format currency compactly
const formatCurrency = (value?: number | null) => {
  if (value == null || value === 0) return "—";
  if (Math.abs(value) >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${value.toLocaleString()}`;
};

// Status badge component
function StatusBadge({ status }: { status: "healthy" | "at_risk" | "critical" }) {
  const config = {
    healthy: {
      label: "Healthy",
      className: "bg-emerald-100 text-emerald-700 border-emerald-200",
    },
    at_risk: {
      label: "At Risk",
      className: "bg-amber-100 text-amber-700 border-amber-200",
    },
    critical: {
      label: "Critical",
      className: "bg-red-100 text-red-700 border-red-200",
    },
  };

  const { label, className } = config[status];
  return (
    <Badge variant="outline" className={cn("text-xs", className)}>
      {label}
    </Badge>
  );
}

// Group configuration
const GROUP_CONFIG = {
  critical: {
    title: "Needs Attention",
    description: "Projects with overdue invoices or financial issues",
    accent: "border-rose-200 bg-rose-50/80",
    icon: AlertTriangle,
    iconColor: "text-rose-600",
  },
  at_risk: {
    title: "Monitor",
    description: "Projects that may need intervention soon",
    accent: "border-amber-200 bg-amber-50/80",
    icon: Clock,
    iconColor: "text-amber-600",
  },
  healthy: {
    title: "On Track",
    description: "Projects progressing normally",
    accent: "border-emerald-200 bg-emerald-50/80",
    icon: CheckCircle2,
    iconColor: "text-emerald-600",
  },
};

export function ProjectsListView({
  onSelect,
  selectedCode,
  className,
}: ProjectsListViewProps) {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");

  const projectsQuery = useQuery({
    queryKey: ["projects", "active"],
    queryFn: () => api.getActiveProjects(),
    staleTime: 1000 * 60 * 5,
  });

  const projects = projectsQuery.data?.data ?? [];

  // Filter and group projects
  const { grouped, counts } = useMemo(() => {
    const filtered = projects.filter((p: ProjectData) => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      const name = (p.project_name || p.project_title || "").toLowerCase();
      const code = (p.project_code || "").toLowerCase();
      const client = (p.client_name || "").toLowerCase();
      return name.includes(query) || code.includes(query) || client.includes(query);
    });

    const groups: Record<string, ProjectData[]> = {
      critical: [],
      at_risk: [],
      healthy: [],
    };

    filtered.forEach((project: ProjectData) => {
      const health = calculateProjectHealth(project);
      groups[health.status].push(project);
    });

    return {
      grouped: groups,
      counts: {
        critical: groups.critical.length,
        at_risk: groups.at_risk.length,
        healthy: groups.healthy.length,
        total: filtered.length,
      },
    };
  }, [projects, searchQuery]);

  if (projectsQuery.isLoading) {
    return (
      <div className={cn("space-y-4", className)}>
        <Skeleton className="h-10 w-full" />
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    );
  }

  const handleProjectClick = (projectCode: string) => {
    if (onSelect) {
      onSelect(projectCode);
    } else {
      router.push(`/projects/${encodeURIComponent(projectCode)}`);
    }
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Search Header */}
      <div className="p-4 border-b border-slate-200 bg-white">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search projects by name, code, or client..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
          <span>{counts.total} projects</span>
          <span className="text-rose-600">{counts.critical} need attention</span>
          <span className="text-amber-600">{counts.at_risk} to monitor</span>
          <span className="text-emerald-600">{counts.healthy} on track</span>
        </div>
      </div>

      {/* Projects List */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-6">
          {(["critical", "at_risk", "healthy"] as const).map((status) => {
            const group = grouped[status];
            if (group.length === 0) return null;

            const config = GROUP_CONFIG[status];
            const Icon = config.icon;

            return (
              <div key={status} className="space-y-3">
                {/* Group Header */}
                <div className="flex items-center gap-2">
                  <Icon className={cn("h-4 w-4", config.iconColor)} />
                  <h3 className="font-semibold text-slate-900">{config.title}</h3>
                  <Badge variant="secondary" className="text-xs">
                    {group.length}
                  </Badge>
                </div>

                {/* Group Container */}
                <div
                  className={cn(
                    "rounded-xl border p-3 space-y-2",
                    config.accent
                  )}
                >
                  {group.map((project: ProjectData) => {
                    const health = calculateProjectHealth(project);
                    const selected = selectedCode === project.project_code;
                    const projectName = project.project_name || project.project_title || project.project_code;
                    const currentPhase = project.current_phase || project.phase || "—";
                    const contractValue = project.contract_value_usd || project.total_fee_usd || 0;
                    const paidAmount = project.paid_to_date_usd || 0;
                    const paymentPct = contractValue > 0 ? Math.round((paidAmount / contractValue) * 100) : 0;

                    return (
                      <button
                        key={project.project_code}
                        className={cn(
                          "w-full border bg-white p-4 text-left transition rounded-lg hover:shadow-md",
                          selected && "border-slate-900 bg-slate-950 text-white shadow-lg"
                        )}
                        onClick={() => handleProjectClick(project.project_code)}
                      >
                        <div className="flex items-start justify-between gap-4">
                          {/* Left: Project Info */}
                          <div className="space-y-1.5 min-w-0 flex-1">
                            <p
                              className={cn(
                                "text-base font-semibold truncate",
                                selected ? "text-white" : "text-slate-900"
                              )}
                            >
                              {projectName}
                            </p>
                            <p
                              className={cn(
                                "text-sm truncate",
                                selected ? "text-white/70" : "text-slate-500"
                              )}
                            >
                              {project.client_name || "Unknown client"}
                            </p>
                            <div className="flex flex-wrap gap-2 mt-2">
                              <Badge
                                variant={selected ? "secondary" : "outline"}
                                className="rounded-full text-xs font-mono"
                              >
                                {project.project_code}
                              </Badge>
                              <Badge
                                variant="outline"
                                className={cn(
                                  "rounded-full text-xs",
                                  selected && "border-white/30 text-white/80"
                                )}
                              >
                                {currentPhase}
                              </Badge>
                              {project.pm_name && (
                                <Badge
                                  variant="outline"
                                  className={cn(
                                    "rounded-full text-xs",
                                    selected && "border-white/30 text-white/80"
                                  )}
                                >
                                  PM: {project.pm_name}
                                </Badge>
                              )}
                            </div>
                          </div>

                          {/* Right: Metrics */}
                          <div className="text-right flex-shrink-0">
                            <p
                              className={cn(
                                "text-xs uppercase tracking-wider",
                                selected ? "text-white/60" : "text-slate-400"
                              )}
                            >
                              Contract
                            </p>
                            <p
                              className={cn(
                                "text-xl font-bold",
                                selected ? "text-white" : "text-slate-900"
                              )}
                            >
                              {formatCurrency(contractValue)}
                            </p>
                            <div className="flex items-center gap-1 mt-1 justify-end">
                              <span
                                className={cn(
                                  "text-xs",
                                  selected ? "text-white/70" : "text-emerald-600"
                                )}
                              >
                                {paymentPct}% collected
                              </span>
                            </div>
                            <div className="mt-2">
                              <StatusBadge status={health.status} />
                            </div>
                          </div>
                        </div>

                        {/* Issues row (if any) */}
                        {health.issues.length > 0 && !selected && (
                          <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap gap-2">
                            {health.issues.slice(0, 3).map((issue, idx) => (
                              <span
                                key={idx}
                                className="text-xs text-rose-600 bg-rose-50 px-2 py-0.5 rounded"
                              >
                                {issue}
                              </span>
                            ))}
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {counts.total === 0 && (
            <div className="text-center py-12">
              <Building2 className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600 font-medium">No projects found</p>
              <p className="text-sm text-slate-400 mt-1">
                {searchQuery
                  ? "Try a different search term"
                  : "Projects will appear here once contracts are signed"}
              </p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
