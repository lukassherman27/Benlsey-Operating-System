/**
 * NextAuth.js Middleware with Role-Based Access Control
 *
 * Protects routes by:
 * 1. Redirecting unauthenticated users to login
 * 2. Restricting admin routes to admin/executive roles
 * 3. Restricting finance routes to finance/executive roles
 */

import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";

// Route protection configuration
const ROUTE_PROTECTION = {
  // Admin routes - require admin or executive role
  admin: {
    paths: ["/admin"],
    allowedRoles: ["admin", "executive"],
  },
  // Finance routes - require finance or executive role
  finance: {
    paths: ["/finance"],
    allowedRoles: ["finance", "executive"],
  },
};

// Map user attributes to RBAC role (mirrors backend logic)
function getUserRole(user: {
  department?: string;
  seniority?: string;
  is_pm?: boolean;
}): string {
  const department = user.department || "";
  const seniority = user.seniority || "";
  const isPm = user.is_pm;

  // Executive: Leadership + Owner/Principal
  if (department === "Leadership" && ["Owner", "Principal"].includes(seniority)) {
    return "executive";
  }
  // Admin: Leadership Director or Operations/Admin department
  if (department === "Leadership" && seniority === "Director") {
    return "admin";
  }
  if (["Operations", "Admin"].includes(department)) {
    return "admin";
  }
  // Finance: Finance department
  if (department === "Finance") {
    return "finance";
  }
  // PM: is_pm flag
  if (isPm) {
    return "pm";
  }
  // Default: staff
  return "staff";
}

// Check if user has any of the allowed roles
function hasAllowedRole(userRole: string, allowedRoles: string[]): boolean {
  // Executive has access to everything
  if (userRole === "executive") return true;
  // Admin has access to admin and finance routes
  if (userRole === "admin" && allowedRoles.some(r => ["admin", "finance"].includes(r))) {
    return true;
  }
  return allowedRoles.includes(userRole);
}

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const pathname = req.nextUrl.pathname;
  const isOnLoginPage = pathname === "/login";

  // If not logged in and not on login page, redirect to login
  if (!isLoggedIn && !isOnLoginPage) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  // If logged in and on login page, redirect to dashboard
  if (isLoggedIn && isOnLoginPage) {
    return NextResponse.redirect(new URL("/", req.url));
  }

  // Role-based route protection
  if (isLoggedIn && req.auth?.user) {
    const user = req.auth.user as {
      department?: string;
      seniority?: string;
      is_pm?: boolean;
    };
    const userRole = getUserRole(user);

    // Check each protected route group
    for (const [, config] of Object.entries(ROUTE_PROTECTION)) {
      const isProtectedPath = config.paths.some(path => pathname.startsWith(path));

      if (isProtectedPath && !hasAllowedRole(userRole, config.allowedRoles)) {
        // User doesn't have required role - redirect to dashboard with error
        const url = new URL("/", req.url);
        url.searchParams.set("error", "access_denied");
        url.searchParams.set("message", "You don't have permission to access this page");
        return NextResponse.redirect(url);
      }
    }
  }

  return NextResponse.next();
});

// Apply middleware to all routes except static files and API routes
export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
