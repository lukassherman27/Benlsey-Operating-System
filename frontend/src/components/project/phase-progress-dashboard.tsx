"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Building2,
  Palette,
  Trees,
  Megaphone,
  CheckCircle2,
  Clock,
  Circle
} from "lucide-react";
import { cn } from "@/lib/utils";

interface PhaseProgressDashboardProps {
  projectCode: string;
  className?: string;
}

const PHASE_ORDER = [
  "Mobilization",
  "Concept Design",
  "Schematic Design",
  "Design Development",
  "Construction Documents",
  "Contract Administration",
  "Construction Observation"
];

const PHASE_SHORT = {
  "Mobilization": "MOB",
  "Concept Design": "CD",
  "Schematic Design": "SD",
  "Design Development": "DD",
  "Construction Documents": "CDs",
  "Contract Administration": "CA",
  "Construction Observation": "CO"
};

const DISCIPLINE_ICONS: Record<string, React.ReactNode> = {
  "Architectural": <Building2 className="h-4 w-4" />,
  "Interior": <Palette className="h-4 w-4" />,
  "Landscape": <Trees className="h-4 w-4" />,
  "Branding Consultancy": <Megaphone className="h-4 w-4" />,
};

const DISCIPLINE_COLORS: Record<string, string> = {
  "Architectural": "text-blue-600",
  "Interior": "text-purple-600",
  "Landscape": "text-green-600",
  "Branding Consultancy": "text-orange-600",
};

const formatCurrency = (value: number) => {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${value.toLocaleString()}`;
};

interface Phase {
  phase_name: string;
  phase_fee_usd: number;
  percentage_invoiced: number;
  percentage_paid: number;
  status: string;
}

interface DisciplineData {
  name: string;
  phases: Phase[];
  totalFee: number;
  totalPaid: number;
  currentPhase: string;
}

export function PhaseProgressDashboard({ projectCode, className }: PhaseProgressDashboardProps) {
  const phasesQuery = useQuery({
    queryKey: ["project-phases", projectCode],
    queryFn: () => api.getProjectPhases(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  if (phasesQuery.isLoading) {
    return (
      <Card className={cn("border-slate-200", className)}>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Phase Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-12 w-full" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const byDiscipline = phasesQuery.data?.by_discipline || {};

  // Process disciplines
  const disciplines: DisciplineData[] = Object.entries(byDiscipline)
    .filter(([name]) => name !== "Unknown")
    .map(([name, phases]) => {
      const phaseList = phases as unknown as Phase[];
      const totalFee = phaseList.reduce((sum, p) => sum + (p.phase_fee_usd || 0), 0);
      const totalPaid = phaseList.reduce((sum, p) => {
        const fee = p.phase_fee_usd || 0;
        const paidPct = p.percentage_paid || 0;
        return sum + (fee * paidPct / 100);
      }, 0);

      // Find current phase (first one that's in_progress or last completed)
      let currentPhase = "Not Started";
      for (const phase of phaseList) {
        if (phase.status === "in_progress") {
          currentPhase = phase.phase_name;
          break;
        }
        if (phase.status === "completed") {
          currentPhase = phase.phase_name;
        }
      }

      return { name, phases: phaseList, totalFee, totalPaid, currentPhase };
    })
    .sort((a, b) => b.totalFee - a.totalFee); // Sort by fee size

  if (disciplines.length === 0) {
    return (
      <Card className={cn("border-slate-200", className)}>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Phase Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500 text-center py-8">
            No phase data available for this project
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("border-slate-200", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Phase Progress by Discipline</CardTitle>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
              Paid
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
              Invoiced
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2.5 w-2.5 rounded-full bg-slate-200" />
              Pending
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-6">
          {disciplines.map((discipline) => (
            <DisciplineRow key={discipline.name} discipline={discipline} />
          ))}
        </div>

        {/* Summary */}
        <div className="mt-6 pt-4 border-t border-slate-100">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-500">Total Contract Value</span>
            <span className="font-semibold text-slate-900">
              {formatCurrency(disciplines.reduce((sum, d) => sum + d.totalFee, 0))}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm mt-1">
            <span className="text-slate-500">Total Collected</span>
            <span className="font-semibold text-emerald-600">
              {formatCurrency(disciplines.reduce((sum, d) => sum + d.totalPaid, 0))}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function DisciplineRow({ discipline }: { discipline: DisciplineData }) {
  const icon = DISCIPLINE_ICONS[discipline.name] || <Building2 className="h-4 w-4" />;
  const colorClass = DISCIPLINE_COLORS[discipline.name] || "text-slate-600";

  // Sort phases by standard order
  const sortedPhases = [...discipline.phases].sort((a, b) => {
    const aIdx = PHASE_ORDER.indexOf(a.phase_name);
    const bIdx = PHASE_ORDER.indexOf(b.phase_name);
    return (aIdx === -1 ? 99 : aIdx) - (bIdx === -1 ? 99 : bIdx);
  });

  const paidPct = discipline.totalFee > 0
    ? Math.round((discipline.totalPaid / discipline.totalFee) * 100)
    : 0;

  return (
    <div>
      {/* Discipline Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={colorClass}>{icon}</span>
          <span className="font-medium text-sm text-slate-900">{discipline.name}</span>
          <Badge variant="outline" className="text-xs px-1.5 py-0 font-normal">
            {discipline.currentPhase}
          </Badge>
        </div>
        <div className="text-right">
          <span className="text-sm font-semibold text-slate-900">
            {formatCurrency(discipline.totalFee)}
          </span>
          <span className="text-xs text-emerald-600 ml-2">
            {paidPct}% paid
          </span>
        </div>
      </div>

      {/* Phase Timeline */}
      <div className="flex gap-1">
        {sortedPhases.map((phase, idx) => {
          const shortName = PHASE_SHORT[phase.phase_name as keyof typeof PHASE_SHORT] || phase.phase_name.slice(0, 3);
          const paidPct = phase.percentage_paid || 0;
          const invoicedPct = phase.percentage_invoiced || 0;

          // Determine status
          let bgColor = "bg-slate-100"; // pending
          let textColor = "text-slate-400";
          let statusIcon = <Circle className="h-3 w-3" />;

          if (paidPct >= 95) {
            bgColor = "bg-emerald-500";
            textColor = "text-white";
            statusIcon = <CheckCircle2 className="h-3 w-3" />;
          } else if (invoicedPct > 0 || paidPct > 0) {
            bgColor = "bg-amber-400";
            textColor = "text-amber-900";
            statusIcon = <Clock className="h-3 w-3" />;
          }

          return (
            <div
              key={phase.phase_name}
              className={cn(
                "flex-1 rounded-md p-2 transition-all cursor-default group relative",
                bgColor
              )}
            >
              <div className={cn("text-center", textColor)}>
                <div className="flex items-center justify-center gap-1 mb-0.5">
                  {statusIcon}
                </div>
                <div className="text-xs font-medium">{shortName}</div>
                <div className="text-[10px] opacity-75">
                  {formatCurrency(phase.phase_fee_usd || 0)}
                </div>
              </div>

              {/* Tooltip on hover */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                <div className="font-medium">{phase.phase_name}</div>
                <div>Fee: {formatCurrency(phase.phase_fee_usd || 0)}</div>
                <div>Invoiced: {Math.round(invoicedPct)}%</div>
                <div>Paid: {Math.round(paidPct)}%</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
