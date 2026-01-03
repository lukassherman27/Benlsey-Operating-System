"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { format, isToday, isYesterday, parseISO, differenceInDays, subDays, isAfter } from "date-fns";
import { useState, useMemo } from "react";
import {
  MessageCircle,
  Paperclip,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  Clock,
  User,
  Search,
  X,
} from "lucide-react";

interface ConversationEmail {
  email_id: number;
  date: string;
  subject: string;
  sender_email: string;
  sender_category: "bill" | "brian" | "lukas" | "mink" | "bensley_other" | "client";
  body_preview?: string;
  has_attachments?: boolean;
  email_direction?: string;
}

interface ConversationViewProps {
  projectCode: string;
}

const EMAILS_PER_PAGE = 20;

// Group emails by date
function groupEmailsByDate(emails: ConversationEmail[]) {
  const groups: { date: string; label: string; emails: ConversationEmail[] }[] = [];
  let currentGroup: { date: string; label: string; emails: ConversationEmail[] } | null = null;

  emails.forEach((email) => {
    const emailDate = email.date ? email.date.substring(0, 10) : "";

    if (!currentGroup || currentGroup.date !== emailDate) {
      // Create date label
      let label = emailDate;
      try {
        const dateObj = parseISO(emailDate);
        if (isToday(dateObj)) {
          label = "Today";
        } else if (isYesterday(dateObj)) {
          label = "Yesterday";
        } else {
          label = format(dateObj, "MMMM d, yyyy");
        }
      } catch {
        label = emailDate;
      }

      currentGroup = { date: emailDate, label, emails: [] };
      groups.push(currentGroup);
    }

    currentGroup.emails.push(email);
  });

  return groups;
}

