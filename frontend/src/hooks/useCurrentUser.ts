"use client";

import { useSession } from "next-auth/react";

/**
 * Hook to get the current authenticated user's info
 * Returns consistent user data from the session
 */
export function useCurrentUser() {
  const { data: session, status } = useSession();

  const user = session?.user;

  return {
    // Core user info
    name: user?.name || "User",
    email: user?.email || "",
    role: user?.role || "",
    staffId: user?.staffId || "",
    department: user?.department || "",
    office: user?.office || "",

    // Auth state
    isAuthenticated: status === "authenticated",
    isLoading: status === "loading",

    // Full session for advanced use
    session,
  };
}

/**
 * Get first name from full name
 */
export function getFirstName(name: string | undefined | null): string {
  if (!name) return "User";
  return name.split(" ")[0];
}
