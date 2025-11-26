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
      <div className="flex min-h-screen items-center justify-center">
        <Card className="rounded-3xl border-rose-200 bg-rose-50">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="mx-auto h-12 w-12 text-rose-600" />
            <h2 className="mt-4 text-xl font-semibold text-slate-900">
              Project Not Found
            </h2>
            <p className="mt-2 text-slate-600">
              Could not load project {projectCode}
            </p>
            <Link href="/projects">
              <Button className="mt-6" variant="outline">
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
  const paidToDate = (projectDetail?.paid_to_date_usd as number) ?? 0;
  const outstandingAmount = (projectDetail?.outstanding_usd as number) ?? (contractValue - paidToDate);
  const paymentProgress = contractValue > 0 ? (paidToDate / contractValue) * 100 : 0;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link href="/projects">
            <Button variant="ghost" className="mb-4 gap-2">
              <ArrowLeft className="h-4 w-4" />
              Back to Projects
            </Button>
          </Link>
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold text-slate-900 lg:text-4xl">
                  {projectCode}
                </h1>
                <Badge variant="outline" className="rounded-full">
                  {(projectDetail?.current_phase as string) ?? (projectDetail?.phase as string) ?? "Unknown Phase"}
                </Badge>
              </div>
              <p className="mt-2 text-lg text-slate-600">
                {(projectDetail?.project_name as string) ?? (projectDetail?.client_name as string) ?? "Project Details"}
              </p>
              {(projectDetail?.client_name as string) && (
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
          <div className="flex h-64 items-center justify-center">
            <p className="text-slate-500">Loading project details...</p>
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
                  subtitle={`${Math.round(paymentProgress)}% of contract`}
                  iconColor="text-emerald-600"
                  bgColor="bg-emerald-50"
                />
                <FinancialCard
                  icon={<Clock className="h-5 w-5" />}
                  label="Outstanding"
                  value={formatCurrency(outstandingAmount)}
                  subtitle={`${invoices.filter((i: Record<string, unknown>) => i.status === "awaiting_payment").length} invoices`}
                  iconColor="text-rose-600"
                  bgColor="bg-rose-50"
                />
                <FinancialCard
                  icon={<TrendingUp className="h-5 w-5" />}
                  label="Payment Progress"
                  value={`${Math.round(paymentProgress)}%`}
                  iconColor="text-purple-600"
                  bgColor="bg-purple-50"
                />
              </div>

              {/* Payment Progress Bar */}
              <Card className="mt-6 rounded-3xl border-slate-200">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium text-slate-700">Payment Progress</p>
                    <p className="text-sm text-slate-500">{Math.round(paymentProgress)}%</p>
                  </div>
                  <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-600 transition-all"
                      style={{ width: `${Math.min(paymentProgress, 100)}%` }}
                    />
                  </div>
                  <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
                    <span>Paid: {formatCurrency(paidToDate)}</span>
                    <span>Remaining: {formatCurrency(contractValue - paidToDate)}</span>
                  </div>
                </CardContent>
              </Card>
            </section>

            {/* Invoices by Discipline & Phase */}
            <section className="mb-8">
              <h2 className="mb-4 text-xl font-semibold text-slate-900">Invoices by Scope</h2>
              {invoices.length === 0 ? (
                <Card className="rounded-3xl border-slate-200">
                  <CardContent className="p-6">
                    <p className="text-center text-sm text-slate-500 py-8">
                      No invoices found for this project
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <InvoicesByDiscipline invoices={invoices} />
              )}
            </section>

            {/* Schedule & Milestones */}
            {timeline?.milestones && Array.isArray(timeline.milestones) && timeline.milestones.length > 0 && (
              <section className="mb-8">
                <h2 className="mb-4 text-xl font-semibold text-slate-900">
                  Schedule & Milestones
                </h2>
                <Card className="rounded-3xl border-slate-200">
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
              <h2 className="mb-4 text-xl font-semibold text-slate-900">
                Communication & Documents
              </h2>
              <div className="grid gap-6 lg:grid-cols-2">
                {/* Recent Emails */}
                <Card className="rounded-3xl border-slate-200">
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
                    <Link href={`/emails?project=${projectCode}`}>
                      <Button variant="outline" className="mt-4 w-full">
                        View All Emails
                      </Button>
                    </Link>
                  </CardContent>
                </Card>

                {/* Documents */}
                <Card className="rounded-3xl border-slate-200">
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
              <h2 className="mb-4 text-xl font-semibold text-slate-900">
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
    <Card className="rounded-2xl border-slate-200 shadow-sm">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className={`rounded-xl ${bgColor} p-3 ${iconColor}`}>{icon}</div>
        </div>
        <div className="mt-4">
          <p className="text-sm font-medium text-slate-600">{label}</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
          {subtitle && (
            <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Phase ordering - Mobilization first, then design phases in order
const PHASE_ORDER: Record<string, number> = {
  'mobilization': 1,
  'master plan': 2,
  'master plan and preconcept': 2,
  'preconcept': 3,
  'concept': 4,
  'concept design': 4,
  'schematic': 5,
  'schematic design': 5,
  'sd': 5,
  'design development': 6,
  'dd': 6,
  'construction documents': 7,
  'cd': 7,
  'construction observation': 8,
  'co': 8,
  'construction administration': 9,
  'ca': 9,
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
          <Card key={discipline} className={`rounded-3xl border-2 ${colors.border}`}>
            <CardContent className="p-0">
              {/* Discipline Header */}
              <button
                onClick={() => toggleDiscipline(discipline)}
                className={`w-full flex items-center justify-between p-6 ${colors.bg} rounded-t-3xl hover:opacity-80 transition-opacity`}
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
