/**
 * RBAC Hook - Role-Based Access Control utilities for frontend
 *
 * Provides helpers to check user permissions and conditionally render components.
 */

import { useSession } from "next-auth/react";

// RBAC role hierarchy (mirrors backend)
export type RBACRole = "executive" | "admin" | "finance" | "pm" | "staff";

/**
 * Compute RBAC role from user session data.
 * Mirrors backend logic in api/dependencies.py
 */
export function getUserRole(user: {
  department?: string;
  seniority?: string;
  is_pm?: boolean;
}): RBACRole {
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

/**
 * Check if user has any of the required roles.
 */
export function hasRole(userRole: RBACRole, requiredRoles: RBACRole[]): boolean {
  // Executive has all permissions
  if (userRole === "executive") return true;

  // Admin has admin and finance permissions
  if (userRole === "admin" && requiredRoles.some(r => ["admin", "finance"].includes(r))) {
    return true;
  }

  return requiredRoles.includes(userRole);
}

/**
 * Hook to get RBAC utilities for the current user.
 */
export function useRBAC() {
  const { data: session, status } = useSession();

  const userRole: RBACRole = session?.user
    ? getUserRole({
        department: session.user.department,
        seniority: session.user.seniority,
        is_pm: session.user.is_pm,
      })
    : "staff";

  return {
    isLoading: status === "loading",
    isAuthenticated: status === "authenticated",
    userRole,

    // Permission checks
    isExecutive: userRole === "executive",
    isAdmin: hasRole(userRole, ["admin"]),
    isFinance: hasRole(userRole, ["finance"]),
    isPM: userRole === "pm",
    isStaff: userRole === "staff",

    // Can view financial data
    canViewFinancials: hasRole(userRole, ["executive", "finance"]),

    // Can access admin functions
    canAccessAdmin: hasRole(userRole, ["admin"]),

    // Generic role check
    hasRole: (roles: RBACRole[]) => hasRole(userRole, roles),
  };
}

/**
 * Component wrapper that only renders children if user has required role.
 */
export function RoleGuard({
  children,
  roles,
  fallback = null,
}: {
  children: React.ReactNode;
  roles: RBACRole[];
  fallback?: React.ReactNode;
}) {
  const { hasRole: checkRole, isLoading } = useRBAC();

  if (isLoading) return null;
  if (!checkRole(roles)) return <>{fallback}</>;
  return <>{children}</>;
}
