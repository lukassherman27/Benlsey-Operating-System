"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Mail,
  FileText,
  Check,
  X,
  ChevronRight,
  ChevronLeft,
  Loader2,
  Paperclip,
  Calendar,
  User,
  Building2,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { AIAnalysisPanel } from "./ai-analysis-panel";
import { UserInputPanel } from "./user-input-panel";
import { DatabasePreview } from "./database-preview";
import { CorrectionDialog } from "./correction-dialog";
import {
  SuggestionItem,
  SuggestionPreviewResponse,
  SuggestionSourceResponse,
} from "@/lib/api";
import {
  AIAnalysis,
  UserContext,
  SuggestionTag,
  SuggestedAction,
} from "@/lib/types";

interface ProjectOption {
  code: string;
  name: string;
}

interface EnhancedReviewCardProps {
  suggestion: SuggestionItem;
  sourceData: SuggestionSourceResponse | null;
  previewData: SuggestionPreviewResponse | null;
  aiAnalysis: AIAnalysis | null;
  isLoading: boolean;
  projectOptions: ProjectOption[];
  availableTags: SuggestionTag[];
  onApprove: (data: {
    actions: string[];
    userContext: UserContext;
    createSenderPattern: boolean;
    createDomainPattern: boolean;
  }) => void;
  onReject: (data: {
    rejection_reason: string;
    correct_project_code?: string;
    create_pattern: boolean;
    pattern_notes?: string;
  }) => void;
  onSkip: () => void;
  isApproving: boolean;
  isRejecting: boolean;
  onPrevious?: () => void;
  onNext?: () => void;
  hasPrevious?: boolean;
  hasNext?: boolean;
  currentIndex?: number;
  totalCount?: number;
}

