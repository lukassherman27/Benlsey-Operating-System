"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import {
  CheckSquare,
  Plus,
  Calendar,
  User,
  Bell,
  Home,
  Trees,
  Lightbulb,
  Sofa,
  LayoutGrid,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { TaskEditModal } from "@/components/tasks/task-edit-modal";

interface Task {
  task_id: number;
  title: string;
  description: string | null;
  task_type: string | null;
  priority: string;
  status: string;
  due_date: string | null;
  project_code: string | null;
  proposal_id?: number | null;
  assignee: string | null;
  source_suggestion_id?: number | null;
  source_email_id?: number | null;
  source_transcript_id?: number | null;
  source_meeting_id?: number | null;
  discipline: string | null;
  phase: string | null;
  created_at: string;
  completed_at?: string | null;
}

interface TaskDisciplineViewProps {
  projectCode: string;
}

// Discipline configuration with icons and colors
const DISCIPLINES = [
  { id: "all", label: "All Tasks", icon: LayoutGrid, color: "slate" },
  { id: "Interior", label: "Interior", icon: Home, color: "blue" },
  { id: "Landscape", label: "Landscape", icon: Trees, color: "green" },
  { id: "Lighting", label: "Lighting", icon: Lightbulb, color: "amber" },
  { id: "FFE", label: "FF&E", icon: Sofa, color: "purple" },
];

// Phase badges
const PHASE_COLORS: Record<string, string> = {
  SD: "bg-blue-100 text-blue-700 border-blue-200",
  DD: "bg-amber-100 text-amber-700 border-amber-200",
  CD: "bg-green-100 text-green-700 border-green-200",
  CA: "bg-purple-100 text-purple-700 border-purple-200",
};

// Priority colors
const PRIORITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700 border-red-200",
  high: "bg-amber-100 text-amber-700 border-amber-200",
  medium: "bg-blue-100 text-blue-700 border-blue-200",
  low: "bg-slate-100 text-slate-700 border-slate-200",
};

// Status colors
const STATUS_COLORS: Record<string, string> = {
  pending: "border-l-slate-400",
  in_progress: "border-l-blue-500",
  completed: "border-l-emerald-500",
};

function TaskRow({
  task,
  onEdit,
  onComplete,
  onSnooze,
}: {
  task: Task;
  onEdit: () => void;
  onComplete: () => void;
  onSnooze: () => void;
}) {
  const today = new Date().toISOString().split("T")[0];
  const isOverdue =
    task.due_date && task.due_date < today && task.status !== "completed";

  return (
    <div
      className={cn(
        "flex items-center gap-3 p-3 border-l-4 bg-white rounded-r-lg cursor-pointer hover:shadow-sm transition-all group",
        STATUS_COLORS[task.status] || "border-l-slate-300",
        isOverdue && "bg-red-50/50"
      )}
      onClick={onEdit}
    >
      <div className="flex-1 min-w-0">
        <p
          className={cn(
            "font-medium text-sm text-slate-800 truncate",
            task.status === "completed" && "line-through text-slate-500"
          )}
        >
          {task.title}
        </p>
        <div className="flex items-center gap-2 mt-1">
          {task.phase && (
            <Badge
              variant="outline"
              className={cn(
                "text-[10px] px-1.5 py-0",
                PHASE_COLORS[task.phase]
              )}
            >
              {task.phase}
            </Badge>
          )}
          {task.priority && (
            <Badge
              variant="outline"
              className={cn(
                "text-[10px] px-1.5 py-0",
                PRIORITY_COLORS[task.priority]
              )}
            >
              {task.priority}
            </Badge>
          )}
        </div>
      </div>

      {/* Due date */}
      {task.due_date && (
        <div
          className={cn(
            "text-xs shrink-0",
            isOverdue ? "text-red-600 font-semibold" : "text-slate-500"
          )}
        >
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {new Date(task.due_date).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            })}
          </span>
        </div>
      )}

      {/* Assignee */}
      {task.assignee && task.assignee !== "us" && (
        <div className="text-xs text-slate-500 shrink-0 flex items-center gap-1">
          <User className="h-3 w-3" />
          {task.assignee}
        </div>
      )}

      {/* Quick actions */}
      {task.status !== "completed" && (
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onComplete();
            }}
            className="h-7 w-7 p-0 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
          >
            <CheckSquare className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onSnooze();
            }}
            className="h-7 w-7 p-0 text-amber-600 hover:text-amber-700 hover:bg-amber-50"
          >
            <Bell className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

