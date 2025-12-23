"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
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
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Users,
  Search,
  Building2,
  Mail,
  Phone,
  Briefcase,
  ChevronRight,
  AlertCircle,
  Calendar,
} from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface Contact {
  contact_id: number;
  name: string | null;
  email: string | null;
  company: string | null;
  role: string | null;
  position: string | null;
  phone: string | null;
  context_notes: string | null;
  source: string | null;
  first_seen_date: string | null;
  notes: string | null;
  client_id: number | null;
}

interface ContactDetail extends Contact {
  client_name?: string | null;
  linked_projects?: {
    project_id: number;
    project_code: string;
    project_title: string;
    status: string;
    email_count: number;
  }[];
  recent_emails?: {
    email_id: number;
    subject: string;
    date: string;
    snippet: string;
  }[];
}

interface ContactsResponse {
  success: boolean;
  contacts: Contact[];
  total: number;
  limit: number;
  offset: number;
}

interface ContactsStatsResponse {
  success: boolean;
  data: {
    total: number;
    unique_companies: number;
    with_email: number;
    with_phone: number;
    top_companies: { company: string; count: number }[];
  };
}

// Fetch contacts
async function fetchContacts(params: {
  search?: string;
  company?: string;
  limit?: number;
  offset?: number;
}): Promise<ContactsResponse> {
  const searchParams = new URLSearchParams();
  if (params.search) searchParams.set("search", params.search);
  if (params.company && params.company !== "all") searchParams.set("company", params.company);
  searchParams.set("limit", String(params.limit ?? 50));
  searchParams.set("offset", String(params.offset ?? 0));

  const response = await fetch(`${API_BASE_URL}/api/contacts?${searchParams}`);
  if (!response.ok) {
    throw new Error("Failed to fetch contacts");
  }
  return response.json();
}

