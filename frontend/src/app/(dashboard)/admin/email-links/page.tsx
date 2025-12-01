"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { EmailLink } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { ds, bensleyVoice, getLoadingMessage } from "@/lib/design-system";
import { Link2, Sparkles, Bot, Unlink, Mail, Search, Trash2, AlertTriangle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { toast } from "sonner";

// Loading skeleton
function EmailLinksSkeleton() {
  return (
    <div className="space-y-4">
      <p className={cn(ds.typography.caption, ds.textColors.tertiary, "text-center mb-4")}>
        {getLoadingMessage()}
      </p>
      {[...Array(3)].map((_, i) => (
        <Card key={i} className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Skeleton className="h-6 w-24" />
                <Skeleton className="h-4 w-4" />
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-5 w-16" />
              </div>
              <Skeleton className="h-24 w-full" />
              <div className="flex items-center gap-4">
                <Skeleton className="h-2 w-24" />
                <Skeleton className="h-4 w-16" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Empty state
function EmptyState({ hasFilter }: { hasFilter: boolean }) {
  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
      <CardContent className="py-16 text-center">
        <Link2 className="mx-auto h-12 w-12 text-slate-300 mb-4" />
        <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
          No email links found
        </p>
        <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
          {hasFilter
            ? "Try a different project code, or the AI has been slacking."
            : bensleyVoice.emptyStates.emails}
        </p>
      </CardContent>
    </Card>
  );
}

// Error state
function ErrorState({ error, onRetry }: { error: Error; onRetry: () => void }) {
  return (
    <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50/30")}>
      <CardContent className="py-16 text-center">
        <AlertTriangle className="mx-auto h-12 w-12 text-red-400 mb-4" />
        <p className={cn(ds.typography.heading3, "text-red-700", "mb-2")}>
          {bensleyVoice.errorMessages.server}
        </p>
        <p className={cn(ds.typography.body, "text-red-600", "mb-4")}>
          {error.message}
        </p>
        <Button onClick={onRetry} className={ds.buttons.secondary}>
          Try again
        </Button>
      </CardContent>
    </Card>
  );
}

export default function EmailLinksPage() {
  const [projectCodeFilter, setProjectCodeFilter] = useState<string>("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["email-links", projectCodeFilter],
    queryFn: () => api.getEmailLinks(projectCodeFilter || undefined),
  });

  const { links = [], total = 0 } = data || {};

  // Selection helpers
  const allSelected = useMemo(() => {
    return links.length > 0 && links.every((l: EmailLink) => selectedIds.has(l.link_id));
  }, [links, selectedIds]);

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(links.map((l: EmailLink) => l.link_id)));
    }
  };

  const toggleSelect = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const unlinkMutation = useMutation({
    mutationFn: (linkId: string) => api.unlinkEmail(linkId),
    onSuccess: () => {
      toast.success("Connection severed. The dots are un-connecting.");
      queryClient.invalidateQueries({ queryKey: ["email-links"] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to unlink: ${error.message}`);
    },
  });

  // Batch unlink mutation
  const batchUnlinkMutation = useMutation({
    mutationFn: async (ids: string[]) => {
      const results = await Promise.allSettled(
        ids.map((id) => api.unlinkEmail(id))
      );
      const succeeded = results.filter((r) => r.status === "fulfilled").length;
      const failed = results.filter((r) => r.status === "rejected").length;
      return { succeeded, failed };
    },
    onSuccess: ({ succeeded, failed }) => {
      if (failed > 0) {
        toast.warning(`Unlinked ${succeeded}, failed ${failed}`);
      } else {
        toast.success(`Unlinked ${succeeded} email connections. The chaos is spreading.`);
      }
      setSelectedIds(new Set());
      queryClient.invalidateQueries({ queryKey: ["email-links"] });
    },
    onError: (error: Error) => {
      toast.error(`Batch unlink failed: ${error.message}`);
    },
  });

  // Get link type badge
  const getLinkTypeBadge = (type: string) => {
    switch (type) {
      case "ai_analysis":
        return (
          <Badge className={ds.badges.success}>
            <Bot className="h-3 w-3 mr-1" />
            AI
          </Badge>
        );
      case "contact_known":
        return (
          <Badge className={ds.badges.info}>
            <Mail className="h-3 w-3 mr-1" />
            CONTACT
          </Badge>
        );
      case "manual":
        return (
          <Badge className={ds.badges.warning}>
            <Sparkles className="h-3 w-3 mr-1" />
            MANUAL
          </Badge>
        );
      case "sender_pattern":
      case "domain_pattern":
        return (
          <Badge className={ds.badges.default}>
            <Mail className="h-3 w-3 mr-1" />
            PATTERN
          </Badge>
        );
      case "id_fix":
        return (
          <Badge className={ds.badges.default}>
            <Link2 className="h-3 w-3 mr-1" />
            ID-FIX
          </Badge>
        );
      default:
        return <Badge className={ds.badges.default}>{(type || "AUTO").toUpperCase()}</Badge>;
    }
  };

  // Get confidence color
  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return "bg-emerald-500";
    if (score >= 0.6) return "bg-amber-500";
    return "bg-red-500";
  };

  return (
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Header */}
      <div>
        <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
          Email-Project Links
        </h1>
        <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
          Review and manage how emails are linked to projects. AI-linked, alias-matched, or manual connections.
        </p>
      </div>

      {/* Data Quality Notice */}
      <Alert variant="info">
        <Link2 className="h-4 w-4" />
        <AlertTitle>Links Rebuilt</AlertTitle>
        <AlertDescription>
          Email links have been rebuilt with verified foreign keys. Quality over quantity -
          every link now connects to a valid email, proposal, or project.
        </AlertDescription>
      </Alert>

      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-4">
        <Card className={cn(ds.borderRadius.card, "border-blue-200 bg-blue-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <Link2 className="h-5 w-5 text-blue-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-blue-700")}>Total Links</p>
                <p className={cn(ds.typography.heading2, "text-blue-800")}>{total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className={cn(ds.borderRadius.card, "border-emerald-200 bg-emerald-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-100">
                <Bot className="h-5 w-5 text-emerald-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-emerald-700")}>AI Analysis</p>
                <p className={cn(ds.typography.heading2, "text-emerald-800")}>
                  {links.filter((l: EmailLink) => l.link_type === "ai_analysis").length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className={cn(ds.borderRadius.card, "border-cyan-200 bg-cyan-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-cyan-100">
                <Mail className="h-5 w-5 text-cyan-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-cyan-700")}>Contact Known</p>
                <p className={cn(ds.typography.heading2, "text-cyan-800")}>
                  {links.filter((l: EmailLink) => l.link_type === "contact_known").length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className={cn(ds.borderRadius.card, "border-violet-200 bg-violet-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-violet-100">
                <Sparkles className="h-5 w-5 text-violet-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-violet-700")}>Other</p>
                <p className={cn(ds.typography.heading2, "text-violet-800")}>
                  {links.filter((l: EmailLink) => !["ai_analysis", "contact_known"].includes(l.link_type || "")).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter and Batch Actions */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Filter by project code (e.g., BK-033)"
            value={projectCodeFilter}
            onChange={(e) => setProjectCodeFilter(e.target.value)}
            className={cn(ds.inputs.default, "pl-10 w-full")}
          />
        </div>
      </div>

      {/* Batch Action Bar */}
      {links.length > 0 && (
        <Card className={cn(ds.borderRadius.card, "border-slate-200 bg-slate-50/50")}>
          <CardContent className="py-3 px-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Checkbox
                  checked={allSelected}
                  onCheckedChange={toggleSelectAll}
                  aria-label="Select all email links"
                />
                <span className={cn(ds.typography.body, ds.textColors.secondary)}>
                  {selectedIds.size > 0
                    ? `${selectedIds.size} selected`
                    : `Select all (${links.length})`}
                </span>
              </div>
              {selectedIds.size > 0 && (
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => {
                      if (confirm(`Are you sure you want to unlink ${selectedIds.size} email(s)?`)) {
                        batchUnlinkMutation.mutate(Array.from(selectedIds));
                      }
                    }}
                    className={ds.buttons.danger}
                    disabled={batchUnlinkMutation.isPending}
                    size="sm"
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    {batchUnlinkMutation.isPending
                      ? "Unlinking..."
                      : `Unlink ${selectedIds.size}`}
                  </Button>
                  <Button
                    onClick={() => setSelectedIds(new Set())}
                    variant="outline"
                    size="sm"
                  >
                    Clear
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Links List */}
      {isLoading ? (
        <EmailLinksSkeleton />
      ) : error ? (
        <ErrorState error={error as Error} onRetry={() => refetch()} />
      ) : links.length === 0 ? (
        <EmptyState hasFilter={!!projectCodeFilter} />
      ) : (
        <div className="space-y-4">
          {links.map((link: EmailLink) => (
            <Card
              key={link.link_id}
              className={cn(
                ds.borderRadius.card,
                "border-slate-200 transition-colors duration-200",
                selectedIds.has(link.link_id) && "border-blue-300 bg-blue-50/30"
              )}
            >
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  {/* Checkbox */}
                  <div className="pt-1">
                    <Checkbox
                      checked={selectedIds.has(link.link_id)}
                      onCheckedChange={() => toggleSelect(link.link_id)}
                      aria-label={`Select email link for ${link.project_code}`}
                    />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        {/* Header */}
                        <div className="flex items-center gap-3 mb-3">
                          <span className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                            {link.project_code}
                          </span>
                          <span className={ds.textColors.tertiary}>•</span>
                          <span className={ds.textColors.secondary}>{link.project_name}</span>
                          {getLinkTypeBadge(link.link_type)}
                        </div>

                        {/* Email Info */}
                        <div className={cn("mb-4 p-4 rounded-lg", ds.status.neutral.bg)}>
                          <div className="flex items-center gap-2 mb-2">
                            <Mail className="h-4 w-4 text-slate-500" />
                            <span className={cn(ds.typography.captionBold, ds.textColors.secondary)}>
                              Email #{link.email_id}
                            </span>
                          </div>
                          <div className={cn(ds.typography.body, ds.textColors.primary, "mb-1")}>
                            <span className={ds.textColors.muted}>Subject: </span>
                            {link.subject}
                          </div>
                          <div className={cn(ds.typography.caption, ds.textColors.secondary, "mb-1")}>
                            <span className={ds.textColors.muted}>From: </span>
                            {link.sender_email}
                          </div>
                          <div className={cn(ds.typography.caption, ds.textColors.secondary, "mb-1")}>
                            <span className={ds.textColors.muted}>Date: </span>
                            {new Date(link.email_date).toLocaleDateString()}
                          </div>
                          {link.category && (
                            <div className={cn(ds.typography.caption, ds.textColors.secondary)}>
                              <span className={ds.textColors.muted}>Category: </span>
                              {link.category}
                            </div>
                          )}
                          {link.snippet && (
                            <p className={cn(ds.typography.body, ds.textColors.secondary, "italic mt-2")}>
                              &quot;{link.snippet.substring(0, 200)}...&quot;
                            </p>
                          )}
                        </div>

                        {/* Confidence */}
                        <div className="flex items-center gap-4 mb-2">
                          <div className="flex items-center gap-2">
                            <span className={cn(ds.typography.caption, ds.textColors.muted)}>
                              Confidence:
                            </span>
                            <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                              <div
                                className={cn("h-full rounded-full", getConfidenceColor(link.confidence_score || 0))}
                                style={{
                                  width: `${(link.confidence_score || 0) * 100}%`,
                                }}
                              />
                            </div>
                            <span className={cn(ds.typography.captionBold, ds.textColors.primary)}>
                              {((link.confidence_score || 0) * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>

                        {link.match_reasons && (
                          <p className={cn(ds.typography.caption, ds.textColors.secondary, "mb-2")}>
                            <span className="font-semibold">Match Reasons:</span> {link.match_reasons}
                          </p>
                        )}

                        <p className={cn(ds.typography.tiny, ds.textColors.muted, "mt-2")}>
                          Linked on {new Date(link.created_at).toLocaleString()}
                        </p>
                      </div>

                      {/* Actions */}
                      <div className="ml-4">
                        <Button
                          onClick={() => {
                            if (
                              confirm(
                                `Are you sure you want to unlink this email from ${link.project_code}?`
                              )
                            ) {
                              unlinkMutation.mutate(link.link_id);
                            }
                          }}
                          className={ds.buttons.danger}
                          disabled={unlinkMutation.isPending}
                        >
                          <Unlink className="h-4 w-4 mr-1" />
                          Unlink
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Summary Footer */}
      {links.length > 0 && (
        <p className={cn(ds.typography.caption, ds.textColors.tertiary, "text-center")}>
          Showing {links.length} of {total} total email links
          {projectCodeFilter && ` for project code "${projectCodeFilter}"`}
        </p>
      )}
    </div>
  );
}
