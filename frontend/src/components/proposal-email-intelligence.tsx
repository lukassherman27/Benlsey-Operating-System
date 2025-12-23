"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
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
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import {
  Mail,
  Calendar,
  User,
  MessageSquare,
  TrendingUp,
  Check,
  X,
  RefreshCw,
  Loader2,
  Link as LinkIcon,
  Search,
} from "lucide-react";

// Email categories matching backend schema
const EMAIL_CATEGORIES = [
  { value: "contract", label: "Contract" },
  { value: "rfi", label: "RFI" },
  { value: "proposal", label: "Proposal" },
  { value: "invoice", label: "Invoice" },
  { value: "meeting", label: "Meeting" },
  { value: "technical", label: "Technical" },
  { value: "administrative", label: "Administrative" },
  { value: "financial", label: "Financial" },
  { value: "general", label: "General" },
];

// Category color mapping
const CATEGORY_COLORS: Record<string, string> = {
  contract: "bg-purple-100 text-purple-800 border-purple-200",
  rfi: "bg-orange-100 text-orange-800 border-orange-200",
  proposal: "bg-blue-100 text-blue-800 border-blue-200",
  invoice: "bg-green-100 text-green-800 border-green-200",
  meeting: "bg-yellow-100 text-yellow-800 border-yellow-200",
  technical: "bg-cyan-100 text-cyan-800 border-cyan-200",
  administrative: "bg-gray-100 text-gray-800 border-gray-200",
  financial: "bg-emerald-100 text-emerald-800 border-emerald-200",
  general: "bg-slate-100 text-slate-800 border-slate-200",
};

interface ProposalEmailIntelligenceProps {
  projectCode: string;
}

interface EmailWithIntelligence {
  email_id: number;
  email_subject: string | null;
  email_from: string | null;
  email_date: string | null;
  key_information: string | null;
  action_items: string | null;
  client_sentiment: string | null;
  status_update: string | null;
  ai_category?: string | null;
  human_approved?: number;
}

