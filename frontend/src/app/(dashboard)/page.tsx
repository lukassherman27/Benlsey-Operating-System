"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CalendarWidget } from "@/components/dashboard/calendar-widget";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { useRBAC } from "@/hooks/useRBAC";
import {
  Clock,
  RefreshCw,
  DollarSign,
  AlertTriangle,
  TrendingUp,
  FileText,
  ChevronRight,
  Building2,
  Users,
  ArrowUpRight,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { api } from "@/lib/api";
import Link from "next/link";

const formatCurrency = (value: number) => {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${value.toLocaleString()}`;
};

export default function DashboardPage() {
  const [lastUpdated] = useState(new Date());
  const { data: session } = useSession();
  const { canViewFinancials, isPM, userRole } = useRBAC();

  // Get user's first name for greeting
  const userName = session?.user?.name?.split(" ")[0] || "there";

  // Fetch proposals that need attention
  const proposalsQuery = useQuery({
    queryKey: ["dashboard-proposals-attention"],
    queryFn: async () => {
      const res = await api.getProposals({ per_page: 50 });
      const proposals = res.data || [];

      // Filter to active proposals that need attention
      const active = proposals.filter((p) =>
        !['Lost', 'Declined', 'Contract Signed', 'Dormant'].includes(p.status as string)
      );

      // Find stale proposals (>14 days in current status)
      const now = new Date();
      const stale = active.filter((p) => {
        const lastContact = (p as { last_contact_date?: string }).last_contact_date
          ? new Date((p as { last_contact_date: string }).last_contact_date)
          : null;
        if (!lastContact) return true;
        const daysSince = Math.floor((now.getTime() - lastContact.getTime()) / (1000 * 60 * 60 * 24));
        return daysSince > 14;
      });

      // Group by status
      const byStatus: Record<string, typeof proposals> = {};
      active.forEach((p) => {
        const status = p.status as string;
        if (!byStatus[status]) byStatus[status] = [];
        byStatus[status].push(p);
      });

      return {
        active,
        stale,
        byStatus,
        totalValue: active.reduce((sum, p) =>
          sum + ((p as { project_value?: number }).project_value || 0), 0
        ),
      };
    },
    staleTime: 1000 * 60 * 5,
  });

  // Fetch overdue invoices
  const invoicesQuery = useQuery({
    queryKey: ["dashboard-overdue-invoices"],
    queryFn: async () => {
      const res = await api.getInvoiceAging();
      const invoices = res.data?.largest_outstanding || [];

      // Group by project
      const byProject: Record<string, {
        projectName: string;
        projectCode: string;
        totalOverdue: number;
        invoices: typeof invoices;
        oldestDays: number;
      }> = {};

      invoices.forEach((inv) => {
        const code = inv.project_code || 'Unknown';
        const name = inv.project_title || code;
        if (!byProject[code]) {
          byProject[code] = {
            projectName: name,
            projectCode: code,
            totalOverdue: 0,
            invoices: [],
            oldestDays: 0
          };
        }
        byProject[code].invoices.push(inv);
        byProject[code].totalOverdue += inv.invoice_amount || 0;
        const days = inv.days_overdue || 0;
        if (days > byProject[code].oldestDays) {
          byProject[code].oldestDays = days;
        }
      });

      // Sort by total overdue
      const sorted = Object.values(byProject).sort((a, b) => b.totalOverdue - a.totalOverdue);

      return {
        totalOverdue: invoices.reduce((sum, i) =>
          sum + (i.invoice_amount || 0), 0
        ),
        invoiceCount: invoices.length,
        byProject: sorted,
      };
    },
    staleTime: 1000 * 60 * 5,
  });

  // Fetch projects with issues
  const projectsQuery = useQuery({
    queryKey: ["dashboard-projects-issues"],
    queryFn: async () => {
      const res = await api.getActiveProjects();
      const projects = res.data || [];

      // Find projects with potential issues
      const withIssues = projects.filter((p: Record<string, unknown>) => {
        const overdue = (p.overdue_invoices_count as number) || 0;
        const daysSince = (p.days_since_activity as number) || 0;
        return overdue > 0 || daysSince > 30;
      }).map((p: Record<string, unknown>) => ({
        ...p,
        issues: [
          ...(p.overdue_invoices_count as number) > 0 ? [`${p.overdue_invoices_count} overdue invoices`] : [],
          ...(p.days_since_activity as number) > 30 ? [`${p.days_since_activity} days inactive`] : [],
        ]
      }));

      return {
        total: projects.length,
        withIssues,
      };
    },
    staleTime: 1000 * 60 * 5,
  });

  const proposals = proposalsQuery.data;
  const invoices = invoicesQuery.data;
  const projects = projectsQuery.data;

  return (
    <div className={cn("w-full max-w-full", ds.spacing.spacious, "space-y-6")}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            Good {new Date().getHours() < 12 ? 'Morning' : new Date().getHours() < 18 ? 'Afternoon' : 'Evening'}, {userName}
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            {format(new Date(), "EEEE, MMMM d, yyyy")}
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Clock className="h-4 w-4" />
          <span>Updated {format(lastUpdated, "h:mm a")}</span>
          <button
            onClick={() => window.location.reload()}
            className="p-1 hover:bg-slate-100 rounded"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Key Numbers - Compact Strip */}
      <div className={cn("grid gap-4", canViewFinancials ? "grid-cols-2 md:grid-cols-4" : "grid-cols-2")}>
        {/* Pipeline Value - Only visible to Finance/Executive */}
        {canViewFinancials && (
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-blue-600 text-sm font-medium">
                <TrendingUp className="h-4 w-4" />
                Pipeline
              </div>
              <p className="text-2xl font-bold text-blue-900 mt-1">
                {formatCurrency(proposals?.totalValue || 0)}
              </p>
              <p className="text-xs text-blue-600 mt-0.5">
                {proposals?.active?.length || 0} active proposals
              </p>
            </CardContent>
          </Card>
        )}

        <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-amber-600 text-sm font-medium">
              <AlertTriangle className="h-4 w-4" />
              Stale
            </div>
            <p className="text-2xl font-bold text-amber-900 mt-1">
              {proposals?.stale?.length || 0}
            </p>
            <p className="text-xs text-amber-600 mt-0.5">
              Need follow-up (&gt;14 days)
            </p>
          </CardContent>
        </Card>

        {/* Overdue Invoices - Only visible to Finance/Executive */}
        {canViewFinancials && (
          <Card className={cn(
            "bg-gradient-to-br border",
            (invoices?.totalOverdue || 0) > 0
              ? "from-red-50 to-red-100 border-red-200"
              : "from-emerald-50 to-emerald-100 border-emerald-200"
          )}>
            <CardContent className="p-4">
              <div className={cn(
                "flex items-center gap-2 text-sm font-medium",
                (invoices?.totalOverdue || 0) > 0 ? "text-red-600" : "text-emerald-600"
              )}>
                <DollarSign className="h-4 w-4" />
                Overdue
              </div>
              <p className={cn(
                "text-2xl font-bold mt-1",
                (invoices?.totalOverdue || 0) > 0 ? "text-red-900" : "text-emerald-900"
              )}>
                {formatCurrency(invoices?.totalOverdue || 0)}
              </p>
              <p className={cn(
                "text-xs mt-0.5",
                (invoices?.totalOverdue || 0) > 0 ? "text-red-600" : "text-emerald-600"
              )}>
                {invoices?.invoiceCount || 0} invoices past due
              </p>
            </CardContent>
          </Card>
        )}

        <Card className="bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-slate-600 text-sm font-medium">
              <Building2 className="h-4 w-4" />
              Projects
            </div>
            <p className="text-2xl font-bold text-slate-900 mt-1">
              {projects?.total || 0}
            </p>
            <p className="text-xs text-slate-600 mt-0.5">
              {projects?.withIssues?.length || 0} need attention
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content - Two Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* LEFT COLUMN: Proposals & Money */}
        <div className="space-y-6">

          {/* Proposals Needing Action */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="h-4 w-4 text-blue-600" />
                  Proposals Needing Action
                </CardTitle>
                <Link href="/proposals">
                  <Button variant="ghost" size="sm" className="text-xs">
                    View All <ChevronRight className="h-3 w-3 ml-1" />
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              {proposalsQuery.isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map(i => <div key={i} className="h-16 bg-slate-100 animate-pulse rounded" />)}
                </div>
              ) : proposals?.stale && proposals.stale.length > 0 ? (
                <div className="space-y-2">
                  {proposals.stale.slice(0, 5).map((p) => (
                    <Link
                      key={p.proposal_id}
                      href={`/proposals/${p.proposal_id}`}
                      className="block p-3 rounded-lg border hover:bg-slate-50 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <p className="font-medium text-slate-900 truncate">
                            {p.project_name || (p as { client_company?: string }).client_company || 'Unnamed'}
                          </p>
                          <p className="text-xs text-slate-500 mt-0.5">
                            {(p as { client_company?: string }).client_company} • {(p as { country?: string }).country || 'Unknown location'}
                          </p>
                        </div>
                        <div className="text-right flex-shrink-0">
                          <Badge variant="outline" className="text-xs">
                            {p.status as string}
                          </Badge>
                          <p className="text-xs text-amber-600 mt-1">
                            {p.last_contact_date
                              ? formatDistanceToNow(new Date(p.last_contact_date as string), { addSuffix: true })
                              : 'No contact'
                            }
                          </p>
                        </div>
                      </div>
                    </Link>
                  ))}
                  {proposals.stale.length > 5 && (
                    <p className="text-xs text-slate-500 text-center pt-2">
                      +{proposals.stale.length - 5} more needing follow-up
                    </p>
                  )}
                </div>
              ) : (
                <div className="text-center py-6 text-slate-500">
                  <FileText className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                  <p className="text-sm">All proposals are up to date!</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Overdue by Project */}
          <Card className={invoices?.totalOverdue ? "border-red-200 bg-red-50/30" : ""}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <DollarSign className={cn("h-4 w-4", invoices?.totalOverdue ? "text-red-600" : "text-emerald-600")} />
                  Money Owed to Us
                </CardTitle>
                <Link href="/finance">
                  <Button variant="ghost" size="sm" className="text-xs">
                    View All <ChevronRight className="h-3 w-3 ml-1" />
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              {invoicesQuery.isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map(i => <div key={i} className="h-14 bg-slate-100 animate-pulse rounded" />)}
                </div>
              ) : invoices?.byProject && invoices.byProject.length > 0 ? (
                <div className="space-y-2">
                  {invoices.byProject.slice(0, 5).map((proj) => (
                    <div
                      key={proj.projectCode}
                      className="p-3 rounded-lg bg-white border border-red-100 flex items-center justify-between"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-slate-900 truncate">
                          {proj.projectName}
                        </p>
                        <p className="text-xs text-red-600 mt-0.5">
                          {proj.invoices.length} invoice{proj.invoices.length > 1 ? 's' : ''} •
                          oldest {proj.oldestDays} days overdue
                        </p>
                      </div>
                      <p className="text-lg font-bold text-red-700 flex-shrink-0">
                        {formatCurrency(proj.totalOverdue)}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-emerald-600">
                  <DollarSign className="h-8 w-8 mx-auto mb-2 text-emerald-300" />
                  <p className="text-sm font-medium">No overdue invoices!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* RIGHT COLUMN: Calendar & Projects */}
        <div className="space-y-6">

          {/* Calendar */}
          <CalendarWidget />

          {/* Projects Needing Attention */}
          {projects?.withIssues && projects.withIssues.length > 0 && (
            <Card className="border-amber-200 bg-amber-50/30">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-amber-600" />
                    Projects Needing Attention
                  </CardTitle>
                  <Link href="/projects">
                    <Button variant="ghost" size="sm" className="text-xs">
                      View All <ChevronRight className="h-3 w-3 ml-1" />
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-2">
                  {projects.withIssues.slice(0, 4).map((proj: Record<string, unknown>) => (
                    <Link
                      key={proj.project_code as string}
                      href={`/projects/${encodeURIComponent(proj.project_code as string)}`}
                      className="block p-3 rounded-lg bg-white border border-amber-100 hover:bg-amber-50 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <p className="font-medium text-slate-900 truncate">
                            {(proj.project_name as string) || (proj.project_title as string) || proj.project_code as string}
                          </p>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {(proj.issues as string[])?.map((issue, i) => (
                              <Badge key={i} variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                                {issue}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <ArrowUpRight className="h-4 w-4 text-slate-400 flex-shrink-0" />
                      </div>
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Quick Links */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Quick Access</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="grid grid-cols-2 gap-2">
                <Link href="/proposals" className="p-3 rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors text-center">
                  <FileText className="h-5 w-5 mx-auto text-blue-600 mb-1" />
                  <p className="text-sm font-medium text-blue-900">Proposals</p>
                </Link>
                <Link href="/projects" className="p-3 rounded-lg bg-purple-50 hover:bg-purple-100 transition-colors text-center">
                  <Building2 className="h-5 w-5 mx-auto text-purple-600 mb-1" />
                  <p className="text-sm font-medium text-purple-900">Projects</p>
                </Link>
                <Link href="/contacts" className="p-3 rounded-lg bg-emerald-50 hover:bg-emerald-100 transition-colors text-center">
                  <Users className="h-5 w-5 mx-auto text-emerald-600 mb-1" />
                  <p className="text-sm font-medium text-emerald-900">Contacts</p>
                </Link>
                <Link href="/finance" className="p-3 rounded-lg bg-amber-50 hover:bg-amber-100 transition-colors text-center">
                  <DollarSign className="h-5 w-5 mx-auto text-amber-600 mb-1" />
                  <p className="text-sm font-medium text-amber-900">Finance</p>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
