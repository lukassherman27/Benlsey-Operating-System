"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import {
  Home,
  ChevronDown,
  ChevronUp,
  DollarSign,
  Mail,
  CheckCircle2,
  Clock,
} from "lucide-react";
import { format } from "date-fns";

interface PersonalProject {
  id: string;
  name: string;
  type: "property" | "investment" | "personal";
  status: string;
  summary?: string;
  nextAction?: string;
  nextActionDate?: string;
  financials?: {
    invested?: number;
    current_value?: number;
    pnl?: number;
    pnl_ytd?: number;
  };
  lastActivity?: string;
  email_count?: number;
}

interface PersonalProjectsWidgetProps {
  className?: string;
  defaultVisible?: boolean;
}

export function PersonalProjectsWidget({
  className,
  defaultVisible = false,
}: PersonalProjectsWidgetProps) {
  const [visible, setVisible] = useState(defaultVisible);
  const [expanded, setExpanded] = useState(true);

  // Fetch personal projects data
  const { data, isLoading } = useQuery({
    queryKey: ["personal-projects"],
    queryFn: async () => {
      // This would be a real API call in production
      // For now, return mock data that matches known personal projects
      return {
        projects: [
          {
            id: "bali-land",
            name: "Bali Land Sale",
            type: "property" as const,
            status: "In Progress",
            summary: "Awaiting survey results from land office",
            nextAction: "Call agent to follow up on survey",
            nextActionDate: "2024-12-20",
            financials: {
              invested: 250000,
              current_value: 320000,
              pnl: 70000,
            },
            lastActivity: "2024-12-15",
            email_count: 12,
          },
          {
            id: "shinta-mani-wild",
            name: "Shinta Mani Wild",
            type: "investment" as const,
            status: "Active",
            summary: "All invoices current",
            financials: {
              invested: 500000,
              current_value: 627000,
              pnl_ytd: 127000,
            },
            lastActivity: "2024-12-10",
            email_count: 45,
          },
        ] as PersonalProject[],
      };
    },
    staleTime: 1000 * 60 * 10, // 10 minutes
    enabled: visible,
  });

  // Don't render anything if not visible
  if (!visible) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setVisible(true)}
          className="text-xs text-slate-500 hover:text-slate-700"
        >
          <Home className="h-3.5 w-3.5 mr-1" />
          Show Personal Projects
        </Button>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white overflow-hidden",
        className
      )}
    >
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            <Home className="h-5 w-5 text-teal-600" />
            <h3 className="font-semibold text-slate-800">Personal Projects</h3>
            {expanded ? (
              <ChevronUp className="h-4 w-4 text-slate-400" />
            ) : (
              <ChevronDown className="h-4 w-4 text-slate-400" />
            )}
          </button>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">Show</span>
            <Switch
              checked={visible}
              onCheckedChange={setVisible}
              className="data-[state=checked]:bg-teal-600"
            />
          </div>
        </div>
      </div>

      {/* Content */}
      {expanded && (
        <div className="p-4">
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : data?.projects && data.projects.length > 0 ? (
            <div className="space-y-3">
              {data.projects.map((project) => (
                <PersonalProjectCard key={project.id} project={project} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-4">
              No personal projects found
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function PersonalProjectCard({ project }: { project: PersonalProject }) {
  const typeConfig = {
    property: { icon: Home, color: "text-amber-600", bg: "bg-amber-50" },
    investment: { icon: DollarSign, color: "text-emerald-600", bg: "bg-emerald-50" },
    personal: { icon: CheckCircle2, color: "text-blue-600", bg: "bg-blue-50" },
  };

  const config = typeConfig[project.type] || typeConfig.personal;
  const Icon = config.icon;

  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    return `$${(value / 1000).toFixed(0)}K`;
  };

  const formatPnL = (value: number) => {
    const formatted = formatCurrency(Math.abs(value));
    return value >= 0 ? `+${formatted}` : `-${formatted}`;
  };

  return (
    <div className="p-4 rounded-lg border border-slate-100 bg-white hover:shadow-sm transition-shadow">
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className={cn("p-2 rounded-lg shrink-0", config.bg)}>
          <Icon className={cn("h-5 w-5", config.color)} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <h4 className="font-semibold text-slate-800 truncate">
              {project.name}
            </h4>
            <Badge
              variant="outline"
              className={cn(
                "text-xs shrink-0",
                project.status === "Active" || project.status === "In Progress"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-slate-50 text-slate-600 border-slate-200"
              )}
            >
              {project.status}
            </Badge>
          </div>

          {project.summary && (
            <p className="text-sm text-slate-600 mb-2">{project.summary}</p>
          )}

          {/* Next Action */}
          {project.nextAction && (
            <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
              <Clock className="h-3 w-3" />
              <span>
                Next: {project.nextAction}
                {project.nextActionDate && (
                  <span className="text-slate-400 ml-1">
                    ({format(new Date(project.nextActionDate), "MMM d")})
                  </span>
                )}
              </span>
            </div>
          )}

          {/* Financials */}
          {project.financials && (
            <div className="flex items-center gap-4 text-xs mt-2 pt-2 border-t border-slate-100">
              {project.financials.pnl !== undefined && (
                <div className="flex items-center gap-1">
                  <span className="text-slate-500">P&L:</span>
                  <span
                    className={cn(
                      "font-semibold",
                      project.financials.pnl >= 0
                        ? "text-emerald-600"
                        : "text-red-600"
                    )}
                  >
                    {formatPnL(project.financials.pnl)}
                  </span>
                </div>
              )}
              {project.financials.pnl_ytd !== undefined && (
                <div className="flex items-center gap-1">
                  <span className="text-slate-500">YTD:</span>
                  <span
                    className={cn(
                      "font-semibold",
                      project.financials.pnl_ytd >= 0
                        ? "text-emerald-600"
                        : "text-red-600"
                    )}
                  >
                    {formatPnL(project.financials.pnl_ytd)}
                  </span>
                </div>
              )}
              {project.email_count && (
                <div className="flex items-center gap-1 text-slate-400">
                  <Mail className="h-3 w-3" />
                  <span>{project.email_count} emails</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
