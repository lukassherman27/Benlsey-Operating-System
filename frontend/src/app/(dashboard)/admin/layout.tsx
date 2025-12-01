"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PropsWithChildren } from "react";
import {
  CheckSquare,
  Link2,
  DollarSign,
  Edit3,
  LayoutDashboard,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

type AdminNavItem = {
  href: string;
  label: string;
  icon: React.ElementType;
  description: string;
};

const adminNavItems: AdminNavItem[] = [
  {
    href: "/admin",
    label: "Overview",
    icon: LayoutDashboard,
    description: "Admin dashboard",
  },
  {
    href: "/admin/validation",
    label: "Data Validation",
    icon: CheckSquare,
    description: "Review AI suggestions",
  },
  {
    href: "/admin/email-links",
    label: "Email Links",
    icon: Link2,
    description: "Manage email connections",
  },
  {
    href: "/admin/financial-entry",
    label: "Financial Entry",
    icon: DollarSign,
    description: "Manual data entry",
  },
  {
    href: "/admin/project-editor",
    label: "Project Editor",
    icon: Edit3,
    description: "Edit project data",
  },
];

export default function AdminLayout({ children }: PropsWithChildren) {
  const pathname = usePathname();

  return (
    <div className="flex gap-6">
      {/* Admin Sidebar */}
      <aside className={cn(
        "w-56 flex-shrink-0 hidden lg:block"
      )}>
        <div className={cn(
          "sticky top-6 rounded-xl border border-slate-200 bg-white",
          ds.shadows.sm,
          "overflow-hidden"
        )}>
          <div className={cn(
            "px-4 py-3 border-b border-slate-100",
            ds.status.info.bg
          )}>
            <h2 className={cn(ds.typography.captionBold, ds.status.info.text)}>
              Admin Tools
            </h2>
          </div>
          <nav className="p-2 space-y-0.5">
            {adminNavItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/admin"
                  ? pathname === "/admin"
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200",
                    isActive
                      ? cn(
                          ds.status.info.bg,
                          ds.status.info.text,
                          "font-medium"
                        )
                      : cn(
                          ds.textColors.secondary,
                          "hover:bg-slate-50"
                        )
                  )}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <span className={cn(ds.typography.body, "truncate")}>
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* Admin Content */}
      <div className="flex-1 min-w-0">
        {children}
      </div>
    </div>
  );
}
