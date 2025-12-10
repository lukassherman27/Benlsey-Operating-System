"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AISuggestion } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { ds, bensleyVoice, getLoadingMessage } from "@/lib/design-system";
import {
  Brain,
  Clock,
  CheckCircle2,
  XCircle,
  Sparkles,
  TrendingUp,
  Zap,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { toast } from "sonner";

// Loading skeleton
function IntelligenceSkeleton() {
  return (
    <div className="space-y-4">
      <p className={cn(ds.typography.caption, ds.textColors.tertiary, "text-center mb-4")}>
        {getLoadingMessage()}
      </p>
      {[...Array(3)].map((_, i) => (
        <Card key={i} className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="p-6">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Skeleton className="h-5 w-20" />
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-5 w-16" />
              </div>
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <div className="flex items-center gap-2">
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

// Empty state for suggestions
function SuggestionsEmptyState() {
  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
      <CardContent className="py-12 text-center">
        <Brain className="mx-auto h-10 w-10 text-slate-300 mb-3" />
        <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-1")}>
          No pending suggestions
        </p>
        <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
          {bensleyVoice.emptyStates.suggestions}
        </p>
      </CardContent>
    </Card>
  );
}

// Empty state for patterns
function PatternsEmptyState() {
  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
      <CardContent className="py-8 text-center">
        <Sparkles className="mx-auto h-8 w-8 text-slate-300 mb-2" />
        <p className={cn(ds.typography.bodyBold, ds.textColors.primary, "mb-1")}>
          No patterns learned yet
        </p>
        <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
          Patterns are created from feedback
        </p>
      </CardContent>
    </Card>
  );
}

export default function AIIntelligencePage() {
  const [typeFilter, setTypeFilter] = useState<string>("");
  const queryClient = useQueryClient();

  // Fetch learning stats
  const { data: statsData } = useQuery({
    queryKey: ["learning-stats"],
    queryFn: () => api.getLearningStats(),
  });

  // Fetch pending suggestions
  const { data: suggestionsData, isLoading } = useQuery({
    queryKey: ["learning-suggestions", typeFilter],
    queryFn: () => api.getLearningPendingSuggestions(typeFilter || undefined),
  });

  // Fetch learned patterns
  const { data: patternsData } = useQuery({
    queryKey: ["learning-patterns"],
    queryFn: () => api.getLearningPatterns(),
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (suggestionId: number) =>
      api.approveLearning(suggestionId, "admin", true),
    onSuccess: () => {
      toast.success(bensleyVoice.successMessages.suggestionApproved);
      queryClient.invalidateQueries({ queryKey: ["learning-suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["learning-stats"] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to approve: ${error.message}`);
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      api.rejectLearning(id, "admin", reason),
    onSuccess: () => {
      toast.success("Suggestion rejected. The AI will learn from this.");
      queryClient.invalidateQueries({ queryKey: ["learning-suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["learning-stats"] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to reject: ${error.message}`);
    },
  });

  // Generate rules mutation
  const generateRulesMutation = useMutation({
    mutationFn: () => api.generateRules(3),
    onSuccess: () => {
      toast.success("New rules generated from feedback patterns.");
      queryClient.invalidateQueries({ queryKey: ["learning-patterns"] });
      queryClient.invalidateQueries({ queryKey: ["learning-stats"] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to generate rules: ${error.message}`);
    },
  });

  const stats = statsData;
  const suggestions = suggestionsData?.suggestions || [];
  const patterns = patternsData?.patterns || [];

  const suggestionTypes = [
    { value: "", label: "All Types" },
    { value: "follow_up_needed", label: "Follow-up Needed" },
    { value: "new_contact", label: "New Contact" },
    { value: "fee_change", label: "Fee Change" },
    { value: "deadline_detected", label: "Deadline" },
    { value: "status_change", label: "Status Change" },
    { value: "action_item", label: "Action Item" },
  ];

  // Get priority badge
  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "critical":
        return <Badge className={ds.badges.danger}>{priority.toUpperCase()}</Badge>;
      case "high":
        return <Badge className={ds.badges.warning}>{priority.toUpperCase()}</Badge>;
      case "medium":
        return <Badge className={ds.badges.info}>{priority.toUpperCase()}</Badge>;
      default:
        return <Badge className={ds.badges.default}>{priority.toUpperCase()}</Badge>;
    }
  };

  // Get confidence color
  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return "bg-emerald-500";
    if (score >= 0.6) return "bg-amber-500";
    return "bg-red-500";
  };

  return (
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Header */}
      <div>
        <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
          AI Intelligence Dashboard
        </h1>
        <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
          Review AI suggestions and manage learned patterns. {bensleyVoice.tooltips.aiConfidence}
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-5 gap-4">
        <Card className={cn(ds.borderRadius.card, "border-amber-200 bg-amber-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-100">
                <Clock className="h-5 w-5 text-amber-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-amber-700")}>Pending Review</p>
                <p className={cn(ds.typography.heading2, "text-amber-800")}>
                  {stats?.suggestions?.pending || 0}
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
                <p className={cn(ds.typography.caption, "text-emerald-700")}>Approved</p>
                <p className={cn(ds.typography.heading2, "text-emerald-800")}>
                  {(stats?.suggestions?.approved || 0) + (stats?.suggestions?.modified || 0)}
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
                <p className={cn(ds.typography.caption, "text-red-700")}>Rejected</p>
                <p className={cn(ds.typography.heading2, "text-red-800")}>
                  {stats?.suggestions?.rejected || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className={cn(ds.borderRadius.card, "border-blue-200 bg-blue-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <Sparkles className="h-5 w-5 text-blue-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-blue-700")}>Active Patterns</p>
                <p className={cn(ds.typography.heading2, "text-blue-800")}>
                  {stats?.active_patterns || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className={cn(ds.borderRadius.card, "border-violet-200 bg-violet-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-violet-100">
                <TrendingUp className="h-5 w-5 text-violet-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-violet-700")}>Approval Rate</p>
                <p className={cn(ds.typography.heading2, "text-violet-800")}>
                  {stats?.approval_rate
                    ? `${(stats.approval_rate * 100).toFixed(0)}%`
                    : "N/A"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Two column layout */}
      <div className="grid grid-cols-3 gap-6">
        {/* Suggestions Column */}
        <div className="col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className={cn(ds.typography.heading3, ds.textColors.primary)}>
              Pending Suggestions
            </h2>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className={cn(ds.inputs.default, "w-48")}
            >
              {suggestionTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {isLoading ? (
            <IntelligenceSkeleton />
          ) : suggestions.length === 0 ? (
            <SuggestionsEmptyState />
          ) : (
            <div className="space-y-4">
              {suggestions.map((suggestion: AISuggestion) => (
                <Card
                  key={suggestion.suggestion_id}
                  className={cn(ds.borderRadius.card, "border-slate-200")}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        {/* Header */}
                        <div className="flex items-center gap-2 mb-2">
                          {getPriorityBadge(suggestion.priority)}
                          <Badge className={ds.badges.neutral}>
                            {suggestion.suggestion_type.replace(/_/g, " ")}
                          </Badge>
                          {suggestion.project_code && (
                            <span className={cn(ds.typography.caption, ds.textColors.muted)}>
                              {suggestion.project_code}
                            </span>
                          )}
                        </div>

                        {/* Title & Description */}
                        <h3 className={cn(ds.typography.bodyBold, ds.textColors.primary, "mb-1")}>
                          {suggestion.title}
                        </h3>
                        {suggestion.description && (
                          <p className={cn(ds.typography.body, ds.textColors.secondary, "mb-2")}>
                            {suggestion.description}
                          </p>
                        )}

                        {/* Source */}
                        <p className={cn(ds.typography.tiny, ds.textColors.muted, "mb-2")}>
                          Source: {suggestion.source_reference}
                        </p>

                        {/* Confidence */}
                        <div className="flex items-center gap-2">
                          <span className={cn(ds.typography.caption, ds.textColors.muted)}>
                            Confidence:
                          </span>
                          <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                            <div
                              className={cn(
                                "h-full rounded-full",
                                getConfidenceColor(suggestion.confidence_score)
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
                      <div className="ml-4 flex flex-col gap-2">
                        <Button
                          onClick={() =>
                            approveMutation.mutate(suggestion.suggestion_id)
                          }
                          className={ds.buttons.primary}
                          disabled={approveMutation.isPending}
                        >
                          <CheckCircle2 className="h-4 w-4 mr-1" />
                          Approve
                        </Button>
                        <Button
                          onClick={() => {
                            const reason = prompt("Reason for rejection:");
                            if (reason) {
                              rejectMutation.mutate({
                                id: suggestion.suggestion_id,
                                reason,
                              });
                            }
                          }}
                          className={ds.buttons.danger}
                          disabled={rejectMutation.isPending}
                        >
                          <XCircle className="h-4 w-4 mr-1" />
                          Reject
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Patterns Column */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className={cn(ds.typography.heading3, ds.textColors.primary)}>
              Learned Patterns
            </h2>
            <Button
              onClick={() => generateRulesMutation.mutate()}
              disabled={generateRulesMutation.isPending}
              className={ds.buttons.secondary}
            >
              <RefreshCw className={cn("h-4 w-4 mr-1", generateRulesMutation.isPending && "animate-spin")} />
              {generateRulesMutation.isPending ? "Generating..." : "Generate Rules"}
            </Button>
          </div>

          {patterns.length === 0 ? (
            <PatternsEmptyState />
          ) : (
            <div className="space-y-3">
              {patterns.map((pattern) => (
                <Card
                  key={pattern.pattern_id}
                  className={cn(ds.borderRadius.card, "border-slate-200")}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                        {pattern.pattern_name}
                      </span>
                      <Badge
                        className={
                          pattern.is_active ? ds.badges.success : ds.badges.neutral
                        }
                      >
                        {pattern.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                    <p className={cn(ds.typography.tiny, ds.textColors.muted, "mb-2")}>
                      Type: {pattern.pattern_type}
                    </p>
                    <div className="flex items-center gap-4">
                      <span className={cn(ds.typography.caption, ds.textColors.secondary)}>
                        Confidence:{" "}
                        <span className="font-semibold">
                          {(pattern.confidence_score * 100).toFixed(0)}%
                        </span>
                      </span>
                      <span className={cn(ds.typography.caption, ds.textColors.secondary)}>
                        Evidence: {pattern.evidence_count}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Quick Actions */}
          <Card className={cn(ds.borderRadius.card, ds.status.neutral.bg, ds.status.neutral.border)}>
            <CardContent className="p-4">
              <h3 className={cn(ds.typography.captionBold, ds.textColors.primary, "mb-3")}>
                Quick Actions
              </h3>
              <Button
                variant="outline"
                className={cn(ds.buttons.secondary, "w-full justify-start")}
                onClick={() =>
                  window.open("/api/agent/follow-up/summary", "_blank")
                }
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                View Follow-up Summary
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
