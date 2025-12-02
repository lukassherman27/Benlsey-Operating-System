"use client";

import { useState, useEffect, useMemo } from "react";
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
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ArrowRight,
  Loader2,
  X,
  Sparkles,
  Building2,
  Mail,
  FileText,
  User,
  Briefcase,
  Globe,
  Ban,
  Megaphone,
  ChevronRight,
  Plus,
  Zap,
  Link2,
  FolderOpen,
  Layers,
  Check,
} from "lucide-react";
import { SuggestionItem } from "@/lib/api";
import { cn } from "@/lib/utils";

// ========================================
// Types
// ========================================

interface ProjectOption {
  code: string;
  name: string;
  type?: 'project' | 'proposal';
}

interface CategoryOption {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: string;
  subcategories?: { id: string; label: string }[];
}

interface LinkedItem {
  type: 'project' | 'proposal' | 'category';
  code: string;
  name: string;
  subcategory?: string;
}

export interface CorrectionSubmitData {
  rejection_reason: string;
  correct_project_code?: string;
  linked_items?: LinkedItem[];
  category?: string;
  subcategory?: string;
  create_pattern: boolean;
  pattern_notes?: string;
}

interface CorrectionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  suggestion: SuggestionItem | null;
  projectOptions: ProjectOption[];
  proposalOptions?: ProjectOption[];
  onSubmit: (data: CorrectionSubmitData) => void;
  isSubmitting: boolean;
}

// ========================================
// Constants
// ========================================

const REJECTION_REASONS = [
  { value: 'wrong_project', label: 'Wrong project/proposal' },
  { value: 'internal_email', label: 'Internal email (not project-related)' },
  { value: 'external_non_project', label: 'External (not project-related)' },
  { value: 'wrong_contact', label: 'Wrong contact' },
  { value: 'spam_irrelevant', label: 'Spam / Irrelevant' },
  { value: 'duplicate', label: 'Duplicate' },
  { value: 'data_incorrect', label: 'Data is incorrect' },
  { value: 'other', label: 'Other' },
];

const CATEGORIES: CategoryOption[] = [
  {
    id: 'project',
    label: 'Project',
    icon: <Building2 className="h-4 w-4" />,
    color: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  },
  {
    id: 'proposal',
    label: 'Proposal',
    icon: <FileText className="h-4 w-4" />,
    color: 'bg-amber-100 text-amber-700 border-amber-200',
  },
  {
    id: 'internal',
    label: 'Internal Email',
    icon: <Mail className="h-4 w-4" />,
    color: 'bg-blue-100 text-blue-700 border-blue-200',
    subcategories: [
      { id: 'hr', label: 'HR' },
      { id: 'it', label: 'IT' },
      { id: 'admin', label: 'Admin' },
      { id: 'finance', label: 'Finance' },
      { id: 'general', label: 'General Internal' },
    ],
  },
  {
    id: 'external',
    label: 'External',
    icon: <Globe className="h-4 w-4" />,
    color: 'bg-purple-100 text-purple-700 border-purple-200',
    subcategories: [
      { id: 'client', label: 'Client Communication' },
      { id: 'vendor', label: 'Vendor' },
      { id: 'contractor', label: 'Contractor' },
      { id: 'partner', label: 'Partner' },
    ],
  },
  {
    id: 'personal',
    label: 'Personal',
    icon: <User className="h-4 w-4" />,
    color: 'bg-slate-100 text-slate-700 border-slate-200',
  },
  {
    id: 'newsletter',
    label: 'Newsletter / Marketing',
    icon: <Megaphone className="h-4 w-4" />,
    color: 'bg-pink-100 text-pink-700 border-pink-200',
  },
  {
    id: 'spam',
    label: 'Spam',
    icon: <Ban className="h-4 w-4" />,
    color: 'bg-red-100 text-red-700 border-red-200',
  },
];

