"use client";

import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle2, AlertCircle, Trash2, Calendar, User } from "lucide-react";
import Link from "next/link";

interface Task {
  task_id: number;
  title: string;
  description: string | null;
  task_type: string | null;
  priority: string;
  status: string;
  due_date: string | null;
  project_code: string | null;
  proposal_id: number | null;
  assignee: string | null;
  source_suggestion_id: number | null;
  source_email_id: number | null;
  source_transcript_id: number | null;
  source_meeting_id: number | null;
  created_at: string;
  completed_at: string | null;
}

interface TaskEditModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task?: Task | null;
  defaultProjectCode?: string;
  mode: "create" | "edit";
}

export function TaskEditModal({
  open,
  onOpenChange,
  task,
  defaultProjectCode,
  mode,
}: TaskEditModalProps) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    priority: "medium",
    status: "pending",
    due_date: "",
    assignee: "us",
    task_type: "action_item",
    project_code: defaultProjectCode || "",
  });

  // Fetch staff for assignee dropdown
  const { data: staffData } = useQuery({
    queryKey: ["staff"],
    queryFn: () => api.getStaff(),
  });

  // Fetch proposals for project dropdown
  const { data: proposalsData } = useQuery({
    queryKey: ["proposals", "active"],
    queryFn: () => api.getProposals({ per_page: 200 }),
  });

  // Initialize form when task changes
  useEffect(() => {
    if (task && mode === "edit") {
      setFormData({
        title: task.title || "",
        description: task.description || "",
        priority: task.priority || "medium",
        status: task.status || "pending",
        due_date: task.due_date || "",
        assignee: task.assignee || "us",
        task_type: task.task_type || "action_item",
        project_code: task.project_code || "",
      });
    } else if (mode === "create") {
      setFormData({
        title: "",
        description: "",
        priority: "medium",
        status: "pending",
        due_date: "",
        assignee: "us",
        task_type: "action_item",
        project_code: defaultProjectCode || "",
      });
    }
  }, [task, mode, defaultProjectCode, open]);

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => api.createTask(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      onOpenChange(false);
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: typeof formData) => {
      if (!task) throw new Error("No task to update");
      return api.updateTask(task.task_id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      onOpenChange(false);
    },
  });

  // Complete mutation
  const completeMutation = useMutation({
    mutationFn: () => {
      if (!task) throw new Error("No task to complete");
      return api.completeTask(task.task_id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      onOpenChange(false);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === "create") {
      createMutation.mutate(formData);
    } else {
      updateMutation.mutate(formData);
    }
  };

  const handleComplete = () => {
    completeMutation.mutate();
  };

  const assignees = staffData?.assignees || [];
  const proposals = proposalsData?.data || [];
  const isPending = createMutation.isPending || updateMutation.isPending || completeMutation.isPending;
  const isError = createMutation.isError || updateMutation.isError;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {mode === "create" ? "Create New Task" : "Edit Task"}
          </DialogTitle>
          <DialogDescription>
            {mode === "create"
              ? "Add a new task to track work items and action items."
              : `Editing task: ${task?.title}`}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="What needs to be done?"
              required
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Additional details..."
              rows={3}
            />
          </div>

          {/* Two column row */}
          <div className="grid grid-cols-2 gap-4">
            {/* Priority */}
            <div className="space-y-2">
              <Label>Priority</Label>
              <Select
                value={formData.priority}
                onValueChange={(v) => setFormData({ ...formData, priority: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Status (only in edit mode) */}
            {mode === "edit" && (
              <div className="space-y-2">
                <Label>Status</Label>
                <Select
                  value={formData.status}
                  onValueChange={(v) => setFormData({ ...formData, status: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Task Type (only in create mode to fill second column) */}
            {mode === "create" && (
              <div className="space-y-2">
                <Label>Task Type</Label>
                <Select
                  value={formData.task_type}
                  onValueChange={(v) => setFormData({ ...formData, task_type: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="action_item">Action Item</SelectItem>
                    <SelectItem value="follow_up">Follow Up</SelectItem>
                    <SelectItem value="deadline">Deadline</SelectItem>
                    <SelectItem value="reminder">Reminder</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {/* Due Date */}
          <div className="space-y-2">
            <Label htmlFor="due_date">Due Date</Label>
            <Input
              id="due_date"
              type="date"
              value={formData.due_date}
              onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
            />
          </div>

          {/* Assignee */}
          <div className="space-y-2">
            <Label>Assignee</Label>
            <Select
              value={formData.assignee}
              onValueChange={(v) => setFormData({ ...formData, assignee: v })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Who should do this?" />
              </SelectTrigger>
              <SelectContent>
                {assignees.map((a) => (
                  <SelectItem key={a.id} value={a.id}>
                    <span className="flex items-center gap-2">
                      <User className="h-3 w-3 text-muted-foreground" />
                      {a.name}
                      {a.department && (
                        <span className="text-muted-foreground text-xs">
                          ({a.department})
                        </span>
                      )}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Project */}
          <div className="space-y-2">
            <Label>Link to Proposal</Label>
            <Select
              value={formData.project_code || "__none__"}
              onValueChange={(v) => setFormData({ ...formData, project_code: v === "__none__" ? "" : v })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a proposal (optional)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">No proposal</SelectItem>
                {proposals.map((p) => (
                  <SelectItem key={p.project_code} value={p.project_code}>
                    {p.project_code} - {p.project_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Source info (edit mode only) */}
          {mode === "edit" && task && (
            <div className="border-t pt-4 space-y-2">
              <Label className="text-muted-foreground text-xs">Source</Label>
              <div className="flex flex-wrap gap-2 text-sm">
                {task.source_transcript_id && (
                  <Badge variant="outline" className="text-purple-600">
                    <Calendar className="h-3 w-3 mr-1" />
                    From Meeting
                  </Badge>
                )}
                {task.source_email_id && (
                  <Badge variant="outline" className="text-blue-600">
                    Email #{task.source_email_id}
                  </Badge>
                )}
                {task.source_suggestion_id && (
                  <Badge variant="outline" className="text-teal-600">
                    AI Suggestion #{task.source_suggestion_id}
                  </Badge>
                )}
                {task.project_code && (
                  <Link
                    href={`/proposals/${encodeURIComponent(task.project_code)}`}
                    className="text-teal-600 hover:underline"
                  >
                    {task.project_code}
                  </Link>
                )}
                <span className="text-muted-foreground">
                  Created: {new Date(task.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          )}

          {/* Error state */}
          {isError && (
            <div className="flex items-center gap-2 text-destructive text-sm">
              <AlertCircle className="h-4 w-4" />
              Failed to save task. Please try again.
            </div>
          )}
        </form>

        <DialogFooter className="flex justify-between gap-2">
          <div className="flex gap-2">
            {mode === "edit" && task && task.status !== "completed" && (
              <Button
                type="button"
                variant="outline"
                onClick={handleComplete}
                disabled={isPending}
                className="text-emerald-600 border-emerald-200 hover:bg-emerald-50"
              >
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Mark Complete
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={isPending || !formData.title}>
              {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {mode === "create" ? "Create Task" : "Save Changes"}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
