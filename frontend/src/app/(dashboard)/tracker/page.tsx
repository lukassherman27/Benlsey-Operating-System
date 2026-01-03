"use client";

import { useState, useMemo, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ProposalTrackerItem, DisciplineFilter } from "@/lib/types";
import { ProposalQuickEditDialog } from "@/components/proposal-quick-edit-dialog";
import { PriorityBanner } from "@/components/proposals/priority-banner";
import {
  MarkWonDialog,
  MarkLostDialog,
  CreateFollowUpDialog,
} from "@/components/proposals/quick-action-dialogs";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { FileText, Loader2, Download, Mail, Copy, X } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { type ProposalStatus } from "@/lib/constants";
import { exportToCSV, prepareDataForExport } from "@/lib/export-utils";

// Import extracted components
import {
  ProposalStatsCards,
  ProposalPipelineFunnel,
  ProposalFilters,
  ProposalTable,
} from "./components";

// Saved filter views
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

function loadSavedViews(): SavedFilterView[] {
  if (typeof window === "undefined") return [];
  try {
    const saved = localStorage.getItem(SAVED_VIEWS_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

function persistSavedViews(views: SavedFilterView[]) {
  if (typeof window === "undefined") return;
  localStorage.setItem(SAVED_VIEWS_KEY, JSON.stringify(views));
}

function ProposalTrackerContent() {
  const searchParams = useSearchParams();
  const codeParam = searchParams.get("code");
  const highlightParam = searchParams.get("highlight");
  const filterParam = searchParams.get("filter");

  // Filter state
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ProposalStatus | "all">("all");
  const [disciplineFilter, setDisciplineFilter] = useState<DisciplineFilter>("all");
  const [ownerFilter, setOwnerFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [activeMetric, setActiveMetric] = useState<string | null>(null);

  // Sort state
  const [sortField, setSortField] = useState<"value" | "date" | "status" | "days" | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

  // Dialog state
  const [selectedProposal, setSelectedProposal] = useState<ProposalTrackerItem | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [markWonDialogOpen, setMarkWonDialogOpen] = useState(false);
  const [markLostDialogOpen, setMarkLostDialogOpen] = useState(false);
  const [createFollowUpDialogOpen, setCreateFollowUpDialogOpen] = useState(false);
  const [quickActionProposal, setQuickActionProposal] = useState<ProposalTrackerItem | null>(null);

  // Follow-up email dialog
  const [followUpDialogOpen, setFollowUpDialogOpen] = useState(false);
  const [followUpEmail, setFollowUpEmail] = useState<{
    subject: string;
    body: string;
    projectName: string;
  } | null>(null);

  // Saved views
  const [savedViews, setSavedViews] = useState<SavedFilterView[]>([]);
  const [saveViewDialogOpen, setSaveViewDialogOpen] = useState(false);
  const [newViewName, setNewViewName] = useState("");

  // Load saved views on mount
  useEffect(() => {
    setSavedViews(loadSavedViews());
  }, []);

  // Handle URL params
  useEffect(() => {
    if (codeParam) {
      setSearch(codeParam);
    }
    if (filterParam === "needs-followup") {
      setActiveMetric("followup");
    }
  }, [codeParam, highlightParam, filterParam]);

  // Data fetching
  const { data: statsData } = useQuery({
    queryKey: ["proposalTrackerStats"],
    queryFn: () => api.getProposalTrackerStats(),
  });

  const { data: disciplineData } = useQuery({
    queryKey: ["proposalTrackerDisciplines"],
    queryFn: () => api.getProposalTrackerDisciplines(),
  });

  const { data: proposalsData, isLoading, isError, error } = useQuery({
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
  const ownerStats = stats?.action_by_owner || null;
  const proposals = useMemo(() => proposalsData?.proposals || [], [proposalsData]);

  // Reset owner filter if no owner data available
  useEffect(() => {
    if (ownerFilter !== "all" && (!ownerStats || Object.keys(ownerStats).length === 0)) {
      setOwnerFilter("all");
    }
  }, [ownerFilter, ownerStats]);

  // Filter and sort proposals
  const filteredProposals = useMemo(() => {
    let result = proposals;
    const hasActionDue = result.some((p) => !!p.action_due);
    const hasActionOwners = result.some((p) => !!p.action_owner);
    const ballValues = new Set(
      result
        .map((p) => p.ball_in_court)
        .filter((value): value is string => !!value)
    );
    const hasBallSignal = ballValues.size > 1;
    const ballReliable = hasBallSignal || hasActionOwners;

    // Owner filter
    if (ownerFilter !== "all") {
      result = result.filter((p) => p.action_owner === ownerFilter);
    }

    // Follow-up filter
    if (activeMetric === "followup") {
      result = result.filter(
        (p) =>
          (p.days_in_current_status || 0) > 14 &&
          p.current_status !== "On Hold" &&
          p.current_status !== "Contract Signed"
      );
    }

    // Overdue filter
    if (activeMetric === "overdue") {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      result = result.filter((p) => {
        if (!p.action_due) return false;
        return new Date(p.action_due) < today;
      });
    }

    // Needs Attention filter (overdue OR ball with us)
    if (activeMetric === "attention") {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const terminalStatuses = ["Contract Signed", "Lost", "Declined", "Dormant"];
      result = result.filter((p) => {
        if (terminalStatuses.includes(p.current_status)) return false;
        const isOverdue = hasActionDue && p.action_due && new Date(p.action_due) < today;
        const isBallWithUs = ballReliable && p.ball_in_court === "us";
        const isStale = !hasActionDue && !ballReliable && (p.days_in_current_status || 0) > 14;
        return isOverdue || isBallWithUs || isStale;
      });
    }

    // Sorting
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

  // Mutations
  const generatePdfMutation = useMutation({
    mutationFn: () => api.generateProposalPdf(),
    onSuccess: (data) => {
      if (data.success) toast.success("PDF generated successfully");
      else toast.error(data.message || "Failed to generate PDF");
    },
    onError: (err: unknown) => {
      toast.error(err instanceof Error ? err.message : "Failed to generate PDF");
    },
  });

  const draftFollowUpMutation = useMutation({
    mutationFn: ({ proposalId, projectName }: { proposalId: number; projectName: string }) =>
      api.draftFollowUpEmail(proposalId, "professional").then((data) => ({ ...data, projectName })),
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
    onError: (err: unknown) => {
      toast.error(err instanceof Error ? err.message : "Failed to draft follow-up");
    },
  });

  // Handlers
  const handleMetricClick = (metric: string, status?: string) => {
    if (activeMetric === metric) {
      setActiveMetric(null);
      setStatusFilter("all");
      setPage(1);
      return;
    }
    setActiveMetric(metric);
    setPage(1);
    if (status) {
      setStatusFilter(status as ProposalStatus);
    } else {
      setStatusFilter("all");
    }
  };

  const handleSort = (field: "value" | "date" | "status" | "days") => {
    if (sortField === field) {
      if (sortDirection === "desc") setSortDirection("asc");
      else setSortField(null);
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  const handleExportCSV = () => {
    if (!proposals?.length) {
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
    } catch {
      toast.error("Failed to export data");
    }
  };

  const handleSaveView = () => {
    if (!newViewName.trim()) {
      toast.error("Please enter a name for the view");
      return;
    }
    const newView: SavedFilterView = {
      id: Date.now().toString(),
      name: newViewName.trim(),
      filters: { search, statusFilter, disciplineFilter, ownerFilter, activeMetric },
      createdAt: new Date().toISOString(),
    };
    const updatedViews = [...savedViews, newView];
    setSavedViews(updatedViews);
    persistSavedViews(updatedViews);
    setNewViewName("");
    setSaveViewDialogOpen(false);
    toast.success(`Saved view "${newViewName}"`);
  };

  const handleApplyView = (view: SavedFilterView) => {
    setSearch(view.filters.search);
    setStatusFilter(view.filters.statusFilter as ProposalStatus | "all");
    setDisciplineFilter(view.filters.disciplineFilter as DisciplineFilter);
    setOwnerFilter(view.filters.ownerFilter);
    setActiveMetric(view.filters.activeMetric);
    setPage(1);
    toast.success(`Applied "${view.name}"`);
  };

  const handleDeleteView = (viewId: string) => {
    const updatedViews = savedViews.filter((v) => v.id !== viewId);
    setSavedViews(updatedViews);
    persistSavedViews(updatedViews);
    toast.success("View deleted");
  };

  const handleClearFilters = () => {
    setSearch("");
    setStatusFilter("all");
    setOwnerFilter("all");
    setDisciplineFilter("all");
    setActiveMetric(null);
    setPage(1);
  };

  const handleCopyEmail = () => {
    if (followUpEmail) {
      navigator.clipboard.writeText(`Subject: ${followUpEmail.subject}\n\n${followUpEmail.body}`);
      toast.success("Email copied to clipboard");
    }
  };

  return (
    <div className={cn(ds.gap.loose, "space-y-6 w-full max-w-full overflow-x-hidden")}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>Proposal Pipeline</h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Track proposals from first contact to contract signed
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            className={cn(ds.gap.tight, ds.borderRadius.button)}
            onClick={handleExportCSV}
            disabled={!proposals?.length}
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

      {/* Priority Banner */}
      {proposals.length > 0 && (
        <PriorityBanner
          proposals={proposals}
          onFilterFollowup={() => setActiveMetric("followup")}
          onFilterMyMove={() => setOwnerFilter("bill")}
        />
      )}

      {/* Stats Cards */}
      <ProposalStatsCards stats={stats} activeMetric={activeMetric} onMetricClick={handleMetricClick} />

      {/* Pipeline Funnel */}
      <ProposalPipelineFunnel
        stats={stats}
        statusFilter={statusFilter}
        onStatusClick={(status) => {
          setStatusFilter(status);
          setPage(1);
        }}
      />

      {/* Filters */}
      <ProposalFilters
        search={search}
        onSearchChange={(v) => { setSearch(v); setPage(1); }}
        statusFilter={statusFilter}
        onStatusFilterChange={(v) => { setStatusFilter(v); setPage(1); }}
        ownerFilter={ownerFilter}
        onOwnerFilterChange={(v) => { setOwnerFilter(v); setPage(1); }}
        ownerStats={ownerStats}
        disciplineFilter={disciplineFilter}
        onDisciplineFilterChange={(v) => { setDisciplineFilter(v); setPage(1); }}
        disciplineData={disciplineData}
        activeMetric={activeMetric}
        savedViews={savedViews}
        onApplyView={handleApplyView}
        onDeleteView={handleDeleteView}
        onSaveViewClick={() => setSaveViewDialogOpen(true)}
        onClearFilters={handleClearFilters}
      />

      {/* Table */}
      <ProposalTable
        proposals={filteredProposals}
        isLoading={isLoading}
        isError={isError}
        error={error as Error | null}
        activeMetric={activeMetric}
        onEditProposal={(p) => { setSelectedProposal(p); setEditDialogOpen(true); }}
        onMarkWon={(p) => { setQuickActionProposal(p); setMarkWonDialogOpen(true); }}
        onMarkLost={(p) => { setQuickActionProposal(p); setMarkLostDialogOpen(true); }}
        onCreateFollowUp={(p) => { setQuickActionProposal(p); setCreateFollowUpDialogOpen(true); }}
        onDraftEmail={(id, name) => draftFollowUpMutation.mutate({ proposalId: id, projectName: name })}
        isDraftingEmail={draftFollowUpMutation.isPending}
        sortField={sortField}
        sortDirection={sortDirection}
        onSort={handleSort}
        page={page}
        totalPages={proposalsData?.total_pages || 1}
        total={proposalsData?.total || 0}
        onPageChange={setPage}
        onClearMetricFilter={() => { setActiveMetric(null); setStatusFilter("all"); }}
      />

      {/* Dialogs */}
      <ProposalQuickEditDialog
        proposal={selectedProposal}
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
      />

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

      {/* Save View Dialog */}
      <Dialog open={saveViewDialogOpen} onOpenChange={setSaveViewDialogOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>Save Filter View</DialogTitle>
            <DialogDescription>Save your current filters as a reusable view.</DialogDescription>
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
                onKeyDown={(e) => { if (e.key === "Enter") handleSaveView(); }}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setSaveViewDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSaveView}>Save View</Button>
          </div>
        </DialogContent>
      </Dialog>

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
                <div className="mt-1 p-3 bg-slate-50 rounded-md border text-sm">{followUpEmail.subject}</div>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Body</label>
                <div className="mt-1 p-3 bg-slate-50 rounded-md border text-sm whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                  {followUpEmail.body}
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => setFollowUpDialogOpen(false)}>
                  <X className="h-4 w-4 mr-2" />
                  Close
                </Button>
                <Button onClick={handleCopyEmail} className="bg-blue-600 hover:bg-blue-700">
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

export default function ProposalTrackerPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Loading tracker...</div>}>
      <ProposalTrackerContent />
    </Suspense>
  );
}