// Fetch contact stats
async function fetchContactStats(): Promise<ContactsStatsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/contacts/stats`);
  if (!response.ok) {
    return { success: false, data: { total: 0, unique_companies: 0, with_email: 0, with_phone: 0, top_companies: [] } };
  }
  return response.json();
}

// Fetch contact detail
async function fetchContactDetail(contactId: number): Promise<ContactDetail | null> {
  const response = await fetch(`${API_BASE_URL}/api/contacts/${contactId}`);
  if (!response.ok) return null;
  const data = await response.json();
  return data.data || data;
}

// Loading skeleton
function ContactsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {[...Array(6)].map((_, i) => (
        <Card key={i} className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="p-4">
            <Skeleton className="h-5 w-3/4 mb-2" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-1/2" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Empty state
function EmptyState() {
  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
      <CardContent className="py-16 text-center">
        <Users className="mx-auto h-16 w-16 text-slate-300 mb-4" />
        <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
          No contacts found
        </p>
        <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
          Contacts will appear here once they&apos;re added to the system.
        </p>
      </CardContent>
    </Card>
  );
}

// Error state
function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50")}>
      <CardContent className="py-12 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
        <p className={cn(ds.typography.heading3, "text-red-700 mb-2")}>
          Failed to load contacts
        </p>
        <Button onClick={onRetry} variant="outline" className="border-red-200 text-red-700 hover:bg-red-100">
          Try Again
        </Button>
      </CardContent>
    </Card>
  );
}

// Contact card
function ContactCard({
  contact,
  onClick,
}: {
  contact: Contact;
  onClick: () => void;
}) {
  const displayName = contact.name || contact.email?.split("@")[0] || "Unknown";

  return (
    <Card
      className={cn(
        ds.borderRadius.card,
        "border-slate-200 cursor-pointer transition-all",
        "hover:border-teal-300 hover:bg-teal-50/30 hover:shadow-md"
      )}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className={cn(ds.typography.bodyBold, ds.textColors.primary, "truncate")}>
              {displayName}
            </h3>
            {contact.email && (
              <p className={cn(ds.typography.caption, "truncate flex items-center gap-1 mt-1")}>
                <Mail className="h-3 w-3 flex-shrink-0" />
                {contact.email}
              </p>
            )}
          </div>
          <ChevronRight className="h-4 w-4 text-slate-400 flex-shrink-0" />
        </div>

        <div className="flex flex-wrap items-center gap-2 mt-3">
          {contact.company && (
            <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
              <Building2 className="h-3 w-3 mr-1" />
              {contact.company}
            </Badge>
          )}
          {contact.position && (
            <Badge variant="outline" className="text-xs">
              <Briefcase className="h-3 w-3 mr-1" />
              {contact.position}
            </Badge>
          )}
        </div>

        {contact.phone && (
          <p className={cn(ds.typography.caption, "mt-2 flex items-center gap-1")}>
            <Phone className="h-3 w-3" />
            {contact.phone}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// Contact detail modal
function ContactDetailModal({
  contactId,
  isOpen,
  onClose,
}: {
  contactId: number | null;
  isOpen: boolean;
  onClose: () => void;
}) {
  const { data: contact, isLoading } = useQuery({
    queryKey: ["contact", contactId],
    queryFn: () => (contactId ? fetchContactDetail(contactId) : null),
    enabled: !!contactId && isOpen,
    staleTime: 1000 * 60 * 5,
  });

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="h-5 w-5 text-teal-600" />
            Contact Details
          </DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="space-y-4 p-4">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        ) : contact ? (
          <ScrollArea className="max-h-[60vh]">
            <div className="space-y-6 p-1">
              {/* Basic Info */}
              <div>
                <h3 className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {contact.name || contact.email?.split("@")[0] || "Unknown"}
                </h3>
                <div className="flex flex-wrap gap-2 mt-2">
                  {contact.company && (
                    <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                      <Building2 className="h-3 w-3 mr-1" />
                      {contact.company}
                    </Badge>
                  )}
                  {contact.position && (
                    <Badge variant="outline">
                      <Briefcase className="h-3 w-3 mr-1" />
                      {contact.position}
                    </Badge>
                  )}
                  {contact.source && (
                    <Badge variant="secondary" className="text-xs">
                      Source: {contact.source}
                    </Badge>
                  )}
                </div>
              </div>

              {/* Contact Info */}
              <div className="grid grid-cols-2 gap-4">
                {contact.email && (
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-slate-500" />
                    <a href={`mailto:${contact.email}`} className="text-teal-600 hover:underline">
                      {contact.email}
                    </a>
                  </div>
                )}
                {contact.phone && (
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-slate-500" />
                    <span>{contact.phone}</span>
                  </div>
                )}
              </div>

              {/* First Seen */}
              {contact.first_seen_date && (
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <Calendar className="h-4 w-4" />
                  First seen: {format(new Date(contact.first_seen_date), "MMM d, yyyy")}
                </div>
              )}

              {/* Context Notes */}
              {contact.context_notes && (
                <div>
                  <h4 className={cn(ds.typography.captionBold, ds.textColors.tertiary, "mb-2")}>
                    Context Notes
                  </h4>
                  <p className={cn(ds.typography.body, "bg-slate-50 p-3 rounded-lg")}>
                    {contact.context_notes}
                  </p>
                </div>
              )}

              {/* Linked Projects */}
              {contact.linked_projects && contact.linked_projects.length > 0 && (
                <div>
                  <h4 className={cn(ds.typography.captionBold, ds.textColors.tertiary, "mb-2")}>
                    Linked Projects ({contact.linked_projects.length})
                  </h4>
                  <div className="space-y-2">
                    {contact.linked_projects.map((project) => (
                      <div
                        key={project.project_id}
                        className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                      >
                        <div>
                          <p className={cn(ds.typography.bodyBold)}>{project.project_code}</p>
                          <p className={cn(ds.typography.caption)}>{project.project_title}</p>
                        </div>
                        <div className="text-right">
                          <Badge variant="outline" className="text-xs">
                            {project.status}
                          </Badge>
                          <p className={cn(ds.typography.caption, "mt-1")}>
                            {project.email_count} emails
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recent Emails */}
              {contact.recent_emails && contact.recent_emails.length > 0 && (
                <div>
                  <h4 className={cn(ds.typography.captionBold, ds.textColors.tertiary, "mb-2")}>
                    Recent Emails ({contact.recent_emails.length})
                  </h4>
                  <div className="space-y-2">
                    {contact.recent_emails.slice(0, 5).map((email) => (
                      <div
                        key={email.email_id}
                        className="p-3 border border-slate-200 rounded-lg"
                      >
                        <p className={cn(ds.typography.bodyBold, "line-clamp-1")}>
                          {email.subject || "No subject"}
                        </p>
                        <p className={cn(ds.typography.caption, "mt-1")}>
                          {email.date && format(new Date(email.date), "MMM d, yyyy")}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        ) : (
          <p className={cn(ds.typography.body, ds.textColors.tertiary, "text-center py-8")}>
            Contact not found
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function ContactsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [companyFilter, setCompanyFilter] = useState<string>("all");
  const [selectedContactId, setSelectedContactId] = useState<number | null>(null);
  const [page, setPage] = useState(0);
  const pageSize = 50;

  // Fetch contacts with pagination
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["contacts", searchQuery, companyFilter, page],
    queryFn: () => fetchContacts({
      search: searchQuery,
      company: companyFilter,
      limit: pageSize,
      offset: page * pageSize,
    }),
    staleTime: 1000 * 60 * 5,
  });

  // Reset page when filters change
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setPage(0);
  };

  const handleCompanyChange = (value: string) => {
    setCompanyFilter(value);
    setPage(0);
  };

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ["contacts-stats"],
    queryFn: fetchContactStats,
    staleTime: 1000 * 60 * 10,
  });

  const contacts = data?.contacts ?? [];
  const total = data?.total ?? 0;
  const stats = statsData?.data;
  const topCompanies = stats?.top_companies ?? [];
  const totalPages = Math.ceil(total / pageSize);
  const startIndex = page * pageSize + 1;
  const endIndex = Math.min((page + 1) * pageSize, total);

  return (
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            Contacts
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Manage your network of clients, collaborators, and partners.
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-teal-100">
                <Users className="h-5 w-5 text-teal-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption)}>Total Contacts</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {isLoading ? "—" : total}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <Building2 className="h-5 w-5 text-blue-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption)}>Companies</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {stats?.unique_companies ?? "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-100">
                <Mail className="h-5 w-5 text-emerald-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption)}>With Email</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {stats?.with_email ?? "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100">
                <Phone className="h-5 w-5 text-purple-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption)}>With Phone</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {stats?.with_phone ?? "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
        <CardContent className="py-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search by name, email, or company..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={companyFilter} onValueChange={handleCompanyChange}>
              <SelectTrigger className="w-[200px]">
                <Building2 className="h-4 w-4 mr-2 text-slate-400" />
                <SelectValue placeholder="Filter by company" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Companies</SelectItem>
                {topCompanies.map((company) => (
                  <SelectItem key={company.company} value={company.company}>
                    {company.company} ({company.count})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      {isLoading ? (
        <ContactsSkeleton />
      ) : error ? (
        <ErrorState onRetry={() => refetch()} />
      ) : contacts.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          <div className="flex items-center justify-between">
            <p className={cn(ds.typography.caption)}>
              Showing {startIndex}-{endIndex} of {total} contacts
            </p>
            {totalPages > 1 && (
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(0)}
                  disabled={page === 0}
                >
                  First
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  Previous
                </Button>
                <span className={cn(ds.typography.caption, "px-2")}>
                  Page {page + 1} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                >
                  Next
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(totalPages - 1)}
                  disabled={page >= totalPages - 1}
                >
                  Last
                </Button>
              </div>
            )}
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {contacts.map((contact) => (
              <ContactCard
                key={contact.contact_id}
                contact={contact}
                onClick={() => setSelectedContactId(contact.contact_id)}
              />
            ))}
          </div>
          {/* Bottom pagination for long lists */}
          {totalPages > 1 && contacts.length > 10 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
              >
                Previous
              </Button>
              <span className={cn(ds.typography.caption, "px-2")}>
                Page {page + 1} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}

      {/* Contact Detail Modal */}
      <ContactDetailModal
        contactId={selectedContactId}
        isOpen={selectedContactId !== null}
        onClose={() => setSelectedContactId(null)}
      />
    </div>
  );
}
