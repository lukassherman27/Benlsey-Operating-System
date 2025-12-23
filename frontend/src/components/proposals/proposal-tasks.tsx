"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Checkbox } from "@/components/ui/checkbox";
import { TaskEditModal } from "@/components/tasks/task-edit-modal";
import {
  CheckSquare,
  Clock,
  ChevronRight,
  FileText,
  User,
  Plus,
} from "lucide-react";
import { format, isPast, parseISO } from "date-fns";
import { cn } from "@/lib/utils";
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
  assigned_to?: string | null;
  source_suggestion_id: number | null;
  source_email_id: number | null;
  source_transcript_id: number | null;
  source_meeting_id: number | null;
  created_at: string;
  completed_at: string | null;
}

interface ProposalTasksProps {
  projectCode: string;
}

const priorityConfig = {
  critical: { color: "bg-red-100 text-red-800 border-red-200", icon: "!" },
  high: { color: "bg-orange-100 text-orange-800 border-orange-200", icon: "!!" },
  normal: { color: "bg-slate-100 text-slate-700 border-slate-200", icon: "" },
  low: { color: "bg-slate-50 text-slate-500 border-slate-100", icon: "" },
};

const statusConfig = {
  pending: { color: "bg-amber-50 border-amber-200", text: "text-amber-700" },
  in_progress: { color: "bg-blue-50 border-blue-200", text: "text-blue-700" },
  completed: { color: "bg-emerald-50 border-emerald-200", text: "text-emerald-700" },
  cancelled: { color: "bg-slate-50 border-slate-200", text: "text-slate-500" },
};

export function ProposalTasks({ projectCode }: ProposalTasksProps) {
  const queryClient = useQueryClient();
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("edit");

  const { data, isLoading, error } = useQuery({
    queryKey: ["project-tasks", projectCode],
    queryFn: () => api.getProjectTasks(projectCode, false),
    enabled: !!projectCode,
    retry: false,
  });

  const completeMutation = useMutation({
    mutationFn: (taskId: number) => api.completeTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project-tasks", projectCode] });
    },
  });

  const handleOpenCreate = () => {
    setSelectedTask(null);
    setModalMode("create");
    setIsModalOpen(true);
  };

  const handleOpenEdit = (task: Task) => {
    setSelectedTask(task);
    setModalMode("edit");
    setIsModalOpen(true);
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent className="space-y-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return null; // Silently hide if tasks API isn't available
  }

  const tasks = data?.tasks || [];

  // Sort: overdue first, then by priority, then by due date
  const sortedTasks = [...tasks].sort((a, b) => {
    // Overdue tasks first
    const aOverdue = a.due_date && isPast(parseISO(a.due_date));
    const bOverdue = b.due_date && isPast(parseISO(b.due_date));
    if (aOverdue && !bOverdue) return -1;
    if (!aOverdue && bOverdue) return 1;

    // Then by priority
    const priorityOrder = { critical: 0, high: 1, normal: 2, low: 3 };
    const aPriority = priorityOrder[a.priority as keyof typeof priorityOrder] ?? 2;
    const bPriority = priorityOrder[b.priority as keyof typeof priorityOrder] ?? 2;
    if (aPriority !== bPriority) return aPriority - bPriority;

    // Then by due date
    if (a.due_date && b.due_date) {
      return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
    }
    return 0;
  });

  // Show widget even with 0 tasks so user can create new ones

  return (
    <Card className="border-amber-200 bg-gradient-to-br from-amber-50/50 to-orange-50/30">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center gap-2 text-amber-800">
            <CheckSquare className="h-4 w-4" />
            <span>Tasks ({tasks.length})</span>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleOpenCreate}
              className="text-amber-700 hover:text-amber-900 hover:bg-amber-100 h-7 w-7 p-0"
              title="Create new task"
            >
              <Plus className="h-4 w-4" />
            </Button>
            <Link href="/tasks">
              <Button variant="ghost" size="sm" className="text-xs text-amber-700 hover:text-amber-900">
                View All <ChevronRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {tasks.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4">
            No tasks yet. Click + to create one.
          </p>
        )}
        {sortedTasks.slice(0, 5).map((task) => {
          const isOverdue = task.due_date && isPast(parseISO(task.due_date));
          const priorityStyle = priorityConfig[task.priority as keyof typeof priorityConfig] || priorityConfig.normal;
          const statusStyle = statusConfig[task.status as keyof typeof statusConfig] || statusConfig.pending;

          return (
            <div
              key={task.task_id}
              className={cn(
                "flex items-start gap-3 p-3 rounded-lg border transition-colors",
                isOverdue ? "bg-red-50 border-red-200" : statusStyle.color
              )}
            >
              <Checkbox
                checked={task.status === "completed"}
                onCheckedChange={() => {
                  if (task.status !== "completed") {
                    completeMutation.mutate(task.task_id);
                  }
                }}
                className="mt-0.5"
                onClick={(e) => e.stopPropagation()}
              />
              <div
                className="flex-1 min-w-0 cursor-pointer hover:opacity-80"
                onClick={() => handleOpenEdit(task as Task)}
              >
                <p className={cn(
                  "text-sm font-medium",
                  task.status === "completed" && "line-through text-muted-foreground"
                )}>
                  {task.title}
                </p>
                <div className="flex flex-wrap items-center gap-2 mt-1">
                  {task.due_date && (
                    <span className={cn(
                      "text-xs flex items-center gap-1",
                      isOverdue ? "text-red-600 font-medium" : "text-muted-foreground"
                    )}>
                      <Clock className="h-3 w-3" />
                      {isOverdue ? "Overdue: " : ""}
                      {format(parseISO(task.due_date), "MMM d")}
                    </span>
                  )}
                  {task.assigned_to && (
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <User className="h-3 w-3" />
                      {task.assigned_to}
                    </span>
                  )}
                  {task.source_transcript_id && (
                    <Badge variant="outline" className="text-xs bg-purple-50 text-purple-700 border-purple-200">
                      <FileText className="h-2.5 w-2.5 mr-1" />
                      From Meeting
                    </Badge>
                  )}
                </div>
              </div>
              <Badge className={cn("text-xs flex-shrink-0", priorityStyle.color)}>
                {task.priority}
              </Badge>
            </div>
          );
        })}
        {tasks.length > 5 && (
          <p className="text-xs text-center text-muted-foreground pt-2">
            +{tasks.length - 5} more tasks
          </p>
        )}
      </CardContent>

      <TaskEditModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        task={selectedTask}
        defaultProjectCode={projectCode}
        mode={modalMode}
      />
    </Card>
  );
}
