"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { CalendarIcon, Loader2, Plus, Pencil, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const DELIVERABLE_TYPES = [
  { value: "drawing", label: "Drawing" },
  { value: "presentation", label: "Presentation" },
  { value: "document", label: "Document" },
  { value: "model", label: "3D Model" },
  { value: "specification", label: "Specification" },
  { value: "report", label: "Report" },
  { value: "review", label: "Review" },
  { value: "other", label: "Other" },
];

const PHASES = [
  { value: "concept_design", label: "Concept Design" },
  { value: "schematic_design", label: "Schematic Design" },
  { value: "design_development", label: "Design Development" },
  { value: "construction_drawings", label: "Construction Drawings" },
  { value: "construction_observation", label: "Construction Administration" },
];

const STATUSES = [
  { value: "pending", label: "Pending" },
  { value: "in_progress", label: "In Progress" },
  { value: "submitted", label: "Submitted" },
  { value: "revision", label: "Needs Revision" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "cancelled", label: "Cancelled" },
];

const PRIORITIES = [
  { value: "low", label: "Low" },
  { value: "normal", label: "Normal" },
  { value: "high", label: "High" },
  { value: "critical", label: "Critical" },
];

interface Deliverable {
  deliverable_id: number;
  name?: string;
  deliverable_name?: string;
  description?: string;
  deliverable_type?: string;
  phase?: string;
  due_date?: string;
  start_date?: string;
  status?: string;
  priority?: string;
  assigned_pm?: string;
  owner_staff_id?: number;
}

interface AddDeliverableFormProps {
  projectCode: string;
  editingDeliverable?: Deliverable | null;
  onClose: () => void;
  onSuccess?: () => void;
}

interface StaffMember {
  staff_id: number;
  display_name: string;
}

export function AddDeliverableForm({
  projectCode,
  editingDeliverable,
  onClose,
  onSuccess,
}: AddDeliverableFormProps) {
  const queryClient = useQueryClient();
  const isEditing = !!editingDeliverable;

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [deliverableType, setDeliverableType] = useState("");
  const [phase, setPhase] = useState("");
  const [dueDate, setDueDate] = useState<Date | undefined>();
  const [startDate, setStartDate] = useState<Date | undefined>();
  const [status, setStatus] = useState("pending");
  const [priority, setPriority] = useState("normal");
  const [ownerId, setOwnerId] = useState("");

  // Populate form when editing
  useEffect(() => {
    if (editingDeliverable) {
      setName(editingDeliverable.name || editingDeliverable.deliverable_name || "");
      setDescription(editingDeliverable.description || "");
      setDeliverableType(editingDeliverable.deliverable_type || "");
      setPhase(editingDeliverable.phase || "");
      setDueDate(editingDeliverable.due_date ? new Date(editingDeliverable.due_date) : undefined);
      setStartDate(editingDeliverable.start_date ? new Date(editingDeliverable.start_date) : undefined);
      setStatus(editingDeliverable.status || "pending");
      setPriority(editingDeliverable.priority || "normal");
      setOwnerId(editingDeliverable.owner_staff_id?.toString() || "");
    }
  }, [editingDeliverable]);

  // Fetch staff for owner dropdown
  const staffQuery = useQuery({
    queryKey: ["staff"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/staff`);
      if (!res.ok) throw new Error("Failed to fetch staff");
      return res.json();
    },
  });

  const staffList: StaffMember[] = staffQuery.data?.staff ?? [];

  // Create mutation
  const createMutation = useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const res = await fetch(`${API_BASE}/api/deliverables`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Failed to create");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deliverables", projectCode] });
      onSuccess?.();
      onClose();
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const res = await fetch(`${API_BASE}/api/deliverables/${editingDeliverable?.deliverable_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Failed to update");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deliverables", projectCode] });
      onSuccess?.();
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const data: Record<string, unknown> = {
      project_code: projectCode,
      name,
      description: description || undefined,
      deliverable_type: deliverableType || undefined,
      phase: phase || undefined,
      due_date: dueDate ? format(dueDate, "yyyy-MM-dd") : undefined,
      start_date: startDate ? format(startDate, "yyyy-MM-dd") : undefined,
      status,
      priority,
      owner_staff_id: ownerId ? parseInt(ownerId) : undefined,
    };

    if (isEditing) {
      updateMutation.mutate(data);
    } else {
      createMutation.mutate(data);
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {isEditing ? (
              <>
                <Pencil className="h-5 w-5 text-teal-600" />
                Edit Deliverable
              </>
            ) : (
              <>
                <Plus className="h-5 w-5 text-teal-600" />
                Add Deliverable
              </>
            )}
          </CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div className="space-y-2">
              <Label>Name *</Label>
              <Input
                placeholder="e.g., Final Concept Presentation"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                placeholder="Optional description..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* Type */}
              <div className="space-y-2">
                <Label>Type</Label>
                <Select value={deliverableType} onValueChange={setDeliverableType}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {DELIVERABLE_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
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

            <div className="grid grid-cols-2 gap-4">
              {/* Start Date */}
              <div className="space-y-2">
                <Label>Start Date</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-full justify-start text-left font-normal",
                        !startDate && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {startDate ? format(startDate, "MMM d, yyyy") : "Select"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={startDate}
                      onSelect={setStartDate}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>

              {/* Due Date */}
              <div className="space-y-2">
                <Label>Due Date</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-full justify-start text-left font-normal",
                        !dueDate && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {dueDate ? format(dueDate, "MMM d, yyyy") : "Select"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={dueDate}
                      onSelect={setDueDate}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* Status */}
              <div className="space-y-2">
                <Label>Status</Label>
                <Select value={status} onValueChange={setStatus}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {STATUSES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Priority */}
              <div className="space-y-2">
                <Label>Priority</Label>
                <Select value={priority} onValueChange={setPriority}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PRIORITIES.map((p) => (
                      <SelectItem key={p.value} value={p.value}>
                        {p.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Owner */}
            <div className="space-y-2">
              <Label>Owner</Label>
              <Select value={ownerId} onValueChange={setOwnerId}>
                <SelectTrigger>
                  <SelectValue placeholder="Assign owner" />
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

            {/* Actions */}
            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={!name || isPending}>
                {isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {isEditing ? "Updating..." : "Creating..."}
                  </>
                ) : isEditing ? (
                  "Update Deliverable"
                ) : (
                  "Add Deliverable"
                )}
              </Button>
            </div>

            {(createMutation.isError || updateMutation.isError) && (
              <p className="text-sm text-red-500 text-center">
                Error: {createMutation.error?.message || updateMutation.error?.message}
              </p>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