export function TaskDisciplineView({ projectCode }: TaskDisciplineViewProps) {
  const queryClient = useQueryClient();
  const [activeDiscipline, setActiveDiscipline] = useState("all");
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");

  // Fetch tasks by discipline
  const { data, isLoading } = useQuery({
    queryKey: ["tasks", "by-discipline", projectCode],
    queryFn: async () => {
      const res = await fetch(
        `${
          process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
        }/api/tasks/by-discipline?project_code=${encodeURIComponent(
          projectCode
        )}`
      );
      return res.json();
    },
  });

  // Complete task mutation
  const completeTask = useMutation({
    mutationFn: (taskId: number) => api.completeTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success("Task completed!");
    },
    onError: () => {
      toast.error("Failed to complete task");
    },
  });

  // Snooze task mutation
  const snoozeTask = useMutation({
    mutationFn: ({ taskId, newDueDate }: { taskId: number; newDueDate: string }) =>
      api.snoozeTask(taskId, newDueDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success("Task snoozed by 7 days");
    },
    onError: () => {
      toast.error("Failed to snooze task");
    },
  });

  const handleSnooze = (task: Task) => {
    const currentDue = task.due_date ? new Date(task.due_date) : new Date();
    currentDue.setDate(currentDue.getDate() + 7);
    const newDueDate = currentDue.toISOString().split("T")[0];
    snoozeTask.mutate({ taskId: task.task_id, newDueDate });
  };

  const handleOpenCreate = () => {
    setSelectedTask(null);
    setModalMode("create");
    setModalOpen(true);
  };

  const handleOpenEdit = (task: Task) => {
    setSelectedTask(task);
    setModalMode("edit");
    setModalOpen(true);
  };

  // Filter tasks by discipline
  const getFilteredTasks = () => {
    if (!data?.tasks) return [];
    if (activeDiscipline === "all") return data.tasks;
    return data.tasks.filter(
      (t: Task) => t.discipline === activeDiscipline
    );
  };

  const filteredTasks = getFilteredTasks();
  const counts = data?.counts || {};

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-10 w-full mb-4" />
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold">
              Tasks by Discipline
            </CardTitle>
            <Button size="sm" onClick={handleOpenCreate} className="gap-1">
              <Plus className="h-4 w-4" />
              Add Task
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs
            value={activeDiscipline}
            onValueChange={setActiveDiscipline}
            className="w-full"
          >
            <TabsList className="grid grid-cols-5 mb-4">
              {DISCIPLINES.map((disc) => {
                const Icon = disc.icon;
                const count =
                  disc.id === "all"
                    ? data?.total || 0
                    : counts[disc.id] || 0;
                return (
                  <TabsTrigger
                    key={disc.id}
                    value={disc.id}
                    className="gap-1.5 text-xs"
                  >
                    <Icon className="h-3.5 w-3.5" />
                    <span className="hidden sm:inline">{disc.label}</span>
                    <Badge
                      variant="secondary"
                      className="h-5 min-w-5 text-[10px] px-1"
                    >
                      {count}
                    </Badge>
                  </TabsTrigger>
                );
              })}
            </TabsList>

            {DISCIPLINES.map((disc) => (
              <TabsContent key={disc.id} value={disc.id} className="mt-0">
                <div className="space-y-2">
                  {filteredTasks.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-slate-400">
                      <CheckSquare className="h-10 w-10 mb-2 opacity-50" />
                      <p className="text-sm font-medium">No tasks</p>
                      <p className="text-xs mt-1">
                        {disc.id === "all"
                          ? "Create your first task for this project"
                          : `No ${disc.label} tasks yet`}
                      </p>
                    </div>
                  ) : (
                    filteredTasks.map((task: Task) => (
                      <TaskRow
                        key={task.task_id}
                        task={task}
                        onEdit={() => handleOpenEdit(task)}
                        onComplete={() => completeTask.mutate(task.task_id)}
                        onSnooze={() => handleSnooze(task)}
                      />
                    ))
                  )}
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>

      <TaskEditModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        task={selectedTask as Parameters<typeof TaskEditModal>[0]['task']}
        defaultProjectCode={projectCode}
        mode={modalMode}
      />
    </>
  );
}
