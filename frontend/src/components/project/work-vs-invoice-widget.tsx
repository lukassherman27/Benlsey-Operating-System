"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface WorkVsInvoiceWidgetProps {
  projectCode: string;
  className?: string;
}

const formatCurrency = (value: number) => {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${value.toLocaleString()}`;
};

// Standard phases in order
const PHASE_ORDER = ["Mobilization", "Concept Design", "Schematic Design", "Design Development", "Construction Documents", "Contract Administration"];
const PHASE_SHORT: Record<string, string> = {
  "Mobilization": "MOB",
  "Concept Design": "CD",
  "Schematic Design": "SD",
  "Design Development": "DD",
  "Construction Documents": "CDs",
  "Contract Administration": "CA",
};

export function WorkVsInvoiceWidget({ projectCode, className }: WorkVsInvoiceWidgetProps) {
  // Get phase data
  const phasesQuery = useQuery({
    queryKey: ["project-phases", projectCode],
    queryFn: () => api.getProjectPhases(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  // Get schedule data for work days
  const scheduleQuery = useQuery({
    queryKey: ["project-schedule", projectCode, 365], // Full year
    queryFn: () => api.getProjectSchedule(projectCode, 365),
    staleTime: 1000 * 60 * 5,
  });

  const isLoading = phasesQuery.isLoading || scheduleQuery.isLoading;

  if (isLoading) {
    return (
      <Card className={cn("border-slate-200", className)}>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Work vs Invoice Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-48 w-full" />
        </CardContent>
      </Card>
    );
  }

  const phases = phasesQuery.data?.phases || [];
  const scheduleEntries = scheduleQuery.data?.entries || [];

  // Count work days by phase
  const workDaysByPhase: Record<string, number> = {};
  scheduleEntries.forEach((entry: { phase?: string }) => {
    const phase = entry.phase || "";
    if (!workDaysByPhase[phase]) workDaysByPhase[phase] = 0;
    workDaysByPhase[phase]++;
  });

  // Aggregate by phase (across all disciplines)
  const phaseAggregates: Record<string, {
    totalFee: number;
    totalInvoiced: number;
    totalPaid: number;
    workDays: number;
  }> = {};

  phases.forEach((p: { phase_name: string; phase_fee_usd?: number; percentage_invoiced?: number; percentage_paid?: number }) => {
    const phaseName = p.phase_name;
    if (!phaseAggregates[phaseName]) {
      phaseAggregates[phaseName] = { totalFee: 0, totalInvoiced: 0, totalPaid: 0, workDays: 0 };
    }
    const fee = p.phase_fee_usd || 0;
    const invoicedPct = p.percentage_invoiced || 0;
    const paidPct = p.percentage_paid || 0;

    phaseAggregates[phaseName].totalFee += fee;
    phaseAggregates[phaseName].totalInvoiced += fee * (invoicedPct / 100);
    phaseAggregates[phaseName].totalPaid += fee * (paidPct / 100);
  });

  // Match work days to phases (fuzzy match)
  Object.entries(workDaysByPhase).forEach(([phase, days]) => {
    const matchingPhase = Object.keys(phaseAggregates).find(p =>
      p.toLowerCase().includes(phase.toLowerCase()) ||
      phase.toLowerCase().includes(p.split(' ')[0].toLowerCase())
    );
    if (matchingPhase) {
      phaseAggregates[matchingPhase].workDays = days;
    }
  });

  // Build phase data array
  const sortedPhases = PHASE_ORDER
    .filter(p => phaseAggregates[p])
    .map(phaseName => {
      const agg = phaseAggregates[phaseName];

      // Estimate work % based on work days relative to expected
      // Simple heuristic: if we have work days, assume some % complete
      let workPct = 0;
      if (agg.totalPaid >= agg.totalFee * 0.9) {
        workPct = 100; // Fully paid = work complete
      } else if (agg.workDays > 0) {
        // If there are work days but not paid, estimate progress
        // This is a rough estimate - real data would come from PM
        workPct = Math.min(90, Math.max(20, agg.workDays * 2)); // 2% per work day, cap at 90%
      }

      const invoicePct = agg.totalFee > 0 ? (agg.totalInvoiced / agg.totalFee) * 100 : 0;
      const gap = workPct - invoicePct;
      const underInvoiced = gap > 0 ? (gap / 100) * agg.totalFee : 0;

      return {
        name: phaseName,
        shortName: PHASE_SHORT[phaseName] || phaseName.slice(0, 3),
        fee: agg.totalFee,
        invoiced: agg.totalInvoiced,
        paid: agg.totalPaid,
        invoicePct,
        paidPct: agg.totalFee > 0 ? (agg.totalPaid / agg.totalFee) * 100 : 0,
        workPct,
        workDays: agg.workDays,
        gap,
        underInvoiced,
        status: gap > 20 ? "under" : gap < -20 ? "over" : "balanced",
      };
    });

  // Calculate totals from sorted phases
  const totalFee = sortedPhases.reduce((sum, p) => sum + p.fee, 0);
  const totalInvoiced = sortedPhases.reduce((sum, p) => sum + p.invoiced, 0);
  const totalPaid = sortedPhases.reduce((sum, p) => sum + p.paid, 0);
  const underInvoicedAmount = sortedPhases.reduce((sum, p) => sum + p.underInvoiced, 0);

  const overallInvoicePct = totalFee > 0 ? (totalInvoiced / totalFee) * 100 : 0;
  const overallPaidPct = totalFee > 0 ? (totalPaid / totalFee) * 100 : 0;

  return (
    <Card className={cn("border-slate-200", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-blue-600" />
            Work vs Invoice Progress
          </CardTitle>
          {underInvoicedAmount > 0 && (
            <Badge variant="destructive" className="text-xs">
              {formatCurrency(underInvoicedAmount)} under-invoiced
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {/* Summary Banner */}
        {underInvoicedAmount > 0 && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-800">
                  Work ahead of invoicing
                </p>
                <p className="text-xs text-red-600 mt-0.5">
                  More work done than invoiced. Time to send invoices!
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Phase Comparison */}
        <div className="space-y-3">
          {sortedPhases.map((phase) => (
            <div key={phase.name} className="space-y-1">
              {/* Phase Header */}
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-slate-900 w-8">{phase.shortName}</span>
                  <span className="text-slate-500 text-xs">{formatCurrency(phase.fee)}</span>
                </div>
                <div className="flex items-center gap-2">
                  {phase.workDays > 0 && (
                    <span className="text-xs text-slate-500">{phase.workDays} work days</span>
                  )}
                  {phase.status === "under" && (
                    <Badge variant="outline" className="text-xs bg-red-50 text-red-700 border-red-200">
                      Under-invoiced
                    </Badge>
                  )}
                  {phase.status === "over" && (
                    <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                      Over-invoiced
                    </Badge>
                  )}
                  {phase.status === "balanced" && phase.invoicePct > 0 && (
                    <Badge variant="outline" className="text-xs bg-emerald-50 text-emerald-700 border-emerald-200">
                      Balanced
                    </Badge>
                  )}
                </div>
              </div>

              {/* Dual Progress Bars */}
              <div className="space-y-1">
                {/* Work Progress */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 w-14">Work</span>
                  <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all"
                      style={{ width: `${Math.min(phase.workPct, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-600 w-10 text-right">
                    {Math.round(phase.workPct)}%
                  </span>
                </div>
                {/* Invoice Progress */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 w-14">Invoice</span>
                  <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all",
                        phase.invoicePct >= phase.workPct ? "bg-emerald-500" : "bg-amber-400"
                      )}
                      style={{ width: `${Math.min(phase.invoicePct, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-600 w-10 text-right">
                    {Math.round(phase.invoicePct)}%
                  </span>
                </div>
                {/* Paid Progress */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 w-14">Paid</span>
                  <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-600 rounded-full transition-all"
                      style={{ width: `${Math.min(phase.paidPct, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-600 w-10 text-right">
                    {Math.round(phase.paidPct)}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Overall Summary */}
        <div className="mt-4 pt-4 border-t border-slate-100">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wide">Total Fee</p>
              <p className="text-lg font-bold text-slate-900">{formatCurrency(totalFee)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wide">Invoiced</p>
              <p className="text-lg font-bold text-amber-600">{Math.round(overallInvoicePct)}%</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wide">Collected</p>
              <p className="text-lg font-bold text-emerald-600">{Math.round(overallPaidPct)}%</p>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="mt-3 flex items-center justify-center gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-blue-500" /> Work Done
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-amber-400" /> Invoiced
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-emerald-600" /> Paid
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
