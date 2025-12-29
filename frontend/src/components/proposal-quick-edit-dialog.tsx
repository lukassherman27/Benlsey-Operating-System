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
import { useCurrentUser } from "@/hooks/useCurrentUser";

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
  const { email: currentUserEmail } = useCurrentUser();
  const [formData, setFormData] = useState({
    project_name: proposal?.project_name || "",
    country: proposal?.country || "",
    current_status: proposal?.current_status || "First Contact",
    current_remark: proposal?.current_remark || "",
    waiting_on: proposal?.waiting_on || "",
    next_steps: proposal?.next_steps || "",
    project_value: proposal?.project_value || 0,
    first_contact_date: proposal?.first_contact_date || "",
    proposal_sent_date: proposal?.proposal_sent_date || "",
    contact_person: proposal?.contact_person || "",
    contact_email: proposal?.contact_email || "",
    contact_phone: proposal?.contact_phone || "",
    project_summary: proposal?.project_summary || "",
    latest_email_context: proposal?.latest_email_context || "",
    last_email_date: proposal?.last_email_date || "",
  });

  // Update form data when proposal changes
  useEffect(() => {
    if (proposal) {
      setFormData({
        project_name: proposal.project_name || "",
        country: proposal.country || "",
        current_status: proposal.current_status,
        current_remark: proposal.current_remark || "",
        waiting_on: proposal.waiting_on || "",
        next_steps: proposal.next_steps || "",
        project_value: proposal.project_value || 0,
        first_contact_date: proposal.first_contact_date || "",
        proposal_sent_date: proposal.proposal_sent_date || "",
        contact_person: proposal.contact_person || "",
        contact_email: proposal.contact_email || "",
        contact_phone: proposal.contact_phone || "",
        project_summary: proposal.project_summary || "",
        latest_email_context: proposal.latest_email_context || "",
        last_email_date: proposal.last_email_date || "",
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    if (formData.project_name !== (proposal?.project_name || "")) {
      updates.project_name = formData.project_name;
    }
    if (formData.country !== (proposal?.country || "")) {
      updates.country = formData.country;
    }
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
    if (formData.proposal_sent_date !== (proposal?.proposal_sent_date || "")) {
      updates.proposal_sent_date = formData.proposal_sent_date;
    }
    if (formData.contact_person !== (proposal?.contact_person || "")) {
      updates.contact_person = formData.contact_person;
    }
    if (formData.contact_email !== (proposal?.contact_email || "")) {
      updates.contact_email = formData.contact_email;
    }
    if (formData.contact_phone !== (proposal?.contact_phone || "")) {
      updates.contact_phone = formData.contact_phone;
    }
    if (formData.project_summary !== (proposal?.project_summary || "")) {
      updates.project_summary = formData.project_summary;
    }
    if (formData.latest_email_context !== (proposal?.latest_email_context || "")) {
      updates.latest_email_context = formData.latest_email_context;
    }
    if (formData.last_email_date !== (proposal?.last_email_date || "")) {
      updates.last_email_date = formData.last_email_date;
    }

    if (Object.keys(updates).length === 0) {
      toast.info("No changes to save");
      return;
    }

    // Add provenance tracking metadata
    updates.updated_by = currentUserEmail || "user";
    updates.source_type = "manual";
    updates.change_reason = "Updated via dashboard";

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
                {/* Project Name */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="project_name" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Project Name
                  </Label>
                  <Input
                    id="project_name"
                    type="text"
                    value={formData.project_name}
                    onChange={(e) =>
                      setFormData({ ...formData, project_name: e.target.value })
                    }
                    className={ds.borderRadius.input}
                  />
                </div>

                {/* Country */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="country" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Country
                  </Label>
                  <Input
                    id="country"
                    type="text"
                    value={formData.country}
                    onChange={(e) =>
                      setFormData({ ...formData, country: e.target.value })
                    }
                    className={ds.borderRadius.input}
                  />
                </div>

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

                {/* Proposal Sent Date */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="proposal_sent_date" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Proposal Sent Date
                  </Label>
                  <Input
                    id="proposal_sent_date"
                    type="date"
                    value={formData.proposal_sent_date}
                    onChange={(e) =>
                      setFormData({ ...formData, proposal_sent_date: e.target.value })
                    }
                    className={cn(ds.borderRadius.input, ds.typography.body)}
                  />
                </div>

                {/* Divider - Contact Information */}
                <div className="pt-4 pb-2">
                  <h4 className={cn(ds.typography.heading3, ds.textColors.primary)}>
                    Contact Information
                  </h4>
                </div>

                {/* Contact Person */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="contact_person" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Contact Person
                  </Label>
                  <Input
                    id="contact_person"
                    type="text"
                    value={formData.contact_person}
                    onChange={(e) =>
                      setFormData({ ...formData, contact_person: e.target.value })
                    }
                    placeholder="John Doe"
                    className={ds.borderRadius.input}
                  />
                </div>

                {/* Contact Email */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="contact_email" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Contact Email
                  </Label>
                  <Input
                    id="contact_email"
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) =>
                      setFormData({ ...formData, contact_email: e.target.value })
                    }
                    placeholder="john@example.com"
                    className={ds.borderRadius.input}
                  />
                </div>

                {/* Contact Phone */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="contact_phone" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Contact Phone
                  </Label>
                  <Input
                    id="contact_phone"
                    type="tel"
                    value={formData.contact_phone}
                    onChange={(e) =>
                      setFormData({ ...formData, contact_phone: e.target.value })
                    }
                    placeholder="+1 234 567 8900"
                    className={ds.borderRadius.input}
                  />
                </div>

                {/* Divider - Project Details */}
                <div className="pt-4 pb-2">
                  <h4 className={cn(ds.typography.heading3, ds.textColors.primary)}>
                    Project Details
                  </h4>
                </div>

                {/* Project Summary */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="project_summary" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Project Summary
                  </Label>
                  <Textarea
                    id="project_summary"
                    value={formData.project_summary}
                    onChange={(e) =>
                      setFormData({ ...formData, project_summary: e.target.value })
                    }
                    rows={3}
                    placeholder="Brief description of the project..."
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

                {/* Divider - Email Intelligence */}
                <div className="pt-4 pb-2">
                  <h4 className={cn(ds.typography.heading3, ds.textColors.primary)}>
                    Email Intelligence
                  </h4>
                </div>

                {/* Latest Email Context */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="email_context" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Latest Email Context
                  </Label>
                  <Textarea
                    id="email_context"
                    value={formData.latest_email_context}
                    onChange={(e) =>
                      setFormData({ ...formData, latest_email_context: e.target.value })
                    }
                    rows={3}
                    placeholder="Summary of latest email communication..."
                    className={cn(ds.borderRadius.input, ds.typography.body)}
                  />
                </div>

                {/* Last Email Date */}
                <div className={cn("grid", ds.gap.tight)}>
                  <Label htmlFor="last_email_date" className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Last Email Date
                  </Label>
                  <Input
                    id="last_email_date"
                    type="date"
                    value={formData.last_email_date}
                    onChange={(e) =>
                      setFormData({ ...formData, last_email_date: e.target.value })
                    }
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
