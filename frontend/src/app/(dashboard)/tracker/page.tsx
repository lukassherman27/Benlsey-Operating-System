"use client";

import { useState, useMemo, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ProposalTrackerItem, DisciplineFilter } from "@/lib/types";
import { ProposalQuickEditDialog } from "@/components/proposal-quick-edit-dialog";
import { PriorityBanner } from "@/components/proposals/priority-banner";
import {
  MarkWonDialog,
  MarkLostDialog,
  CreateFollowUpDialog,
} from "@/components/proposals/quick-action-dialogs";
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
  User,
  CheckCheck,
  ArrowLeftRight,
  Trophy,
  Ban,
  Bookmark,
  BookmarkPlus,
  Trash2,
  MoreHorizontal,
  CalendarPlus,
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// Status colors for the pipeline visualization (matches database values)
const STATUS_COLORS: Record<string, { bg: string; fill: string; text: string }> = {
  "First Contact": { bg: "bg-blue-50", fill: "bg-blue-400", text: "text-blue-700" },
  "Proposal Prep": { bg: "bg-yellow-50", fill: "bg-yellow-500", text: "text-yellow-700" },
  "Proposal Sent": { bg: "bg-amber-50", fill: "bg-amber-500", text: "text-amber-700" },
  "Negotiation": { bg: "bg-purple-50", fill: "bg-purple-500", text: "text-purple-700" },
  "On Hold": { bg: "bg-gray-100", fill: "bg-gray-400", text: "text-gray-600" },
  "Contract Signed": { bg: "bg-emerald-50", fill: "bg-emerald-500", text: "text-emerald-700" },
  "Lost": { bg: "bg-red-50", fill: "bg-red-400", text: "text-red-600" },
  "Declined": { bg: "bg-rose-50", fill: "bg-rose-400", text: "text-rose-600" },
  "Dormant": { bg: "bg-slate-100", fill: "bg-slate-400", text: "text-slate-500" },
};

// Activity color based on days since last activity
function getActivityColor(days: number): { bg: string; text: string; label: string } {
  if (days <= 7) return { bg: "bg-emerald-100", text: "text-emerald-700", label: "Active" };
  if (days <= 14) return { bg: "bg-amber-100", text: "text-amber-700", label: "Needs attention" };
  return { bg: "bg-red-100", text: "text-red-700", label: "Stalled" };
}

// All valid proposal statuses for the dropdown (matches database values)
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

// Saved filter views type
interface SavedFilterView {
  id: string;
  name: string;
  filters: {
    search: string;
    statusFilter: string;
    disciplineFilter: string;
    ownerFilter: string;
    activeMetric: string | null;
  };
  createdAt: string;
}

const SAVED_VIEWS_KEY = "bensley-proposal-saved-views";

