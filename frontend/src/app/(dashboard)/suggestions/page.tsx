"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, SuggestionItem, NewContactSuggestion, ProjectAliasSuggestion } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  UserPlus,
  Link2,
  Check,
  X,
  Loader2,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Zap,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";

type SuggestionType = "all" | "new_contact" | "project_alias";
type ConfidenceFilter = "all" | "high" | "medium" | "low";

const ITEMS_PER_PAGE = 50;

export default function SuggestionsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<SuggestionType>("all");
  const [confidenceFilter, setConfidenceFilter] = useState<ConfidenceFilter>("all");
  const [page, setPage] = useState(0);
  const [bulkApproveDialogOpen, setBulkApproveDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState<SuggestionItem | null>(null);

  // Get confidence range from filter
  const getMinConfidence = (filter: ConfidenceFilter): number | undefined => {
    switch (filter) {
      case "high": return 0.8;
      case "medium": return 0.7;
      case "low": return undefined;
      default: return undefined;
    }
  };

  // Fetch stats
  const statsQuery = useQuery({
    queryKey: ["suggestions-stats"],
    queryFn: () => api.getSuggestionsStats(),
    staleTime: 30 * 1000,
  });

  // Fetch suggestions
  const suggestionsQuery = useQuery({
    queryKey: ["suggestions", activeTab, confidenceFilter, page],
    queryFn: () =>
      api.getSuggestions({
        status: "pending",
        field_name: activeTab === "all" ? undefined : activeTab,
        min_confidence: getMinConfidence(confidenceFilter),
        limit: ITEMS_PER_PAGE,
        offset: page * ITEMS_PER_PAGE,
      }),
    staleTime: 10 * 1000,
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (suggestionId: number) => api.approveAISuggestion(suggestionId),
    onSuccess: (data) => {
      toast.success(data.message || "Suggestion approved");
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to approve: ${error.message}`);
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) =>
      api.rejectAISuggestion(id, reason),
    onSuccess: () => {
      toast.success("Suggestion rejected");
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
      setRejectDialogOpen(false);
      setSelectedSuggestion(null);
    },
    onError: (error: Error) => {
      toast.error(`Failed to reject: ${error.message}`);
    },
  });

  // Bulk approve mutation
  const bulkApproveMutation = useMutation({
    mutationFn: () => api.bulkApproveAISuggestions(0.8),
    onSuccess: (data) => {
      toast.success(`Approved ${data.approved} suggestions (${data.skipped} skipped, ${data.errors} errors)`);
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
      setBulkApproveDialogOpen(false);
    },
    onError: (error: Error) => {
      toast.error(`Bulk approve failed: ${error.message}`);
    },
  });

  const stats = statsQuery.data;
  const suggestions = suggestionsQuery.data?.suggestions || [];
  const totalSuggestions = suggestionsQuery.data?.total || 0;
  const totalPages = Math.ceil(totalSuggestions / ITEMS_PER_PAGE);

  // Parse suggested value JSON (handles both string and already-parsed object)
  const parseSuggestedValue = (suggestion: SuggestionItem): NewContactSuggestion | ProjectAliasSuggestion | null => {
    try {
      const value = suggestion.suggested_value;
      // If it's already an object, return it directly
      if (typeof value === "object" && value !== null) {
        return value as unknown as NewContactSuggestion | ProjectAliasSuggestion;
      }
      // If it's a string, parse it
      if (typeof value === "string") {
        return JSON.parse(value);
      }
      return null;
    } catch {
      return null;
    }
  };

  // Get confidence color
  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return "bg-emerald-100 text-emerald-700 border-emerald-200";
    if (confidence >= 0.7) return "bg-amber-100 text-amber-700 border-amber-200";
    return "bg-red-100 text-red-700 border-red-200";
  };

  const getConfidenceBadgeVariant = (confidence: number): "default" | "secondary" | "destructive" => {
    if (confidence >= 0.8) return "default";
    if (confidence >= 0.7) return "secondary";
    return "destructive";
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Sparkles className="h-8 w-8 text-purple-600" />
            <h1 className="text-3xl font-bold text-slate-900">AI Suggestions Review</h1>
          </div>
          <p className="text-slate-600">
            Review and approve AI-extracted contacts and project aliases to train the system
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-slate-900">
                {stats?.by_status?.pending?.toLocaleString() || "—"}
              </div>
              <p className="text-sm text-slate-500">Total Pending</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <UserPlus className="h-5 w-5 text-blue-600" />
                <span className="text-2xl font-bold text-slate-900">
                  {stats?.pending_by_field?.new_contact?.toLocaleString() || "—"}
                </span>
              </div>
              <p className="text-sm text-slate-500">New Contacts</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Link2 className="h-5 w-5 text-purple-600" />
                <span className="text-2xl font-bold text-slate-900">
                  {stats?.pending_by_field?.project_alias?.toLocaleString() || "—"}
                </span>
              </div>
              <p className="text-sm text-slate-500">Project Aliases</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-emerald-600" />
                <span className="text-2xl font-bold text-emerald-600">
                  {stats?.high_confidence_pending?.toLocaleString() || "—"}
                </span>
              </div>
              <p className="text-sm text-slate-500">High Confidence (80%+)</p>
            </CardContent>
          </Card>
        </div>

        {/* Bulk Actions */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            {/* Confidence Filter */}
            <Select
              value={confidenceFilter}
              onValueChange={(v) => {
                setConfidenceFilter(v as ConfidenceFilter);
                setPage(0);
              }}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by confidence" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Confidence</SelectItem>
                <SelectItem value="high">High (80%+)</SelectItem>
                <SelectItem value="medium">Medium (70-80%)</SelectItem>
                <SelectItem value="low">Low (&lt;70%)</SelectItem>
              </SelectContent>
            </Select>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                queryClient.invalidateQueries({ queryKey: ["suggestions"] });
                queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
              }}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>

          <Button
            onClick={() => setBulkApproveDialogOpen(true)}
            disabled={!stats?.high_confidence_pending || stats.high_confidence_pending === 0}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            <Zap className="h-4 w-4 mr-2" />
            Bulk Approve High Confidence ({stats?.high_confidence_pending || 0})
          </Button>
        </div>

        {/* Tabs */}
        <Tabs
          value={activeTab}
          onValueChange={(v) => {
            setActiveTab(v as SuggestionType);
            setPage(0);
          }}
        >
          <TabsList className="mb-6">
            <TabsTrigger value="all">
              All ({stats?.by_status?.pending || 0})
            </TabsTrigger>
            <TabsTrigger value="new_contact">
              <UserPlus className="h-4 w-4 mr-1" />
              Contacts ({stats?.pending_by_field?.new_contact || 0})
            </TabsTrigger>
            <TabsTrigger value="project_alias">
              <Link2 className="h-4 w-4 mr-1" />
              Aliases ({stats?.pending_by_field?.project_alias || 0})
            </TabsTrigger>
          </TabsList>

          <TabsContent value={activeTab} className="mt-0">
            {suggestionsQuery.isLoading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
              </div>
            ) : suggestions.length === 0 ? (
              <Card>
                <CardContent className="py-20 text-center">
                  <Sparkles className="h-12 w-12 mx-auto text-slate-300 mb-4" />
                  <p className="text-slate-500">No pending suggestions found</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {suggestions.map((suggestion) => {
                  const parsed = parseSuggestedValue(suggestion);
                  const isContact = suggestion.field_name === "new_contact";

                  return (
                    <Card
                      key={suggestion.suggestion_id}
                      className={`border-2 ${getConfidenceColor(suggestion.confidence).replace("bg-", "border-").replace("-100", "-200")}`}
                    >
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between gap-4">
                          {/* Left: Content */}
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-3">
                              {isContact ? (
                                <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                                  <UserPlus className="h-3 w-3 mr-1" />
                                  New Contact
                                </Badge>
                              ) : (
                                <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
                                  <Link2 className="h-3 w-3 mr-1" />
                                  Project Alias
                                </Badge>
                              )}
                              <Badge
                                variant={getConfidenceBadgeVariant(suggestion.confidence)}
                                className={getConfidenceColor(suggestion.confidence)}
                              >
                                {Math.round(suggestion.confidence * 100)}% confidence
                              </Badge>
                              <span className="text-xs text-slate-400">
                                {format(new Date(suggestion.created_at), "MMM d, yyyy")}
                              </span>
                            </div>

                            {/* Parsed Content */}
                            {isContact && parsed ? (
                              <div className="bg-slate-50 rounded-lg p-4 space-y-2">
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <p className="text-xs text-slate-500 uppercase tracking-wide">Name</p>
                                    <p className="font-medium text-slate-900">
                                      {(parsed as NewContactSuggestion).name || "—"}
                                    </p>
                                  </div>
                                  <div>
                                    <p className="text-xs text-slate-500 uppercase tracking-wide">Email</p>
                                    <p className="font-medium text-slate-900">
                                      {(parsed as NewContactSuggestion).email || "—"}
                                    </p>
                                  </div>
                                  <div>
                                    <p className="text-xs text-slate-500 uppercase tracking-wide">Company</p>
                                    <p className="text-slate-700">
                                      {(parsed as NewContactSuggestion).company || "—"}
                                    </p>
                                  </div>
                                  <div>
                                    <p className="text-xs text-slate-500 uppercase tracking-wide">Related Project</p>
                                    <p className="text-slate-700">
                                      {(parsed as NewContactSuggestion).related_project || "—"}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ) : !isContact && parsed ? (
                              <div className="bg-slate-50 rounded-lg p-4">
                                <div className="flex items-center gap-4">
                                  <div>
                                    <p className="text-xs text-slate-500 uppercase tracking-wide">Alias</p>
                                    <p className="font-medium text-slate-900 font-mono">
                                      {(parsed as ProjectAliasSuggestion).alias || "—"}
                                    </p>
                                  </div>
                                  <div className="text-slate-400">→</div>
                                  <div>
                                    <p className="text-xs text-slate-500 uppercase tracking-wide">Project Code</p>
                                    <p className="font-medium text-purple-700 font-mono">
                                      {(parsed as ProjectAliasSuggestion).project_code || "—"}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ) : (
                              <pre className="text-xs bg-slate-50 rounded p-2 overflow-auto">
                                {typeof suggestion.suggested_value === "string"
                                  ? suggestion.suggested_value
                                  : JSON.stringify(suggestion.suggested_value, null, 2)}
                              </pre>
                            )}

                            {/* Evidence */}
                            {suggestion.evidence && (
                              <div className="mt-3">
                                <p className="text-xs text-slate-500 mb-1">Evidence:</p>
                                <p className="text-sm text-slate-600 italic">
                                  &ldquo;{suggestion.evidence}&rdquo;
                                </p>
                              </div>
                            )}
                          </div>

                          {/* Right: Actions */}
                          <div className="flex flex-col gap-2">
                            <Button
                              size="sm"
                              onClick={() => approveMutation.mutate(suggestion.suggestion_id)}
                              disabled={approveMutation.isPending}
                              className="bg-emerald-600 hover:bg-emerald-700"
                            >
                              {approveMutation.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <>
                                  <Check className="h-4 w-4 mr-1" />
                                  Approve
                                </>
                              )}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedSuggestion(suggestion);
                                setRejectDialogOpen(true);
                              }}
                              className="text-red-600 border-red-200 hover:bg-red-50"
                            >
                              <X className="h-4 w-4 mr-1" />
                              Reject
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between pt-4">
                    <p className="text-sm text-slate-500">
                      Showing {page * ITEMS_PER_PAGE + 1} -{" "}
                      {Math.min((page + 1) * ITEMS_PER_PAGE, totalSuggestions)} of{" "}
                      {totalSuggestions.toLocaleString()}
                    </p>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.max(0, p - 1))}
                        disabled={page === 0}
                      >
                        <ChevronLeft className="h-4 w-4" />
                        Previous
                      </Button>
                      <span className="text-sm text-slate-600">
                        Page {page + 1} of {totalPages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                        disabled={page >= totalPages - 1}
                      >
                        Next
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Bulk Approve Dialog */}
        <AlertDialog open={bulkApproveDialogOpen} onOpenChange={setBulkApproveDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Bulk Approve High Confidence Suggestions</AlertDialogTitle>
              <AlertDialogDescription>
                This will approve all {stats?.high_confidence_pending || 0} suggestions with 80%+ confidence.
                <br /><br />
                • New contacts will be added to the contacts table
                <br />
                • Project aliases will be added to learned patterns
                <br /><br />
                This action cannot be easily undone. Continue?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => bulkApproveMutation.mutate()}
                disabled={bulkApproveMutation.isPending}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {bulkApproveMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Zap className="h-4 w-4 mr-2" />
                )}
                Approve All
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* Reject Dialog */}
        <AlertDialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Reject Suggestion</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to reject this suggestion? This will mark it as rejected and help train the AI to avoid similar suggestions.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => setSelectedSuggestion(null)}>
                Cancel
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={() => {
                  if (selectedSuggestion) {
                    rejectMutation.mutate({ id: selectedSuggestion.suggestion_id });
                  }
                }}
                disabled={rejectMutation.isPending}
                className="bg-red-600 hover:bg-red-700"
              >
                {rejectMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <X className="h-4 w-4 mr-2" />
                )}
                Reject
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
}
