"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, Mail, Building2, Star } from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

interface ProjectContactsCardProps {
  projectCode: string;
}

export function ProjectContactsCard({ projectCode }: ProjectContactsCardProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["project", projectCode, "contacts"],
    queryFn: () => api.getProjectContacts(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const contacts = data?.data ?? [];

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null;
    try {
      return format(new Date(dateStr), "MMM d, yyyy");
    } catch {
      return dateStr;
    }
  };

  if (isLoading) {
    return (
      <Card className={ds.cards.default}>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4 text-blue-600" />
            Client Contacts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-slate-100 rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || contacts.length === 0) {
    return (
      <Card className={ds.cards.default}>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4 text-blue-600" />
            Client Contacts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">No contacts found for this project.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={ds.cards.default}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Users className="h-4 w-4 text-blue-600" />
          Client Contacts
          <Badge variant="secondary" className="ml-auto">
            {contacts.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          {contacts.map((contact, idx) => (
            <div
              key={contact.email || idx}
              className={cn(
                "p-3 rounded-lg border",
                contact.is_primary_contact
                  ? "bg-blue-50 border-blue-200"
                  : "bg-slate-50 border-slate-200"
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-900 truncate">
                      {contact.name || contact.email}
                    </span>
                    {contact.is_primary_contact === 1 && (
                      <Star className="h-3.5 w-3.5 text-amber-500 fill-amber-500 flex-shrink-0" />
                    )}
                  </div>

                  {contact.company && (
                    <div className="flex items-center gap-1 text-xs text-slate-500 mt-0.5">
                      <Building2 className="h-3 w-3" />
                      {contact.company}
                    </div>
                  )}

                  <div className="flex items-center gap-1 text-xs text-slate-500 mt-1">
                    <Mail className="h-3 w-3" />
                    <a
                      href={`mailto:${contact.email}`}
                      className="hover:text-blue-600 hover:underline"
                    >
                      {contact.email}
                    </a>
                  </div>
                </div>

                <div className="text-right flex-shrink-0">
                  {contact.email_count > 0 && (
                    <div className="text-xs">
                      <span className="font-medium text-slate-700">
                        {contact.email_count}
                      </span>
                      <span className="text-slate-400 ml-1">emails</span>
                    </div>
                  )}
                  {contact.last_email_date && (
                    <div className="text-xs text-slate-400">
                      Last: {formatDate(contact.last_email_date)}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
