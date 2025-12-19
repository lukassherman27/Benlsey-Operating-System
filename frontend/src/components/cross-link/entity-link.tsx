"use client";

import * as React from "react";
import * as HoverCard from "@radix-ui/react-hover-card";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  FileText,
  Briefcase,
  User,
  Mail,
  Calendar,
  Loader2,
  ExternalLink,
  Target,
  Clock,
  DollarSign,
  AlertCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

// =============================================================================
// TYPES
// =============================================================================

export type EntityType = "proposal" | "project" | "contact" | "email" | "meeting";

export interface EntityLinkProps {
  type: EntityType;
  id: string | number;
  label: string;
  showIcon?: boolean;
  showPreview?: boolean;
  className?: string;
}

// Preview data types
interface ProposalPreview {
  project_code: string;
  project_name: string;
  client_company: string;
  project_value: number;
  status: string;
  health_score: number;
  ball_in_court: string;
  days_since_contact: number;
  waiting_for: string | null;
}

interface ProjectPreview {
  project_code: string;
  project_title: string;
  client_name: string;
  total_fee_usd: number;
  total_paid: number;
  outstanding: number;
  health_status: string;
  days_since_activity: number;
}

interface ContactPreview {
  contact_id: number;
  name: string;
  email: string;
  company: string;
  role: string;
  email_count: number;
  last_contact_date: string | null;
  is_primary: boolean;
}

interface EmailPreview {
  email_id: number;
  subject: string;
  sender_name: string;
  sender_email: string;
  date: string;
  ai_summary: string | null;
  sentiment: string | null;
  urgency_level: string | null;
  key_points: string[];
}

// =============================================================================
// ENTITY ICON MAPPING
// =============================================================================

const entityIcons: Record<EntityType, typeof FileText> = {
  proposal: Target,
  project: Briefcase,
  contact: User,
  email: Mail,
  meeting: Calendar,
};

const entityColors: Record<EntityType, string> = {
  proposal: "text-amber-600",
  project: "text-emerald-600",
  contact: "text-blue-600",
  email: "text-purple-600",
  meeting: "text-teal-600",
};

// =============================================================================
// URL BUILDERS
// =============================================================================

function getEntityUrl(type: EntityType, id: string | number): string {
  switch (type) {
    case "proposal":
      return `/proposals/${encodeURIComponent(String(id))}`;
    case "project":
      return `/projects/${encodeURIComponent(String(id))}`;
    case "contact":
      return `/contacts/${id}`;
    case "email":
      return `/emails/${id}`;
    case "meeting":
      return `/meetings/${id}`;
    default:
      return "#";
  }
}

// =============================================================================
// PREVIEW CARD COMPONENTS
// =============================================================================

function ProposalPreviewCard({ data }: { data: ProposalPreview }) {
  const ballColors: Record<string, string> = {
    us: "bg-amber-100 text-amber-800 border-amber-200",
    them: "bg-blue-100 text-blue-800 border-blue-200",
    mutual: "bg-slate-100 text-slate-700 border-slate-200",
    on_hold: "bg-slate-100 text-slate-500 border-slate-200",
  };

  const healthColor = data.health_score >= 70 ? "text-emerald-600" :
                     data.health_score >= 50 ? "text-amber-600" : "text-red-600";

  return (
    <div className="space-y-3">
      <div>
        <p className="font-semibold text-slate-900 text-sm">{data.project_name}</p>
        <p className="text-xs text-slate-500">{data.project_code}</p>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <Badge variant="outline" className="text-xs">{data.status}</Badge>
        <Badge className={cn("text-xs border", ballColors[data.ball_in_court] || ballColors.mutual)}>
          Ball: {data.ball_in_court === "us" ? "OUR MOVE" : data.ball_in_court === "them" ? "THEIR MOVE" : data.ball_in_court.toUpperCase()}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <p className="text-slate-500">Client</p>
          <p className="font-medium text-slate-700 truncate">{data.client_company}</p>
        </div>
        <div>
          <p className="text-slate-500">Value</p>
          <p className="font-medium text-slate-700">
            ${(data.project_value / 1000000).toFixed(1)}M
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs border-t pt-2">
        <div className="flex items-center gap-1">
          <span className="text-slate-500">Health:</span>
          <span className={cn("font-semibold", healthColor)}>{data.health_score}</span>
        </div>
        <div className="flex items-center gap-1 text-slate-500">
          <Clock className="h-3 w-3" />
          {data.days_since_contact}d ago
        </div>
      </div>

      {data.waiting_for && (
        <p className="text-xs text-slate-500 italic truncate">
          Waiting: {data.waiting_for}
        </p>
      )}
    </div>
  );
}

