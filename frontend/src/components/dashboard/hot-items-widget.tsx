"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { DollarSign, FileText, HelpCircle, Sparkles, ChevronRight, AlertTriangle, Flame } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import Link from "next/link";

interface HotItem {
  type: "invoice" | "proposal" | "rfi" | "suggestion";
  icon: React.ReactNode;
  text: string;
  link: string;
  urgency: "high" | "medium" | "low";
  subtext?: string;
}

export function HotItemsWidget() {
  // Fetch overdue invoices
  const overdueQuery = useQuery({
    queryKey: ["overdue-invoices-hot"],
    queryFn: () => api.getOldestUnpaidInvoices(5),
    staleTime: 1000 * 60 * 5,
  });

  // Fetch proposals needing follow-up
  const proposalsQuery = useQuery({
    queryKey: ["proposals-stale"],
    queryFn: () => api.getDailyBriefing(),
    staleTime: 1000 * 60 * 10,
  });

  // Fetch pending RFIs
  const rfisQuery = useQuery({
    queryKey: ["rfis-pending"],
    queryFn: () => api.getRfis({ status: "pending" }),
    staleTime: 1000 * 60 * 10,
  });

  // Fetch high-confidence suggestions
  const suggestionsQuery = useQuery({
    queryKey: ["suggestions-hot"],
    queryFn: () => api.getSuggestions({ status: "pending", min_confidence: 0.8, limit: 3 }),
    staleTime: 1000 * 60 * 10,
  });

  const hotItems: HotItem[] = [];

  // Add overdue invoices
  if (overdueQuery.data?.invoices) {
    overdueQuery.data.invoices
      .filter((inv: Record<string, unknown>) => (inv.days_overdue as number) > 0)
      .slice(0, 3)
      .forEach((inv: Record<string, unknown>) => {
        hotItems.push({
          type: "invoice",
          icon: <DollarSign className="h-4 w-4" />,
          text: `${inv.project_name || inv.project_code} - ${formatCurrency(inv.amount_outstanding as number)}`,
          subtext: `${inv.days_overdue} days overdue`,
          link: `/projects/${inv.project_code}`,
          urgency: (inv.days_overdue as number) > 60 ? "high" : "medium",
        });
      });
  }

  // Add stale proposals (URGENT - 14+ days or no contact)
  if (proposalsQuery.data?.urgent) {
    proposalsQuery.data.urgent.slice(0, 5).forEach((prop) => {
      // Format: "25 BK-033 (Ritz-Carlton Nusa Dua)" or just code if no name
      const displayText = prop.project_name
        ? `${prop.project_code} (${prop.project_name})`
        : prop.project_code || "Unknown";

      hotItems.push({
        type: "proposal",
        icon: <FileText className="h-4 w-4" />,
        text: displayText,
        subtext: String(prop.context || "Needs attention"),
        link: `/proposals/${prop.project_code}`,
        urgency: "high",
      });
    });
  }

  // Add needs_attention proposals (7-13 days)
  if (proposalsQuery.data?.needs_attention) {
    proposalsQuery.data.needs_attention.slice(0, 5).forEach((prop) => {
      // Format: "25 BK-033 (Ritz-Carlton Nusa Dua)" or just code if no name
      const displayText = prop.project_name
        ? `${prop.project_code} (${prop.project_name})`
        : prop.project_code || "Unknown";

      hotItems.push({
        type: "proposal",
        icon: <FileText className="h-4 w-4" />,
        text: displayText,
        subtext: String(prop.context || "Follow up needed"),
        link: `/proposals/${prop.project_code}`,
        urgency: "medium",
      });
    });
  }

  // Add pending RFIs
  if (rfisQuery.data?.rfis) {
    rfisQuery.data.rfis.slice(0, 2).forEach((rfi: Record<string, unknown>) => {
      hotItems.push({
        type: "rfi",
        icon: <HelpCircle className="h-4 w-4" />,
        text: `RFI: ${rfi.subject || rfi.title || "Pending response"}`,
        subtext: String(rfi.project_code || ""),
        link: "/rfis",
        urgency: "medium",
      });
    });
  }

  // Add high-confidence suggestions
  if (suggestionsQuery.data?.suggestions) {
    suggestionsQuery.data.suggestions.slice(0, 2).forEach((sug) => {
      hotItems.push({
        type: "suggestion",
        icon: <Sparkles className="h-4 w-4" />,
        text: `AI: ${sug.title}`,
        subtext: sug.description?.slice(0, 50) || sug.suggested_action,
        link: "/admin/suggestions",
        urgency: sug.priority === "high" ? "high" : "low",
      });
    });
  }

  const isLoading = overdueQuery.isLoading || proposalsQuery.isLoading;

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-orange-500" />
            <h3 className="font-semibold">Hot Items</h3>
          </div>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-slate-100 rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (hotItems.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-orange-500" />
            <h3 className="font-semibold">Hot Items</h3>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-slate-500">
            <p className="text-sm">No urgent items</p>
            <p className="text-xs mt-1">All caught up!</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Sort by urgency
  const sortedItems = hotItems.sort((a, b) => {
    const urgencyOrder = { high: 0, medium: 1, low: 2 };
    return urgencyOrder[a.urgency] - urgencyOrder[b.urgency];
  });

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-orange-500" />
            <h3 className="font-semibold">Hot Items</h3>
            <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">
              {hotItems.length}
            </span>
          </div>
          <Link
            href="/tracker?filter=needs-followup"
            className="text-xs text-slate-500 hover:text-slate-700 flex items-center gap-1"
          >
            View all <ChevronRight className="h-3 w-3" />
          </Link>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="overflow-x-auto pb-2 -mx-2 px-2">
          <div className="flex gap-3 min-w-max">
            {sortedItems.slice(0, 10).map((item, idx) => (
              <HotItemCard key={idx} item={item} />
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function HotItemCard({ item }: { item: HotItem }) {
  const urgencyStyles = {
    high: "border-red-200 bg-red-50 hover:bg-red-100",
    medium: "border-amber-200 bg-amber-50 hover:bg-amber-100",
    low: "border-blue-200 bg-blue-50 hover:bg-blue-100",
  };

  const iconStyles = {
    high: "text-red-600",
    medium: "text-amber-600",
    low: "text-blue-600",
  };

  return (
    <Link href={item.link}>
      <div
        className={cn(
          "flex items-start gap-3 p-3 rounded-lg border transition-colors cursor-pointer min-w-[200px] max-w-[280px]",
          urgencyStyles[item.urgency]
        )}
      >
        <div className={cn("mt-0.5", iconStyles[item.urgency])}>
          {item.urgency === "high" ? <AlertTriangle className="h-4 w-4" /> : item.icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-900 truncate">
            {item.text}
          </p>
          {item.subtext && (
            <p className="text-xs text-slate-600 truncate mt-0.5">
              {item.subtext}
            </p>
          )}
        </div>
        <ChevronRight className="h-4 w-4 text-slate-400 flex-shrink-0" />
      </div>
    </Link>
  );
}
