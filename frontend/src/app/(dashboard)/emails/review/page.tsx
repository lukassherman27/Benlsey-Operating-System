"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import {
  RefreshCw,
  Check,
  X,
  Mail,
  Building2,
  User,
  Clock,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Inbox,
} from "lucide-react";

// Type for review queue email
interface ReviewQueueEmail {
  email_id: number;
  subject: string;
  sender_email: string;
  sender_name: string;
  date: string;
  snippet: string;
  has_attachments: boolean;
  category: string;
  ai_summary: string;
  suggestion: {
    suggestion_id: number;
    type: string;
    target_type: string;
    target_id: number;
    target_code: string;
    target_name: string;
    confidence: number;
    match_method: string;
    reason: string;
    suggested_value: string;
    context: string;
    created_at: string;
  };
  sender_context: {
    total_emails: number;
    linked_projects: string[];
    is_known_contact: boolean;
  };
}

export default function EmailReviewQueuePage() {
  const [emails, setEmails] = useState<ReviewQueueEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [processingIds, setProcessingIds] = useState<Set<number>>(new Set());
  const [totalPending, setTotalPending] = useState(0);
  const [byType, setByType] = useState<Record<string, number>>({});

  // Fetch review queue
  const fetchQueue = useCallback(async () => {
    try {
      const result = await api.getEmailReviewQueue(50);
      if (result.success) {
        setEmails(result.emails);
        setTotalPending(result.total_pending);
        setByType(result.by_type);
      }
    } catch (error) {
      console.error("Failed to fetch review queue:", error);
      toast.error("Failed to load review queue");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  // Handle refresh
  const handleRefresh = () => {
    setRefreshing(true);
    fetchQueue();
  };

  // Toggle selection
  const toggleSelection = (emailId: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(emailId)) {
        next.delete(emailId);
      } else {
        next.add(emailId);
      }
      return next;
    });
  };

  // Select all
  const selectAll = () => {
    if (selectedIds.size === emails.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(emails.map((e) => e.email_id)));
    }
  };

  // Quick approve single email
  const handleQuickApprove = async (email: ReviewQueueEmail) => {
    if (!email.suggestion?.target_code) {
      toast.error("No project code to link to");
      return;
    }

    setProcessingIds((prev) => new Set(prev).add(email.email_id));
    try {
      const result = await api.quickApproveEmail(
        email.email_id,
        email.suggestion.target_code,
        true
      );
      if (result.success) {
        toast.success(
          <div>
            <p>Linked to {result.project_code}</p>
            {result.pattern_learned && (
              <p className="text-xs text-muted-foreground mt-1">
                Pattern learned: {result.pattern_learned}
              </p>
            )}
          </div>
        );
        // Remove from list
        setEmails((prev) => prev.filter((e) => e.email_id !== email.email_id));
        setSelectedIds((prev) => {
          const next = new Set(prev);
          next.delete(email.email_id);
          return next;
        });
      } else {
        toast.error("Failed to approve");
      }
    } catch (error) {
      console.error("Failed to approve:", error);
      toast.error("Failed to approve email");
    } finally {
      setProcessingIds((prev) => {
        const next = new Set(prev);
        next.delete(email.email_id);
        return next;
      });
    }
  };

  // Bulk approve selected
  const handleBulkApprove = async () => {
    if (selectedIds.size === 0) {
      toast.error("No emails selected");
      return;
    }

    const ids = Array.from(selectedIds);
    ids.forEach((id) =>
      setProcessingIds((prev) => new Set(prev).add(id))
    );

    try {
      const result = await api.bulkApproveEmails(ids, true);
      if (result.success) {
        toast.success(
          <div>
            <p>
              {result.data.approved} approved, {result.data.failed} failed
            </p>
            {result.data.patterns_learned.length > 0 && (
              <p className="text-xs text-muted-foreground mt-1">
                Patterns learned: {result.data.patterns_learned.join(", ")}
              </p>
            )}
          </div>
        );
        // Refresh the list
        fetchQueue();
        setSelectedIds(new Set());
      }
    } catch (error) {
      console.error("Failed to bulk approve:", error);
      toast.error("Failed to bulk approve");
    } finally {
      setProcessingIds(new Set());
    }
  };

  // Format date
  const formatDate = (dateStr: string) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  // Confidence color
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return "text-green-600 bg-green-100";
    if (confidence >= 0.7) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Email Review Queue</h1>
          <p className="text-muted-foreground">
            Review and approve AI suggestions to teach the system
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw
              className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Badge variant="secondary">{totalPending} pending</Badge>
        </div>
      </div>

      {/* Stats by type */}
      {Object.keys(byType).length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {Object.entries(byType).map(([type, count]) => (
            <Badge key={type} variant="outline">
              {type}: {count}
            </Badge>
          ))}
        </div>
      )}

      {/* Bulk Actions Bar */}
      {emails.length > 0 && (
        <Card>
          <CardContent className="py-3 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Checkbox
                checked={
                  selectedIds.size > 0 && selectedIds.size === emails.length
                }
                onCheckedChange={selectAll}
              />
              <span className="text-sm text-muted-foreground">
                {selectedIds.size > 0
                  ? `${selectedIds.size} selected`
                  : "Select all"}
              </span>
            </div>
            {selectedIds.size > 0 && (
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  onClick={handleBulkApprove}
                  disabled={processingIds.size > 0}
                >
                  <Check className="h-4 w-4 mr-2" />
                  Approve Selected ({selectedIds.size})
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Email List */}
      {emails.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <Inbox className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">Queue is empty</h3>
            <p className="text-muted-foreground">
              No emails with pending suggestions. Run email sync to import new
              emails.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {emails.map((email) => (
            <Card
              key={email.email_id}
              className={`transition-all ${
                selectedIds.has(email.email_id)
                  ? "ring-2 ring-primary"
                  : "hover:shadow-md"
              }`}
            >
              <CardContent className="py-4">
                <div className="flex items-start gap-4">
                  {/* Checkbox */}
                  <Checkbox
                    checked={selectedIds.has(email.email_id)}
                    onCheckedChange={() => toggleSelection(email.email_id)}
                    disabled={processingIds.has(email.email_id)}
                  />

                  {/* Email Content */}
                  <div className="flex-1 min-w-0">
                    {/* Header Row */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium truncate">
                          {email.sender_name || email.sender_email}
                        </span>
                        {email.sender_context?.is_known_contact && (
                          <Badge
                            variant="secondary"
                            className="text-xs"
                          >
                            <User className="h-3 w-3 mr-1" />
                            Contact
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {formatDate(email.date)}
                      </div>
                    </div>

                    {/* Subject */}
                    <h3 className="font-medium mb-1 truncate">
                      {email.subject}
                    </h3>

                    {/* Snippet */}
                    {email.snippet && (
                      <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                        {email.snippet}
                      </p>
                    )}

                    {/* AI Suggestion */}
                    {email.suggestion && (
                      <div className="bg-muted/50 rounded-lg p-3 mt-2">
                        <div className="flex items-center gap-2 mb-2">
                          <Building2 className="h-4 w-4 text-primary" />
                          <span className="font-medium">
                            Suggested:{" "}
                            {email.suggestion.target_code}
                          </span>
                          {email.suggestion.target_name && (
                            <span className="text-muted-foreground">
                              ({email.suggestion.target_name})
                            </span>
                          )}
                          <Badge
                            className={getConfidenceColor(
                              email.suggestion.confidence
                            )}
                          >
                            {Math.round(email.suggestion.confidence * 100)}%
                          </Badge>
                        </div>
                        {email.suggestion.reason && (
                          <p className="text-sm text-muted-foreground">
                            {email.suggestion.reason}
                          </p>
                        )}

                        {/* Sender Context */}
                        {email.sender_context &&
                          email.sender_context.total_emails > 1 && (
                            <p className="text-xs text-muted-foreground mt-2">
                              {email.sender_context.total_emails} emails from
                              this sender
                              {email.sender_context.linked_projects.length >
                                0 && (
                                <>
                                  {" "}
                                  • Linked to:{" "}
                                  {email.sender_context.linked_projects.join(
                                    ", "
                                  )}
                                </>
                              )}
                            </p>
                          )}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col gap-2">
                    <Button
                      size="sm"
                      onClick={() => handleQuickApprove(email)}
                      disabled={processingIds.has(email.email_id)}
                    >
                      {processingIds.has(email.email_id) ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          <CheckCircle2 className="h-4 w-4 mr-1" />
                          Approve
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
