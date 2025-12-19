"use client";

import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { api, FeeBreakdown } from "@/lib/api";
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
import { TopOutstandingInvoicesWidget } from "@/components/dashboard/top-outstanding-invoices-widget";
import { AllInvoicesList } from "@/components/dashboard/all-invoices-list";
import {
  CheckCircle2,
  TrendingUp,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  FolderOpen,
} from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Edit, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProjectQuickEditDialog } from "@/components/project-quick-edit-dialog";
import { ds, bensleyVoice } from "@/lib/design-system";

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
  const [expandedPhaseInvoices, setExpandedPhaseInvoices] = useState<Set<string>>(new Set());
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

  const togglePhaseInvoices = (projectCode: string, discipline: string, phase: string) => {
    const key = `${projectCode}-${discipline}-${phase}`;
    setExpandedPhaseInvoices((prev) => {
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
    <div className="min-h-screen bg-slate-50 w-full max-w-full overflow-x-hidden">
      <div className="mx-auto max-w-full px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className={ds.typography.pageTitle}>
                {bensleyVoice.sectionHeaders.projects}
              </h1>
              <p className={cn(ds.typography.bodySmall, "mt-2")}>
                Track payments, schedules, and deliverables across all active contracts
              </p>
            </div>
            <Badge variant="secondary" className={ds.badges.default}>
              <TrendingUp className="h-3.5 w-3.5 mr-1" />
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
          <Card className={ds.cards.default}>
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
                            {(payment.project_name as string) || (payment.project_code as string) || 'Unknown Project'}
                          </p>
                          <p className="text-xs text-slate-500">
                            {payment.paid_on
                              ? formatDisplayDate(payment.paid_on)
                              : "Date unknown"}
                            {payment.invoice_number && ` • #${payment.invoice_number}`}
                            {payment.discipline && ` • ${payment.discipline}`}
                          </p>
                        </div>
                        <p className="text-lg font-bold text-green-600">
                          {formatCurrency(payment.amount_usd)}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Widget 2: Projects by Outstanding - IMPROVED CLARITY */}
          <Card className={ds.cards.default}>
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
                    {projectsByOutstandingQuery.data.projects.map((project: Record<string, unknown>, idx: number) => {
                      const overdueAmount = (project.overdue_amount as number) || 0;
                      const outstandingAmount = (project.outstanding_balance_usd as number) || (project.outstanding_usd as number) || 0;
                      const hasOverdue = overdueAmount > 0;

                      return (
                        <div
                          key={`${project.project_code}-${idx}`}
                          className={cn(
                            "rounded-2xl border p-4 transition-colors",
                            hasOverdue
                              ? "border-red-200 bg-red-50/50 hover:bg-red-50"
                              : "border-slate-100 hover:bg-slate-50"
                          )}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <p className="font-semibold text-slate-900 truncate">
                                {(project.project_name as string) || (project.project_code as string)}
                              </p>
                              <p className="text-xs text-slate-500 mt-0.5">
                                {project.project_code as string}
                              </p>
                            </div>
                            <div className="text-right flex-shrink-0 ml-4">
                              <p className="text-sm text-slate-600">Outstanding</p>
                              <p className="font-bold text-lg text-orange-600">
                                {formatCurrency(outstandingAmount)}
                              </p>
                            </div>
                          </div>
                          {hasOverdue && (
                            <div className="mt-2 flex items-center gap-1.5 text-red-600">
                              <AlertTriangle className="h-3.5 w-3.5" />
                              <span className="text-xs font-medium">
                                {formatCurrency(overdueAmount)} overdue (&gt;30 days)
                              </span>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Widget 3: Oldest Unpaid Invoices */}
          <Card className={ds.cards.default}>
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
          <Card className={ds.cards.default}>
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
                          {formatCurrency((project.remaining_value as number) || (project.total_remaining_usd as number))}
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
          <Card className={ds.cards.default}>
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
                  <thead className={ds.tables.header}>
                    <tr>
                      <th className={ds.tables.headerCell}>Project</th>
                      <th className={ds.tables.headerCellRight}>Contract Value</th>
                      <th className={ds.tables.headerCellRight}>Paid</th>
                      <th className={ds.tables.headerCellRight}>Outstanding</th>
                      <th className={cn(ds.tables.headerCell, "text-center")}>Health</th>
                      <th className={cn(ds.tables.headerCell, "text-center")}>Actions</th>
                    </tr>
                  </thead>
                  <tbody className={ds.tables.divider}>
                    {activeProjectsQuery.isLoading ? (
                      <>
                        {[1, 2, 3, 4, 5].map((i) => (
                          <tr key={i} className="animate-pulse">
                            <td className="py-4"><div className="h-4 w-48 bg-slate-200 rounded" /></td>
                            <td className="py-4 text-right"><div className="h-4 w-20 bg-slate-200 rounded ml-auto" /></td>
                            <td className="py-4 text-right"><div className="h-4 w-16 bg-slate-200 rounded ml-auto" /></td>
                            <td className="py-4 text-right"><div className="h-4 w-16 bg-slate-200 rounded ml-auto" /></td>
                            <td className="py-4 text-center"><div className="h-6 w-16 bg-slate-200 rounded mx-auto" /></td>
                            <td className="py-4 text-center"><div className="h-8 w-8 bg-slate-200 rounded mx-auto" /></td>
                          </tr>
                        ))}
                      </>
                    ) : activeProjects.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-16 text-center">
                          <FolderOpen className="mx-auto h-16 w-16 text-slate-300 mb-4" />
                          <p className={ds.typography.cardHeader}>{bensleyVoice.emptyStates.projects}</p>
                          <p className={cn(ds.typography.caption, "mt-2")}>Projects will appear here once contracts are signed</p>
                        </td>
                      </tr>
                    ) : (
                      activeProjects.map((project: Record<string, unknown>) => (
                        <ProjectRow
                          key={String(project.project_id || project.project_code)}
                          project={project}
                          isExpanded={expandedProjects.has(project.project_code as string)}
                          expandedDisciplines={expandedDisciplines}
                          expandedPhaseInvoices={expandedPhaseInvoices}
                          onToggle={() => toggleProject(project.project_code as string)}
                          onToggleDiscipline={(discipline) => toggleDiscipline(project.project_code as string, discipline)}
                          onTogglePhaseInvoices={(discipline, phase) => togglePhaseInvoices(project.project_code as string, discipline, phase)}
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

        {/* Invoice Management Section - Full Width */}
        <section className="mt-8">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-900">Invoice Management</h2>
            <p className="text-sm text-slate-600 mt-1">
              Track and manage all outstanding invoices across projects
            </p>
          </div>

          {/* Top Outstanding Invoices */}
          <div className="mb-6">
            <TopOutstandingInvoicesWidget />
          </div>

          {/* All Invoices List with Filters */}
          <AllInvoicesList />
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
  expandedPhaseInvoices,
  onToggle,
  onToggleDiscipline,
  onTogglePhaseInvoices,
  onEdit,
}: {
  project: Record<string, unknown>;
  isExpanded: boolean;
  expandedDisciplines: Set<string>;
  expandedPhaseInvoices: Set<string>;
  onToggle: () => void;
  onToggleDiscipline: (discipline: string) => void;
  onTogglePhaseInvoices: (discipline: string, phase: string) => void;
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
    queryFn: () => api.getProjectFeeBreakdowns(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const invoices = invoicesQuery.data?.invoices ?? [];
  const feeBreakdowns = feeBreakdownQuery.data?.breakdowns ?? [];

  // Normalize discipline names to the main categories
  const normalizeDiscipline = (discipline: string | null | undefined): string | null => {
    if (!discipline) return null;
    const lower = discipline.toLowerCase().trim();

    // Map variations to main categories (in priority order)
    if (lower.includes('architect') && !lower.includes('landscape')) return 'Architecture';
    if (lower.includes('interior')) return 'Interior';
    if (lower.includes('landscape')) return 'Landscape';
    if (lower.includes('specialty') || lower.includes('branding')) return 'Specialty';

    // Return original discipline if not matched
    return discipline;
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

  // Sort disciplines in desired order: Architecture, Interior, Landscape, Specialty/Branding
  const disciplineOrder = ['Architecture', 'Interior', 'Landscape', 'Specialty', 'Branding'];
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
    (sum: number, fb: FeeBreakdown) => sum + (fb.phase_fee_usd || 0),
    0
  );
  // Use contract fee breakdowns if available, otherwise use total project fee
  const totalProjectFee: number = projectContractFee > 0
    ? projectContractFee
    : (Number(project.contract_value) || Number(project.total_fee_usd) || 0);
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

  const router = useRouter();

  const handleRowClick = () => {
    router.push(`/projects/${encodeURIComponent(projectCode)}`);
  };

  return (
    <>
      <tr
        className="group cursor-pointer hover:bg-slate-50"
        onClick={handleRowClick}
      >
        {/* Project Name (primary) with Code (secondary) */}
        <td className="py-4">
          <div className="flex items-center gap-2">
            <ExternalLink className="h-4 w-4 text-slate-400 group-hover:text-teal-600" />
            <div>
              <div className="font-medium text-slate-900 group-hover:text-teal-700">
                {(project.project_title as string) || (project.client_name as string) || "Unnamed Project"}
              </div>
              <div className="text-xs text-slate-500">
                {(project.project_code as string)}
              </div>
            </div>
          </div>
        </td>
        {/* Contract Value */}
        <td className="py-4">
          <div className="text-right">
            <div className="text-sm font-medium text-slate-900">
              {formatCurrency(totalProjectFee)}
            </div>
          </div>
        </td>
        {/* Total Paid */}
        <td className="py-4">
          <div className="text-right">
            <div className="text-sm font-medium text-emerald-600">
              {formatCurrency(projectTotalPaid)}
            </div>
          </div>
        </td>
        {/* Outstanding */}
        <td className="py-4">
          <div className="text-right">
            <div className={cn(
              "text-sm font-medium",
              projectTotalOutstanding > 500000
                ? "text-amber-600 font-bold"
                : "text-amber-600"
            )}>
              {formatCurrency(projectTotalOutstanding)}
            </div>
          </div>
        </td>
        {/* Health Status */}
        <td className="py-4">
          <StatusBadge status={(project.status as string) || "active"} />
        </td>
        {/* Actions */}
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
          <td colSpan={6} className="bg-slate-50 p-0">
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
                      .filter((fb: FeeBreakdown) => normalizeDiscipline(fb.discipline) === discipline)
                      .reduce((sum: number, fb: FeeBreakdown) => sum + (fb.phase_fee_usd || 0), 0);

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
                                  .filter((fb: FeeBreakdown) => normalizeDiscipline(fb.discipline) === discipline)
                                  .map((fb: FeeBreakdown) => fb.phase);

                                // Combine contract phases with invoice phases
                                const allPhases = new Set([...contractPhases, ...Object.keys(invoicesByPhase)]);

                                // Define phase order (correct sequence per user requirements)
                                const phaseOrder = [
                                  'Mobilization',
                                  'Concept Design',
                                  'Schematic Design',
                                  'Design Development',
                                  'Construction Documents',
                                  'Construction Observation'
                                ];

                                // Sort phases by defined order
                                // Check if phase name contains any of the order patterns
                                const getPhaseIndex = (phase: string): number => {
                                  const lowerPhase = phase.toLowerCase();
                                  for (let i = 0; i < phaseOrder.length; i++) {
                                    if (lowerPhase.includes(phaseOrder[i].toLowerCase())) {
                                      return i;
                                    }
                                  }
                                  return 999; // Unknown phases go last
                                };

                                const sortedPhases = Array.from(allPhases).sort((a, b) => {
                                  return getPhaseIndex(a) - getPhaseIndex(b);
                                });

                                return sortedPhases.map((phase: string) => {
                                // Get contract fee for this phase
                                const phaseFee = feeBreakdowns
                                  .filter((fb: FeeBreakdown) =>
                                    normalizeDiscipline(fb.discipline) === discipline &&
                                    fb.phase === phase
                                  )
                                  .reduce((sum: number, fb: FeeBreakdown) => sum + (fb.phase_fee_usd || 0), 0);

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
                                    {/* Invoice Details - Collapsible */}
                                    {phaseInvoices.length > 0 ? (
                                      <div className="mt-2">
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            onTogglePhaseInvoices(discipline, phase);
                                          }}
                                          className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
                                        >
                                          {expandedPhaseInvoices.has(`${projectCode}-${discipline}-${phase}`) ? (
                                            <>
                                              <ChevronDown className="h-4 w-4" />
                                              Hide {phaseInvoices.length} invoice{phaseInvoices.length !== 1 ? 's' : ''}
                                            </>
                                          ) : (
                                            <>
                                              <ChevronRight className="h-4 w-4" />
                                              View {phaseInvoices.length} invoice{phaseInvoices.length !== 1 ? 's' : ''}
                                            </>
                                          )}
                                        </button>

                                        {expandedPhaseInvoices.has(`${projectCode}-${discipline}-${phase}`) && (
                                          <div className="mt-2 space-y-2">
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
                                          </div>
                                        )}

                                        {phaseRemaining > 0 && (
                                          <div className="mt-2 rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-4">
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
                                      </div>
                                    ) : (
                                      <div className="mt-2 rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-4">
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
  const statusConfig: Record<string, { label: string; className: string }> = {
    active: { label: "Active", className: ds.badges.success },
    on_hold: { label: "On Hold", className: ds.badges.warning },
    at_risk: { label: "At Risk", className: ds.badges.danger },
    completed: { label: "Completed", className: ds.badges.default },
    cancelled: { label: "Cancelled", className: ds.badges.danger },
    archived: { label: "Archived", className: ds.badges.neutral },
    proposal: { label: "Proposal", className: ds.badges.info },
  };

  const config = statusConfig[status.toLowerCase()] || {
    label: status,
    className: ds.badges.neutral,
  };

  return (
    <span className={config.className}>
      {config.label}
    </span>
  );
}
