"use client";

import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
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
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle2, AlertCircle, Trash2 } from "lucide-react";

interface ActionItem {
  task: string;
  assignee?: string;
  due_date?: string;
  priority?: string;
}

interface ParsedSummary {
  summary: string;
  keyPoints: string[];
  actionItems: ActionItem[];
  nextMeetingDate?: string;
}

interface PasteSummaryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  transcriptId: number;
  transcriptTitle?: string;
  detectedProjectCode?: string;
}

function parseClaudeSummary(text: string): ParsedSummary {
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);

  const keyPoints: string[] = [];
  const actionItems: ActionItem[] = [];
  let summary = "";
  let nextMeetingDate: string | undefined;

  let currentSection: "summary" | "keypoints" | "actions" | "meeting" | null = null;

  for (const line of lines) {
    const lowerLine = line.toLowerCase();

    // Detect section headers
    if (lowerLine.includes("summary") && (lowerLine.startsWith("#") || lowerLine.startsWith("**"))) {
      currentSection = "summary";
      continue;
    }
    if (lowerLine.includes("key point") || lowerLine.includes("keypoint") || lowerLine.includes("highlights")) {
      currentSection = "keypoints";
      continue;
    }
    if (lowerLine.includes("action item") || lowerLine.includes("action:") || lowerLine.includes("todo") || lowerLine.includes("next step")) {
      currentSection = "actions";
      continue;
    }
    if (lowerLine.includes("next meeting") || lowerLine.includes("follow-up date") || lowerLine.includes("scheduled")) {
      currentSection = "meeting";
      continue;
    }

    // Parse content based on section
    if (currentSection === "summary" || currentSection === null) {
      // First non-header text is likely summary
      if (!summary && !line.startsWith("-") && !line.startsWith("*") && !line.match(/^\d+\./)) {
        summary = line.replace(/^\*\*|\*\*$/g, "").replace(/^#+\s*/, "");
      } else if (currentSection === "summary") {
        summary += " " + line;
      }
    }

    if (currentSection === "keypoints") {
      const cleanLine = line.replace(/^[-*•]\s*/, "").replace(/^\d+\.\s*/, "");
      if (cleanLine && cleanLine.length > 3) {
        keyPoints.push(cleanLine);
      }
    }

    if (currentSection === "actions") {
      const cleanLine = line.replace(/^[-*•]\s*/, "").replace(/^\d+\.\s*/, "");
      if (cleanLine && cleanLine.length > 3) {
        // Try to extract priority
        let priority = "normal";
        if (lowerLine.includes("urgent") || lowerLine.includes("asap") || lowerLine.includes("critical")) {
          priority = "critical";
        } else if (lowerLine.includes("high priority") || lowerLine.includes("important")) {
          priority = "high";
        } else if (lowerLine.includes("low priority") || lowerLine.includes("when possible")) {
          priority = "low";
        }

        // Try to extract assignee
        let assignee: string | undefined;
        const assigneeMatch = cleanLine.match(/\(([^)]+)\)|\[@?([^\]]+)\]|assigned to:?\s*(\w+)/i);
        if (assigneeMatch) {
          assignee = assigneeMatch[1] || assigneeMatch[2] || assigneeMatch[3];
        }

        actionItems.push({
          task: cleanLine.replace(/\([^)]*\)|\[[^\]]*\]/g, "").trim(),
          priority,
          assignee,
        });
      }
    }

    if (currentSection === "meeting") {
      // Try to extract date
      const dateMatch = line.match(/(\d{4}-\d{2}-\d{2})|(\d{1,2}\/\d{1,2}\/\d{2,4})/);
      if (dateMatch) {
        nextMeetingDate = dateMatch[0];
      }
    }
  }

  // If no structured summary found, use first paragraph
  if (!summary && lines.length > 0) {
    summary = lines.slice(0, 3).join(" ");
  }

  return {
    summary: summary.trim(),
    keyPoints,
    actionItems,
    nextMeetingDate,
  };
}

