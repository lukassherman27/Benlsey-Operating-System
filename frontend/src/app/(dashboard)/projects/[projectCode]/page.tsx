"use client";

import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  FileText,
  Mail,
  TrendingUp,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import Link from "next/link";
import { useState, use } from "react";
import { UnifiedTimeline } from "@/components/project/unified-timeline";
import { ds, bensleyVoice } from "@/lib/design-system";
import { cn } from "@/lib/utils";

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

const formatDisplayDate = (value?: string | null) => {
  if (!value) return "—";
  try {
    return format(new Date(value), "MMM d, yyyy");
  } catch {
    return value;
  }
};

export default function ProjectDetailPage({
  params,
}: {
  params: Promise<{ projectCode: string }>;
}) {
  const { projectCode } = use(params);

  // Fetch project data
  const projectDetailQuery = useQuery({
    queryKey: ["project", projectCode, "detail"],
    queryFn: () => api.getProjectDetail(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const projectTimelineQuery = useQuery({
    queryKey: ["project", projectCode, "timeline"],
    queryFn: () => api.getProjectTimeline(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const invoicesQuery = useQuery({
    queryKey: ["project", projectCode, "invoices"],
    queryFn: () => api.getInvoicesByProject(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const projectDetail = projectDetailQuery.data;
  const timeline = projectTimelineQuery.data;
  const invoices = invoicesQuery.data?.invoices ?? [];

  const isLoading =
    projectDetailQuery.isLoading ||
    projectTimelineQuery.isLoading ||
    invoicesQuery.isLoading;

  if (projectDetailQuery.error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Card className={cn(ds.cards.default, "border-red-200 bg-red-50")}>
          <CardContent className="p-8 text-center">
            <AlertTriangle className="mx-auto h-12 w-12 text-red-600" />
            <h2 className={cn(ds.typography.cardHeader, "mt-4")}>
              Project Not Found
            </h2>
            <p className={cn(ds.typography.bodySmall, "mt-2")}>
              Could not load project {projectCode}
            </p>
            <Link href="/projects">
              <Button className={cn(ds.buttons.secondary, "mt-6")}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Projects
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Calculate financial stats
  const contractValue = (projectDetail?.contract_value_usd as number) ?? (projectDetail?.total_fee_usd as number) ?? 0;
  const totalInvoiced = (projectDetail?.total_invoiced as number) ?? 0;
  const paidToDate = (projectDetail?.paid_to_date_usd as number) ?? 0;
  const outstandingAmount = totalInvoiced - paidToDate; // Outstanding = Invoiced - Paid
  const invoicingProgress = contractValue > 0 ? (totalInvoiced / contractValue) * 100 : 0;
  const paymentProgress = totalInvoiced > 0 ? (paidToDate / totalInvoiced) * 100 : 0;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link href="/projects">
            <Button variant="ghost" className={cn(ds.buttons.ghost, "mb-4 gap-2")}>
              <ArrowLeft className="h-4 w-4" />
              Back to Projects
            </Button>
          </Link>
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h1 className={ds.typography.pageTitle}>
                  {(projectDetail?.project_name as string) ?? (projectDetail?.client_name as string) ?? projectCode}
                </h1>
                <span className={ds.badges.default}>
                  {(projectDetail?.current_phase as string) ?? (projectDetail?.phase as string) ?? "Unknown Phase"}
                </span>
              </div>
              <p className={cn(ds.typography.bodySmall, "mt-2")}>
                <span className="text-slate-500">{projectCode}</span>
              </p>
              {(projectDetail?.client_name as string) && (projectDetail?.project_name as string) && (
                <p className="mt-1 text-sm text-slate-500">
                  Client: {projectDetail?.client_name as string}
                </p>
              )}
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-500">Contract Value</p>
              <p className="text-2xl font-bold text-slate-900">
                {formatCurrency(contractValue)}
              </p>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-6">
            {/* Skeleton for financial summary */}
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <Card key={i} className={cn(ds.cards.default, "animate-pulse")}>
                  <CardContent className="p-6">
                    <div className="h-10 w-10 bg-slate-200 rounded-xl mb-4" />
                    <div className="h-4 w-20 bg-slate-200 rounded mb-2" />
                    <div className="h-8 w-32 bg-slate-200 rounded" />
                  </CardContent>
                </Card>
              ))}
            </div>
            {/* Skeleton for invoices section */}
            <Card className={cn(ds.cards.default, "animate-pulse")}>
              <CardContent className="p-6 space-y-4">
                <div className="h-6 w-48 bg-slate-200 rounded" />
                <div className="h-4 w-full bg-slate-200 rounded" />
                <div className="h-4 w-3/4 bg-slate-200 rounded" />
              </CardContent>
            </Card>
          </div>
        ) : (
          <>
            {/* Financial Summary */}
            <section className="mb-8">
              <h2 className="mb-4 text-xl font-semibold text-slate-900">
                Financial Summary
              </h2>
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <FinancialCard
                  icon={<DollarSign className="h-5 w-5" />}
                  label="Contract Value"
                  value={formatCurrency(contractValue)}
                  iconColor="text-blue-600"
                  bgColor="bg-blue-50"
                />
                <FinancialCard
                  icon={<CheckCircle2 className="h-5 w-5" />}
                  label="Paid to Date"
                  value={formatCurrency(paidToDate)}
                  subtitle={`${Math.round(paymentProgress)}% of invoiced`}
                  iconColor="text-emerald-600"
                  bgColor="bg-emerald-50"
                />
                <FinancialCard
                  icon={<Clock className="h-5 w-5" />}
                  label="Outstanding"
                  value={formatCurrency(outstandingAmount > 0 ? outstandingAmount : 0)}
                  subtitle={`${invoices.filter((i: Record<string, unknown>) => i.status === "awaiting_payment").length} unpaid invoices`}
                  iconColor="text-rose-600"
                  bgColor="bg-rose-50"
                />
                <FinancialCard
                  icon={<TrendingUp className="h-5 w-5" />}
                  label="Invoiced"
                  value={formatCurrency(totalInvoiced)}
                  subtitle={`${Math.round(invoicingProgress)}% of contract`}
                  iconColor="text-purple-600"
                  bgColor="bg-purple-50"
                />
              </div>

              {/* Progress Bars - Invoicing and Payment */}
              <Card className={cn(ds.cards.default, "mt-6")}>
                <CardContent className="p-6 space-y-6">
                  {/* Invoicing Progress (% of contract invoiced) */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium text-slate-700">Invoicing Progress</p>
                      <p className="text-sm text-slate-500">{Math.round(invoicingProgress)}% of contract</p>
                    </div>
                    <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-purple-500 to-purple-600 transition-all"
                        style={{ width: `${Math.min(invoicingProgress, 100)}%` }}
                      />
                    </div>
                    <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                      <span>Invoiced: {formatCurrency(totalInvoiced)}</span>
                      <span>Remaining to invoice: {formatCurrency(Math.max(0, contractValue - totalInvoiced))}</span>
                    </div>
                  </div>

                  {/* Payment Progress (% of invoiced amount paid) */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium text-slate-700">Payment Progress</p>
                      <p className="text-sm text-slate-500">{Math.round(paymentProgress)}% of invoiced</p>
                    </div>
                    <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-600 transition-all"
                        style={{ width: `${Math.min(paymentProgress, 100)}%` }}
                      />
                    </div>
                    <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                      <span>Paid: {formatCurrency(paidToDate)}</span>
                      <span>Outstanding: {formatCurrency(Math.max(0, outstandingAmount))}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </section>

            {/* Invoices by Discipline & Phase */}
            <section className="mb-8">
              <h2 className={cn(ds.typography.sectionHeader, "mb-4")}>Invoices by Scope</h2>
              {invoices.length === 0 ? (
                <Card className={ds.cards.default}>
                  <CardContent className="p-6 py-12 text-center">
                    <FileText className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                    <p className={ds.typography.cardHeader}>{bensleyVoice.emptyStates.invoices}</p>
                    <p className={cn(ds.typography.caption, "mt-2")}>No invoices found for this project</p>
                  </CardContent>
                </Card>
              ) : (
                <InvoicesByDiscipline invoices={invoices} />
              )}
            </section>

            {/* Schedule & Milestones */}
            {timeline?.milestones && Array.isArray(timeline.milestones) && timeline.milestones.length > 0 && (
              <section className="mb-8">
                <h2 className={cn(ds.typography.sectionHeader, "mb-4")}>
                  Schedule & Milestones
                </h2>
                <Card className={ds.cards.default}>
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      {timeline.milestones.map((milestone: Record<string, unknown>) => {
                        const isUpcoming = milestone.target_date &&
                          new Date(milestone.target_date as string) > new Date();
                        const isCompleted = milestone.status === "completed" || milestone.completed_date;

                        return (
                          <div
                            key={milestone.milestone_id as string}
                            className="flex items-start gap-4 rounded-2xl border border-slate-200 p-4"
                          >
                            <div className={`rounded-full p-2 ${isCompleted ? "bg-emerald-50" : "bg-blue-50"}`}>
                              {isCompleted ? (
                                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                              ) : (
                                <Calendar className="h-5 w-5 text-blue-600" />
                              )}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="font-medium text-slate-900">
                                    {(milestone.milestone_name as string) ?? (milestone.phase as string)}
                                  </p>
                                  <p className="text-sm text-slate-600">
                                    {(milestone.description as string) ?? ""}
                                  </p>
                                </div>
                                <div className="text-right">
                                  <p className="text-sm font-medium text-slate-900">
                                    {formatDisplayDate((milestone.target_date as string) ?? (milestone.completed_date as string))}
                                  </p>
                                  {isCompleted ? (
                                    <Badge variant="outline" className="mt-1 rounded-full bg-emerald-50 text-emerald-700">
                                      Completed
                                    </Badge>
                                  ) : isUpcoming ? (
                                    <Badge variant="secondary" className="mt-1 rounded-full">
                                      Upcoming
                                    </Badge>
                                  ) : (
                                    <Badge variant="destructive" className="mt-1 rounded-full">
                                      Overdue
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              </section>
            )}

            {/* Communication & Documents */}
            <section className="mb-8">
              <h2 className={cn(ds.typography.sectionHeader, "mb-4")}>
                Communication & Documents
              </h2>
              <div className="grid gap-6 lg:grid-cols-2">
                {/* Recent Emails */}
                <Card className={ds.cards.default}>
                  <CardContent className="p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <Mail className="h-5 w-5 text-blue-600" />
                      <h3 className="font-semibold text-slate-900">Recent Emails</h3>
                    </div>
                    <div className="space-y-3">
                      {timeline?.recent_emails && Array.isArray(timeline.recent_emails) && timeline.recent_emails.length > 0 ? (
                        timeline.recent_emails.slice(0, 5).map((email: Record<string, unknown>) => (
                          <div
                            key={email.email_id as string}
                            className="rounded-xl border border-slate-200 p-3"
                          >
                            <p className="text-sm font-medium text-slate-900">
                              {email.subject as string}
                            </p>
                            <p className="text-xs text-slate-500">
                              From: {email.sender_email as string} • {formatDisplayDate(email.received_date as string)}
                            </p>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-slate-500">No recent emails</p>
                      )}
                    </div>
                    <Link href={`/projects/${projectCode}/emails`}>
                      <Button variant="outline" className="mt-4 w-full">
                        View All Emails
                      </Button>
                    </Link>
                  </CardContent>
                </Card>

                {/* Documents */}
                <Card className={ds.cards.default}>
                  <CardContent className="p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <FileText className="h-5 w-5 text-purple-600" />
                      <h3 className="font-semibold text-slate-900">Documents</h3>
                    </div>
                    <div className="space-y-3">
                      {/* Contract */}
                      <div className="rounded-xl border border-slate-200 p-3">
                        <p className="text-sm font-medium text-slate-900">
                          Contract Agreement
                        </p>
                        <p className="text-xs text-slate-500">
                          Signed: {formatDisplayDate(projectDetail?.contract_date as string)}
                        </p>
                      </div>
                      {/* Add more document types as needed */}
                      <p className="text-sm text-slate-500">
                        Additional documents will be listed here
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </section>

            {/* Unified Project Timeline */}
            <section className="mb-8">
              <h2 className={cn(ds.typography.sectionHeader, "mb-4")}>
                Project Activity Timeline
              </h2>
              <UnifiedTimeline projectCode={projectCode} limit={30} />
            </section>
          </>
        )}
      </div>
    </div>
  );
}

function FinancialCard({
  icon,
  label,
  value,
  subtitle,
  iconColor,
  bgColor,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  subtitle?: string;
  iconColor: string;
  bgColor: string;
}) {
  return (
    <Card className={ds.cards.default}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className={cn("rounded-xl p-3", bgColor, iconColor)}>{icon}</div>
        </div>
        <div className="mt-4">
          <p className={ds.typography.metricLabel}>{label}</p>
          <p className={cn(ds.typography.metricLarge, "mt-2")}>{value}</p>
          {subtitle && (
            <p className={cn(ds.typography.caption, "mt-1")}>{subtitle}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Phase ordering per user requirements:
// 1. Mobilization, 2. Concept Design, 3. Design Development, 4. Construction Documents, 5. Construction Observation
const PHASE_ORDER: Record<string, number> = {
  'mobilization': 1,
  'concept': 2,
  'concept design': 2,
  'design development': 3,
  'dd': 3,
  'construction documents': 4,
  'construction drawings': 4,
  'cd': 4,
  'construction observation': 5,
  'co': 5,
  'construction administration': 5,
  'ca': 5,
  'schematic': 6,
  'schematic design': 6,
  'sd': 6,
  'master plan': 7,
  'preconcept': 8,
  'general': 99,
  'other': 100,
};

const getPhaseOrder = (phase: string): number => {
  const normalized = phase.toLowerCase().trim();
  return PHASE_ORDER[normalized] || 50;
};

function InvoicesByDiscipline({ invoices }: { invoices: Record<string, unknown>[] }) {
  const [expandedDisciplines, setExpandedDisciplines] = useState<Set<string>>(new Set());
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set());

  // Group invoices by discipline and phase
  const groupedInvoices = invoices.reduce((acc: Record<string, Record<string, Record<string, unknown>[]>>, invoice: Record<string, unknown>) => {
    const discipline = (invoice.discipline as string) || (invoice.project_phase as string) || "Other";
    const phase = (invoice.phase as string) || (invoice.invoice_description as string) || "General";

    if (!acc[discipline]) {
      acc[discipline] = {};
    }
    if (!acc[discipline][phase]) {
      acc[discipline][phase] = [];
    }
    acc[discipline][phase].push(invoice);

    return acc;
  }, {});

  // Sort phases within each discipline
  const sortedGroupedInvoices = Object.fromEntries(
    Object.entries(groupedInvoices).map(([discipline, phases]) => [
      discipline,
      Object.fromEntries(
        Object.entries(phases).sort(([phaseA], [phaseB]) =>
          getPhaseOrder(phaseA) - getPhaseOrder(phaseB)
        )
      )
    ])
  );

  const toggleDiscipline = (discipline: string) => {
    const newExpanded = new Set(expandedDisciplines);
    if (newExpanded.has(discipline)) {
      newExpanded.delete(discipline);
    } else {
      newExpanded.add(discipline);
    }
    setExpandedDisciplines(newExpanded);
  };

  const togglePhase = (key: string) => {
    const newExpanded = new Set(expandedPhases);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedPhases(newExpanded);
  };

  const getDisciplineColor = (discipline: string) => {
    const colors: Record<string, { bg: string; text: string; border: string }> = {
      "Landscape Architecture": { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" },
      "Interior Design": { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200" },
      "Architecture": { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
      "Landscape": { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" },
      "Interior": { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200" },
      "Other": { bg: "bg-slate-50", text: "text-slate-700", border: "border-slate-200" },
    };
    return colors[discipline] || colors["Other"];
  };

  // Calculate grand totals for summary bar
  const grandTotalAmount = invoices.reduce((sum, inv) => sum + ((inv.amount_usd as number) || 0), 0);
  const grandTotalPaid = invoices.reduce((sum, inv) =>
    sum + (inv.status === "paid" ? ((inv.payment_amount_usd as number) || (inv.amount_usd as number) || 0) : 0), 0
  );
  const grandTotalOutstanding = grandTotalAmount - grandTotalPaid;

  return (
    <div className="space-y-6">
      {/* Summary Bar */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <div className="grid grid-cols-4 gap-4">
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide">Total Invoiced</div>
            <div className="text-xl font-bold text-slate-900">{formatCurrency(grandTotalAmount)}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide">Amount Paid</div>
            <div className="text-xl font-bold text-emerald-600">{formatCurrency(grandTotalPaid)}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide">Amount Due</div>
            <div className="text-xl font-bold text-orange-600">{formatCurrency(grandTotalOutstanding)}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide">Progress</div>
            <div className="text-xl font-bold text-blue-600">
              {grandTotalAmount > 0 ? Math.round((grandTotalPaid / grandTotalAmount) * 100) : 0}%
            </div>
          </div>
        </div>
      </div>

      {/* Invoices by Discipline */}
      {Object.entries(sortedGroupedInvoices).map(([discipline, phases]: [string, Record<string, Record<string, unknown>[]>]) => {
        const isExpanded = expandedDisciplines.has(discipline);
        const colors = getDisciplineColor(discipline);

        // Calculate totals for this discipline
        const disciplineInvoices = Object.values(phases).flat() as Record<string, unknown>[];
        const totalAmount = disciplineInvoices.reduce((sum, inv) => sum + ((inv.amount_usd as number) || 0), 0);
        const totalPaid = disciplineInvoices.reduce((sum, inv) =>
          sum + (inv.status === "paid" ? ((inv.payment_amount_usd as number) || (inv.amount_usd as number) || 0) : 0), 0
        );
        const totalOutstanding = totalAmount - totalPaid;

        return (
          <Card key={discipline} className={cn(ds.cards.default, "border-2", colors.border)}>
            <CardContent className="p-0">
              {/* Discipline Header */}
              <button
                onClick={() => toggleDiscipline(discipline)}
                className={cn("w-full flex items-center justify-between p-6 rounded-t-xl hover:opacity-80 transition-opacity", colors.bg)}
              >
                <div className="flex items-center gap-3">
                  {isExpanded ? (
                    <ChevronDown className={`h-5 w-5 ${colors.text}`} />
                  ) : (
                    <ChevronRight className={`h-5 w-5 ${colors.text}`} />
                  )}
                  <h3 className={`text-lg font-semibold ${colors.text}`}>
                    {discipline}
                  </h3>
                  <Badge variant="outline" className={`${colors.bg} ${colors.text}`}>
                    {disciplineInvoices.length} invoice{disciplineInvoices.length !== 1 ? "s" : ""}
                  </Badge>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-medium ${colors.text}`}>
                    {formatCurrency(totalAmount)}
                  </p>
                  <p className="text-xs text-slate-500">
                    Outstanding: {formatCurrency(totalOutstanding)}
                  </p>
                </div>
              </button>

              {/* Phases */}
              {isExpanded && (
                <div className="p-4 space-y-3">
                  {Object.entries(phases).map(([phase, phaseInvoices]: [string, Record<string, unknown>[]]) => {
                    const phaseKey = `${discipline}-${phase}`;
                    const isPhaseExpanded = expandedPhases.has(phaseKey);

                    const phaseTotal = phaseInvoices.reduce((sum: number, inv: Record<string, unknown>) =>
                      sum + ((inv.amount_usd as number) || 0), 0
                    );
                    const phasePaid = phaseInvoices.reduce((sum: number, inv: Record<string, unknown>) =>
                      sum + (inv.status === "paid" ? ((inv.payment_amount_usd as number) || (inv.amount_usd as number) || 0) : 0), 0
                    );
                    const phaseOutstanding = phaseTotal - phasePaid;

                    return (
                      <div key={phaseKey} className="rounded-2xl border border-slate-200 overflow-hidden">
                        {/* Phase Header */}
                        <button
                          onClick={() => togglePhase(phaseKey)}
                          className="w-full flex items-center justify-between p-4 bg-slate-50 hover:bg-slate-100 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            {isPhaseExpanded ? (
                              <ChevronDown className="h-4 w-4 text-slate-600" />
                            ) : (
                              <ChevronRight className="h-4 w-4 text-slate-600" />
                            )}
                            <span className="font-medium text-slate-900">{phase}</span>
                            <Badge variant="secondary" className="text-xs">
                              {phaseInvoices.length}
                            </Badge>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-medium text-slate-900">
                              {formatCurrency(phaseTotal)}
                            </p>
                            <p className="text-xs text-slate-500">
                              Outstanding: {formatCurrency(phaseOutstanding)}
                            </p>
                          </div>
                        </button>

                        {/* Invoice Details - Compact Format */}
                        {isPhaseExpanded && (
                          <div className="divide-y divide-slate-100">
                            {phaseInvoices.map((invoice: Record<string, unknown>) => {
                              const isPaid = invoice.status === "paid";
                              const amountPaid = isPaid ? ((invoice.payment_amount_usd as number) || (invoice.amount_usd as number) || 0) : 0;
                              const outstanding = ((invoice.amount_usd as number) || 0) - amountPaid;

                              return (
                                <div
                                  key={invoice.invoice_id as string}
                                  className="px-4 py-3 flex justify-between items-start hover:bg-slate-50 transition-colors"
                                >
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                      <span className="font-medium text-slate-900">
                                        {invoice.invoice_number as string || "—"}
                                      </span>
                                      <Badge
                                        variant={isPaid ? "outline" : "secondary"}
                                        className={`text-xs ${isPaid ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-orange-50 text-orange-700 border-orange-200"}`}
                                      >
                                        {isPaid ? "Paid" : "Outstanding"}
                                      </Badge>
                                    </div>
                                    <div className="text-xs text-slate-500 mt-1">
                                      Invoiced: {formatDisplayDate(invoice.invoice_date as string)}
                                      {isPaid && (invoice.payment_received_date as string | null) && (
                                        <span className="text-emerald-600 ml-2">
                                          • Paid: {formatDisplayDate(invoice.payment_received_date as string)}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <div className="font-semibold text-slate-900">
                                      {formatCurrency(invoice.amount_usd as number)}
                                    </div>
                                    {!isPaid && outstanding > 0 && (
                                      <div className="text-xs text-orange-600">
                                        Due: {formatCurrency(outstanding)}
                                      </div>
                                    )}
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
      })}
    </div>
  );
}
