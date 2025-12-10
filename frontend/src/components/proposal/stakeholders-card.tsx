"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { Users, Mail, Phone, Building2, ChevronDown, ChevronRight, Star } from "lucide-react";
import { useState } from "react";
import { format, parseISO, isValid } from "date-fns";
import { cn } from "@/lib/utils";

interface StakeholdersCardProps {
  projectCode: string;
}

interface Stakeholder {
  contact_id: number;
  name: string | null;
  email: string | null;
  role: string | null;
  company: string | null;
  phone: string | null;
  is_primary: number;
  last_contact_date: string | null;
  email_count: number;
}

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return "Never";
  try {
    const date = parseISO(dateStr);
    if (!isValid(date)) return "Never";
    return format(date, "MMM d, yyyy");
  } catch {
    return "Never";
  }
};

export function StakeholdersCard({ projectCode }: StakeholdersCardProps) {
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  const { data, isLoading, error } = useQuery({
    queryKey: ["proposal-stakeholders", projectCode],
    queryFn: () => api.getProposalStakeholders(projectCode),
    retry: 1,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const toggleExpanded = (contactId: number) => {
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(contactId)) {
      newExpanded.delete(contactId);
    } else {
      newExpanded.add(contactId);
    }
    setExpandedIds(newExpanded);
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Stakeholders
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-amber-200 bg-amber-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Stakeholders
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-amber-700">
            Unable to load stakeholders. This feature may not be available yet.
          </p>
        </CardContent>
      </Card>
    );
  }

  const stakeholders: Stakeholder[] = data?.stakeholders || [];

  if (stakeholders.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Stakeholders
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Users className="h-12 w-12 mx-auto text-slate-200 mb-3" />
            <p className="text-muted-foreground text-sm">
              No stakeholders found for this proposal
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Sort: primary first, then by email count
  const sortedStakeholders = [...stakeholders].sort((a, b) => {
    if (a.is_primary !== b.is_primary) return b.is_primary - a.is_primary;
    return b.email_count - a.email_count;
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          Stakeholders
          <Badge variant="secondary" className="ml-2">
            {stakeholders.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {sortedStakeholders.map((stakeholder) => {
            const isExpanded = expandedIds.has(stakeholder.contact_id);
            const displayName = stakeholder.name || stakeholder.email || "Unknown";

            return (
              <div
                key={stakeholder.contact_id}
                className="border rounded-lg overflow-hidden transition-all"
              >
                {/* Collapsed view */}
                <div
                  className={cn(
                    "p-3 cursor-pointer hover:bg-slate-50 transition-colors",
                    isExpanded && "bg-slate-50"
                  )}
                  onClick={() => toggleExpanded(stakeholder.contact_id)}
                >
                  <div className="flex items-start gap-2">
                    <div className="flex-shrink-0 mt-0.5">
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4 text-slate-500" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-slate-500" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-medium text-sm truncate">{displayName}</p>
                        {stakeholder.is_primary === 1 && (
                          <Badge variant="default" className="text-xs flex items-center gap-1">
                            <Star className="h-3 w-3" />
                            Primary
                          </Badge>
                        )}
                        {stakeholder.email_count > 0 && (
                          <Badge variant="outline" className="text-xs">
                            {stakeholder.email_count} email{stakeholder.email_count !== 1 ? 's' : ''}
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-slate-500 flex-wrap">
                        {stakeholder.role && (
                          <span className="flex items-center gap-1">
                            {stakeholder.role}
                          </span>
                        )}
                        {stakeholder.company && (
                          <span className="flex items-center gap-1">
                            <Building2 className="h-3 w-3" />
                            {stakeholder.company}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Expanded view */}
                {isExpanded && (
                  <div className="px-3 pb-3 pt-2 bg-slate-50 border-t space-y-2">
                    {stakeholder.email && (
                      <div className="flex items-start gap-2 text-sm">
                        <Mail className="h-4 w-4 text-slate-400 mt-0.5 flex-shrink-0" />
                        <span className="text-slate-700 break-all">{stakeholder.email}</span>
                      </div>
                    )}
                    {stakeholder.phone && (
                      <div className="flex items-start gap-2 text-sm">
                        <Phone className="h-4 w-4 text-slate-400 mt-0.5 flex-shrink-0" />
                        <span className="text-slate-700">{stakeholder.phone}</span>
                      </div>
                    )}
                    {stakeholder.last_contact_date && (
                      <div className="flex items-start gap-2 text-sm">
                        <Mail className="h-4 w-4 text-slate-400 mt-0.5 flex-shrink-0" />
                        <span className="text-slate-500">
                          Last contact: {formatDate(stakeholder.last_contact_date)}
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