// Quick actions for common patterns
const QUICK_ACTIONS = [
  {
    id: 'link_different',
    label: 'Link to different project',
    icon: <Link2 className="h-4 w-4" />,
    reason: 'wrong_project',
    goToTab: 'project' as const,
  },
  {
    id: 'internal_not_project',
    label: 'Internal email, not project related',
    icon: <Mail className="h-4 w-4" />,
    reason: 'internal_email',
    category: 'internal',
    subcategory: 'general',
  },
  {
    id: 'spam',
    label: 'Spam / Marketing',
    icon: <Ban className="h-4 w-4" />,
    reason: 'spam_irrelevant',
    category: 'spam',
  },
  {
    id: 'personal',
    label: 'Personal email',
    icon: <User className="h-4 w-4" />,
    reason: 'spam_irrelevant',
    category: 'personal',
  },
  {
    id: 'newsletter',
    label: 'Newsletter / Marketing',
    icon: <Megaphone className="h-4 w-4" />,
    reason: 'spam_irrelevant',
    category: 'newsletter',
  },
  {
    id: 'link_multiple',
    label: 'Link to multiple projects',
    icon: <Layers className="h-4 w-4" />,
    reason: 'wrong_project',
    goToTab: 'project' as const,
  },
];

// ========================================
// Component
// ========================================

