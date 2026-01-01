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
  ClipboardList,
  Package,
} from "lucide-react";
import Link from "next/link";
import { use, useState } from "react";
import { UnifiedTimeline } from "@/components/project/unified-timeline";
import { ProjectFeesCard } from "@/components/project/project-fees-card";
import { TaskMiniKanban } from "@/components/tasks/task-mini-kanban";
import { BensleyTeamCard } from "@/components/project/bensley-team-card";
import { ProjectContactsCard } from "@/components/project/project-contacts-card";
import { ProjectMeetingsCard } from "@/components/project/project-meetings-card";
import { ProjectEmailsCard } from "@/components/project/project-emails-card";
import { ProjectInvoicesCard } from "@/components/project/project-invoices-card";
import { ProjectHealthBanner, calculateProjectHealth } from "@/components/project/project-health-banner";
import { RFIDeliverablesPanel } from "@/components/project/rfi-deliverables-panel";
import { WorkVsInvoiceWidget } from "@/components/project/work-vs-invoice-widget";
import { ProjectInsights } from "@/components/project/project-insights";
import { PhaseProgressBar } from "@/components/project/phase-progress-bar";
import { WeeklyScheduleGrid } from "@/components/project/weekly-schedule-grid";
import { PhaseTimeline } from "@/components/project/phase-timeline";
import { DailyWorkSubmissionForm, DailyWorkList, DailyWorkReviewInterface } from "@/components/daily-work";
import { DeliverablesTable, AddDeliverableForm } from "@/components/deliverables";
import { TaskDisciplineView } from "@/components/projects/task-discipline-view";
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

  // State for daily work review modal
  const [selectedDailyWork, setSelectedDailyWork] = useState<{
    daily_work_id: number;
    project_code: string;
    work_date: string;
    submitted_at: string;
    description: string;
    task_type: string | null;
    discipline: string | null;
    phase: string | null;
    hours_spent: number | null;
    staff_id: number | null;
    staff_name: string | null;
    attachments: Array<{ file_id: number; filename: string }>;
    reviewer_id: number | null;
    reviewer_name: string | null;
    review_status: "pending" | "reviewed" | "needs_revision" | "approved";
    review_comments: string | null;
    reviewed_at: string | null;
  } | null>(null);

  // State for deliverables form
  const [showDeliverableForm, setShowDeliverableForm] = useState(false);
  const [editingDeliverable, setEditingDeliverable] = useState<{
    deliverable_id: number;
    name?: string;
    deliverable_name?: string;
    description?: string;
    deliverable_type?: string;
    phase?: string;
    due_date?: string;
    start_date?: string;
    status?: string;
    priority?: string;
    assigned_pm?: string;
    owner_staff_id?: number;
  } | null>(null);

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
    <div className="p-4 sm:p-6 space-y-4 sm:space-y-6 max-w-[100vw] overflow-x-hidden">
      {/* Header Row */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <Link href="/projects">
          <Button variant="ghost" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Projects
          </Button>
        </Link>
        <div className="flex gap-2 flex-wrap">
          <Badge
            variant="outline"
            className={cn(
              "text-xs px-3 py-1",
              (projectDetail?.status as string) === "Active"
                ? "bg-teal-50 text-teal-700 border-teal-200"
                : "bg-slate-100 text-slate-600 border-slate-200"
            )}
          >
            {(projectDetail?.status as string) || "Active Project"}
          </Badge>
          <Badge
            variant="outline"
            className={cn(
              "text-xs px-3 py-1",
              outstandingAmount > 0
                ? "bg-amber-50 text-amber-700 border-amber-200"
                : "bg-emerald-50 text-emerald-700 border-emerald-200"
            )}
          >
            {outstandingAmount > 0 ? `${formatCurrency(outstandingAmount)} outstanding` : "Paid up"}
          </Badge>
        </div>
      </div>

      {/* Hero Card */}
      <Card className="border-2 border-slate-200">
        <CardContent className="p-4 sm:p-6">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
            {/* Left side - Project info */}
            <div className="space-y-4 flex-1 min-w-0">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 break-words">
                  {(projectDetail?.project_name as string) ?? (projectDetail?.client_name as string) ?? projectCode}
                </h1>
                <p className="text-lg text-slate-500 break-words mt-1">
                  {(projectDetail?.client_name as string) || "Client not specified"}
                </p>
              </div>

              {/* Badges row */}
              <div className="flex flex-wrap gap-2">
                <Badge className="text-sm px-3 py-1 font-mono bg-slate-100 text-slate-700">
                  {projectCode}
                </Badge>
                <Badge className="text-sm px-3 py-1 bg-teal-100 text-teal-700">
                  {(projectDetail?.current_phase as string) ?? "Unknown Phase"}
                </Badge>
                {(projectDetail?.country as string) && (
                  <Badge variant="outline" className="text-sm px-3 py-1 gap-1">
                    <Building2 className="h-3 w-3" />
                    {projectDetail?.country as string}
                  </Badge>
                )}
              </div>

              {/* Meta info */}
              <div className="flex flex-wrap gap-4 text-sm text-slate-500">
                {teamCount > 0 && (
                  <span className="flex items-center gap-1.5">
                    <Users className="h-4 w-4 text-blue-500" />
                    <span className="font-medium text-slate-700">{teamCount}</span> team members
                  </span>
                )}
                {(projectDetail?.contract_signed_date as string) && (
                  <span className="flex items-center gap-1.5">
                    <Calendar className="h-4 w-4 text-slate-400" />
                    Since {formatDisplayDate(projectDetail?.contract_signed_date as string)}
                  </span>
                )}
                {phases.length > 0 && (
                  <span className="flex items-center gap-1.5">
                    <BarChart3 className="h-4 w-4 text-teal-500" />
                    {phases.filter((p: { status: string }) => p.status === 'completed').length}/{phases.length} phases complete
                  </span>
                )}
              </div>
            </div>

            {/* Right side - Financial summary */}
            <div className="lg:text-right bg-slate-50 rounded-xl p-4 lg:min-w-[240px]">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Contract Value</p>
              <p className="text-3xl font-bold text-slate-900 tabular-nums">
                {formatCurrency(contractValue)}
              </p>

              {/* Progress bars */}
              <div className="mt-4 space-y-2">
                <div>
                  <div className="flex justify-between text-xs text-slate-500 mb-1">
                    <span>Invoiced</span>
                    <span className="font-medium text-slate-700">{Math.round(invoicingProgress)}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-blue-400 to-blue-600 transition-all"
                      style={{ width: `${Math.min(invoicingProgress, 100)}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs text-slate-500 mb-1">
                    <span>Collected</span>
                    <span className="font-medium text-emerald-600">{Math.round(paymentProgress)}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600 transition-all"
                      style={{ width: `${Math.min(paymentProgress, 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Quick stats */}
              <div className="mt-4 pt-4 border-t border-slate-200 grid grid-cols-2 gap-3 text-center">
                <div>
                  <p className="text-lg font-bold text-emerald-600">{formatCurrency(paidToDate)}</p>
                  <p className="text-xs text-slate-500">Paid</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-amber-600">{formatCurrency(Math.max(0, outstandingAmount))}</p>
                  <p className="text-xs text-slate-500">Outstanding</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

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
            <TabsList className="grid w-full grid-cols-6 lg:w-auto lg:inline-flex">
              <TabsTrigger value="overview" className="gap-2">
                <BarChart3 className="h-4 w-4" />
                <span className="hidden sm:inline">Overview</span>
              </TabsTrigger>
              <TabsTrigger value="phases" className="gap-2">
                <Calendar className="h-4 w-4" />
                <span className="hidden sm:inline">Phases</span>
              </TabsTrigger>
              <TabsTrigger value="daily-work" className="gap-2">
                <ClipboardList className="h-4 w-4" />
                <span className="hidden sm:inline">Daily Work</span>
              </TabsTrigger>
              <TabsTrigger value="deliverables" className="gap-2">
                <Package className="h-4 w-4" />
                <span className="hidden sm:inline">Deliverables</span>
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

              {/* Communication & Financial Preview */}
              <div className="grid gap-6 lg:grid-cols-3">
                <ProjectEmailsCard projectCode={projectCode} limit={5} />
                <ProjectMeetingsCard projectCode={projectCode} />
                <ProjectInvoicesCard
                  projectCode={projectCode}
                  limit={5}
                  onViewAll={() => {
                    // Switch to Finance tab
                    const financeTab = document.querySelector('[value="finance"]') as HTMLButtonElement;
                    financeTab?.click();
                  }}
                />
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
                      phases={phases.map(p => ({
                        phase_name: p.phase_name,
                        status: p.status,
                        phase_fee_usd: p.phase_fee_usd ?? undefined,
                        invoiced_amount_usd: p.invoiced_amount_usd ?? undefined,
                        paid_amount_usd: p.paid_amount_usd ?? undefined,
                        start_date: p.start_date ?? undefined,
                        expected_completion_date: p.expected_completion_date ?? undefined,
                        actual_completion_date: p.actual_completion_date ?? undefined,
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
                          {phases.map((phase) => (
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

            {/* DAILY WORK TAB */}
            <TabsContent value="daily-work" className="space-y-6 mt-6">
              {/* Submission Form */}
              <DailyWorkSubmissionForm projectCode={projectCode} />

              {/* Submissions List */}
              <DailyWorkList
                projectCode={projectCode}
                onSelectItem={(item) => setSelectedDailyWork(item)}
              />
            </TabsContent>

            {/* DELIVERABLES TAB */}
            <TabsContent value="deliverables" className="space-y-6 mt-6">
              <DeliverablesTable
                projectCode={projectCode}
                onAddNew={() => {
                  setEditingDeliverable(null);
                  setShowDeliverableForm(true);
                }}
                onEdit={(d) => {
                  setEditingDeliverable(d);
                  setShowDeliverableForm(true);
                }}
              />
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
              {/* Tasks by Discipline */}
              <TaskDisciplineView projectCode={projectCode} />

              {/* RFI/Deliverables Panel */}
              <RFIDeliverablesPanel
                rfis={(projectDetail?.rfis as Array<{rfi_id: number; rfi_number?: string; subject: string; status: "open" | "answered" | "closed"; submitted_date: string; response_date?: string | null; days_open?: number}>) ?? []}
                deliverables={(projectDetail?.deliverables as Array<{deliverable_id: number; name: string; status: "pending" | "in_progress" | "delivered" | "approved"; due_date: string | null; delivered_date?: string | null; responsible_party?: string}>) ?? []}
                projectCode={projectCode}
              />

              {/* Quick Kanban View */}
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

      {/* Daily Work Review Modal */}
      {selectedDailyWork && (
        <DailyWorkReviewInterface
          item={selectedDailyWork}
          onClose={() => setSelectedDailyWork(null)}
          reviewerName="Bill"
        />
      )}

      {/* Deliverables Add/Edit Form Modal */}
      {showDeliverableForm && (
        <AddDeliverableForm
          projectCode={projectCode}
          editingDeliverable={editingDeliverable}
          onClose={() => {
            setShowDeliverableForm(false);
            setEditingDeliverable(null);
          }}
        />
      )}
    </div>
  );
}
