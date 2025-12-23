"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Mail, Paperclip, Send, Inbox } from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";

interface ProposalEmailsCardProps {
  projectCode: string;
  limit?: number;
}

interface ProposalEmail {
  email_id?: number;
  id?: number;
  subject?: string;
  title?: string;
  sender_email?: string;
  from?: string;
  date_normalized?: string;
  date?: string;
  has_attachments?: number;
  snippet?: string;
  ai_summary?: string;
  direction?: "inbound" | "outbound" | "internal";
}

export function ProposalEmailsCard({ projectCode, limit = 8 }: ProposalEmailsCardProps) {
  // Use the timeline API which joins via email_proposal_links
  const { data, isLoading, error } = useQuery({
    queryKey: ["proposal-timeline", projectCode],
    queryFn: () => api.getProposalTimeline(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  // Extract emails from timeline - filter to only email entries
  const timelineEmails = (data?.timeline ?? []).filter(
    (item: { type?: string }) => item.type === "email"
  );
  const directEmails = data?.emails ?? [];

  // Combine and dedupe
  const allEmails = [...directEmails, ...timelineEmails];
  const seenIds = new Set<number>();
  const emails: ProposalEmail[] = allEmails
    .filter((e: ProposalEmail) => {
      const id = e.email_id || e.id;
      if (!id || seenIds.has(id)) return false;
      seenIds.add(id);
      return true;
    })
    .slice(0, limit);
  const totalCount = data?.stats?.total_emails ?? emails.length;

  const formatDate = (dateStr: string | null | undefined) => {
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
      return String(dateStr);
    }
  };

  const extractSenderName = (email: ProposalEmail) => {
    const senderEmail = email.sender_email || email.from || "";
    // Extract name from "Name <email@domain.com>" format
    const match = senderEmail.match(/^([^<]+)</);
    if (match) return match[1].trim();

    // Just return the email part before @
    const emailMatch = senderEmail.match(/([^@]+)@/);
    if (emailMatch) return emailMatch[1];

    return senderEmail || "Unknown";
  };

  const getDirectionIcon = (email: ProposalEmail) => {
    const sender = (email.sender_email || email.from || "").toLowerCase();
    if (sender.includes("@bensley.com")) {
      return <Send className="h-3 w-3 text-blue-500" />;
    }
    return <Inbox className="h-3 w-3 text-green-500" />;
  };

  const getEmailDate = (email: ProposalEmail) => {
    return email.date_normalized || email.date || "";
  };

  const getEmailSubject = (email: ProposalEmail) => {
    return email.subject || email.title || "(No subject)";
  };

  if (isLoading) {
    return (
      <Card className="border rounded-xl shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Mail className="h-4 w-4 text-green-600" />
            Recent Emails
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-12 bg-slate-100 rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || emails.length === 0) {
    return (
      <Card className="border rounded-xl shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Mail className="h-4 w-4 text-green-600" />
            Recent Emails
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">No emails linked to this proposal yet.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border rounded-xl shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center gap-2">
            <Mail className="h-4 w-4 text-green-600" />
            Recent Emails
            <Badge variant="secondary" className="text-xs">{totalCount}</Badge>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-1 max-h-[320px] overflow-y-auto">
          {emails.map((email) => (
            <div
              key={email.email_id || email.id}
              className="p-2 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer border border-transparent hover:border-slate-200"
            >
              <div className="flex items-start gap-2">
                <div className="mt-1">
                  {getDirectionIcon(email)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm text-slate-900 truncate">
                      {extractSenderName(email)}
                    </span>
                    <span className="text-xs text-slate-400">
                      {formatDate(getEmailDate(email))}
                    </span>
                    {email.has_attachments === 1 && (
                      <Paperclip className="h-3 w-3 text-slate-400" />
                    )}
                  </div>
                  <p className="text-sm text-slate-600 truncate">
                    {getEmailSubject(email)}
                  </p>
                  {(email.ai_summary || email.snippet) && (
                    <p className="text-xs text-slate-400 truncate mt-0.5">
                      {email.ai_summary || email.snippet}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {totalCount > limit && (
          <div className="mt-3 pt-3 border-t">
            <Button variant="outline" size="sm" className="w-full text-xs">
              View all {totalCount} emails
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
