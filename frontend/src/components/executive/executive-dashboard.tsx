"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn, formatCurrency } from "@/lib/utils";
import { NeedsAttentionWidget } from "./needs-attention-widget";
import Link from "next/link";
import { format } from "date-fns";
import {
  TrendingUp,
  Building2,
  DollarSign,
  ChevronRight,
  RefreshCw,
  Clock,
  FileText,
  Users,
} from "lucide-react";

// Status color mapping for pipeline breakdown
const STATUS_COLORS: Record<string, string> = {
  "First Contact": "bg-sky-100 text-sky-800 border-sky-200",
  "Proposal Prep": "bg-purple-100 text-purple-800 border-purple-200",
  "Proposal Sent": "bg-blue-100 text-blue-800 border-blue-200",
  Negotiation: "bg-amber-100 text-amber-800 border-amber-200",
  "Contract Signed": "bg-emerald-100 text-emerald-800 border-emerald-200",
  "On Hold": "bg-slate-100 text-slate-800 border-slate-200",
};

interface ExecutiveStats {
  role: string;
  pipeline_value: number;
  active_projects_count: number;
  outstanding_invoices_total: number;
  overdue_invoices_count: number;
}

interface ProposalStats {
  active_pipeline: number;
  total_proposals: number;
  by_status: Record<string, number>;
  need_followup: number;
}