// Load saved views from localStorage
function loadSavedViews(): SavedFilterView[] {
  if (typeof window === "undefined") return [];
  try {
    const saved = localStorage.getItem(SAVED_VIEWS_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

// Save views to localStorage
function persistSavedViews(views: SavedFilterView[]) {
  if (typeof window === "undefined") return;
  localStorage.setItem(SAVED_VIEWS_KEY, JSON.stringify(views));
}

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
  const [ownerFilter, setOwnerFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [selectedProposal, setSelectedProposal] = useState<ProposalTrackerItem | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [activeMetric, setActiveMetric] = useState<string | null>(null);
  const [, setHighlightedCode] = useState<string | null>(null);
  const [sortField, setSortField] = useState<"value" | "date" | "status" | "days" | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [followUpDialogOpen, setFollowUpDialogOpen] = useState(false);
  const [followUpEmail, setFollowUpEmail] = useState<{ subject: string; body: string; projectName: string } | null>(null);

  // Quick action dialog state
  const [markWonDialogOpen, setMarkWonDialogOpen] = useState(false);
  const [markLostDialogOpen, setMarkLostDialogOpen] = useState(false);
  const [createFollowUpDialogOpen, setCreateFollowUpDialogOpen] = useState(false);
  const [quickActionProposal, setQuickActionProposal] = useState<ProposalTrackerItem | null>(null);

  // Saved filter views
  const [savedViews, setSavedViews] = useState<SavedFilterView[]>([]);
  const [saveViewDialogOpen, setSaveViewDialogOpen] = useState(false);
  const [newViewName, setNewViewName] = useState("");

  // Load saved views on mount
  useEffect(() => {
    setSavedViews(loadSavedViews());
  }, []);

  // Save current filters as a new view
  const handleSaveView = () => {
    if (!newViewName.trim()) {
      toast.error("Please enter a name for the view");
      return;
    }

    const newView: SavedFilterView = {
      id: Date.now().toString(),
      name: newViewName.trim(),
      filters: {
        search,
        statusFilter,
        disciplineFilter,
        ownerFilter,
        activeMetric,
      },
      createdAt: new Date().toISOString(),
    };

    const updatedViews = [...savedViews, newView];
    setSavedViews(updatedViews);
    persistSavedViews(updatedViews);
    setNewViewName("");
    setSaveViewDialogOpen(false);
    toast.success(`Saved view "${newViewName}"`);
  };

  // Apply a saved view
  const handleApplyView = (view: SavedFilterView) => {
    setSearch(view.filters.search);
    setStatusFilter(view.filters.statusFilter as ProposalStatus | "all");
    setDisciplineFilter(view.filters.disciplineFilter as DisciplineFilter);
    setOwnerFilter(view.filters.ownerFilter);
    setActiveMetric(view.filters.activeMetric);
    setPage(1);
    toast.success(`Applied "${view.name}"`);
  };

  // Delete a saved view
  const handleDeleteView = (viewId: string) => {
    const updatedViews = savedViews.filter(v => v.id !== viewId);
    setSavedViews(updatedViews);
    persistSavedViews(updatedViews);
    toast.success("View deleted");
  };

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
    queryKey: ["proposalTrackerList", statusFilter, disciplineFilter, search, page],
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

  // Quick action: Mark as followed up (ball to them)
  const markFollowedUpMutation = useMutation({
    mutationFn: ({ projectCode }: { projectCode: string }) =>
      api.updateProposalTracker(projectCode, { ball_in_court: 'them' }),
    onSuccess: (_, variables) => {
      toast.success(`Marked as followed up - ball now with client`);
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerList"] });
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerStats"] });
    },
    onError: (error: unknown) => {
      toast.error(error instanceof Error ? error.message : "Failed to update");
    },
  });

  // Quick action: Flip ball in court
  const flipBallMutation = useMutation({
    mutationFn: ({ projectCode, currentBall }: { projectCode: string; currentBall: string }) =>
      api.updateProposalTracker(projectCode, {
        ball_in_court: currentBall === 'us' ? 'them' : 'us'
      }),
    onSuccess: (_, variables) => {
      const newBall = variables.currentBall === 'us' ? 'client' : 'us';
      toast.success(`Ball now with ${newBall}`);
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerList"] });
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerStats"] });
    },
    onError: (error: unknown) => {
      toast.error(error instanceof Error ? error.message : "Failed to update");
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

  // Client-side filtering for owner, follow-up, overdue, and sorting
  const filteredProposals = useMemo(() => {
    let result = proposals;

    // Apply owner filter
    if (ownerFilter !== "all") {
      result = result.filter(p => p.action_owner === ownerFilter);
    }

    // Apply follow-up filter
    if (activeMetric === "followup") {
      result = result.filter(p =>
        (p.days_in_current_status || 0) > 14 &&
        p.current_status !== "On Hold" &&
        p.current_status !== "Contract Signed"
      );
    }

    // Apply overdue filter
    if (activeMetric === "overdue") {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      result = result.filter(p => {
        if (!p.action_due) return false;
        return new Date(p.action_due) < today;
      });
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
  }, [proposals, ownerFilter, activeMetric, sortField, sortDirection]);

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

      {/* Priority Banner - shows overdue and "your move" items */}
      {proposals.length > 0 && (
        <PriorityBanner
          proposals={proposals}
          onFilterOverdue={() => setActiveMetric("overdue")}
          onFilterMyMove={() => setOwnerFilter("bill")}
        />
      )}

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
                {(stats.overdue_count ?? 0) > 0 && (
                  <span className="flex items-center gap-1 text-red-600 font-semibold">
                    <AlertTriangle className="h-3 w-3" />
                    {stats.overdue_count} overdue
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3 text-amber-500" />
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
        <CardContent className="py-3 px-4">
          <div className="flex flex-wrap items-center gap-2">
            {/* Search */}
            <div className="relative w-full sm:w-auto sm:flex-1 sm:max-w-xs">
              <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                className="pl-8 h-8 text-sm"
              />
            </div>

            {/* Status Filter */}
            <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v as ProposalStatus | "all"); setPage(1); }}>
              <SelectTrigger className="w-[130px] h-8 text-sm">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                {ALL_STATUSES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>

            {/* Owner Filter */}
            <Select value={ownerFilter} onValueChange={(v) => { setOwnerFilter(v); setPage(1); }}>
              <SelectTrigger className="w-[100px] h-8 text-sm">
                <SelectValue placeholder="Owner" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="bill">Bill</SelectItem>
                <SelectItem value="brian">Brian</SelectItem>
                <SelectItem value="lukas">Lukas</SelectItem>
                <SelectItem value="mink">Mink</SelectItem>
              </SelectContent>
            </Select>

            {/* Discipline Filter */}
            <Select value={disciplineFilter} onValueChange={(v) => { setDisciplineFilter(v as DisciplineFilter); setPage(1); }}>
              <SelectTrigger className="w-[120px] h-8 text-sm">
                <SelectValue placeholder="Discipline" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All ({disciplineData?.disciplines?.all?.count || 0})</SelectItem>
                <SelectItem value="landscape">LA ({disciplineData?.disciplines?.landscape?.count || 0})</SelectItem>
                <SelectItem value="interior">ID ({disciplineData?.disciplines?.interior?.count || 0})</SelectItem>
                <SelectItem value="architect">Arch ({disciplineData?.disciplines?.architect?.count || 0})</SelectItem>
                <SelectItem value="combined">Combined ({disciplineData?.disciplines?.combined?.count || 0})</SelectItem>
              </SelectContent>
            </Select>

            {/* Saved Views */}
            {savedViews.length > 0 && (
              <Select value="" onValueChange={(id) => { const v = savedViews.find(x => x.id === id); if (v) handleApplyView(v); }}>
                <SelectTrigger className="w-[120px] h-8 text-sm">
                  <Bookmark className="h-3 w-3 mr-1" />
                  <SelectValue placeholder="Views" />
                </SelectTrigger>
                <SelectContent>
                  {savedViews.map((view) => (
                    <div key={view.id} className="flex items-center justify-between px-2 py-1 hover:bg-slate-100 rounded cursor-pointer group">
                      <span className="text-sm" onClick={() => handleApplyView(view)}>{view.name}</span>
                      <Button variant="ghost" size="sm" className="h-5 w-5 p-0 opacity-0 group-hover:opacity-100 text-red-500" onClick={(e) => { e.stopPropagation(); handleDeleteView(view.id); }}>
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </SelectContent>
              </Select>
            )}

            {/* Save View */}
            <Button variant="outline" size="sm" onClick={() => setSaveViewDialogOpen(true)} className="h-8 text-xs gap-1">
              <BookmarkPlus className="h-3 w-3" />
              Save
            </Button>

            {/* Clear Filters - show when any filter is active */}
            {(search || statusFilter !== "all" || ownerFilter !== "all" || disciplineFilter !== "all" || activeMetric) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSearch("");
                  setStatusFilter("all");
                  setOwnerFilter("all");
                  setDisciplineFilter("all");
                  setActiveMetric(null);
                  setPage(1);
                }}
                className="h-8 text-xs text-slate-500 hover:text-slate-700"
              >
                <X className="h-3 w-3 mr-1" />
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Save View Dialog */}
      <Dialog open={saveViewDialogOpen} onOpenChange={setSaveViewDialogOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>Save Filter View</DialogTitle>
            <DialogDescription>
              Save your current filters as a reusable view.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label htmlFor="view-name" className="text-sm font-medium text-slate-700">
                View Name
              </label>
              <Input
                id="view-name"
                placeholder="e.g., My Hot Deals, Overdue Proposals"
                value={newViewName}
                onChange={(e) => setNewViewName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSaveView();
                }}
              />
            </div>
            <div className="text-xs text-slate-500">
              <p className="font-medium mb-1">Current filters:</p>
              <ul className="space-y-0.5">
                {search && <li>Search: &quot;{search}&quot;</li>}
                {statusFilter !== "all" && <li>Status: {statusFilter}</li>}
                {disciplineFilter !== "all" && <li>Discipline: {disciplineFilter}</li>}
                {ownerFilter !== "all" && <li>Owner: {ownerFilter}</li>}
                {activeMetric && <li>Metric: {activeMetric}</li>}
                {!search && statusFilter === "all" && disciplineFilter === "all" && ownerFilter === "all" && !activeMetric && (
                  <li className="text-amber-600">No filters applied - consider adding some filters first</li>
                )}
              </ul>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setSaveViewDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveView}>
              Save View
            </Button>
          </div>
        </DialogContent>
      </Dialog>

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
                {search || statusFilter !== "all" || activeMetric
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
                    <TableHead className={cn("w-[90px]", ds.typography.captionBold)}>
                      Code
                    </TableHead>
                    <TableHead className={cn("min-w-[150px]", ds.typography.captionBold)}>
                      Project
                    </TableHead>
                    <TableHead
                      className={cn("text-right w-[80px] cursor-pointer hover:bg-slate-50 select-none", ds.typography.captionBold)}
                      onClick={() => handleSort("value")}
                    >
                      <span className="flex items-center justify-end">
                        Value {getSortIcon("value")}
                      </span>
                    </TableHead>
                    <TableHead
                      className={cn("w-[110px] cursor-pointer hover:bg-slate-50 select-none", ds.typography.captionBold)}
                      onClick={() => handleSort("status")}
                    >
                      <span className="flex items-center">
                        Status {getSortIcon("status")}
                      </span>
                    </TableHead>
                    <TableHead className={cn("text-center w-[45px]", ds.typography.captionBold)}>
                      Ball
                    </TableHead>
                    <TableHead className={cn("text-center w-[40px]", ds.typography.captionBold)} title="Owner">
                      <User className="h-3.5 w-3.5 mx-auto" />
                    </TableHead>
                    <TableHead
                      className={cn("text-center w-[55px] cursor-pointer hover:bg-slate-50 select-none", ds.typography.captionBold)}
                      onClick={() => handleSort("days")}
                      title="Days in current status"
                    >
                      <span className="flex items-center justify-center">
                        Days {getSortIcon("days")}
                      </span>
                    </TableHead>
                    <TableHead className={cn("text-center w-[90px]", ds.typography.captionBold)} title="Health / Win% / Sentiment">
                      Score
                    </TableHead>
                    <TableHead className={cn("min-w-[140px]", ds.typography.captionBold)}>
                      Action Needed
                    </TableHead>
                    <TableHead className={cn("w-[70px] text-center", ds.typography.captionBold)}>

                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredProposals.map((proposal) => {
                    const activityColor = getActivityColor(proposal.days_in_current_status);
                    const today = new Date();
                    today.setHours(0, 0, 0, 0);
                    const isOverdue = proposal.action_due && new Date(proposal.action_due) < today &&
                      !["Contract Signed", "Lost", "Declined", "Dormant"].includes(proposal.current_status);
                    const isOurMove = proposal.ball_in_court === 'us' &&
                      !["Contract Signed", "Lost", "Declined", "Dormant"].includes(proposal.current_status);
                    return (
                      <TableRow
                        key={proposal.id}
                        className={cn(
                          "cursor-pointer",
                          ds.hover.subtle,
                          isOverdue && "bg-red-50/50",
                          !isOverdue && isOurMove && "bg-amber-50/30"
                        )}
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
                        <TableCell className={cn("font-mono text-xs", ds.textColors.primary)}>
                          {proposal.project_code}
                        </TableCell>
                        <TableCell className={cn("max-w-[200px]", ds.typography.body, ds.textColors.primary)}>
                          <span className="block truncate text-sm" title={proposal.project_name}>
                            {proposal.project_name}
                          </span>
                        </TableCell>
                        <TableCell className={cn("text-right whitespace-nowrap text-sm", ds.textColors.primary)}>
                          {formatCurrency(proposal.project_value)}
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
                          {/* Owner Avatar */}
                          {proposal.action_owner ? (
                            <div
                              className={cn(
                                "inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-semibold",
                                proposal.action_owner === 'bill' && "bg-blue-100 text-blue-700",
                                proposal.action_owner === 'brian' && "bg-purple-100 text-purple-700",
                                proposal.action_owner === 'lukas' && "bg-green-100 text-green-700",
                                proposal.action_owner === 'mink' && "bg-amber-100 text-amber-700",
                              )}
                              title={proposal.action_owner.charAt(0).toUpperCase() + proposal.action_owner.slice(1)}
                            >
                              {proposal.action_owner === 'brian' ? 'Br' : proposal.action_owner.charAt(0).toUpperCase()}
                            </div>
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
                          {/* Combined Score: Health / Win% / Sentiment */}
                          <div className="flex items-center justify-center gap-1">
                            {proposal.health_score != null && (
                              <div
                                className={cn(
                                  "inline-flex items-center justify-center w-6 h-6 rounded text-[10px] font-bold",
                                  proposal.health_score >= 70 ? "bg-emerald-100 text-emerald-700" :
                                  proposal.health_score >= 50 ? "bg-amber-100 text-amber-700" :
                                  "bg-red-100 text-red-700"
                                )}
                                title={`Health: ${proposal.health_score}`}
                              >
                                {proposal.health_score}
                              </div>
                            )}
                            {proposal.win_probability != null && (
                              <span
                                className={cn(
                                  "text-[10px] font-semibold",
                                  proposal.win_probability >= 60 ? "text-emerald-600" :
                                  proposal.win_probability >= 30 ? "text-amber-600" :
                                  "text-slate-400"
                                )}
                                title={`Win: ${proposal.win_probability}%`}
                              >
                                {proposal.win_probability}%
                              </span>
                            )}
                            {proposal.last_sentiment && (
                              <div
                                className={cn(
                                  "inline-flex items-center justify-center w-4 h-4 rounded-full text-[8px] font-bold",
                                  proposal.last_sentiment === 'positive' && "bg-emerald-100 text-emerald-700",
                                  proposal.last_sentiment === 'concerned' && "bg-amber-100 text-amber-700",
                                  proposal.last_sentiment === 'negative' && "bg-red-100 text-red-700",
                                  proposal.last_sentiment === 'neutral' && "bg-slate-100 text-slate-600"
                                )}
                                title={proposal.last_sentiment}
                              >
                                {proposal.last_sentiment === 'positive' ? '+' :
                                 proposal.last_sentiment === 'concerned' ? '!' :
                                 proposal.last_sentiment === 'negative' ? '-' : '~'}
                              </div>
                            )}
                            {!proposal.health_score && !proposal.win_probability && !proposal.last_sentiment && (
                              <span className="text-slate-400">—</span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className={cn("max-w-[300px]", ds.typography.caption)}>
                          {proposal.action_needed ? (
                            <div className="flex flex-col gap-0.5">
                              <span
                                className={cn(
                                  "block truncate",
                                  proposal.action_due && new Date(proposal.action_due) < new Date()
                                    ? "text-red-700 font-medium"
                                    : proposal.health_score && proposal.health_score < 50
                                      ? "text-amber-700"
                                      : ds.textColors.secondary
                                )}
                                title={proposal.action_needed}
                              >
                                {proposal.action_needed}
                              </span>
                              {proposal.action_due && (
                                <span
                                  className={cn(
                                    "text-[10px]",
                                    new Date(proposal.action_due) < new Date()
                                      ? "text-red-600 font-semibold"
                                      : "text-slate-400"
                                  )}
                                >
                                  {new Date(proposal.action_due) < new Date() ? "OVERDUE: " : "Due: "}
                                  {new Date(proposal.action_due).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                </span>
                              )}
                            </div>
                          ) : proposal.current_remark ? (
                            <span className={cn("block truncate", ds.textColors.tertiary)} title={proposal.current_remark}>
                              {proposal.current_remark}
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center" onClick={(e) => e.stopPropagation()}>
                          <div className="flex items-center justify-center gap-0.5">
                            {/* Primary: Edit */}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setSelectedProposal(proposal);
                                setEditDialogOpen(true);
                              }}
                              className="h-7 w-7 p-0"
                              title="Edit"
                            >
                              <Pencil className="h-3.5 w-3.5" />
                            </Button>
                            {/* Primary: Email (when needed) */}
                            {(proposal.ball_in_court === 'us' || proposal.days_in_current_status > 7) && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  draftFollowUpMutation.mutate({
                                    proposalId: proposal.id,
                                    projectName: proposal.project_name,
                                  });
                                }}
                                disabled={draftFollowUpMutation.isPending}
                                className="h-7 w-7 p-0 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                title="Draft email"
                              >
                                {draftFollowUpMutation.isPending ? (
                                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                ) : (
                                  <Mail className="h-3.5 w-3.5" />
                                )}
                              </Button>
                            )}
                            {/* More actions dropdown */}
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                                  <MoreHorizontal className="h-3.5 w-3.5" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-40">
                                <DropdownMenuItem
                                  onClick={() => flipBallMutation.mutate({
                                    projectCode: proposal.project_code,
                                    currentBall: proposal.ball_in_court || 'them',
                                  })}
                                >
                                  <ArrowLeftRight className="h-4 w-4 mr-2" />
                                  Flip Ball
                                </DropdownMenuItem>
                                {proposal.ball_in_court === 'us' && (
                                  <DropdownMenuItem
                                    onClick={() => markFollowedUpMutation.mutate({
                                      projectCode: proposal.project_code,
                                    })}
                                  >
                                    <CheckCheck className="h-4 w-4 mr-2" />
                                    Mark Followed Up
                                  </DropdownMenuItem>
                                )}
                                {!["Contract Signed", "Lost", "Declined", "Dormant"].includes(proposal.current_status) && (
                                  <>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem
                                      onClick={() => {
                                        setQuickActionProposal(proposal);
                                        setMarkWonDialogOpen(true);
                                      }}
                                      className="text-emerald-600"
                                    >
                                      <Trophy className="h-4 w-4 mr-2" />
                                      Mark Won
                                    </DropdownMenuItem>
                                    <DropdownMenuItem
                                      onClick={() => {
                                        setQuickActionProposal(proposal);
                                        setMarkLostDialogOpen(true);
                                      }}
                                      className="text-red-600"
                                    >
                                      <Ban className="h-4 w-4 mr-2" />
                                      Mark Lost
                                    </DropdownMenuItem>
                                    <DropdownMenuItem
                                      onClick={() => {
                                        setQuickActionProposal(proposal);
                                        setCreateFollowUpDialogOpen(true);
                                      }}
                                      className="text-blue-600"
                                    >
                                      <CalendarPlus className="h-4 w-4 mr-2" />
                                      Create Follow-up
                                    </DropdownMenuItem>
                                  </>
                                )}
                              </DropdownMenuContent>
                            </DropdownMenu>
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

      {/* Quick Action Dialogs */}
      <MarkWonDialog
        proposal={quickActionProposal}
        open={markWonDialogOpen}
        onOpenChange={setMarkWonDialogOpen}
      />
      <MarkLostDialog
        proposal={quickActionProposal}
        open={markLostDialogOpen}
        onOpenChange={setMarkLostDialogOpen}
      />
      <CreateFollowUpDialog
        proposal={quickActionProposal}
        open={createFollowUpDialogOpen}
        onOpenChange={setCreateFollowUpDialogOpen}
      />
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