export function EnhancedReviewCard({
  suggestion,
  sourceData,
  previewData,
  aiAnalysis,
  isLoading,
  projectOptions,
  availableTags,
  onApprove,
  onReject,
  onSkip,
  isApproving,
  isRejecting,
  onPrevious,
  onNext,
  hasPrevious = false,
  hasNext = false,
  currentIndex,
  totalCount,
}: EnhancedReviewCardProps) {
  const [selectedActions, setSelectedActions] = useState<Set<string>>(new Set());
  const [userContext, setUserContext] = useState<UserContext>({
    notes: "",
    tags: [],
    contact_role: undefined,
    priority: undefined,
  });
  const [createSenderPattern, setCreateSenderPattern] = useState(false);
  const [createDomainPattern, setCreateDomainPattern] = useState(false);
  const [correctionDialogOpen, setCorrectionDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"source" | "analysis">("source");

  // Initialize selected actions from AI analysis
  useEffect(() => {
    if (aiAnalysis?.suggested_actions) {
      const defaultSelected = new Set(
        aiAnalysis.suggested_actions
          .filter(a => a.enabled_by_default)
          .map(a => a.id)
      );
      setSelectedActions(defaultSelected);
    }
  }, [aiAnalysis]);

  const toggleAction = (actionId: string) => {
    setSelectedActions((prev) => {
      const next = new Set(prev);
      if (next.has(actionId)) {
        next.delete(actionId);
      } else {
        next.add(actionId);
      }
      return next;
    });
  };

  const handleApprove = () => {
    onApprove({
      actions: Array.from(selectedActions),
      userContext,
      createSenderPattern,
      createDomainPattern,
    });
  };

  const handleReject = (data: {
    rejection_reason: string;
    correct_project_code?: string;
    create_pattern: boolean;
    pattern_notes?: string;
  }) => {
    onReject(data);
    setCorrectionDialogOpen(false);
  };

  const confidencePercent = Math.round(suggestion.confidence_score * 100);
  const senderEmail = sourceData?.metadata?.sender;
  const isEmailLink = suggestion.suggestion_type === 'email_link';
  const isNewContact = suggestion.suggestion_type === 'new_contact';

  // Look up project name from options
  const projectName = suggestion.project_code
    ? projectOptions.find(p => p.code === suggestion.project_code)?.name
    : null;

  // Get selected action details for preview
  const selectedActionDetails = aiAnalysis?.suggested_actions?.filter(
    a => selectedActions.has(a.id)
  ) || [];

  return (
    <>
      <Card className="border-2 border-purple-200 shadow-lg">
        <CardContent className="p-0">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b bg-slate-50">
            <div className="flex items-center gap-3">
              {/* Type Badge */}
              {isEmailLink && (
                <Badge variant="outline" className="bg-teal-50 text-teal-700 border-teal-200">
                  <Mail className="h-3 w-3 mr-1" />
                  Email Link
                </Badge>
              )}
              {isNewContact && (
                <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                  <User className="h-3 w-3 mr-1" />
                  New Contact
                </Badge>
              )}
              {!isEmailLink && !isNewContact && (
                <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                  {suggestion.suggestion_type.replace(/_/g, " ")}
                </Badge>
              )}

              {/* Confidence */}
              <Badge
                variant="outline"
                className={cn(
                  "text-xs",
                  confidencePercent >= 80 ? "bg-emerald-100 text-emerald-700 border-emerald-200" :
                  confidencePercent >= 50 ? "bg-amber-100 text-amber-700 border-amber-200" :
                  "bg-red-100 text-red-700 border-red-200"
                )}
              >
                {confidencePercent}% confidence
              </Badge>

              {/* Project Code + Name */}
              {suggestion.project_code && (
                <div className="flex items-center gap-1.5">
                  <code className="bg-purple-100 px-2 py-0.5 rounded text-purple-700 text-xs font-semibold">
                    {suggestion.project_code}
                  </code>
                  {projectName && (
                    <span className="text-xs text-slate-600 truncate max-w-[200px]">
                      {projectName}
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Navigation */}
            <div className="flex items-center gap-2">
              {currentIndex !== undefined && totalCount !== undefined && (
                <span className="text-sm text-slate-500">
                  {currentIndex + 1} of {totalCount}
                </span>
              )}
              <Button
                size="sm"
                variant="ghost"
                onClick={onPrevious}
                disabled={!hasPrevious}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={onNext}
                disabled={!hasNext}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Title */}
          <div className="px-4 py-3 border-b">
            <h3 className="font-semibold text-slate-900">{suggestion.title}</h3>
            <p className="text-sm text-slate-500 mt-1">{suggestion.description}</p>
          </div>

          {/* Main Content - Split Pane */}
          {isLoading ? (
            <div className="p-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-3">
                  <Skeleton className="h-6 w-32" />
                  <Skeleton className="h-40 w-full" />
                </div>
                <div className="space-y-3">
                  <Skeleton className="h-6 w-32" />
                  <Skeleton className="h-40 w-full" />
                </div>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x">
              {/* Left Panel: Source Content */}
              <div className="p-4 max-h-[500px] overflow-y-auto">
                <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "source" | "analysis")}>
                  <TabsList className="mb-3 lg:hidden">
                    <TabsTrigger value="source">Source</TabsTrigger>
                    <TabsTrigger value="analysis">Analysis</TabsTrigger>
                  </TabsList>

                  <TabsContent value="source" className="mt-0">
                    <SourcePanel sourceData={sourceData} />
                  </TabsContent>

                  <TabsContent value="analysis" className="mt-0 lg:hidden">
                    {aiAnalysis && (
                      <AIAnalysisPanel
                        analysis={aiAnalysis}
                        selectedActions={selectedActions}
                        onToggleAction={toggleAction}
                      />
                    )}
                  </TabsContent>
                </Tabs>

                {/* Desktop: Always show source */}
                <div className="hidden lg:block">
                  <SourcePanel sourceData={sourceData} />
                </div>
              </div>

              {/* Right Panel: AI Analysis + User Input */}
              <div className="p-4 max-h-[500px] overflow-y-auto hidden lg:block">
                <div className="space-y-6">
                  {/* AI Analysis */}
                  {aiAnalysis && (
                    <AIAnalysisPanel
                      analysis={aiAnalysis}
                      selectedActions={selectedActions}
                      onToggleAction={toggleAction}
                    />
                  )}

                  {/* Divider */}
                  <div className="border-t" />

                  {/* User Input */}
                  <UserInputPanel
                    userContext={userContext}
                    onChange={setUserContext}
                    availableTags={availableTags}
                    showPatternOptions={isEmailLink}
                    createSenderPattern={createSenderPattern}
                    onSenderPatternChange={setCreateSenderPattern}
                    createDomainPattern={createDomainPattern}
                    onDomainPatternChange={setCreateDomainPattern}
                    senderEmail={senderEmail}
                    suggestionType={suggestion.suggestion_type}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Mobile: User Input Section */}
          <div className="p-4 border-t lg:hidden">
            <UserInputPanel
              userContext={userContext}
              onChange={setUserContext}
              availableTags={availableTags}
              showPatternOptions={isEmailLink}
              createSenderPattern={createSenderPattern}
              onSenderPatternChange={setCreateSenderPattern}
              createDomainPattern={createDomainPattern}
              onDomainPatternChange={setCreateDomainPattern}
              senderEmail={senderEmail}
              suggestionType={suggestion.suggestion_type}
            />
          </div>

          {/* Database Preview */}
          {previewData && (
            <div className="p-4 border-t bg-slate-50">
              <DatabasePreview
                action={previewData.action as 'insert' | 'update' | 'delete' | 'none'}
                table={previewData.table || ''}
                summary={previewData.summary || ''}
                changes={(previewData.changes || []).map(c => ({
                  field: c.field,
                  old_value: c.old_value as string | number | null,
                  new_value: c.new_value as string | number | null,
                }))}
                selectedActions={selectedActionDetails}
              />
            </div>
          )}

          {/* Actions Footer */}
          <div className="flex items-center justify-between p-4 border-t bg-white">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={onSkip}
                disabled={isApproving || isRejecting}
              >
                Skip
              </Button>
              <Button
                variant="outline"
                onClick={() => setCorrectionDialogOpen(true)}
                disabled={isApproving || isRejecting}
                className="text-red-600 border-red-200 hover:bg-red-50"
              >
                <X className="h-4 w-4 mr-1" />
                Wrong / Reject
              </Button>
            </div>

            <div className="flex items-center gap-2">
              {(createSenderPattern || createDomainPattern) && (
                <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                  <Sparkles className="h-3 w-3 mr-1" />
                  Will learn pattern
                </Badge>
              )}
              <Button
                onClick={handleApprove}
                disabled={isApproving || isRejecting}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {isApproving ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Check className="h-4 w-4 mr-2" />
                )}
                Apply {selectedActions.size > 0 ? `(${selectedActions.size})` : ''}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <CorrectionDialog
        open={correctionDialogOpen}
        onOpenChange={setCorrectionDialogOpen}
        suggestion={suggestion}
        projectOptions={projectOptions}
        onSubmit={handleReject}
        isSubmitting={isRejecting}
      />
    </>
  );
}

function SourcePanel({ sourceData }: { sourceData: SuggestionSourceResponse | null }) {
  if (!sourceData) {
    return (
      <div className="text-center py-8 text-slate-400">
        <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No source content available</p>
      </div>
    );
  }

  const isEmail = sourceData.source_type === 'email';
  const isTranscript = sourceData.source_type === 'transcript';

  return (
    <div className="space-y-4">
      {/* Source Type Badge */}
      <div className="flex items-center gap-2">
        {isEmail && (
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            <Mail className="h-3 w-3 mr-1" />
            Email
          </Badge>
        )}
        {isTranscript && (
          <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
            <FileText className="h-3 w-3 mr-1" />
            Transcript
          </Badge>
        )}
      </div>

      {/* Metadata */}
      {isEmail && sourceData.metadata && (
        <div className="space-y-2">
          {sourceData.metadata.subject && (
            <div>
              <Label className="text-xs text-slate-400">Subject</Label>
              <p className="font-medium text-sm text-slate-900">{sourceData.metadata.subject}</p>
            </div>
          )}
          <div className="grid grid-cols-2 gap-2">
            {sourceData.metadata.sender && (
              <div>
                <Label className="text-xs text-slate-400">From</Label>
                <p className="text-sm text-slate-700 truncate">{sourceData.metadata.sender}</p>
              </div>
            )}
            {sourceData.metadata.date && (
              <div>
                <Label className="text-xs text-slate-400">Date</Label>
                <p className="text-sm text-slate-700">{sourceData.metadata.date}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {isTranscript && sourceData.metadata && (
        <div className="space-y-2">
          {sourceData.metadata.title && (
            <div>
              <Label className="text-xs text-slate-400">Meeting Title</Label>
              <p className="font-medium text-sm text-slate-900">{sourceData.metadata.title}</p>
            </div>
          )}
          <div className="grid grid-cols-2 gap-2">
            {sourceData.metadata.date && (
              <div>
                <Label className="text-xs text-slate-400">Date</Label>
                <p className="text-sm text-slate-700">{sourceData.metadata.date}</p>
              </div>
            )}
            {sourceData.metadata.filename && (
              <div>
                <Label className="text-xs text-slate-400">File</Label>
                <p className="text-sm text-slate-700 truncate">{sourceData.metadata.filename}</p>
              </div>
            )}
          </div>
          {sourceData.metadata.summary && (
            <div>
              <Label className="text-xs text-slate-400">Summary</Label>
              <p className="text-sm text-slate-700">{sourceData.metadata.summary}</p>
            </div>
          )}
        </div>
      )}

      {/* Content */}
      {sourceData.content ? (
        <div>
          <Label className="text-xs text-slate-400">Content</Label>
          <div className="mt-1 p-3 bg-slate-50 rounded-lg border text-sm text-slate-700 max-h-[300px] overflow-y-auto whitespace-pre-wrap font-mono leading-relaxed">
            {sourceData.content}
          </div>
        </div>
      ) : (
        <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-sm text-amber-700">
          {sourceData.metadata?.note || "No content available"}
        </div>
      )}
    </div>
  );
}

// Export individual components for flexible use
export { AIAnalysisPanel } from "./ai-analysis-panel";
export { UserInputPanel } from "./user-input-panel";
export { DatabasePreview } from "./database-preview";
export { CorrectionDialog } from "./correction-dialog";
