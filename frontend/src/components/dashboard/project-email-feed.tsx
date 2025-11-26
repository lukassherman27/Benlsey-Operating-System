"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ProjectEmail } from "@/lib/types";
import { useState } from "react";

interface ProjectEmailFeedProps {
  projectCode: string;
  limit?: number;
  compact?: boolean;
}

export function ProjectEmailFeed({
  projectCode,
  limit = 20,
  compact = false
}: ProjectEmailFeedProps) {
  const [expandedEmailId, setExpandedEmailId] = useState<number | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["project-emails", projectCode, limit],
    queryFn: () => api.getProjectEmails(projectCode, limit),
    refetchInterval: 1000 * 60 * 5, // Refresh every 5 minutes
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Email Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-slate-100 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg text-red-600">Email Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-500">
            Failed to load emails: {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </CardContent>
      </Card>
    );
  }

  const emails = data?.data || [];

  if (emails.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Email Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">No emails found for this project.</p>
        </CardContent>
      </Card>
    );
  }

  const getCategoryColor = (category: string | null | undefined) => {
    if (!category) return "bg-slate-100 text-slate-600";

    const cat = category.toLowerCase();
    if (cat.includes("invoice") || cat.includes("billing")) return "bg-green-100 text-green-700";
    if (cat.includes("urgent") || cat.includes("priority")) return "bg-red-100 text-red-700";
    if (cat.includes("meeting") || cat.includes("schedule")) return "bg-blue-100 text-blue-700";
    if (cat.includes("contract") || cat.includes("legal")) return "bg-purple-100 text-purple-700";
    if (cat.includes("rfi") || cat.includes("inquiry")) return "bg-orange-100 text-orange-700";
    return "bg-slate-100 text-slate-600";
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diff = now.getTime() - date.getTime();
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));

      if (days === 0) return "Today";
      if (days === 1) return "Yesterday";
      if (days < 7) return `${days} days ago`;
      if (days < 30) return `${Math.floor(days / 7)} weeks ago`;

      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined
      });
    } catch {
      return dateStr;
    }
  };

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">
            Email Activity
            <span className="ml-2 text-sm font-normal text-slate-500">
              ({emails.length} {emails.length === 1 ? "email" : "emails"})
            </span>
          </CardTitle>
          {data?.count && data.count > limit && (
            <Badge variant="outline" className="text-xs">
              Showing {limit} of {data.count}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {emails.map((email: ProjectEmail, idx: number) => {
            const isExpanded = expandedEmailId === email.email_id;

            return (
              <div
                key={email.email_id}
                className={`
                  border border-slate-200 rounded-lg p-4 transition-all
                  hover:border-slate-300 hover:shadow-sm cursor-pointer
                  ${idx > 0 ? "opacity-90" : ""}
                `}
                onClick={() => setExpandedEmailId(isExpanded ? null : email.email_id)}
              >
                {/* Email Header */}
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-sm text-slate-900 truncate">
                      {email.subject || "(No subject)"}
                    </h4>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-slate-600">
                        {email.sender_email}
                      </span>
                      {email.has_attachments === 1 && (
                        <Badge variant="outline" className="text-xs px-1.5 py-0">
                          📎
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                    <span className="text-xs text-slate-500 whitespace-nowrap">
                      {formatDate(email.date)}
                    </span>
                    {email.category && (
                      <Badge className={`text-xs px-2 py-0 ${getCategoryColor(email.category)}`}>
                        {email.category}
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Email Preview */}
                {!isExpanded && (email.snippet || email.body_preview) && (
                  <p className="text-xs text-slate-600 line-clamp-2">
                    {truncateText(email.snippet || email.body_preview || "", 150)}
                  </p>
                )}

                {/* Expanded View */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-200 space-y-2">
                    {email.body_preview && (
                      <div className="text-sm text-slate-700 whitespace-pre-wrap max-h-64 overflow-y-auto">
                        {email.body_preview}
                      </div>
                    )}

                    {email.ai_summary && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-2">
                        <h5 className="text-xs font-semibold text-blue-900 mb-1">
                          AI Summary
                        </h5>
                        <p className="text-xs text-blue-800">{email.ai_summary}</p>
                      </div>
                    )}

                    <div className="flex items-center gap-4 text-xs text-slate-500 pt-2">
                      {email.confidence_score && (
                        <span>
                          Confidence: {(email.confidence_score * 100).toFixed(0)}%
                        </span>
                      )}
                      {email.importance_score !== null && email.importance_score !== undefined && (
                        <span>
                          Importance: {email.importance_score}/10
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* View All Button */}
        {data?.count && data.count > limit && (
          <div className="mt-4 text-center">
            <Button variant="outline" size="sm">
              View All {data.count} Emails
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
