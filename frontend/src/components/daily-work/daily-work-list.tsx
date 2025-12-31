"use client";

import * as React from "react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, parseISO } from "date-fns";
import {
  Clock,
  User,
  FileText,
  CheckCircle2,
  AlertCircle,
  Eye,
  Loader2,
  Calendar,
  Filter,
  Paperclip,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DailyWorkItem {
  daily_work_id: number;
  project_code: string;
  work_date: string;
  submitted_at: string;
  description: string;
  task_type: string | null;
  discipline: string | null;
  phase: string | null;
  hours_spent: number | null;
  staff_id: number | null;
  staff_name: string | null;
  attachments: Array<{ file_id: number; filename: string }>;
  reviewer_id: number | null;
  reviewer_name: string | null;
  review_status: "pending" | "reviewed" | "needs_revision" | "approved";
  review_comments: string | null;
  reviewed_at: string | null;
}

interface DailyWorkListProps {
  projectCode: string;
  onSelectItem?: (item: DailyWorkItem) => void;
}

const STATUS_CONFIG = {
  pending: {
    label: "Pending Review",
    color: "bg-amber-100 text-amber-700 border-amber-200",
    icon: Clock,
  },
  reviewed: {
    label: "Reviewed",
    color: "bg-blue-100 text-blue-700 border-blue-200",
    icon: Eye,
  },
  needs_revision: {
    label: "Needs Revision",
    color: "bg-red-100 text-red-700 border-red-200",
    icon: AlertCircle,
  },
  approved: {
    label: "Approved",
    color: "bg-emerald-100 text-emerald-700 border-emerald-200",
    icon: CheckCircle2,
  },
};

export function DailyWorkList({ projectCode, onSelectItem }: DailyWorkListProps) {
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const { data, isLoading, error } = useQuery({
    queryKey: ["daily-work", projectCode, statusFilter],
    queryFn: async () => {
      const url = new URL(
        `${API_BASE}/api/projects/${encodeURIComponent(projectCode)}/daily-work`
      );
      if (statusFilter && statusFilter !== "all") {
        url.searchParams.set("status", statusFilter);
      }
      const res = await fetch(url.toString());
      if (!res.ok) throw new Error("Failed to fetch daily work");
      return res.json();
    },
  });

  const submissions: DailyWorkItem[] = data?.submissions ?? [];
  const stats = data?.stats ?? { total: 0, pending: 0, reviewed: 0, needs_revision: 0, approved: 0 };

  if (error) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-red-500">
          <AlertCircle className="h-8 w-8 mx-auto mb-2" />
          Failed to load daily work submissions
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-teal-600" />
            Daily Work Submissions
          </CardTitle>

          {/* Filters */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All ({stats.total})</SelectItem>
                <SelectItem value="pending">
                  Pending ({stats.pending})
                </SelectItem>
                <SelectItem value="reviewed">
                  Reviewed ({stats.reviewed})
                </SelectItem>
                <SelectItem value="needs_revision">
                  Needs Revision ({stats.needs_revision})
                </SelectItem>
                <SelectItem value="approved">
                  Approved ({stats.approved})
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Stats Summary */}
        <div className="flex flex-wrap gap-2 mt-2">
          {Object.entries(STATUS_CONFIG).map(([key, config]) => {
            const count = stats[key as keyof typeof stats] || 0;
            const Icon = config.icon;
            return (
              <Badge
                key={key}
                variant="outline"
                className={cn("gap-1", config.color)}
              >
                <Icon className="h-3 w-3" />
                {count} {config.label}
              </Badge>
            );
          })}
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
          </div>
        ) : submissions.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="text-lg font-medium">No submissions yet</p>
            <p className="text-sm">
              Daily work submissions for this project will appear here
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Staff</TableHead>
                  <TableHead className="max-w-[300px]">Description</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Phase</TableHead>
                  <TableHead>Hours</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {submissions.map((item) => {
                  const statusConfig = STATUS_CONFIG[item.review_status];
                  const StatusIcon = statusConfig.icon;

                  return (
                    <TableRow key={item.daily_work_id}>
                      <TableCell className="font-medium whitespace-nowrap">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3 text-slate-400" />
                          {item.work_date
                            ? format(parseISO(item.work_date), "MMM d, yyyy")
                            : "-"}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <User className="h-3 w-3 text-slate-400" />
                          {item.staff_name || "-"}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[300px]">
                        <p className="truncate">{item.description}</p>
                        {item.attachments.length > 0 && (
                          <div className="flex items-center gap-1 text-xs text-slate-500 mt-1">
                            <Paperclip className="h-3 w-3" />
                            {item.attachments.length} file(s)
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        {item.task_type ? (
                          <Badge variant="secondary" className="capitalize">
                            {item.task_type}
                          </Badge>
                        ) : (
                          "-"
                        )}
                      </TableCell>
                      <TableCell>{item.phase || "-"}</TableCell>
                      <TableCell>
                        {item.hours_spent ? `${item.hours_spent}h` : "-"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={cn("gap-1", statusConfig.color)}
                        >
                          <StatusIcon className="h-3 w-3" />
                          {statusConfig.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onSelectItem?.(item)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
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
