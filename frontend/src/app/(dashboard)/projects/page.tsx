"use client";

import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { api } from "@/lib/api";
import type { Project } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { InvoiceAgingWidget } from "@/components/dashboard/invoice-aging-widget";
import { ProjectEmailFeed } from "@/components/dashboard/project-email-feed";
import { EmailIntelligenceSummary } from "@/components/dashboard/email-intelligence-summary";
import { QuickActionsPanel } from "@/components/dashboard/quick-actions-panel";
import { ProjectHierarchyTree } from "@/components/dashboard/project-hierarchy-tree";
import { RFITrackerWidget } from "@/components/dashboard/rfi-tracker-widget";
import { MilestonesWidget } from "@/components/dashboard/milestones-widget";
import {
  CheckCircle2,
  TrendingUp,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Edit } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProjectQuickEditDialog } from "@/components/project-quick-edit-dialog";

const formatCurrency = (value?: number | null) => {
  if (value == null) return "$0";
  return `$${value.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
};

const formatDisplayDate = (value?: string | null) => {
  if (!value) return "—";
  try {
    return format(new Date(value), "MMM d, yyyy");
  } catch {
    return value;
  }
};

export default function ProjectsPage() {
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());
  const [expandedDisciplines, setExpandedDisciplines] = useState<Set<string>>(new Set());
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  const activeProjectsQuery = useQuery({
    queryKey: ["projects", "active"],
    queryFn: () => api.getActiveProjects(),
    staleTime: 1000 * 60 * 5,
  });

  // Fetch insight widgets data
  const recentPaymentsQuery = useQuery({
    queryKey: ["recent-payments"],
    queryFn: () => api.getRecentPayments(5),
    staleTime: 1000 * 60 * 10,
  });

  const projectsByOutstandingQuery = useQuery({
    queryKey: ["projects-by-outstanding"],
    queryFn: () => api.getProjectsByOutstanding(5),
    staleTime: 1000 * 60 * 10,
  });

  const oldestUnpaidQuery = useQuery({
    queryKey: ["oldest-unpaid-invoices"],
    queryFn: () => api.getOldestUnpaidInvoices(5),
    staleTime: 1000 * 60 * 10,
  });

  const projectsByRemainingQuery = useQuery({
    queryKey: ["projects-by-remaining"],
    queryFn: () => api.getProjectsByRemaining(5),
    staleTime: 1000 * 60 * 10,
  });

  const activeProjects = activeProjectsQuery.data?.data ?? [];
  const totalActiveProjects = activeProjects.length;

  // Toggle functions for expandable rows
  const toggleProject = (projectCode: string) => {
    setExpandedProjects((prev) => {
      const next = new Set(prev);
      if (next.has(projectCode)) {
        next.delete(projectCode);
        // Also collapse all disciplines for this project
        setExpandedDisciplines((prevDisciplines) => {
          const nextDisciplines = new Set(prevDisciplines);
          Array.from(nextDisciplines).forEach((key) => {
            if (key.startsWith(`${projectCode}-`)) {
              nextDisciplines.delete(key);
            }
          });
          return nextDisciplines;
        });
      } else {
        next.add(projectCode);
      }
      return next;
    });
  };

  const toggleDiscipline = (projectCode: string, discipline: string) => {
    const key = `${projectCode}-${discipline}`;
    setExpandedDisciplines((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 lg:text-4xl">
                Active Projects
              </h1>
              <p className="mt-2 text-lg text-slate-600">
                Track payments, schedules, and deliverables across all active contracts
              </p>
            </div>
            <Badge variant="secondary" className="gap-1 rounded-full">
              <TrendingUp className="h-3.5 w-3.5" />
              Updated 5 min ago
            </Badge>
          </div>
        </div>

        {/* Top Section: Invoice Aging + Quick Actions */}
        <div className="mb-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Invoice Aging Widget - Takes 2/3 width */}
          <div className="lg:col-span-2">
            <InvoiceAgingWidget />
          </div>

          {/* Quick Actions Panel - Takes 1/3 width */}
          <div className="lg:col-span-1">
            <QuickActionsPanel variant="compact" />
          </div>
        </div>

        {/* Financial Insight Widgets */}
        <div className="mb-8 grid gap-6 md:grid-cols-2">
          {/* Widget 1: Recent Payments */}
          <Card className="rounded-3xl border-slate-200/70">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-slate-400">
                    Recent Payments
                  </p>
                  <h3 className="text-lg font-semibold text-slate-900">
                    Last 5 Payments Received
                  </h3>
                </div>
                <Badge variant="secondary" className="rounded-full">
                  <TrendingUp className="mr-1 h-3.5 w-3.5" />
                  Updated
                </Badge>
              </div>
              <div>
                {recentPaymentsQuery.isLoading ? (
                  <p className="text-sm text-slate-500">Loading payments...</p>
                ) : recentPaymentsQuery.isError ? (
                  <p className="text-sm text-red-600">Unable to load payments</p>
                ) : !recentPaymentsQuery.data?.payments ||
                  recentPaymentsQuery.data.payments.length === 0 ? (
                  <p className="text-sm text-slate-500">No payments recorded yet</p>
                ) : (
                  <div className="space-y-3">
                    {recentPaymentsQuery.data.payments.map((payment, idx: number) => (
                      <div
                        key={`${payment.invoice_id}-${idx}`}
                        className="flex items-center justify-between rounded-2xl border border-slate-100 p-4 hover:bg-slate-50 transition-colors"
                      >
                        <div className="flex-1">
                          <p className="font-semibold text-slate-900">
                            {(payment.invoice_number as string) || 'N/A'} - {(payment.project_name as string) || (payment.project_code as string)}
                          </p>
                          <p className="text-xs text-slate-500">
                            {payment.paid_on
                              ? formatDisplayDate(payment.paid_on)
                              : "Date unknown"}{" "}
                            {payment.discipline && `• ${payment.discipline}`}
                          </p>
                        </div>
                        <p className="font-semibold text-green-600">
                          {formatCurrency(payment.amount_usd)}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Widget 2: Projects by Outstanding */}
          <Card className="rounded-3xl border-slate-200/70">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-slate-400">
                    Outstanding Fees
                  </p>
                  <h3 className="text-lg font-semibold text-slate-900">
                    Top 5 Projects by Outstanding
                  </h3>
                </div>
                <Badge variant="outline" className="rounded-full">
                  {projectsByOutstandingQuery.data?.count || 0} projects
                </Badge>
              </div>
              <div>
                {projectsByOutstandingQuery.isLoading ? (
                  <p className="text-sm text-slate-500">Loading projects...</p>
                ) : projectsByOutstandingQuery.isError ? (
                  <p className="text-sm text-red-600">Unable to load projects</p>
                ) : !projectsByOutstandingQuery.data?.projects ||
                  projectsByOutstandingQuery.data.projects.length === 0 ? (
                  <p className="text-sm text-slate-500">No outstanding invoices</p>
                ) : (
                  <div className="space-y-3">
                    {projectsByOutstandingQuery.data.projects.map((project: Record<string, unknown>, idx: number) => (
                      <div
                        key={`${project.project_code}-${idx}`}
                        className="flex items-center justify-between rounded-2xl border border-slate-100 p-4 hover:bg-slate-50 transition-colors"
                      >
                        <div className="flex-1">
                          <p className="font-semibold text-slate-900">
                            {(project.project_name as string) || (project.project_code as string)}
                          </p>
                          <p className="text-xs text-slate-500">
                            {(project.overdue_amount as number) > 0
                              ? `${formatCurrency(project.overdue_amount as number)} overdue`
                              : `${project.overdue_invoice_count || 0} overdue invoices`}
                          </p>
                        </div>
                        <p className="font-semibold text-orange-600">
                          {formatCurrency(project.outstanding_usd as number)}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Widget 3: Oldest Unpaid Invoices */}
          <Card className="rounded-3xl border-slate-200/70">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-slate-400">
                    Aging Invoices
                  </p>
                  <h3 className="text-lg font-semibold text-slate-900">
                    Oldest Unpaid Invoices
                  </h3>
                </div>
                <Badge variant="outline" className="rounded-full">
                  By days outstanding
                </Badge>
              </div>
              <div>
                {oldestUnpaidQuery.isLoading ? (
                  <p className="text-sm text-slate-500">Loading invoices...</p>
                ) : oldestUnpaidQuery.isError ? (
                  <p className="text-sm text-red-600">Unable to load invoices</p>
                ) : !oldestUnpaidQuery.data?.invoices ||
                  oldestUnpaidQuery.data.invoices.length === 0 ? (
                  <p className="text-sm text-slate-500">No unpaid invoices</p>
                ) : (
                  <div className="space-y-3">
                    {oldestUnpaidQuery.data.invoices.map((invoice: Record<string, unknown>, idx: number) => (
                      <div
                        key={`${invoice.invoice_id}-${idx}`}
                        className="flex items-center justify-between rounded-2xl border border-slate-100 p-4 hover:bg-slate-50 transition-colors"
                      >
                        <div className="flex-1">
                          <p className="font-semibold text-slate-900">
                            {(invoice.invoice_number as string)} - {(invoice.project_name as string) || (invoice.project_code as string)}
                          </p>
                          <p className="text-xs text-slate-500">
                            {(invoice.days_outstanding as number)} days outstanding
                            {(invoice.days_overdue as number) > 0 && ` • ${invoice.days_overdue} days overdue`}
                            {(invoice.discipline as string) && ` • ${(invoice.discipline as string)}`}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-slate-900">
                            {formatCurrency(invoice.amount_outstanding as number)}
                          </p>
                          <Badge
                            variant={(invoice.aging_bucket as string) === "90+ days" ? "destructive" : "outline"}
                            className="mt-1 text-xs"
                          >
                            {(invoice.aging_bucket as string)}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Widget 4: Remaining Contract Value */}
          <Card className="rounded-3xl border-slate-200/70">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-slate-400">
                    Future Revenue
                  </p>
                  <h3 className="text-lg font-semibold text-slate-900">
                    Top 5 by Remaining Value
                  </h3>
                </div>
                <Badge variant="outline" className="rounded-full">
                  Uninvoiced work
                </Badge>
              </div>
              <div>
                {projectsByRemainingQuery.isLoading ? (
                  <p className="text-sm text-slate-500">Loading projects...</p>
                ) : projectsByRemainingQuery.isError ? (
                  <p className="text-sm text-red-600">Unable to load projects</p>
                ) : !projectsByRemainingQuery.data?.projects ||
                  projectsByRemainingQuery.data.projects.length === 0 ? (
                  <p className="text-sm text-slate-500">No remaining contract value</p>
                ) : (
                  <div className="space-y-3">
                    {projectsByRemainingQuery.data.projects.map((project: Record<string, unknown>, idx: number) => (
                      <div
                        key={`${project.project_code}-${idx}`}
                        className="flex items-center justify-between rounded-2xl border border-slate-100 p-4 hover:bg-slate-50 transition-colors"
                      >
                        <div className="flex-1">
                          <p className="font-semibold text-slate-900">
                            {(project.project_name as string) || (project.project_code as string)}
                          </p>
                          <p className="text-xs text-slate-500">
                            {((project.percent_invoiced as number) || 0).toFixed(1)}% invoiced •{" "}
                            {formatCurrency(project.contract_value as number)} total
                          </p>
                        </div>
                        <p className="font-semibold text-blue-600">
                          {formatCurrency(project.total_remaining_usd as number)}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </Card>
        </div>

        {/* RFI and Milestones Tracker Row */}
        <div className="mb-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RFITrackerWidget />
          <MilestonesWidget />
        </div>

        {/* All Active Projects Table */}
        <section>
          <Card className="rounded-3xl border-slate-200">
            <CardContent className="p-6">
              <div className="mb-6">
                <div className="flex items-baseline justify-between">
                  <div>
                    <p className="text-sm uppercase tracking-[0.3em] text-slate-400 mb-1">
                      Contract Overview
                    </p>
                    <h2 className="text-2xl font-bold text-slate-900">
                      All Active Projects
                    </h2>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-500">Total Contracts</p>
                    <p className="text-3xl font-bold text-slate-900">
                      {totalActiveProjects}
                    </p>
                  </div>
                </div>
                <p className="mt-2 text-sm text-slate-600">
                  Click on any project to view detailed financial breakdown by discipline and phase
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b-2 border-slate-200 text-left text-xs uppercase tracking-wider text-slate-500">
                      <th className="pb-4 pt-2 font-semibold">Project Code</th>
                      <th className="pb-4 pt-2 font-semibold">Project Name</th>
                      <th className="pb-4 pt-2 font-semibold text-right">Contract Value</th>
                      <th className="pb-4 pt-2 font-semibold text-right">Amount Due</th>
                      <th className="pb-4 pt-2 font-semibold text-right">Uninvoiced</th>
                      <th className="pb-4 pt-2 font-semibold text-center">Health</th>
                      <th className="pb-4 pt-2 font-semibold text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {activeProjectsQuery.isLoading ? (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-sm text-slate-500">
                          Loading projects...
                        </td>
                      </tr>
                    ) : activeProjects.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-sm text-slate-500">
                          No active projects found
                        </td>
                      </tr>
                    ) : (
                      activeProjects.map((project: Record<string, unknown>) => (
                        <ProjectRow
                          key={String(project.project_id || project.project_code)}
                          project={project}
                          isExpanded={expandedProjects.has(project.project_code as string)}
                          expandedDisciplines={expandedDisciplines}
                          onToggle={() => toggleProject(project.project_code as string)}
                          onToggleDiscipline={(discipline) => toggleDiscipline(project.project_code as string, discipline)}
                          onEdit={(proj) => {
                            setSelectedProject(proj as unknown as Project);
                            setEditDialogOpen(true);
                          }}
                        />
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>

      <ProjectQuickEditDialog
        project={selectedProject}
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
      />
    </div>
  );
}

function ProjectRow({
  project,
  isExpanded,
  expandedDisciplines,
  onToggle,
  onToggleDiscipline,
  onEdit,
}: {
  project: Record<string, unknown>;
  isExpanded: boolean;
  expandedDisciplines: Set<string>;
  onToggle: () => void;
  onToggleDiscipline: (discipline: string) => void;
  onEdit: (project: Record<string, unknown>) => void;
}) {
  const projectCode = project.project_code as string;

  // Fetch invoices (always load to calculate totals)
  const invoicesQuery = useQuery({
    queryKey: ["invoices", "project", projectCode],
    queryFn: () => api.getInvoicesByProject(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  // Fetch contract fee breakdown (always load to calculate totals)
  const feeBreakdownQuery = useQuery({
    queryKey: ["fee-breakdown", "project", projectCode],
    queryFn: async () => {
      const response = await fetch(`http://localhost:8000/api/projects/${encodeURIComponent(projectCode)}/fee-breakdown`);
      return response.json();
    },
    staleTime: 1000 * 60 * 5,
  });

  const invoices = invoicesQuery.data?.invoices ?? [];
  const feeBreakdowns = feeBreakdownQuery.data?.fee_breakdowns ?? [];

  // Normalize discipline names to the three main categories
  const normalizeDiscipline = (discipline: string | null | undefined): string | null => {
    if (!discipline) return null;
    const lower = discipline.toLowerCase().trim();

    // Map variations to main categories
    if (lower.includes('architect')) return 'Architecture';
    if (lower.includes('interior')) return 'Interior';
    if (lower.includes('landscape')) return 'Landscape';

    // Filter out non-main disciplines
    return null;
  };

  // Group invoices by normalized discipline
  const invoicesByDiscipline = invoices.reduce((acc: Record<string, Record<string, unknown>[]>, invoice: Record<string, unknown>) => {
    const normalizedDiscipline = normalizeDiscipline(invoice.discipline as string | null | undefined);
    if (normalizedDiscipline) {
      if (!acc[normalizedDiscipline]) {
        acc[normalizedDiscipline] = [];
      }
      acc[normalizedDiscipline].push(invoice);
    }
    return acc;
  }, {});

  // Sort disciplines in desired order
  const disciplineOrder = ['Landscape', 'Interior', 'Architecture'];
  const sortedDisciplines = disciplineOrder.filter(d => invoicesByDiscipline[d]);

  // Calculate project-level totals
  const projectTotalInvoiced = invoices.reduce(
    (sum: number, inv: Record<string, unknown>) => sum + ((inv.invoice_amount as number) || (inv.amount_usd as number) || 0),
    0
  );
  const projectTotalPaid = invoices.reduce(
    (sum: number, inv: Record<string, unknown>) => sum + ((inv.payment_amount as number) || (inv.amount_paid as number) || 0),
    0
  );
  const projectTotalOutstanding = projectTotalInvoiced - projectTotalPaid;
  const projectContractFee = feeBreakdowns.reduce(
    (sum: number, fb: Record<string, unknown>) => sum + ((fb.phase_fee_usd as number) || 0),
    0
  );
  // Use contract fee breakdowns if available, otherwise use total project fee
  const totalProjectFee = projectContractFee > 0
    ? projectContractFee
    : (project.contract_value || project.total_fee_usd || 0);
  const projectTotalRemaining = totalProjectFee - projectTotalInvoiced;

  // Group invoices by phase within each discipline
  const getInvoicesByPhase = (disciplineInvoices: Record<string, unknown>[]) => {
    return disciplineInvoices.reduce((acc: Record<string, Record<string, unknown>[]>, invoice: Record<string, unknown>) => {
      const phase = (invoice.phase as string) || "Unknown Phase";
      if (!acc[phase]) {
        acc[phase] = [];
      }
      acc[phase].push(invoice);
      return acc;
    }, {});
  };

  return (
    <>
      <tr
        className="group cursor-pointer hover:bg-slate-50"
        onClick={onToggle}
      >
        <td className="py-4">
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-slate-400" />
            ) : (
              <ChevronRight className="h-4 w-4 text-slate-400" />
            )}
            <span className="font-medium text-blue-600">
              {(project.project_code as string)}
            </span>
          </div>
        </td>
        <td className="py-4 text-sm text-slate-900">
          {(project.project_title as string) || (project.client_name as string)}
        </td>
        <td className="py-4">
          <div className="text-right">
            <div className="text-sm font-medium text-slate-900">
              {formatCurrency(totalProjectFee)}
            </div>
            <div className="text-xs text-slate-500">Total Fee</div>
          </div>
        </td>
        <td className="py-4">
          <div className="text-right">
            <div className="text-sm font-medium text-amber-600">
              {formatCurrency(projectTotalOutstanding)}
            </div>
            <div className="text-xs text-slate-500">Outstanding</div>
          </div>
        </td>
        <td className="py-4">
          <div className="text-right">
            <div className={cn(
              "text-sm font-medium",
              projectTotalRemaining > 1000000
                ? "text-rose-700 font-bold text-base"
                : projectTotalRemaining > 500000
                ? "text-rose-700 font-semibold"
                : "text-rose-700"
            )}>
              {formatCurrency(projectTotalRemaining)}
              {projectTotalRemaining > 1000000 && (
                <span className="ml-1 text-xs">!</span>
              )}
            </div>
            <div className="text-xs text-slate-500">Remaining</div>
          </div>
        </td>
        <td className="py-4">
          <StatusBadge status={(project.status as string) || "active"} />
        </td>
        <td className="py-4 text-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onEdit(project);
            }}
            className="h-8 w-8 p-0"
          >
            <Edit className="h-4 w-4" />
            <span className="sr-only">Edit project</span>
          </Button>
        </td>
      </tr>

      {isExpanded && (
        <tr>
          <td colSpan={7} className="bg-slate-50 p-0">
            <div className="p-6">
              {invoicesQuery.isLoading ? (
                <div className="py-4 text-center text-sm text-slate-500">
                  Loading invoices...
                </div>
              ) : invoices.length === 0 ? (
                <div className="py-4 text-center text-sm text-slate-500">
                  No invoices found for this project
                </div>
              ) : sortedDisciplines.length === 0 ? (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                  <p className="text-sm text-amber-800">
                    <strong>Note:</strong> This project has {invoices.length} invoice{invoices.length !== 1 ? 's' : ''} but they are not categorized by discipline yet.
                    Please update the discipline information in the database to see the breakdown by Landscape, Interior, and Architecture.
                  </p>
                  <div className="mt-4 space-y-2">
                    <p className="text-xs font-semibold text-amber-900">Invoice Details:</p>
                    {invoices.map((invoice: Record<string, unknown>) => (
                      <div
                        key={String(invoice.invoice_id || invoice.invoice_number)}
                        className="grid grid-cols-6 gap-4 rounded-lg border border-amber-100 bg-white p-3 text-sm"
                      >
                        <div>
                          <div className="text-xs text-slate-500">Invoice #</div>
                          <div className="font-medium text-slate-900">
                            {(invoice.invoice_number as string)}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500">Invoice Date</div>
                          <div className="text-slate-900">
                            {formatDisplayDate((invoice.invoice_date as string) || (invoice.issued_date as string))}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500">Payment Date</div>
                          <div className="text-slate-900">
                            {formatDisplayDate(invoice.payment_date as string) || '-'}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500">Invoice Amount</div>
                          <div className="font-semibold text-slate-900">
                            {formatCurrency((invoice.invoice_amount as number) || (invoice.amount_usd as number))}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500">Payment Amount</div>
                          <div className="font-semibold text-emerald-600">
                            {formatCurrency((invoice.payment_amount as number) || (invoice.amount_paid as number))}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500">Outstanding</div>
                          <div className="font-semibold text-rose-700">
                            {formatCurrency(((invoice.invoice_amount as number) || (invoice.amount_usd as number) || 0) - ((invoice.payment_amount as number) || (invoice.amount_paid as number) || 0))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {sortedDisciplines.map((discipline: string) => {
                    const disciplineInvoices = invoicesByDiscipline[discipline];
                    const disciplineKey = `${projectCode}-${discipline}`;
                    const isDisciplineExpanded = expandedDisciplines.has(disciplineKey);
                    const invoicesByPhase = getInvoicesByPhase(disciplineInvoices);

                    // Get contract fee for this discipline (sum of all phases)
                    const contractFee = feeBreakdowns
                      .filter((fb: Record<string, unknown>) => normalizeDiscipline(fb.discipline as string | null | undefined) === discipline)
                      .reduce((sum: number, fb: Record<string, unknown>) => sum + ((fb.phase_fee_usd as number) || 0), 0);

                    // Calculate discipline totals
                    const totalInvoiced = disciplineInvoices.reduce(
                      (sum: number, inv: Record<string, unknown>) => sum + ((inv.invoice_amount as number) || (inv.amount_usd as number) || 0),
                      0
                    );
                    const totalPaid = disciplineInvoices.reduce(
                      (sum: number, inv: Record<string, unknown>) => sum + ((inv.payment_amount as number) || (inv.amount_paid as number) || 0),
                      0
                    );
                    const outstanding = totalInvoiced - totalPaid;
                    const remaining = contractFee > 0 ? contractFee - totalInvoiced : 0;

                    return (
                      <div key={discipline} className="rounded-lg border-2 border-slate-300 bg-gradient-to-r from-slate-50 to-white shadow-sm">
                        <div
                          className="flex cursor-pointer items-center justify-between p-5 hover:bg-slate-100 transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            onToggleDiscipline(discipline);
                          }}
                        >
                          <div className="flex items-center gap-3">
                            {isDisciplineExpanded ? (
                              <ChevronDown className="h-5 w-5 text-slate-600" />
                            ) : (
                              <ChevronRight className="h-5 w-5 text-slate-600" />
                            )}
                            <div>
                              <h3 className="text-xl font-bold text-slate-900">
                                {discipline}
                              </h3>
                              {contractFee > 0 && (
                                <p className="text-sm text-slate-600 mt-0.5">
                                  Contract Fee: {formatCurrency(contractFee)}
                                </p>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-8">
                            <div className="text-center">
                              <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-1">TOTAL PAID</div>
                              <div className="text-lg font-bold text-emerald-600">
                                {formatCurrency(totalPaid)}
                              </div>
                            </div>
                            <div className="h-12 w-px bg-slate-300"></div>
                            <div className="text-center">
                              <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-1">OUTSTANDING</div>
                              <div className="text-lg font-bold text-amber-600">
                                {formatCurrency(outstanding)}
                              </div>
                            </div>
                            <div className="h-12 w-px bg-slate-300"></div>
                            <div className="text-center">
                              <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-1">REMAINING</div>
                              <div className="text-lg font-bold text-slate-700">
                                {formatCurrency(remaining)}
                              </div>
                            </div>
                          </div>
                        </div>

                        {isDisciplineExpanded && (
                          <div className="border-t border-slate-200 p-4">
                            <div className="space-y-4">
                              {(() => {
                                // Get all phases from contract for this discipline
                                const contractPhases = feeBreakdowns
                                  .filter((fb: Record<string, unknown>) => normalizeDiscipline(fb.discipline as string | null | undefined) === discipline)
                                  .map((fb: Record<string, unknown>) => fb.phase);

                                // Combine contract phases with invoice phases
                                const allPhases = new Set([...contractPhases, ...Object.keys(invoicesByPhase)]);

                                // Define phase order
                                const phaseOrder = [
                                  'Mobilization',
                                  'Concept Design',
                                  'Schematic Design',
                                  'Design Development',
                                  'Construction Documents',
                                  'Construction Observation'
                                ];

                                // Sort phases by defined order
                                const sortedPhases = Array.from(allPhases).sort((a, b) => {
                                  const indexA = phaseOrder.findIndex(p => a.toLowerCase().includes(p.toLowerCase()));
                                  const indexB = phaseOrder.findIndex(p => b.toLowerCase().includes(p.toLowerCase()));

                                  // If both found, sort by index
                                  if (indexA !== -1 && indexB !== -1) return indexA - indexB;
                                  // If only A found, put it first
                                  if (indexA !== -1) return -1;
                                  // If only B found, put it first
                                  if (indexB !== -1) return 1;
                                  // Neither found, alphabetical
                                  return a.localeCompare(b);
                                });

                                return sortedPhases.map((phase: string) => {
                                // Get contract fee for this phase
                                const phaseFee = feeBreakdowns
                                  .filter((fb: Record<string, unknown>) =>
                                    normalizeDiscipline(fb.discipline as string | null | undefined) === discipline &&
                                    fb.phase === phase
                                  )
                                  .reduce((sum: number, fb: Record<string, unknown>) => sum + ((fb.phase_fee_usd as number) || 0), 0);

                                // Get invoices for this phase (might be empty array)
                                const phaseInvoices = invoicesByPhase[phase] || [];

                                // Calculate phase totals
                                const phaseInvoiced = phaseInvoices.reduce(
                                  (sum: number, inv: Record<string, unknown>) => sum + ((inv.invoice_amount as number) || (inv.amount_usd as number) || 0),
                                  0
                                );
                                const phasePaid = phaseInvoices.reduce(
                                  (sum: number, inv: Record<string, unknown>) => sum + ((inv.payment_amount as number) || (inv.amount_paid as number) || 0),
                                  0
                                );
                                const phaseOutstanding = phaseInvoiced - phasePaid;
                                const phaseRemaining = phaseFee - phaseInvoiced;

                                // Check if phase is fully complete (100% invoiced AND 100% paid)
                                const isComplete = phaseFee > 0 && phaseInvoiced >= phaseFee && phasePaid >= phaseInvoiced;

                                // Determine if this is a partial invoice (check if multiple invoices with different amounts exist for this phase)
                                const isPartial = phaseFee > 0 && phaseInvoiced > 0 && phaseInvoiced < phaseFee;
                                const percentageInvoiced = phaseFee > 0 ? (phaseInvoiced / phaseFee) * 100 : 0;

                                return (
                                  <div key={phase} className="space-y-2">
                                    <div className={`flex items-center justify-between rounded-lg p-3 ${
                                      isComplete
                                        ? 'bg-emerald-50 border-2 border-emerald-400'
                                        : 'bg-blue-50 border border-blue-200'
                                    }`}>
                                      <div className="flex items-center gap-2">
                                        {isComplete && <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0" />}
                                        <h4 className="text-base font-semibold text-slate-900">
                                          {phase}
                                          {isComplete && <span className="ml-2 text-emerald-600 font-bold">✓ COMPLETE</span>}
                                          {isPartial && !isComplete && ` (${percentageInvoiced.toFixed(0)}%)`}
                                          {phaseFee > 0 && (
                                            <span className="ml-2 text-slate-600">
                                              - {formatCurrency(phaseFee)}
                                            </span>
                                          )}
                                        </h4>
                                      </div>
                                      <div className="flex items-center gap-4">
                                        <div className="text-right">
                                          <div className="text-xs text-slate-500">Invoiced</div>
                                          <div className="text-sm font-semibold text-blue-600">
                                            {formatCurrency(phaseInvoiced)}
                                          </div>
                                        </div>
                                        <div className="text-right">
                                          <div className="text-xs text-slate-500">Paid</div>
                                          <div className="text-sm font-semibold text-emerald-600">
                                            {formatCurrency(phasePaid)}
                                          </div>
                                        </div>
                                        <div className="text-right">
                                          <div className="text-xs text-slate-500">Outstanding</div>
                                          <div className="text-sm font-semibold text-amber-600">
                                            {formatCurrency(phaseOutstanding)}
                                          </div>
                                        </div>
                                        {phaseFee > 0 && (
                                          <div className="text-right">
                                            <div className="text-xs text-slate-500">Remaining</div>
                                            <div className="text-sm font-semibold text-slate-700">
                                              {formatCurrency(phaseRemaining)}
                                            </div>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                    <div className="space-y-2">
                                      {phaseInvoices.length > 0 ? (
                                        <>
                                          {phaseInvoices.map((invoice: Record<string, unknown>) => (
                                            <div
                                              key={String(invoice.invoice_id || invoice.invoice_number)}
                                              className="grid grid-cols-5 gap-4 rounded-lg border border-slate-200 bg-white p-3 text-sm hover:bg-slate-50 transition-colors"
                                            >
                                              <div>
                                                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Invoice #</div>
                                                <div className="font-semibold text-slate-900 mt-1">
                                                  {(invoice.invoice_number as string)}
                                                </div>
                                              </div>
                                              <div>
                                                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Invoice Date</div>
                                                <div className="text-slate-900 mt-1">
                                                  {formatDisplayDate((invoice.invoice_date as string) || (invoice.issued_date as string))}
                                                </div>
                                              </div>
                                              <div>
                                                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Payment Amount</div>
                                                <div className="font-bold text-emerald-600 mt-1">
                                                  {formatCurrency((invoice.payment_amount as number) || (invoice.amount_paid as number) || 0)}
                                                </div>
                                              </div>
                                              <div>
                                                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Payment Date</div>
                                                <div className="text-slate-900 mt-1">
                                                  {formatDisplayDate(invoice.payment_date as string) || '-'}
                                                </div>
                                              </div>
                                              <div>
                                                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Outstanding Amount</div>
                                                <div className="font-bold text-amber-600 mt-1">
                                                  {formatCurrency(((invoice.invoice_amount as number) || (invoice.amount_usd as number) || 0) - ((invoice.payment_amount as number) || (invoice.amount_paid as number) || 0))}
                                                </div>
                                              </div>
                                            </div>
                                          ))}
                                          {phaseRemaining > 0 && (
                                            <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-4">
                                              <div className="flex items-center justify-between">
                                                <div>
                                                  <p className="text-sm font-semibold text-slate-700">
                                                    Remaining Uninvoiced
                                                  </p>
                                                  <p className="text-xs text-slate-500 mt-0.5">
                                                    Not yet billed
                                                  </p>
                                                </div>
                                                <p className="text-lg font-bold text-slate-700">
                                                  {formatCurrency(phaseRemaining)}
                                                </p>
                                              </div>
                                            </div>
                                          )}
                                        </>
                                      ) : (
                                        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-4">
                                          <div className="flex items-center justify-between">
                                            <div>
                                              <p className="text-sm font-semibold text-slate-700">
                                                Not Yet Invoiced
                                              </p>
                                              <p className="text-xs text-slate-500 mt-0.5">
                                                Full phase fee remaining
                                              </p>
                                            </div>
                                            <p className="text-lg font-bold text-slate-700">
                                              {formatCurrency(phaseRemaining)}
                                            </p>
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                );
                              });
                              })()}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Financial Hierarchy */}
              {isExpanded && (
                <div className="mt-8">
                  <ProjectHierarchyTree projectCode={projectCode} />
                </div>
              )}

              {/* Email Intelligence and Activity */}
              {isExpanded && (
                <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Email Intelligence Summary (AI-powered) */}
                  <EmailIntelligenceSummary projectCode={projectCode} />

                  {/* Email Activity Feed (Individual emails) */}
                  <ProjectEmailFeed projectCode={projectCode} limit={10} />
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}


function StatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
    active: { label: "Active", variant: "default" },
    on_hold: { label: "On Hold", variant: "secondary" },
    at_risk: { label: "At Risk", variant: "destructive" },
    completed: { label: "Completed", variant: "outline" },
  };

  const config = statusConfig[status.toLowerCase()] || {
    label: status,
    variant: "outline" as const,
  };

  return (
    <Badge variant={config.variant} className="rounded-full">
      {config.label}
    </Badge>
  );
}
