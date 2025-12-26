"use client";

import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ArrowLeft,
  Building2,
  Clock,
  TrendingUp,
  AlertTriangle,
  Calendar,
  CreditCard,
  Users,
  ListTodo,
  DollarSign,
  BarChart3,
} from "lucide-react";
import Link from "next/link";
import { use } from "react";
import { UnifiedTimeline } from "@/components/project/unified-timeline";
import { ProjectFeesCard } from "@/components/project/project-fees-card";
import { TaskMiniKanban } from "@/components/tasks/task-mini-kanban";
import { BensleyTeamCard } from "@/components/project/bensley-team-card";
import { ProjectContactsCard } from "@/components/project/project-contacts-card";
import { ProjectMeetingsCard } from "@/components/project/project-meetings-card";
import { ProjectEmailsCard } from "@/components/project/project-emails-card";
import { ProjectHealthBanner, calculateProjectHealth } from "@/components/project/project-health-banner";
import { RFIDeliverablesPanel } from "@/components/project/rfi-deliverables-panel";
import { WorkVsInvoiceWidget } from "@/components/project/work-vs-invoice-widget";
import { ProjectInsights } from "@/components/project/project-insights";
import { PhaseProgressBar } from "@/components/project/phase-progress-bar";
import { WeeklyScheduleGrid } from "@/components/project/weekly-schedule-grid";
import { PhaseTimeline } from "@/components/project/phase-timeline";
import { ds } from "@/lib/design-system";
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
  const { projectCode: rawProjectCode } = use(params);
  const projectCode = decodeURIComponent(rawProjectCode);

  // Fetch project data
  const projectDetailQuery = useQuery({
    queryKey: ["project", projectCode, "detail"],
    queryFn: () => api.getProjectDetail(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const invoicesQuery = useQuery({
    queryKey: ["project", projectCode, "invoices"],
    queryFn: () => api.getInvoicesByProject(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const phasesQuery = useQuery({
    queryKey: ["project-phases", projectCode],
    queryFn: () => api.getProjectPhases(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const teamQuery = useQuery({
    queryKey: ["project-team", projectCode],
    queryFn: () => api.getProjectTeam(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const projectDetail = projectDetailQuery.data;
  const invoices = invoicesQuery.data?.invoices ?? [];
  const phases = phasesQuery.data?.phases ?? [];
  const teamCount = teamQuery.data?.count ?? 0;

  const isLoading = projectDetailQuery.isLoading || invoicesQuery.isLoading;

  if (projectDetailQuery.error) {
    const errorMsg = projectDetailQuery.error instanceof Error
      ? projectDetailQuery.error.message
      : String(projectDetailQuery.error);
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
            <p className="text-xs text-red-600 mt-2 font-mono">
              Error: {errorMsg}
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
  const outstandingAmount = totalInvoiced - paidToDate;
  const invoicingProgress = contractValue > 0 ? (totalInvoiced / contractValue) * 100 : 0;
  const paymentProgress = totalInvoiced > 0 ? (paidToDate / totalInvoiced) * 100 : 0;

  // Count invoice stats
  const unpaidInvoices = invoices.filter((i: Record<string, unknown>) =>
    i.status === "awaiting_payment" || i.status === "pending" || i.status === "sent"
  ).length;

  // Health calculation
  const health = calculateProjectHealth({
    overdue_invoices_count: invoices.filter((i: Record<string, unknown>) =>
      i.status !== 'paid' && i.due_date && new Date(i.due_date as string) < new Date()
    ).length,
    overdue_invoices_amount: invoices
      .filter((i: Record<string, unknown>) => i.status !== 'paid' && i.due_date && new Date(i.due_date as string) < new Date())
      .reduce((sum: number, i: Record<string, unknown>) => sum + ((i.invoice_amount as number) || 0), 0),
    open_rfis_count: (projectDetail?.open_rfis_count as number) ?? 0,
    days_since_activity: (projectDetail?.days_since_activity as number) ?? 0,
    overdue_deliverables_count: (projectDetail?.overdue_deliverables_count as number) ?? 0,
  });

  return (
    <div className={cn(ds.gap.loose, "space-y-6 w-full max-w-full overflow-x-hidden")}>
      {/* Header */}
      <div className="mb-2">
        <Link href="/projects">
          <Button variant="ghost" className={cn(ds.buttons.ghost, "mb-4 gap-2")}>
            <ArrowLeft className="h-4 w-4" />
            Back to Projects
          </Button>
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className={ds.typography.pageTitle}>
                {(projectDetail?.project_name as string) ?? (projectDetail?.client_name as string) ?? projectCode}
              </h1>
              <Badge className={ds.badges.default}>
                {(projectDetail?.current_phase as string) ?? (projectDetail?.phase as string) ?? "Unknown Phase"}
              </Badge>
            </div>
            <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
              <span className="font-mono">{projectCode}</span>
              {(projectDetail?.client_name as string) && (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Building2 className="h-3.5 w-3.5" />
                    {projectDetail?.client_name as string}
                  </span>
                </>
              )}
              {teamCount > 0 && (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Users className="h-3.5 w-3.5" />
                    {teamCount} team member{teamCount !== 1 ? 's' : ''}
                  </span>
                </>
              )}
              {(projectDetail?.contract_signed_date as string) && (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    Since {formatDisplayDate(projectDetail?.contract_signed_date as string)}
                  </span>
                </>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 justify-end mb-1">
              <Badge
                variant="outline"
                className={cn(
                  "text-xs",
                  outstandingAmount > 0
                    ? "bg-amber-50 text-amber-700 border-amber-200"
                    : "bg-emerald-50 text-emerald-700 border-emerald-200"
                )}
              >
                {outstandingAmount > 0 ? `${formatCurrency(outstandingAmount)} outstanding` : "Paid up"}
              </Badge>
              <Badge
                variant="outline"
                className={cn(
                  "text-xs",
                  (projectDetail?.status as string) === "Active"
                    ? "bg-teal-50 text-teal-700 border-teal-200"
                    : "bg-slate-100 text-slate-600 border-slate-200"
                )}
              >
                {(projectDetail?.status as string) || "Active"}
              </Badge>
            </div>
            <p className="text-sm text-slate-500">Contract Value</p>
            <p className="text-3xl font-bold text-slate-900">
              {formatCurrency(contractValue)}
            </p>
            <div className="mt-2 w-48 ml-auto">
              <div className="flex justify-between text-xs text-slate-500 mb-1">
                <span>{Math.round(invoicingProgress)}% invoiced</span>
                <span>{Math.round(paymentProgress)}% paid</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-teal-500 to-emerald-500 transition-all"
                  style={{ width: `${Math.min(invoicingProgress, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className={cn(ds.cards.default, "animate-pulse")}>
                <CardContent className="p-6">
                  <div className="h-5 w-32 bg-slate-200 rounded mb-4" />
                  <div className="h-10 w-24 bg-slate-200 rounded mb-2" />
                  <div className="h-4 w-full bg-slate-200 rounded" />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      ) : (
        <>
          {/* Health Banner */}
          <ProjectHealthBanner
            status={health.status}
            issues={health.issues}
            projectName={(projectDetail?.project_name as string) ?? projectCode}
            className="mb-2"
          />

          {/* Tabbed Content */}
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-flex">
              <TabsTrigger value="overview" className="gap-2">
                <BarChart3 className="h-4 w-4" />
                <span className="hidden sm:inline">Overview</span>
              </TabsTrigger>
              <TabsTrigger value="phases" className="gap-2">
                <Calendar className="h-4 w-4" />
                <span className="hidden sm:inline">Phases</span>
              </TabsTrigger>
              <TabsTrigger value="team" className="gap-2">
                <Users className="h-4 w-4" />
                <span className="hidden sm:inline">Team</span>
              </TabsTrigger>
              <TabsTrigger value="tasks" className="gap-2">
                <ListTodo className="h-4 w-4" />
                <span className="hidden sm:inline">Tasks</span>
              </TabsTrigger>
              <TabsTrigger value="finance" className="gap-2">
                <DollarSign className="h-4 w-4" />
                <span className="hidden sm:inline">Finance</span>
              </TabsTrigger>
            </TabsList>

            {/* OVERVIEW TAB */}
            <TabsContent value="overview" className="space-y-6 mt-6">
              {/* Project Insights */}
              <ProjectInsights
                projectCode={projectCode}
                projectDetail={projectDetail as Record<string, unknown>}
                invoices={invoices}
              />

              {/* Quick Stats Grid */}
              <div className="grid gap-4 lg:grid-cols-4">
                <Card className="border-l-4 border-l-teal-500">
                  <CardContent className="pt-4">
                    <p className="text-xs font-medium text-slate-500 uppercase">Phase</p>
                    <p className="text-lg font-bold text-slate-900 mt-1">
                      {(projectDetail?.current_phase as string) || "Not Started"}
                    </p>
                    <p className="text-xs text-slate-500">
                      {phases.filter((p: { status: string }) => p.status === 'completed').length} of {phases.length} complete
                    </p>
                  </CardContent>
                </Card>

                <Card className="border-l-4 border-l-blue-500">
                  <CardContent className="pt-4">
                    <p className="text-xs font-medium text-slate-500 uppercase">Team Size</p>
                    <p className="text-lg font-bold text-slate-900 mt-1">{teamCount}</p>
                    <p className="text-xs text-slate-500">Bensley members assigned</p>
                  </CardContent>
                </Card>

                <Card className="border-l-4 border-l-amber-500">
                  <CardContent className="pt-4">
                    <p className="text-xs font-medium text-slate-500 uppercase">Outstanding</p>
                    <p className="text-lg font-bold text-slate-900 mt-1">
                      {formatCurrency(Math.max(0, outstandingAmount))}
                    </p>
                    <p className="text-xs text-slate-500">{unpaidInvoices} unpaid invoices</p>
                  </CardContent>
                </Card>

                <Card className="border-l-4 border-l-emerald-500">
                  <CardContent className="pt-4">
                    <p className="text-xs font-medium text-slate-500 uppercase">Collected</p>
                    <p className="text-lg font-bold text-slate-900 mt-1">
                      {formatCurrency(paidToDate)}
                    </p>
                    <p className="text-xs text-slate-500">{Math.round(paymentProgress)}% of invoiced</p>
                  </CardContent>
                </Card>
              </div>

              {/* Communication Preview */}
              <div className="grid gap-6 lg:grid-cols-2">
                <ProjectEmailsCard projectCode={projectCode} limit={5} />
                <ProjectMeetingsCard projectCode={projectCode} />
              </div>

              {/* Activity Timeline */}
              <section>
                <h2 className={cn(ds.typography.cardHeader, ds.textColors.primary, "mb-4")}>
                  Recent Activity
                </h2>
                <UnifiedTimeline projectCode={projectCode} limit={20} />
              </section>
            </TabsContent>

            {/* PHASES TAB */}
            <TabsContent value="phases" className="space-y-6 mt-6">
              {/* Phase Progress Bar */}
              <Card className={ds.cards.default}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5 text-teal-600" />
                    Phase Progress
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {phases.length > 0 ? (
                    <PhaseProgressBar
                      phases={phases.map((p: { phase_name: string; status: string }) => ({
                        phase_name: p.phase_name,
                        status: p.status,
                      }))}
                    />
                  ) : (
                    <p className="text-sm text-slate-500 text-center py-8">
                      No phases defined for this project
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Phase Details Table */}
              <Card className={ds.cards.default}>
                <CardHeader>
                  <CardTitle>Phase Details</CardTitle>
                </CardHeader>
                <CardContent>
                  {phases.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-200">
                            <th className="text-left py-3 px-4 font-medium text-slate-500">Phase</th>
                            <th className="text-left py-3 px-4 font-medium text-slate-500">Status</th>
                            <th className="text-left py-3 px-4 font-medium text-slate-500">Discipline</th>
                            <th className="text-right py-3 px-4 font-medium text-slate-500">Fee</th>
                          </tr>
                        </thead>
                        <tbody>
                          {phases.map((phase: { phase_id: number; phase_name: string; status: string; discipline?: string; phase_fee_usd?: number }) => (
                            <tr key={phase.phase_id} className="border-b border-slate-100">
                              <td className="py-3 px-4 font-medium">{phase.phase_name}</td>
                              <td className="py-3 px-4">
                                <Badge
                                  variant="outline"
                                  className={cn(
                                    "text-xs",
                                    phase.status === 'completed' ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
                                    phase.status === 'in_progress' ? "bg-blue-50 text-blue-700 border-blue-200" :
                                    "bg-slate-100 text-slate-600 border-slate-200"
                                  )}
                                >
                                  {phase.status}
                                </Badge>
                              </td>
                              <td className="py-3 px-4 text-slate-600">{phase.discipline || "—"}</td>
                              <td className="py-3 px-4 text-right font-medium">
                                {phase.phase_fee_usd ? formatCurrency(phase.phase_fee_usd) : "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500 text-center py-8">
                      No phases defined
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Phase Timeline */}
              <PhaseTimeline projectCode={projectCode} />
            </TabsContent>

            {/* TEAM TAB */}
            <TabsContent value="team" className="space-y-6 mt-6">
              <div className="grid gap-6 lg:grid-cols-2">
                <BensleyTeamCard projectCode={projectCode} />
                <ProjectContactsCard projectCode={projectCode} />
              </div>

              {/* Weekly Schedule Grid */}
              <WeeklyScheduleGrid projectCode={projectCode} />
            </TabsContent>

            {/* TASKS TAB */}
            <TabsContent value="tasks" className="space-y-6 mt-6">
              {/* RFI/Deliverables Panel */}
              <RFIDeliverablesPanel
                rfis={(projectDetail?.rfis as Array<{rfi_id: number; rfi_number?: string; subject: string; status: "open" | "answered" | "closed"; submitted_date: string; response_date?: string | null; days_open?: number}>) ?? []}
                deliverables={(projectDetail?.deliverables as Array<{deliverable_id: number; name: string; status: "pending" | "in_progress" | "delivered" | "approved"; due_date: string | null; delivered_date?: string | null; responsible_party?: string}>) ?? []}
                projectCode={projectCode}
              />

              {/* Tasks Card */}
              <TaskMiniKanban projectCode={projectCode} />
            </TabsContent>

            {/* FINANCE TAB */}
            <TabsContent value="finance" className="space-y-6 mt-6">
              {/* Main Dashboard Cards */}
              <div className="grid gap-6 lg:grid-cols-3">
                <ProjectFeesCard
                  projectCode={projectCode}
                  contractValue={contractValue}
                />

                {/* Payments Card */}
                <Card className={ds.cards.default}>
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <CreditCard className="h-4 w-4 text-emerald-600" />
                      Payments
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-baseline justify-between">
                          <span className={ds.typography.metricLarge}>{formatCurrency(paidToDate)}</span>
                          <span className="text-sm text-emerald-600 font-medium">
                            {Math.round(paymentProgress)}% collected
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">of {formatCurrency(totalInvoiced)} invoiced</p>
                      </div>

                      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-600 transition-all"
                          style={{ width: `${Math.min(paymentProgress, 100)}%` }}
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4 pt-2">
                        <div className="p-3 rounded-lg bg-slate-50">
                          <div className="flex items-center gap-2 mb-1">
                            <TrendingUp className="h-4 w-4 text-purple-600" />
                            <span className="text-xs text-slate-500">Invoiced</span>
                          </div>
                          <p className="text-lg font-semibold text-slate-900">
                            {formatCurrency(totalInvoiced)}
                          </p>
                          <p className="text-xs text-slate-500">
                            {Math.round(invoicingProgress)}% of contract
                          </p>
                        </div>
                        <div className="p-3 rounded-lg bg-slate-50">
                          <div className="flex items-center gap-2 mb-1">
                            <Clock className="h-4 w-4 text-amber-600" />
                            <span className="text-xs text-slate-500">Outstanding</span>
                          </div>
                          <p className="text-lg font-semibold text-slate-900">
                            {formatCurrency(Math.max(0, outstandingAmount))}
                          </p>
                          <p className="text-xs text-slate-500">
                            {unpaidInvoices} unpaid invoice{unpaidInvoices !== 1 ? 's' : ''}
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Tasks Card for Finance Tab */}
                <TaskMiniKanban projectCode={projectCode} />
              </div>

              {/* Work vs Invoice Progress */}
              <WorkVsInvoiceWidget projectCode={projectCode} />
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
}