function ProjectPreviewCard({ data }: { data: ProjectPreview }) {
  const paidPercent = data.total_fee_usd > 0
    ? Math.round((data.total_paid / data.total_fee_usd) * 100)
    : 0;

  const healthColors: Record<string, string> = {
    healthy: "bg-emerald-100 text-emerald-800",
    attention: "bg-amber-100 text-amber-800",
    at_risk: "bg-red-100 text-red-800",
  };

  return (
    <div className="space-y-3">
      <div>
        <p className="font-semibold text-slate-900 text-sm">{data.project_title}</p>
        <p className="text-xs text-slate-500">{data.project_code}</p>
      </div>

      <div className="flex items-center gap-2">
        <Badge className={cn("text-xs", healthColors[data.health_status] || "bg-slate-100 text-slate-700")}>
          {data.health_status}
        </Badge>
      </div>

      <div className="space-y-1">
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">Contract</span>
          <span className="font-medium">${(data.total_fee_usd / 1000000).toFixed(2)}M</span>
        </div>
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full"
            style={{ width: `${paidPercent}%` }}
          />
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-emerald-600">${(data.total_paid / 1000).toFixed(0)}K paid</span>
          {data.outstanding > 0 && (
            <span className="text-amber-600">${(data.outstanding / 1000).toFixed(0)}K outstanding</span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1 text-xs text-slate-500 border-t pt-2">
        <Clock className="h-3 w-3" />
        Last activity: {data.days_since_activity}d ago
      </div>
    </div>
  );
}

function ContactPreviewCard({ data }: { data: ContactPreview }) {
  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-semibold text-slate-900 text-sm">{data.name}</p>
          {data.role && <p className="text-xs text-slate-600">{data.role}</p>}
          <p className="text-xs text-slate-500">{data.company}</p>
        </div>
        {data.is_primary && (
          <Badge className="bg-teal-100 text-teal-800 text-xs">Primary</Badge>
        )}
      </div>

      <div className="text-xs space-y-1">
        <p className="text-slate-600 truncate">{data.email}</p>
      </div>

      <div className="flex items-center justify-between text-xs border-t pt-2">
        <div className="flex items-center gap-1">
          <Mail className="h-3 w-3 text-slate-400" />
          <span className="text-slate-600">{data.email_count} emails</span>
        </div>
        {data.last_contact_date && (
          <span className="text-slate-500">
            Last: {new Date(data.last_contact_date).toLocaleDateString()}
          </span>
        )}
      </div>

      <Button
        size="sm"
        variant="outline"
        className="w-full text-xs h-7"
        onClick={(e) => {
          e.preventDefault();
          window.location.href = `mailto:${data.email}`;
        }}
      >
        <Mail className="h-3 w-3 mr-1" />
        Send Email
      </Button>
    </div>
  );
}

function EmailPreviewCard({ data }: { data: EmailPreview }) {
  const sentimentColors: Record<string, string> = {
    positive: "bg-emerald-100 text-emerald-800",
    neutral: "bg-slate-100 text-slate-700",
    concerned: "bg-amber-100 text-amber-800",
    urgent: "bg-red-100 text-red-800",
  };

  const urgencyColors: Record<string, string> = {
    low: "text-slate-500",
    medium: "text-blue-600",
    high: "text-amber-600",
    critical: "text-red-600",
  };

  return (
    <div className="space-y-3">
      <div>
        <p className="font-semibold text-slate-900 text-sm line-clamp-2">{data.subject}</p>
        <p className="text-xs text-slate-500 mt-1">
          From: {data.sender_name || data.sender_email}
        </p>
        <p className="text-xs text-slate-400">
          {new Date(data.date).toLocaleDateString()} {new Date(data.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        {data.sentiment && (
          <Badge className={cn("text-xs", sentimentColors[data.sentiment] || sentimentColors.neutral)}>
            {data.sentiment}
          </Badge>
        )}
        {data.urgency_level && data.urgency_level !== "low" && (
          <span className={cn("text-xs font-medium", urgencyColors[data.urgency_level])}>
            {data.urgency_level} priority
          </span>
        )}
      </div>

      {data.ai_summary && (
        <div className="text-xs text-slate-600 bg-slate-50 rounded p-2">
          <p className="font-medium text-slate-500 mb-1">AI Summary:</p>
          <p className="line-clamp-3">{data.ai_summary}</p>
        </div>
      )}

      {data.key_points && data.key_points.length > 0 && (
        <div className="text-xs">
          <p className="font-medium text-slate-500 mb-1">Key Points:</p>
          <ul className="list-disc list-inside text-slate-600 space-y-0.5">
            {data.key_points.slice(0, 3).map((point, i) => (
              <li key={i} className="truncate">{point}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function PreviewLoading() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-5 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-8 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  );
}

function PreviewError({ message }: { message?: string }) {
  return (
    <div className="flex items-center gap-2 text-xs text-red-600">
      <AlertCircle className="h-4 w-4" />
      <span>{message || "Failed to load preview"}</span>
    </div>
  );
}

// =============================================================================
// PREVIEW CONTENT WRAPPER
// =============================================================================

function PreviewContent({ type, id }: { type: EntityType; id: string | number }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["entity-preview", type, id],
    queryFn: async () => {
      // Use the preview API endpoints
      switch (type) {
        case "proposal":
          return api.getPreviewProposal(String(id));
        case "project":
          return api.getPreviewProject(String(id));
        case "contact":
          return api.getPreviewContact(Number(id));
        case "email":
          return api.getPreviewEmail(Number(id));
        default:
          throw new Error(`Preview not supported for ${type}`);
      }
    },
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
    enabled: true,
  });

  if (isLoading) return <PreviewLoading />;
  if (error || !data?.success) return <PreviewError />;

  switch (type) {
    case "proposal":
      return <ProposalPreviewCard data={data.preview as ProposalPreview} />;
    case "project":
      return <ProjectPreviewCard data={data.preview as ProjectPreview} />;
    case "contact":
      return <ContactPreviewCard data={data.preview as ContactPreview} />;
    case "email":
      return <EmailPreviewCard data={data.preview as EmailPreview} />;
    default:
      return <PreviewError message="Preview not available" />;
  }
}

// =============================================================================
// MAIN ENTITY LINK COMPONENT
// =============================================================================

export function EntityLink({
  type,
  id,
  label,
  showIcon = true,
  showPreview = true,
  className,
}: EntityLinkProps) {
  const Icon = entityIcons[type];
  const iconColor = entityColors[type];
  const href = getEntityUrl(type, id);

  const linkContent = (
    <Link
      href={href}
      className={cn(
        "inline-flex items-center gap-1.5 font-medium text-sm",
        "text-slate-700 hover:text-teal-600 hover:underline underline-offset-2",
        "transition-colors duration-150",
        className
      )}
    >
      {showIcon && <Icon className={cn("h-3.5 w-3.5 shrink-0", iconColor)} />}
      <span className="truncate">{label}</span>
    </Link>
  );

  if (!showPreview) {
    return linkContent;
  }

  return (
    <HoverCard.Root openDelay={200} closeDelay={100}>
      <HoverCard.Trigger asChild>
        {linkContent}
      </HoverCard.Trigger>
      <HoverCard.Portal>
        <HoverCard.Content
          className={cn(
            "w-72 p-4 bg-white rounded-xl shadow-lg border border-slate-200",
            "animate-in fade-in-0 zoom-in-95 duration-200",
            "data-[side=bottom]:slide-in-from-top-2",
            "data-[side=top]:slide-in-from-bottom-2",
            "z-50"
          )}
          sideOffset={8}
          align="start"
        >
          <PreviewContent type={type} id={id} />
          <HoverCard.Arrow className="fill-white" />
        </HoverCard.Content>
      </HoverCard.Portal>
    </HoverCard.Root>
  );
}

// =============================================================================
// CONVENIENCE COMPONENTS
// =============================================================================

export function ProposalLink({ projectCode, label, ...props }: Omit<EntityLinkProps, "type" | "id"> & { projectCode: string }) {
  return <EntityLink type="proposal" id={projectCode} label={label} {...props} />;
}

export function ProjectLink({ projectCode, label, ...props }: Omit<EntityLinkProps, "type" | "id"> & { projectCode: string }) {
  return <EntityLink type="project" id={projectCode} label={label} {...props} />;
}

export function ContactLink({ contactId, label, ...props }: Omit<EntityLinkProps, "type" | "id"> & { contactId: number }) {
  return <EntityLink type="contact" id={contactId} label={label} {...props} />;
}

export function EmailLink({ emailId, label, ...props }: Omit<EntityLinkProps, "type" | "id"> & { emailId: number }) {
  return <EntityLink type="email" id={emailId} label={label} {...props} />;
}
