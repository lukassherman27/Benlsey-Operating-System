"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Brain,
  Sparkles,
  Trash2,
  Pencil,
  Plus,
  RefreshCw,
  Loader2,
  Check,
  TrendingUp,
  Activity,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

interface Pattern {
  pattern_id: number;
  pattern_type: string;
  pattern_key: string;
  target_type: string;
  target_id: number;
  target_code: string;
  target_name: string | null;
  confidence: number;
  times_used: number;
  times_correct: number;
  times_rejected: number;
  is_active: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
  last_used_at: string | null;
}

const PATTERN_TYPE_LABELS: Record<string, string> = {
  sender_to_project: "Sender -> Project",
  sender_to_proposal: "Sender -> Proposal",
  domain_to_project: "Domain -> Project",
  domain_to_proposal: "Domain -> Proposal",
  keyword_to_project: "Keyword -> Project",
  keyword_to_proposal: "Keyword -> Proposal",
  contact_to_project: "Contact -> Project",
  sender_name_to_project: "Sender Name -> Project",
  sender_name_to_proposal: "Sender Name -> Proposal",
};

export default function PatternsPage() {
  const queryClient = useQueryClient();
  const [filterType, setFilterType] = useState<string>("all");
  const [filterActive, setFilterActive] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");

  // Dialog states
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null);

  // Form state
  const [editNotes, setEditNotes] = useState("");
  const [editConfidence, setEditConfidence] = useState(0.8);
  const [newPatternType, setNewPatternType] = useState("sender_to_project");
  const [newPatternKey, setNewPatternKey] = useState("");
  const [newTargetType, setNewTargetType] = useState("project");
  const [newTargetCode, setNewTargetCode] = useState("");
  const [newNotes, setNewNotes] = useState("");

  // Fetch patterns
  const patternsQuery = useQuery({
    queryKey: ["patterns", filterType, filterActive],
    queryFn: () =>
      api.getPatterns({
        pattern_type: filterType === "all" ? undefined : filterType,
        is_active: filterActive === "all" ? undefined : filterActive === "active",
        limit: 500,
      }),
    staleTime: 30 * 1000,
  });

  // Fetch pattern stats
  const statsQuery = useQuery({
    queryKey: ["pattern-stats"],
    queryFn: () => api.getPatternStats(),
    staleTime: 60 * 1000,
  });

  // Fetch projects for dropdown
  const projectsQuery = useQuery({
    queryKey: ["projects-for-linking"],
    queryFn: () => api.getProjectsForLinking(500),
    staleTime: 60 * 1000,
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ patternId, data }: { patternId: number; data: { is_active?: boolean; notes?: string; confidence?: number } }) =>
      api.updatePattern(patternId, data),
    onSuccess: () => {
      toast.success("Pattern updated");
      queryClient.invalidateQueries({ queryKey: ["patterns"] });
      queryClient.invalidateQueries({ queryKey: ["pattern-stats"] });
      setEditDialogOpen(false);
      setSelectedPattern(null);
    },
    onError: (error: Error) => {
      toast.error(`Update failed: ${error.message}`);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (patternId: number) => api.deletePattern(patternId),
    onSuccess: () => {
      toast.success("Pattern deleted");
      queryClient.invalidateQueries({ queryKey: ["patterns"] });
      queryClient.invalidateQueries({ queryKey: ["pattern-stats"] });
      setDeleteConfirmOpen(false);
      setSelectedPattern(null);
    },
    onError: (error: Error) => {
      toast.error(`Delete failed: ${error.message}`);
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: {
      pattern_type: string;
      pattern_key: string;
      target_type: string;
      target_code: string;
      notes?: string;
    }) => api.createPattern(data),
    onSuccess: () => {
      toast.success("Pattern created");
      queryClient.invalidateQueries({ queryKey: ["patterns"] });
      queryClient.invalidateQueries({ queryKey: ["pattern-stats"] });
      setCreateDialogOpen(false);
      setNewPatternType("sender_to_project");
      setNewPatternKey("");
      setNewTargetType("project");
      setNewTargetCode("");
      setNewNotes("");
    },
    onError: (error: Error) => {
      toast.error(`Create failed: ${error.message}`);
    },
  });

  const patterns = patternsQuery.data?.patterns || [];
  const stats = statsQuery.data?.stats;
  const projectOptions = projectsQuery.data?.projects || [];

  // Filter patterns by search term
  const filteredPatterns = patterns.filter((p) => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      p.pattern_key.toLowerCase().includes(search) ||
      p.target_code?.toLowerCase().includes(search) ||
      p.target_name?.toLowerCase().includes(search) ||
      p.notes?.toLowerCase().includes(search)
    );
  });

  const openEditDialog = (pattern: Pattern) => {
    setSelectedPattern(pattern);
    setEditNotes(pattern.notes || "");
    setEditConfidence(pattern.confidence);
    setEditDialogOpen(true);
  };

  const openDeleteConfirm = (pattern: Pattern) => {
    setSelectedPattern(pattern);
    setDeleteConfirmOpen(true);
  };

  const handleToggleActive = (pattern: Pattern) => {
    updateMutation.mutate({
      patternId: pattern.pattern_id,
      data: { is_active: pattern.is_active === 0 },
    });
  };

  const getSuccessRate = (pattern: Pattern): number => {
    if (pattern.times_used === 0) return 0;
    return Math.round((pattern.times_correct / pattern.times_used) * 100);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-slate-100">
            <Brain className="h-6 w-6 text-slate-600" />
          </div>
          <div>
            <h1 className={ds.typography.pageTitle}>Learned Patterns</h1>
            <p className={ds.typography.bodySmall}>
              Patterns the system has learned from your feedback
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: ["patterns"] });
              queryClient.invalidateQueries({ queryKey: ["pattern-stats"] });
            }}
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={() => setCreateDialogOpen(true)}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Pattern
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Patterns</p>
                <p className="text-2xl font-bold text-slate-900">
                  {stats?.total_patterns || 0}
                </p>
              </div>
              <Sparkles className="h-8 w-8 text-blue-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Active</p>
                <p className="text-2xl font-bold text-emerald-600">
                  {stats?.active_patterns || 0}
                </p>
              </div>
              <Check className="h-8 w-8 text-emerald-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Times Used</p>
                <p className="text-2xl font-bold text-slate-900">
                  {stats?.total_uses || 0}
                </p>
              </div>
              <Activity className="h-8 w-8 text-purple-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Avg. Confidence</p>
                <p className="text-2xl font-bold text-slate-900">
                  {stats?.avg_confidence ? `${Math.round(stats.avg_confidence * 100)}%` : "N/A"}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-amber-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search patterns..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-xs"
              />
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Label className="text-sm text-slate-500">Type:</Label>
                <Select value={filterType} onValueChange={setFilterType}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    {Object.entries(PATTERN_TYPE_LABELS).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2">
                <Label className="text-sm text-slate-500">Status:</Label>
                <Select value={filterActive} onValueChange={setFilterActive}>
                  <SelectTrigger className="w-[120px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Patterns Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {filteredPatterns.length} Pattern{filteredPatterns.length !== 1 ? "s" : ""}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {patternsQuery.isLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : filteredPatterns.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No patterns found</p>
              <p className="text-sm mt-1">
                Patterns are created when you approve suggestions with learning enabled
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]">Active</TableHead>
                  <TableHead>Pattern</TableHead>
                  <TableHead>Target</TableHead>
                  <TableHead className="text-center">Used</TableHead>
                  <TableHead className="text-center">Success</TableHead>
                  <TableHead className="text-center">Confidence</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPatterns.map((pattern) => (
                  <TableRow key={pattern.pattern_id}>
                    <TableCell>
                      <Switch
                        checked={pattern.is_active === 1}
                        onCheckedChange={() => handleToggleActive(pattern)}
                        disabled={updateMutation.isPending}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <Badge variant="outline" className="text-xs">
                          {PATTERN_TYPE_LABELS[pattern.pattern_type] || pattern.pattern_type}
                        </Badge>
                        <p className="font-medium text-sm text-slate-900">
                          {pattern.pattern_key}
                        </p>
                        {pattern.notes && (
                          <p className="text-xs text-slate-500 truncate max-w-[200px]">
                            {pattern.notes}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium text-sm text-slate-900">
                          {pattern.target_code}
                        </p>
                        {pattern.target_name && (
                          <p className="text-xs text-slate-500 truncate max-w-[150px]">
                            {pattern.target_name}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-medium">{pattern.times_used}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span
                        className={cn(
                          "font-medium",
                          getSuccessRate(pattern) >= 80
                            ? "text-emerald-600"
                            : getSuccessRate(pattern) >= 50
                            ? "text-amber-600"
                            : "text-red-600"
                        )}
                      >
                        {getSuccessRate(pattern)}%
                      </span>
                      <span className="text-xs text-slate-400 ml-1">
                        ({pattern.times_correct}/{pattern.times_used})
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-medium">
                        {Math.round(pattern.confidence * 100)}%
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => openEditDialog(pattern)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => openDeleteConfirm(pattern)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Pattern</DialogTitle>
            <DialogDescription>
              Update the pattern settings
            </DialogDescription>
          </DialogHeader>
          {selectedPattern && (
            <div className="space-y-4 py-4">
              <div className="p-3 bg-slate-50 rounded-lg border">
                <Badge variant="outline" className="text-xs mb-2">
                  {PATTERN_TYPE_LABELS[selectedPattern.pattern_type] || selectedPattern.pattern_type}
                </Badge>
                <p className="font-medium text-slate-900">{selectedPattern.pattern_key}</p>
                <p className="text-sm text-slate-500">
                  Links to: {selectedPattern.target_code}
                </p>
              </div>

              <div className="space-y-2">
                <Label>Confidence ({Math.round(editConfidence * 100)}%)</Label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={editConfidence}
                  onChange={(e) => setEditConfidence(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Input
                  value={editNotes}
                  onChange={(e) => setEditNotes(e.target.value)}
                  placeholder="Optional notes about this pattern"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (selectedPattern) {
                  updateMutation.mutate({
                    patternId: selectedPattern.pattern_id,
                    data: {
                      notes: editNotes || undefined,
                      confidence: editConfidence,
                    },
                  });
                }
              }}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Check className="h-4 w-4 mr-2" />
              )}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Pattern Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Pattern</DialogTitle>
            <DialogDescription>
              Manually create a new pattern
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Pattern Type</Label>
              <Select value={newPatternType} onValueChange={setNewPatternType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(PATTERN_TYPE_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Pattern Key</Label>
              <Input
                value={newPatternKey}
                onChange={(e) => setNewPatternKey(e.target.value)}
                placeholder={
                  newPatternType.includes("sender")
                    ? "e.g., john@example.com"
                    : newPatternType.includes("domain")
                    ? "e.g., @example.com"
                    : "e.g., keyword"
                }
              />
              <p className="text-xs text-slate-500">
                The value to match against (email, domain, or keyword)
              </p>
            </div>

            <div className="space-y-2">
              <Label>Target Project/Proposal</Label>
              <Select value={newTargetCode} onValueChange={setNewTargetCode}>
                <SelectTrigger>
                  <SelectValue placeholder="Select target" />
                </SelectTrigger>
                <SelectContent className="max-h-[300px]">
                  {projectOptions.map((p) => (
                    <SelectItem key={p.code} value={p.code}>
                      {p.code} - {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Notes (optional)</Label>
              <Input
                value={newNotes}
                onChange={(e) => setNewNotes(e.target.value)}
                placeholder="e.g., Main client contact"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                createMutation.mutate({
                  pattern_type: newPatternType,
                  pattern_key: newPatternKey,
                  target_type: newPatternType.includes("proposal") ? "proposal" : "project",
                  target_code: newTargetCode,
                  notes: newNotes || undefined,
                });
              }}
              disabled={createMutation.isPending || !newPatternKey || !newTargetCode}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {createMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Plus className="h-4 w-4 mr-2" />
              )}
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirm Dialog */}
      <AlertDialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Pattern</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this pattern? This action cannot be undone.
              {selectedPattern && (
                <div className="mt-3 p-3 bg-slate-50 rounded-lg border">
                  <p className="font-medium text-slate-900">{selectedPattern.pattern_key}</p>
                  <p className="text-sm text-slate-500">
                    Links to: {selectedPattern.target_code}
                  </p>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (selectedPattern) {
                  deleteMutation.mutate(selectedPattern.pattern_id);
                }
              }}
              disabled={deleteMutation.isPending}
              className="bg-red-600 hover:bg-red-700"
            >
              {deleteMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Trash2 className="h-4 w-4 mr-2" />
              )}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
