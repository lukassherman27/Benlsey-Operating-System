"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Mail, ChevronRight, Paperclip, Clock } from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

interface ProjectEmailsCardProps {
  projectCode: string;
  limit?: number;
}

interface ProjectEmail {
  email_id: number;
  subject: string;
  sender_email: string;
  date_normalized: string;
  has_attachments: number;
  snippet?: string;
  ai_summary?: string;
}

export function ProjectEmailsCard({ projectCode, limit = 10 }: ProjectEmailsCardProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["project", projectCode, "emails", limit],
    queryFn: () => api.getProjectEmails(projectCode, limit),
    staleTime: 1000 * 60 * 5,
  });

  const emails: ProjectEmail[] = (data?.data ?? []) as ProjectEmail[];
  const totalCount = data?.count ?? 0;

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "";
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

      if (diffDays < 7) {
        return formatDistanceToNow(date, { addSuffix: true });
      }
      return format(date, "MMM d");
    } catch {
      return dateStr;
    }
  };

  const extractSenderName = (senderEmail: string) => {
    // Extract name from "Name <email@domain.com>" format
    const match = senderEmail.match(/^([^<]+)</);
    if (match) return match[1].trim();

    // Just return the email part before @
    const emailMatch = senderEmail.match(/([^@]+)@/);
    if (emailMatch) return emailMatch[1];

    return senderEmail;
  };

  if (isLoading) {
    return (
      <Card className={ds.cards.default}>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Mail className="h-4 w-4 text-green-600" />
            Recent Emails
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-14 bg-slate-100 rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || emails.length === 0) {
    return (
      <Card className={ds.cards.default}>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Mail className="h-4 w-4 text-green-600" />
            Recent Emails
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">No emails found for this project.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={ds.cards.default}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center gap-2">
            <Mail className="h-4 w-4 text-green-600" />
            Recent Emails
            <Badge variant="secondary">{totalCount}</Badge>
          </div>
          <Link href={`/projects/${encodeURIComponent(projectCode)}/emails`}>
            <Button variant="ghost" size="sm" className="text-xs gap-1">
              View All
              <ChevronRight className="h-3 w-3" />
            </Button>
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-1">
          {emails.map((email) => (
            <div
              key={email.email_id}
              className="p-2 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer"
            >
              <div className="flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm text-slate-900 truncate">
                      {extractSenderName(email.sender_email)}
                    </span>
                    <span className="text-xs text-slate-400">
                      {formatDate(email.date_normalized)}
                    </span>
                    {email.has_attachments === 1 && (
                      <Paperclip className="h-3 w-3 text-slate-400" />
                    )}
                  </div>
                  <p className="text-sm text-slate-600 truncate">
                    {email.subject || "(No subject)"}
                  </p>
                  {email.ai_summary && (
                    <p className="text-xs text-slate-400 truncate mt-0.5">
                      {email.ai_summary}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {totalCount > limit && (
          <div className="mt-3 pt-3 border-t">
            <Link href={`/projects/${encodeURIComponent(projectCode)}/emails`}>
              <Button variant="outline" size="sm" className="w-full text-xs">
                View all {totalCount} emails
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
