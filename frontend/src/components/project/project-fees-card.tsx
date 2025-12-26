"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Wallet, ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { api } from "@/lib/api";

interface FeeBreakdown {
  breakdown_id: string;
  discipline: string;
  phase: string;
  phase_fee_usd: number;
  total_invoiced: number;
  total_paid: number;
  percentage_of_total?: number;
}

interface FeeBreakdownResponse {
  success: boolean;
  project_code: string;
  breakdowns: FeeBreakdown[];
  summary?: {
    total_breakdown_fee: number;
    total_invoiced: number;
    total_paid: number;
    total_outstanding: number;
    remaining_to_invoice: number;
    percentage_invoiced: number;
    percentage_paid: number;
  };
}

interface ProjectFeesCardProps {
  projectCode: string;
  contractValue?: number;
}

const formatCurrency = (value?: number | null) => {
  if (value == null) return "$0";
  if (Math.abs(value) >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(2)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `$${(value / 1_000).toFixed(1)}K`;
  }
  return `$${value.toLocaleString()}`;
};

const DISCIPLINE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  "Landscape Architecture": { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" },
  "Interior Design": { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200" },
  "Architecture": { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
  "Landscape": { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" },
  "Interior": { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200" },
  "Other": { bg: "bg-slate-50", text: "text-slate-700", border: "border-slate-200" },
};

const getDisciplineColor = (discipline: string) => {
  return DISCIPLINE_COLORS[discipline] || DISCIPLINE_COLORS["Other"];
};

// Standard phase order: Mobilization → Concept → Schematic → DD → CD → CA
const PHASE_ORDER = [
  'Mobilization',
  'Concept Design',
  'Concept',
  'Schematic Design',
  'Schematic',
  'Design Development',
  'Construction Documents',
  'Construction Drawings',
  'Construction Observation',
  'Construction Administration',
  'Additional Services',
];

const getPhaseIndex = (phaseName: string): number => {
  const lowerPhase = phaseName.toLowerCase();
  const index = PHASE_ORDER.findIndex(p =>
    lowerPhase.includes(p.toLowerCase()) || p.toLowerCase().includes(lowerPhase)
  );
  return index === -1 ? 999 : index;
};

const sortPhases = (phases: FeeBreakdown[]): FeeBreakdown[] => {
  return [...phases].sort((a, b) => getPhaseIndex(a.phase) - getPhaseIndex(b.phase));
};

export function ProjectFeesCard({ projectCode, contractValue = 0 }: ProjectFeesCardProps) {
  const [expandedDiscipline, setExpandedDiscipline] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery<FeeBreakdownResponse>({
    queryKey: ["fee-breakdown", projectCode],
    queryFn: () => api.getProjectFeeBreakdowns(projectCode),
  });

  if (isLoading) {
    return (
      <Card className={ds.cards.default}>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-5 w-32 bg-slate-200 rounded" />
            <div className="h-8 w-24 bg-slate-200 rounded" />
            <div className="space-y-2">
              <div className="h-4 w-full bg-slate-200 rounded" />
              <div className="h-4 w-3/4 bg-slate-200 rounded" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={ds.cards.default}>
        <CardContent className="p-6">
          <p className="text-sm text-slate-500">Could not load fee breakdown</p>
        </CardContent>
      </Card>
    );
  }

  const breakdowns = data?.breakdowns || [];
  const summary = data?.summary;

  // Group breakdowns by discipline
  const byDiscipline = breakdowns.reduce((acc, bd) => {
    const disc = bd.discipline || "Other";
    if (!acc[disc]) {
      acc[disc] = {
        total_fee: 0,
        total_invoiced: 0,
        total_paid: 0,
        phases: [],
      };
    }
    acc[disc].total_fee += bd.phase_fee_usd || 0;
    acc[disc].total_invoiced += bd.total_invoiced || 0;
    acc[disc].total_paid += bd.total_paid || 0;
    acc[disc].phases.push(bd);
    return acc;
  }, {} as Record<string, { total_fee: number; total_invoiced: number; total_paid: number; phases: FeeBreakdown[] }>);

  const totalFee = summary?.total_breakdown_fee || contractValue || Object.values(byDiscipline).reduce((sum, d) => sum + d.total_fee, 0);
  const totalInvoiced = summary?.total_invoiced || Object.values(byDiscipline).reduce((sum, d) => sum + d.total_invoiced, 0);
  const percentInvoiced = totalFee > 0 ? Math.round((totalInvoiced / totalFee) * 100) : 0;

  return (
    <Card className={ds.cards.default}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Wallet className="h-4 w-4 text-teal-600" />
          Fees & Scope
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {/* Summary */}
        <div className="mb-4">
          <div className="flex items-baseline justify-between">
            <span className={ds.typography.metricLarge}>{formatCurrency(totalFee)}</span>
            <span className="text-sm text-slate-500">{percentInvoiced}% invoiced</span>
          </div>
          {/* Progress bar */}
          <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-gradient-to-r from-teal-500 to-teal-600 transition-all"
              style={{ width: `${Math.min(percentInvoiced, 100)}%` }}
            />
          </div>
        </div>

        {/* Discipline breakdown */}
        {Object.keys(byDiscipline).length === 0 ? (
          <p className="text-sm text-slate-500">No fee breakdown available</p>
        ) : (
          <div className="space-y-2">
            {Object.entries(byDiscipline).map(([discipline, data]) => {
              const colors = getDisciplineColor(discipline);
              const isExpanded = expandedDiscipline === discipline;
              const disciplinePercent = totalFee > 0 ? Math.round((data.total_fee / totalFee) * 100) : 0;
              const invoicedPercent = data.total_fee > 0 ? Math.round((data.total_invoiced / data.total_fee) * 100) : 0;

              return (
                <div key={discipline} className={cn("rounded-lg border", colors.border)}>
                  <button
                    onClick={() => setExpandedDiscipline(isExpanded ? null : discipline)}
                    className={cn(
                      "w-full flex items-center justify-between p-3 rounded-lg transition-colors",
                      colors.bg,
                      "hover:opacity-90"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      {isExpanded ? (
                        <ChevronDown className={cn("h-4 w-4", colors.text)} />
                      ) : (
                        <ChevronRight className={cn("h-4 w-4", colors.text)} />
                      )}
                      <span className={cn("text-sm font-medium", colors.text)}>
                        {discipline}
                      </span>
                      <Badge variant="outline" className={cn("text-xs", colors.bg, colors.text)}>
                        {disciplinePercent}%
                      </Badge>
                    </div>
                    <div className="text-right">
                      <p className={cn("text-sm font-semibold", colors.text)}>
                        {formatCurrency(data.total_fee)}
                      </p>
                      <p className="text-xs text-slate-500">
                        {invoicedPercent}% invoiced
                      </p>
                    </div>
                  </button>

                  {/* Expanded phases - sorted in correct order */}
                  {isExpanded && data.phases.length > 0 && (
                    <div className="px-3 pb-3 space-y-2">
                      {sortPhases(data.phases).map((phase) => {
                        const phaseInvoicedPct = phase.phase_fee_usd > 0
                          ? Math.round((phase.total_invoiced / phase.phase_fee_usd) * 100)
                          : 0;
                        const phasePaidPct = phase.phase_fee_usd > 0
                          ? Math.round((phase.total_paid / phase.phase_fee_usd) * 100)
                          : 0;
                        return (
                          <div
                            key={phase.breakdown_id}
                            className="py-2 px-3 rounded-lg bg-white border border-slate-100"
                          >
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-sm font-medium text-slate-700">{phase.phase}</span>
                              <span className="text-sm font-semibold text-slate-900">
                                {formatCurrency(phase.phase_fee_usd)}
                              </span>
                            </div>
                            {/* Phase progress bar */}
                            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                              {/* Paid portion (darker) */}
                              <div className="h-full flex">
                                <div
                                  className={cn("h-full transition-all", colors.bg.replace("-50", "-500"))}
                                  style={{ width: `${Math.min(phasePaidPct, 100)}%` }}
                                />
                                {/* Invoiced but unpaid (lighter) */}
                                <div
                                  className={cn("h-full transition-all", colors.bg.replace("-50", "-300"))}
                                  style={{ width: `${Math.min(Math.max(phaseInvoicedPct - phasePaidPct, 0), 100 - phasePaidPct)}%` }}
                                />
                              </div>
                            </div>
                            {/* Stats row */}
                            <div className="flex items-center justify-between mt-1.5 text-xs text-slate-500">
                              <span>{phaseInvoicedPct}% invoiced</span>
                              <span>{phasePaidPct}% paid</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
