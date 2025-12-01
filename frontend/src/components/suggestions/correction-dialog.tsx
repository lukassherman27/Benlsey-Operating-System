"use client";

import { useState, useEffect } from "react";
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
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Loader2, X, Sparkles } from "lucide-react";
import { SuggestionItem } from "@/lib/api";

interface ProjectOption {
  code: string;
  name: string;
  type?: 'project' | 'proposal';
}

interface CorrectionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  suggestion: SuggestionItem | null;
  projectOptions: ProjectOption[];
  proposalOptions?: ProjectOption[];
  onSubmit: (data: {
    rejection_reason: string;
    correct_project_code?: string;
    create_pattern: boolean;
    pattern_notes?: string;
  }) => void;
  isSubmitting: boolean;
}

const REJECTION_REASONS = [
  { value: 'wrong_project', label: 'Wrong project' },
  { value: 'wrong_contact', label: 'Wrong contact' },
  { value: 'spam_irrelevant', label: 'Spam / Irrelevant' },
  { value: 'duplicate', label: 'Duplicate' },
  { value: 'data_incorrect', label: 'Data is incorrect' },
  { value: 'other', label: 'Other' },
];

export function CorrectionDialog({
  open,
  onOpenChange,
  suggestion,
  projectOptions,
  proposalOptions = [],
  onSubmit,
  isSubmitting,
}: CorrectionDialogProps) {
  const [rejectionReason, setRejectionReason] = useState("wrong_project");
  const [correctProjectCode, setCorrectProjectCode] = useState("");
  const [createPattern, setCreatePattern] = useState(false);
  const [patternNotes, setPatternNotes] = useState("");
  const [projectSearch, setProjectSearch] = useState("");

  // Reset form when suggestion changes or dialog opens
  useEffect(() => {
    if (open && suggestion) {
      setRejectionReason("wrong_project");
      setCorrectProjectCode("");
      setCreatePattern(false);
      setPatternNotes("");
      setProjectSearch("");
    }
  }, [open, suggestion?.suggestion_id]);

  const handleSubmit = () => {
    onSubmit({
      rejection_reason: rejectionReason,
      correct_project_code: correctProjectCode || undefined,
      create_pattern: createPattern,
      pattern_notes: patternNotes || undefined,
    });
  };

  const handleClose = () => {
    onOpenChange(false);
    // Reset form
    setRejectionReason("wrong_project");
    setCorrectProjectCode("");
    setCreatePattern(false);
    setPatternNotes("");
    setProjectSearch("");
  };

  // Combine projects and proposals, marking the type
  console.log('[CorrectionDialog] projectOptions:', projectOptions.length, 'proposalOptions:', proposalOptions.length);
  const allOptions: ProjectOption[] = [
    ...projectOptions.map(p => ({ ...p, type: 'project' as const })),
    ...proposalOptions.map(p => ({ ...p, type: 'proposal' as const })),
  ];
  console.log('[CorrectionDialog] allOptions:', allOptions.length);

  const filteredOptions = allOptions.filter(
    p => p.code.toLowerCase().includes(projectSearch.toLowerCase()) ||
         p.name.toLowerCase().includes(projectSearch.toLowerCase())
  ).slice(0, 50);

  // Show project correction for any link-type suggestion
  const isLinkSuggestion = suggestion?.suggestion_type === 'email_link' ||
                            suggestion?.suggestion_type === 'contact_link' ||
                            suggestion?.suggestion_type === 'transcript_link';
  const showProjectCorrection = isLinkSuggestion && rejectionReason === 'wrong_project';

  // Look up current project name
  const currentProjectName = suggestion?.project_code
    ? projectOptions.find(p => p.code === suggestion.project_code)?.name
    : null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <X className="h-5 w-5 text-red-500" />
            Correct This Suggestion
          </DialogTitle>
          <DialogDescription>
            Tell us what&apos;s wrong and optionally provide the correct information.
            This helps the system learn!
          </DialogDescription>
        </DialogHeader>

        {suggestion && (
          <div className="space-y-4 py-2">
            {/* Current Suggestion Info */}
            <div className="p-3 bg-slate-50 rounded-lg border">
              <p className="font-medium text-sm text-slate-900">{suggestion.title}</p>
              <p className="text-xs text-slate-500 mt-1">{suggestion.description}</p>
              {suggestion.project_code && (
                <Badge variant="outline" className="mt-2 text-xs">
                  Current: {suggestion.project_code}
                  {currentProjectName && ` - ${currentProjectName}`}
                </Badge>
              )}
            </div>

            {/* Rejection Reason */}
            <div className="space-y-2">
              <Label className="text-sm">Why is this suggestion incorrect?</Label>
              <Select value={rejectionReason} onValueChange={setRejectionReason}>
                <SelectTrigger>
                  <SelectValue placeholder="Select reason" />
                </SelectTrigger>
                <SelectContent>
                  {REJECTION_REASONS.map((reason) => (
                    <SelectItem key={reason.value} value={reason.value}>
                      {reason.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Correct Project Selection */}
            {showProjectCorrection && (
              <div className="space-y-2">
                <Label className="text-sm">
                  Which project/proposal should this be linked to?
                  <span className="ml-2 text-xs text-slate-400">
                    ({projectOptions.length} projects, {proposalOptions.length} proposals)
                  </span>
                </Label>
                <Input
                  placeholder="Search projects..."
                  value={projectSearch}
                  onChange={(e) => setProjectSearch(e.target.value)}
                  className="mb-2"
                />
                <Select value={correctProjectCode || "none"} onValueChange={(v) => setCorrectProjectCode(v === "none" ? "" : v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select correct project or proposal" />
                  </SelectTrigger>
                  <SelectContent className="max-h-[300px]">
                    <SelectItem value="none">-- None / Don&apos;t link --</SelectItem>
                    {filteredOptions.map((p) => (
                      <SelectItem key={p.code} value={p.code}>
                        <span className="flex items-center gap-2">
                          {p.type === 'proposal' && (
                            <span className="text-[10px] bg-amber-100 text-amber-700 px-1 rounded">PROPOSAL</span>
                          )}
                          {p.type === 'project' && (
                            <span className="text-[10px] bg-emerald-100 text-emerald-700 px-1 rounded">PROJECT</span>
                          )}
                          {p.code} - {p.name}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {/* Show correction preview */}
                {correctProjectCode && (
                  <div className="flex items-center gap-2 p-2 bg-emerald-50 rounded text-sm">
                    <div className="flex flex-col">
                      <Badge variant="outline" className="text-red-600 line-through">
                        {suggestion.project_code || 'None'}
                      </Badge>
                      {currentProjectName && (
                        <span className="text-xs text-red-500 line-through mt-0.5">{currentProjectName}</span>
                      )}
                    </div>
                    <ArrowRight className="h-4 w-4 text-slate-400" />
                    <div className="flex flex-col">
                      <Badge variant="outline" className="text-emerald-600 bg-emerald-50">
                        {correctProjectCode}
                      </Badge>
                      {allOptions.find(p => p.code === correctProjectCode)?.name && (
                        <span className="text-xs text-emerald-600 mt-0.5">
                          {allOptions.find(p => p.code === correctProjectCode)?.name}
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Pattern Learning Option */}
            {correctProjectCode && (
              <div className="space-y-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="createPattern"
                    checked={createPattern}
                    onCheckedChange={(checked) => setCreatePattern(checked === true)}
                  />
                  <Label htmlFor="createPattern" className="text-sm text-blue-900 cursor-pointer">
                    <Sparkles className="h-4 w-4 inline mr-1 text-blue-600" />
                    Learn from this correction
                  </Label>
                </div>
                <p className="text-xs text-blue-700">
                  Future emails from this sender will automatically be linked to the correct project.
                </p>

                {createPattern && (
                  <div className="space-y-2 pt-2">
                    <Label className="text-xs text-blue-800">Pattern notes (optional)</Label>
                    <Input
                      value={patternNotes}
                      onChange={(e) => setPatternNotes(e.target.value)}
                      placeholder="e.g., Main client contact for this project"
                      className="bg-white"
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="bg-red-600 hover:bg-red-700"
          >
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <X className="h-4 w-4 mr-2" />
            )}
            {correctProjectCode ? "Reject & Correct" : "Reject"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
