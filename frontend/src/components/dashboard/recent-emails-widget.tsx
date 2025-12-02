"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FeedbackButtons } from "@/components/ui/feedback-buttons";
import { Mail, ExternalLink, User, Calendar } from "lucide-react";
import { EmailSummary } from "@/lib/types";
import Link from "next/link";

interface RecentEmailsWidgetProps {
  limit?: number;
  compact?: boolean;
}

export function RecentEmailsWidget({
  limit = 10,
  compact = false
}: RecentEmailsWidgetProps) {
  // eslint-disable-next-line react-hooks/purity
  const now = useMemo(() => Date.now(), []); // Memoize timestamp for email recency check

  const { data, isLoading, error } = useQuery({
    queryKey: ["recent-emails", limit, 30], // Include days param for proper cache invalidation
    queryFn: () => api.getRecentEmails(limit, 30), // Explicitly pass days=30
    refetchInterval: 1000 * 60 * 2, // Refresh every 2 minutes
    staleTime: 0, // Always fetch fresh data (fixes cache issue with old emails)
  });

  const emails: EmailSummary[] = data?.data || [];
  const totalCount = data?.count || 0;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Emails</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading recent emails...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Emails</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">
            Error loading emails: {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </CardContent>
      </Card>
    );
  }

  if (emails.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Emails</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No recent emails found</p>
        </CardContent>
      </Card>
    );
  }

  // Compact mode shows only summary
  if (compact) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Mail className="h-4 w-4" />
            Recent Emails
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between items-center mb-3">
              <span className="text-2xl font-bold">{totalCount}</span>
              <Link href="/query">
                <Badge variant="secondary" className="cursor-pointer hover:bg-secondary/80">
                  View All
                </Badge>
              </Link>
            </div>
            <div className="space-y-2">
              {emails.slice(0, 3).map((email) => (
                <div
                  key={email.email_id}
                  className="p-2 bg-gray-50 border border-gray-200 rounded-md hover:bg-gray-100 transition-colors cursor-pointer"
                >
                  <p className="text-xs font-medium truncate">{email.subject || "No subject"}</p>
                  <p className="text-[10px] text-muted-foreground truncate mt-0.5">
                    {email.sender_email}
                  </p>
                </div>
              ))}
            </div>

            {/* RLHF Feedback */}
            <div className="pt-3 border-t mt-3">
              <FeedbackButtons
                featureType="widget_recent_emails"
                featureId="dashboard"
                currentValue={`${emails.length} emails`}
                compact
              />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Full mode with all details
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Recent Emails
          </CardTitle>
          <Link href="/query">
            <Badge variant="outline" className="gap-1 cursor-pointer hover:bg-secondary">
              <ExternalLink className="h-3 w-3" />
              View All
            </Badge>
          </Link>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Email List */}
        <div className="space-y-2">
          {emails.map((email) => {
            const hasProject = !!email.project_code;
            const emailDate = email.date ? new Date(email.date) : null;
            const isRecent = emailDate && (now - emailDate.getTime()) < 1000 * 60 * 60 * 24; // Last 24h

            return (
              <Link
                key={email.email_id}
                href={`/query?email_id=${email.email_id}`}
                className="block"
              >
                <div
                  className={`p-3 rounded-md border transition-colors ${
                    isRecent
                      ? "bg-blue-50 border-blue-200 hover:bg-blue-100"
                      : "bg-gray-50 border-gray-200 hover:bg-gray-100"
                  }`}
                >
                  {/* Email Header */}
                  <div className="flex justify-between items-start mb-1.5">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm truncate">
                        {email.subject || "No subject"}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <User className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                        <p className="text-xs text-muted-foreground truncate">
                          {email.sender_email}
                        </p>
                      </div>
                    </div>
                    {isRecent && (
                      <Badge variant="default" className="ml-2 text-[10px] px-1.5 py-0 h-5">
                        New
                      </Badge>
                    )}
                  </div>

                  {/* Email Metadata */}
                  <div className="flex items-center justify-between text-xs mt-2">
                    <div className="flex items-center gap-1.5 text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      <span>
                        {emailDate
                          ? emailDate.toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                              year:
                                emailDate.getFullYear() !== new Date().getFullYear()
                                  ? "numeric"
                                  : undefined,
                            })
                          : "Unknown date"}
                      </span>
                    </div>
                    {hasProject && (
                      <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-5">
                        {email.project_code}
                      </Badge>
                    )}
                  </div>

                  {/* Email Preview */}
                  {email.snippet && (
                    <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                      {email.snippet}
                    </p>
                  )}

                  {/* Category Badge */}
                  {email.category && email.category !== "general" && (
                    <div className="mt-2">
                      <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-5">
                        {email.category.replace("_", " ")}
                      </Badge>
                    </div>
                  )}
                </div>
              </Link>
            );
          })}
        </div>

        {/* Summary Footer */}
        {emails.length > 0 && (
          <div className="pt-3 border-t">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                Showing {emails.length} of {totalCount} recent emails
              </span>
              <Link href="/query">
                <button className="text-primary hover:underline text-sm font-medium">
                  View all emails →
                </button>
              </Link>
            </div>
          </div>
        )}

        {/* RLHF Feedback */}
        <div className="pt-3 border-t">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Was this widget helpful?</span>
            <FeedbackButtons
              featureType="widget_recent_emails"
              featureId="full_view"
              currentValue={`${emails.length} emails`}
              compact
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
