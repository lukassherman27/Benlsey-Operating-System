"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, SuggestionItem, NewContactSuggestion, ProjectAliasSuggestion, SuggestionPreviewResponse, SuggestionSourceResponse, GroupedSuggestion } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Checkbox } from "@/components/ui/checkbox";
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
  ChevronDown,
  Zap,
  RefreshCw,
  Pencil,
  Loader2,
  Mail,
  Eye,
  CheckSquare,
  Square,
  Keyboard,
  RotateCcw,
  FileText,
  Info,
  List,
  FolderKanban,
  Building2,
  Layers,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { ds, bensleyVoice, getLoadingMessage } from "@/lib/design-system";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { EnhancedReviewCard } from "@/components/suggestions";
import { AIAnalysis, UserContext, SuggestionTag } from "@/lib/types";

type SuggestionType = "all" | "new_contact" | "project_alias" | "email_link";
type ConfidenceFilter = "all" | "high" | "medium" | "low";
type ViewMode = "list" | "grouped" | "enhanced";

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
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [focusedIndex, setFocusedIndex] = useState<number>(0);

  // Dialog states
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [emailPreviewOpen, setEmailPreviewOpen] = useState(false);
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState<SuggestionItem | null>(null);
  const [previewSheetOpen, setPreviewSheetOpen] = useState(false);
  const [sourceSheetOpen, setSourceSheetOpen] = useState(false);
  const [rollbackConfirmOpen, setRollbackConfirmOpen] = useState(false);

  // Status filter for viewing approved suggestions
  const [statusFilter, setStatusFilter] = useState<"pending" | "approved">("pending");

  // Preview/Source data
  const [previewData, setPreviewData] = useState<SuggestionPreviewResponse | null>(null);
  const [sourceData, setSourceData] = useState<SuggestionSourceResponse | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingSource, setLoadingSource] = useState(false);

  // Email preview data (legacy - kept for backward compat)
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

  // Enhanced reject form state
  const [rejectReason, setRejectReason] = useState<string>("wrong_project");
  const [correctProjectCode, setCorrectProjectCode] = useState<string>("");
  const [createPatternOnReject, setCreatePatternOnReject] = useState(false);
  const [rejectPatternNotes, setRejectPatternNotes] = useState("");

  // Approve with context dialog state
  const [approveContextDialogOpen, setApproveContextDialogOpen] = useState(false);
  const [createSenderPattern, setCreateSenderPattern] = useState(false);
  const [createDomainPattern, setCreateDomainPattern] = useState(false);
  const [approvePatternNotes, setApprovePatternNotes] = useState("");
  const [approveContactRole, setApproveContactRole] = useState("");

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
    queryKey: ["suggestions", activeTab, confidenceFilter, page, statusFilter],
    queryFn: () =>
      api.getSuggestions({
        status: statusFilter,
        field_name: activeTab === "all" ? undefined : activeTab,
        min_confidence: getMinConfidence(confidenceFilter),
        limit: ITEMS_PER_PAGE,
        offset: page * ITEMS_PER_PAGE,
      }),
    staleTime: 10 * 1000,
  });

  // Fetch grouped suggestions
  const groupedSuggestionsQuery = useQuery({
    queryKey: ["suggestions-grouped", statusFilter, confidenceFilter],
    queryFn: () =>
      api.getGroupedSuggestions({
        status: statusFilter,
        min_confidence: getMinConfidence(confidenceFilter),
      }),
    staleTime: 10 * 1000,
    enabled: viewMode === "grouped",
  });

  // Enhanced review state (uses suggestions, defined later)
  const [enhancedReviewIndex, setEnhancedReviewIndex] = useState(0);
  const [enhancedContextData, setEnhancedContextData] = useState<{
    ai_analysis: AIAnalysis;
    source_content: { type: string; id: number; subject?: string; sender?: string; date: string; body: string } | null;
    preview: { is_actionable: boolean; action: string; table: string; summary: string; changes: { field: string; old_value: string | null; new_value: string | null }[] } | null;
    suggestion?: { project_name?: string };
  } | null>(null);
  const [loadingEnhancedContext, setLoadingEnhancedContext] = useState(false);

  // Fetch suggestion tags for autocomplete
  const tagsQuery = useQuery({
    queryKey: ["suggestion-tags"],
    queryFn: () => api.getSuggestionTags(),
    staleTime: 60 * 1000,
    enabled: viewMode === "enhanced",
  });
  const availableTags: SuggestionTag[] = tagsQuery.data?.tags || [];

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

  // Rollback mutation
  const rollbackMutation = useMutation({
    mutationFn: (suggestionId: number) => api.rollbackSuggestion(suggestionId),
    onSuccess: (data) => {
      toast.success(data.message || "Suggestion rolled back successfully");
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
      setRollbackConfirmOpen(false);
      setSelectedSuggestion(null);
    },
    onError: (error: Error) => {
      toast.error(`Rollback failed: ${error.message}`);
    },
  });

  // Fetch projects for linking dropdown
  const projectsQuery = useQuery({
    queryKey: ["projects-for-linking"],
    queryFn: () => api.getProjectsForLinking(500),
    staleTime: 60 * 1000,
  });
  const projectOptions = projectsQuery.data?.projects || [];

  // Fetch proposals for correction dialog (backend limits per_page to 100)
  const proposalsQuery = useQuery({
    queryKey: ["proposals-for-linking"],
    queryFn: () => api.getProposals({ per_page: 100 }),
    staleTime: 60 * 1000,
  });
  // api.getProposals uses normalizePaginationResponse which returns {data: [...], pagination: {...}}
  const proposalOptions = (proposalsQuery.data?.data || []).map((p) => ({
    code: p.project_code,
    name: p.project_name || p.project_code,
  }));

  // Enhanced reject with correction mutation
  const rejectWithCorrectionMutation = useMutation({
    mutationFn: (data: {
      suggestionId: number;
      rejection_reason: string;
      correct_project_code?: string;
      create_pattern?: boolean;
      pattern_notes?: string;
    }) =>
      api.rejectWithCorrection(data.suggestionId, {
        rejection_reason: data.rejection_reason,
        correct_project_code: data.correct_project_code,
        create_pattern: data.create_pattern,
        pattern_notes: data.pattern_notes,
      }),
    onSuccess: (data) => {
      const msg = data.data?.corrected
        ? `Rejected with correction${data.data?.pattern_created ? " and pattern created" : ""}`
        : "Suggestion rejected";
      toast.success(msg);
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
      setRejectDialogOpen(false);
      setSelectedSuggestion(null);
      // Reset form state
      setRejectReason("wrong_project");
      setCorrectProjectCode("");
      setCreatePatternOnReject(false);
      setRejectPatternNotes("");
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

  // Approve with context mutation
  const approveWithContextMutation = useMutation({
    mutationFn: (data: {
      suggestionId: number;
      create_sender_pattern?: boolean;
      create_domain_pattern?: boolean;
      contact_role?: string;
      pattern_notes?: string;
    }) =>
      api.approveWithContext(data.suggestionId, {
        create_sender_pattern: data.create_sender_pattern,
        create_domain_pattern: data.create_domain_pattern,
        contact_role: data.contact_role,
        pattern_notes: data.pattern_notes,
      }),
    onSuccess: (data) => {
      const patternsCreated = data.data?.patterns_created?.length || 0;
      const msg = patternsCreated > 0
        ? `Approved with ${patternsCreated} pattern(s) created`
        : "Suggestion approved";
      toast.success(msg);
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
      setApproveContextDialogOpen(false);
      setSelectedSuggestion(null);
      // Reset form state
      setCreateSenderPattern(false);
      setCreateDomainPattern(false);
      setApprovePatternNotes("");
      setApproveContactRole("");
      setSelectedIds((prev) => {
        const newSet = new Set(prev);
        if (selectedSuggestion) newSet.delete(selectedSuggestion.suggestion_id);
        return newSet;
      });
    },
    onError: (error: Error) => {
      toast.error(`Failed to approve: ${error.message}`);
    },
  });

  const stats = statsQuery.data;
  const suggestions = suggestionsQuery.data?.suggestions || [];
  const totalSuggestions = suggestionsQuery.data?.total || 0;
  const totalPages = Math.ceil(totalSuggestions / ITEMS_PER_PAGE);
  const groupedData = groupedSuggestionsQuery.data?.groups || [];

  // Current suggestion for enhanced view (needs to be after suggestions is defined)
  const enhancedSuggestion = suggestions[enhancedReviewIndex] || null;

  // Fetch full context when entering enhanced mode
  useEffect(() => {
    if (viewMode === "enhanced" && enhancedSuggestion) {
      setLoadingEnhancedContext(true);
      api.getSuggestionFullContext(enhancedSuggestion.suggestion_id)
        .then((data) => {
          setEnhancedContextData({
            ai_analysis: data.ai_analysis as AIAnalysis,
            source_content: data.source_content,
            preview: data.preview,
            suggestion: data.suggestion as { project_name?: string } | undefined,
          });
        })
        .catch((e) => {
          console.error("Failed to load enhanced context:", e);
          toast.error("Failed to load suggestion context");
        })
        .finally(() => setLoadingEnhancedContext(false));
    }
  }, [viewMode, enhancedSuggestion?.suggestion_id]);

  // Toggle group expansion
  const toggleGroup = (groupKey: string) => {
    setExpandedGroups((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(groupKey)) {
        newSet.delete(groupKey);
      } else {
        newSet.add(groupKey);
      }
      return newSet;
    });
  };

  // Get group key for a suggestion group
  const getGroupKey = (group: GroupedSuggestion) =>
    group.project_code || "ungrouped";

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

  // Open email preview (legacy)
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

  // Open preview sheet - shows what changes will be made
  const openPreview = async (suggestion: SuggestionItem) => {
    setSelectedSuggestion(suggestion);
    setLoadingPreview(true);
    setPreviewSheetOpen(true);
    try {
      const data = await api.getSuggestionPreview(suggestion.suggestion_id);
      setPreviewData(data);
    } catch {
      toast.error("Failed to load preview");
      setPreviewData(null);
    } finally {
      setLoadingPreview(false);
    }
  };

  // Open source sheet - shows the original email/transcript
  const openSource = async (suggestion: SuggestionItem) => {
    setSelectedSuggestion(suggestion);
    setLoadingSource(true);
    setSourceSheetOpen(true);
    try {
      const data = await api.getSuggestionSource(suggestion.suggestion_id);
      setSourceData(data);
    } catch {
      toast.error("Failed to load source");
      setSourceData(null);
    } finally {
      setLoadingSource(false);
    }
  };

  // Open rollback confirmation
  const openRollbackConfirm = (suggestion: SuggestionItem) => {
    setSelectedSuggestion(suggestion);
    setRollbackConfirmOpen(true);
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
  }, [page, activeTab, confidenceFilter, statusFilter]);

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
              value={statusFilter}
              onValueChange={(v) => {
                setStatusFilter(v as "pending" | "approved");
                setPage(0);
                setSelectedIds(new Set());
              }}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
              </SelectContent>
            </Select>

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
                queryClient.invalidateQueries({ queryKey: ["suggestions-grouped"] });
              }}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>

            {/* View Mode Toggle */}
            <div className="flex items-center rounded-md border">
              <Button
                variant={viewMode === "list" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("list")}
                className="rounded-r-none border-0"
              >
                <List className="h-4 w-4 mr-1" />
                List
              </Button>
              <Button
                variant={viewMode === "grouped" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("grouped")}
                className="border-0"
              >
                <FolderKanban className="h-4 w-4 mr-1" />
                Grouped
              </Button>
              <Button
                variant={viewMode === "enhanced" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => {
                  setViewMode("enhanced");
                  setEnhancedReviewIndex(0);
                }}
                className="rounded-l-none border-0"
              >
                <Layers className="h-4 w-4 mr-1" />
                Enhanced
              </Button>
            </div>
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
            {/* Grouped View */}
            {viewMode === "grouped" ? (
              <div className="space-y-4">
                {groupedSuggestionsQuery.isLoading ? (
                  <div className="space-y-3">
                    <p className={cn(ds.typography.caption, ds.textColors.tertiary, "text-center mb-4")}>
                      {getLoadingMessage()}
                    </p>
                    {[...Array(3)].map((_, i) => (
                      <Card key={i} className={cn(ds.borderRadius.card, "border-slate-200")}>
                        <CardContent className="p-4">
                          <Skeleton className="h-6 w-48 mb-2" />
                          <Skeleton className="h-4 w-24" />
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : groupedData.length === 0 ? (
                  <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
                    <CardContent className="py-20 text-center">
                      <Sparkles className="h-12 w-12 mx-auto text-slate-300 mb-4" />
                      <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
                        No Suggestions to Group
                      </p>
                      <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                        {bensleyVoice.emptyStates.suggestions}
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="space-y-3">
                    {groupedData.map((group) => {
                      const groupKey = getGroupKey(group);
                      const isExpanded = expandedGroups.has(groupKey);
                      const isUngrouped = !group.project_code;

                      return (
                        <Collapsible
                          key={groupKey}
                          open={isExpanded}
                          onOpenChange={() => toggleGroup(groupKey)}
                        >
                          <Card className={cn(
                            "border transition-all",
                            isExpanded && "border-purple-300 shadow-sm",
                            isUngrouped && "border-dashed border-slate-300"
                          )}>
                            <CollapsibleTrigger className="w-full">
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-3">
                                    <div className={cn(
                                      "p-2 rounded-lg",
                                      isUngrouped ? "bg-slate-100" : "bg-purple-100"
                                    )}>
                                      {isUngrouped ? (
                                        <FileText className="h-5 w-5 text-slate-600" />
                                      ) : (
                                        <Building2 className="h-5 w-5 text-purple-600" />
                                      )}
                                    </div>
                                    <div className="text-left">
                                      <div className="flex items-center gap-2">
                                        <h3 className="font-semibold text-slate-900">
                                          {isUngrouped ? "Ungrouped Suggestions" : group.project_code}
                                        </h3>
                                        {!isUngrouped && group.project_name && (
                                          <span className="text-sm text-slate-500">
                                            {group.project_name}
                                          </span>
                                        )}
                                      </div>
                                      <p className="text-sm text-slate-500">
                                        {group.suggestion_count} suggestion{group.suggestion_count !== 1 ? "s" : ""}
                                      </p>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Badge variant="secondary" className="text-xs">
                                      {group.suggestion_count}
                                    </Badge>
                                    <ChevronDown className={cn(
                                      "h-5 w-5 text-slate-400 transition-transform",
                                      isExpanded && "rotate-180"
                                    )} />
                                  </div>
                                </div>
                              </CardContent>
                            </CollapsibleTrigger>
                            <CollapsibleContent>
                              <div className="border-t px-4 pb-4 space-y-2">
                                {group.suggestions.map((suggestion) => {
                                  const isContact = suggestion.suggestion_type === "new_contact";
                                  const confidencePercent = Math.round(suggestion.confidence_score * 100);

                                  return (
                                    <div
                                      key={suggestion.suggestion_id}
                                      className="p-3 bg-slate-50 rounded-lg border border-slate-200 mt-2"
                                    >
                                      <div className="flex items-start justify-between gap-4">
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-center gap-2 mb-1">
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
                                            <Badge
                                              variant="outline"
                                              className={`text-xs ${getConfidenceColor(suggestion.confidence_score)}`}
                                            >
                                              {confidencePercent}%
                                            </Badge>
                                          </div>
                                          <p className="font-medium text-sm text-slate-900">{suggestion.title}</p>
                                          <p className="text-xs text-slate-500 mt-0.5">{suggestion.description}</p>
                                        </div>
                                        <div className="flex items-center gap-1 shrink-0">
                                          <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={(e) => { e.stopPropagation(); openPreview(suggestion); }}
                                            className="h-8 w-8 p-0 text-blue-600"
                                          >
                                            <Eye className="h-4 w-4" />
                                          </Button>
                                          {statusFilter === "pending" && (
                                            <>
                                              <Button
                                                size="sm"
                                                variant="ghost"
                                                onClick={(e) => { e.stopPropagation(); approveMutation.mutate({ suggestionId: suggestion.suggestion_id }); }}
                                                disabled={approveMutation.isPending}
                                                className="h-8 w-8 p-0 text-emerald-600"
                                              >
                                                <Check className="h-4 w-4" />
                                              </Button>
                                              <Button
                                                size="sm"
                                                variant="ghost"
                                                onClick={(e) => {
                                                  e.stopPropagation();
                                                  setSelectedSuggestion(suggestion);
                                                  setRejectDialogOpen(true);
                                                }}
                                                className="h-8 w-8 p-0 text-red-600"
                                              >
                                                <X className="h-4 w-4" />
                                              </Button>
                                            </>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </CollapsibleContent>
                          </Card>
                        </Collapsible>
                      );
                    })}
                  </div>
                )}
              </div>
            ) : viewMode === "enhanced" ? (
              /* Enhanced Review Mode */
              <div className="space-y-4">
                {suggestionsQuery.isLoading ? (
                  <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
                    <CardContent className="p-8">
                      <div className="flex items-center justify-center gap-2">
                        <Loader2 className="h-6 w-6 animate-spin text-purple-600" />
                        <span className="text-slate-600">Loading suggestions...</span>
                      </div>
                    </CardContent>
                  </Card>
                ) : suggestions.length === 0 ? (
                  <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
                    <CardContent className="py-20 text-center">
                      <Sparkles className="h-12 w-12 mx-auto text-slate-300 mb-4" />
                      <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
                        No Suggestions to Review
                      </p>
                      <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                        {bensleyVoice.emptyStates.suggestions}
                      </p>
                    </CardContent>
                  </Card>
                ) : enhancedSuggestion ? (
                  <EnhancedReviewCard
                    suggestion={{
                      ...enhancedSuggestion,
                      // Merge project_name from full-context API
                      ...(enhancedContextData?.suggestion ? {
                        project_name: enhancedContextData.suggestion.project_name
                      } : {})
                    }}
                    sourceData={enhancedContextData?.source_content ? {
                      success: true,
                      source_type: enhancedContextData.source_content.type as 'email' | 'transcript',
                      content: enhancedContextData.source_content.body,
                      metadata: {
                        subject: enhancedContextData.source_content.subject,
                        sender: enhancedContextData.source_content.sender,
                        date: enhancedContextData.source_content.date,
                      }
                    } : null}
                    previewData={enhancedContextData?.preview ? {
                      success: true,
                      is_actionable: enhancedContextData.preview.is_actionable,
                      action: enhancedContextData.preview.action as 'insert' | 'update' | 'delete' | 'none',
                      table: enhancedContextData.preview.table,
                      summary: enhancedContextData.preview.summary,
                      // Transform API's {new, old} to component's {new_value, old_value}
                      changes: (enhancedContextData.preview.changes || []).map((c: { field: string; new?: unknown; old?: unknown; new_value?: unknown; old_value?: unknown }) => ({
                        field: c.field,
                        old_value: c.old_value ?? c.old ?? null,
                        new_value: c.new_value ?? c.new ?? null,
                      })),
                    } : null}
                    aiAnalysis={enhancedContextData?.ai_analysis || null}
                    isLoading={loadingEnhancedContext}
                    projectOptions={projectOptions.map(p => ({ code: p.code, name: p.name || p.code }))}
                    proposalOptions={proposalOptions}
                    availableTags={availableTags}
                    onApprove={async (data) => {
                      try {
                        const result = await api.approveWithContext(enhancedSuggestion.suggestion_id, {
                          create_sender_pattern: data.createSenderPattern,
                          create_domain_pattern: data.createDomainPattern,
                          pattern_notes: data.userContext.notes || undefined,
                          contact_role: data.userContext.contact_role,
                        });
                        if (data.userContext.notes || data.userContext.tags.length > 0) {
                          await api.saveSuggestionFeedback(enhancedSuggestion.suggestion_id, {
                            context_notes: data.userContext.notes,
                            tags: data.userContext.tags,
                            contact_role: data.userContext.contact_role,
                            priority: data.userContext.priority,
                          });
                        }
                        const patternsMsg = (result.data?.patterns_created?.length || 0) > 0
                          ? ` Created ${result.data?.patterns_created?.length} pattern(s).`
                          : '';
                        toast.success(`Suggestion approved!${patternsMsg}`);
                        queryClient.invalidateQueries({ queryKey: ["suggestions"] });
                        queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
                        // Move to next suggestion
                        if (enhancedReviewIndex < suggestions.length - 1) {
                          setEnhancedReviewIndex(enhancedReviewIndex + 1);
                        }
                      } catch (e: unknown) {
                        toast.error(`Failed to approve: ${e instanceof Error ? e.message : 'Unknown error'}`);
                      }
                    }}
                    onReject={async (data) => {
                      try {
                        const result = await api.rejectWithCorrection(enhancedSuggestion.suggestion_id, {
                          rejection_reason: data.rejection_reason,
                          correct_project_code: data.correct_project_code,
                          linked_items: data.linked_items,
                          category: data.category,
                          subcategory: data.subcategory,
                          create_pattern: data.create_pattern,
                          pattern_notes: data.pattern_notes,
                        });
                        // Build message based on what was done
                        const parts: string[] = [];
                        if (result.data?.links_created && result.data.links_created.length > 0) {
                          parts.push(`linked to ${result.data.links_created.length} item(s)`);
                        }
                        if (result.data?.category_updated) {
                          parts.push(`categorized as ${result.data.category}`);
                        }
                        if (result.data?.pattern_created) {
                          parts.push("pattern learned");
                        }
                        const msg = parts.length > 0
                          ? `Rejected with correction: ${parts.join(", ")}`
                          : "Suggestion rejected";
                        toast.success(msg);
                        queryClient.invalidateQueries({ queryKey: ["suggestions"] });
                        queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
                        // Move to next suggestion
                        if (enhancedReviewIndex < suggestions.length - 1) {
                          setEnhancedReviewIndex(enhancedReviewIndex + 1);
                        }
                      } catch (e: unknown) {
                        toast.error(`Failed to reject: ${e instanceof Error ? e.message : 'Unknown error'}`);
                      }
                    }}
                    onSkip={() => {
                      // Move to next suggestion
                      if (enhancedReviewIndex < suggestions.length - 1) {
                        setEnhancedReviewIndex(enhancedReviewIndex + 1);
                      } else {
                        toast.info("No more suggestions");
                      }
                    }}
                    isApproving={approveMutation.isPending}
                    isRejecting={rejectMutation.isPending || rejectWithCorrectionMutation.isPending}
                    onPrevious={() => {
                      if (enhancedReviewIndex > 0) {
                        setEnhancedReviewIndex(enhancedReviewIndex - 1);
                      }
                    }}
                    onNext={() => {
                      if (enhancedReviewIndex < suggestions.length - 1) {
                        setEnhancedReviewIndex(enhancedReviewIndex + 1);
                      }
                    }}
                    hasPrevious={enhancedReviewIndex > 0}
                    hasNext={enhancedReviewIndex < suggestions.length - 1}
                    currentIndex={enhancedReviewIndex}
                    totalCount={suggestions.length}
                  />
                ) : null}
              </div>
            ) : suggestionsQuery.isLoading ? (
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
                            {/* Preview button - shows what changes will happen */}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openPreview(suggestion)}
                              className="text-blue-600"
                              title="Preview changes"
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            {/* View Source button - shows original email/transcript */}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openSource(suggestion)}
                              className="text-slate-500"
                              title="View source (p)"
                            >
                              <FileText className="h-4 w-4" />
                            </Button>
                            {statusFilter === "pending" && (
                              <>
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
                                {(suggestion.suggestion_type === "email_link" || suggestion.suggestion_type === "new_contact") && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => {
                                      setSelectedSuggestion(suggestion);
                                      setApproveContextDialogOpen(true);
                                    }}
                                    className="text-emerald-600 border-emerald-200 hover:bg-emerald-50"
                                    title="Approve with learning patterns"
                                  >
                                    <Sparkles className="h-4 w-4" />
                                  </Button>
                                )}
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
                              </>
                            )}
                            {statusFilter === "approved" && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openRollbackConfirm(suggestion)}
                                className="text-amber-600 border-amber-200 hover:bg-amber-50"
                                title="Undo/Rollback"
                              >
                                <RotateCcw className="h-4 w-4 mr-1" />
                                Undo
                              </Button>
                            )}
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

        {/* Enhanced Reject Dialog */}
        <Dialog open={rejectDialogOpen} onOpenChange={(open) => {
          setRejectDialogOpen(open);
          if (!open) {
            setSelectedSuggestion(null);
            setRejectReason("wrong_project");
            setCorrectProjectCode("");
            setCreatePatternOnReject(false);
            setRejectPatternNotes("");
          }
        }}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Reject Suggestion</DialogTitle>
              <DialogDescription>
                Explain why this suggestion is incorrect. Optionally provide the correct information to help the system learn.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              {/* Rejection Reason */}
              <div className="space-y-2">
                <Label>Why is this suggestion incorrect?</Label>
                <Select value={rejectReason} onValueChange={setRejectReason}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select reason" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="wrong_project">Wrong project</SelectItem>
                    <SelectItem value="wrong_contact">Wrong contact</SelectItem>
                    <SelectItem value="spam_irrelevant">Spam/irrelevant</SelectItem>
                    <SelectItem value="duplicate">Duplicate</SelectItem>
                    <SelectItem value="data_incorrect">Data is incorrect</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Correct Project/Proposal (for link-type suggestions) */}
              {(selectedSuggestion?.suggestion_type === "email_link" ||
                selectedSuggestion?.suggestion_type === "contact_link" ||
                selectedSuggestion?.suggestion_type === "transcript_link") &&
               rejectReason === "wrong_project" && (
                <div className="space-y-2">
                  <Label>Which project or proposal should this be linked to?</Label>
                  <Select value={correctProjectCode || "none"} onValueChange={(v) => setCorrectProjectCode(v === "none" ? "" : v)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select correct project or proposal" />
                    </SelectTrigger>
                    <SelectContent className="max-h-[300px]">
                      <SelectItem value="none">-- None / Don&apos;t link --</SelectItem>
                      {/* Projects */}
                      {projectOptions.length > 0 && (
                        <SelectItem value="__header_projects" disabled className="font-bold text-emerald-700 bg-emerald-50">
                          ── ACTIVE PROJECTS ──
                        </SelectItem>
                      )}
                      {projectOptions.map((p) => (
                        <SelectItem key={`proj-${p.code}`} value={p.code}>
                          <span className="flex items-center gap-2">
                            <span className="text-[10px] bg-emerald-100 text-emerald-700 px-1 rounded">PROJECT</span>
                            {p.code} - {p.name}
                          </span>
                        </SelectItem>
                      ))}
                      {/* Proposals */}
                      {proposalOptions.length > 0 && (
                        <SelectItem value="__header_proposals" disabled className="font-bold text-amber-700 bg-amber-50">
                          ── PROPOSALS ──
                        </SelectItem>
                      )}
                      {proposalOptions.map((p) => (
                        <SelectItem key={`prop-${p.code}`} value={p.code}>
                          <span className="flex items-center gap-2">
                            <span className="text-[10px] bg-amber-100 text-amber-700 px-1 rounded">PROPOSAL</span>
                            {p.code} - {p.name}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-500">
                    Selecting a project/proposal will create the correct link.
                  </p>
                </div>
              )}

              {/* Create Pattern Option */}
              {correctProjectCode && (
                <div className="space-y-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="createPatternOnReject"
                      checked={createPatternOnReject}
                      onCheckedChange={(checked) => setCreatePatternOnReject(checked === true)}
                    />
                    <Label htmlFor="createPatternOnReject" className="text-sm font-medium text-blue-900">
                      Learn from this correction
                    </Label>
                  </div>
                  <p className="text-xs text-blue-700">
                    This will create a pattern so emails from this sender are automatically linked to the correct project in the future.
                  </p>
                  {createPatternOnReject && (
                    <div className="space-y-2">
                      <Label className="text-xs text-blue-800">Pattern notes (optional)</Label>
                      <Input
                        value={rejectPatternNotes}
                        onChange={(e) => setRejectPatternNotes(e.target.value)}
                        placeholder="e.g., Contact for Rosewood project"
                        className="bg-white"
                      />
                    </div>
                  )}
                </div>
              )}
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setRejectDialogOpen(false);
                  setSelectedSuggestion(null);
                }}
              >
                Cancel
              </Button>
              <Button
                onClick={() => {
                  if (selectedSuggestion) {
                    if (correctProjectCode || createPatternOnReject) {
                      // Use enhanced reject with correction
                      rejectWithCorrectionMutation.mutate({
                        suggestionId: selectedSuggestion.suggestion_id,
                        rejection_reason: rejectReason,
                        correct_project_code: correctProjectCode || undefined,
                        create_pattern: createPatternOnReject,
                        pattern_notes: rejectPatternNotes || undefined,
                      });
                    } else {
                      // Use simple reject
                      rejectMutation.mutate({
                        id: selectedSuggestion.suggestion_id,
                        reason: rejectReason,
                      });
                    }
                  }
                }}
                disabled={rejectMutation.isPending || rejectWithCorrectionMutation.isPending}
                className="bg-red-600 hover:bg-red-700"
              >
                {(rejectMutation.isPending || rejectWithCorrectionMutation.isPending) ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <X className="h-4 w-4 mr-2" />
                )}
                {correctProjectCode ? "Reject & Correct" : "Reject"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Approve with Context Dialog */}
        <Dialog open={approveContextDialogOpen} onOpenChange={(open) => {
          setApproveContextDialogOpen(open);
          if (!open) {
            setSelectedSuggestion(null);
            setCreateSenderPattern(false);
            setCreateDomainPattern(false);
            setApprovePatternNotes("");
            setApproveContactRole("");
          }
        }}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Approve with Learning</DialogTitle>
              <DialogDescription>
                Approve this suggestion and optionally create patterns to improve future suggestions.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              {/* Show suggestion info */}
              {selectedSuggestion && (
                <div className="p-3 bg-slate-50 rounded-lg border">
                  <p className="font-medium text-sm text-slate-900">{selectedSuggestion.title}</p>
                  <p className="text-xs text-slate-500 mt-1">{selectedSuggestion.description}</p>
                </div>
              )}

              {/* Pattern options for email_link suggestions */}
              {selectedSuggestion?.suggestion_type === "email_link" && (
                <div className="space-y-3">
                  <Label className="text-sm font-medium">Create learning patterns</Label>

                  <div className="space-y-3 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                    <div className="flex items-center gap-2">
                      <Checkbox
                        id="createSenderPattern"
                        checked={createSenderPattern}
                        onCheckedChange={(checked) => setCreateSenderPattern(checked === true)}
                      />
                      <Label htmlFor="createSenderPattern" className="text-sm text-emerald-900">
                        Always link emails from this sender to this project
                      </Label>
                    </div>

                    <div className="flex items-center gap-2">
                      <Checkbox
                        id="createDomainPattern"
                        checked={createDomainPattern}
                        onCheckedChange={(checked) => setCreateDomainPattern(checked === true)}
                      />
                      <Label htmlFor="createDomainPattern" className="text-sm text-emerald-900">
                        Always link emails from this domain to this project
                      </Label>
                    </div>

                    {(createSenderPattern || createDomainPattern) && (
                      <div className="space-y-2 pt-2">
                        <Label className="text-xs text-emerald-800">Pattern notes (optional)</Label>
                        <Input
                          value={approvePatternNotes}
                          onChange={(e) => setApprovePatternNotes(e.target.value)}
                          placeholder="e.g., Main client contact"
                          className="bg-white"
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Contact role for new_contact suggestions */}
              {selectedSuggestion?.suggestion_type === "new_contact" && (
                <div className="space-y-2">
                  <Label>Contact Role</Label>
                  <Select value={approveContactRole} onValueChange={setApproveContactRole}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select role (optional)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">-- Not specified --</SelectItem>
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
              )}
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  // Just approve without patterns
                  if (selectedSuggestion) {
                    approveMutation.mutate({ suggestionId: selectedSuggestion.suggestion_id });
                  }
                  setApproveContextDialogOpen(false);
                }}
                disabled={approveMutation.isPending || approveWithContextMutation.isPending}
              >
                Just Approve
              </Button>
              <Button
                onClick={() => {
                  if (selectedSuggestion) {
                    approveWithContextMutation.mutate({
                      suggestionId: selectedSuggestion.suggestion_id,
                      create_sender_pattern: createSenderPattern,
                      create_domain_pattern: createDomainPattern,
                      contact_role: approveContactRole || undefined,
                      pattern_notes: approvePatternNotes || undefined,
                    });
                  }
                }}
                disabled={approveMutation.isPending || approveWithContextMutation.isPending || (!createSenderPattern && !createDomainPattern && !approveContactRole)}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {approveWithContextMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Check className="h-4 w-4 mr-2" />
                )}
                Approve & Learn
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

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

        {/* Preview Changes Sheet */}
        <Sheet open={previewSheetOpen} onOpenChange={setPreviewSheetOpen}>
          <SheetContent className="w-[400px] sm:w-[540px] sm:max-w-lg">
            <SheetHeader>
              <SheetTitle className="flex items-center gap-2">
                <Eye className="h-5 w-5" />
                Preview Changes
              </SheetTitle>
              <SheetDescription>
                What will happen when this suggestion is approved
              </SheetDescription>
            </SheetHeader>
            <div className="mt-6 space-y-4">
              {loadingPreview ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
                </div>
              ) : previewData ? (
                <>
                  {/* Actionable indicator */}
                  <div className="flex items-center gap-2">
                    {previewData.is_actionable ? (
                      <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
                        <Check className="h-3 w-3 mr-1" />
                        Actionable
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="bg-slate-50 text-slate-600 border-slate-200">
                        <Info className="h-3 w-3 mr-1" />
                        Info Only
                      </Badge>
                    )}
                    <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                      {previewData.action}
                    </Badge>
                  </div>

                  {/* Summary */}
                  <div>
                    <Label className="text-xs text-slate-500">Summary</Label>
                    <p className="text-sm text-slate-900 mt-1">{previewData.summary}</p>
                  </div>

                  {/* Target Table */}
                  {previewData.table && (
                    <div>
                      <Label className="text-xs text-slate-500">Target Table</Label>
                      <code className="block mt-1 px-2 py-1 bg-slate-100 rounded text-sm text-slate-700">
                        {previewData.table}
                      </code>
                    </div>
                  )}

                  {/* Changes */}
                  {previewData.changes && previewData.changes.length > 0 && (
                    <div>
                      <Label className="text-xs text-slate-500">Field Changes</Label>
                      <div className="mt-2 space-y-2">
                        {previewData.changes.map((change, idx) => (
                          <div key={idx} className="p-2 bg-slate-50 rounded border text-sm">
                            <span className="font-medium text-slate-700">{change.field}</span>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-red-600 line-through">
                                {change.old_value !== null && change.old_value !== undefined
                                  ? String(change.old_value)
                                  : "(empty)"}
                              </span>
                              <span className="text-slate-400">→</span>
                              <span className="text-emerald-600">
                                {change.new_value !== null && change.new_value !== undefined
                                  ? String(change.new_value)
                                  : "(empty)"}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-slate-500 text-center py-8">No preview available</p>
              )}
            </div>
          </SheetContent>
        </Sheet>

        {/* Source Content Sheet */}
        <Sheet open={sourceSheetOpen} onOpenChange={setSourceSheetOpen}>
          <SheetContent className="w-[400px] sm:w-[640px] sm:max-w-2xl">
            <SheetHeader>
              <SheetTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Source Content
              </SheetTitle>
              <SheetDescription>
                The original content that triggered this suggestion
              </SheetDescription>
            </SheetHeader>
            <div className="mt-6 space-y-4">
              {loadingSource ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
                </div>
              ) : sourceData ? (
                <>
                  {/* Source Type */}
                  <div className="flex items-center gap-2">
                    {sourceData.source_type === "email" ? (
                      <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                        <Mail className="h-3 w-3 mr-1" />
                        Email
                      </Badge>
                    ) : sourceData.source_type === "transcript" ? (
                      <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
                        <FileText className="h-3 w-3 mr-1" />
                        Transcript
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="bg-slate-50 text-slate-600 border-slate-200">
                        {sourceData.source_type || "Unknown"}
                      </Badge>
                    )}
                  </div>

                  {/* Metadata */}
                  {sourceData.source_type === "email" && sourceData.metadata && (
                    <div className="space-y-3">
                      {sourceData.metadata.subject && (
                        <div>
                          <Label className="text-xs text-slate-500">Subject</Label>
                          <p className="font-medium text-slate-900">{sourceData.metadata.subject}</p>
                        </div>
                      )}
                      <div className="grid grid-cols-2 gap-4">
                        {sourceData.metadata.sender && (
                          <div>
                            <Label className="text-xs text-slate-500">From</Label>
                            <p className="text-sm text-slate-700">{sourceData.metadata.sender}</p>
                          </div>
                        )}
                        {sourceData.metadata.date && (
                          <div>
                            <Label className="text-xs text-slate-500">Date</Label>
                            <p className="text-sm text-slate-700">{sourceData.metadata.date}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {sourceData.source_type === "transcript" && sourceData.metadata && (
                    <div className="space-y-3">
                      {sourceData.metadata.title && (
                        <div>
                          <Label className="text-xs text-slate-500">Meeting Title</Label>
                          <p className="font-medium text-slate-900">{sourceData.metadata.title}</p>
                        </div>
                      )}
                      <div className="grid grid-cols-2 gap-4">
                        {sourceData.metadata.date && (
                          <div>
                            <Label className="text-xs text-slate-500">Date</Label>
                            <p className="text-sm text-slate-700">{sourceData.metadata.date}</p>
                          </div>
                        )}
                        {sourceData.metadata.filename && (
                          <div>
                            <Label className="text-xs text-slate-500">File</Label>
                            <p className="text-sm text-slate-700 truncate">{sourceData.metadata.filename}</p>
                          </div>
                        )}
                      </div>
                      {sourceData.metadata.summary && (
                        <div>
                          <Label className="text-xs text-slate-500">Summary</Label>
                          <p className="text-sm text-slate-700">{sourceData.metadata.summary}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Content */}
                  {sourceData.content ? (
                    <div>
                      <Label className="text-xs text-slate-500">Content</Label>
                      <div className="mt-2 p-3 bg-slate-50 rounded-lg border text-sm text-slate-700 max-h-[400px] overflow-y-auto whitespace-pre-wrap">
                        {sourceData.content}
                      </div>
                    </div>
                  ) : (
                    <div className="p-4 bg-amber-50 rounded-lg border border-amber-200 text-sm text-amber-700">
                      {sourceData.metadata?.note || "No content available for this source"}
                    </div>
                  )}
                </>
              ) : (
                <p className="text-slate-500 text-center py-8">No source data available</p>
              )}
            </div>
          </SheetContent>
        </Sheet>

        {/* Rollback Confirmation Dialog */}
        <AlertDialog open={rollbackConfirmOpen} onOpenChange={setRollbackConfirmOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Undo Suggestion</AlertDialogTitle>
              <AlertDialogDescription>
                This will rollback the changes made by this approved suggestion. The database will be restored to its previous state.
                {selectedSuggestion && (
                  <span className="block mt-2 text-slate-700 font-medium">
                    {selectedSuggestion.title}
                  </span>
                )}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => setSelectedSuggestion(null)}>
                Cancel
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={() => {
                  if (selectedSuggestion) {
                    rollbackMutation.mutate(selectedSuggestion.suggestion_id);
                  }
                }}
                disabled={rollbackMutation.isPending}
                className="bg-amber-600 hover:bg-amber-700"
              >
                {rollbackMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <RotateCcw className="h-4 w-4 mr-2" />
                )}
                Undo Changes
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
}
