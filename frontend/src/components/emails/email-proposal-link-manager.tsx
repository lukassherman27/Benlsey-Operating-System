"use client";

import { useState, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, EmailValidationItem } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
  Search,
  RefreshCw,
  Link as LinkIcon,
  Unlink,
  Check,
  X,
  Mail,
  Calendar,
  User,
  Paperclip,
  AlertCircle,
  Loader2,
  Filter,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Filter options
const FILTER_OPTIONS = [
  { value: "all", label: "All Emails" },
  { value: "unlinked", label: "Unlinked" },
  { value: "low_confidence", label: "Low Confidence (<70%)" },
];

// Confidence color mapping
const getConfidenceColor = (confidence: number | null | undefined) => {
  if (!confidence) return "bg-gray-100 text-gray-700 border-gray-200";
  if (confidence >= 0.9) return "bg-green-100 text-green-700 border-green-200";
  if (confidence >= 0.7) return "bg-yellow-100 text-yellow-700 border-yellow-200";
  return "bg-red-100 text-red-700 border-red-200";
};

export default function EmailProposalLinkManager() {
  const queryClient = useQueryClient();
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedEmail, setSelectedEmail] = useState<EmailValidationItem | null>(null);
  const [linkProjectCode, setLinkProjectCode] = useState<string>("");
  const [linkReason, setLinkReason] = useState<string>("");
  const [projectSearch, setProjectSearch] = useState<string>("");

  // Fetch validation queue
  const {
    data: queueData,
    isLoading,
    isError,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["emailValidationQueue", filterStatus],
    queryFn: () =>
      api.getEmailValidationQueue({
        status: filterStatus as "unlinked" | "low_confidence" | "all",
        limit: 100,
      }),
  });

  // Fetch projects for linking
  const { data: projectsData } = useQuery({
    queryKey: ["projectsForLinking"],
    queryFn: () => api.getProjectsForLinking(500),
    staleTime: 1000 * 60 * 5,
  });

  const projects = projectsData?.projects || [];
  const filteredProjects = projectSearch
    ? projects.filter(
        (p) =>
          p.code.toLowerCase().includes(projectSearch.toLowerCase()) ||
          p.name?.toLowerCase().includes(projectSearch.toLowerCase())
      )
    : projects.slice(0, 50);

  // Update email link mutation
  const updateLinkMutation = useMutation({
    mutationFn: ({
      emailId,
      projectCode,
      reason,
    }: {
      emailId: number;
      projectCode: string;
      reason: string;
    }) => api.updateEmailLink(emailId, { project_code: projectCode, reason }),
    onSuccess: () => {
      toast.success("Email linked", {
        description: "Email linked to project. Training data logged.",
      });
      setSelectedEmail(null);
      setLinkProjectCode("");
      setLinkReason("");
      queryClient.invalidateQueries({ queryKey: ["emailValidationQueue"] });
    },
    onError: (error: Error) => {
      toast.error("Failed to link email", { description: error.message });
    },
  });

  // Confirm link mutation
  const confirmLinkMutation = useMutation({
    mutationFn: (emailId: number) => api.confirmEmailLink(emailId),
    onSuccess: () => {
      toast.success("Link confirmed", {
        description: "AI link confirmed. Training data logged.",
      });
      queryClient.invalidateQueries({ queryKey: ["emailValidationQueue"] });
    },
    onError: (error: Error) => {
      toast.error("Failed to confirm", { description: error.message });
    },
  });

  // Unlink mutation
  const unlinkMutation = useMutation({
    mutationFn: ({ emailId, reason }: { emailId: number; reason: string }) =>
      api.unlinkEmailIntelligence(emailId, reason),
    onSuccess: () => {
      toast.success("Email unlinked", {
        description: "Link removed. Training data logged.",
      });
      queryClient.invalidateQueries({ queryKey: ["emailValidationQueue"] });
    },
    onError: (error: Error) => {
      toast.error("Failed to unlink", { description: error.message });
    },
  });

  const emails = queueData?.emails || [];
  const counts = queueData?.counts || {
    unlinked: 0,
    low_confidence: 0,
    total_linked: 0,
    returned: 0,
  };

  // Filter emails by search query
  const filteredEmails = useMemo(() => {
    if (!searchQuery.trim()) return emails;
    const query = searchQuery.toLowerCase();
    return emails.filter(
      (email) =>
        email.subject?.toLowerCase().includes(query) ||
        email.sender_email?.toLowerCase().includes(query) ||
        email.sender_name?.toLowerCase().includes(query) ||
        email.project_code?.toLowerCase().includes(query)
    );
  }, [emails, searchQuery]);

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return "Unknown date";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return "Invalid date";
    }
  };

  const handleManualLink = (email: EmailValidationItem) => {
    setSelectedEmail(email);
    setLinkProjectCode(email.project_code || "");
    setLinkReason("");
  };

  const handleConfirmLink = (email: EmailValidationItem) => {
    confirmLinkMutation.mutate(email.email_id);
  };

  const handleUnlink = (email: EmailValidationItem) => {
    unlinkMutation.mutate({
      emailId: email.email_id,
      reason: "Incorrect link - removed by user",
    });
  };

  const handleSaveLink = () => {
    if (!selectedEmail || !linkProjectCode) return;
    updateLinkMutation.mutate({
      emailId: selectedEmail.email_id,
      projectCode: linkProjectCode,
      reason: linkReason || `Manually linked to ${linkProjectCode}`,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Email-Project Link Manager</h2>
          <p className="text-muted-foreground">
            Review and correct email-project links to improve AI accuracy
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card
          className={cn(
            "cursor-pointer hover:border-primary transition",
            filterStatus === "unlinked" && "border-primary bg-primary/5"
          )}
          onClick={() => setFilterStatus("unlinked")}
        >
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Unlinked</p>
                <p className="text-2xl font-bold">{counts.unlinked}</p>
              </div>
              <AlertCircle className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        <Card
          className={cn(
            "cursor-pointer hover:border-primary transition",
            filterStatus === "low_confidence" && "border-primary bg-primary/5"
          )}
          onClick={() => setFilterStatus("low_confidence")}
        >
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Low Confidence</p>
                <p className="text-2xl font-bold">{counts.low_confidence}</p>
              </div>
              <AlertCircle className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>
        <Card
          className={cn(
            "cursor-pointer hover:border-primary transition",
            filterStatus === "all" && "border-primary bg-primary/5"
          )}
          onClick={() => setFilterStatus("all")}
        >
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Linked</p>
                <p className="text-2xl font-bold">{counts.total_linked}</p>
              </div>
              <LinkIcon className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter & Search */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <CardTitle>Email Validation Queue</CardTitle>
              <CardDescription>
                {filteredEmails.length} emails{" "}
                {filterStatus !== "all" && `(${filterStatus.replace("_", " ")})`}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-[180px]">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Filter by..." />
                </SelectTrigger>
                <SelectContent>
                  {FILTER_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="relative mt-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by subject, sender, or project..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-6">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : isError ? (
            <div className="p-6 text-center text-red-500">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              <p>Failed to load emails. Please try again.</p>
            </div>
          ) : filteredEmails.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">
              <Mail className="h-12 w-12 mx-auto mb-4 opacity-20" />
              <p className="text-lg font-medium">No emails found</p>
              <p className="text-sm mt-1">Try adjusting your filter or search</p>
            </div>
          ) : (
            <ScrollArea className="max-h-[500px]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[40%]">Email</TableHead>
                    <TableHead className="w-[20%]">Current Link</TableHead>
                    <TableHead className="w-[15%]">Confidence</TableHead>
                    <TableHead className="w-[25%] text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEmails.map((email) => (
                    <TableRow key={email.email_id} className="group">
                      <TableCell>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                            <p className="font-medium text-sm truncate max-w-[300px]">
                              {email.subject || "(No subject)"}
                            </p>
                            {email.has_attachments === 1 && (
                              <Paperclip className="h-3 w-3 text-muted-foreground" />
                            )}
                          </div>
                          <div className="flex items-center gap-3 text-xs text-muted-foreground ml-6">
                            <span className="flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {email.sender_email || email.sender_name || "Unknown"}
                            </span>
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {formatDate(email.date)}
                            </span>
                          </div>
                          {email.category && (
                            <div className="ml-6">
                              <Badge variant="outline" className="text-[10px]">
                                {email.category}
                              </Badge>
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {email.project_code ? (
                          <div className="space-y-1">
                            <Badge variant="outline" className="font-mono">
                              <LinkIcon className="h-3 w-3 mr-1" />
                              {email.project_code}
                            </Badge>
                            {email.project_name && (
                              <p className="text-xs text-muted-foreground truncate max-w-[150px]">
                                {email.project_name}
                              </p>
                            )}
                          </div>
                        ) : (
                          <Badge variant="outline" className="text-orange-600 border-orange-200">
                            <AlertCircle className="h-3 w-3 mr-1" />
                            Unlinked
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {email.confidence != null ? (
                          <Badge
                            variant="outline"
                            className={getConfidenceColor(email.confidence)}
                          >
                            {Math.round(email.confidence * 100)}%
                          </Badge>
                        ) : (
                          <span className="text-xs text-muted-foreground">-</span>
                        )}
                        {email.link_method && (
                          <p className="text-[10px] text-muted-foreground mt-1">
                            {email.link_method}
                          </p>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          {email.project_code ? (
                            <>
                              {email.confidence != null && email.confidence < 1.0 && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="h-7 text-xs border-green-200 text-green-700 hover:bg-green-50"
                                  onClick={() => handleConfirmLink(email)}
                                  disabled={confirmLinkMutation.isPending}
                                >
                                  <Check className="h-3 w-3 mr-1" />
                                  Confirm
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7 text-xs"
                                onClick={() => handleManualLink(email)}
                              >
                                <LinkIcon className="h-3 w-3 mr-1" />
                                Relink
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7 text-xs border-red-200 text-red-700 hover:bg-red-50"
                                onClick={() => handleUnlink(email)}
                                disabled={unlinkMutation.isPending}
                              >
                                <Unlink className="h-3 w-3 mr-1" />
                                Unlink
                              </Button>
                            </>
                          ) : (
                            <Button
                              size="sm"
                              className="h-7 text-xs"
                              onClick={() => handleManualLink(email)}
                            >
                              <LinkIcon className="h-3 w-3 mr-1" />
                              Link to Project
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* Manual Link Dialog */}
      <Dialog open={!!selectedEmail} onOpenChange={() => setSelectedEmail(null)}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Link Email to Project</DialogTitle>
            <DialogDescription>
              Select a project to link this email to. This helps train the AI for better linking.
            </DialogDescription>
          </DialogHeader>
          {selectedEmail && (
            <div className="space-y-4 py-4">
              {/* Email Preview */}
              <div className="p-3 bg-muted rounded-lg space-y-2">
                <p className="text-sm font-medium line-clamp-2">
                  {selectedEmail.subject || "(No subject)"}
                </p>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <span>From: {selectedEmail.sender_email}</span>
                  <span>{formatDate(selectedEmail.date)}</span>
                </div>
                {selectedEmail.snippet && (
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {selectedEmail.snippet}
                  </p>
                )}
              </div>

              {/* Project Search */}
              <div className="space-y-2">
                <Label>Select Project</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search projects..."
                    value={projectSearch}
                    onChange={(e) => setProjectSearch(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <ScrollArea className="h-[150px] border rounded-md">
                  <div className="p-2 space-y-1">
                    {filteredProjects.map((p) => (
                      <button
                        key={p.code}
                        type="button"
                        className={cn(
                          "w-full text-left px-3 py-2 text-sm rounded hover:bg-muted",
                          linkProjectCode === p.code && "bg-primary/10 border border-primary"
                        )}
                        onClick={() => setLinkProjectCode(p.code)}
                      >
                        <span className="font-medium">{p.code}</span>
                        <span className="text-muted-foreground ml-2">{p.name}</span>
                        {p.is_active_project === 1 && (
                          <Badge variant="outline" className="ml-2 text-[10px]">
                            Active
                          </Badge>
                        )}
                      </button>
                    ))}
                    {filteredProjects.length === 0 && (
                      <p className="text-xs text-muted-foreground text-center py-4">
                        No projects found
                      </p>
                    )}
                  </div>
                </ScrollArea>
              </div>

              {/* Reason */}
              <div className="space-y-2">
                <Label htmlFor="link-reason">Why is this the correct project? (optional)</Label>
                <Textarea
                  id="link-reason"
                  placeholder="e.g., Email mentions project name, client name matches..."
                  value={linkReason}
                  onChange={(e) => setLinkReason(e.target.value)}
                  className="min-h-[80px]"
                />
                <p className="text-xs text-muted-foreground">
                  This helps train the AI to make better links in the future.
                </p>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedEmail(null)}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveLink}
              disabled={!linkProjectCode || updateLinkMutation.isPending}
            >
              {updateLinkMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              <LinkIcon className="h-4 w-4 mr-2" />
              Link Email
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
