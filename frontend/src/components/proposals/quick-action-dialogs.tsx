"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ProposalTrackerItem } from "@/lib/types";
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
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { Loader2, Trophy, Ban, CalendarPlus } from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

// Lost reasons dropdown options (CRM best practice)
const LOST_REASONS = [
  { value: "price_budget", label: "Price / Budget" },
  { value: "timing_not_ready", label: "Timing / Not Ready" },
  { value: "competition", label: "Competition" },
  { value: "scope_mismatch", label: "Scope Mismatch" },
  { value: "no_response", label: "No Response" },
  { value: "client_internal", label: "Client Internal Changes" },
  { value: "other", label: "Other" },
] as const;

interface QuickActionDialogProps {
  proposal: ProposalTrackerItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

// =============================================================================
// MARK WON DIALOG
// =============================================================================

export function MarkWonDialog({
  proposal,
  open,
  onOpenChange,
  onSuccess,
}: QuickActionDialogProps) {
  const queryClient = useQueryClient();
  const today = new Date().toISOString().split("T")[0];

  const [wonDate, setWonDate] = useState(today);
  const [contractValue, setContractValue] = useState<number | "">(
    proposal?.project_value || ""
  );
  const [notes, setNotes] = useState("");

  // Reset form when dialog opens with new proposal
  const resetForm = () => {
    setWonDate(today);
    setContractValue(proposal?.project_value || "");
    setNotes("");
  };

  const markWonMutation = useMutation({
    mutationFn: async () => {
      if (!proposal) throw new Error("No proposal selected");

      return api.updateProposalTracker(proposal.project_code, {
        current_status: "Contract Signed",
        won_date: wonDate,
        contract_signed_date: wonDate,
        ...(contractValue !== "" && { project_value: contractValue }),
        ...(notes && { internal_notes: notes }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerList"] });
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerStats"] });
      toast.success(`${proposal?.project_name} marked as WON!`);
      resetForm();
      onOpenChange(false);
      onSuccess?.();
    },
    onError: (error: unknown) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to mark as won"
      );
    },
  });

  if (!proposal) return null;

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        if (!isOpen) resetForm();
        onOpenChange(isOpen);
      }}
    >
      <DialogContent className={cn("sm:max-w-[425px]", ds.borderRadius.card)}>
        <DialogHeader>
          <DialogTitle
            className={cn(
              ds.typography.heading2,
              ds.textColors.primary,
              "flex items-center gap-2"
            )}
          >
            <Trophy className="h-5 w-5 text-emerald-600" />
            Mark as Won
          </DialogTitle>
          <DialogDescription
            className={cn(ds.typography.body, ds.textColors.secondary)}
          >
            Congratulations! Mark{" "}
            <span className="font-semibold">{proposal.project_name}</span> as
            won.
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            markWonMutation.mutate();
          }}
        >
          <div className="grid gap-4 py-4">
            {/* Won Date */}
            <div className="grid gap-2">
              <Label htmlFor="won_date">Contract Signed Date</Label>
              <Input
                id="won_date"
                type="date"
                value={wonDate}
                onChange={(e) => setWonDate(e.target.value)}
                className={ds.borderRadius.input}
                required
              />
            </div>

            {/* Contract Value */}
            <div className="grid gap-2">
              <Label htmlFor="contract_value">
                Contract Value ($){" "}
                <span className="text-slate-400 text-xs">(optional)</span>
              </Label>
              <Input
                id="contract_value"
                type="number"
                value={contractValue}
                onChange={(e) =>
                  setContractValue(
                    e.target.value ? parseFloat(e.target.value) : ""
                  )
                }
                placeholder={
                  proposal.project_value
                    ? `Current: $${proposal.project_value.toLocaleString()}`
                    : "Enter value"
                }
                className={ds.borderRadius.input}
              />
            </div>

            {/* Notes */}
            <div className="grid gap-2">
              <Label htmlFor="won_notes">
                Notes <span className="text-slate-400 text-xs">(optional)</span>
              </Label>
              <Textarea
                id="won_notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Any notes about the deal..."
                rows={2}
                className={ds.borderRadius.input}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={markWonMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={markWonMutation.isPending}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {markWonMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              Mark as Won
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// =============================================================================
// MARK LOST DIALOG
// =============================================================================

export function MarkLostDialog({
  proposal,
  open,
  onOpenChange,
  onSuccess,
}: QuickActionDialogProps) {
  const queryClient = useQueryClient();
  const today = new Date().toISOString().split("T")[0];

  const [lostDate, setLostDate] = useState(today);
  const [lostReason, setLostReason] = useState("");
  const [lostToCompetitor, setLostToCompetitor] = useState("");
  const [notes, setNotes] = useState("");

  const resetForm = () => {
    setLostDate(today);
    setLostReason("");
    setLostToCompetitor("");
    setNotes("");
  };

  const markLostMutation = useMutation({
    mutationFn: async () => {
      if (!proposal) throw new Error("No proposal selected");

      return api.updateProposalTracker(proposal.project_code, {
        current_status: "Lost",
        lost_date: lostDate,
        lost_reason: lostReason,
        ...(lostToCompetitor && { lost_to_competitor: lostToCompetitor }),
        ...(notes && { internal_notes: notes }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerList"] });
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerStats"] });
      toast.success(`${proposal?.project_name} marked as Lost`);
      resetForm();
      onOpenChange(false);
      onSuccess?.();
    },
    onError: (error: unknown) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to mark as lost"
      );
    },
  });

  if (!proposal) return null;

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        if (!isOpen) resetForm();
        onOpenChange(isOpen);
      }}
    >
      <DialogContent className={cn("sm:max-w-[425px]", ds.borderRadius.card)}>
        <DialogHeader>
          <DialogTitle
            className={cn(
              ds.typography.heading2,
              ds.textColors.primary,
              "flex items-center gap-2"
            )}
          >
            <Ban className="h-5 w-5 text-red-600" />
            Mark as Lost
          </DialogTitle>
          <DialogDescription
            className={cn(ds.typography.body, ds.textColors.secondary)}
          >
            Mark <span className="font-semibold">{proposal.project_name}</span>{" "}
            as lost.
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!lostReason) {
              toast.error("Please select a reason");
              return;
            }
            markLostMutation.mutate();
          }}
        >
          <div className="grid gap-4 py-4">
            {/* Lost Date */}
            <div className="grid gap-2">
              <Label htmlFor="lost_date">Lost Date</Label>
              <Input
                id="lost_date"
                type="date"
                value={lostDate}
                onChange={(e) => setLostDate(e.target.value)}
                className={ds.borderRadius.input}
                required
              />
            </div>

            {/* Lost Reason */}
            <div className="grid gap-2">
              <Label htmlFor="lost_reason">
                Reason <span className="text-red-500">*</span>
              </Label>
              <Select value={lostReason} onValueChange={setLostReason}>
                <SelectTrigger className={ds.borderRadius.input}>
                  <SelectValue placeholder="Select reason..." />
                </SelectTrigger>
                <SelectContent>
                  {LOST_REASONS.map((reason) => (
                    <SelectItem key={reason.value} value={reason.value}>
                      {reason.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Lost to Competitor (show only if reason is competition) */}
            {lostReason === "competition" && (
              <div className="grid gap-2">
                <Label htmlFor="lost_to_competitor">
                  Competitor Name{" "}
                  <span className="text-slate-400 text-xs">(optional)</span>
                </Label>
                <Input
                  id="lost_to_competitor"
                  type="text"
                  value={lostToCompetitor}
                  onChange={(e) => setLostToCompetitor(e.target.value)}
                  placeholder="Enter competitor name..."
                  className={ds.borderRadius.input}
                />
              </div>
            )}

            {/* Notes */}
            <div className="grid gap-2">
              <Label htmlFor="lost_notes">
                Notes <span className="text-slate-400 text-xs">(optional)</span>
              </Label>
              <Textarea
                id="lost_notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Any notes about why this was lost..."
                rows={2}
                className={ds.borderRadius.input}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={markLostMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={markLostMutation.isPending || !lostReason}
              variant="destructive"
            >
              {markLostMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              Mark as Lost
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// =============================================================================
// CREATE FOLLOW-UP DIALOG
// =============================================================================

export function CreateFollowUpDialog({
  proposal,
  open,
  onOpenChange,
  onSuccess,
}: QuickActionDialogProps) {
  const queryClient = useQueryClient();

  // Default due date is 3 days from now
  const defaultDueDate = new Date();
  defaultDueDate.setDate(defaultDueDate.getDate() + 3);
  const defaultDueDateStr = defaultDueDate.toISOString().split("T")[0];

  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState(defaultDueDateStr);
  const [priority, setPriority] = useState("medium");
  const [notes, setNotes] = useState("");

  const resetForm = () => {
    setTitle("");
    setDueDate(defaultDueDateStr);
    setPriority("medium");
    setNotes("");
  };

  const createFollowUpMutation = useMutation({
    mutationFn: async () => {
      if (!proposal) throw new Error("No proposal selected");

      const taskTitle =
        title || `Follow up on ${proposal.project_code} (${proposal.project_name})`;

      return api.createTask({
        title: taskTitle,
        task_type: "follow_up",
        due_date: dueDate,
        priority,
        proposal_id: proposal.id,
        project_code: proposal.project_code,
        ...(notes && { description: notes }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerList"] });
      toast.success(`Follow-up task created for ${proposal?.project_name}`);
      resetForm();
      onOpenChange(false);
      onSuccess?.();
    },
    onError: (error: unknown) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to create follow-up"
      );
    },
  });

  if (!proposal) return null;

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        if (!isOpen) resetForm();
        onOpenChange(isOpen);
      }}
    >
      <DialogContent className={cn("sm:max-w-[425px]", ds.borderRadius.card)}>
        <DialogHeader>
          <DialogTitle
            className={cn(
              ds.typography.heading2,
              ds.textColors.primary,
              "flex items-center gap-2"
            )}
          >
            <CalendarPlus className="h-5 w-5 text-blue-600" />
            Create Follow-up
          </DialogTitle>
          <DialogDescription
            className={cn(ds.typography.body, ds.textColors.secondary)}
          >
            Create a follow-up task for{" "}
            <span className="font-semibold">{proposal.project_name}</span>
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            createFollowUpMutation.mutate();
          }}
        >
          <div className="grid gap-4 py-4">
            {/* Task Title */}
            <div className="grid gap-2">
              <Label htmlFor="task_title">
                Title{" "}
                <span className="text-slate-400 text-xs">
                  (auto-generated if empty)
                </span>
              </Label>
              <Input
                id="task_title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder={`Follow up on ${proposal.project_code}...`}
                className={ds.borderRadius.input}
              />
            </div>

            {/* Due Date */}
            <div className="grid gap-2">
              <Label htmlFor="due_date">Due Date</Label>
              <Input
                id="due_date"
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className={ds.borderRadius.input}
                required
              />
            </div>

            {/* Priority */}
            <div className="grid gap-2">
              <Label htmlFor="priority">Priority</Label>
              <Select value={priority} onValueChange={setPriority}>
                <SelectTrigger className={ds.borderRadius.input}>
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

            {/* Notes */}
            <div className="grid gap-2">
              <Label htmlFor="followup_notes">
                Notes <span className="text-slate-400 text-xs">(optional)</span>
              </Label>
              <Textarea
                id="followup_notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="What needs to be followed up on..."
                rows={2}
                className={ds.borderRadius.input}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createFollowUpMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createFollowUpMutation.isPending}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {createFollowUpMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              Create Follow-up
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
