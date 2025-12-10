"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, formatDistanceToNow } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
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
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  ClipboardList,
  Search,
  Filter,
  Download,
  User,
  AlertCircle,
  Plus,
  Pencil,
  Trash2,
  Eye,
  Clock,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface AuditLog {
  id: number;
  action: string;
  entity_type: string;
  entity_id?: string;
  entity_name?: string;
  user_id?: string;
  user_name?: string;
  ip_address?: string;
  changes?: Record<string, { old: unknown; new: unknown }>;
  metadata?: Record<string, unknown>;
  created_at: string;
}

interface AuditStats {
  total_logs: number;
  logs_today: number;
  unique_users: number;
  by_action: { action: string; count: number }[];
}

// Fetch audit logs
async function fetchAuditLogs(params?: {
  action?: string;
  entity_type?: string;
  user_id?: string;
  limit?: number;
  offset?: number;
}): Promise<{ logs: AuditLog[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params?.action) searchParams.append("action", params.action);
  if (params?.entity_type) searchParams.append("entity_type", params.entity_type);
  if (params?.user_id) searchParams.append("user_id", params.user_id);
  if (params?.limit) searchParams.append("limit", params.limit.toString());
  if (params?.offset) searchParams.append("offset", params.offset.toString());

  const response = await fetch(`${API_BASE_URL}/api/audit/logs?${searchParams}`);
  if (!response.ok) {
    // Return empty if endpoint doesn't exist
    return { logs: [], total: 0 };
  }
  return response.json();
}

// Fetch audit stats - uses learning stats endpoint
async function fetchAuditStats(): Promise<AuditStats> {
  const response = await fetch(`${API_BASE_URL}/api/learning/stats`);
  if (!response.ok) {
    return { total_logs: 0, logs_today: 0, unique_users: 0, by_action: [] };
  }
  const data = await response.json();
  // Map learning stats to audit stats format
  return {
    total_logs: data.total_suggestions || 0,
    logs_today: data.pending || 0,
    unique_users: data.patterns_learned || 0,
    by_action: [],
  };
}

// Get action icon
function getActionIcon(action: string) {
  switch (action.toLowerCase()) {
    case "create":
      return <Plus className="h-4 w-4 text-emerald-600" />;
    case "update":
    case "edit":
      return <Pencil className="h-4 w-4 text-blue-600" />;
    case "delete":
      return <Trash2 className="h-4 w-4 text-red-600" />;
    case "view":
    case "read":
      return <Eye className="h-4 w-4 text-slate-600" />;
    default:
      return <Activity className="h-4 w-4 text-slate-600" />;
  }
}

// Get action badge
function getActionBadge(action: string) {
  const actionLower = action.toLowerCase();
  const styles: Record<string, string> = {
    create: "bg-emerald-50 text-emerald-700 border-emerald-200",
    update: "bg-blue-50 text-blue-700 border-blue-200",
    edit: "bg-blue-50 text-blue-700 border-blue-200",
    delete: "bg-red-50 text-red-700 border-red-200",
    view: "bg-slate-50 text-slate-600 border-slate-200",
    read: "bg-slate-50 text-slate-600 border-slate-200",
  };

  return (
    <Badge variant="outline" className={cn("text-xs", styles[actionLower] || styles.view)}>
      {action}
    </Badge>
  );
}

// Loading skeleton
function AuditSkeleton() {
  return (
    <div className="space-y-2">
      {[...Array(10)].map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 border rounded-lg">
          <Skeleton className="h-4 w-4" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-24" />
        </div>
      ))}
    </div>
  );
}

// Empty state
function EmptyState() {
  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
      <CardContent className="py-16 text-center">
        <ClipboardList className="mx-auto h-16 w-16 text-slate-300 mb-4" />
        <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
          No audit logs yet
        </p>
        <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
          System activity will appear here. The watchers are watching.
        </p>
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
        <p className={cn(ds.typography.heading3, "text-red-700 mb-2")}>
          Failed to load audit logs
        </p>
        <p className={cn(ds.typography.body, "text-red-600 mb-4")}>
          Even the audit system can have a bad day. Try again?
        </p>
        <Button onClick={onRetry} variant="outline" className="border-red-200 text-red-700 hover:bg-red-100">
          Try Again
        </Button>
      </CardContent>
    </Card>
  );
}

