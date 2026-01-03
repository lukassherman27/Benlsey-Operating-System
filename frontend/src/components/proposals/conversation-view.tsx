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
  Filter,
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

function groupEmailsByDate(emails: ConversationEmail[]) {
  const groups: { date: string; label: string; emails: ConversationEmail[] }[] = [];
  let currentGroup: { date: string; label: string; emails: ConversationEmail[] } | null = null;

  emails.forEach((email) => {
    const emailDate = email.date ? email.date.substring(0, 10) : "";
    if (!currentGroup || currentGroup.date !== emailDate) {
      let label = emailDate;
      try {
        const dateObj = parseISO(emailDate);
        if (isToday(dateObj)) label = "Today";
        else if (isYesterday(dateObj)) label = "Yesterday";
        else label = format(dateObj, "MMMM d, yyyy");
      } catch { label = emailDate; }
      currentGroup = { date: emailDate, label, emails: [] };
      groups.push(currentGroup);
    }
    currentGroup.emails.push(email);
  });
  return groups;
}

function getSenderName(email: ConversationEmail): string {
  switch (email.sender_category) {
    case "bill": return "Bill Bensley";
    case "brian": return "Brian Sherman";
    case "lukas": return "Lukas Sherman";
    case "mink": return "Mink";
    case "bensley_other":
      const match = email.sender_email?.match(/([^@<]+)@/);
      return match ? match[1].replace(/\./g, " ").split(" ").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ") : "Bensley Team";
    default:
      const clientMatch = email.sender_email?.match(/^([^<]+)</);
      if (clientMatch) return clientMatch[1].trim().replace(/"/g, "");
      const emailMatch = email.sender_email?.match(/([^@<]+)@/);
      if (emailMatch) return emailMatch[1].replace(/[._]/g, " ").split(" ").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
      return email.sender_email || "Unknown";
  }
}

function isBensleyPerson(category: string): boolean {
  return ["bill", "brian", "lukas", "mink", "bensley_other"].includes(category);
}

function getInitials(name: string): string {
  const words = name.trim().split(/\s+/);
  return words.length >= 2 ? (words[0][0] + words[words.length - 1][0]).toUpperCase() : name.substring(0, 2).toUpperCase();
}

function getAvatarColor(category: string): string {
  const colors: Record<string, string> = {
    bill: "bg-blue-600 text-white",
    brian: "bg-emerald-600 text-white",
    lukas: "bg-purple-600 text-white",
    mink: "bg-amber-600 text-white",
    bensley_other: "bg-slate-600 text-white",
  };
  return colors[category] || "bg-gray-400 text-white";
}

function MessageBubble({ email, isExpanded, onToggle, searchQuery }: {
  email: ConversationEmail; isExpanded: boolean; onToggle: () => void; searchQuery: string;
}) {
  const isBensley = isBensleyPerson(email.sender_category);
  const senderName = getSenderName(email);
  const initials = getInitials(senderName);
  const avatarColor = getAvatarColor(email.sender_category);

  let timeDisplay = "";
  try { timeDisplay = format(parseISO(email.date), "h:mm a"); }
  catch { timeDisplay = email.date?.substring(11, 16) || ""; }

  // Use only body_preview per #385 security requirement
  const bodyText = email.body_preview || "";
  const stripHtmlTags = (html: string): string => {
    let text = html, prev = "";
    while (prev !== text) { prev = text; text = text.replace(/<[^>]*>/g, " "); }
    return text.replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&lt;/g, "").replace(/&gt;/g, "")
      .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/\s+/g, " ").trim();
  };
  const cleanedBody = stripHtmlTags(bodyText);

  const highlightMatches = (text: string, query: string) => {
    if (!query.trim()) return text;
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.split(regex).map((part, i) =>
      regex.test(part) ? <mark key={i} className="bg-yellow-200 px-0.5 rounded">{part}</mark> : part
    );
  };

  return (
    <div className={cn("flex gap-2 max-w-[85%]", isBensley ? "ml-auto flex-row-reverse" : "mr-auto")}>
      <div className={cn("flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium", avatarColor)}>{initials}</div>
      <div className="flex flex-col">
        <div className={cn("flex items-center gap-2 mb-1 text-xs text-slate-500", isBensley ? "flex-row-reverse" : "")}>
          <span className="font-medium">{senderName}</span>
          <span>{timeDisplay}</span>
          {email.has_attachments && <Paperclip className="h-3 w-3" />}
        </div>
        <div className={cn("rounded-2xl px-4 py-2 cursor-pointer transition-all", isBensley ? "bg-blue-500 text-white rounded-tr-sm" : "bg-slate-100 text-slate-900 rounded-tl-sm")} onClick={onToggle}>
          <p className={cn("font-medium text-sm mb-1", isBensley ? "text-blue-100" : "text-slate-600")}>{highlightMatches(email.subject || "(No subject)", searchQuery)}</p>
          <p className={cn("text-sm", isExpanded ? "" : "line-clamp-3")}>{searchQuery ? highlightMatches(cleanedBody || "(No content)", searchQuery) : (cleanedBody || "(No content)")}</p>
          {cleanedBody.length > 200 && (
            <div className={cn("flex items-center justify-center mt-2 text-xs", isBensley ? "text-blue-200" : "text-slate-400")}>
              {isExpanded ? <><ChevronUp className="h-3 w-3 mr-1" />Show less</> : <><ChevronDown className="h-3 w-3 mr-1" />Show more</>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function WaitingIndicator({ lastEmail, emails }: { lastEmail: ConversationEmail | undefined; emails: ConversationEmail[] }) {
  if (!lastEmail || emails.length === 0) return null;
  const isBensleyLast = isBensleyPerson(lastEmail.sender_category);
  let daysWaiting = 0;
  try { daysWaiting = differenceInDays(new Date(), parseISO(lastEmail.date)); } catch { return null; }
  if (daysWaiting < 1) return null;
  return (
    <div className={cn("flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm", isBensleyLast ? "bg-amber-50 text-amber-700 border border-amber-200" : "bg-blue-50 text-blue-700 border border-blue-200")}>
      <Clock className="h-4 w-4" />
      {isBensleyLast ? <span>Waiting <strong>{daysWaiting} day{daysWaiting !== 1 ? "s" : ""}</strong> for client response</span> : <span>Client waiting <strong>{daysWaiting} day{daysWaiting !== 1 ? "s" : ""}</strong> for your response</span>}
    </div>
  );
}

function Pagination({ currentPage, totalPages, onPageChange }: { currentPage: number; totalPages: number; onPageChange: (page: number) => void }) {
  if (totalPages <= 1) return null;
  return (
    <div className="flex items-center justify-center gap-2 pt-4 border-t">
      <Button variant="outline" size="sm" onClick={() => onPageChange(currentPage - 1)} disabled={currentPage === 1}><ChevronLeft className="h-4 w-4" /></Button>
      <span className="text-sm text-slate-600">Page {currentPage} of {totalPages}</span>
      <Button variant="outline" size="sm" onClick={() => onPageChange(currentPage + 1)} disabled={currentPage === totalPages}><ChevronRight className="h-4 w-4" /></Button>
    </div>
  );
}

export function ConversationView({ projectCode }: ConversationViewProps) {
  const [expandedEmails, setExpandedEmails] = useState<Set<number>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");
  const [senderFilter, setSenderFilter] = useState<"all" | "bensley" | "client">("all");
  const [dateFilter, setDateFilter] = useState<"all" | "7days" | "30days" | "90days">("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["proposal-conversation", projectCode],
    queryFn: () => api.getProposalConversation(projectCode),
    enabled: !!projectCode,
  });

  const toggleEmail = (emailId: number) => {
    setExpandedEmails(prev => { const next = new Set(prev); next.has(emailId) ? next.delete(emailId) : next.add(emailId); return next; });
  };

  const filteredEmails = useMemo(() => {
    if (!data?.emails) return [];
    let emails = [...data.emails];
    if (senderFilter === "bensley") emails = emails.filter(e => isBensleyPerson(e.sender_category));
    else if (senderFilter === "client") emails = emails.filter(e => !isBensleyPerson(e.sender_category));
    if (dateFilter !== "all") {
      const daysMap = { "7days": 7, "30days": 30, "90days": 90 };
      const cutoffDate = subDays(new Date(), daysMap[dateFilter]);
      emails = emails.filter(e => { try { return isAfter(parseISO(e.date), cutoffDate); } catch { return true; } });
    }
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      emails = emails.filter(e => e.subject?.toLowerCase().includes(query) || e.body_preview?.toLowerCase().includes(query) || e.sender_email?.toLowerCase().includes(query));
    }
    return emails;
  }, [data?.emails, senderFilter, dateFilter, searchQuery]);

  const totalPages = Math.ceil(filteredEmails.length / EMAILS_PER_PAGE);
  const paginatedEmails = useMemo(() => filteredEmails.slice((currentPage - 1) * EMAILS_PER_PAGE, currentPage * EMAILS_PER_PAGE), [filteredEmails, currentPage]);

  const handleFilterChange = () => setCurrentPage(1);
  const clearFilters = () => { setSearchQuery(""); setSenderFilter("all"); setDateFilter("all"); setCurrentPage(1); };
  const hasActiveFilters = searchQuery || senderFilter !== "all" || dateFilter !== "all";

  if (isLoading) return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><MessageCircle className="h-5 w-5" />Conversation</CardTitle></CardHeader>
    <CardContent><div className="space-y-4">{[1, 2, 3].map((i) => <div key={i} className="flex gap-3"><Skeleton className="h-8 w-8 rounded-full" /><Skeleton className="h-20 flex-1 rounded-2xl" /></div>)}</div></CardContent></Card>
  );

  if (isError) return (
    <Card className="border-destructive"><CardHeader><CardTitle className="text-destructive">Error Loading Conversation</CardTitle></CardHeader>
    <CardContent><p className="text-sm text-muted-foreground">{error instanceof Error ? error.message : "Failed to load conversation"}</p></CardContent></Card>
  );

  const allEmails = data?.emails || [];
  const emailGroups = groupEmailsByDate(paginatedEmails);
  const lastEmail = allEmails[allEmails.length - 1];
  const bensleyCount = allEmails.filter(e => isBensleyPerson(e.sender_category)).length;
  const clientCount = allEmails.filter(e => !isBensleyPerson(e.sender_category)).length;

  if (allEmails.length === 0) return (
    <Card><CardHeader><CardTitle className="flex items-center gap-2"><MessageCircle className="h-5 w-5" />Conversation</CardTitle></CardHeader>
    <CardContent><div className="text-center py-8 text-muted-foreground"><User className="h-12 w-12 mx-auto mb-4 opacity-50" /><p>No external correspondence yet</p><p className="text-sm">Emails with clients will appear here</p></div></CardContent></Card>
  );

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2"><MessageCircle className="h-5 w-5" />Conversation</CardTitle>
          <div className="flex gap-2">
            <Badge variant="outline" className="text-xs"><span className="inline-block w-2 h-2 rounded-full bg-blue-500 mr-1.5" />{bensleyCount} from us</Badge>
            <Badge variant="outline" className="text-xs"><span className="inline-block w-2 h-2 rounded-full bg-gray-400 mr-1.5" />{clientCount} from client</Badge>
          </div>
        </div>
        <div className="mt-3 space-y-2">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input placeholder="Search emails..." value={searchQuery} onChange={(e) => { setSearchQuery(e.target.value); handleFilterChange(); }} className="pl-9 h-9" />
            </div>
            <Button variant={showFilters ? "secondary" : "outline"} size="sm" onClick={() => setShowFilters(!showFilters)} className="h-9">
              <Filter className="h-4 w-4 mr-1" />Filters{hasActiveFilters && <span className="ml-1 w-2 h-2 rounded-full bg-blue-500" />}
            </Button>
          </div>
          {showFilters && (
            <div className="flex flex-wrap gap-2 p-3 bg-slate-50 rounded-lg">
              <Select value={senderFilter} onValueChange={(v: "all" | "bensley" | "client") => { setSenderFilter(v); handleFilterChange(); }}>
                <SelectTrigger className="w-[140px] h-8"><SelectValue placeholder="Sender" /></SelectTrigger>
                <SelectContent><SelectItem value="all">All senders</SelectItem><SelectItem value="bensley">From Bensley</SelectItem><SelectItem value="client">From Client</SelectItem></SelectContent>
              </Select>
              <Select value={dateFilter} onValueChange={(v: "all" | "7days" | "30days" | "90days") => { setDateFilter(v); handleFilterChange(); }}>
                <SelectTrigger className="w-[140px] h-8"><SelectValue placeholder="Date range" /></SelectTrigger>
                <SelectContent><SelectItem value="all">All time</SelectItem><SelectItem value="7days">Last 7 days</SelectItem><SelectItem value="30days">Last 30 days</SelectItem><SelectItem value="90days">Last 90 days</SelectItem></SelectContent>
              </Select>
              {hasActiveFilters && <Button variant="ghost" size="sm" onClick={clearFilters} className="h-8 text-slate-500"><X className="h-3 w-3 mr-1" />Clear</Button>}
            </div>
          )}
          {hasActiveFilters && <p className="text-xs text-slate-500">Showing {filteredEmails.length} of {allEmails.length} emails</p>}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {!hasActiveFilters && <WaitingIndicator lastEmail={lastEmail} emails={allEmails} />}
        {paginatedEmails.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground"><Search className="h-8 w-8 mx-auto mb-2 opacity-50" /><p>No emails match your search</p><Button variant="link" size="sm" onClick={clearFilters} className="mt-2">Clear filters</Button></div>
        ) : (
          <div className="space-y-6 max-h-[600px] overflow-y-auto pr-2">
            {emailGroups.map((group) => (
              <div key={group.date}>
                <div className="flex items-center justify-center mb-4"><div className="bg-slate-100 text-slate-600 text-xs font-medium px-3 py-1 rounded-full">{group.label}</div></div>
                <div className="space-y-3">{group.emails.map((email) => <MessageBubble key={email.email_id} email={email} isExpanded={expandedEmails.has(email.email_id)} onToggle={() => toggleEmail(email.email_id)} searchQuery={searchQuery} />)}</div>
              </div>
            ))}
          </div>
        )}
        <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />
        <div className="text-center text-xs text-slate-400 pt-2 border-t">{allEmails.length} message{allEmails.length !== 1 ? "s" : ""} in this conversation</div>
      </CardContent>
    </Card>
  );
}