export function PasteSummaryModal({
  open,
  onOpenChange,
  transcriptId,
  transcriptTitle,
  detectedProjectCode,
}: PasteSummaryModalProps) {
  const queryClient = useQueryClient();
  const [rawText, setRawText] = useState("");
  const [parsed, setParsed] = useState<ParsedSummary | null>(null);
  const [selectedProposalCode, setSelectedProposalCode] = useState<string>(
    detectedProjectCode || ""
  );
  const [editedActionItems, setEditedActionItems] = useState<ActionItem[]>([]);

  // Fetch active proposals for dropdown
  const { data: proposalsData } = useQuery({
    queryKey: ["proposals", "active"],
    queryFn: () => api.getProposals({ per_page: 100 }),
  });

  const saveMutation = useMutation({
    mutationFn: (data: {
      summary: string;
      key_points?: string[];
      action_items?: ActionItem[];
      next_meeting_date?: string;
      proposal_code?: string;
    }) => api.saveClaudeSummary(transcriptId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["transcripts"] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      onOpenChange(false);
      // Reset state
      setRawText("");
      setParsed(null);
      setEditedActionItems([]);
    },
  });

  // Parse when raw text changes
  useEffect(() => {
    if (rawText.trim()) {
      const result = parseClaudeSummary(rawText);
      setParsed(result);
      setEditedActionItems(result.actionItems);
    } else {
      setParsed(null);
      setEditedActionItems([]);
    }
  }, [rawText]);

  // Update selected proposal when detected code changes
  useEffect(() => {
    if (detectedProjectCode) {
      setSelectedProposalCode(detectedProjectCode);
    }
  }, [detectedProjectCode]);

  const handleSave = () => {
    if (!parsed) return;

    saveMutation.mutate({
      summary: parsed.summary,
      key_points: parsed.keyPoints.length > 0 ? parsed.keyPoints : undefined,
      action_items: editedActionItems.length > 0 ? editedActionItems : undefined,
      next_meeting_date: parsed.nextMeetingDate,
      proposal_code: selectedProposalCode || undefined,
    });
  };

  const removeActionItem = (index: number) => {
    setEditedActionItems((items) => items.filter((_, i) => i !== index));
  };

  const updateActionItemPriority = (index: number, priority: string) => {
    setEditedActionItems((items) =>
      items.map((item, i) => (i === index ? { ...item, priority } : item))
    );
  };

  const proposals = proposalsData?.data || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Save Claude Summary</DialogTitle>
          <DialogDescription>
            Paste the summary Claude generated for{" "}
            {transcriptTitle ? `"${transcriptTitle}"` : "this transcript"}.
            Action items will be extracted and created as tasks.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Raw text input */}
          <div className="space-y-2">
            <Label htmlFor="summary-text">Paste Claude&apos;s Summary</Label>
            <Textarea
              id="summary-text"
              placeholder="Paste the summary here. Include sections like:
## Summary
The meeting covered...

## Key Points
- Point 1
- Point 2

## Action Items
- Send proposal update (high priority)
- Schedule follow-up call"
              className="min-h-[200px] font-mono text-sm"
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
            />
          </div>

          {/* Proposal selector */}
          <div className="space-y-2">
            <Label>Link to Proposal</Label>
            <Select
              value={selectedProposalCode}
              onValueChange={setSelectedProposalCode}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a proposal (optional)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">No proposal</SelectItem>
                {proposals.map((p) => (
                  <SelectItem key={p.project_code} value={p.project_code}>
                    {p.project_code} - {p.project_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Preview parsed content */}
          {parsed && (
            <div className="space-y-4 border rounded-lg p-4 bg-muted/50">
              <h4 className="font-medium flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Parsed Preview
              </h4>

              {/* Summary preview */}
              {parsed.summary && (
                <div>
                  <Label className="text-xs text-muted-foreground">Summary</Label>
                  <p className="text-sm mt-1">{parsed.summary.slice(0, 200)}...</p>
                </div>
              )}

              {/* Key points preview */}
              {parsed.keyPoints.length > 0 && (
                <div>
                  <Label className="text-xs text-muted-foreground">
                    Key Points ({parsed.keyPoints.length})
                  </Label>
                  <ul className="text-sm mt-1 space-y-1">
                    {parsed.keyPoints.slice(0, 3).map((point, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-muted-foreground">•</span>
                        {point}
                      </li>
                    ))}
                    {parsed.keyPoints.length > 3 && (
                      <li className="text-muted-foreground">
                        +{parsed.keyPoints.length - 3} more...
                      </li>
                    )}
                  </ul>
                </div>
              )}

              {/* Action items preview */}
              {editedActionItems.length > 0 && (
                <div>
                  <Label className="text-xs text-muted-foreground">
                    Action Items ({editedActionItems.length} tasks will be created)
                  </Label>
                  <div className="mt-2 space-y-2">
                    {editedActionItems.map((item, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-2 text-sm bg-background rounded p-2"
                      >
                        <Select
                          value={item.priority || "normal"}
                          onValueChange={(v) => updateActionItemPriority(i, v)}
                        >
                          <SelectTrigger className="w-24 h-7 text-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="low">Low</SelectItem>
                            <SelectItem value="normal">Normal</SelectItem>
                            <SelectItem value="high">High</SelectItem>
                            <SelectItem value="critical">Critical</SelectItem>
                          </SelectContent>
                        </Select>
                        <span className="flex-1 truncate">{item.task}</span>
                        {item.assignee && (
                          <Badge variant="outline" className="text-xs">
                            {item.assignee}
                          </Badge>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => removeActionItem(i)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Next meeting date */}
              {parsed.nextMeetingDate && (
                <div>
                  <Label className="text-xs text-muted-foreground">
                    Next Meeting Date
                  </Label>
                  <p className="text-sm mt-1">{parsed.nextMeetingDate}</p>
                </div>
              )}
            </div>
          )}

          {/* Error state */}
          {saveMutation.isError && (
            <div className="flex items-center gap-2 text-destructive text-sm">
              <AlertCircle className="h-4 w-4" />
              Failed to save summary. Please try again.
            </div>
          )}

          {/* Success state */}
          {saveMutation.isSuccess && (
            <div className="flex items-center gap-2 text-green-600 text-sm">
              <CheckCircle2 className="h-4 w-4" />
              Summary saved! {saveMutation.data?.tasks_created || 0} tasks created.
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!parsed?.summary || saveMutation.isPending}
          >
            {saveMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Save Summary
            {editedActionItems.length > 0 && ` & ${editedActionItems.length} Tasks`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