export function CorrectionDialog({
  open,
  onOpenChange,
  suggestion,
  projectOptions,
  proposalOptions = [],
  onSubmit,
  isSubmitting,
}: CorrectionDialogProps) {
  // Form state
  const [rejectionReason, setRejectionReason] = useState("wrong_project");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedSubcategory, setSelectedSubcategory] = useState<string | null>(null);
  const [linkedItems, setLinkedItems] = useState<LinkedItem[]>([]);
  const [createPattern, setCreatePattern] = useState(false);
  const [patternNotes, setPatternNotes] = useState("");
  const [projectSearch, setProjectSearch] = useState("");
  const [activeTab, setActiveTab] = useState<"quick" | "category" | "project">("quick");
  const [selectedQuickAction, setSelectedQuickAction] = useState<string | null>(null);

  // Reset form when suggestion changes or dialog opens
  useEffect(() => {
    if (open && suggestion) {
      setRejectionReason("wrong_project");
      setSelectedCategory(null);
      setSelectedSubcategory(null);
      setLinkedItems([]);
      setCreatePattern(false);
      setPatternNotes("");
      setProjectSearch("");
      setActiveTab("quick");
      setSelectedQuickAction(null);
    }
  }, [open, suggestion?.suggestion_id]);

  // Combine projects and proposals with type markers
  const allOptions = useMemo(() => [
    ...projectOptions.map(p => ({ ...p, type: 'project' as const })),
    ...proposalOptions.map(p => ({ ...p, type: 'proposal' as const })),
  ], [projectOptions, proposalOptions]);

  // Filter options based on search
  const filteredOptions = useMemo(() =>
    allOptions.filter(
      p => p.code.toLowerCase().includes(projectSearch.toLowerCase()) ||
           p.name.toLowerCase().includes(projectSearch.toLowerCase())
    ).slice(0, 50),
    [allOptions, projectSearch]
  );

  // Check if this is a link-type suggestion
  const isLinkSuggestion = suggestion?.suggestion_type === 'email_link' ||
                            suggestion?.suggestion_type === 'contact_link' ||
                            suggestion?.suggestion_type === 'transcript_link';

  // Get current category details
  const currentCategoryDetails = selectedCategory
    ? CATEGORIES.find(c => c.id === selectedCategory)
    : null;

  // Look up current project name
  const currentProjectName = suggestion?.project_code
    ? projectOptions.find(p => p.code === suggestion.project_code)?.name
    : null;

  // Handle quick action selection
  const handleQuickAction = (action: typeof QUICK_ACTIONS[0]) => {
    setSelectedQuickAction(action.id);
    setRejectionReason(action.reason);
    if (action.category) {
      setSelectedCategory(action.category);
      if (action.subcategory) {
        setSelectedSubcategory(action.subcategory);
      }
    } else {
      // Clear category if this action doesn't have one
      setSelectedCategory(null);
      setSelectedSubcategory(null);
    }
    if (action.goToTab) {
      setActiveTab(action.goToTab);
    }
  };

  // Handle category selection
  const handleCategorySelect = (categoryId: string) => {
    setSelectedCategory(categoryId);
    setSelectedSubcategory(null);

    // Auto-set rejection reason based on category
    if (categoryId === 'internal') {
      setRejectionReason('internal_email');
    } else if (categoryId === 'external') {
      setRejectionReason('external_non_project');
    } else if (['spam', 'newsletter', 'personal'].includes(categoryId)) {
      setRejectionReason('spam_irrelevant');
    } else if (categoryId === 'project' || categoryId === 'proposal') {
      setRejectionReason('wrong_project');
      setActiveTab('project');
    }
  };

  // Add project/proposal to linked items
  const addLinkedItem = (option: ProjectOption) => {
    const exists = linkedItems.some(
      item => item.code === option.code && item.type === option.type
    );
    if (!exists) {
      setLinkedItems([...linkedItems, {
        type: option.type || 'project',
        code: option.code,
        name: option.name,
      }]);
    }
  };

  // Remove from linked items
  const removeLinkedItem = (code: string) => {
    setLinkedItems(linkedItems.filter(item => item.code !== code));
  };

  // Handle form submission
  const handleSubmit = () => {
    const data: CorrectionSubmitData = {
      rejection_reason: rejectionReason,
      create_pattern: createPattern,
      pattern_notes: patternNotes || undefined,
    };

    // If we have linked items, use those
    if (linkedItems.length > 0) {
      data.linked_items = linkedItems;
      // For backward compatibility, also set correct_project_code to first item
      data.correct_project_code = linkedItems[0].code;
    }

    // If we have a category selection
    if (selectedCategory && !['project', 'proposal'].includes(selectedCategory)) {
      data.category = selectedCategory;
      if (selectedSubcategory) {
        data.subcategory = selectedSubcategory;
      }
    }

    onSubmit(data);
  };

  const handleClose = () => {
    onOpenChange(false);
  };

  // Determine button text
  const getButtonText = () => {
    if (linkedItems.length > 0) {
      return `Reject & Link to ${linkedItems.length} item${linkedItems.length > 1 ? 's' : ''}`;
    }
    if (selectedCategory) {
      return `Categorize as ${CATEGORIES.find(c => c.id === selectedCategory)?.label}`;
    }
    return "Reject";
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <X className="h-5 w-5 text-red-500" />
            Correct This Suggestion
          </DialogTitle>
          <DialogDescription>
            Categorize this item or link it to the correct project(s).
          </DialogDescription>
        </DialogHeader>

        {suggestion && (
          <div className="flex-1 overflow-hidden flex flex-col space-y-4">
            {/* Current Suggestion Info */}
            <div className="p-3 bg-slate-50 rounded-lg border shrink-0">
              <p className="font-medium text-sm text-slate-900">{suggestion.title}</p>
              <p className="text-xs text-slate-500 mt-1 line-clamp-2">{suggestion.description}</p>
              <div className="flex items-center gap-2 mt-2">
                <Badge variant="outline" className="text-xs">
                  {suggestion.suggestion_type.replace(/_/g, ' ')}
                </Badge>
                {suggestion.project_code && (
                  <Badge variant="outline" className="text-xs bg-purple-50">
                    Current: {suggestion.project_code}
                    {currentProjectName && ` - ${currentProjectName}`}
                  </Badge>
                )}
              </div>
            </div>

            {/* Main Content - Tabs */}
            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)} className="flex-1 overflow-hidden flex flex-col">
              <TabsList className="grid grid-cols-3 shrink-0">
                <TabsTrigger value="quick" className="flex items-center gap-1">
                  <Zap className="h-3 w-3" />
                  Quick Actions
                </TabsTrigger>
                <TabsTrigger value="category" className="flex items-center gap-1">
                  <FolderOpen className="h-3 w-3" />
                  Category
                </TabsTrigger>
                <TabsTrigger value="project" className="flex items-center gap-1">
                  <Link2 className="h-3 w-3" />
                  Link to Project
                </TabsTrigger>
              </TabsList>

              {/* Quick Actions Tab */}
              <TabsContent value="quick" className="flex-1 overflow-auto mt-4">
                <div className="grid grid-cols-2 gap-2">
                  {QUICK_ACTIONS.map((action) => (
                    <Button
                      key={action.id}
                      variant="outline"
                      className={cn(
                        "h-auto py-3 px-4 justify-start transition-all",
                        selectedQuickAction === action.id
                          ? "border-blue-500 bg-blue-50 ring-2 ring-blue-200"
                          : "hover:border-slate-300"
                      )}
                      onClick={() => handleQuickAction(action)}
                      aria-pressed={selectedQuickAction === action.id}
                    >
                      <span className="flex items-center gap-2">
                        {action.icon}
                        <span className="text-sm">{action.label}</span>
                        {selectedQuickAction === action.id && (
                          <Check className="h-3 w-3 ml-auto text-blue-600" />
                        )}
                      </span>
                    </Button>
                  ))}
                </div>

                {/* Rejection Reason (shown in quick tab too) */}
                <div className="mt-4 space-y-2">
                  <Label className="text-sm text-slate-500">Rejection Reason</Label>
                  <Select value={rejectionReason} onValueChange={setRejectionReason}>
                    <SelectTrigger className="h-9">
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
              </TabsContent>

              {/* Category Tab */}
              <TabsContent value="category" className="flex-1 overflow-auto mt-4">
                <div className="space-y-4">
                  {/* Category Grid */}
                  <div className="grid grid-cols-2 gap-2">
                    {CATEGORIES.filter(c => !['project', 'proposal'].includes(c.id)).map((category) => (
                      <Button
                        key={category.id}
                        variant="outline"
                        className={cn(
                          "h-auto py-3 px-4 justify-start",
                          selectedCategory === category.id && "border-blue-500 bg-blue-50"
                        )}
                        onClick={() => handleCategorySelect(category.id)}
                      >
                        <span className="flex items-center gap-2">
                          {category.icon}
                          <span className="text-sm">{category.label}</span>
                          {category.subcategories && (
                            <ChevronRight className="h-3 w-3 ml-auto text-slate-400" />
                          )}
                        </span>
                      </Button>
                    ))}
                  </div>

                  {/* Subcategory Selection */}
                  {currentCategoryDetails?.subcategories && (
                    <div className="p-3 bg-slate-50 rounded-lg border space-y-2">
                      <Label className="text-sm" id="subcategory-label">Select Subcategory</Label>
                      <div
                        className="flex flex-wrap gap-2"
                        role="group"
                        aria-labelledby="subcategory-label"
                      >
                        {currentCategoryDetails.subcategories.map((sub) => (
                          <Badge
                            key={sub.id}
                            variant={selectedSubcategory === sub.id ? "default" : "outline"}
                            className={cn(
                              "cursor-pointer transition-colors",
                              selectedSubcategory === sub.id
                                ? "bg-blue-600"
                                : "hover:bg-slate-100"
                            )}
                            onClick={() => setSelectedSubcategory(sub.id)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                setSelectedSubcategory(sub.id);
                              }
                            }}
                            role="button"
                            tabIndex={0}
                            aria-pressed={selectedSubcategory === sub.id}
                            aria-label={`Select ${sub.label} subcategory`}
                          >
                            {sub.label}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Selected Category Preview */}
                  {selectedCategory && (
                    <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                      <p className="text-sm text-emerald-700 flex items-center gap-2">
                        <span>Will categorize as:</span>
                        <Badge className={currentCategoryDetails?.color}>
                          {currentCategoryDetails?.label}
                          {selectedSubcategory && ` > ${currentCategoryDetails?.subcategories?.find(s => s.id === selectedSubcategory)?.label}`}
                        </Badge>
                      </p>
                    </div>
                  )}
                </div>
              </TabsContent>

              {/* Project Linking Tab */}
              <TabsContent value="project" className="flex-1 overflow-hidden mt-4 flex flex-col">
                <div className="space-y-4 flex-1 overflow-hidden flex flex-col">
                  {/* Search */}
                  <div className="space-y-2 shrink-0">
                    <Label className="text-sm">
                      Search & Select Projects/Proposals
                      <span className="ml-2 text-xs text-slate-400">
                        (Multi-select enabled)
                      </span>
                    </Label>
                    <Input
                      placeholder="Search by code or name..."
                      value={projectSearch}
                      onChange={(e) => setProjectSearch(e.target.value)}
                    />
                  </div>

                  {/* Selected Items */}
                  {linkedItems.length > 0 && (
                    <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200 shrink-0">
                      <Label className="text-xs text-emerald-700 mb-2 block">
                        Linked to ({linkedItems.length}):
                      </Label>
                      <div className="flex flex-wrap gap-2">
                        {linkedItems.map((item) => (
                          <Badge
                            key={item.code}
                            variant="outline"
                            className={cn(
                              "pl-2 pr-1 py-1",
                              item.type === 'proposal'
                                ? "bg-amber-50 border-amber-200"
                                : "bg-emerald-50 border-emerald-200"
                            )}
                          >
                            <span className="text-xs font-medium mr-1">
                              {item.type === 'proposal' ? 'P' : 'J'}
                            </span>
                            {item.code}
                            <button
                              onClick={() => removeLinkedItem(item.code)}
                              className="ml-1 p-0.5 hover:bg-slate-200 rounded"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Project List */}
                  <ScrollArea className="flex-1 border rounded-lg">
                    <div className="p-2 space-y-1">
                      {filteredOptions.length === 0 ? (
                        <p className="text-sm text-slate-500 text-center py-4">
                          No projects found
                        </p>
                      ) : (
                        filteredOptions.map((option) => {
                          const isSelected = linkedItems.some(item => item.code === option.code);
                          return (
                            <button
                              key={option.code}
                              className={cn(
                                "w-full flex items-center justify-between p-2 rounded-md text-left transition-colors",
                                isSelected
                                  ? "bg-blue-50 border border-blue-200"
                                  : "hover:bg-slate-50 border border-transparent"
                              )}
                              onClick={() => isSelected ? removeLinkedItem(option.code) : addLinkedItem(option)}
                            >
                              <div className="flex items-center gap-2 min-w-0">
                                <Badge
                                  variant="outline"
                                  className={cn(
                                    "text-[10px] shrink-0",
                                    option.type === 'proposal'
                                      ? "bg-amber-100 text-amber-700 border-amber-200"
                                      : "bg-emerald-100 text-emerald-700 border-emerald-200"
                                  )}
                                >
                                  {option.type === 'proposal' ? 'PROPOSAL' : 'PROJECT'}
                                </Badge>
                                <span className="font-mono text-sm text-slate-700 shrink-0">
                                  {option.code}
                                </span>
                                <span className="text-sm text-slate-500 truncate">
                                  {option.name}
                                </span>
                              </div>
                              {isSelected ? (
                                <Badge className="shrink-0 bg-blue-600">
                                  Selected
                                </Badge>
                              ) : (
                                <Plus className="h-4 w-4 text-slate-400 shrink-0" />
                              )}
                            </button>
                          );
                        })
                      )}
                    </div>
                  </ScrollArea>

                  {/* Correction Preview */}
                  {linkedItems.length > 0 && (
                    <div className="flex items-center gap-2 p-2 bg-slate-50 rounded text-sm shrink-0">
                      {suggestion?.project_code ? (
                        <>
                          <Badge variant="outline" className="text-red-600 line-through">
                            {suggestion.project_code}
                          </Badge>
                          <ArrowRight className="h-4 w-4 text-slate-400" />
                        </>
                      ) : (
                        <span className="text-slate-500 text-xs">Will link to:</span>
                      )}
                      <div className="flex gap-1 flex-wrap">
                        {linkedItems.map((item) => (
                          <Badge
                            key={item.code}
                            variant="outline"
                            className={cn(
                              item.type === 'proposal'
                                ? "text-amber-600 bg-amber-50 border-amber-200"
                                : "text-emerald-600 bg-emerald-50 border-emerald-200"
                            )}
                          >
                            {item.type === 'proposal' ? 'P: ' : ''}{item.code}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </TabsContent>
            </Tabs>

            {/* Pattern Learning Option */}
            {(linkedItems.length > 0 || selectedCategory) && (
              <div className="space-y-3 p-3 bg-blue-50 rounded-lg border border-blue-200 shrink-0">
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
                  Future emails from this sender will be automatically categorized/linked the same way.
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

        <DialogFooter className="shrink-0 pt-4">
          <Button variant="outline" onClick={handleClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className={cn(
              linkedItems.length > 0 || selectedCategory
                ? "bg-emerald-600 hover:bg-emerald-700"
                : "bg-red-600 hover:bg-red-700"
            )}
          >
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : linkedItems.length > 0 || selectedCategory ? (
              <Sparkles className="h-4 w-4 mr-2" />
            ) : (
              <X className="h-4 w-4 mr-2" />
            )}
            {getButtonText()}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
