"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ProposalTrackerItem, DisciplineFilter } from "@/lib/types";
import { ProposalQuickEditDialog } from "@/components/proposal-quick-edit-dialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Search,
  Filter,
  FileText,
  Loader2,
  Download,
  Pencil,
  TrendingUp,
  TrendingDown,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  DollarSign,
  Calendar
} from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { formatCurrency, getStatusColor, cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { type ProposalStatus } from "@/lib/constants";
import { Skeleton } from "@/components/ui/skeleton";
import { exportToCSV, prepareDataForExport } from "@/lib/export-utils";

// Status colors for the pipeline visualization
const STATUS_COLORS = {
  "First Contact": { bg: "bg-slate-100", fill: "bg-slate-400", text: "text-slate-700" },
  "Drafting": { bg: "bg-blue-100", fill: "bg-blue-500", text: "text-blue-700" },
  "Proposal Sent": { bg: "bg-amber-100", fill: "bg-amber-500", text: "text-amber-700" },
  "On Hold": { bg: "bg-orange-100", fill: "bg-orange-500", text: "text-orange-700" },
  "Contract Signed": { bg: "bg-emerald-100", fill: "bg-emerald-500", text: "text-emerald-700" },
  "Archived": { bg: "bg-red-100", fill: "bg-red-400", text: "text-red-700" },
};

// Activity color based on days since last activity
function getActivityColor(days: number): { bg: string; text: string; label: string } {
  if (days <= 7) return { bg: "bg-emerald-100", text: "text-emerald-700", label: "Active" };
  if (days <= 14) return { bg: "bg-amber-100", text: "text-amber-700", label: "Needs attention" };
  return { bg: "bg-red-100", text: "text-red-700", label: "Stalled" };
}

export default function ProposalTrackerPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ProposalStatus | "all">("all");
  const [countryFilter, setCountryFilter] = useState<string>("all");
  const [disciplineFilter, setDisciplineFilter] = useState<DisciplineFilter>("all");
  const [yearFilter, setYearFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [selectedProposal, setSelectedProposal] = useState<ProposalTrackerItem | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [activeMetric, setActiveMetric] = useState<string | null>(null);

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ["proposalTrackerStats"],
    queryFn: () => api.getProposalTrackerStats(),
  });

  // Fetch countries for filter
  const { data: countriesData } = useQuery({
    queryKey: ["proposalTrackerCountries"],
    queryFn: () => api.getProposalTrackerCountries(),
  });

  // Fetch discipline stats for filter dropdown
  const { data: disciplineData } = useQuery({
    queryKey: ["proposalTrackerDisciplines"],
    queryFn: () => api.getProposalTrackerDisciplines(),
  });

  // Fetch proposals list
  const { data: proposalsData, isLoading } = useQuery({
    queryKey: ["proposalTrackerList", statusFilter, countryFilter, disciplineFilter, yearFilter, search, page],
    queryFn: () =>
      api.getProposalTrackerList({
        status: statusFilter !== "all" ? statusFilter : undefined,
        country: countryFilter !== "all" ? countryFilter : undefined,
        discipline: disciplineFilter !== "all" ? disciplineFilter : undefined,
        search: search || undefined,
        page,
        per_page: 50,
      }),
  });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const stats = statsData?.stats as any;
  const proposals = proposalsData?.proposals || [];
  const countries = countriesData?.countries || [];

  // Calculate totals for status breakdown visualization
  const statusTotals = useMemo(() => {
    if (!stats?.status_breakdown) return [];
    const total = stats.status_breakdown.reduce((sum: number, s: { count: number }) => sum + s.count, 0);
    return stats.status_breakdown.map((s: { current_status: string; count: number; total_value: number }) => ({
      ...s,
      percentage: total > 0 ? (s.count / total) * 100 : 0,
    }));
  }, [stats?.status_breakdown]);

  // PDF generation mutation
  const generatePdfMutation = useMutation({
    mutationFn: () => api.generateProposalPdf(),
    onSuccess: (data) => {
      if (data.success) {
        toast.success(`PDF generated successfully at ${data.pdf_path}`);
      } else {
        toast.error(data.message || "Failed to generate PDF");
      }
    },
    onError: (error: unknown) => {
      toast.error(error instanceof Error ? error.message : "Failed to generate PDF");
    },
  });

  // Export to CSV
  const handleExportCSV = () => {
    if (!proposals || proposals.length === 0) {
      toast.error("No data to export");
      return;
    }

    try {
      const exportData = prepareDataForExport(proposals as unknown as Record<string, unknown>[], {
        project_code: "Project Code",
        project_name: "Project Name",
        project_value: "Value",
        country: "Country",
        current_status: "Status",
        days_in_current_status: "Days in Status",
        current_remark: "Remark",
      });

      exportToCSV(exportData, "proposal-tracker");
      toast.success(`Exported ${proposals.length} proposals to CSV`);
    } catch (error) {
      toast.error("Failed to export data");
      console.error("Export error:", error);
    }
  };

  // Handle metric click to filter - toggles on/off and handles special cases
  const handleMetricClick = (metric: string, status?: string) => {
    // If clicking the same metric, clear all filters
    if (activeMetric === metric) {
      setActiveMetric(null);
      setStatusFilter("all");
      setPage(1);
      return;
    }

    setActiveMetric(metric);
    setPage(1);

    // Handle different metrics
    switch (metric) {
      case "pipeline":
        // Show all active proposals (clear status filter)
        setStatusFilter("all");
        break;
      case "followup":
        // "Needs Follow-up" - this requires client-side filtering
        // For now, clear status to show all and let UI highlight stalled ones
        setStatusFilter("all");
        break;
      case "avgdays":
        // Clicking avg days doesn't filter
        setStatusFilter("all");
        break;
      default:
        // For metrics with specific status (close, signed, lost)
        if (status) {
          setStatusFilter(status as ProposalStatus);
        }
    }
  };

  // Client-side filtering for "Needs Follow-up" (>14 days stalled)
  const filteredProposals = useMemo(() => {
    if (activeMetric === "followup") {
      return proposals.filter(p =>
        (p.days_in_current_status || 0) > 14 &&
        p.current_status !== "On Hold" &&
        p.current_status !== "Contract Signed"
      );
    }
    return proposals;
  }, [proposals, activeMetric]);

  return (
    <div className={cn(ds.gap.loose, "space-y-6")}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            Proposal Pipeline
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Track proposals from first contact to contract signed
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            className={cn(ds.gap.tight, ds.borderRadius.button)}
            onClick={handleExportCSV}
            disabled={!proposals || proposals.length === 0}
          >
            <Download className="h-4 w-4" aria-hidden="true" />
            Export CSV
          </Button>
          <Button
            variant="outline"
            className={cn(ds.gap.tight, ds.borderRadius.button)}
            onClick={() => generatePdfMutation.mutate()}
            disabled={generatePdfMutation.isPending}
          >
            {generatePdfMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <FileText className="h-4 w-4" aria-hidden="true" />
            )}
            {generatePdfMutation.isPending ? "Generating..." : "Generate PDF"}
          </Button>
        </div>
      </div>

      {/* KEY METRICS - Redesigned to 6 cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* 1. Pipeline Value - HERO CARD */}
          <Card
            className={cn(
              "md:col-span-2 lg:col-span-1",
              "bg-gradient-to-br from-indigo-600 to-purple-700 text-white border-0",
              "cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.01]",
              activeMetric === "pipeline" && "ring-2 ring-white/50"
            )}
            onClick={() => handleMetricClick("pipeline")}
          >
            <CardHeader className="pb-2">
              <CardTitle className="text-indigo-100 text-sm font-medium flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Total Pipeline Value
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {formatCurrency(stats.total_pipeline_value)}
              </div>
              <div className="flex items-center gap-4 mt-3 text-indigo-200 text-sm">
                <span>{stats.total_proposals} proposals tracked</span>
                <span className="flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  {stats.active_proposals_count} active
                </span>
              </div>
            </CardContent>
          </Card>

          {/* 2. Close to Signing */}
          <Card
            className={cn(
              "border-emerald-200 bg-gradient-to-br from-emerald-50 to-green-50",
              "cursor-pointer transition-all duration-200 hover:shadow-md hover:scale-[1.01]",
              activeMetric === "close" && "ring-2 ring-emerald-400"
            )}
            onClick={() => handleMetricClick("close", "Proposal Sent")}
          >
            <CardHeader className="pb-2">
              <CardTitle className="text-emerald-700 text-sm font-medium flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Close to Signing
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-emerald-800">
                  {stats.status_breakdown?.find((s: { current_status: string }) => s.current_status === "Proposal Sent")?.count || 0}
                </span>
                <span className="text-sm text-emerald-600">proposals sent</span>
              </div>
              <p className="text-emerald-700 font-medium mt-1">
                {formatCurrency(stats.status_breakdown?.find((s: { current_status: string }) => s.current_status === "Proposal Sent")?.total_value || 0)}
              </p>
            </CardContent>
          </Card>

          {/* 3. Needs Follow-up - WARNING */}
          <Card
            className={cn(
              "border-amber-300 bg-gradient-to-br from-amber-50 to-orange-50",
              "cursor-pointer transition-all duration-200 hover:shadow-md hover:scale-[1.01]",
              activeMetric === "followup" && "ring-2 ring-amber-400"
            )}
            onClick={() => handleMetricClick("followup")}
          >
            <CardHeader className="pb-2">
              <CardTitle className="text-amber-700 text-sm font-medium flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Needs Follow-up
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-amber-800">
                  {stats.needs_followup}
                </span>
                <span className="text-sm text-amber-600">stalled &gt;14 days</span>
              </div>
              <p className="text-amber-600 text-sm mt-1">
                Requires immediate attention
              </p>
            </CardContent>
          </Card>

          {/* 4. Contracts Signed YTD - SUCCESS */}
          <Card
            className={cn(
              "border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50",
              "cursor-pointer transition-all duration-200 hover:shadow-md hover:scale-[1.01]",
              activeMetric === "signed" && "ring-2 ring-blue-400"
            )}
            onClick={() => handleMetricClick("signed", "Contract Signed")}
          >
            <CardHeader className="pb-2">
              <CardTitle className="text-blue-700 text-sm font-medium flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Contracts Signed 2025
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-blue-800">
                  {stats.signed_2025_count || 0}
                </span>
                <span className="text-sm text-blue-600">this year</span>
              </div>
              <p className="text-blue-700 font-medium mt-1">
                {formatCurrency(stats.signed_2025_value || 0)}
              </p>
            </CardContent>
          </Card>

          {/* 5. Archived/Lost Projects - with placeholder loss reason tracking */}
          <Card
            className={cn(
              "border-slate-200 bg-gradient-to-br from-slate-50 to-gray-50",
              "cursor-pointer transition-all duration-200 hover:shadow-md hover:scale-[1.01]",
              activeMetric === "lost" && "ring-2 ring-slate-400"
            )}
            onClick={() => handleMetricClick("lost", "Archived")}
          >
            <CardHeader className="pb-2">
              <CardTitle className="text-slate-600 text-sm font-medium flex items-center gap-2">
                <XCircle className="h-4 w-4" />
                Archived / Lost
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-slate-700">
                  {stats.status_breakdown?.find((s: { current_status: string }) => s.current_status === "Archived")?.count || 0}
                </span>
                <span className="text-sm text-slate-500">proposals</span>
              </div>
              <p className="text-slate-500 text-sm mt-1">
                {formatCurrency(stats.status_breakdown?.find((s: { current_status: string }) => s.current_status === "Archived")?.total_value || 0)}
              </p>
              {/* Loss reason breakdown placeholder - will show when data is entered */}
              <div className="mt-2 pt-2 border-t border-slate-200">
                <p className="text-xs text-slate-400">
                  Track: Competitor won • Fee too high • We declined • No follow-up
                </p>
              </div>
            </CardContent>
          </Card>

          {/* 6. Avg Days to Progress */}
          <Card
            className={cn(
              "border-slate-200",
              "cursor-pointer transition-all duration-200 hover:shadow-md hover:scale-[1.01]",
              activeMetric === "avgdays" && "ring-2 ring-slate-400"
            )}
            onClick={() => handleMetricClick("avgdays")}
          >
            <CardHeader className="pb-2">
              <CardTitle className="text-slate-600 text-sm font-medium flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Avg Days in Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-slate-700">
                  {Math.round(stats.avg_days_in_status)}
                </span>
                <span className="text-sm text-slate-500">days</span>
              </div>
              <p className="text-slate-500 text-sm mt-1 flex items-center gap-1">
                {stats.avg_days_in_status < 20 ? (
                  <>
                    <TrendingDown className="h-3 w-3 text-emerald-500" />
                    <span className="text-emerald-600">Good velocity</span>
                  </>
                ) : (
                  <>
                    <TrendingUp className="h-3 w-3 text-amber-500" />
                    <span className="text-amber-600">Could improve</span>
                  </>
                )}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* STATUS PIPELINE VISUALIZATION */}
      {stats && statusTotals.length > 0 && (
        <Card className="border-slate-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-600">
              Pipeline by Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* Horizontal stacked bar */}
            <div className="flex h-8 rounded-lg overflow-hidden mb-4">
              {statusTotals.map((status: { current_status: string; count: number; total_value: number; percentage: number }) => {
                const colors = STATUS_COLORS[status.current_status as keyof typeof STATUS_COLORS] || STATUS_COLORS["First Contact"];
                return (
                  <div
                    key={status.current_status}
                    className={cn(
                      colors.fill,
                      "flex items-center justify-center cursor-pointer transition-all hover:opacity-80",
                      statusFilter === status.current_status && "ring-2 ring-offset-1 ring-slate-400"
                    )}
                    style={{ width: `${Math.max(status.percentage, 5)}%` }}
                    onClick={() => {
                      setStatusFilter(statusFilter === status.current_status ? "all" : status.current_status as ProposalStatus);
                      setPage(1);
                    }}
                    title={`${status.current_status}: ${status.count} (${formatCurrency(status.total_value)})`}
                  >
                    {status.percentage > 10 && (
                      <span className="text-white text-xs font-medium">{status.count}</span>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Legend */}
            <div className="flex flex-wrap gap-4">
              {statusTotals.map((status: { current_status: string; count: number; total_value: number; percentage: number }) => {
                const colors = STATUS_COLORS[status.current_status as keyof typeof STATUS_COLORS] || STATUS_COLORS["First Contact"];
                return (
                  <button
                    key={status.current_status}
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-md transition-all",
                      colors.bg,
                      statusFilter === status.current_status && "ring-2 ring-slate-400"
                    )}
                    onClick={() => {
                      setStatusFilter(statusFilter === status.current_status ? "all" : status.current_status as ProposalStatus);
                      setPage(1);
                    }}
                  >
                    <div className={cn("w-3 h-3 rounded-full", colors.fill)} />
                    <span className={cn("text-sm font-medium", colors.text)}>
                      {status.current_status}
                    </span>
                    <Badge variant="secondary" className="text-xs">
                      {status.count}
                    </Badge>
                    <span className="text-xs text-slate-500">
                      {formatCurrency(status.total_value)}
                    </span>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
        <CardContent className={ds.spacing.spacious}>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className={cn(
                "absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4",
                ds.textColors.tertiary
              )} aria-hidden="true" />
              <Input
                placeholder="Search by project code or name..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className={cn("pl-10", ds.borderRadius.input)}
                aria-label="Search proposals by project code or name"
              />
            </div>

            {/* Discipline Filter - with counts from API */}
            <Select
              value={disciplineFilter}
              onValueChange={(value) => {
                setDisciplineFilter(value as DisciplineFilter);
                setPage(1);
              }}
            >
              <SelectTrigger className={cn("w-[220px]", ds.borderRadius.input)} aria-label="Filter by discipline">
                <Filter className={cn("h-4 w-4 mr-2", ds.textColors.tertiary)} aria-hidden="true" />
                <SelectValue placeholder="Discipline" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">
                  All Disciplines ({disciplineData?.disciplines?.all?.count || 0})
                </SelectItem>
                <SelectItem value="landscape">
                  Landscape ({disciplineData?.disciplines?.landscape?.count || 0})
                </SelectItem>
                <SelectItem value="interior">
                  Interior ({disciplineData?.disciplines?.interior?.count || 0})
                </SelectItem>
                <SelectItem value="architect">
                  Architecture ({disciplineData?.disciplines?.architect?.count || 0})
                </SelectItem>
                <SelectItem value="combined">
                  Combined ({disciplineData?.disciplines?.combined?.count || 0})
                </SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={statusFilter}
              onValueChange={(value) => {
                setStatusFilter(value as ProposalStatus | "all");
                setPage(1);
              }}
            >
              <SelectTrigger className={cn("w-[180px]", ds.borderRadius.input)} aria-label="Filter by proposal status">
                <Filter className={cn("h-4 w-4 mr-2", ds.textColors.tertiary)} aria-hidden="true" />
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="First Contact">First Contact</SelectItem>
                <SelectItem value="Drafting">Drafting</SelectItem>
                <SelectItem value="Proposal Sent">Proposal Sent</SelectItem>
                <SelectItem value="On Hold">On Hold</SelectItem>
                <SelectItem value="Contract Signed">Contract Signed</SelectItem>
                <SelectItem value="Archived">Archived</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={countryFilter}
              onValueChange={(value) => {
                setCountryFilter(value);
                setPage(1);
              }}
            >
              <SelectTrigger className={cn("w-[180px]", ds.borderRadius.input)} aria-label="Filter by country">
                <Filter className={cn("h-4 w-4 mr-2", ds.textColors.tertiary)} aria-hidden="true" />
                <SelectValue placeholder="Country" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Countries</SelectItem>
                {countries.map((country) => (
                  <SelectItem key={country} value={country}>
                    {country}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={yearFilter}
              onValueChange={(value) => {
                setYearFilter(value);
                setPage(1);
              }}
            >
              <SelectTrigger className={cn("w-[140px]", ds.borderRadius.input)} aria-label="Filter by year">
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Years</SelectItem>
                <SelectItem value="2025">2025</SelectItem>
                <SelectItem value="2024">2024</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Proposals Table */}
      <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
        <CardContent className={ds.spacing.spacious}>
          {isLoading ? (
            <div className="space-y-3 p-6">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-12 w-24" />
                  <Skeleton className="h-12 flex-1" />
                  <Skeleton className="h-12 w-32" />
                  <Skeleton className="h-12 w-24" />
                  <Skeleton className="h-12 w-24" />
                  <Skeleton className="h-12 w-16" />
                  <Skeleton className="h-12 flex-1" />
                </div>
              ))}
            </div>
          ) : filteredProposals.length === 0 ? (
            <div className="py-16 text-center">
              <FileText className="mx-auto h-16 w-16 text-slate-300 mb-4" aria-hidden="true" />
              <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
                No proposals found
              </p>
              <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                {search || statusFilter !== "all" || countryFilter !== "all" || yearFilter !== "all" || activeMetric
                  ? "Try adjusting your filters"
                  : "Proposals will appear here once created"}
              </p>
              {activeMetric && (
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => {
                    setActiveMetric(null);
                    setStatusFilter("all");
                  }}
                >
                  Clear metric filter
                </Button>
              )}
            </div>
          ) : (
            <div className={cn("rounded-md border border-slate-200", ds.borderRadius.card)}>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className={cn("w-[120px]", ds.typography.captionBold)}>
                      Project #
                    </TableHead>
                    <TableHead className={ds.typography.captionBold}>
                      Project Name
                    </TableHead>
                    <TableHead className={cn("text-right min-w-[120px]", ds.typography.captionBold)}>
                      Value
                    </TableHead>
                    <TableHead className={ds.typography.captionBold}>
                      Country
                    </TableHead>
                    <TableHead className={ds.typography.captionBold}>
                      Status
                    </TableHead>
                    <TableHead className={cn("text-center", ds.typography.captionBold)}>
                      Last Activity
                    </TableHead>
                    <TableHead className={ds.typography.captionBold}>
                      Remark
                    </TableHead>
                    <TableHead className={cn("w-[80px] text-center", ds.typography.captionBold)}>
                      Actions
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredProposals.map((proposal) => {
                    const activityColor = getActivityColor(proposal.days_in_current_status);
                    return (
                      <TableRow
                        key={proposal.id}
                        className={cn("cursor-pointer", ds.hover.subtle)}
                        onClick={() => {
                          router.push(`/proposals/${encodeURIComponent(proposal.project_code)}`);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            router.push(`/proposals/${encodeURIComponent(proposal.project_code)}`);
                          }
                        }}
                        tabIndex={0}
                        role="button"
                      >
                        <TableCell className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                          {proposal.project_code}
                        </TableCell>
                        <TableCell className={cn(ds.typography.body, ds.textColors.primary)}>
                          {proposal.project_name}
                        </TableCell>
                        <TableCell className={cn("text-right min-w-[120px] whitespace-nowrap", ds.typography.body, ds.textColors.primary)}>
                          {formatCurrency(proposal.project_value)}
                        </TableCell>
                        <TableCell className={cn(ds.typography.body, ds.textColors.secondary)}>
                          {proposal.country}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={cn(
                              ds.typography.tiny,
                              ds.borderRadius.badge,
                              getStatusColor(proposal.current_status as ProposalStatus)
                            )}
                          >
                            {proposal.current_status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <div className={cn(
                            "inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium",
                            activityColor.bg,
                            activityColor.text
                          )}>
                            <Clock className="h-3 w-3" />
                            {proposal.days_in_current_status}d
                          </div>
                        </TableCell>
                        <TableCell className={cn("max-w-[300px] truncate", ds.typography.caption, ds.textColors.tertiary)}>
                          {proposal.current_remark || "-"}
                        </TableCell>
                        <TableCell className="text-center">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedProposal(proposal);
                              setEditDialogOpen(true);
                            }}
                            className="h-8 w-8 p-0"
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}

          {/* Pagination */}
          {proposalsData && proposalsData.total_pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                Showing {(page - 1) * 50 + 1} to{" "}
                {Math.min(page * 50, proposalsData.total)} of {proposalsData.total}{" "}
                proposals
              </div>
              <div className={cn(ds.gap.tight, "flex")}>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  className={ds.borderRadius.button}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page === proposalsData.total_pages}
                  className={ds.borderRadius.button}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Edit Dialog */}
      <ProposalQuickEditDialog
        proposal={selectedProposal}
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
      />
    </div>
  );
}
