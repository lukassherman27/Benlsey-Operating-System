"use client";

import * as React from "react";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { format, parseISO, differenceInDays } from "date-fns";
import {
  Calendar,
  AlertCircle,
  CheckCircle2,
  Clock,
  Loader2,
  MoreHorizontal,
  Plus,
  Pencil,
  Trash2,
  Eye,
  Filter,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Deliverable {
  deliverable_id: number;
  project_code: string;
  project_title?: string;
  name: string;
  deliverable_name?: string;
  description?: string;
  deliverable_type?: string;
  phase?: string;
  due_date?: string;
  start_date?: string;
  actual_completion_date?: string;
  status: "pending" | "in_progress" | "submitted" | "revision" | "approved" | "rejected" | "cancelled";
  priority: "low" | "normal" | "high" | "critical";
  assigned_pm?: string;
  owner_staff_id?: number;
  days_until_due?: number;
  is_overdue?: number;
}

interface DeliverablesTableProps {
  projectCode: string;
  onAddNew?: () => void;
  onEdit?: (deliverable: Deliverable) => void;
  onViewDetail?: (deliverable: Deliverable) => void;
}

const STATUS_CONFIG = {
  pending: { label: "Pending", color: "bg-slate-100 text-slate-700", icon: Clock },
  in_progress: { label: "In Progress", color: "bg-blue-100 text-blue-700", icon: Clock },
  submitted: { label: "Submitted", color: "bg-purple-100 text-purple-700", icon: CheckCircle2 },
  revision: { label: "Revision", color: "bg-amber-100 text-amber-700", icon: AlertCircle },
  approved: { label: "Approved", color: "bg-emerald-100 text-emerald-700", icon: CheckCircle2 },
  rejected: { label: "Rejected", color: "bg-red-100 text-red-700", icon: AlertCircle },
  cancelled: { label: "Cancelled", color: "bg-gray-100 text-gray-500", icon: Clock },
};

const PRIORITY_CONFIG = {
  low: { label: "Low", color: "bg-slate-100 text-slate-600" },
  normal: { label: "Normal", color: "bg-blue-100 text-blue-600" },
  high: { label: "High", color: "bg-amber-100 text-amber-700" },
  critical: { label: "Critical", color: "bg-red-100 text-red-700" },
};

export function DeliverablesTable({
  projectCode,
  onAddNew,
  onEdit,
  onViewDetail,
}: DeliverablesTableProps) {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [phaseFilter, setPhaseFilter] = useState<string>("all");

  const { data, isLoading, error } = useQuery({
    queryKey: ["deliverables", projectCode, statusFilter, phaseFilter],
    queryFn: async () => {
      const url = new URL(`${API_BASE}/api/deliverables/by-project/${encodeURIComponent(projectCode)}`);
      if (statusFilter && statusFilter !== "all") {
        url.searchParams.set("status", statusFilter);
      }
      const res = await fetch(url.toString());
      if (!res.ok) throw new Error("Failed to fetch deliverables");
      return res.json();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`${API_BASE}/api/deliverables/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deliverables", projectCode] });
    },
  });

  const deliverables: Deliverable[] = data?.deliverables ?? data?.data ?? [];
  const phases = [...new Set(deliverables.map((d) => d.phase).filter(Boolean))];

  const filteredDeliverables = deliverables.filter((d) => {
    if (phaseFilter !== "all" && d.phase !== phaseFilter) return false;
    return true;
  });

  const handleDelete = (id: number) => {
    if (confirm("Delete this deliverable?")) {
      deleteMutation.mutate(id);
    }
  };

  const getDueDateInfo = (dueDate?: string, status?: string) => {
    if (!dueDate) return null;
    if (status === "approved" || status === "cancelled") return null;

    const days = differenceInDays(parseISO(dueDate), new Date());
    if (days < 0) return { label: `${Math.abs(days)}d overdue`, color: "text-red-600" };
    if (days === 0) return { label: "Due today", color: "text-amber-600" };
    if (days <= 7) return { label: `${days}d left`, color: "text-amber-600" };
    return { label: `${days}d left`, color: "text-slate-500" };
  };

  if (error) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-red-500">
          <AlertCircle className="h-8 w-8 mx-auto mb-2" />
          Failed to load deliverables
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <CardTitle className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-teal-600" />
            Deliverables
          </CardTitle>

          <div className="flex items-center gap-2">
            {/* Phase Filter */}
            <Select value={phaseFilter} onValueChange={setPhaseFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Phase" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Phases</SelectItem>
                {phases.map((p) => (
                  <SelectItem key={p} value={p!}>
                    {p}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Status Filter */}
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="submitted">Submitted</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
              </SelectContent>
            </Select>

            {onAddNew && (
              <Button onClick={onAddNew} size="sm">
                <Plus className="h-4 w-4 mr-1" />
                Add
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
          </div>
        ) : filteredDeliverables.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <CheckCircle2 className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="text-lg font-medium">No deliverables</p>
            <p className="text-sm">Add deliverables to track project progress</p>
            {onAddNew && (
              <Button onClick={onAddNew} className="mt-4" variant="outline">
                <Plus className="h-4 w-4 mr-1" />
                Add First Deliverable
              </Button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Phase</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDeliverables.map((d) => {
                  const statusConfig = STATUS_CONFIG[d.status] || STATUS_CONFIG.pending;
                  const StatusIcon = statusConfig.icon;
                  const priorityConfig = PRIORITY_CONFIG[d.priority] || PRIORITY_CONFIG.normal;
                  const dueDateInfo = getDueDateInfo(d.due_date, d.status);

                  return (
                    <TableRow key={d.deliverable_id}>
                      <TableCell className="font-medium">
                        {d.name || d.deliverable_name}
                        {d.description && (
                          <p className="text-xs text-slate-500 mt-0.5 truncate max-w-[200px]">
                            {d.description}
                          </p>
                        )}
                      </TableCell>
                      <TableCell>
                        {d.deliverable_type ? (
                          <Badge variant="outline" className="capitalize">
                            {d.deliverable_type}
                          </Badge>
                        ) : (
                          "-"
                        )}
                      </TableCell>
                      <TableCell>{d.phase || "-"}</TableCell>
                      <TableCell>
                        {d.due_date ? (
                          <div>
                            <div className="flex items-center gap-1">
                              <Calendar className="h-3 w-3 text-slate-400" />
                              {format(parseISO(d.due_date), "MMM d, yyyy")}
                            </div>
                            {dueDateInfo && (
                              <span className={cn("text-xs", dueDateInfo.color)}>
                                {dueDateInfo.label}
                              </span>
                            )}
                          </div>
                        ) : (
                          "-"
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={cn("gap-1", statusConfig.color)}>
                          <StatusIcon className="h-3 w-3" />
                          {statusConfig.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={priorityConfig.color}>
                          {priorityConfig.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {onViewDetail && (
                              <DropdownMenuItem onClick={() => onViewDetail(d)}>
                                <Eye className="h-4 w-4 mr-2" />
                                View Details
                              </DropdownMenuItem>
                            )}
                            {onEdit && (
                              <DropdownMenuItem onClick={() => onEdit(d)}>
                                <Pencil className="h-4 w-4 mr-2" />
                                Edit
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem
                              onClick={() => handleDelete(d.deliverable_id)}
                              className="text-red-600"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
