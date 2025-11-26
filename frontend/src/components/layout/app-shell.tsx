"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { PropsWithChildren, useState } from "react";
import {
  BarChart3,
  FileText,
  Home,
  ListChecks,
  Mail,
  Search,
  ChevronDown,
  ChevronRight,
  ClipboardList,
  Settings,
  CheckSquare,
  Link2,
  DollarSign,
  CalendarCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

type NavItem = {
  href: string;
  label: string;
  icon: React.ElementType;
  disabled?: boolean;
  subItems?: { href: string; label: string; icon: React.ElementType }[];
};

const navItems: NavItem[] = [
  { href: "/", label: "Overview", icon: Home },
  { href: "/tracker", label: "Proposals", icon: ListChecks },
  { href: "/projects", label: "Active Projects", icon: FileText },
  { href: "/deliverables", label: "Deliverables", icon: CalendarCheck },
  { href: "/query", label: "Query", icon: Search },
  { href: "/emails", label: "Emails", icon: Mail },
  {
    href: "/admin",
    label: "Admin",
    icon: Settings,
    subItems: [
      { href: "/admin/validation", label: "Data Validation", icon: CheckSquare },
      { href: "/admin/email-links", label: "Email Links", icon: Link2 },
      { href: "/admin/financial-entry", label: "Financial Entry", icon: DollarSign }
    ]
  },
  { href: "/analytics", label: "Analytics", icon: BarChart3, disabled: true },
];

export default function AppShell({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  const toggleExpanded = (href: string) => {
    setExpandedItems((prev) =>
      prev.includes(href) ? prev.filter((h) => h !== href) : [...prev, href]
    );
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="flex">
        <aside className={cn(
          "hidden w-72 flex-col border-r border-slate-200 bg-white/95 backdrop-blur lg:flex",
          ds.spacing.spacious,
          ds.shadows.sm
        )}>
          <div className={cn("mb-10 flex items-center", ds.gap.normal)}>
            <Image
              src="/images/bensley-wordmark.svg"
              alt="Bensley Design Studios"
              width={140}
              height={48}
              priority
              className="h-12 w-auto"
            />
          </div>
          <nav className={cn(ds.gap.tight, "space-y-1")}>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              const hasSubItems = item.subItems && item.subItems.length > 0;
              const isExpanded = expandedItems.includes(item.href);

              return (
                <div key={item.href}>
                  <div className="flex items-center">
                    <Link
                      href={item.href}
                      aria-disabled={item.disabled}
                      className={cn(
                        "flex flex-1 items-center px-3 py-2 transition-all duration-200",
                        ds.borderRadius.button,
                        ds.gap.normal,
                        ds.typography.bodyBold,
                        item.disabled && "pointer-events-none opacity-40",
                        isActive && !hasSubItems
                          ? cn(
                              ds.status.info.bg,
                              ds.status.info.border,
                              ds.status.info.text,
                              "border",
                              ds.shadows.sm
                            )
                          : cn(
                              ds.textColors.secondary,
                              "hover:bg-slate-50",
                              ds.hover.subtle
                            )
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      {item.label}
                      {item.disabled && (
                        <span className={cn(
                          "ml-auto px-2 py-0.5",
                          ds.borderRadius.badge,
                          ds.typography.tiny,
                          "bg-slate-100 text-slate-600"
                        )}>
                          Soon
                        </span>
                      )}
                    </Link>
                    {hasSubItems && (
                      <button
                        onClick={() => toggleExpanded(item.href)}
                        className={cn(
                          "p-2 transition-colors duration-200",
                          ds.borderRadius.button,
                          ds.textColors.tertiary,
                          "hover:bg-slate-100",
                          ds.hover.subtle
                        )}
                      >
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </button>
                    )}
                  </div>
                  {hasSubItems && isExpanded && (
                    <div className={cn("ml-7 mt-1", ds.gap.tight, "space-y-1")}>
                      {item.subItems!.map((subItem) => {
                        const SubIcon = subItem.icon;
                        const isSubActive = pathname === subItem.href;
                        return (
                          <Link
                            key={subItem.href}
                            href={subItem.href}
                            className={cn(
                              "flex items-center px-3 py-1.5 transition-all duration-200",
                              ds.borderRadius.card,
                              ds.gap.normal,
                              ds.typography.body,
                              isSubActive
                                ? cn(
                                    ds.status.info.bg,
                                    ds.status.info.border,
                                    ds.status.info.text,
                                    "border",
                                    ds.shadows.sm
                                  )
                                : cn(
                                    ds.textColors.tertiary,
                                    "hover:bg-slate-50",
                                    ds.hover.subtle
                                  )
                            )}
                          >
                            <SubIcon className="h-3.5 w-3.5" />
                            {subItem.label}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>
          <div className={cn(
            "mt-auto border border-dashed",
            ds.borderRadius.card,
            "border-slate-300 bg-slate-50/80",
            ds.spacing.normal,
            ds.shadows.sm
          )}>
            <p className={cn(ds.typography.label, ds.textColors.muted)}>
              Phase 1 status
            </p>
            <p className={cn("mt-1", ds.typography.heading3, ds.textColors.primary)}>
              Proposal Tracker live
            </p>
            <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
              Financials, meetings, staff intelligence up next.
            </p>
          </div>
        </aside>
        <main className={cn(
          "flex-1 bg-white/70 p-4 sm:p-6 lg:p-10"
        )}>
          {children}
        </main>
      </div>
    </div>
  );
}
