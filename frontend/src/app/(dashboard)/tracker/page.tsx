"use client";

import { useState, useMemo, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
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
import {
  Search,
  Filter,
  FileText,
  Loader2,
  Download,
  Pencil,
  TrendingUp,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Mail,
  Copy,
  X,
} from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { formatCurrency, cn } from "@/lib/utils";
import { ds, bensleyVoice } from "@/lib/design-system";
import { type ProposalStatus } from "@/lib/constants";
import { Skeleton } from "@/components/ui/skeleton";
import { exportToCSV, prepareDataForExport } from "@/lib/export-utils";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

// Status colors for the pipeline visualization
const STATUS_COLORS: Record<string, { bg: string; fill: string; text: string }> = {
  "First Contact": { bg: "bg-blue-50", fill: "bg-blue-400", text: "text-blue-700" },
  "Meeting Held": { bg: "bg-cyan-50", fill: "bg-cyan-500", text: "text-cyan-700" },
  "Proposal Prep": { bg: "bg-yellow-50", fill: "bg-yellow-500", text: "text-yellow-700" },
  "Proposal Sent": { bg: "bg-amber-50", fill: "bg-amber-500", text: "text-amber-700" },
  "Negotiation": { bg: "bg-purple-50", fill: "bg-purple-500", text: "text-purple-700" },
  "On Hold": { bg: "bg-gray-100", fill: "bg-gray-400", text: "text-gray-600" },
  "Contract Signed": { bg: "bg-emerald-50", fill: "bg-emerald-500", text: "text-emerald-700" },
  "Lost": { bg: "bg-red-50", fill: "bg-red-400", text: "text-red-600" },
  "Declined": { bg: "bg-rose-50", fill: "bg-rose-400", text: "text-rose-600" },
  "Dormant": { bg: "bg-slate-100", fill: "bg-slate-400", text: "text-slate-500" },
  "Cancelled": { bg: "bg-stone-100", fill: "bg-stone-400", text: "text-stone-500" },
};

// Activity color based on days since last activity
function getActivityColor(days: number): { bg: string; text: string; label: string } {
  if (days <= 7) return { bg: "bg-emerald-100", text: "text-emerald-700", label: "Active" };
  if (days <= 14) return { bg: "bg-amber-100", text: "text-amber-700", label: "Needs attention" };
  return { bg: "bg-red-100", text: "text-red-700", label: "Stalled" };
}

// All valid proposal statuses for the dropdown (synced with database)
// Issue #119: Removed "Meeting Held" and "Cancelled" - not in database
const ALL_STATUSES = [
  "First Contact",
  "Proposal Prep",
  "Proposal Sent",
  "Negotiation",
  "On Hold",
  "Contract Signed",
  "Lost",
  "Declined",
  "Dormant",
] as const;

function ProposalTrackerContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const codeParam = searchParams.get("code");
  const highlightParam = searchParams.get("highlight");
  const filterParam = searchParams.get("filter");

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ProposalStatus | "all">("all");
  const [disciplineFilter, setDisciplineFilter] = useState<DisciplineFilter>("all");
  const [yearFilter, setYearFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [selectedProposal, setSelectedProposal] = useState<ProposalTrackerItem | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [activeMetric, setActiveMetric] = useState<string | null>(null);
  const [, setHighlightedCode] = useState<string | null>(null);
  const [sortField, setSortField] = useState<"value" | "date" | "status" | "days" | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [followUpDialogOpen, setFollowUpDialogOpen] = useState(false);
  const [followUpEmail, setFollowUpEmail] = useState<{ subject: string; body: string; projectName: string } | null>(null);

  // Read URL params on mount - auto-search for code if provided
  useEffect(() => {
    if (codeParam) {
      setSearch(codeParam);
      if (highlightParam === "true") {
        setHighlightedCode(codeParam);
      }
    }
    // Handle filter param from FollowUpWidget
    if (filterParam === "needs-followup") {
      setActiveMetric("followup");
    }
  }, [codeParam, highlightParam, filterParam]);

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ["proposalTrackerStats"],
    queryFn: () => api.getProposalTrackerStats(),
  });

  // Fetch discipline stats for filter dropdown
  const { data: disciplineData } = useQuery({
    queryKey: ["proposalTrackerDisciplines"],
    queryFn: () => api.getProposalTrackerDisciplines(),
  });

  // Fetch proposals list
  const { data: proposalsData, isLoading } = useQuery({
    queryKey: ["proposalTrackerList", statusFilter, disciplineFilter, yearFilter, search, page],
    queryFn: () =>
      api.getProposalTrackerList({
        status: statusFilter !== "all" ? statusFilter : undefined,
        discipline: disciplineFilter !== "all" ? disciplineFilter : undefined,
        search: search || undefined,
        page,
        per_page: 50,
      }),
  });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const stats = statsData?.stats as any;
  const proposals = useMemo(() => proposalsData?.proposals || [], [proposalsData]);

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
        toast.success("PDF generated successfully");
      } else {
        toast.error(data.message || "Failed to generate PDF");
      }
    },
    onError: (error: unknown) => {
      toast.error(error instanceof Error ? error.message : "Failed to generate PDF");
    },
  });

  // Quick status update mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ projectCode, newStatus }: { projectCode: string; newStatus: string }) =>
      api.updateProposalTracker(projectCode, { current_status: newStatus as ProposalStatus }),
    onSuccess: (data, variables) => {
      toast.success(`Status updated to ${variables.newStatus}`);
      // Refresh the list
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerList"] });
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerStats"] });
    },
    onError: (error: unknown) => {
      toast.error(error instanceof Error ? error.message : "Failed to update status");
    },
  });

  // Draft follow-up email mutation
  const draftFollowUpMutation = useMutation({
    mutationFn: ({ proposalId, projectName }: { proposalId: number; projectName: string }) =>
      api.draftFollowUpEmail(proposalId, "professional").then(data => ({ ...data, projectName })),
    onSuccess: (data) => {
      if (data.success && data.subject && data.body) {
        setFollowUpEmail({
          subject: data.subject,
          body: data.body,
          projectName: data.projectName,
        });
        setFollowUpDialogOpen(true);
      } else {
        toast.error(data.error || "Failed to generate follow-up email");
      }
    },
    onError: (error: unknown) => {
      toast.error(error instanceof Error ? error.message : "Failed to draft follow-up");
    },
  });

  // Copy email to clipboard
  const handleCopyEmail = () => {
    if (followUpEmail) {
      const emailText = `Subject: ${followUpEmail.subject}\n\n${followUpEmail.body}`;
      navigator.clipboard.writeText(emailText);
      toast.success("Email copied to clipboard");
    }
  };

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

  // Client-side filtering for "Needs Follow-up" (>14 days stalled) and sorting
  const filteredProposals = useMemo(() => {
    let result = proposals;

    // Apply follow-up filter
    if (activeMetric === "followup") {
      result = result.filter(p =>
        (p.days_in_current_status || 0) > 14 &&
        p.current_status !== "On Hold" &&
        p.current_status !== "Contract Signed"
      );
    }

    // Apply sorting
    if (sortField) {
      result = [...result].sort((a, b) => {
        let comparison = 0;

        switch (sortField) {
          case "value":
            comparison = (a.project_value || 0) - (b.project_value || 0);
            break;
          case "date":
            const dateA = a.last_email_date ? new Date(a.last_email_date).getTime() : 0;
            const dateB = b.last_email_date ? new Date(b.last_email_date).getTime() : 0;
            comparison = dateA - dateB;
            break;
          case "status":
            comparison = (a.current_status || "").localeCompare(b.current_status || "");
            break;
          case "days":
            comparison = (a.days_in_current_status || 0) - (b.days_in_current_status || 0);
            break;
        }

        return sortDirection === "asc" ? comparison : -comparison;
      });
    }

    return result;
  }, [proposals, activeMetric, sortField, sortDirection]);

  // Toggle sort on column click
  const handleSort = (field: "value" | "date" | "status" | "days") => {
    if (sortField === field) {
      // Toggle direction or clear if already desc
      if (sortDirection === "desc") {
        setSortDirection("asc");
      } else {
        setSortField(null);
      }
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  // Get sort icon for a column
  const getSortIcon = (field: "value" | "date" | "status" | "days") => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-3 w-3 ml-1 opacity-50" />;
    }
    return sortDirection === "desc"
      ? <ArrowDown className="h-3 w-3 ml-1" />
      : <ArrowUp className="h-3 w-3 ml-1" />;
  };

  return (
    <div className={cn(ds.gap.loose, "space-y-6 w-full max-w-full overflow-x-hidden")}>
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

      {/* YEAR OVERVIEW - 4 summary cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total Pipeline */}
          <Card className={cn("border-slate-200", activeMetric === "pipeline" && "ring-2 ring-slate-400")}
                onClick={() => { setStatusFilter("all"); setActiveMetric("pipeline"); }}>
            <CardContent className="pt-4">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Total Pipeline</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">{stats.all_proposals_total || stats.total_proposals}</p>
              <p className="text-sm font-semibold text-slate-600">{formatCurrency(stats.all_proposals_value || stats.total_pipeline_value)}</p>
            </CardContent>
          </Card>

          {/* Won (Contract Signed) */}
          <Card className={cn("border-emerald-200 bg-emerald-50/50", activeMetric === "signed" && "ring-2 ring-emerald-400")}
                onClick={() => handleMetricClick("signed", "Contract Signed")}>
            <CardContent className="pt-4">
              <p className="text-xs font-medium text-emerald-600 uppercase tracking-wide flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" /> Won
              </p>
              <p className="text-2xl font-bold text-emerald-700 mt-1">{stats.won_count || 0}</p>
              <p className="text-sm font-semibold text-emerald-600">{formatCurrency(stats.won_value || 0)}</p>
            </CardContent>
          </Card>

          {/* Lost/Declined */}
          <Card className={cn("border-red-200 bg-red-50/50", activeMetric === "lost" && "ring-2 ring-red-400")}
                onClick={() => handleMetricClick("lost", "Lost")}>
            <CardContent className="pt-4">
              <p className="text-xs font-medium text-red-600 uppercase tracking-wide flex items-center gap-1">
                <XCircle className="h-3 w-3" /> Lost
              </p>
              <p className="text-2xl font-bold text-red-700 mt-1">{stats.lost_count || 0}</p>
              <p className="text-sm font-semibold text-red-600">{formatCurrency(stats.lost_value || 0)}</p>
            </CardContent>
          </Card>

          {/* Still Active */}
          <Card className={cn("border-blue-200 bg-blue-50/50", activeMetric === "active" && "ring-2 ring-blue-400")}
                onClick={() => { setStatusFilter("all"); setActiveMetric("active"); }}>
            <CardContent className="pt-4">
              <p className="text-xs font-medium text-blue-600 uppercase tracking-wide flex items-center gap-1">
                <TrendingUp className="h-3 w-3" /> Active
              </p>
              <p className="text-2xl font-bold text-blue-700 mt-1">{stats.active_proposals_count}</p>
              <p className="text-sm font-semibold text-blue-600">{formatCurrency(stats.active_proposals_value)}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* PIPELINE FUNNEL - Stages from early to close */}
      {stats && statusTotals.length > 0 && (
        <Card className="border-slate-200">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-slate-600">Pipeline Stages</CardTitle>
              <div className="flex items-center gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3 text-amber-500" />
                  {stats.needs_followup} need follow-up
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {/* Active funnel stages - ordered from early to close */}
            {[
              { status: "First Contact", color: "bg-slate-400", textColor: "text-slate-700", label: "First Contact" },
              { status: "Proposal Prep", color: "bg-blue-400", textColor: "text-blue-700", label: "Preparing Proposal" },
              { status: "Proposal Sent", color: "bg-amber-500", textColor: "text-amber-700", label: "Proposal Sent" },
              { status: "Negotiation", color: "bg-emerald-500", textColor: "text-emerald-700", label: "Negotiation" },
              { status: "On Hold", color: "bg-orange-400", textColor: "text-orange-700", label: "On Hold (Paused)" },
            ].map(({ status, color, textColor, label }) => {
              const data = stats.status_breakdown?.find((s: { current_status: string }) => s.current_status === status);
              const count = data?.count || 0;
              const value = data?.total_value || 0;
              const maxCount = Math.max(...(stats.status_breakdown?.map((s: { count: number }) => s.count) || [1]));
              const widthPercent = maxCount > 0 ? Math.max((count / maxCount) * 100, 8) : 8;

              return (
                <div
                  key={status}
                  className={cn(
                    "flex items-center gap-3 cursor-pointer p-2 rounded hover:bg-slate-50 transition-colors",
                    statusFilter === status && "bg-slate-100 ring-1 ring-slate-300"
                  )}
                  onClick={() => {
                    setStatusFilter(statusFilter === status ? "all" : status as ProposalStatus);
                    setPage(1);
                  }}
                >
                  {/* Stage label */}
                  <span className={cn("w-36 text-sm font-medium", textColor)}>{label}</span>

                  {/* Bar */}
                  <div className="flex-1 h-6 bg-slate-100 rounded overflow-hidden">
                    <div
                      className={cn(color, "h-full flex items-center justify-end pr-2 transition-all")}
                      style={{ width: `${widthPercent}%` }}
                    >
                      {count > 0 && <span className="text-white text-xs font-bold">{count}</span>}
                    </div>
                  </div>

                  {/* Value */}
                  <span className="w-24 text-right text-sm font-medium text-slate-600">
                    {formatCurrency(value)}
                  </span>
                </div>
              );
            })}
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
              <p className={cn(ds.typography.cardHeader, ds.textColors.primary, "mb-2")}>
                {bensleyVoice.emptyStates.proposals}
              </p>
              <p className={cn(ds.typography.body, ds.textColors.tertiary, "mt-2")}>
                {search || statusFilter !== "all" || yearFilter !== "all" || activeMetric
                  ? bensleyVoice.emptyStates.search
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
            <div className={cn("rounded-md border border-slate-200 overflow-x-auto", ds.borderRadius.card)}>
              <Table className="min-w-[900px]">
                <TableHeader>
                  <TableRow>
                    <TableHead className={cn("w-[100px] min-w-[100px]", ds.typography.captionBold)}>
                      Project #
                    </TableHead>
                    <TableHead className={cn("min-w-[180px] max-w-[280px]", ds.typography.captionBold)}>
                      Project Name
                    </TableHead>
                    <TableHead
                      className={cn("text-right w-[90px] min-w-[90px] cursor-pointer hover:bg-slate-50 select-none", ds.typography.captionBold)}
                      onClick={() => handleSort("value")}
                    >
                      <span className="flex items-center justify-end">
                        Value {getSortIcon("value")}
                      </span>
                    </TableHead>
                    <TableHead
                      className={cn("w-[100px] min-w-[100px] cursor-pointer hover:bg-slate-50 select-none", ds.typography.captionBold)}
                      onClick={() => handleSort("date")}
                    >
                      <span className="flex items-center">
                        Last Contact {getSortIcon("date")}
                      </span>
                    </TableHead>
                    <TableHead
                      className={cn("w-[100px] min-w-[100px] cursor-pointer hover:bg-slate-50 select-none", ds.typography.captionBold)}
                      onClick={() => handleSort("status")}
                    >
                      <span className="flex items-center">
                        Status {getSortIcon("status")}
                      </span>
                    </TableHead>
                    <TableHead className={cn("text-center w-[60px] min-w-[60px]", ds.typography.captionBold)}>
                      Ball
                    </TableHead>
                    <TableHead
                      className={cn("text-center w-[80px] min-w-[80px] cursor-pointer hover:bg-slate-50 select-none", ds.typography.captionBold)}
                      onClick={() => handleSort("days")}
                    >
                      <span className="flex items-center justify-center">
                        Days {getSortIcon("days")}
                      </span>
                    </TableHead>
                    <TableHead className={cn("text-center w-[60px] min-w-[60px]", ds.typography.captionBold)}>
                      Health
                    </TableHead>
                    <TableHead className={cn("min-w-[180px] max-w-[300px]", ds.typography.captionBold)}>
                      Action Needed
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
                        <TableCell className={cn("font-mono text-sm", ds.textColors.primary)}>
                          {proposal.project_code}
                        </TableCell>
                        <TableCell className={cn("max-w-[280px]", ds.typography.body, ds.textColors.primary)}>
                          <span className="block truncate" title={proposal.project_name}>
                            {proposal.project_name}
                          </span>
                        </TableCell>
                        <TableCell className={cn("text-right whitespace-nowrap", ds.typography.body, ds.textColors.primary)}>
                          {formatCurrency(proposal.project_value)}
                        </TableCell>
                        <TableCell className={cn("text-xs", ds.textColors.secondary)}>
                          {proposal.last_email_date ? (
                            <div className="flex flex-col">
                              <span>{new Date(proposal.last_email_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                              {(proposal.email_count ?? 0) > 0 && (
                                <span className="text-slate-400">{proposal.email_count} emails</span>
                              )}
                            </div>
                          ) : "—"}
                        </TableCell>
                        <TableCell onClick={(e) => e.stopPropagation()}>
                          <Select
                            value={proposal.current_status}
                            onValueChange={(value) => {
                              updateStatusMutation.mutate({
                                projectCode: proposal.project_code,
                                newStatus: value,
                              });
                            }}
                            disabled={updateStatusMutation.isPending}
                          >
                            <SelectTrigger
                              className={cn(
                                "h-7 w-[130px] text-xs border-0 bg-transparent",
                                STATUS_COLORS[proposal.current_status]?.bg || "bg-slate-50",
                                STATUS_COLORS[proposal.current_status]?.text || "text-slate-600"
                              )}
                            >
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {ALL_STATUSES.map((status) => (
                                <SelectItem key={status} value={status} className="text-xs">
                                  <span className={cn(
                                    "px-1.5 py-0.5 rounded",
                                    STATUS_COLORS[status]?.bg,
                                    STATUS_COLORS[status]?.text
                                  )}>
                                    {status}
                                  </span>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell className="text-center">
                          {proposal.ball_in_court === 'us' ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700" title="Ball in our court">
                              Us
                            </span>
                          ) : proposal.ball_in_court === 'them' ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700" title="Waiting on client">
                              Them
                            </span>
                          ) : proposal.ball_in_court === 'mutual' ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700" title="Mutual action needed">
                              Both
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          <div className={cn(
                            "inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium whitespace-nowrap",
                            activityColor.bg,
                            activityColor.text
                          )}>
                            <Clock className="h-3 w-3" />
                            {proposal.days_in_current_status}d
                          </div>
                        </TableCell>
                        <TableCell className="text-center">
                          {/* Health Score Visual */}
                          {proposal.health_score != null ? (
                            <div
                              className={cn(
                                "inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold",
                                proposal.health_score >= 70 ? "bg-emerald-100 text-emerald-700" :
                                proposal.health_score >= 50 ? "bg-amber-100 text-amber-700" :
                                "bg-red-100 text-red-700"
                              )}
                              title={`Health: ${proposal.health_score}/100`}
                            >
                              {proposal.health_score}
                            </div>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </TableCell>
                        <TableCell className={cn("max-w-[300px]", ds.typography.caption)}>
                          {proposal.action_needed ? (
                            <span
                              className={cn(
                                "block truncate",
                                proposal.health_score && proposal.health_score < 50
                                  ? "text-red-700 font-medium"
                                  : ds.textColors.secondary
                              )}
                              title={proposal.action_needed}
                            >
                              {proposal.action_needed}
                            </span>
                          ) : proposal.current_remark ? (
                            <span className={cn("block truncate", ds.textColors.tertiary)} title={proposal.current_remark}>
                              {proposal.current_remark}
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          <div className="flex items-center justify-center gap-1">
                            {/* Follow Up Button - shows when ball is in our court or needs follow-up */}
                            {(proposal.ball_in_court === 'us' || proposal.days_in_current_status > 7) && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  draftFollowUpMutation.mutate({
                                    proposalId: proposal.id,
                                    projectName: proposal.project_name,
                                  });
                                }}
                                disabled={draftFollowUpMutation.isPending}
                                className="h-8 w-8 p-0 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                title="Draft follow-up email"
                              >
                                {draftFollowUpMutation.isPending ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Mail className="h-4 w-4" />
                                )}
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedProposal(proposal);
                                setEditDialogOpen(true);
                              }}
                              className="h-8 w-8 p-0"
                              title="Edit proposal"
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                          </div>
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

      {/* Follow-Up Email Dialog */}
      <Dialog open={followUpDialogOpen} onOpenChange={setFollowUpDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5 text-blue-600" />
              Follow-Up Email Draft
            </DialogTitle>
            <DialogDescription>
              {followUpEmail?.projectName && `Draft email for ${followUpEmail.projectName}`}
            </DialogDescription>
          </DialogHeader>
          {followUpEmail && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-700">Subject</label>
                <div className="mt-1 p-3 bg-slate-50 rounded-md border text-sm">
                  {followUpEmail.subject}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Body</label>
                <div className="mt-1 p-3 bg-slate-50 rounded-md border text-sm whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                  {followUpEmail.body}
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="outline"
                  onClick={() => setFollowUpDialogOpen(false)}
                >
                  <X className="h-4 w-4 mr-2" />
                  Close
                </Button>
                <Button
                  onClick={handleCopyEmail}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy to Clipboard
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Wrap in Suspense for useSearchParams (Next.js 14+ requirement)
export default function ProposalTrackerPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Loading tracker...</div>}>
      <ProposalTrackerContent />
    </Suspense>
  );
}