// Get sender display name
function getSenderName(email: ConversationEmail): string {
  const category = email.sender_category;

  switch (category) {
    case "bill":
      return "Bill Bensley";
    case "brian":
      return "Brian Sherman";
    case "lukas":
      return "Lukas Sherman";
    case "mink":
      return "Mink";
    case "bensley_other":
      // Extract name from email
      const bensleyMatch = email.sender_email?.match(/([^@<]+)@/);
      return bensleyMatch ? bensleyMatch[1].replace(/\./g, " ").split(" ").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ") : "Bensley Team";
    case "client":
    default:
      // Extract name from email address
      const clientMatch = email.sender_email?.match(/^([^<]+)</);
      if (clientMatch) {
        return clientMatch[1].trim().replace(/"/g, "");
      }
      const emailMatch = email.sender_email?.match(/([^@<]+)@/);
      if (emailMatch) {
        return emailMatch[1].replace(/[._]/g, " ").split(" ").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
      }
      return email.sender_email || "Unknown";
  }
}

// Is this a Bensley person (shown on right side)?
function isBensleyPerson(category: string): boolean {
  return ["bill", "brian", "lukas", "mink", "bensley_other"].includes(category);
}

// Get avatar initials
function getInitials(name: string): string {
  const words = name.trim().split(/\s+/);
  if (words.length >= 2) {
    return (words[0][0] + words[words.length - 1][0]).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
}

// Get avatar color based on sender category
function getAvatarColor(category: string): string {
  switch (category) {
    case "bill":
      return "bg-blue-600 text-white";
    case "brian":
      return "bg-emerald-600 text-white";
    case "lukas":
      return "bg-purple-600 text-white";
    case "mink":
      return "bg-amber-600 text-white";
    case "bensley_other":
      return "bg-slate-600 text-white";
    case "client":
    default:
      return "bg-gray-400 text-white";
  }
}

// Highlight search matches in text
function highlightText(text: string, searchTerm: string): React.ReactNode {
  if (!searchTerm.trim()) return text;

  const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
  const parts = text.split(regex);

  return parts.map((part, i) =>
    regex.test(part) ? (
      <mark key={i} className="bg-yellow-200 text-yellow-900 rounded px-0.5">{part}</mark>
    ) : part
  );
}

// Message bubble component
function MessageBubble({
  email,
  isExpanded,
  onToggle,
  searchTerm,
}: {
  email: ConversationEmail;
  isExpanded: boolean;
  onToggle: () => void;
  searchTerm: string;
}) {
  const isBensley = isBensleyPerson(email.sender_category);
  const senderName = getSenderName(email);
  const initials = getInitials(senderName);
  const avatarColor = getAvatarColor(email.sender_category);

  // Format time
  let timeDisplay = "";
  try {
    const emailDate = parseISO(email.date);
    timeDisplay = format(emailDate, "h:mm a");
  } catch {
    timeDisplay = email.date?.substring(11, 16) || "";
  }

  // Clean body text - use body_preview only (security: never expose body_full)
  const bodyText = email.body_preview || "";
  // Use a safer approach: strip tags iteratively to handle nested/malformed HTML,
  // then decode common HTML entities and normalize whitespace
  const stripHtmlTags = (html: string): string => {
    let text = html;
    // Keep stripping until no more tags found (handles nested tags)
    let prev = "";
    while (prev !== text) {
      prev = text;
      text = text.replace(/<[^>]*>/g, " ");
    }
    // Decode common HTML entities (except < and > to avoid double-escaping)
    return text
      .replace(/&nbsp;/g, " ")
      .replace(/&amp;/g, "&")
      .replace(/&lt;/g, "")  // Remove rather than decode to avoid XSS
      .replace(/&gt;/g, "")  // Remove rather than decode to avoid XSS
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/\s+/g, " ")
      .trim();
  };
  const cleanedBody = stripHtmlTags(bodyText);

  return (
    <div className={cn(
      "flex gap-2 max-w-[85%]",
      isBensley ? "ml-auto flex-row-reverse" : "mr-auto"
    )}>
      {/* Avatar */}
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium",
        avatarColor
      )}>
        {initials}
      </div>

      {/* Message bubble */}
      <div className="flex flex-col">
        {/* Sender name and time */}
        <div className={cn(
          "flex items-center gap-2 mb-1 text-xs text-slate-500",
          isBensley ? "flex-row-reverse" : ""
        )}>
          <span className="font-medium">{senderName}</span>
          <span>{timeDisplay}</span>
          {email.has_attachments && (
            <Paperclip className="h-3 w-3" />
          )}
        </div>

        {/* Bubble */}
        <div
          className={cn(
            "rounded-2xl px-4 py-2 cursor-pointer transition-all",
            isBensley
              ? "bg-blue-500 text-white rounded-tr-sm"
              : "bg-slate-100 text-slate-900 rounded-tl-sm"
          )}
          onClick={onToggle}
        >
          {/* Subject line */}
          <p className={cn(
            "font-medium text-sm mb-1",
            isBensley ? "text-blue-100" : "text-slate-600"
          )}>
            {searchTerm ? highlightText(email.subject || "(No subject)", searchTerm) : (email.subject || "(No subject)")}
          </p>

          {/* Body preview */}
          <p className={cn(
            "text-sm",
            isExpanded ? "" : "line-clamp-3"
          )}>
            {searchTerm ? highlightText(cleanedBody || "(No content)", searchTerm) : (cleanedBody || "(No content)")}
          </p>

          {/* Expand/collapse indicator */}
          {cleanedBody.length > 200 && (
            <div className={cn(
              "flex items-center justify-center mt-2 text-xs",
              isBensley ? "text-blue-200" : "text-slate-400"
            )}>
              {isExpanded ? (
                <>
                  <ChevronUp className="h-3 w-3 mr-1" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3 mr-1" />
                  Show more
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Waiting indicator component
function WaitingIndicator({
  lastEmail,
  emails
}: {
  lastEmail: ConversationEmail | undefined;
  emails: ConversationEmail[];
}) {
  if (!lastEmail || emails.length === 0) return null;

  const isBensleyLast = isBensleyPerson(lastEmail.sender_category);

  // Calculate days waiting using date-fns (pure function)
  let daysWaiting = 0;
  try {
    const lastDate = parseISO(lastEmail.date);
    daysWaiting = differenceInDays(new Date(), lastDate);
  } catch {
    return null;
  }

  if (daysWaiting < 1) return null;

  return (
    <div className={cn(
      "flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm",
      isBensleyLast
        ? "bg-amber-50 text-amber-700 border border-amber-200"
        : "bg-blue-50 text-blue-700 border border-blue-200"
    )}>
      <Clock className="h-4 w-4" />
      {isBensleyLast ? (
        <span>
          Waiting <strong>{daysWaiting} day{daysWaiting !== 1 ? "s" : ""}</strong> for client response
        </span>
      ) : (
        <span>
          Client waiting <strong>{daysWaiting} day{daysWaiting !== 1 ? "s" : ""}</strong> for your response
        </span>
      )}
    </div>
  );
}

// Pagination component
function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-2 pt-3 border-t">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>
      <span className="text-sm text-slate-600">
        Page {currentPage} of {totalPages}
      </span>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  );
}

export function ConversationView({ projectCode }: ConversationViewProps) {
  const [expandedEmails, setExpandedEmails] = useState<Set<number>>(new Set());
  const [searchTerm, setSearchTerm] = useState("");
  const [senderFilter, setSenderFilter] = useState<"all" | "bensley" | "client">("all");
  const [dateFilter, setDateFilter] = useState<"all" | "7days" | "30days" | "90days">("all");
  const [currentPage, setCurrentPage] = useState(1);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["proposal-conversation", projectCode],
    queryFn: () => api.getProposalConversation(projectCode),
    enabled: !!projectCode,
  });

  const toggleEmail = (emailId: number) => {
    setExpandedEmails(prev => {
      const next = new Set(prev);
      if (next.has(emailId)) {
        next.delete(emailId);
      } else {
        next.add(emailId);
      }
      return next;
    });
  };

  // Filter and search emails
  const filteredEmails = useMemo(() => {
    let emails = data?.emails || [];

    // Apply sender filter
    if (senderFilter === "bensley") {
      emails = emails.filter(e => isBensleyPerson(e.sender_category));
    } else if (senderFilter === "client") {
      emails = emails.filter(e => !isBensleyPerson(e.sender_category));
    }

    // Apply date filter
    if (dateFilter !== "all") {
      const daysMap = { "7days": 7, "30days": 30, "90days": 90 };
      const cutoffDate = subDays(new Date(), daysMap[dateFilter]);
      emails = emails.filter(e => {
        try {
          return isAfter(parseISO(e.date), cutoffDate);
        } catch {
          return false;
        }
      });
    }

    // Apply search filter
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      emails = emails.filter(e =>
        e.subject?.toLowerCase().includes(term) ||
        e.body_preview?.toLowerCase().includes(term) ||
        e.sender_email?.toLowerCase().includes(term)
      );
    }

    return emails;
  }, [data?.emails, senderFilter, dateFilter, searchTerm]);

  // Paginate emails
  const totalPages = Math.ceil(filteredEmails.length / EMAILS_PER_PAGE);
  const paginatedEmails = useMemo(() => {
    const start = (currentPage - 1) * EMAILS_PER_PAGE;
    return filteredEmails.slice(start, start + EMAILS_PER_PAGE);
  }, [filteredEmails, currentPage]);

  // Reset to page 1 when filters change
  const handleFilterChange = (setter: (value: string) => void, value: string) => {
    setter(value);
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setSearchTerm("");
    setSenderFilter("all");
    setDateFilter("all");
    setCurrentPage(1);
  };

  const hasActiveFilters = searchTerm || senderFilter !== "all" || dateFilter !== "all";

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5" />
            Conversation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex gap-3">
                <Skeleton className="h-8 w-8 rounded-full" />
                <Skeleton className="h-20 flex-1 rounded-2xl" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Error Loading Conversation</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : "Failed to load conversation"}
          </p>
        </CardContent>
      </Card>
    );
  }

  const allEmails = data?.emails || [];
  const emailGroups = groupEmailsByDate(paginatedEmails);
  const lastEmail = allEmails[allEmails.length - 1];

  // Count by sender type
  const bensleyCount = allEmails.filter(e => isBensleyPerson(e.sender_category)).length;
  const clientCount = allEmails.filter(e => !isBensleyPerson(e.sender_category)).length;

  if (allEmails.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5" />
            Conversation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <User className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No external correspondence yet</p>
            <p className="text-sm">Emails with clients will appear here</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5" />
            Conversation
          </CardTitle>
          <div className="flex gap-2">
            <Badge variant="outline" className="text-xs">
              <span className="inline-block w-2 h-2 rounded-full bg-blue-500 mr-1.5" />
              {bensleyCount} from us
            </Badge>
            <Badge variant="outline" className="text-xs">
              <span className="inline-block w-2 h-2 rounded-full bg-gray-400 mr-1.5" />
              {clientCount} from client
            </Badge>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-2 mt-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search emails..."
              value={searchTerm}
              onChange={(e) => handleFilterChange(setSearchTerm, e.target.value)}
              className="pl-9"
            />
          </div>
          <Select
            value={senderFilter}
            onValueChange={(v) => handleFilterChange(setSenderFilter, v)}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Sender" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All senders</SelectItem>
              <SelectItem value="bensley">From us</SelectItem>
              <SelectItem value="client">From client</SelectItem>
            </SelectContent>
          </Select>
          <Select
            value={dateFilter}
            onValueChange={(v) => handleFilterChange(setDateFilter, v)}
          >
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="Date" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All time</SelectItem>
              <SelectItem value="7days">Last 7 days</SelectItem>
              <SelectItem value="30days">Last 30 days</SelectItem>
              <SelectItem value="90days">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
          {hasActiveFilters && (
            <Button variant="ghost" size="icon" onClick={clearFilters} title="Clear filters">
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Filter summary */}
        {hasActiveFilters && (
          <p className="text-xs text-slate-500 mt-2">
            Showing {filteredEmails.length} of {allEmails.length} emails
          </p>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Waiting indicator at top */}
        <WaitingIndicator lastEmail={lastEmail} emails={allEmails} />

        {/* Conversation timeline */}
        {paginatedEmails.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No emails match your filters</p>
          </div>
        ) : (
          <div className="space-y-6 max-h-[600px] overflow-y-auto pr-2">
            {emailGroups.map((group) => (
              <div key={group.date}>
                {/* Date separator */}
                <div className="flex items-center justify-center mb-4">
                  <div className="bg-slate-100 text-slate-600 text-xs font-medium px-3 py-1 rounded-full">
                    {group.label}
                  </div>
                </div>

                {/* Messages for this date */}
                <div className="space-y-3">
                  {group.emails.map((email) => (
                    <MessageBubble
                      key={email.email_id}
                      email={email}
                      isExpanded={expandedEmails.has(email.email_id)}
                      onToggle={() => toggleEmail(email.email_id)}
                      searchTerm={searchTerm}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />

        {/* Footer with total count */}
        <div className="text-center text-xs text-slate-400 pt-2 border-t">
          {allEmails.length} message{allEmails.length !== 1 ? "s" : ""} in this conversation
        </div>
      </CardContent>
    </Card>
  );
}
