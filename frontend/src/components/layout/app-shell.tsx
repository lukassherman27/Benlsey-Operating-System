"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { PropsWithChildren } from "react";
import {
  BarChart3,
  FileText,
  Home,
  ListChecks,
  Mail,
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Overview", icon: Home },
  { href: "/proposals", label: "Proposals", icon: ListChecks },
  { href: "/emails", label: "Emails", icon: Mail },
  { href: "/documents", label: "Documents", icon: FileText, disabled: true },
  { href: "/analytics", label: "Analytics", icon: BarChart3, disabled: true },
  { href: "/query", label: "Query Brain", icon: Search, disabled: true },
];

export default function AppShell({ children }: PropsWithChildren) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-muted/30">
      <div className="flex">
        <aside className="hidden w-72 flex-col border-r bg-sidebar/80 p-6 backdrop-blur lg:flex">
          <div className="mb-10 flex items-center gap-3">
            <Image
              src="/images/bensley-wordmark.svg"
              alt="Bensley Design Studios"
              width={140}
              height={48}
              priority
              className="h-12 w-auto"
            />
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-disabled={item.disabled}
                  className={cn(
                    "flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition",
                    item.disabled && "pointer-events-none opacity-40",
                    isActive
                      ? "bg-primary/15 text-primary shadow-sm"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                  {item.disabled && (
                    <span className="ml-auto rounded bg-secondary px-2 py-0.5 text-xs">
                      Soon
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
          <div className="mt-auto rounded-2xl border border-dashed border-muted bg-background/80 p-4 text-sm shadow-sm">
            <p className="text-xs uppercase text-muted-foreground">
              Phase 1 status
            </p>
            <p className="mt-1 text-base font-semibold text-foreground">
              Proposal Tracker live
            </p>
            <p className="text-xs text-muted-foreground">
              Financials, meetings, staff intelligence up next.
            </p>
          </div>
        </aside>
        <main className="flex-1 bg-background/70 p-4 sm:p-6 lg:p-10">
          {children}
        </main>
      </div>
    </div>
  );
}
