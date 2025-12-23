"use client";

import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Project } from "@/lib/types";
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
import { toast } from "sonner";
import { Loader2, Save, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

interface ProjectQuickEditDialogProps {
  project: Project | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ProjectQuickEditDialog({
  project,
  open,
  onOpenChange,
}: ProjectQuickEditDialogProps) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    project_title: "",
    total_fee_usd: 0,
    country: "",
    city: "",
    status: "",
    notes: "",
    contract_term_months: 0,
    team_lead: "",
    current_phase: "",
    target_completion: "",
    payment_due_days: 30,
    payment_terms: "",
    late_payment_interest_rate: 0,
  });

  // Update form data when project changes
  useEffect(() => {
    if (project) {
      setFormData({
        project_title: (project.project_title as string) || "",
        total_fee_usd: (project.total_fee_usd as number) || 0,
        country: (project.country as string) || "",
        city: (project.city as string) || "",
        status: (project.status as string) || "",
        notes: (project.notes as string) || "",
        contract_term_months: (project.contract_term_months as number) || 0,
        team_lead: (project.team_lead as string) || "",
        current_phase: (project.current_phase as string) || "",
        target_completion: (project.target_completion as string) || "",
        payment_due_days: (project.payment_due_days as number) || 30,
        payment_terms: (project.payment_terms as string) || "",
        late_payment_interest_rate: (project.late_payment_interest_rate as number) || 0,
      });
    }
  }, [project]);

  const updateMutation = useMutation({
    mutationFn: (updates: Record<string, unknown>) => {
      if (!project) throw new Error("No project selected");
      return api.updateProject(project.project_code as string, updates);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", "active"] });
      toast.success("Project updated successfully");
      onOpenChange(false);
    },
    onError: (error: unknown) => {
      const errorMessage = error instanceof Error ? error.message : "Failed to update project";
      toast.error(errorMessage);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const updates: Record<string, unknown> = {};
    if (formData.project_title) updates.project_title = formData.project_title;
    if (formData.total_fee_usd) updates.total_fee_usd = formData.total_fee_usd;
    if (formData.country) updates.country = formData.country;
    if (formData.city) updates.city = formData.city;
    if (formData.status) updates.status = formData.status;
    if (formData.notes) updates.notes = formData.notes;
    if (formData.contract_term_months) updates.contract_term_months = formData.contract_term_months;
    if (formData.team_lead) updates.team_lead = formData.team_lead;
    if (formData.current_phase) updates.current_phase = formData.current_phase;
    if (formData.target_completion) updates.target_completion = formData.target_completion;
    if (formData.payment_due_days) updates.payment_due_days = formData.payment_due_days;
    if (formData.payment_terms) updates.payment_terms = formData.payment_terms;
    if (formData.late_payment_interest_rate) updates.late_payment_interest_rate = formData.late_payment_interest_rate;

    updateMutation.mutate(updates);
  };

  if (!project) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn("max-w-3xl max-h-[90vh] overflow-y-auto", ds.shadows.lg)}>
        <DialogHeader>
          <DialogTitle className={cn(ds.typography.heading2)}>
            Edit Project: {project.project_code}
          </DialogTitle>
          <DialogDescription className={cn(ds.typography.body, ds.textColors.secondary)}>
            Update project information, contract terms, and team details
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className={cn("space-y-4 rounded-lg border p-4", ds.borderRadius.card, "border-slate-200 bg-slate-50")}>
            <h3 className={cn(ds.typography.heading3, ds.textColors.primary)}>Basic Information</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="project_title" className={cn(ds.typography.label)}>Project Title</Label>
                <Input
                  id="project_title"
                  value={formData.project_title}
                  onChange={(e) => setFormData({ ...formData, project_title: e.target.value })}
                  className={cn(ds.borderRadius.input)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="total_fee_usd" className={cn(ds.typography.label)}>Total Fee (USD)</Label>
                <Input
                  id="total_fee_usd"
                  type="number"
                  value={formData.total_fee_usd}
                  onChange={(e) => setFormData({ ...formData, total_fee_usd: parseFloat(e.target.value) || 0 })}
                  className={cn(ds.borderRadius.input)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="country" className={cn(ds.typography.label)}>Country</Label>
                <Input
                  id="country"
                  value={formData.country}
                  onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                  className={cn(ds.borderRadius.input)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="city" className={cn(ds.typography.label)}>City</Label>
                <Input
                  id="city"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  className={cn(ds.borderRadius.input)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="status" className={cn(ds.typography.label)}>Status</Label>
                <Input
                  id="status"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className={cn(ds.borderRadius.input)}
                />
              </div>
            </div>
          </div>

          {/* Team & Schedule */}
          <div className={cn("space-y-4 rounded-lg border p-4", ds.borderRadius.card, "border-slate-200 bg-slate-50")}>
            <h3 className={cn(ds.typography.heading3, ds.textColors.primary)}>Team & Schedule</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="team_lead" className={cn(ds.typography.label)}>Team Lead</Label>
                <Input
                  id="team_lead"
                  value={formData.team_lead}
                  onChange={(e) => setFormData({ ...formData, team_lead: e.target.value })}
                  placeholder="Project manager or team lead"
                  className={cn(ds.borderRadius.input)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="current_phase" className={cn(ds.typography.label)}>Current Phase</Label>
                <Input
                  id="current_phase"
                  value={formData.current_phase}
                  onChange={(e) => setFormData({ ...formData, current_phase: e.target.value })}
                  placeholder="e.g., Concept Design, DD, CD"
                  className={cn(ds.borderRadius.input)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="target_completion" className={cn(ds.typography.label)}>Target Completion</Label>
                <Input
                  id="target_completion"
                  type="date"
                  value={formData.target_completion}
                  onChange={(e) => setFormData({ ...formData, target_completion: e.target.value })}
                  className={cn(ds.borderRadius.input)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="contract_term_months" className={cn(ds.typography.label)}>Contract Term (months)</Label>
                <Input
                  id="contract_term_months"
                  type="number"
                  value={formData.contract_term_months}
                  onChange={(e) => setFormData({ ...formData, contract_term_months: parseInt(e.target.value) || 0 })}
                  className={cn(ds.borderRadius.input)}
                />
              </div>
            </div>
          </div>

          {/* Contract Terms */}
          <div className={cn("space-y-4 rounded-lg border p-4", ds.borderRadius.card, "border-slate-200 bg-slate-50")}>
            <h3 className={cn(ds.typography.heading3, ds.textColors.primary)}>Contract Terms</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="payment_due_days" className={cn(ds.typography.label)}>Payment Due (days after invoice)</Label>
                <Input
                  id="payment_due_days"
                  type="number"
                  value={formData.payment_due_days}
                  onChange={(e) => setFormData({ ...formData, payment_due_days: parseInt(e.target.value) || 30 })}
                  placeholder="e.g., 30, 60, 90"
                  className={cn(ds.borderRadius.input)}
                />
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                  Days until payment due, or days until work can stop
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="late_payment_interest_rate" className={cn(ds.typography.label)}>Late Payment Interest (%)</Label>
                <Input
                  id="late_payment_interest_rate"
                  type="number"
                  step="0.01"
                  value={formData.late_payment_interest_rate}
                  onChange={(e) => setFormData({ ...formData, late_payment_interest_rate: parseFloat(e.target.value) || 0 })}
                  placeholder="e.g., 1.5"
                  className={cn(ds.borderRadius.input)}
                />
              </div>

              <div className="col-span-2 space-y-2">
                <Label htmlFor="payment_terms" className={cn(ds.typography.label)}>Payment Terms (full text)</Label>
                <Textarea
                  id="payment_terms"
                  value={formData.payment_terms}
                  onChange={(e) => setFormData({ ...formData, payment_terms: e.target.value })}
                  placeholder="e.g., Net 30 days from invoice date. 1.5% monthly interest on late payments. Work suspension after 90 days overdue."
                  className={cn(ds.borderRadius.input)}
                  rows={3}
                />
              </div>
            </div>
          </div>

          {/* Notes */}
          <div className={cn("space-y-4 rounded-lg border p-4", ds.borderRadius.card, "border-slate-200 bg-slate-50")}>
            <h3 className={cn(ds.typography.heading3, ds.textColors.primary)}>Notes & Context</h3>

            <div className="space-y-2">
              <Label htmlFor="notes" className={cn(ds.typography.label)}>Project Notes</Label>
              <Textarea
                id="notes"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Add any additional context, special requirements, or important notes..."
                className={cn(ds.borderRadius.input)}
                rows={4}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={updateMutation.isPending}
              className={cn(ds.gap.normal)}
            >
              <X className="h-4 w-4" />
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={updateMutation.isPending}
              className={cn(ds.gap.normal)}
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Save Changes
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
