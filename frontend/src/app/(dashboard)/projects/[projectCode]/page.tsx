"use client";

import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  Building2,
  CheckCircle2,
  Clock,
  DollarSign,
  Mail,
  TrendingUp,
  AlertTriangle,
  Calendar,
  CreditCard,
} from "lucide-react";
import Link from "next/link";
import { use } from "react";
import { UnifiedTimeline } from "@/components/project/unified-timeline";
import { ProjectFeesCard } from "@/components/project/project-fees-card";
import { ProjectTasksCard } from "@/components/project/project-tasks-card";
import { TeamCard } from "@/components/project/team-card";
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

  const invoicesQuery = useQuery({
    queryKey: ["project", projectCode, "invoices"],
    queryFn: () => api.getInvoicesByProject(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const projectDetail = projectDetailQuery.data;
  const invoices = invoicesQuery.data?.invoices ?? [];

  const isLoading = projectDetailQuery.isLoading || invoicesQuery.isLoading;

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
              <p className="text-sm text-slate-500">Contract Value</p>
              <p className="text-3xl font-bold text-slate-900">
                {formatCurrency(contractValue)}
              </p>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-6">
            {/* Skeleton for main cards */}
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
            {/* Main Dashboard Cards - 3 column layout */}
            <section className="mb-8">
              <div className="grid gap-6 lg:grid-cols-3">
                {/* Fees & Scope Card */}
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
                    {/* Payment Summary */}
                    <div className="space-y-4">
                      {/* Paid to Date */}
                      <div>
                        <div className="flex items-baseline justify-between">
                          <span className={ds.typography.metricLarge}>{formatCurrency(paidToDate)}</span>
                          <span className="text-sm text-emerald-600 font-medium">
                            {Math.round(paymentProgress)}% collected
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">of {formatCurrency(totalInvoiced)} invoiced</p>
                      </div>

                      {/* Progress bar */}
                      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-600 transition-all"
                          style={{ width: `${Math.min(paymentProgress, 100)}%` }}
                        />
                      </div>

                      {/* Stats */}
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

                {/* Pending Tasks Card */}
                <ProjectTasksCard projectCode={projectCode} maxItems={4} />
              </div>
            </section>

            {/* Project Team */}
            <section className="mb-8">
              <TeamCard projectCode={projectCode} />
            </section>

            {/* Project Activity Timeline */}
            <section className="mb-8">
              <UnifiedTimeline projectCode={projectCode} limit={50} />
            </section>

            {/* Communication Quick Links */}
            <section className="mb-8">
              <Card className={ds.cards.default}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Mail className="h-5 w-5 text-blue-600" />
                      <h3 className="font-semibold text-slate-900">Communication</h3>
                    </div>
                    <Link href={`/projects/${projectCode}/emails`}>
                      <Button variant="outline" size="sm" className={ds.buttons.secondary}>
                        View All Emails
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
