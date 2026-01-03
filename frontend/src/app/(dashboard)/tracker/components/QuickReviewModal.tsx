"use client";

import { useState, useEffect, useCallback } from "react";
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
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { Loader2, Clock, DollarSign, Calendar, Zap } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import {
  ds,
  proposalStatusColors,
  ALL_PROPOSAL_STATUSES,
} from "@/lib/design-system";
import { type ProposalStatus } from "@/lib/constants";

interface QuickReviewModalProps {
  proposal: ProposalTrackerItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function QuickReviewModal({
  proposal,
  open,
  onOpenChange,
}: QuickReviewModalProps) {
  const queryClient = useQueryClient();

  // Form state
  const [status, setStatus] = useState<string>("");
  const [quickNote, setQuickNote] = useState("");
  const [markFollowUp, setMarkFollowUp] = useState(false);
  const [followUpAction, setFollowUpAction] = useState("");

  // Default follow-up action text
  const defaultFollowUpAction = proposal
    ? `Follow up on ${proposal.project_code}`
    : "";

  // Track if anything changed
  const hasChanges =
    (status && status !== proposal?.current_status) ||
    quickNote.trim() !== "" ||
    (markFollowUp && followUpAction.trim() !== "");

  // Reset form when dialog opens with new proposal
  useEffect(() => {
    if (proposal && open) {
      setStatus(proposal.current_status);
      setQuickNote("");
      setMarkFollowUp(false);
      setFollowUpAction(`Follow up on ${proposal.project_code}`);
    }
  }, [proposal, open]);

  // Mutation for saving changes
  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!proposal) throw new Error("No proposal selected");

      const updates: Record<string, unknown> = {};

      // Only include changed status
      if (status && status !== proposal.current_status) {
        updates.current_status = status as ProposalStatus;
      }

      // Add quick note as current_remark
      if (quickNote.trim()) {
        updates.current_remark = quickNote.trim();
      }

      // Add follow-up action using existing action_needed field
      if (markFollowUp && followUpAction.trim()) {
        updates.action_needed = followUpAction.trim();
      }

      // Only call API if there are updates
      if (Object.keys(updates).length > 0) {
        return api.updateProposalTracker(proposal.project_code, updates);
      }

      return { success: true, message: "No changes", updated_fields: [] };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerList"] });
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerStats"] });

      // Show success message
      const messages: string[] = [];
      if (status !== proposal?.current_status) {
        messages.push(`Status updated to ${status}`);
      }
      if (quickNote.trim()) {
        messages.push("Note added");
      }
      if (markFollowUp && followUpAction.trim()) {
        messages.push("Follow-up action set");
      }

      if (messages.length > 0) {
        toast.success(messages.join(", "));
      }