export function ExecutiveDashboard() {
  const [lastUpdatedLabel, setLastUpdatedLabel] = useState("");
  const [todayLabel, setTodayLabel] = useState("");

  useEffect(() => {
    const now = new Date();
    setLastUpdatedLabel(format(now, "h:mm a"));
    setTodayLabel(format(now, "EEEE, MMMM d, yyyy"));
  }, []);

  const emptyExecutiveStats: ExecutiveStats = {
    role: "executive",
    pipeline_value: 0,
    active_projects_count: 0,
    outstanding_invoices_total: 0,
    overdue_invoices_count: 0,
  };

  const emptyProposalStats: ProposalStats = {
    active_pipeline: 0,
    total_proposals: 0,
    by_status: {},
    need_followup: 0,
  };

  // Fetch executive-specific stats
  const statsQuery = useQuery({
    queryKey: ["executive-stats"],
    queryFn: async () => {
      const res = await api.getDashboardStats("executive");
      return (res as unknown as ExecutiveStats) || emptyExecutiveStats;
    },
    staleTime: 1000 * 60 * 5,
  });

  // Fetch proposal stats for pipeline breakdown
  const proposalStatsQuery = useQuery({
    queryKey: ["executive-proposal-stats"],
    queryFn: async () => {
      const res = await api.getProposalStats();
      return (res as unknown as ProposalStats) || emptyProposalStats;
    },
    staleTime: 1000 * 60 * 5,
  });

  const stats = statsQuery.data;
  const proposalStats = proposalStatsQuery.data;
  const isLoading = statsQuery.isLoading || proposalStatsQuery.isLoading;

  return (
    <div className="w-full max-w-full p-4 md:p-6 space-y-6">
      {/* Header - Compact for iPad */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Executive Dashboard</h1>
          <p className="text-sm text-slate-500">{todayLabel || "—"}</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Clock className="h-4 w-4" />
          <span>Updated {lastUpdatedLabel || "—"}</span>
          <button
            onClick={() => window.location.reload()}
            className="p-1 hover:bg-slate-100 rounded"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* KPI Cards - 3 Main Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Pipeline Value */}
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="p-4 md:p-6">
            <div className="flex items-center gap-2 text-blue-600 text-sm font-medium mb-2">
              <TrendingUp className="h-5 w-5" />
              Pipeline Value
            </div>
            {isLoading ? (
              <Skeleton className="h-9 w-32" />
            ) : (
              <>
                <p className="text-3xl font-bold text-blue-900">
                  {formatCurrency(stats?.pipeline_value || 0)}
                </p>
                <p className="text-sm text-blue-600 mt-1">
                  {proposalStats?.active_pipeline || 0} active proposals
                </p>
              </>
            )}
          </CardContent>
        </Card>

        {/* Active Projects */}
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardContent className="p-4 md:p-6">
            <div className="flex items-center gap-2 text-purple-600 text-sm font-medium mb-2">
              <Building2 className="h-5 w-5" />
              Active Projects
            </div>
            {isLoading ? (
              <Skeleton className="h-9 w-20" />
            ) : (
              <>
                <p className="text-3xl font-bold text-purple-900">
                  {stats?.active_projects_count || 0}
                </p>
                <Link href="/projects">
                  <p className="text-sm text-purple-600 mt-1 hover:underline cursor-pointer">
                    View all projects
                  </p>
                </Link>
              </>
            )}
          </CardContent>
        </Card>

        {/* Outstanding Invoices */}
        <Card
          className={cn(
            "bg-gradient-to-br border",
            (stats?.outstanding_invoices_total || 0) > 0
              ? "from-red-50 to-red-100 border-red-200"
              : "from-emerald-50 to-emerald-100 border-emerald-200"
          )}
        >
          <CardContent className="p-4 md:p-6">
            <div
              className={cn(
                "flex items-center gap-2 text-sm font-medium mb-2",
                (stats?.outstanding_invoices_total || 0) > 0 ? "text-red-600" : "text-emerald-600"
              )}
            >
              <DollarSign className="h-5 w-5" />
              Outstanding Invoices
            </div>
            {isLoading ? (
              <Skeleton className="h-9 w-28" />
            ) : (
              <>
                <p
                  className={cn(
                    "text-3xl font-bold",
                    (stats?.outstanding_invoices_total || 0) > 0
                      ? "text-red-900"
                      : "text-emerald-900"
                  )}
                >
                  {formatCurrency(stats?.outstanding_invoices_total || 0)}
                </p>
                <p
                  className={cn(
                    "text-sm mt-1",
                    (stats?.outstanding_invoices_total || 0) > 0
                      ? "text-red-600"
                      : "text-emerald-600"
                  )}
                >
                  {stats?.overdue_invoices_count || 0} overdue
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Main Content - Two Columns on Desktop, Stacked on iPad */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* LEFT: Needs Attention (takes 3/5 on desktop) */}
        <div className="lg:col-span-3">
          <NeedsAttentionWidget maxItems={8} />
        </div>

        {/* RIGHT: Pipeline + Quick Links (takes 2/5 on desktop) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Pipeline Breakdown */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="h-4 w-4 text-blue-600" />
                  Pipeline by Status
                </CardTitle>
                <Link href="/proposals">
                  <Button variant="ghost" size="sm" className="text-xs">
                    View All <ChevronRight className="h-3 w-3 ml-1" />
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              {proposalStatsQuery.isLoading ? (
                <div className="flex flex-wrap gap-2">
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-8 w-24 rounded-full" />
                  ))}
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {proposalStats?.by_status &&
                    Object.entries(proposalStats.by_status)
                      .filter(([status]) => !["Dormant", "Lost", "Declined"].includes(status))
                      .sort((a, b) => b[1] - a[1])
                      .map(([status, count]) => (
                        <Link
                          key={status}
                          href={`/proposals?status=${encodeURIComponent(status)}`}
                          className={cn(
                            "px-3 py-1.5 rounded-full text-sm font-medium border hover:opacity-80 transition-opacity",
                            STATUS_COLORS[status] || "bg-slate-100 text-slate-800 border-slate-200"
                          )}
                        >
                          {status}: {count}
                        </Link>
                      ))}
                </div>
              )}

              {/* Follow-up count highlight */}
              {proposalStats?.need_followup && proposalStats.need_followup > 0 && (
                <div className="mt-4 p-3 rounded-lg bg-amber-50 border border-amber-200">
                  <p className="text-sm text-amber-800">
                    <span className="font-semibold">{proposalStats.need_followup}</span> proposals
                    need follow-up (&gt;14 days)
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Access Links */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Quick Access</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="grid grid-cols-2 gap-2">
                <Link
                  href="/proposals"
                  className="p-3 rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors text-center"
                >
                  <FileText className="h-5 w-5 mx-auto text-blue-600 mb-1" />
                  <p className="text-sm font-medium text-blue-900">Proposals</p>
                </Link>
                <Link
                  href="/projects"
                  className="p-3 rounded-lg bg-purple-50 hover:bg-purple-100 transition-colors text-center"
                >
                  <Building2 className="h-5 w-5 mx-auto text-purple-600 mb-1" />
                  <p className="text-sm font-medium text-purple-900">Projects</p>
                </Link>
                <Link
                  href="/contacts"
                  className="p-3 rounded-lg bg-emerald-50 hover:bg-emerald-100 transition-colors text-center"
                >
                  <Users className="h-5 w-5 mx-auto text-emerald-600 mb-1" />
                  <p className="text-sm font-medium text-emerald-900">Contacts</p>
                </Link>
                <Link
                  href="/finance"
                  className="p-3 rounded-lg bg-amber-50 hover:bg-amber-100 transition-colors text-center"
                >
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
