"use client";

import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import {
  FileText,
  Loader2,
  Pencil,
  Clock,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Mail,
  User,
  CheckCheck,
  ArrowLeftRight,
  Trophy,
  Ban,
  MoreHorizontal,
  CalendarPlus,
  AlertCircle,
} from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import {
  ds,
  bensleyVoice,
  proposalStatusColors,
  ALL_PROPOSAL_STATUSES,
  getActivityColor,
} from "@/lib/design-system";
import { type ProposalStatus } from "@/lib/constants";
import { ProposalTrackerItem } from "@/lib/types";
import { api } from "@/lib/api";

type SortField = "value" | "date" | "status" | "days";
type SortDirection = "asc" | "desc";

interface ProposalTableProps {
  proposals: ProposalTrackerItem[];
  isLoading: boolean;
  isError?: boolean;
  error?: Error | null;
  activeMetric: string | null;
  onEditProposal: (proposal: ProposalTrackerItem) => void;
  onMarkWon: (proposal: ProposalTrackerItem) => void;
  onMarkLost: (proposal: ProposalTrackerItem) => void;
  onCreateFollowUp: (proposal: ProposalTrackerItem) => void;
  onDraftEmail: (proposalId: number, projectName: string) => void;
  isDraftingEmail: boolean;
  sortField: SortField | null;
  sortDirection: SortDirection;
  onSort: (field: SortField) => void;
  // Pagination
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
  onClearMetricFilter: () => void;
}

