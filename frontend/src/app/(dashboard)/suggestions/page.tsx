"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, SuggestionItem, NewContactSuggestion, ProjectAliasSuggestion } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  Pencil,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";

type SuggestionType = "all" | "new_contact" | "project_alias";
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

  // Dialog states
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [bulkRejectDialogOpen, setBulkRejectDialogOpen] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState<SuggestionItem | null>(null);

  // Edit form state
  const [contactForm, setContactForm] = useState<ContactFormData>({
    name: "",
    email: "",
    company: "",
    role: "",
    related_project: "",
    notes: "",
  });

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
      toast.success(data.message || "Contact added successfully");
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
      setEditDialogOpen(false);
      setSelectedSuggestion(null);
      // Reset form
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
    },
    onError: (error: Error) => {
      toast.error(`Failed to reject: ${error.message}`);
    },
  });

  // Bulk reject duplicates mutation
  const bulkRejectMutation = useMutation({
    mutationFn: () => api.bulkApproveAISuggestions(0.8), // TODO: Need bulk reject API
    onSuccess: (data) => {
      toast.success(`Processed ${data.approved} suggestions`);
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["suggestions-stats"] });
      setBulkRejectDialogOpen(false);
    },
    onError: (error: Error) => {
      toast.error(`Failed: ${error.message}`);
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
    if (parsed && suggestion.field_name === "new_contact") {
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

  // Get confidence color
  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return "bg-emerald-100 text-emerald-700 border-emerald-200";
    if (confidence >= 0.7) return "bg-amber-100 text-amber-700 border-amber-200";
    return "bg-red-100 text-red-700 border-red-200";
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
            Review, edit, and approve AI-extracted contacts. Click Edit to add context before approving.
          </p>
          <p className="text-sm text-amber-600 mt-2">
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
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
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
              <div className="space-y-3">
                {suggestions.map((suggestion) => {
                  const parsed = parseSuggestedValue(suggestion);
                  const isContact = suggestion.field_name === "new_contact";

                  return (
                    <Card
                      key={suggestion.suggestion_id}
                      className="border hover:border-slate-300 transition-colors"
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between gap-4">
                          {/* Left: Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              {isContact ? (
                                <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs">
                                  <UserPlus className="h-3 w-3 mr-1" />
                                  Contact
                                </Badge>
                              ) : (
                                <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200 text-xs">
                                  <Link2 className="h-3 w-3 mr-1" />
                                  Alias
                                </Badge>
                              )}
                              <Badge
                                variant="outline"
                                className={`text-xs ${getConfidenceColor(suggestion.confidence)}`}
                              >
                                {Math.round(suggestion.confidence * 100)}%
                              </Badge>
                            </div>

                            {/* Contact Info */}
                            {isContact && parsed ? (
                              <div className="flex items-center gap-4 text-sm">
                                <span className="font-medium text-slate-900">
                                  {(parsed as NewContactSuggestion).name || "Unknown"}
                                </span>
                                <span className="text-slate-500">
                                  {(parsed as NewContactSuggestion).email}
                                </span>
                                {(parsed as NewContactSuggestion).company && (
                                  <span className="text-slate-400">
                                    {(parsed as NewContactSuggestion).company}
                                  </span>
                                )}
                              </div>
                            ) : !isContact && parsed ? (
                              <div className="flex items-center gap-2 text-sm">
                                <code className="bg-slate-100 px-2 py-0.5 rounded text-slate-700">
                                  {(parsed as ProjectAliasSuggestion).alias}
                                </code>
                                <span className="text-slate-400">→</span>
                                <code className="bg-purple-100 px-2 py-0.5 rounded text-purple-700">
                                  {(parsed as ProjectAliasSuggestion).project_code}
                                </code>
                              </div>
                            ) : (
                              <pre className="text-xs text-slate-500 truncate">
                                {typeof suggestion.suggested_value === "string"
                                  ? suggestion.suggested_value
                                  : JSON.stringify(suggestion.suggested_value)}
                              </pre>
                            )}

                            {suggestion.evidence && (
                              <p className="text-xs text-slate-400 mt-1 truncate">
                                From: {suggestion.evidence}
                              </p>
                            )}
                          </div>

                          {/* Right: Actions */}
                          <div className="flex items-center gap-2">
                            {isContact && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openEditDialog(suggestion)}
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
      </div>
    </div>
  );
}
