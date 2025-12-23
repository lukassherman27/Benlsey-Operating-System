"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ValidationSuggestion } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { ds, bensleyVoice, getLoadingMessage } from "@/lib/design-system";
import { CheckCircle2, XCircle, Clock, AlertCircle, Sparkles, CheckCheck } from "lucide-react";
import { toast } from "sonner";

// Loading skeleton
function ValidationSkeleton() {
  return (
    <div className="space-y-4">
      <p className={cn(ds.typography.caption, ds.textColors.tertiary, "text-center mb-4")}>
        {getLoadingMessage()}
      </p>
      {[...Array(3)].map((_, i) => (
        <Card key={i} className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Skeleton className="h-6 w-24" />
                <Skeleton className="h-4 w-4" />
                <Skeleton className="h-6 w-32" />
              </div>
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-16 w-full" />
              <div className="flex items-center gap-4">
                <Skeleton className="h-2 w-24" />
                <Skeleton className="h-4 w-12" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Empty state
function EmptyState({ status }: { status: string }) {
  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
      <CardContent className="py-16 text-center">
        <Sparkles className="mx-auto h-12 w-12 text-slate-300 mb-4" />
        <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
          No {status} suggestions
        </p>
        <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
          {bensleyVoice.emptyStates.suggestions}
        </p>
      </CardContent>
    </Card>
  );
}

export default function ValidationPage() {
  const [statusFilter] = useState<string>("pending");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["validation-suggestions", statusFilter],
    queryFn: () => api.getValidationSuggestions(statusFilter),
  });

  const { suggestions = [], stats } = data || {};

  // Selection helpers
  const allSelected = useMemo(() => {
    const pendingItems = suggestions.filter((s: ValidationSuggestion) => s.status === "pending");
    return pendingItems.length > 0 && pendingItems.every((s: ValidationSuggestion) => selectedIds.has(s.suggestion_id));
  }, [suggestions, selectedIds]);

  const toggleSelectAll = () => {
    const pendingItems = suggestions.filter((s: ValidationSuggestion) => s.status === "pending");
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(pendingItems.map((s: ValidationSuggestion) => s.suggestion_id)));
    }
  };

  const toggleSelect = (id: number) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const approveMutation = useMutation({
    mutationFn: (id: number) =>
      api.approveSuggestion(id, {
        reviewed_by: "admin",
        review_notes: "Approved via UI",
      }),
    onSuccess: () => {
      toast.success(bensleyVoice.successMessages.suggestionApproved);
      queryClient.invalidateQueries({ queryKey: ["validation-suggestions"] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to approve: ${error.message}`);
    },
  });

  const denyMutation = useMutation({
    mutationFn: ({
      id,
      notes,
    }: {
      id: number;
      notes: string;
    }) =>
      api.denySuggestion(id, {
        reviewed_by: "admin",
        review_notes: notes,
      }),
    onSuccess: () => {
      toast.success("Suggestion rejected");
      queryClient.invalidateQueries({ queryKey: ["validation-suggestions"] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to reject: ${error.message}`);
    },
  });

  // Batch approve mutation
  const batchApproveMutation = useMutation({
    mutationFn: async (ids: number[]) => {
      const results = await Promise.allSettled(
        ids.map((id) =>
          api.approveSuggestion(id, {
            reviewed_by: "admin",
            review_notes: "Batch approved via UI",
          })
        )
      );
      const succeeded = results.filter((r) => r.status === "fulfilled").length;
      const failed = results.filter((r) => r.status === "rejected").length;
      return { succeeded, failed };
    },
    onSuccess: ({ succeeded, failed }) => {
      if (failed > 0) {
        toast.warning(`Approved ${succeeded}, failed ${failed}`);
      } else {
        toast.success(`Approved ${succeeded} suggestions. ${bensleyVoice.successMessages.suggestionApproved}`);
      }
      setSelectedIds(new Set());
      queryClient.invalidateQueries({ queryKey: ["validation-suggestions"] });
    },
    onError: (error: Error) => {
      toast.error(`Batch approve failed: ${error.message}`);
    },
  });

  // Get status badge
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "pending":
        return <Badge className={ds.badges.warning}>{status.toUpperCase()}</Badge>;
      case "applied":
        return <Badge className={ds.badges.success}>{status.toUpperCase()}</Badge>;
      case "approved":
        return <Badge className={ds.badges.info}>{status.toUpperCase()}</Badge>;
      case "denied":
        return <Badge className={ds.badges.danger}>{status.toUpperCase()}</Badge>;
      default:
        return <Badge className={ds.badges.default}>{status.toUpperCase()}</Badge>;
    }
  };

  return (
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            Data Validation Dashboard
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Review AI-generated data corrections. Trust but verify.
          </p>
        </div>
      </div>

      {/* Batch Action Bar */}
      {statusFilter === "pending" && suggestions.length > 0 && (
        <Card className={cn(ds.borderRadius.card, "border-slate-200 bg-slate-50/50")}>
          <CardContent className="py-3 px-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Checkbox
                  checked={allSelected}
                  onCheckedChange={toggleSelectAll}
                  aria-label="Select all pending suggestions"
                />
                <span className={cn(ds.typography.body, ds.textColors.secondary)}>
                  {selectedIds.size > 0
                    ? `${selectedIds.size} selected`
                    : "Select all pending"}
                </span>
              </div>
              {selectedIds.size > 0 && (
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => batchApproveMutation.mutate(Array.from(selectedIds))}
                    className={ds.buttons.primary}
                    disabled={batchApproveMutation.isPending}
                    size="sm"
                  >
                    <CheckCheck className="h-4 w-4 mr-1" />
                    {batchApproveMutation.isPending
                      ? "Approving..."
                      : `Approve ${selectedIds.size}`}
                  </Button>
                  <Button
                    onClick={() => setSelectedIds(new Set())}
                    variant="outline"
                    size="sm"
                  >
                    Clear
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-4">
        <Card className={cn(ds.borderRadius.card, "border-amber-200 bg-amber-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-100">
                <Clock className="h-5 w-5 text-amber-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-amber-700")}>Pending</p>
                <p className={cn(ds.typography.heading2, "text-amber-800")}>
                  {stats?.pending || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className={cn(ds.borderRadius.card, "border-emerald-200 bg-emerald-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-100">
                <CheckCircle2 className="h-5 w-5 text-emerald-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-emerald-700")}>Applied</p>
                <p className={cn(ds.typography.heading2, "text-emerald-800")}>
                  {stats?.applied || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className={cn(ds.borderRadius.card, "border-blue-200 bg-blue-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <AlertCircle className="h-5 w-5 text-blue-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-blue-700")}>Approved</p>
                <p className={cn(ds.typography.heading2, "text-blue-800")}>
                  {stats?.approved || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-100">
                <XCircle className="h-5 w-5 text-red-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-red-700")}>Denied</p>
                <p className={cn(ds.typography.heading2, "text-red-800")}>
                  {stats?.denied || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Suggestions List */}
      {isLoading ? (
        <ValidationSkeleton />
      ) : suggestions.length === 0 ? (
        <EmptyState status={statusFilter} />
      ) : (
        <div className="space-y-4">
          {suggestions.map((suggestion: ValidationSuggestion) => (
            <Card
              key={suggestion.suggestion_id}
              className={cn(
                ds.borderRadius.card,
                "border-slate-200 transition-colors duration-200",
                selectedIds.has(suggestion.suggestion_id) && "border-blue-300 bg-blue-50/30"
              )}
            >
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  {/* Checkbox for pending items */}
                  {suggestion.status === "pending" && (
                    <div className="pt-1">
                      <Checkbox
                        checked={selectedIds.has(suggestion.suggestion_id)}
                        onCheckedChange={() => toggleSelect(suggestion.suggestion_id)}
                        aria-label={`Select suggestion for ${suggestion.project_code}`}
                      />
                    </div>
                  )}

                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                            {suggestion.project_code}
                          </span>
                          <span className={ds.textColors.tertiary}>•</span>
                          <span className={ds.textColors.secondary}>{suggestion.entity_name}</span>
                        </div>

                        <div className="mb-4">
                          <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mb-2")}>
                            Field: {suggestion.field_name}
                          </p>
                          <div className="flex items-center gap-4">
                            <div>
                              <span className={cn(ds.typography.caption, ds.textColors.muted)}>Current: </span>
                              <span className={cn(ds.badges.danger, "font-mono")}>
                                {suggestion.current_value}
                              </span>
                            </div>
                            <span className={ds.textColors.muted}>→</span>
                            <div>
                              <span className={cn(ds.typography.caption, ds.textColors.muted)}>Suggested: </span>
                              <span className={cn(ds.badges.success, "font-mono")}>
                                {suggestion.suggested_value}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Evidence */}
                        <div className={cn("mb-4 p-4 rounded-lg", ds.status.neutral.bg)}>
                          <p className={cn(ds.typography.captionBold, ds.textColors.secondary, "mb-1")}>
                            Evidence ({suggestion.evidence_source}):
                          </p>
                          {suggestion.evidence_email_subject && (
                            <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mb-1")}>
                              Subject: {suggestion.evidence_email_subject}
                            </p>
                          )}
                          <p className={cn(ds.typography.body, ds.textColors.secondary, "italic")}>
                            &quot;{suggestion.evidence_snippet}&quot;
                          </p>
                        </div>

                        {/* AI Reasoning */}
                        <p className={cn(ds.typography.caption, ds.textColors.secondary, "mb-2")}>
                          <span className="font-semibold">AI Reasoning:</span>{" "}
                          {suggestion.reasoning}
                        </p>

                        {/* Confidence */}
                        <div className="flex items-center gap-2">
                          <span className={cn(ds.typography.caption, ds.textColors.muted)}>Confidence:</span>
                          <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                            <div
                              className={cn(
                                "h-full rounded-full",
                                suggestion.confidence_score >= 0.8
                                  ? "bg-emerald-500"
                                  : suggestion.confidence_score >= 0.6
                                  ? "bg-amber-500"
                                  : "bg-red-500"
                              )}
                              style={{
                                width: `${suggestion.confidence_score * 100}%`,
                              }}
                            />
                          </div>
                          <span className={cn(ds.typography.captionBold, ds.textColors.primary)}>
                            {(suggestion.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>

                      {/* Actions */}
                      {suggestion.status === "pending" && (
                        <div className="ml-4 flex flex-col gap-2">
                          <Button
                            onClick={() => approveMutation.mutate(suggestion.suggestion_id)}
                            className={ds.buttons.primary}
                            disabled={approveMutation.isPending}
                          >
                            <CheckCircle2 className="h-4 w-4 mr-1" />
                            Approve
                          </Button>
                          <Button
                            onClick={() => {
                              const notes = prompt("Reason for denial:");
                              if (notes) {
                                denyMutation.mutate({
                                  id: suggestion.suggestion_id,
                                  notes,
                                });
                              }
                            }}
                            variant="outline"
                            className={ds.buttons.danger}
                            disabled={denyMutation.isPending}
                          >
                            <XCircle className="h-4 w-4 mr-1" />
                            Deny
                          </Button>
                        </div>
                      )}
                    </div>

                    {/* Status Badge */}
                    <div className="mt-4 flex items-center gap-2">
                      {getStatusBadge(suggestion.status)}
                      {suggestion.reviewed_by && (
                        <span className={cn(ds.typography.caption, ds.textColors.muted)}>
                          Reviewed by {suggestion.reviewed_by} on{" "}
                          {new Date(suggestion.reviewed_at!).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
