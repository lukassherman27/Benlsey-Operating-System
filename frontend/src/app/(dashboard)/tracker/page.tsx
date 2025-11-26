"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ProposalTrackerItem } from "@/lib/types";
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
import { Search, Filter, FileText, Loader2, Download, Pencil } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { formatCurrency, getStatusColor, cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { type ProposalStatus } from "@/lib/constants";
import { Skeleton } from "@/components/ui/skeleton";
import { exportToCSV, prepareDataForExport } from "@/lib/export-utils";

export default function ProposalTrackerPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ProposalStatus | "all">("all");
  const [countryFilter, setCountryFilter] = useState<string>("all");
  const [yearFilter, setYearFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [selectedProposal, setSelectedProposal] = useState<ProposalTrackerItem | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

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

  // Fetch proposals list
  const { data: proposalsData, isLoading } = useQuery({
    queryKey: ["proposalTrackerList", statusFilter, countryFilter, yearFilter, search, page],
    queryFn: () =>
      api.getProposalTrackerList({
        status: statusFilter !== "all" ? statusFilter : undefined,
        country: countryFilter !== "all" ? countryFilter : undefined,
        search: search || undefined,
        page,
        per_page: 50,
      }),
  });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const stats = statsData?.stats as any;
  const proposals = proposalsData?.proposals || [];
  const countries = countriesData?.countries || [];

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

  return (
    <div className={cn(ds.gap.loose, "space-y-6")}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            Proposal Tracker
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Track all active proposals and their status
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

      {/* Comprehensive Stats Cards - All Proposals */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className={cn(ds.borderRadius.card, "border-slate-200/70", ds.hover.card)}>
            <CardHeader className="pb-3">
              <CardTitle className={cn(ds.typography.captionBold, ds.textColors.secondary)}>
                Total Proposals
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={cn(ds.typography.heading2, ds.textColors.primary)}>
                {stats?.all_proposals_total || 87}
              </div>
              <p className={cn(ds.typography.tiny, ds.textColors.tertiary, "mt-1")}>
                All time
              </p>
            </CardContent>
          </Card>

          <Card className={cn(ds.borderRadius.card, "border-slate-200/70", ds.hover.card)}>
            <CardHeader className="pb-3">
              <CardTitle className={cn(ds.typography.captionBold, ds.textColors.secondary)}>
                Active Pipeline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={cn(ds.typography.heading2, ds.textColors.primary)}>
                {stats.active_proposals_count || stats.total_proposals}
              </div>
              <p className={cn(ds.typography.tiny, ds.textColors.tertiary, "mt-1")}>
                In progress
              </p>
            </CardContent>
          </Card>

          <Card className={cn(ds.borderRadius.card, "border-blue-200/70 bg-gradient-to-br from-blue-50 to-indigo-50", "hover:shadow-md transition-all duration-200")}>
            <CardHeader className="pb-3">
              <CardTitle className={cn(ds.typography.captionBold, "text-blue-700")}>
                Contracts Signed (2025)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={cn(ds.typography.heading2, "text-blue-900")}>
                {stats.signed_2025_count || 0}
              </div>
              <p className={cn(ds.typography.tiny, "text-blue-700 font-medium mt-1")}>
                {formatCurrency(stats.signed_2025_value || 0)}
              </p>
            </CardContent>
          </Card>

          <Card className={cn(ds.borderRadius.card, "border-slate-200/70", ds.hover.card)}>
            <CardHeader className="pb-3">
              <CardTitle className={cn(ds.typography.captionBold, ds.textColors.secondary)}>
                Total Sent (2025)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={cn(ds.typography.heading2, ds.textColors.primary)}>
                {stats.sent_2025_count || 0}
              </div>
              <p className={cn(ds.typography.tiny, ds.textColors.tertiary, "mt-1")}>
                {formatCurrency(stats.sent_2025_value || 0)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Active Tracking Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className={cn(ds.borderRadius.card, "border-slate-200/70", ds.hover.card)}>
            <CardHeader className="pb-3">
              <CardTitle className={cn(ds.typography.captionBold, ds.textColors.secondary)}>
                Actively Tracked
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={cn(ds.typography.heading2, ds.textColors.primary)}>
                {stats.total_proposals}
              </div>
              <p className={cn(ds.typography.tiny, ds.textColors.tertiary, "mt-1")}>
                Current focus
              </p>
            </CardContent>
          </Card>

          <Card className={cn(ds.borderRadius.card, "border-slate-200/70", ds.hover.card)}>
            <CardHeader className="pb-3">
              <CardTitle className={cn(ds.typography.captionBold, ds.textColors.secondary)}>
                Pipeline Value
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={cn(ds.typography.heading2, ds.textColors.primary)}>
                {formatCurrency(stats.total_pipeline_value)}
              </div>
              <p className={cn(ds.typography.tiny, ds.textColors.tertiary, "mt-1")}>
                Tracked proposals
              </p>
            </CardContent>
          </Card>

          <Card className={cn(ds.borderRadius.card, ds.status.warning.bg, "border", ds.status.warning.border, "hover:shadow-md transition-all duration-200")}>
            <CardHeader className="pb-3">
              <CardTitle className={cn(ds.typography.captionBold, ds.status.warning.text)}>
                Needs Follow-up
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={cn(ds.typography.heading2, ds.status.warning.text)}>
                {stats.needs_followup}
              </div>
              <p className={cn(ds.typography.tiny, ds.status.warning.text, "mt-1")}>
                {">"}14 days in status
              </p>
            </CardContent>
          </Card>

          <Card className={cn(ds.borderRadius.card, "border-slate-200/70", ds.hover.card)}>
            <CardHeader className="pb-3">
              <CardTitle className={cn(ds.typography.captionBold, ds.textColors.secondary)}>
                Avg Days in Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={cn(ds.typography.heading2, ds.textColors.primary)}>
                {Math.round(stats.avg_days_in_status)}
              </div>
              <p className={cn(ds.typography.tiny, ds.textColors.tertiary, "mt-1")}>
                All tracked
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Proposals Sent This Year - COMMENTED OUT (data not available in backend) */}
      {/* {stats && (
        <Card className={cn(ds.borderRadius.card, "border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50")}>
          <CardHeader className="pb-3">
            <CardTitle className={cn(ds.typography.heading3, "text-blue-900")}>
              Proposals Sent by Year
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white/80 rounded-lg p-4 border border-blue-200">
                <p className={cn(ds.typography.caption, "text-blue-700 font-semibold mb-2")}>
                  2025 (Current Year)
                </p>
                <div className="flex items-baseline gap-2">
                  <span className={cn(ds.typography.heading2, "text-blue-900")}>
                    {stats.proposals_sent_2025}
                  </span>
                  <span className={cn(ds.typography.body, ds.textColors.secondary)}>proposals</span>
                </div>
                <p className={cn(ds.typography.body, "text-blue-700 font-medium mt-1")}>
                  {formatCurrency(stats.proposals_sent_value_2025)}
                </p>
              </div>

              <div className="bg-white/80 rounded-lg p-4 border border-slate-200">
                <p className={cn(ds.typography.caption, ds.textColors.secondary, "font-semibold mb-2")}>
                  2024 (Last Year)
                </p>
                <div className="flex items-baseline gap-2">
                  <span className={cn(ds.typography.heading2, ds.textColors.primary)}>
                    {stats.proposals_sent_2024}
                  </span>
                  <span className={cn(ds.typography.body, ds.textColors.secondary)}>proposals</span>
                </div>
                <p className={cn(ds.typography.body, ds.textColors.primary, "font-medium mt-1")}>
                  {formatCurrency(stats.proposals_sent_value_2024)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )} */}

      {/* Status Breakdown - RESPONSIVE */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {stats.status_breakdown.map((status: Record<string, unknown>) => (
            <Card key={status.current_status as string} className={cn(ds.borderRadius.card, "border-slate-200/70", ds.hover.card, "cursor-pointer")}>
              <CardContent className={ds.spacing.normal}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                      {status.current_status as string}
                    </p>
                    <p className={cn(ds.typography.heading2, ds.textColors.primary, "mt-1")}>
                      {status.count as number}
                    </p>
                  </div>
                  <Badge
                    variant="outline"
                    className={cn(
                      ds.typography.tiny,
                      ds.borderRadius.badge,
                      getStatusColor(status.current_status as ProposalStatus)
                    )}
                  >
                    {formatCurrency(status.total_value as number)}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
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
              <SelectTrigger className={cn("w-[180px]", ds.borderRadius.input)} aria-label="Filter by year">
                <Filter className={cn("h-4 w-4 mr-2", ds.textColors.tertiary)} aria-hidden="true" />
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Years</SelectItem>
                <SelectItem value="2025">2025 Signed</SelectItem>
                <SelectItem value="2024">2024 Signed</SelectItem>
                <SelectItem value="2023">2023 Signed</SelectItem>
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
          ) : proposals.length === 0 ? (
            <div className="py-16 text-center">
              <FileText className="mx-auto h-16 w-16 text-slate-300 mb-4" aria-hidden="true" />
              <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
                No proposals found
              </p>
              <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                {search || statusFilter !== "all" || countryFilter !== "all" || yearFilter !== "all"
                  ? "Try adjusting your filters"
                  : "Proposals will appear here once created"}
              </p>
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
                    <TableHead className={cn("text-right", ds.typography.captionBold)}>
                      Days
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
                  {proposals.map((proposal) => (
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
                      <TableCell className="text-right">
                        <span
                          className={cn(
                            ds.typography.body,
                            proposal.days_in_current_status > 60
                              ? cn(ds.status.danger.text, ds.typography.bodyBold, "text-base")
                              : proposal.days_in_current_status > 30
                              ? cn(ds.status.warning.text, ds.typography.bodyBold)
                              : proposal.days_in_current_status > 14
                              ? ds.status.warning.text
                              : ds.textColors.primary
                          )}
                        >
                          {proposal.days_in_current_status}
                          {proposal.days_in_current_status > 60 && (
                            <span className="ml-1 text-xs">!</span>
                          )}
                        </span>
                      </TableCell>
                      <TableCell className={cn("max-w-[300px] truncate", ds.typography.caption, ds.textColors.tertiary)}>
                        {proposal.current_remark || "-"}
                      </TableCell>
                      <TableCell className="text-center">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation(); // Prevent row navigation
                            setSelectedProposal(proposal);
                            setEditDialogOpen(true);
                          }}
                          className="h-8 w-8 p-0"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
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
