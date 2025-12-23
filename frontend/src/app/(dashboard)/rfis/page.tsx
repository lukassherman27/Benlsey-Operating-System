"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { format, formatDistanceToNow } from "date-fns";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import {
  HelpCircle,
  Search,
  Filter,
  Clock,
  CheckCircle2,
  AlertTriangle,
  MessageSquare,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  Send,
  FileQuestion,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { toast } from "sonner";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface RFI {
  id: number;
  rfi_number?: string;
  subject: string;
  description?: string;
  project_code?: string;
  project_name?: string;
  status: string;
  priority?: string;
  requested_by?: string;
  assigned_to?: string;
  created_at: string;
  due_date?: string;
  responded_at?: string;
  closed_at?: string;
  response?: string;
  days_open?: number;
  is_overdue?: boolean;
}

interface RFIStats {
  total: number;
  pending: number;
  responded: number;
  closed: number;
  overdue: number;
  avg_response_days?: number;
}

// Fetch RFIs
async function fetchRFIs(params?: { status?: string; project_code?: string }): Promise<{ rfis: RFI[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.append("status", params.status);
  if (params?.project_code) searchParams.append("project_code", params.project_code);

  const response = await fetch(`${API_BASE_URL}/api/rfis?${searchParams}`);
  if (!response.ok) throw new Error("Failed to fetch RFIs");
  return response.json();
}

// Fetch RFI stats
async function fetchRFIStats(): Promise<RFIStats> {
  const response = await fetch(`${API_BASE_URL}/api/rfis/stats`);
  if (!response.ok) {
    // Fallback if stats endpoint doesn't exist
    return { total: 0, pending: 0, responded: 0, closed: 0, overdue: 0 };
  }
  return response.json();
}

// Respond to RFI
async function respondToRFI(rfiId: number, response: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/rfis/${rfiId}/respond`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ response }),
  });
  if (!res.ok) throw new Error("Failed to respond to RFI");
}

// Get status badge
function getStatusBadge(status: string) {
  switch (status.toLowerCase()) {
    case "pending":
      return <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">Pending</Badge>;
    case "responded":
      return <Badge variant="outline" className="bg-teal-50 text-teal-700 border-teal-200">Responded</Badge>;
    case "closed":
      return <Badge variant="outline" className="bg-slate-50 text-slate-600 border-slate-200">Closed</Badge>;
    case "overdue":
      return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">Overdue</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

// Get priority indicator
function getPriorityIndicator(priority?: string, isOverdue?: boolean) {
  if (isOverdue) {
    return <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" title="Overdue" />;
  }
  switch (priority?.toLowerCase()) {
    case "high":
    case "urgent":
      return <span className="w-2 h-2 rounded-full bg-red-500" title="High Priority" />;
    case "medium":
      return <span className="w-2 h-2 rounded-full bg-amber-500" title="Medium Priority" />;
    default:
      return <span className="w-2 h-2 rounded-full bg-slate-300" title="Normal Priority" />;
  }
}

// Loading skeleton
function RFISkeleton() {
  return (
    <div className="space-y-2">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 border rounded-lg">
          <Skeleton className="h-4 w-4" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-6 w-20" />
          <Skeleton className="h-4 w-24" />
        </div>
      ))}
    </div>
  );
}

// Empty state
function EmptyState({ status }: { status?: string }) {
  const messages: Record<string, { title: string; subtitle: string }> = {
    pending: { title: "No pending RFIs", subtitle: "All caught up! The team is on top of things." },
    responded: { title: "No responded RFIs", subtitle: "Nothing in the responded queue yet." },
    closed: { title: "No closed RFIs", subtitle: "The archive is empty. Fresh start!" },
    default: { title: "No RFIs found", subtitle: "Quiet day for questions. Enjoy it while it lasts." },
  };

  const { title, subtitle } = messages[status || "default"] || messages.default;

  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
      <CardContent className="py-16 text-center">
        <FileQuestion className="mx-auto h-16 w-16 text-slate-300 mb-4" />
        <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>{title}</p>
        <p className={cn(ds.typography.body, ds.textColors.tertiary)}>{subtitle}</p>
      </CardContent>
    </Card>
  );
}

// Error state
function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50")}>
      <CardContent className="py-12 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
        <p className={cn(ds.typography.heading3, "text-red-700 mb-2")}>Failed to load RFIs</p>
        <p className={cn(ds.typography.body, "text-red-600 mb-4")}>
          Something broke. Our fault, not yours. Try again?
        </p>
        <Button onClick={onRetry} variant="outline" className="border-red-200 text-red-700 hover:bg-red-100">
          Try Again
        </Button>
      </CardContent>
    </Card>
  );
}

// RFI Row component
function RFIRow({
  rfi,
  isExpanded,
  onToggle,
  onRespond,
}: {
  rfi: RFI;
  isExpanded: boolean;
  onToggle: () => void;
  onRespond: () => void;
}) {
  return (
    <>
      <TableRow
        key={`${rfi.id}-main`}
        className={cn(
          "cursor-pointer hover:bg-slate-50 transition-colors",
          rfi.is_overdue && "bg-red-50/50"
        )}
        onClick={onToggle}
      >
        <TableCell className="w-8">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-slate-400" />
          )}
        </TableCell>
        <TableCell className="w-8">
          {getPriorityIndicator(rfi.priority, rfi.is_overdue)}
        </TableCell>
        <TableCell className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
          {rfi.rfi_number || `RFI-${rfi.id}`}
        </TableCell>
        <TableCell className={cn(ds.typography.body, ds.textColors.primary, "max-w-md truncate")}>
          {rfi.subject}
        </TableCell>
        <TableCell>
          {rfi.project_code && (
            <Badge variant="outline" className="text-xs">
              {rfi.project_code}
            </Badge>
          )}
        </TableCell>
        <TableCell>{getStatusBadge(rfi.is_overdue ? "overdue" : rfi.status)}</TableCell>
        <TableCell className={cn(ds.typography.caption, ds.textColors.tertiary)}>
          {rfi.due_date ? format(new Date(rfi.due_date), "MMM d, yyyy") : "—"}
        </TableCell>
        <TableCell className={cn(ds.typography.caption, ds.textColors.tertiary)}>
          {rfi.days_open !== undefined ? `${rfi.days_open}d` : formatDistanceToNow(new Date(rfi.created_at), { addSuffix: false })}
        </TableCell>
      </TableRow>
      {isExpanded && (
        <TableRow key={`${rfi.id}-expanded`}>
          <TableCell colSpan={8} className="bg-slate-50 p-0">
            <div className="p-6 space-y-4">
              {/* Description */}
              {rfi.description && (
                <div>
                  <h4 className={cn(ds.typography.captionBold, ds.textColors.secondary, "mb-1")}>
                    Question
                  </h4>
                  <p className={cn(ds.typography.body, ds.textColors.primary)}>
                    {rfi.description}
                  </p>
                </div>
              )}

              {/* Details grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted)}>Requested By</p>
                  <p className={cn(ds.typography.body, ds.textColors.primary)}>
                    {rfi.requested_by || "—"}
                  </p>
                </div>
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted)}>Assigned To</p>
                  <p className={cn(ds.typography.body, ds.textColors.primary)}>
                    {rfi.assigned_to || "Unassigned"}
                  </p>
                </div>
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted)}>Created</p>
                  <p className={cn(ds.typography.body, ds.textColors.primary)}>
                    {format(new Date(rfi.created_at), "MMM d, yyyy")}
                  </p>
                </div>
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted)}>Project</p>
                  <p className={cn(ds.typography.body, ds.textColors.primary)}>
                    {rfi.project_name || rfi.project_code || "—"}
                  </p>
                </div>
              </div>

              {/* Response */}
              {rfi.response && (
                <div className="p-4 bg-teal-50 rounded-lg border border-teal-200">
                  <h4 className={cn(ds.typography.captionBold, "text-teal-700 mb-1")}>
                    Response
                  </h4>
                  <p className={cn(ds.typography.body, "text-teal-900")}>
                    {rfi.response}
                  </p>
                  {rfi.responded_at && (
                    <p className={cn(ds.typography.caption, "text-teal-600 mt-2")}>
                      Responded {format(new Date(rfi.responded_at), "MMM d, yyyy 'at' h:mm a")}
                    </p>
                  )}
                </div>
              )}

              {/* Action buttons */}
              {rfi.status === "pending" && (
                <div className="flex justify-end">
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      onRespond();
                    }}
                    className="bg-teal-600 hover:bg-teal-700"
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Respond
                  </Button>
                </div>
              )}
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

export default function RFIsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<string>("pending");
  const [searchQuery, setSearchQuery] = useState("");
  const [projectFilter, setProjectFilter] = useState<string>("all");
  const [expandedRFI, setExpandedRFI] = useState<number | null>(null);
  const [respondDialogOpen, setRespondDialogOpen] = useState(false);
  const [selectedRFI, setSelectedRFI] = useState<RFI | null>(null);
  const [responseText, setResponseText] = useState("");

  // Fetch RFIs
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["rfis", activeTab],
    queryFn: () => fetchRFIs({ status: activeTab === "all" ? undefined : activeTab }),
    staleTime: 1000 * 60 * 2,
  });

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ["rfi-stats"],
    queryFn: fetchRFIStats,
    staleTime: 1000 * 60 * 5,
  });

  // Respond mutation
  const respondMutation = useMutation({
    mutationFn: ({ rfiId, response }: { rfiId: number; response: string }) =>
      respondToRFI(rfiId, response),
    onSuccess: () => {
      toast.success("Response submitted successfully");
      queryClient.invalidateQueries({ queryKey: ["rfis"] });
      queryClient.invalidateQueries({ queryKey: ["rfi-stats"] });
      setRespondDialogOpen(false);
      setSelectedRFI(null);
      setResponseText("");
    },
    onError: (error: Error) => {
      toast.error(`Failed to submit response: ${error.message}`);
    },
  });

  const rfis = data?.rfis || [];

  // Filter RFIs
  const filteredRFIs = rfis.filter((rfi) => {
    const matchesSearch =
      !searchQuery ||
      rfi.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rfi.rfi_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rfi.project_code?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesProject =
      projectFilter === "all" || rfi.project_code === projectFilter;

    return matchesSearch && matchesProject;
  });

  // Get unique projects for filter
  const uniqueProjects = [...new Set(rfis.map((r) => r.project_code).filter(Boolean))];

  return (
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            RFI Dashboard
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Requests for Information. Questions need answers.
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-100">
                <HelpCircle className="h-5 w-5 text-slate-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>Total</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {stats?.total ?? "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-amber-200 bg-amber-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-100">
                <Clock className="h-5 w-5 text-amber-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-amber-700")}>Pending</p>
                <p className={cn(ds.typography.heading2, "text-amber-800")}>
                  {stats?.pending ?? "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-100">
                <AlertTriangle className="h-5 w-5 text-red-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-red-700")}>Overdue</p>
                <p className={cn(ds.typography.heading2, "text-red-800")}>
                  {stats?.overdue ?? "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-teal-200 bg-teal-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-teal-100">
                <MessageSquare className="h-5 w-5 text-teal-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-teal-700")}>Responded</p>
                <p className={cn(ds.typography.heading2, "text-teal-800")}>
                  {stats?.responded ?? "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-100">
                <CheckCircle2 className="h-5 w-5 text-emerald-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>Closed</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {stats?.closed ?? "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
        <CardContent className="py-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search RFIs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={projectFilter} onValueChange={setProjectFilter}>
              <SelectTrigger className="w-[200px]">
                <Filter className="h-4 w-4 mr-2 text-slate-400" />
                <SelectValue placeholder="Filter by project" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Projects</SelectItem>
                {uniqueProjects.map((project) => (
                  <SelectItem key={project} value={project!}>
                    {project}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* RFI Table */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="pending">Pending</TabsTrigger>
          <TabsTrigger value="responded">Responded</TabsTrigger>
          <TabsTrigger value="closed">Closed</TabsTrigger>
          <TabsTrigger value="all">All</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          {isLoading ? (
            <RFISkeleton />
          ) : error ? (
            <ErrorState onRetry={() => refetch()} />
          ) : filteredRFIs.length === 0 ? (
            <EmptyState status={activeTab} />
          ) : (
            <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-8"></TableHead>
                    <TableHead className="w-8"></TableHead>
                    <TableHead className={cn(ds.typography.captionBold, "w-28")}>RFI #</TableHead>
                    <TableHead className={ds.typography.captionBold}>Subject</TableHead>
                    <TableHead className={ds.typography.captionBold}>Project</TableHead>
                    <TableHead className={ds.typography.captionBold}>Status</TableHead>
                    <TableHead className={ds.typography.captionBold}>Due Date</TableHead>
                    <TableHead className={ds.typography.captionBold}>Age</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRFIs.map((rfi) => (
                    <RFIRow
                      key={rfi.id}
                      rfi={rfi}
                      isExpanded={expandedRFI === rfi.id}
                      onToggle={() => setExpandedRFI(expandedRFI === rfi.id ? null : rfi.id)}
                      onRespond={() => {
                        setSelectedRFI(rfi);
                        setRespondDialogOpen(true);
                      }}
                    />
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Respond Dialog */}
      <Dialog open={respondDialogOpen} onOpenChange={setRespondDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Respond to RFI</DialogTitle>
            <DialogDescription>
              {selectedRFI?.rfi_number || `RFI-${selectedRFI?.id}`}: {selectedRFI?.subject}
            </DialogDescription>
          </DialogHeader>

          {selectedRFI?.description && (
            <div className="p-3 bg-slate-50 rounded-lg text-sm">
              <p className="font-medium text-slate-700 mb-1">Question:</p>
              <p className="text-slate-600">{selectedRFI.description}</p>
            </div>
          )}

          <Textarea
            placeholder="Enter your response..."
            value={responseText}
            onChange={(e) => setResponseText(e.target.value)}
            rows={5}
          />

          <DialogFooter>
            <Button variant="outline" onClick={() => setRespondDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (selectedRFI && responseText.trim()) {
                  respondMutation.mutate({ rfiId: selectedRFI.id, response: responseText });
                }
              }}
              disabled={respondMutation.isPending || !responseText.trim()}
              className="bg-teal-600 hover:bg-teal-700"
            >
              <Send className="h-4 w-4 mr-2" />
              {respondMutation.isPending ? "Submitting..." : "Submit Response"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
