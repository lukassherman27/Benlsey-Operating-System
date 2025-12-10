"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, SuggestionItem, NewContactSuggestion, ProjectAliasSuggestion } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  UserPlus,
  Link2,
  Check,
  X,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Zap,
  RefreshCw,
  Pencil,
  Loader2,
  Mail,
  Eye,
  CheckSquare,
  Square,
  Keyboard,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { ds, bensleyVoice, getLoadingMessage } from "@/lib/design-system";

type SuggestionType = "all" | "new_contact" | "project_alias" | "email_link";
type ConfidenceFilter = "all" | "high" | "medium" | "low";

const ITEMS_PER_PAGE = 25;

// Contact form data with enriched fields
interface ContactFormData {
  name: string;
  email: string;
  company: string;
  role: string;
  related_project: string;
  notes: string;
}

export default function SuggestionsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<SuggestionType>("all");
  const [confidenceFilter, setConfidenceFilter] = useState<ConfidenceFilter>("all");
  const [page, setPage] = useState(0);

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [focusedIndex, setFocusedIndex] = useState<number>(0);

  // Dialog states
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [emailPreviewOpen, setEmailPreviewOpen] = useState(false);
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState<SuggestionItem | null>(null);

  // Email preview data
  const [previewEmail, setPreviewEmail] = useState<{
    subject: string;
    sender: string;
    date: string;
    body: string;
  } | null>(null);

  // Edit form state
  const [contactForm, setContactForm] = useState<ContactFormData>({
    name: "",
    email: "",
    company: "",
    role: "",
    related_project: "",
    notes: "",
  });

  // Ref for keyboard focus
  const listContainerRef = useRef<HTMLDivElement>(null);

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

  // Approve mutation (with edited data)
  const approveMutation = useMutation({
    mutationFn: ({ suggestionId, edits }: { suggestionId: number; edits?: ContactFormData }) =>
      api.approveAISuggestion(suggestionId, edits),
    onSuccess: (data) => {
      toast.success(data.message || bensleyVoice.successMessages.suggestionApproved);
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
      setEditDialogOpen(false);
      setSelectedSuggestion(null);
      setSelectedIds((prev) => {
        const newSet = new Set(prev);
        if (selectedSuggestion) newSet.delete(selectedSuggestion.suggestion_id);
        return newSet;
      });
      setContactForm({ name: "", email: "", company: "", role: "", related_project: "", notes: "" });
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
      setSelectedIds((prev) => {
        const newSet = new Set(prev);
        if (selectedSuggestion) newSet.delete(selectedSuggestion.suggestion_id);
        return newSet;
      });
    },
    onError: (error: Error) => {
      toast.error(`Failed to reject: ${error.message}`);
    },
  });

  // Bulk approve mutation
  const bulkApproveMutation = useMutation({
    mutationFn: (ids: number[]) => api.bulkApproveByIds(ids),
    onSuccess: (data) => {
      toast.success(`Approved ${data.approved} of ${data.total} suggestions`);
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
      setSelectedIds(new Set());
    },
    onError: (error: Error) => {
      toast.error(`Bulk approve failed: ${error.message}`);
    },
  });

  // Bulk reject mutation
  const bulkRejectMutation = useMutation({
    mutationFn: (ids: number[]) => api.bulkRejectByIds(ids, "batch_rejected"),
    onSuccess: (data) => {
      toast.success(`Rejected ${data.rejected} of ${data.total} suggestions`);
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
      setSelectedIds(new Set());
    },
    onError: (error: Error) => {
      toast.error(`Bulk reject failed: ${error.message}`);
    },
  });

  const stats = statsQuery.data;
  const suggestions = suggestionsQuery.data?.suggestions || [];
  const totalSuggestions = suggestionsQuery.data?.total || 0;
  const totalPages = Math.ceil(totalSuggestions / ITEMS_PER_PAGE);

  // Parse suggested data JSON
  const parseSuggestedValue = (suggestion: SuggestionItem): NewContactSuggestion | ProjectAliasSuggestion | null => {
    try {
      const value = suggestion.suggested_data;
      if (typeof value === "object" && value !== null) {
        return value as unknown as NewContactSuggestion | ProjectAliasSuggestion;
      }
      if (typeof value === "string") {
        return JSON.parse(value);
      }
      return null;
    } catch {
      return null;
    }
  };

  // Open edit dialog with pre-filled data
  const openEditDialog = (suggestion: SuggestionItem) => {
    const parsed = parseSuggestedValue(suggestion);
    if (parsed && suggestion.suggestion_type === "new_contact") {
      const contact = parsed as NewContactSuggestion;
      setContactForm({
        name: contact.name || "",
        email: contact.email || "",
        company: contact.company || "",
        role: "",
        related_project: contact.related_project || "",
        notes: "",
      });
    }
    setSelectedSuggestion(suggestion);
    setEditDialogOpen(true);
  };

  // Open email preview
  const openEmailPreview = async (suggestion: SuggestionItem) => {
    // Extract email info from source_reference or description
    const evidence = suggestion.source_reference || suggestion.description || "";
    setPreviewEmail({
      subject: suggestion.title || "No subject",
      sender: "Extracted from email",
      date: suggestion.created_at || "",
      body: evidence,
    });
    setEmailPreviewOpen(true);
  };

  // Get confidence progress bar color
  const getConfidenceBarColor = (confidence: number): string => {
    if (confidence >= 0.8) return "bg-emerald-500";
    if (confidence >= 0.5) return "bg-amber-500";
    return "bg-red-500";
  };

  // Get confidence badge color
  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return "bg-emerald-100 text-emerald-700 border-emerald-200";
    if (confidence >= 0.5) return "bg-amber-100 text-amber-700 border-amber-200";
    return "bg-red-100 text-red-700 border-red-200";
  };

  // Selection handlers
  const toggleSelection = (id: number) => {
    setSelectedIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const selectAll = () => {
    if (selectedIds.size === suggestions.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(suggestions.map((s) => s.suggestion_id)));
    }
  };

  const handleBulkApprove = () => {
    if (selectedIds.size === 0) return;
    bulkApproveMutation.mutate(Array.from(selectedIds));
  };

  const handleBulkReject = () => {
    if (selectedIds.size === 0) return;
    bulkRejectMutation.mutate(Array.from(selectedIds));
  };

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      // Don't handle if in input/textarea
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        editDialogOpen ||
        rejectDialogOpen
      ) {
        return;
      }

      const currentSuggestion = suggestions[focusedIndex];

      switch (e.key) {
        case "j":
        case "ArrowDown":
          e.preventDefault();
          setFocusedIndex((prev) => Math.min(prev + 1, suggestions.length - 1));
          break;
        case "k":
        case "ArrowUp":
          e.preventDefault();
          setFocusedIndex((prev) => Math.max(prev - 1, 0));
          break;
        case "a":
          e.preventDefault();
          if (currentSuggestion) {
            approveMutation.mutate({ suggestionId: currentSuggestion.suggestion_id });
          }
          break;
        case "r":
          e.preventDefault();
          if (currentSuggestion) {
            setSelectedSuggestion(currentSuggestion);
            setRejectDialogOpen(true);
          }
          break;
        case "e":
          e.preventDefault();
          if (currentSuggestion && currentSuggestion.suggestion_type === "new_contact") {
            openEditDialog(currentSuggestion);
          }
          break;
        case "p":
          e.preventDefault();
          if (currentSuggestion) {
            openEmailPreview(currentSuggestion);
          }
          break;
        case " ":
          e.preventDefault();
          if (currentSuggestion) {
            toggleSelection(currentSuggestion.suggestion_id);
          }
          break;
        case "?":
          e.preventDefault();
          setShowKeyboardHelp(true);
          break;
        case "Escape":
          setShowKeyboardHelp(false);
          setEmailPreviewOpen(false);
          break;
      }
    },
    [suggestions, focusedIndex, editDialogOpen, rejectDialogOpen, approveMutation]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // Reset focused index when page changes
  useEffect(() => {
    setFocusedIndex(0);
  }, [page, activeTab, confidenceFilter]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white w-full max-w-full overflow-x-hidden">
      <div className="mx-auto max-w-full px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <Sparkles className="h-8 w-8 text-purple-600" />
              <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
                {bensleyVoice.sectionHeaders.suggestions}
              </h1>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowKeyboardHelp(true)}
              className="text-slate-500"
            >
              <Keyboard className="h-4 w-4 mr-1" />
              Shortcuts
            </Button>
          </div>
          <p className={cn(ds.typography.body, ds.textColors.secondary)}>
            Review, edit, and approve AI-extracted contacts. Click Edit to add context before approving.
          </p>
          <p className={cn(ds.typography.caption, "text-amber-600 mt-2")}>
            Note: Many duplicates exist because contacts were extracted from multiple emails.
            Edit and approve unique ones, reject duplicates.
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

        {/* Actions Bar */}
        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <Select
              value={confidenceFilter}
              onValueChange={(v) => {
                setConfidenceFilter(v as ConfidenceFilter);
                setPage(0);
                setSelectedIds(new Set());
              }}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by confidence" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Confidence</SelectItem>
                <SelectItem value="high">High (80%+)</SelectItem>
                <SelectItem value="medium">Medium (50-80%)</SelectItem>
                <SelectItem value="low">Low (&lt;50%)</SelectItem>
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

          {/* Batch Actions */}
          {suggestions.length > 0 && (
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={selectAll}
                className="text-slate-600"
              >
                {selectedIds.size === suggestions.length ? (
                  <CheckSquare className="h-4 w-4 mr-2" />
                ) : (
                  <Square className="h-4 w-4 mr-2" />
                )}
                {selectedIds.size === suggestions.length ? "Deselect All" : "Select All"}
              </Button>

              {selectedIds.size > 0 && (
                <>
                  <span className="text-sm text-slate-500">
                    {selectedIds.size} selected
                  </span>
                  <Button
                    size="sm"
                    onClick={handleBulkApprove}
                    disabled={bulkApproveMutation.isPending}
                    className="bg-emerald-600 hover:bg-emerald-700"
                  >
                    {bulkApproveMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-1" />
                    ) : (
                      <Check className="h-4 w-4 mr-1" />
                    )}
                    Approve Selected
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleBulkReject}
                    disabled={bulkRejectMutation.isPending}
                    className="text-red-600 border-red-200 hover:bg-red-50"
                  >
                    {bulkRejectMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-1" />
                    ) : (
                      <X className="h-4 w-4 mr-1" />
                    )}
                    Reject Selected
                  </Button>
                </>
              )}
            </div>
          )}
        </div>

        {/* Tabs */}
        <Tabs
          value={activeTab}
          onValueChange={(v) => {
            setActiveTab(v as SuggestionType);
            setPage(0);
            setSelectedIds(new Set());
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
            <TabsTrigger value="email_link">
              <Mail className="h-4 w-4 mr-1" />
              Email Links ({stats?.pending_by_field?.email_link || 0})
            </TabsTrigger>
          </TabsList>

          <TabsContent value={activeTab} className="mt-0">
            {suggestionsQuery.isLoading ? (
              <div className="space-y-3">
                <p className={cn(ds.typography.caption, ds.textColors.tertiary, "text-center mb-4")}>
                  {getLoadingMessage()}
                </p>
                {[...Array(5)].map((_, i) => (
                  <Card key={i} className={cn(ds.borderRadius.card, "border-slate-200")}>
                    <CardContent className="p-4">
                      <div className="flex items-center gap-4">
                        <div className="flex-1 space-y-2">
                          <div className="flex gap-2">
                            <Skeleton className="h-5 w-16" />
                            <Skeleton className="h-5 w-12" />
                          </div>
                          <Skeleton className="h-4 w-3/4" />
                          <Skeleton className="h-3 w-1/2" />
                        </div>
                        <div className="flex gap-2">
                          <Skeleton className="h-8 w-16" />
                          <Skeleton className="h-8 w-8" />
                          <Skeleton className="h-8 w-8" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : suggestions.length === 0 ? (
              <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
                <CardContent className="py-20 text-center">
                  <Sparkles className="h-12 w-12 mx-auto text-slate-300 mb-4" />
                  <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
                    {bensleyVoice.sectionHeaders.suggestions}
                  </p>
                  <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                    {bensleyVoice.emptyStates.suggestions}
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3" ref={listContainerRef}>
                {suggestions.map((suggestion, index) => {
                  const parsed = parseSuggestedValue(suggestion);
                  const isContact = suggestion.suggestion_type === "new_contact";
                  const isSelected = selectedIds.has(suggestion.suggestion_id);
                  const isFocused = index === focusedIndex;
                  const confidencePercent = Math.round(suggestion.confidence_score * 100);

                  return (
                    <Card
                      key={suggestion.suggestion_id}
                      className={cn(
                        "border transition-all",
                        isSelected && "border-blue-400 bg-blue-50/30",
                        isFocused && "ring-2 ring-purple-400 ring-offset-1",
                        !isSelected && !isFocused && "hover:border-slate-300"
                      )}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center gap-4">
                          {/* Checkbox */}
                          <Checkbox
                            checked={isSelected}
                            onCheckedChange={() => toggleSelection(suggestion.suggestion_id)}
                            className="shrink-0"
                          />

                          {/* Left: Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              {isContact ? (
                                <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs">
                                  <UserPlus className="h-3 w-3 mr-1" />
                                  Contact
                                </Badge>
                              ) : suggestion.suggestion_type === "email_link" ? (
                                <Badge variant="outline" className="bg-teal-50 text-teal-700 border-teal-200 text-xs">
                                  <Mail className="h-3 w-3 mr-1" />
                                  Email Link
                                </Badge>
                              ) : (
                                <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200 text-xs">
                                  <Zap className="h-3 w-3 mr-1" />
                                  {suggestion.suggestion_type.replace(/_/g, " ")}
                                </Badge>
                              )}

                              {/* Confidence Progress Bar */}
                              <div className="flex items-center gap-2 min-w-[120px]">
                                <div className="w-16 h-2 bg-slate-200 rounded-full overflow-hidden">
                                  <div
                                    className={cn("h-full rounded-full transition-all", getConfidenceBarColor(suggestion.confidence_score))}
                                    style={{ width: `${confidencePercent}%` }}
                                  />
                                </div>
                                <Badge
                                  variant="outline"
                                  className={`text-xs ${getConfidenceColor(suggestion.confidence_score)}`}
                                >
                                  {confidencePercent}%
                                </Badge>
                              </div>

                              {/* Priority Badge */}
                              {suggestion.priority === "high" && (
                                <Badge variant="destructive" className="text-xs">
                                  High Priority
                                </Badge>
                              )}
                            </div>

                            {/* Title and Description */}
                            <div className="font-medium text-slate-900 text-sm">
                              {suggestion.title}
                            </div>
                            <p className="text-xs text-slate-500 mt-1">
                              {suggestion.description}
                            </p>

                            {suggestion.project_code && (
                              <div className="mt-1">
                                <code className="bg-blue-100 px-2 py-0.5 rounded text-blue-700 text-xs">
                                  {suggestion.project_code}
                                </code>
                              </div>
                            )}

                            {suggestion.source_reference && (
                              <p className="text-xs text-slate-400 mt-1 truncate">
                                From: {suggestion.source_reference}
                              </p>
                            )}
                          </div>

                          {/* Right: Actions */}
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openEmailPreview(suggestion)}
                              className="text-slate-500"
                              title="Preview source (p)"
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            {isContact && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openEditDialog(suggestion)}
                                title="Edit (e)"
                              >
                                <Pencil className="h-4 w-4 mr-1" />
                                Edit
                              </Button>
                            )}
                            <Button
                              size="sm"
                              onClick={() => approveMutation.mutate({ suggestionId: suggestion.suggestion_id })}
                              disabled={approveMutation.isPending}
                              className="bg-emerald-600 hover:bg-emerald-700"
                              title="Approve (a)"
                            >
                              <Check className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedSuggestion(suggestion);
                                setRejectDialogOpen(true);
                              }}
                              className="text-red-600 border-red-200 hover:bg-red-50"
                              title="Reject (r)"
                            >
                              <X className="h-4 w-4" />
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
                      Page {page + 1} of {totalPages} ({totalSuggestions.toLocaleString()} total)
                    </p>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.max(0, p - 1))}
                        disabled={page === 0}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                        disabled={page >= totalPages - 1}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Edit Contact Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Edit Contact Before Adding</DialogTitle>
              <DialogDescription>
                Review and enrich this contact with additional context before adding to your database.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    value={contactForm.name}
                    onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                    placeholder="Full name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={contactForm.email}
                    onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                    placeholder="email@example.com"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="company">Company</Label>
                  <Input
                    id="company"
                    value={contactForm.company}
                    onChange={(e) => setContactForm({ ...contactForm, company: e.target.value })}
                    placeholder="Company name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">Role/Title</Label>
                  <Select
                    value={contactForm.role}
                    onValueChange={(v) => setContactForm({ ...contactForm, role: v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="client">Client</SelectItem>
                      <SelectItem value="client_contact">Client Contact</SelectItem>
                      <SelectItem value="contractor">Contractor</SelectItem>
                      <SelectItem value="consultant">Consultant</SelectItem>
                      <SelectItem value="vendor">Vendor</SelectItem>
                      <SelectItem value="architect">Architect</SelectItem>
                      <SelectItem value="engineer">Engineer</SelectItem>
                      <SelectItem value="project_manager">Project Manager</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="related_project">Related Project(s)</Label>
                <Input
                  id="related_project"
                  value={contactForm.related_project}
                  onChange={(e) => setContactForm({ ...contactForm, related_project: e.target.value })}
                  placeholder="e.g., 22 BK-095, Rosewood Bangkok"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  value={contactForm.notes}
                  onChange={(e) => setContactForm({ ...contactForm, notes: e.target.value })}
                  placeholder="Any additional context about this contact..."
                  rows={3}
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => {
                  if (selectedSuggestion) {
                    approveMutation.mutate({
                      suggestionId: selectedSuggestion.suggestion_id,
                      edits: contactForm,
                    });
                  }
                }}
                disabled={approveMutation.isPending || !contactForm.name || !contactForm.email}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {approveMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Check className="h-4 w-4 mr-2" />
                )}
                Add Contact
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Reject Dialog */}
        <AlertDialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Reject Suggestion</AlertDialogTitle>
              <AlertDialogDescription>
                This will mark the suggestion as rejected. Use this for duplicates or incorrect data.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => setSelectedSuggestion(null)}>
                Cancel
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={() => {
                  if (selectedSuggestion) {
                    rejectMutation.mutate({ id: selectedSuggestion.suggestion_id, reason: "duplicate_or_invalid" });
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

        {/* Email Preview Sheet */}
        <Sheet open={emailPreviewOpen} onOpenChange={setEmailPreviewOpen}>
          <SheetContent className="w-[400px] sm:w-[540px] sm:max-w-lg">
            <SheetHeader>
              <SheetTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                Source Email
              </SheetTitle>
              <SheetDescription>
                Email that this suggestion was extracted from
              </SheetDescription>
            </SheetHeader>
            {previewEmail && (
              <div className="mt-6 space-y-4">
                <div>
                  <Label className="text-xs text-slate-500">Subject</Label>
                  <p className="font-medium text-slate-900">{previewEmail.subject}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs text-slate-500">From</Label>
                    <p className="text-sm text-slate-700">{previewEmail.sender}</p>
                  </div>
                  <div>
                    <Label className="text-xs text-slate-500">Date</Label>
                    <p className="text-sm text-slate-700">{previewEmail.date || "Unknown"}</p>
                  </div>
                </div>
                <div>
                  <Label className="text-xs text-slate-500">Evidence / Context</Label>
                  <div className="mt-2 p-3 bg-slate-50 rounded-lg border text-sm text-slate-700 max-h-[400px] overflow-y-auto whitespace-pre-wrap">
                    {previewEmail.body || "No additional context available"}
                  </div>
                </div>
              </div>
            )}
          </SheetContent>
        </Sheet>

        {/* Keyboard Shortcuts Help Dialog */}
        <Dialog open={showKeyboardHelp} onOpenChange={setShowKeyboardHelp}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Keyboard className="h-5 w-5" />
                Keyboard Shortcuts
              </DialogTitle>
              <DialogDescription>
                Speed up your workflow with these shortcuts
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-4">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-slate-100 rounded text-xs font-mono">j</kbd>
                  <span className="text-slate-600">Move down</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-slate-100 rounded text-xs font-mono">k</kbd>
                  <span className="text-slate-600">Move up</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-slate-100 rounded text-xs font-mono">a</kbd>
                  <span className="text-slate-600">Approve</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-slate-100 rounded text-xs font-mono">r</kbd>
                  <span className="text-slate-600">Reject</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-slate-100 rounded text-xs font-mono">e</kbd>
                  <span className="text-slate-600">Edit contact</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-slate-100 rounded text-xs font-mono">p</kbd>
                  <span className="text-slate-600">Preview email</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-slate-100 rounded text-xs font-mono">Space</kbd>
                  <span className="text-slate-600">Toggle select</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-slate-100 rounded text-xs font-mono">?</kbd>
                  <span className="text-slate-600">Show help</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-slate-100 rounded text-xs font-mono">Esc</kbd>
                  <span className="text-slate-600">Close dialogs</span>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
