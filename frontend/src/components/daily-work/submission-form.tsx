"use client";

import * as React from "react";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { CalendarIcon, Loader2, Send, Paperclip } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { FileUpload } from "@/components/file-upload";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TASK_TYPES = [
  { value: "drawing", label: "Drawing" },
  { value: "model", label: "3D Model" },
  { value: "presentation", label: "Presentation" },
  { value: "research", label: "Research" },
  { value: "coordination", label: "Coordination" },
  { value: "documentation", label: "Documentation" },
  { value: "other", label: "Other" },
];

const DISCIPLINES = [
  { value: "Architecture", label: "Architecture" },
  { value: "Interior", label: "Interior Design" },
  { value: "Landscape", label: "Landscape" },
  { value: "Artwork", label: "Artwork" },
  { value: "Other", label: "Other" },
];

const PHASES = [
  { value: "Concept", label: "Concept" },
  { value: "SD", label: "Schematic Design (SD)" },
  { value: "DD", label: "Design Development (DD)" },
  { value: "CD", label: "Construction Documents (CD)" },
  { value: "CA", label: "Construction Administration (CA)" },
];

interface SubmissionFormProps {
  projectCode: string;
  onSuccess?: () => void;
}

interface StaffMember {
  staff_id: number;
  display_name: string;
  email?: string;
}

interface UploadedFile {
  file_id: number;
  filename: string;
}

export function DailyWorkSubmissionForm({ projectCode, onSuccess }: SubmissionFormProps) {
  const queryClient = useQueryClient();
  const [date, setDate] = useState<Date>(new Date());
  const [description, setDescription] = useState("");
  const [taskType, setTaskType] = useState("");
  const [discipline, setDiscipline] = useState("");
  const [phase, setPhase] = useState("");
  const [hoursSpent, setHoursSpent] = useState("");
  const [staffId, setStaffId] = useState("");
  const [attachments, setAttachments] = useState<UploadedFile[]>([]);
  const [showUpload, setShowUpload] = useState(false);

  // Fetch staff list for dropdown
  const staffQuery = useQuery({
    queryKey: ["staff"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/staff`);
      if (!res.ok) throw new Error("Failed to fetch staff");
      return res.json();
    },
  });

  const staffList: StaffMember[] = staffQuery.data?.staff ?? [];

  // Submit mutation
  const submitMutation = useMutation({
    mutationFn: async (data: {
      work_date: string;
      description: string;
      task_type?: string;
      discipline?: string;
      phase?: string;
      hours_spent?: number;
      staff_id?: number;
      staff_name?: string;
      attachments?: UploadedFile[];
    }) => {
      const res = await fetch(
        `${API_BASE}/api/projects/${encodeURIComponent(projectCode)}/daily-work`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        }
      );
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to submit");
      }
      return res.json();
    },
    onSuccess: () => {
      // Reset form
      setDescription("");
      setTaskType("");
      setDiscipline("");
      setPhase("");
      setHoursSpent("");
      setStaffId("");
      setAttachments([]);
      setShowUpload(false);
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ["daily-work", projectCode] });
      onSuccess?.();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const selectedStaff = staffList.find((s) => s.staff_id.toString() === staffId);

    submitMutation.mutate({
      work_date: format(date, "yyyy-MM-dd"),
      description,
      task_type: taskType || undefined,
      discipline: discipline || undefined,
      phase: phase || undefined,
      hours_spent: hoursSpent ? parseFloat(hoursSpent) : undefined,
      staff_id: staffId ? parseInt(staffId) : undefined,
      staff_name: selectedStaff?.display_name,
      attachments: attachments.length > 0 ? attachments : undefined,
    });
  };

  const handleFileUpload = (file: { file_id: number; filename: string }) => {
    setAttachments((prev) => [...prev, file]);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Send className="h-5 w-5 text-teal-600" />
          Submit Daily Work
        </CardTitle>
        <CardDescription>
          Log your daily work progress for this project
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            {/* Date Picker */}
            <div className="space-y-2">
              <Label>Work Date *</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !date && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {date ? format(date, "PPP") : "Select date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={date}
                    onSelect={(d) => d && setDate(d)}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>

            {/* Staff Selector */}
            <div className="space-y-2">
              <Label>Your Name</Label>
              <Select value={staffId} onValueChange={setStaffId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select yourself" />
                </SelectTrigger>
                <SelectContent>
                  {staffList.map((s) => (
                    <SelectItem key={s.staff_id} value={s.staff_id.toString()}>
                      {s.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label>Description *</Label>
            <Textarea
              placeholder="Describe what you worked on today..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              required
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {/* Task Type */}
            <div className="space-y-2">
              <Label>Task Type</Label>
              <Select value={taskType} onValueChange={setTaskType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  {TASK_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Discipline */}
            <div className="space-y-2">
              <Label>Discipline</Label>
              <Select value={discipline} onValueChange={setDiscipline}>
                <SelectTrigger>
                  <SelectValue placeholder="Select discipline" />
                </SelectTrigger>
                <SelectContent>
                  {DISCIPLINES.map((d) => (
                    <SelectItem key={d.value} value={d.value}>
                      {d.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Phase */}
            <div className="space-y-2">
              <Label>Phase</Label>
              <Select value={phase} onValueChange={setPhase}>
                <SelectTrigger>
                  <SelectValue placeholder="Select phase" />
                </SelectTrigger>
                <SelectContent>
                  {PHASES.map((p) => (
                    <SelectItem key={p.value} value={p.value}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Hours */}
          <div className="space-y-2 max-w-[200px]">
            <Label>Hours Spent</Label>
            <Input
              type="number"
              step="0.5"
              min="0"
              max="24"
              placeholder="e.g., 8"
              value={hoursSpent}
              onChange={(e) => setHoursSpent(e.target.value)}
            />
          </div>

          {/* Attachments */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Attachments</Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setShowUpload(!showUpload)}
              >
                <Paperclip className="h-4 w-4 mr-1" />
                {showUpload ? "Hide" : "Add Files"}
              </Button>
            </div>

            {attachments.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {attachments.map((f, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-1 px-2 py-1 bg-slate-100 rounded text-sm"
                  >
                    <Paperclip className="h-3 w-3" />
                    {f.filename}
                    <button
                      type="button"
                      className="ml-1 text-slate-500 hover:text-red-500"
                      onClick={() =>
                        setAttachments((prev) =>
                          prev.filter((_, idx) => idx !== i)
                        )
                      }
                    >
                      &times;
                    </button>
                  </div>
                ))}
              </div>
            )}

            {showUpload && (
              <div className="border rounded-lg p-4">
                <FileUpload
                  projectCode={projectCode}
                  defaultCategory="Daily Work"
                  onUploadComplete={handleFileUpload}
                />
              </div>
            )}
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={!description || submitMutation.isPending}
            className="w-full sm:w-auto"
          >
            {submitMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Submit Work
              </>
            )}
          </Button>

          {submitMutation.isError && (
            <p className="text-sm text-red-500">
              Error: {submitMutation.error?.message}
            </p>
          )}

          {submitMutation.isSuccess && (
            <p className="text-sm text-green-600">Work submitted successfully!</p>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
