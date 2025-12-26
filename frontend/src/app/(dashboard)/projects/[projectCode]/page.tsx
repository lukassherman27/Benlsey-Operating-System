"use client";

import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { api } from "@/lib/api";
import { Card, Text, Tab, TabGroup, TabList, TabPanel, TabPanels, Badge as TremorBadge, Grid, Metric, ProgressBar } from "@tremor/react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  Building2,
  AlertTriangle,
  Calendar,
  Users,
  FileCheck,
  DollarSign,
  Clock,
  Layers,
} from "lucide-react";
import Link from "next/link";
import { use } from "react";
import { UnifiedTimeline } from "@/components/project/unified-timeline";
import { ProjectFeesCard } from "@/components/project/project-fees-card";
import { ProjectTasksCard } from "@/components/project/project-tasks-card";
import { BensleyTeamCard } from "@/components/project/bensley-team-card";
import { ProjectContactsCard } from "@/components/project/project-contacts-card";
import { ProjectMeetingsCard } from "@/components/project/project-meetings-card";
import { ProjectEmailsCard } from "@/components/project/project-emails-card";
import { ProjectHealthBanner, calculateProjectHealth } from "@/components/project/project-health-banner";
import { RFIDeliverablesPanel } from "@/components/project/rfi-deliverables-panel";
import { WorkVsInvoiceWidget } from "@/components/project/work-vs-invoice-widget";
import { ProjectInsights } from "@/components/project/project-insights";
import { PhaseProgressBar } from "@/components/project/phase-progress-bar";
import { ProjectKPICards } from "@/components/project/project-kpi-cards";
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
  // Decode in case URL params are still encoded
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
    queryKey: ["project-schedule-team", projectCode],
    queryFn: async () => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/projects/${projectCode}/schedule-team`);
      if (!res.ok) return { team: [], schedule: [] };
      return res.json();
    },
    staleTime: 1000 * 60 * 5,
  });

  const projectDetail = projectDetailQuery.data;
  const invoices = invoicesQuery.data?.invoices ?? [];
  const phases = phasesQuery.data?.phases ?? [];
  const team = teamQuery.data?.team ?? [];

  const isLoading = projectDetailQuery.isLoading;

  if (projectDetailQuery.error) {
    const errorMsg = projectDetailQuery.error instanceof Error
      ? projectDetailQuery.error.message
      : String(projectDetailQuery.error);
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Card className="border-red-200 bg-red-50 p-8 text-center max-w-md">
          <AlertTriangle className="mx-auto h-12 w-12 text-red-600" />
          <Text className="text-lg font-semibold text-slate-900 mt-4">Project Not Found</Text>
          <Text className="text-sm text-slate-600 mt-2">Could not load project {projectCode}</Text>
          <Text className="text-xs text-red-600 mt-2 font-mono">Error: {errorMsg}</Text>
          <Link href="/projects">
            <Button className={cn(ds.buttons.secondary, "mt-6")}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Projects
            </Button>
          </Link>
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
            <div className="grid gap-4 grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <Card key={i} className="animate-pulse p-4">
                  <div className="h-4 w-20 bg-slate-200 rounded mb-2" />
                  <div className="h-8 w-16 bg-slate-200 rounded" />
                </Card>
              ))}
            </div>
          </div>
        ) : (
          <>
            {/* Health Banner */}
            {(() => {
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
                <ProjectHealthBanner
                  status={health.status}
                  issues={health.issues}
                  projectName={(projectDetail?.project_name as string) ?? projectCode}
                  className="mb-6"
                />
              );
            })()}

            {/* Tabbed Content */}
            <TabGroup>
              <TabList className="mb-6">
                <Tab icon={Layers}>Overview</Tab>
                <Tab icon={Clock}>Phases</Tab>
                <Tab icon={Users}>Team</Tab>
                <Tab icon={FileCheck}>Submissions</Tab>
                <Tab icon={DollarSign}>Finance</Tab>
              </TabList>

              <TabPanels>
                {/* OVERVIEW TAB */}
                <TabPanel>
                  {/* KPI Cards */}
                  <div className="mb-6">
                    <ProjectKPICards projectCode={projectCode} />
                  </div>

                  {/* Insights */}
                  <div className="mb-6">
                    <ProjectInsights
                      projectCode={projectCode}
                      projectDetail={projectDetail as Record<string, unknown>}
                      invoices={invoices}
                    />
                  </div>

                  {/* Quick Stats Grid */}
                  <Grid numItemsSm={2} numItemsLg={4} className="gap-4 mb-6">
                    <Card decoration="left" decorationColor="teal">
                      <Text>Team Size</Text>
                      <Metric>{team.length}</Metric>
                    </Card>
                    <Card decoration="left" decorationColor="blue">
                      <Text>Phases Complete</Text>
                      <Metric>
                        {phases.filter((p: { status: string }) => p.status === 'completed').length} / {phases.length}
                      </Metric>
                    </Card>
                    <Card decoration="left" decorationColor="amber">
                      <Text>Open RFIs</Text>
                      <Metric>{(projectDetail?.open_rfis_count as number) ?? 0}</Metric>
                    </Card>
                    <Card decoration="left" decorationColor="emerald">
                      <Text>Collection Rate</Text>
                      <Metric>{Math.round(paymentProgress)}%</Metric>
                    </Card>
                  </Grid>

                  {/* Tasks & Communication */}
                  <div className="grid gap-6 lg:grid-cols-2">
                    <ProjectTasksCard projectCode={projectCode} maxItems={5} />
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <Text className="font-semibold">Recent Emails</Text>
                        <Link href={`/projects/${encodeURIComponent(projectCode)}/emails`}>
                          <Button variant="ghost" size="sm" className="text-xs">
                            View All
                          </Button>
                        </Link>
                      </div>
                      <ProjectEmailsCard projectCode={projectCode} limit={5} />
                    </div>
                  </div>
                </TabPanel>

                {/* PHASES TAB */}
                <TabPanel>
                  {/* Phase Progress Bar */}
                  <Card className="mb-6 p-6">
                    <Text className="font-semibold text-slate-900 mb-4">Design Phase Progress</Text>
                    <PhaseProgressBar phases={phases} />
                  </Card>

                  {/* Phase Details */}
                  <div className="grid gap-4 mb-6">
                    {phases.map((phase: { phase_name: string; status: string; phase_fee_usd?: number; invoiced_amount_usd?: number; paid_amount_usd?: number }) => (
                      <Card key={phase.phase_name} className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className={cn(
                              "w-3 h-3 rounded-full",
                              phase.status === 'completed' ? "bg-emerald-500" :
                              phase.status === 'in_progress' ? "bg-teal-500" :
                              "bg-slate-300"
                            )} />
                            <Text className="font-medium">{phase.phase_name}</Text>
                          </div>
                          <div className="flex items-center gap-4">
                            <TremorBadge color={
                              phase.status === 'completed' ? "emerald" :
                              phase.status === 'in_progress' ? "teal" :
                              "gray"
                            }>
                              {phase.status === 'completed' ? "Complete" :
                               phase.status === 'in_progress' ? "In Progress" :
                               "Pending"}
                            </TremorBadge>
                            {phase.phase_fee_usd && (
                              <Text className="text-sm text-slate-500">
                                {formatCurrency(phase.phase_fee_usd)}
                              </Text>
                            )}
                          </div>
                        </div>
                        {phase.status !== 'pending' && phase.phase_fee_usd && (
                          <div className="mt-3">
                            <ProgressBar
                              value={phase.invoiced_amount_usd ? (phase.invoiced_amount_usd / phase.phase_fee_usd) * 100 : 0}
                              color="teal"
                              className="h-2"
                            />
                            <Text className="text-xs text-slate-500 mt-1">
                              {formatCurrency(phase.invoiced_amount_usd || 0)} invoiced of {formatCurrency(phase.phase_fee_usd)}
                            </Text>
                          </div>
                        )}
                      </Card>
                    ))}
                  </div>

                  {/* Timeline */}
                  <Card className="p-6">
                    <Text className="font-semibold text-slate-900 mb-4">Activity Timeline</Text>
                    <UnifiedTimeline projectCode={projectCode} limit={30} />
                  </Card>
                </TabPanel>

                {/* TEAM TAB */}
                <TabPanel>
                  <div className="grid gap-6 lg:grid-cols-2">
                    <BensleyTeamCard projectCode={projectCode} />
                    <ProjectContactsCard projectCode={projectCode} />
                  </div>
                  <div className="mt-6">
                    <ProjectMeetingsCard projectCode={projectCode} />
                  </div>
                </TabPanel>

                {/* SUBMISSIONS TAB */}
                <TabPanel>
                  <RFIDeliverablesPanel
                    rfis={(projectDetail?.rfis as Array<{rfi_id: number; rfi_number?: string; subject: string; status: "open" | "answered" | "closed"; submitted_date: string; response_date?: string | null; days_open?: number}>) ?? []}
                    deliverables={(projectDetail?.deliverables as Array<{deliverable_id: number; name: string; status: "pending" | "in_progress" | "delivered" | "approved"; due_date: string | null; delivered_date?: string | null; responsible_party?: string}>) ?? []}
                    projectCode={projectCode}
                  />
                </TabPanel>

                {/* FINANCE TAB */}
                <TabPanel>
                  <div className="grid gap-6 lg:grid-cols-2 mb-6">
                    <ProjectFeesCard
                      projectCode={projectCode}
                      contractValue={contractValue}
                    />
                    <Card className="p-6">
                      <div className="flex items-center gap-2 mb-4">
                        <DollarSign className="h-5 w-5 text-emerald-600" />
                        <Text className="font-semibold text-slate-900">Payments</Text>
                      </div>
                      <Metric className="mb-2">{formatCurrency(paidToDate)}</Metric>
                      <Text className="text-sm text-slate-500 mb-4">
                        of {formatCurrency(totalInvoiced)} invoiced ({Math.round(paymentProgress)}%)
                      </Text>
                      <ProgressBar value={paymentProgress} color="emerald" className="mb-4" />
                      <Grid numItemsSm={2} className="gap-4">
                        <div className="p-3 rounded-lg bg-slate-50">
                          <Text className="text-xs text-slate-500">Outstanding</Text>
                          <Text className="text-lg font-semibold text-slate-900">
                            {formatCurrency(Math.max(0, outstandingAmount))}
                          </Text>
                        </div>
                        <div className="p-3 rounded-lg bg-slate-50">
                          <Text className="text-xs text-slate-500">Unpaid Invoices</Text>
                          <Text className="text-lg font-semibold text-slate-900">
                            {unpaidInvoices}
                          </Text>
                        </div>
                      </Grid>
                    </Card>
                  </div>
                  <WorkVsInvoiceWidget projectCode={projectCode} />
                </TabPanel>
              </TabPanels>
            </TabGroup>
          </>
        )}
      </div>
    </div>
  );
}