// Changes diff viewer
function ChangesDiff({ changes }: { changes: Record<string, { old: unknown; new: unknown }> }) {
  return (
    <div className="space-y-2">
      {Object.entries(changes).map(([field, { old: oldVal, new: newVal }]) => (
        <div key={field} className="text-sm">
          <span className="font-medium text-slate-700">{field}:</span>
          <div className="ml-4 flex items-center gap-2">
            <span className="bg-red-50 text-red-700 px-2 py-0.5 rounded line-through">
              {String(oldVal ?? "null")}
            </span>
            <span className="text-slate-400">→</span>
            <span className="bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded">
              {String(newVal ?? "null")}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AuditLogPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState<string>("all");
  const [entityFilter, setEntityFilter] = useState<string>("all");
  const [page, setPage] = useState(0);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const ITEMS_PER_PAGE = 50;

  // Fetch logs
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["audit-logs", actionFilter, entityFilter, page],
    queryFn: () =>
      fetchAuditLogs({
        action: actionFilter !== "all" ? actionFilter : undefined,
        entity_type: entityFilter !== "all" ? entityFilter : undefined,
        limit: ITEMS_PER_PAGE,
        offset: page * ITEMS_PER_PAGE,
      }),
    staleTime: 1000 * 30, // Refresh frequently
  });

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ["audit-stats"],
    queryFn: fetchAuditStats,
    staleTime: 1000 * 60 * 5,
  });

  const logs = data?.logs || [];
  const totalLogs = data?.total || 0;
  const totalPages = Math.ceil(totalLogs / ITEMS_PER_PAGE);

  // Filter logs client-side for search
  const filteredLogs = logs.filter((log) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      log.action.toLowerCase().includes(query) ||
      log.entity_type.toLowerCase().includes(query) ||
      log.entity_name?.toLowerCase().includes(query) ||
      log.user_name?.toLowerCase().includes(query)
    );
  });

  // Get unique entity types for filter
  const entityTypes = [...new Set(logs.map((l) => l.entity_type))];

  // Export to CSV
  const handleExport = () => {
    const csvContent = [
      ["Timestamp", "Action", "Entity Type", "Entity", "User", "IP Address"].join(","),
      ...logs.map((log) =>
        [
          format(new Date(log.created_at), "yyyy-MM-dd HH:mm:ss"),
          log.action,
          log.entity_type,
          log.entity_name || log.entity_id || "",
          log.user_name || log.user_id || "",
          log.ip_address || "",
        ].join(",")
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-log-${format(new Date(), "yyyy-MM-dd")}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            Audit Log
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Who did what, when, and where. The system remembers everything.
          </p>
        </div>
        <Button variant="outline" onClick={handleExport} disabled={logs.length === 0}>
          <Download className="h-4 w-4 mr-2" />
          Export CSV
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-100">
                <ClipboardList className="h-5 w-5 text-slate-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>Total Logs</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {stats?.total_logs?.toLocaleString() || "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-blue-200 bg-blue-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <Clock className="h-5 w-5 text-blue-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-blue-700")}>Today</p>
                <p className={cn(ds.typography.heading2, "text-blue-800")}>
                  {stats?.logs_today || "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-teal-200 bg-teal-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-teal-100">
                <User className="h-5 w-5 text-teal-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-teal-700")}>Active Users</p>
                <p className={cn(ds.typography.heading2, "text-teal-800")}>
                  {stats?.unique_users || "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-100">
                <Activity className="h-5 w-5 text-emerald-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>Most Common</p>
                <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                  {stats?.by_action?.[0]?.action || "—"}
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
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={actionFilter} onValueChange={setActionFilter}>
              <SelectTrigger className="w-[150px]">
                <Filter className="h-4 w-4 mr-2 text-slate-400" />
                <SelectValue placeholder="Action" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Actions</SelectItem>
                <SelectItem value="create">Create</SelectItem>
                <SelectItem value="update">Update</SelectItem>
                <SelectItem value="delete">Delete</SelectItem>
                <SelectItem value="view">View</SelectItem>
              </SelectContent>
            </Select>
            <Select value={entityFilter} onValueChange={setEntityFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Entity Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Entities</SelectItem>
                {entityTypes.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Audit Log Table */}
      {isLoading ? (
        <AuditSkeleton />
      ) : error ? (
        <ErrorState onRetry={() => refetch()} />
      ) : filteredLogs.length === 0 ? (
        <EmptyState />
      ) : (
        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-8"></TableHead>
                <TableHead className={ds.typography.captionBold}>Timestamp</TableHead>
                <TableHead className={ds.typography.captionBold}>Action</TableHead>
                <TableHead className={ds.typography.captionBold}>Entity</TableHead>
                <TableHead className={ds.typography.captionBold}>User</TableHead>
                <TableHead className={cn(ds.typography.captionBold, "w-16")}></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLogs.map((log) => (
                <TableRow
                  key={log.id}
                  className="hover:bg-slate-50 transition-colors cursor-pointer"
                  onClick={() => setSelectedLog(log)}
                >
                  <TableCell>{getActionIcon(log.action)}</TableCell>
                  <TableCell>
                    <div>
                      <p className={cn(ds.typography.body, ds.textColors.primary)}>
                        {format(new Date(log.created_at), "MMM d, yyyy")}
                      </p>
                      <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                        {format(new Date(log.created_at), "h:mm:ss a")}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>{getActionBadge(log.action)}</TableCell>
                  <TableCell>
                    <div>
                      <p className={cn(ds.typography.body, ds.textColors.primary)}>
                        {log.entity_name || log.entity_id || "—"}
                      </p>
                      <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                        {log.entity_type}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center">
                        <User className="h-3 w-3 text-slate-600" />
                      </div>
                      <span className={cn(ds.typography.body, ds.textColors.secondary)}>
                        {log.user_name || log.user_id || "System"}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between p-4 border-t">
              <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                Page {page + 1} of {totalPages} ({totalLogs.toLocaleString()} total)
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Log Detail Dialog */}
      <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedLog && getActionIcon(selectedLog.action)}
              Audit Log Details
            </DialogTitle>
            <DialogDescription>
              {selectedLog && format(new Date(selectedLog.created_at), "EEEE, MMMM d, yyyy 'at' h:mm:ss a")}
            </DialogDescription>
          </DialogHeader>

          {selectedLog && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted)}>Action</p>
                  <div className="mt-1">{getActionBadge(selectedLog.action)}</div>
                </div>
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted)}>Entity Type</p>
                  <p className={cn(ds.typography.body, ds.textColors.primary, "mt-1")}>
                    {selectedLog.entity_type}
                  </p>
                </div>
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted)}>Entity</p>
                  <p className={cn(ds.typography.body, ds.textColors.primary, "mt-1")}>
                    {selectedLog.entity_name || selectedLog.entity_id || "—"}
                  </p>
                </div>
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted)}>User</p>
                  <p className={cn(ds.typography.body, ds.textColors.primary, "mt-1")}>
                    {selectedLog.user_name || selectedLog.user_id || "System"}
                  </p>
                </div>
              </div>

              {selectedLog.ip_address && (
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted)}>IP Address</p>
                  <p className={cn(ds.typography.body, ds.textColors.primary, "mt-1")}>
                    {selectedLog.ip_address}
                  </p>
                </div>
              )}

              {selectedLog.changes && Object.keys(selectedLog.changes).length > 0 && (
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted, "mb-2")}>Changes</p>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <ChangesDiff changes={selectedLog.changes} />
                  </div>
                </div>
              )}

              {selectedLog.metadata && Object.keys(selectedLog.metadata).length > 0 && (
                <div>
                  <p className={cn(ds.typography.label, ds.textColors.muted, "mb-2")}>Metadata</p>
                  <pre className="p-3 bg-slate-50 rounded-lg text-xs overflow-auto">
                    {JSON.stringify(selectedLog.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
