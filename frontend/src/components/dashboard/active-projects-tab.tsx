"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

import { useState } from "react";
import { formatCurrency, cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { ds } from "@/lib/design-system";
import { TrendingUp, DollarSign, FileText, Clock, AlertTriangle, CheckCircle } from "lucide-react";

import { DisciplineBreakdown, ProjectPhase, PhaseInvoice } from "@/lib/types";

// Define phase ordering at top level
const PHASE_ORDER: Record<string, number> = {
  "Mobilization": 1,
  "Concept Design": 2,
  "Schematic Design": 3,
  "Design Development": 4,
  "Construction Documents": 5,
  "Construction Administration": 6,
  "Construction Observation": 7,
  "Additional Services": 8,
  "Branding": 9,
  "Closeout": 10,
};

// Get phase order for sorting
function getPhaseOrder(phase: string | null | undefined): number {
  if (!phase) return 99;
  // Check for partial matches
  for (const [key, order] of Object.entries(PHASE_ORDER)) {
    if (phase.toLowerCase().includes(key.toLowerCase())) {
      return order;
    }
  }
  return 99;
}

// Get phase badge color
function getPhaseColor(phase: string | null | undefined): string {
  const order = getPhaseOrder(phase);
  if (order <= 2) return "bg-blue-50 text-blue-700 border-blue-200";
  if (order <= 4) return "bg-purple-50 text-purple-700 border-purple-200";
  if (order <= 6) return "bg-amber-50 text-amber-700 border-amber-200";
  if (order <= 8) return "bg-emerald-50 text-emerald-700 border-emerald-200";
  return "bg-slate-50 text-slate-700 border-slate-200";
}

export default function ActiveProjectsTab() {
  const projectsQuery = useQuery({
    queryKey: ["active-projects"],
    queryFn: () => api.getActiveProjects(),
    refetchInterval: 1000 * 60 * 5,
  });

  // Sort projects by phase order (Mobilization first)
  const sortedProjects = useMemo(() => {
    if (!projectsQuery.data?.data) return [];
    return [...projectsQuery.data.data].sort((a: Record<string, unknown>, b: Record<string, unknown>) => {
      const aPhase = getPhaseOrder(a.current_phase as string);
      const bPhase = getPhaseOrder(b.current_phase as string);
      return aPhase - bPhase;
    });
  }, [projectsQuery.data?.data]);

  // Calculate summary metrics
  const summary = useMemo(() => {
    if (!sortedProjects.length) return null;

    const totalContractValue = sortedProjects.reduce((sum, p) => sum + ((p.contract_value as number) || 0), 0);
    const totalInvoiced = sortedProjects.reduce((sum, p) => sum + ((p.total_invoiced as number) || 0), 0);
    const totalPaid = sortedProjects.reduce((sum, p) => sum + ((p.total_paid as number) || 0), 0);
    const totalOutstanding = totalInvoiced - totalPaid;
    const avgProgress = totalContractValue > 0 ? (totalInvoiced / totalContractValue) * 100 : 0;

    // Count projects by payment status
    const overdueCount = sortedProjects.filter(p => (p.payment_status as string) === 'overdue').length;
    const paidCount = sortedProjects.filter(p => (p.payment_status as string) === 'paid').length;

    return {
      projectCount: sortedProjects.length,
      totalContractValue,
      totalInvoiced,
      totalPaid,
      totalOutstanding,
      avgProgress,
      overdueCount,
      paidCount,
    };
  }, [sortedProjects]);

  return (
    <div className="space-y-6">
      {/* Business Health Summary Bar */}
      {summary && (
        <Card className={cn(ds.borderRadius.cardLarge, "border-blue-200 bg-gradient-to-r from-blue-50 to-slate-50")}>
          <CardContent className="p-6">
            <div className="mb-4">
              <p className="text-sm uppercase tracking-[0.3em] text-blue-600 font-medium">
                Business Health Overview
              </p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {/* Active Projects */}
              <div className="p-3 bg-white rounded-xl border border-slate-200">
                <div className="flex items-center gap-2 mb-1">
                  <FileText className="h-4 w-4 text-blue-600" />
                  <span className="text-xs text-slate-500">Active Projects</span>
                </div>
                <p className="text-2xl font-bold text-slate-900">{summary.projectCount}</p>
              </div>

              {/* Total Contract Value */}
              <div className="p-3 bg-white rounded-xl border border-slate-200">
                <div className="flex items-center gap-2 mb-1">
                  <DollarSign className="h-4 w-4 text-emerald-600" />
                  <span className="text-xs text-slate-500">Contract Value</span>
                </div>
                <p className="text-2xl font-bold text-slate-900">
                  ${(summary.totalContractValue / 1000000).toFixed(1)}M
                </p>
              </div>

              {/* Total Invoiced */}
              <div className="p-3 bg-white rounded-xl border border-slate-200">
                <div className="flex items-center gap-2 mb-1">
                  <FileText className="h-4 w-4 text-purple-600" />
                  <span className="text-xs text-slate-500">Total Invoiced</span>
                </div>
                <p className="text-2xl font-bold text-slate-900">
                  ${(summary.totalInvoiced / 1000000).toFixed(1)}M
                </p>
              </div>

              {/* Outstanding Payments */}
              <div className={cn(
                "p-3 rounded-xl border",
                summary.totalOutstanding > 0
                  ? "bg-amber-50 border-amber-200"
                  : "bg-white border-slate-200"
              )}>
                <div className="flex items-center gap-2 mb-1">
                  <Clock className="h-4 w-4 text-amber-600" />
                  <span className="text-xs text-slate-500">Outstanding</span>
                </div>
                <p className={cn(
                  "text-2xl font-bold",
                  summary.totalOutstanding > 0 ? "text-amber-700" : "text-slate-900"
                )}>
                  ${(summary.totalOutstanding / 1000000).toFixed(2)}M
                </p>
              </div>

              {/* Invoicing Progress */}
              <div className="p-3 bg-white rounded-xl border border-slate-200">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="h-4 w-4 text-blue-600" />
                  <span className="text-xs text-slate-500">Avg Progress</span>
                </div>
                <p className="text-2xl font-bold text-slate-900">
                  {summary.avgProgress.toFixed(0)}%
                </p>
                <div className="mt-1 h-1.5 w-full rounded-full bg-slate-200">
                  <div
                    className="h-1.5 rounded-full bg-blue-500"
                    style={{ width: `${Math.min(summary.avgProgress, 100)}%` }}
                  />
                </div>
              </div>

              {/* Payment Health */}
              <div className={cn(
                "p-3 rounded-xl border",
                summary.overdueCount > 0
                  ? "bg-red-50 border-red-200"
                  : "bg-emerald-50 border-emerald-200"
              )}>
                <div className="flex items-center gap-2 mb-1">
                  {summary.overdueCount > 0 ? (
                    <AlertTriangle className="h-4 w-4 text-red-600" />
                  ) : (
                    <CheckCircle className="h-4 w-4 text-emerald-600" />
                  )}
                  <span className="text-xs text-slate-500">Payment Health</span>
                </div>
                {summary.overdueCount > 0 ? (
                  <p className="text-lg font-bold text-red-700">
                    {summary.overdueCount} Overdue
                  </p>
                ) : (
                  <p className="text-lg font-bold text-emerald-700">
                    All Current
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Projects Table */}
      <Card className={cn(ds.borderRadius.cardLarge, "border-slate-200/70")}>
        <CardContent className="p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-slate-400">
                Active projects
              </p>
              <h2 className={cn(ds.typography.heading2, ds.textColors.primary)}>
                Projects with received payments
              </h2>
            </div>
            <Badge variant="secondary" className="rounded-full">
              {sortedProjects.length} active
            </Badge>
          </div>

          {projectsQuery.isLoading ? (
            <p className="text-sm text-slate-500">Loading active projects...</p>
          ) : projectsQuery.isError ? (
            <div className="rounded-2xl border border-red-100 bg-red-50 p-4">
              <p className="text-sm text-red-700">
                Unable to load projects. Make sure the API endpoint /api/projects/active is implemented.
              </p>
            </div>
          ) : sortedProjects.length === 0 ? (
            <p className="text-sm text-slate-500">No active projects yet</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">
                      PROJECT
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">
                      CURRENT PHASE
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">
                      CLIENT
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">
                      LAST INVOICE
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">
                      PAYMENT STATUS
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">
                      REMAINING VALUE
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {sortedProjects.map((project: Record<string, unknown>) => (
                    <ProjectRow key={project.project_code as string} project={project} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ProjectRow({ project }: { project: Record<string, unknown> }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const lastInvoice = project.last_invoice as Record<string, unknown> | null | undefined;
  const paymentStatus = (project.payment_status as string) || "pending";
  const remainingValue = (project.remaining_value as number) || 0;
  const currentPhase = (project.current_phase as string) || null;

  const statusColorMap: Record<string, string> = {
    paid: "bg-emerald-50 text-emerald-700 border-emerald-200",
    outstanding: "bg-amber-50 text-amber-700 border-amber-200",
    overdue: "bg-red-50 text-red-700 border-red-200",
    pending: "bg-slate-50 text-slate-700 border-slate-200",
  };
  const statusColor = statusColorMap[paymentStatus] || "bg-slate-50 text-slate-700 border-slate-200";
  const phaseColor = getPhaseColor(currentPhase);

  return (
    <>
      <tr className="hover:bg-slate-50 cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
        <td className="px-4 py-4">
          <div>
            <p className="font-semibold text-slate-900">{project.project_title as string}</p>
            <p className="text-xs text-slate-500">{project.project_code as string}</p>
          </div>
        </td>
        <td className="px-4 py-4">
          {currentPhase ? (
            <Badge className={`rounded-full border text-xs ${phaseColor}`}>
              {currentPhase}
            </Badge>
          ) : (
            <span className="text-sm text-slate-400">—</span>
          )}
        </td>
        <td className="px-4 py-4 text-sm text-slate-700">{(project.client_name as string) || "—"}</td>
        <td className="px-4 py-4">
          {lastInvoice ? (
            <div>
              <p className="text-sm font-medium text-slate-900">
                {lastInvoice.invoice_number as string}
              </p>
              <p className="text-xs text-slate-500">
                {new Date(lastInvoice.invoice_date as string).toLocaleDateString()}
              </p>
            </div>
          ) : (
            <p className="text-sm text-slate-500">No invoices</p>
          )}
        </td>
        <td className="px-4 py-4">
          <Badge className={`rounded-full border ${statusColor}`}>
            {paymentStatus.charAt(0).toUpperCase() + paymentStatus.slice(1)}
          </Badge>
        </td>
        <td className="px-4 py-4 text-right">
          <p className="font-semibold text-slate-900">
            {formatCurrency(remainingValue)}
          </p>
        </td>
      </tr>
      {isExpanded && (
        <tr className="bg-slate-50">
          <td colSpan={6} className="px-4 py-4">
            <ProjectDetails project={project} />
          </td>
        </tr>
      )}
    </>
  );
}

function ProjectDetails({ project }: { project: Record<string, unknown> }) {
  const projectCode = project.project_code as string;

  // Fetch hierarchical breakdown
  const hierarchyQuery = useQuery({
    queryKey: ["project-hierarchy", projectCode],
    queryFn: () => api.getProjectHierarchy(projectCode),
    enabled: !!projectCode,
  });

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
            Total contract value
          </p>
          <p className="mt-1 text-lg font-semibold text-slate-900">
            {formatCurrency((project.contract_value as number) || 0)}
          </p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
            Total invoiced
          </p>
          <p className="mt-1 text-lg font-semibold text-slate-900">
            {formatCurrency((project.total_invoiced as number) || 0)}
          </p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
            Total paid
          </p>
          <p className="mt-1 text-lg font-semibold text-emerald-700">
            {formatCurrency((project.total_paid as number) || 0)}
          </p>
        </div>
      </div>

      {/* Hierarchical Invoice Display */}
      {hierarchyQuery.isLoading ? (
        <p className="text-sm text-slate-500">Loading breakdown...</p>
      ) : hierarchyQuery.isError ? (
        <p className="text-sm text-red-600">Error loading breakdown</p>
      ) : hierarchyQuery.data?.disciplines ? (
        <ProjectHierarchyDisplay
          disciplines={hierarchyQuery.data.disciplines}
          projectTitle={project.project_title as string}
        />
      ) : null}
    </div>
  );
}

// Helper to determine color based on percentage invoiced
function getInvoicingColor(percentage: number): string {
  if (percentage < 50) return "text-red-600 bg-red-50 border-red-200";
  if (percentage < 80) return "text-yellow-600 bg-yellow-50 border-yellow-200";
  return "text-emerald-600 bg-emerald-50 border-emerald-200";
}

function ProjectHierarchyDisplay({
  disciplines,
  projectTitle: _projectTitle,
}: {
  disciplines: Record<string, DisciplineBreakdown>;
  projectTitle: string;
}) {
  return (
    <div className="space-y-6">
      {Object.entries(disciplines).map(([disciplineName, discipline]) => (
        <div key={disciplineName} className="space-y-3">
          {/* Discipline Header */}
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">
              {disciplineName}
            </h3>
            <div className="flex items-center gap-4 text-xs text-slate-600">
              <span>
                Fee: {formatCurrency(discipline.total_fee || 0)}
              </span>
              <span>
                Invoiced: {formatCurrency(discipline.total_invoiced || 0)}
              </span>
            </div>
          </div>

          {/* Phases */}
          <div className="space-y-3">
            {discipline.phases
              ?.sort((a: ProjectPhase, b: ProjectPhase) => (PHASE_ORDER[a.phase] || 99) - (PHASE_ORDER[b.phase] || 99))
              .map((phase: ProjectPhase) => {
                const phaseFee = phase.phase_fee || 0;
                const phaseInvoiced = phase.total_invoiced || 0;
                const phasePaid = phase.total_paid || 0;
                const percentageInvoiced = phaseFee > 0 ? (phaseInvoiced / phaseFee) * 100 : 0;
                const colorClass = getInvoicingColor(percentageInvoiced);

                return (
                  <div key={phase.breakdown_id} className="ml-4 space-y-2">
                    {/* Phase Header */}
                    <div className="flex items-start justify-between rounded-lg bg-slate-50 p-3">
                      <div className="flex-1">
                        <p className="font-medium text-slate-900">{phase.phase}</p>
                        <div className="mt-1 flex items-center gap-4 text-xs text-slate-600">
                          <span>Fee: {formatCurrency(phaseFee)}</span>
                          <span>Invoiced: {formatCurrency(phaseInvoiced)}</span>
                          <span>Paid: {formatCurrency(phasePaid)}</span>
                        </div>
                        {/* Progress Bar */}
                        <div className="mt-2">
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-slate-600">Invoicing Progress</span>
                            <Badge className={`rounded-full border text-xs ${colorClass}`}>
                              {percentageInvoiced.toFixed(1)}%
                            </Badge>
                          </div>
                          <div className="h-2 w-full rounded-full bg-slate-200">
                            <div
                              className={cn(
                                "h-2 rounded-full transition-all",
                                percentageInvoiced < 50
                                  ? "bg-red-500"
                                  : percentageInvoiced < 80
                                  ? "bg-yellow-500"
                                  : "bg-emerald-500"
                              )}
                              style={{ width: `${Math.min(percentageInvoiced, 100)}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Invoices under this phase */}
                    {phase.invoices && phase.invoices.length > 0 && (
                      <div className="ml-6 space-y-2">
                        {phase.invoices.map((invoice: PhaseInvoice) => (
                          <div
                            key={invoice.invoice_id}
                            className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3"
                          >
                            <div>
                              <p className="text-sm font-medium text-slate-900">
                                {invoice.invoice_number}
                              </p>
                              <p className="text-xs text-slate-500">
                                {invoice.invoice_date
                                  ? new Date(invoice.invoice_date).toLocaleDateString()
                                  : "—"}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-semibold text-slate-900">
                                {formatCurrency(invoice.invoice_amount || 0)}
                              </p>
                              <Badge
                                variant="outline"
                                className={cn(
                                  "text-xs",
                                  invoice.status === "paid"
                                    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                                    : "border-amber-200 bg-amber-50 text-amber-700"
                                )}
                              >
                                {invoice.status || "pending"}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
          </div>
        </div>
      ))}
    </div>
  );
}
