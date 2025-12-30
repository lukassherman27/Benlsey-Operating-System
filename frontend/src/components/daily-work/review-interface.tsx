"use client";

import * as React from "react";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { format, parseISO } from "date-fns";
import {
  X,
  User,
  Calendar,
  Clock,
  FileText,
  Download,
  CheckCircle,
  AlertTriangle,
  MessageSquare,
  Loader2,
  Paperclip,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { FileUpload } from "@/components/file-upload";
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

interface ReviewInterfaceProps {
  item: DailyWorkItem;
  onClose: () => void;
  reviewerName?: string;
  reviewerId?: number;
}

const STATUS_OPTIONS = [
  { value: "reviewed", label: "Mark as Reviewed", color: "bg-blue-500" },
  { value: "needs_revision", label: "Needs Revision", color: "bg-amber-500" },
  { value: "approved", label: "Approve", color: "bg-emerald-500" },
];

export function DailyWorkReviewInterface({
  item,
  onClose,
  reviewerName = "Bill",
  reviewerId,
}: ReviewInterfaceProps) {
  const queryClient = useQueryClient();
  const [reviewStatus, setReviewStatus] = useState(item.review_status);
  const [reviewComments, setReviewComments] = useState(item.review_comments || "");
  const [showUpload, setShowUpload] = useState(false);

  const reviewMutation = useMutation({
    mutationFn: async (data: {
      review_status: string;
      review_comments: string;
      reviewer_name: string;
      reviewer_id?: number;
    }) => {
      const res = await fetch(
        `${API_BASE}/api/daily-work/${item.daily_work_id}/review`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        }
      );
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to submit review");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["daily-work", item.project_code] });
      onClose();
    },
  });

  const handleDownload = async (fileId: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/files/download/${fileId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.download_url) {
          window.open(data.download_url, "_blank");
        }
      }
    } catch (e) {
      console.error("Download failed:", e);
    }
  };

  const handleSubmitReview = () => {
    reviewMutation.mutate({
      review_status: reviewStatus,
      review_comments: reviewComments,
      reviewer_name: reviewerName,
      reviewer_id: reviewerId,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-teal-600" />
              Review Daily Work
            </CardTitle>
            <p className="text-sm text-slate-500 mt-1">
              Submitted by {item.staff_name || "Unknown"} on{" "}
              {item.work_date
                ? format(parseISO(item.work_date), "MMMM d, yyyy")
                : "-"}
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Submission Details */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <Label className="text-xs text-slate-500">Staff</Label>
                <p className="font-medium flex items-center gap-1">
                  <User className="h-3 w-3 text-slate-400" />
                  {item.staff_name || "-"}
                </p>
              </div>
              <div>
                <Label className="text-xs text-slate-500">Work Date</Label>
                <p className="font-medium flex items-center gap-1">
                  <Calendar className="h-3 w-3 text-slate-400" />
                  {item.work_date
                    ? format(parseISO(item.work_date), "MMM d, yyyy")
                    : "-"}
                </p>
              </div>
              <div>
                <Label className="text-xs text-slate-500">Hours</Label>
                <p className="font-medium flex items-center gap-1">
                  <Clock className="h-3 w-3 text-slate-400" />
                  {item.hours_spent ? `${item.hours_spent}h` : "-"}
                </p>
              </div>
              <div>
                <Label className="text-xs text-slate-500">Phase</Label>
                <p className="font-medium">{item.phase || "-"}</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {item.task_type && (
                <Badge variant="secondary" className="capitalize">
                  {item.task_type}
                </Badge>
              )}
              {item.discipline && (
                <Badge variant="outline">{item.discipline}</Badge>
              )}
            </div>

            <div>
              <Label className="text-xs text-slate-500">Description</Label>
              <div className="mt-1 p-3 bg-slate-50 rounded-lg text-sm whitespace-pre-wrap">
                {item.description}
              </div>
            </div>
          </div>

          {/* Attachments */}
          {item.attachments.length > 0 && (
            <div>
              <Label className="text-xs text-slate-500 mb-2 block">
                Attachments ({item.attachments.length})
              </Label>
              <div className="space-y-2">
                {item.attachments.map((file) => (
                  <div
                    key={file.file_id}
                    className="flex items-center justify-between p-2 bg-slate-50 rounded-lg"
                  >
                    <div className="flex items-center gap-2">
                      <Paperclip className="h-4 w-4 text-slate-400" />
                      <span className="text-sm">{file.filename}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDownload(file.file_id)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <Separator />

          {/* Previous Review (if any) */}
          {item.reviewed_at && (
            <div className="p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center gap-2 text-sm text-blue-700 mb-1">
                <MessageSquare className="h-4 w-4" />
                Previous review by {item.reviewer_name || "Unknown"} on{" "}
                {format(parseISO(item.reviewed_at), "MMM d, yyyy")}
              </div>
              {item.review_comments && (
                <p className="text-sm text-blue-800">{item.review_comments}</p>
              )}
            </div>
          )}

          {/* Review Form */}
          <div className="space-y-4">
            <div>
              <Label>Review Status</Label>
              <Select
                value={reviewStatus}
                onValueChange={(v) =>
                  setReviewStatus(v as typeof reviewStatus)
                }
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Review Comments</Label>
              <Textarea
                placeholder="Add your feedback here..."
                value={reviewComments}
                onChange={(e) => setReviewComments(e.target.value)}
                rows={4}
                className="mt-1"
              />
            </div>

            {/* Upload Marked-up Files */}
            <div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowUpload(!showUpload)}
              >
                <Paperclip className="h-4 w-4 mr-1" />
                {showUpload ? "Hide Upload" : "Upload Marked-up File"}
              </Button>

              {showUpload && (
                <div className="mt-2 border rounded-lg p-4">
                  <FileUpload
                    projectCode={item.project_code}
                    defaultCategory="Daily Work"
                    onUploadComplete={(file) => {
                      setReviewComments(
                        (prev) =>
                          prev +
                          (prev ? "\n" : "") +
                          `Uploaded feedback file: ${file.filename}`
                      );
                    }}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmitReview}
              disabled={reviewMutation.isPending}
              className={cn(
                reviewStatus === "approved" && "bg-emerald-600 hover:bg-emerald-700",
                reviewStatus === "needs_revision" && "bg-amber-600 hover:bg-amber-700"
              )}
            >
              {reviewMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : reviewStatus === "approved" ? (
                <>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Approve Work
                </>
              ) : reviewStatus === "needs_revision" ? (
                <>
                  <AlertTriangle className="mr-2 h-4 w-4" />
                  Request Revision
                </>
              ) : (
                "Submit Review"
              )}
            </Button>
          </div>

          {reviewMutation.isError && (
            <p className="text-sm text-red-500 text-center">
              Error: {reviewMutation.error?.message}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
