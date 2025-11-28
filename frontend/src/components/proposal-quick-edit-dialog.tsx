"use client";

import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ProposalTrackerItem, ProposalStatus } from "@/lib/types";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ProposalStatusTimeline } from "./proposal-status-timeline";
import { ProposalEmailIntelligence } from "./proposal-email-intelligence";
import { toast } from "sonner";
import { Loader2, Edit, History, Mail } from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

interface ProposalQuickEditDialogProps {
  proposal: ProposalTrackerItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ProposalQuickEditDialog({
  proposal,
  open,
  onOpenChange,
}: ProposalQuickEditDialogProps) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    current_status: proposal?.current_status || "First Contact",
    current_remark: proposal?.current_remark || "",
    waiting_on: proposal?.waiting_on || "",
    next_steps: proposal?.next_steps || "",
    project_value: proposal?.project_value || 0,
    first_contact_date: proposal?.first_contact_date || "",
  });

  // Update form data when proposal changes
  useEffect(() => {
    if (proposal) {
      setFormData({
        current_status: proposal.current_status,
        current_remark: proposal.current_remark || "",
        waiting_on: proposal.waiting_on || "",
        next_steps: proposal.next_steps || "",
        project_value: proposal.project_value || 0,
        first_contact_date: proposal.first_contact_date || "",
      });
    }
  }, [proposal?.project_code]); // Only update when a different proposal is selected

  const updateMutation = useMutation({
    mutationFn: (updates: Record<string, unknown>) => {
      if (!proposal) throw new Error("No proposal selected");
      return api.updateProposalTracker(proposal.project_code, updates);
    },
    onSuccess: () => {
      // Invalidate queries to refetch data
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerList"] });
      queryClient.invalidateQueries({ queryKey: ["proposalTrackerStats"] });
      toast.success("Proposal updated successfully");
      onOpenChange(false);
    },
    onError: (error: unknown) => {
      const errorMessage = error instanceof Error ? error.message : "Failed to update proposal";
      toast.error(errorMessage);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const updates: Record<string, unknown> = {};

    // Only include changed fields
    if (formData.current_status !== proposal?.current_status) {
      updates.current_status = formData.current_status;
    }
    if (formData.current_remark !== (proposal?.current_remark || "")) {
      updates.current_remark = formData.current_remark;
    }
    if (formData.waiting_on !== (proposal?.waiting_on || "")) {
      updates.waiting_on = formData.waiting_on;
    }
    if (formData.next_steps !== (proposal?.next_steps || "")) {
      updates.next_steps = formData.next_steps;
    }
    if (formData.project_value !== proposal?.project_value) {
      updates.project_value = formData.project_value;
    }
    if (formData.first_contact_date !== (proposal?.first_contact_date || "")) {
      updates.first_contact_date = formData.first_contact_date;
    }

    if (Object.keys(updates).length === 0) {
      toast.info("No changes to save");
      return;
    }

    updateMutation.mutate(updates);
  };

  if (!proposal) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn("sm:max-w-[600px] max-h-[90vh] overflow-y-auto", ds.borderRadius.card)}>
        <DialogHeader>
          <DialogTitle className={cn(ds.typography.heading2, ds.textColors.primary)}>
            {proposal.project_code}
          </DialogTitle>
          <DialogDescription className={cn(ds.typography.body, ds.textColors.secondary)}>
            {proposal.project_name}
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="edit" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="edit" className={ds.gap.tight}>
              <Edit className="h-4 w-4" />
              Edit
            </TabsTrigger>
            <TabsTrigger value="history" className={ds.gap.tight}>
              <History className="h-4 w-4" />
              History
            </TabsTrigger>
            <TabsTrigger value="emails" className={ds.gap.tight}>
              <Mail className="h-4 w-4" />
              Emails
            </TabsTrigger>
          </TabsList>

          <TabsContent value="edit" className={cn(ds.gap.normal, "space-y-4")}>
            <form onSubmit={handleSubmit}>
              <div className={cn("grid py-4", ds.gap.normal)}>
                {/* Status */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="status" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Status
                  </Label>
                  <Select
                    value={formData.current_status}
                    onValueChange={(value) =>
                      setFormData({ ...formData, current_status: value as ProposalStatus })
                    }
                  >
                    <SelectTrigger id="status" className={ds.borderRadius.input}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="First Contact">First Contact</SelectItem>
                      <SelectItem value="Drafting">Drafting</SelectItem>
                      <SelectItem value="Proposal Sent">Proposal Sent</SelectItem>
                      <SelectItem value="On Hold">On Hold</SelectItem>
                      <SelectItem value="Contract Signed">Contract Signed</SelectItem>
                      <SelectItem value="Active">Active</SelectItem>
                      <SelectItem value="Cancelled">Cancelled</SelectItem>
                      <SelectItem value="Closed Lost">Closed Lost</SelectItem>
                      <SelectItem value="Withdrawn">Withdrawn</SelectItem>
                      <SelectItem value="Archived">Archived</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Project Value */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="value" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Project Value ($)
                  </Label>
                  <Input
                    id="value"
                    type="number"
                    value={formData.project_value}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        project_value: parseFloat(e.target.value) || 0,
                      })
                    }
                    className={cn(ds.borderRadius.input, ds.typography.body)}
                    placeholder="0"
                  />
                </div>

                {/* First Contact Date */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="first_contact_date" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    First Contact Date
                  </Label>
                  <Input
                    id="first_contact_date"
                    type="date"
                    value={formData.first_contact_date}
                    onChange={(e) =>
                      setFormData({ ...formData, first_contact_date: e.target.value })
                    }
                    className={cn(ds.borderRadius.input, ds.typography.body)}
                  />
                </div>

                {/* Current Remark */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="remark" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Current Remark
                  </Label>
                  <Textarea
                    id="remark"
                    value={formData.current_remark}
                    onChange={(e) =>
                      setFormData({ ...formData, current_remark: e.target.value })
                    }
                    rows={3}
                    placeholder="Latest update or status..."
                    className={cn(ds.borderRadius.input, ds.typography.body)}
                  />
                </div>

                {/* Waiting On */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="waiting" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Waiting On
                  </Label>
                  <Input
                    id="waiting"
                    value={formData.waiting_on}
                    onChange={(e) =>
                      setFormData({ ...formData, waiting_on: e.target.value })
                    }
                    placeholder="Client decision, documents, etc."
                    className={cn(ds.borderRadius.input, ds.typography.body)}
                  />
                </div>

                {/* Next Steps */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="next" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Next Steps
                  </Label>
                  <Textarea
                    id="next"
                    value={formData.next_steps}
                    onChange={(e) =>
                      setFormData({ ...formData, next_steps: e.target.value })
                    }
                    rows={2}
                    placeholder="What needs to happen next..."
                    className={cn(ds.borderRadius.input, ds.typography.body)}
                  />
                </div>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                  disabled={updateMutation.isPending}
                  className={ds.borderRadius.button}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className={cn(ds.borderRadius.button, ds.gap.tight)}
                >
                  {updateMutation.isPending && (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  )}
                  Save Changes
                </Button>
              </DialogFooter>
            </form>
          </TabsContent>

          <TabsContent value="history" className={cn(ds.gap.normal, "space-y-4")}>
            <ProposalStatusTimeline projectCode={proposal.project_code} />
          </TabsContent>

          <TabsContent value="emails" className={cn(ds.gap.normal, "space-y-4")}>
            <ProposalEmailIntelligence projectCode={proposal.project_code} />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