      onOpenChange(false);
    },
    onError: (error: unknown) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to save changes"
      );
    },
  });

  // Handle save
  const handleSave = useCallback(() => {
    if (!hasChanges) {
      onOpenChange(false);
      return;
    }
    saveMutation.mutate();
  }, [hasChanges, saveMutation, onOpenChange]);

  // Keyboard shortcuts
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Enter to save (only if not in textarea or input with shift)
      if (
        e.key === "Enter" &&
        !e.shiftKey &&
        !(e.target instanceof HTMLTextAreaElement) &&
        !(e.target instanceof HTMLInputElement)
      ) {
        e.preventDefault();
        handleSave();
      }
      // Esc to close (handled by Dialog but we ensure it works)
      if (e.key === "Escape") {
        onOpenChange(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, handleSave, onOpenChange]);

  if (!proposal) return null;

  // Format last activity - use last_email_date or fall back to days_in_current_status
  const lastActivityDisplay = proposal.last_email_date
    ? new Date(proposal.last_email_date).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      })
    : proposal.days_in_current_status > 0
      ? `${proposal.days_in_current_status}d ago`
      : "No activity";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={cn("sm:max-w-[500px]", ds.borderRadius.card)}
        onKeyDown={(e) => {
          // Prevent dialog close on Enter in textarea/input
          if (
            e.key === "Enter" &&
            (e.target instanceof HTMLTextAreaElement ||
              e.target instanceof HTMLInputElement)
          ) {
            e.stopPropagation();
          }
        }}
      >
        <DialogHeader>
          <DialogTitle
            className={cn(
              ds.typography.heading2,
              ds.textColors.primary,
              "flex items-center gap-2"
            )}
          >
            <Zap className="h-5 w-5 text-amber-500" />
            Quick Review
          </DialogTitle>
          <DialogDescription
            className={cn(ds.typography.body, ds.textColors.secondary)}
          >
            <span className="font-semibold text-slate-700">
              {proposal.project_code}
            </span>{" "}
            - {proposal.project_name}
          </DialogDescription>
        </DialogHeader>

        {/* Proposal Summary */}
        <div className="grid grid-cols-3 gap-3 py-3 px-1 bg-slate-50 rounded-lg">
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-slate-400" />
            <div>
              <p className="text-xs text-slate-500">Value</p>
              <p className="text-sm font-medium text-slate-700">
                {formatCurrency(proposal.project_value)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-slate-400" />
            <div>
              <p className="text-xs text-slate-500">Days in Status</p>
              <p className="text-sm font-medium text-slate-700">
                {proposal.days_in_current_status}d
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-slate-400" />
            <div>
              <p className="text-xs text-slate-500">Last Activity</p>
              <p className="text-sm font-medium text-slate-700">
                {lastActivityDisplay}
              </p>
            </div>
          </div>
        </div>

        {/* Current context if exists */}
        {proposal.current_remark && (
          <div className="text-sm text-slate-600 bg-blue-50 border border-blue-100 rounded-md p-3">
            <span className="font-medium text-blue-700">Current note:</span>{" "}
            {proposal.current_remark}
          </div>
        )}

        {/* Existing action if any */}
        {proposal.action_needed && (
          <div className="text-sm text-slate-600 bg-amber-50 border border-amber-100 rounded-md p-3">
            <span className="font-medium text-amber-700">Current action:</span>{" "}
            {proposal.action_needed}
          </div>
        )}

        {/* Form */}
        <div className="grid gap-4 py-2">
          {/* Status Update */}
          <div className="grid gap-2">
            <Label htmlFor="status">Status</Label>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger
                id="status"
                className={cn(
                  ds.borderRadius.input,
                  proposalStatusColors[status as ProposalStatus]?.bg,
                  proposalStatusColors[status as ProposalStatus]?.text
                )}
              >
                <SelectValue placeholder="Select status..." />
              </SelectTrigger>
              <SelectContent>
                {ALL_PROPOSAL_STATUSES.map((s) => (
                  <SelectItem key={s} value={s}>
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded text-xs",
                        proposalStatusColors[s]?.bg,
                        proposalStatusColors[s]?.text
                      )}
                    >
                      {s}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Quick Note */}
          <div className="grid gap-2">
            <Label htmlFor="quick_note">
              Quick Note{" "}
              <span className="text-slate-400 text-xs">(optional)</span>
            </Label>
            <Textarea
              id="quick_note"
              value={quickNote}
              onChange={(e) => setQuickNote(e.target.value)}
              placeholder="Add a quick note about this proposal..."
              rows={2}
              className={ds.borderRadius.input}
            />
          </div>

          {/* Mark for Follow-up */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="follow_up"
                checked={markFollowUp}
                onCheckedChange={(checked) => setMarkFollowUp(checked === true)}
              />
              <Label
                htmlFor="follow_up"
                className="text-sm font-normal cursor-pointer"
              >
                Set follow-up action
              </Label>
            </div>
            {markFollowUp && (
              <Input
                value={followUpAction}
                onChange={(e) => setFollowUpAction(e.target.value)}
                placeholder="e.g., Send revised proposal, Schedule call..."
                className={cn(ds.borderRadius.input, "mt-2")}
              />
            )}
          </div>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <div className="text-xs text-slate-400 mr-auto hidden sm:block">
            Press Enter to save, Esc to close
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={saveMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleSave}
            disabled={saveMutation.isPending}
            className="bg-amber-600 hover:bg-amber-700"
          >
            {saveMutation.isPending && (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            )}
            {hasChanges ? "Save Changes" : "Close"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
