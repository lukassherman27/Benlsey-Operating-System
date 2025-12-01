"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Plus,
  FileText,
  Mail,
  Search,
  BarChart3
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

export function QuickActionsWidget() {
  const actions = [
    {
      label: "New Proposal",
      icon: Plus,
      href: "/tracker",
      iconBg: "bg-blue-500",
      iconHover: "group-hover:bg-blue-600",
      description: "Create proposal"
    },
    {
      label: "View Tracker",
      icon: FileText,
      href: "/tracker",
      iconBg: "bg-purple-500",
      iconHover: "group-hover:bg-purple-600",
      description: "Proposal tracker"
    },
    {
      label: "Active Projects",
      icon: BarChart3,
      href: "/projects",
      iconBg: "bg-green-500",
      iconHover: "group-hover:bg-green-600",
      description: "View projects"
    },
    {
      label: "Search Emails",
      icon: Mail,
      href: "/query",
      iconBg: "bg-orange-500",
      iconHover: "group-hover:bg-orange-600",
      description: "AI email search"
    },
    {
      label: "Query System",
      icon: Search,
      href: "/query",
      iconBg: "bg-slate-500",
      iconHover: "group-hover:bg-slate-600",
      description: "AI search"
    },
  ];

  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
      <CardHeader>
        <div>
          <p className={cn(ds.typography.label, ds.textColors.muted)}>
            Quick Actions
          </p>
          <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
            Common Tasks
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          {actions.map((action, idx) => {
            const Icon = action.icon;
            return (
              <Link key={idx} href={action.href}>
                <Button
                  variant="outline"
                  className={cn(
                    "group w-full h-auto flex-col items-center gap-2 p-4",
                    "border-slate-200 bg-white",
                    ds.hover.card
                  )}
                >
                  <div className={cn(
                    ds.borderRadius.button,
                    "p-3 text-white transition-colors",
                    ds.shadows.md,
                    action.iconBg,
                    action.iconHover
                  )}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="text-center">
                    <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                      {action.label}
                    </p>
                    <p className={cn(ds.typography.tiny, ds.textColors.tertiary)}>
                      {action.description}
                    </p>
                  </div>
                </Button>
              </Link>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
