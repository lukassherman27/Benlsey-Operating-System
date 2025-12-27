"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { PropsWithChildren, useState } from "react";
import {
  Home,
  ListChecks,
  ChevronDown,
  ChevronRight,
  Settings,
  DollarSign,
  Sparkles,
  Calendar,
  Menu,
  Sun,
  Brain,
  Mail,
  Mic,
  LayoutDashboard,
  FolderKanban,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";

type NavItem = {
  href: string;
  label: string;
  icon: React.ElementType;
  disabled?: boolean;
  subItems?: { href: string; label: string; icon: React.ElementType }[];
};

// Simplified navigation - context lives in proposal/project detail pages
// Dec 26, 2025: Merged Transcripts into Meetings page (unified view)
const navItems: NavItem[] = [
  { href: "/my-day", label: "My Day", icon: Sun },
  { href: "/", label: "Overview", icon: Home },
  {
    href: "/tracker",
    label: "Proposals",
    icon: ListChecks,
    subItems: [
      { href: "/tracker", label: "Pipeline Tracker", icon: ListChecks },
      { href: "/overview", label: "Dashboard", icon: LayoutDashboard },
    ]
  },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/team", label: "PM Workload", icon: Users },
  { href: "/meetings", label: "Meetings", icon: Calendar },
  { href: "/finance", label: "Finance", icon: DollarSign },
  {
    href: "/admin",
    label: "Admin",
    icon: Settings,
    subItems: [
      { href: "/emails/review", label: "Email Review", icon: Mail },
      { href: "/admin/suggestions", label: "AI Review", icon: Sparkles },
      { href: "/admin/patterns", label: "Patterns", icon: Brain },
      { href: "/system", label: "System", icon: Settings },
    ]
  },
];

export default function AppShell({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const [expandedItems, setExpandedItems] = useState<string[]>([]);
  const [mobileOpen, setMobileOpen] = useState(false);

  const toggleExpanded = (href: string) => {
    setExpandedItems((prev) =>
      prev.includes(href) ? prev.filter((h) => h !== href) : [...prev, href]
    );
  };

  // Navigation content render function (reused in desktop sidebar and mobile sheet)
  const renderNavContent = (onItemClick?: () => void) => (
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
                onClick={onItemClick}
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
                      onClick={onItemClick}
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
  );

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile Header */}
      <header className="sticky top-0 z-50 flex items-center justify-between border-b border-slate-200 bg-white/95 backdrop-blur px-4 py-3 lg:hidden">
        <div className="flex items-center gap-3">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="shrink-0">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Open menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-72 p-0">
              <SheetHeader className="border-b border-slate-200 p-4">
                <SheetTitle className="flex items-center gap-2">
                  <Image
                    src="/images/bensley-wordmark.svg"
                    alt="Bensley"
                    width={120}
                    height={40}
                    className="h-10 w-auto"
                  />
                </SheetTitle>
              </SheetHeader>
              <div className="p-4 overflow-y-auto max-h-[calc(100vh-80px)]">
                {renderNavContent(() => setMobileOpen(false))}
              </div>
            </SheetContent>
          </Sheet>
          <Image
            src="/images/bensley-wordmark.svg"
            alt="Bensley"
            width={100}
            height={32}
            className="h-8 w-auto"
          />
        </div>
        <span className={cn(ds.typography.caption, ds.textColors.tertiary)}>
          Operations
        </span>
      </header>

      <div className="flex">
        {/* Desktop Sidebar */}
        <aside className={cn(
          "hidden w-72 flex-col border-r border-slate-200 bg-white/95 backdrop-blur lg:flex",
          "sticky top-0 h-screen",
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
          {renderNavContent()}
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
          "flex-1 min-w-0 overflow-x-hidden bg-white/70 p-4 sm:p-6 lg:p-10"
        )}>
          <div className="w-full max-w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