export function ProposalEmailIntelligence({ projectCode }: ProposalEmailIntelligenceProps) {
  const queryClient = useQueryClient();
  const [recategorizeEmail, setRecategorizeEmail] = useState<EmailWithIntelligence | null>(null);
  const [newCategory, setNewCategory] = useState<string>("");
  const [rejectionReason, setRejectionReason] = useState<string>("");
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [projectSearch, setProjectSearch] = useState<string>("");

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["proposalEmailIntelligence", projectCode],
    queryFn: () => api.getProposalEmailIntelligence(projectCode),
    enabled: !!projectCode,
  });

  // Fetch projects for linking dropdown
  const { data: projectsData } = useQuery({
    queryKey: ["projectsForLinking"],
    queryFn: () => api.getProjectsForLinking(200),
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  });

  const projects = projectsData?.projects || [];
  const filteredProjects = projectSearch
    ? projects.filter(
        (p) =>
          p.code.toLowerCase().includes(projectSearch.toLowerCase()) ||
          p.name?.toLowerCase().includes(projectSearch.toLowerCase())
      )
    : projects.slice(0, 50); // Show first 50 if no search

  // Approve category mutation
  const approveMutation = useMutation({
    mutationFn: (emailId: number) => api.approveEmailCategory(emailId),
    onSuccess: () => {
      toast.success("Category approved", {
        description: "AI categorization confirmed. Training data logged.",
      });
      queryClient.invalidateQueries({ queryKey: ["proposalEmailIntelligence", projectCode] });
    },
    onError: (error: Error) => {
      toast.error("Failed to approve", { description: error.message });
    },
  });

  // Reject category mutation
  const rejectMutation = useMutation({
    mutationFn: ({ emailId, category, reason }: { emailId: number; category: string; reason?: string }) =>
      api.rejectEmailCategory(emailId, category, reason),
    onSuccess: (data) => {
      toast.success("Category corrected", {
        description: `Changed to "${data.new_category}". Training data logged.`,
      });
      setRecategorizeEmail(null);
      setNewCategory("");
      setRejectionReason("");
      setSelectedProject("");
      queryClient.invalidateQueries({ queryKey: ["proposalEmailIntelligence", projectCode] });
    },
    onError: (error: Error) => {
      toast.error("Failed to update category", { description: error.message });
    },
  });

  // Link to project mutation
  const linkMutation = useMutation({
    mutationFn: ({ emailId, projectCode }: { emailId: number; projectCode: string }) =>
      api.linkEmailToProject(emailId, projectCode, 1.0),
    onSuccess: () => {
      toast.success("Email linked", {
        description: "Email linked to project successfully.",
      });
      queryClient.invalidateQueries({ queryKey: ["proposalEmailIntelligence", projectCode] });
    },
    onError: (error: Error) => {
      toast.error("Failed to link email", { description: error.message });
    },
  });

  const emails = data?.emails || [];

  const handleApprove = (email: EmailWithIntelligence) => {
    approveMutation.mutate(email.email_id);
  };

  const handleReject = (email: EmailWithIntelligence) => {
    setRecategorizeEmail(email);
    setNewCategory(email.ai_category || "general");
  };

  const handleConfirmRecategorize = () => {
    if (!recategorizeEmail || !newCategory) return;

    // First update category
    rejectMutation.mutate(
      {
        emailId: recategorizeEmail.email_id,
        category: newCategory,
        reason: rejectionReason || undefined,
      },
      {
        onSuccess: () => {
          // If a different project was selected, link it
          if (selectedProject && selectedProject !== projectCode) {
            linkMutation.mutate({
              emailId: recategorizeEmail.email_id,
              projectCode: selectedProject,
            });
          }
        },
      }
    );
  };

  const getCategoryBadge = (category: string | null | undefined) => {
    const cat = category || "general";
    const colorClass = CATEGORY_COLORS[cat] || CATEGORY_COLORS.general;
    return (
      <Badge variant="outline" className={`${colorClass} text-xs`}>
        {cat.replace(/_/g, " ")}
      </Badge>
    );
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">Email Intelligence</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">Loading email insights...</div>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">Email Intelligence</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-red-600">Failed to load email insights</div>
        </CardContent>
      </Card>
    );
  }

  if (emails.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">Email Intelligence</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">
            No email intelligence available for this proposal
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium">Email Intelligence</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="gap-1">
                <Mail className="h-3 w-3" />
                {emails.length} {emails.length === 1 ? "email" : "emails"}
              </Badge>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => refetch()}
                disabled={isFetching}
                title="Refresh emails"
              >
                <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {emails.map((email: EmailWithIntelligence) => (
              <div
                key={email.email_id}
                className="rounded-lg border bg-card p-4 space-y-3"
              >
                {/* Email Header */}
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                      <p className="font-semibold text-sm">{email.email_subject}</p>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {email.email_from}
                      </div>
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(email.email_date || "").toLocaleDateString("en-US", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        })}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {email.status_update && (
                      <Badge variant="outline" className="text-xs">
                        {email.status_update}
                      </Badge>
                    )}
                    {getCategoryBadge(email.ai_category)}
                  </div>
                </div>

                {/* AI Context */}
                {email.key_information && (
                  <div className="rounded-md bg-blue-50 dark:bg-blue-950/30 p-3">
                    <div className="flex items-start gap-2">
                      <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-xs font-medium text-blue-900 dark:text-blue-100 mb-1">
                          AI Insights
                        </p>
                        <p className="text-xs text-blue-800 dark:text-blue-200">
                          {email.key_information}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Action Items */}
                {email.action_items && (
                  <div>
                    <p className="text-xs font-medium text-orange-600 dark:text-orange-400 mb-2">
                      Action Items:
                    </p>
                    <div className="text-xs text-foreground flex gap-2 p-2 rounded bg-orange-50 dark:bg-orange-950/30">
                      <span className="text-orange-600 dark:text-orange-400">→</span>
                      <span>{email.action_items}</span>
                    </div>
                  </div>
                )}

                {/* Sentiment */}
                {email.client_sentiment && (
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-3 w-3 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">Sentiment:</span>
                    <Badge
                      variant="outline"
                      className={
                        email.client_sentiment === "positive"
                          ? "bg-green-50 text-green-700 border-green-200"
                          : email.client_sentiment === "negative"
                          ? "bg-red-50 text-red-700 border-red-200"
                          : "bg-slate-50 text-slate-700 border-slate-200"
                      }
                    >
                      {email.client_sentiment}
                    </Badge>
                  </div>
                )}

                {/* Categorization Actions */}
                <div className="flex items-center justify-between pt-2 border-t">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>AI Suggested:</span>
                    {getCategoryBadge(email.ai_category)}
                    {email.human_approved === 1 && (
                      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 text-[10px]">
                        <Check className="h-2.5 w-2.5 mr-1" />
                        Approved
                      </Badge>
                    )}
                  </div>
                  {email.human_approved !== 1 && (
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 text-xs border-green-200 text-green-700 hover:bg-green-50"
                        onClick={() => handleApprove(email)}
                        disabled={approveMutation.isPending}
                      >
                        {approveMutation.isPending && approveMutation.variables === email.email_id ? (
                          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        ) : (
                          <Check className="h-3 w-3 mr-1" />
                        )}
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 text-xs border-red-200 text-red-700 hover:bg-red-50"
                        onClick={() => handleReject(email)}
                      >
                        <X className="h-3 w-3 mr-1" />
                        Recategorize
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recategorize Dialog */}
      <Dialog open={!!recategorizeEmail} onOpenChange={() => setRecategorizeEmail(null)}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Correct Email Category</DialogTitle>
            <DialogDescription>
              Help train the AI by selecting the correct category. This feedback improves future categorization.
            </DialogDescription>
          </DialogHeader>
          {recategorizeEmail && (
            <div className="space-y-4 py-4">
              <div className="p-3 bg-muted rounded-lg">
                <p className="text-sm font-medium truncate">{recategorizeEmail.email_subject}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Current: {recategorizeEmail.ai_category || "general"}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="category">Correct Category</Label>
                <Select value={newCategory} onValueChange={setNewCategory}>
                  <SelectTrigger id="category">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {EMAIL_CATEGORIES.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>
                        {cat.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="project">Link to Project (optional)</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="project-search"
                    placeholder="Search projects..."
                    value={projectSearch}
                    onChange={(e) => setProjectSearch(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <ScrollArea className="h-[120px] border rounded-md">
                  <div className="p-2 space-y-1">
                    <button
                      type="button"
                      className={`w-full text-left px-2 py-1.5 text-sm rounded hover:bg-muted ${
                        selectedProject === "" ? "bg-muted font-medium" : ""
                      }`}
                      onClick={() => setSelectedProject("")}
                    >
                      Keep current project ({projectCode})
                    </button>
                    {filteredProjects.map((p) => (
                      <button
                        key={p.code}
                        type="button"
                        className={`w-full text-left px-2 py-1.5 text-sm rounded hover:bg-muted ${
                          selectedProject === p.code ? "bg-muted font-medium" : ""
                        }`}
                        onClick={() => setSelectedProject(p.code)}
                      >
                        <span className="font-medium">{p.code}</span>
                        <span className="text-muted-foreground ml-2 truncate">
                          {p.name}
                        </span>
                        {p.is_active_project === 1 && (
                          <Badge variant="outline" className="ml-2 text-[10px]">
                            Active
                          </Badge>
                        )}
                      </button>
                    ))}
                    {filteredProjects.length === 0 && (
                      <p className="text-xs text-muted-foreground text-center py-2">
                        No projects found
                      </p>
                    )}
                  </div>
                </ScrollArea>
                {selectedProject && selectedProject !== projectCode && (
                  <p className="text-xs text-blue-600">
                    <LinkIcon className="h-3 w-3 inline mr-1" />
                    Will link email to: {selectedProject}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="reason">Why is this the correct category? (optional)</Label>
                <Textarea
                  id="reason"
                  placeholder="Helps train the AI..."
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  className="min-h-[80px]"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setRecategorizeEmail(null)}>
              Cancel
            </Button>
            <Button
              onClick={handleConfirmRecategorize}
              disabled={!newCategory || rejectMutation.isPending}
            >
              {rejectMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Save Correction
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