export function ProposalTable({
  proposals,
  isLoading,
  isError,
  error,
  activeMetric,
  onEditProposal,
  onMarkWon,
  onMarkLost,
  onCreateFollowUp,
  onDraftEmail,
  isDraftingEmail,
  sortField,
  sortDirection,
  onSort,
  page,
  totalPages,
  total,
  onPageChange,
  onClearMetricFilter,
}: ProposalTableProps) {
  const router = useRouter();
  const queryClient = useQueryClient();

  // Quick status update mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ projectCode, newStatus }: { projectCode: string; newStatus: string }) =>
      api.updateProposalTracker(projectCode, { current_status: newStatus as ProposalStatus }),
    onSuccess: (_, variables) => {
      toast.success(`Status updated to ${variables.newStatus}`);
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerList"] });
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerStats"] });
    },
    onError: (err: unknown) => {
      toast.error(err instanceof Error ? err.message : "Failed to update status");
    },
  });

  // Flip ball mutation
  const flipBallMutation = useMutation({
    mutationFn: ({ projectCode, currentBall }: { projectCode: string; currentBall: string }) =>
      api.updateProposalTracker(projectCode, {
        ball_in_court: currentBall === "us" ? "them" : "us",
      }),
    onSuccess: (_, variables) => {
      const newBall = variables.currentBall === "us" ? "client" : "us";
      toast.success(`Ball now with ${newBall}`);
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerList"] });
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerStats"] });
    },
    onError: (err: unknown) => {
      toast.error(err instanceof Error ? err.message : "Failed to update");
    },
  });

  // Mark followed up mutation
  const markFollowedUpMutation = useMutation({
    mutationFn: ({ projectCode }: { projectCode: string }) =>
      api.updateProposalTracker(projectCode, { ball_in_court: "them" }),
    onSuccess: () => {
      toast.success("Marked as followed up - ball now with client");
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerList"] });
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerStats"] });
    },
    onError: (err: unknown) => {
      toast.error(err instanceof Error ? err.message : "Failed to update");
    },
  });

  // Clear action mutation (mark done)
  const clearActionMutation = useMutation({
    mutationFn: ({ projectCode }: { projectCode: string }) =>
      api.updateProposalTracker(projectCode, {
        action_needed: null,
        action_due: null,
      }),
    onSuccess: () => {
      toast.success("Action marked as done");
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerList"] });
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerStats"] });
    },
    onError: (err: unknown) => {
      toast.error(err instanceof Error ? err.message : "Failed to clear action");
    },
  });

  // Get sort icon
  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-3 w-3 ml-1 opacity-50" />;
    }
    return sortDirection === "desc" ? (
      <ArrowDown className="h-3 w-3 ml-1" />
    ) : (
      <ArrowUp className="h-3 w-3 ml-1" />
    );
  };

  // Error state
  if (isError) {
    return (
      <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50")}>
        <CardContent className="py-12 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
          <p className="text-lg font-medium text-red-700 mb-2">
            Failed to load proposals
          </p>
          <p className="text-sm text-red-600 mb-4">
            {error?.message || "Something went wrong. Please try again."}
          </p>
          <Button
            variant="outline"
            onClick={() => queryClient.invalidateQueries({ queryKey: ["proposalTrackerList"] })}
            className="border-red-300 text-red-700 hover:bg-red-100"
          >
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
        <CardContent className={ds.spacing.spacious}>
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
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (proposals.length === 0) {
    return (
      <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
        <CardContent className={ds.spacing.spacious}>
          <div className="py-16 text-center">
            <FileText className="mx-auto h-16 w-16 text-slate-300 mb-4" aria-hidden="true" />
            <p className={cn(ds.typography.cardHeader, ds.textColors.primary, "mb-2")}>
              {bensleyVoice.emptyStates.proposals}
            </p>
            <p className={cn(ds.typography.body, ds.textColors.tertiary, "mt-2")}>
              {activeMetric
                ? bensleyVoice.emptyStates.search
                : "Proposals will appear here once created"}
            </p>
            {activeMetric && (
              <Button variant="outline" className="mt-4" onClick={onClearMetricFilter}>
                Clear metric filter
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
      <CardContent className={ds.spacing.spacious}>
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
                  className={cn(
                    "text-right w-[80px] cursor-pointer hover:bg-slate-50 select-none",
                    ds.typography.captionBold
                  )}
                  onClick={() => onSort("value")}
                >
                  <span className="flex items-center justify-end">
                    Value {getSortIcon("value")}
                  </span>
                </TableHead>
                <TableHead
                  className={cn(
                    "w-[110px] cursor-pointer hover:bg-slate-50 select-none",
                    ds.typography.captionBold
                  )}
                  onClick={() => onSort("status")}
                >
                  <span className="flex items-center">
                    Status {getSortIcon("status")}
                  </span>
                </TableHead>
                <TableHead className={cn("text-center w-[45px]", ds.typography.captionBold)}>
                  Ball
                </TableHead>
                <TableHead
                  className={cn("text-center w-[40px]", ds.typography.captionBold)}
                  title="Owner"
                >
                  <User className="h-3.5 w-3.5 mx-auto" />
                </TableHead>
                <TableHead
                  className={cn(
                    "text-center w-[55px] cursor-pointer hover:bg-slate-50 select-none",
                    ds.typography.captionBold
                  )}
                  onClick={() => onSort("days")}
                  title="Days in current status"
                >
                  <span className="flex items-center justify-center">
                    Days {getSortIcon("days")}
                  </span>
                </TableHead>
                <TableHead
                  className={cn("text-center w-[90px]", ds.typography.captionBold)}
                  title="Health / Win% / Sentiment"
                >
                  Score
                </TableHead>
                <TableHead className={cn("min-w-[140px]", ds.typography.captionBold)}>
                  Action Needed
                </TableHead>
                <TableHead className={cn("w-[70px] text-center", ds.typography.captionBold)} />
              </TableRow>
            </TableHeader>
            <TableBody>
              {proposals.map((proposal) => {
                const activityColor = getActivityColor(proposal.days_in_current_status);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                const isOverdue =
                  proposal.action_due &&
                  new Date(proposal.action_due) < today &&
                  !["Contract Signed", "Lost", "Declined", "Dormant"].includes(proposal.current_status);
                const isOurMove =
                  proposal.ball_in_court === "us" &&
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
                    onClick={() => router.push(`/proposals/${encodeURIComponent(proposal.project_code)}`)}
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
                            proposalStatusColors[proposal.current_status]?.bg || "bg-slate-50",
                            proposalStatusColors[proposal.current_status]?.text || "text-slate-600"
                          )}
                        >
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {ALL_PROPOSAL_STATUSES.map((status) => (
                            <SelectItem key={status} value={status} className="text-xs">
                              <span
                                className={cn(
                                  "px-1.5 py-0.5 rounded",
                                  proposalStatusColors[status]?.bg,
                                  proposalStatusColors[status]?.text
                                )}
                              >
                                {status}
                              </span>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell className="text-center" onClick={(e) => e.stopPropagation()}>
                      {proposal.ball_in_court === "us" ? (
                        <button
                          type="button"
                          onClick={() => flipBallMutation.mutate({
                            projectCode: proposal.project_code,
                            currentBall: "us",
                          })}
                          disabled={flipBallMutation.isPending}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700 hover:bg-red-200 transition-colors cursor-pointer"
                          title="Click to flip ball to client"
                        >
                          Us
                        </button>
                      ) : proposal.ball_in_court === "them" ? (
                        <button
                          type="button"
                          onClick={() => flipBallMutation.mutate({
                            projectCode: proposal.project_code,
                            currentBall: "them",
                          })}
                          disabled={flipBallMutation.isPending}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 hover:bg-green-200 transition-colors cursor-pointer"
                          title="Click to flip ball to us"
                        >
                          Them
                        </button>
                      ) : proposal.ball_in_court === "mutual" ? (
                        <button
                          type="button"
                          onClick={() => flipBallMutation.mutate({
                            projectCode: proposal.project_code,
                            currentBall: "mutual",
                          })}
                          disabled={flipBallMutation.isPending}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors cursor-pointer"
                          title="Click to flip ball"
                        >
                          Both
                        </button>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      {proposal.action_owner ? (
                        <div
                          className={cn(
                            "inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-semibold",
                            proposal.action_owner === "bill" && "bg-blue-100 text-blue-700",
                            proposal.action_owner === "brian" && "bg-purple-100 text-purple-700",
                            proposal.action_owner === "lukas" && "bg-green-100 text-green-700",
                            proposal.action_owner === "mink" && "bg-amber-100 text-amber-700"
                          )}
                          title={proposal.action_owner.charAt(0).toUpperCase() + proposal.action_owner.slice(1)}
                        >
                          {proposal.action_owner === "brian"
                            ? "Br"
                            : proposal.action_owner.charAt(0).toUpperCase()}
                        </div>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      <div
                        className={cn(
                          "inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium whitespace-nowrap",
                          activityColor.bg,
                          activityColor.text
                        )}
                      >
                        <Clock className="h-3 w-3" />
                        {proposal.days_in_current_status}d
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center gap-1">
                        {proposal.health_score != null && (
                          <div
                            className={cn(
                              "inline-flex items-center justify-center w-6 h-6 rounded text-[10px] font-bold",
                              proposal.health_score >= 70
                                ? "bg-emerald-100 text-emerald-700"
                                : proposal.health_score >= 50
                                  ? "bg-amber-100 text-amber-700"
                                  : "bg-red-100 text-red-700"
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
                              proposal.win_probability >= 60
                                ? "text-emerald-600"
                                : proposal.win_probability >= 30
                                  ? "text-amber-600"
                                  : "text-slate-400"
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
                              proposal.last_sentiment === "positive" && "bg-emerald-100 text-emerald-700",
                              proposal.last_sentiment === "concerned" && "bg-amber-100 text-amber-700",
                              proposal.last_sentiment === "negative" && "bg-red-100 text-red-700",
                              proposal.last_sentiment === "neutral" && "bg-slate-100 text-slate-600"
                            )}
                            title={proposal.last_sentiment}
                          >
                            {proposal.last_sentiment === "positive"
                              ? "+"
                              : proposal.last_sentiment === "concerned"
                                ? "!"
                                : proposal.last_sentiment === "negative"
                                  ? "-"
                                  : "~"}
                          </div>
                        )}
                        {!proposal.health_score && !proposal.win_probability && !proposal.last_sentiment && (
                          <span className="text-slate-400">—</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell
                      className={cn("max-w-[300px]", ds.typography.caption)}
                      onClick={(e) => e.stopPropagation()}
                    >
                      {proposal.action_needed ? (
                        <div className="flex items-start gap-1">
                          <button
                            type="button"
                            onClick={() => clearActionMutation.mutate({ projectCode: proposal.project_code })}
                            disabled={clearActionMutation.isPending}
                            className="flex-shrink-0 mt-0.5 w-4 h-4 rounded border border-slate-300 hover:bg-emerald-100 hover:border-emerald-400 transition-colors flex items-center justify-center group"
                            title="Mark action as done"
                          >
                            <CheckCheck className="h-2.5 w-2.5 text-slate-400 group-hover:text-emerald-600" />
                          </button>
                          <div className="flex flex-col gap-0.5 min-w-0">
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
                                {new Date(proposal.action_due).toLocaleDateString("en-US", {
                                  month: "short",
                                  day: "numeric",
                                })}
                              </span>
                            )}
                          </div>
                        </div>
                      ) : proposal.current_remark ? (
                        <span
                          className={cn("block truncate", ds.textColors.tertiary)}
                          title={proposal.current_remark}
                        >
                          {proposal.current_remark}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-center gap-0.5">
                        {/* Edit button */}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onEditProposal(proposal)}
                          className="h-7 w-7 p-0"
                          title="Edit"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>

                        {/* Email button (when needed) */}
                        {(proposal.ball_in_court === "us" || proposal.days_in_current_status > 7) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onDraftEmail(proposal.id, proposal.project_name)}
                            disabled={isDraftingEmail}
                            className="h-7 w-7 p-0 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                            title="Draft email"
                          >
                            {isDraftingEmail ? (
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
                              onClick={() =>
                                flipBallMutation.mutate({
                                  projectCode: proposal.project_code,
                                  currentBall: proposal.ball_in_court || "them",
                                })
                              }
                            >
                              <ArrowLeftRight className="h-4 w-4 mr-2" />
                              Flip Ball
                            </DropdownMenuItem>
                            {proposal.ball_in_court === "us" && (
                              <DropdownMenuItem
                                onClick={() =>
                                  markFollowedUpMutation.mutate({
                                    projectCode: proposal.project_code,
                                  })
                                }
                              >
                                <CheckCheck className="h-4 w-4 mr-2" />
                                Mark Followed Up
                              </DropdownMenuItem>
                            )}
                            {!["Contract Signed", "Lost", "Declined", "Dormant"].includes(
                              proposal.current_status
                            ) && (
                              <>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  onClick={() => onMarkWon(proposal)}
                                  className="text-emerald-600"
                                >
                                  <Trophy className="h-4 w-4 mr-2" />
                                  Mark Won
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={() => onMarkLost(proposal)}
                                  className="text-red-600"
                                >
                                  <Ban className="h-4 w-4 mr-2" />
                                  Mark Lost
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={() => onCreateFollowUp(proposal)}
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

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <div className={cn(ds.typography.caption, ds.textColors.tertiary)}>
              Showing {(page - 1) * 50 + 1} to {Math.min(page * 50, total)} of {total} proposals
            </div>
            <div className={cn(ds.gap.tight, "flex")}>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(page - 1)}
                disabled={page === 1}
                className={ds.borderRadius.button}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(page + 1)}
                disabled={page === totalPages}
                className={ds.borderRadius.button}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
