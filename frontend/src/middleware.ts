/**
 * NextAuth.js Middleware (DISABLED)
 *
 * Authentication middleware is temporarily disabled until:
 * 1. All staff users have passwords set
 * 2. Auth flow is fully tested
 *
 * Once ready, replace this with the protected version.
 *
 * Issue #185 - Auth system not fully configured
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(_request: NextRequest) {
  // Allow all requests through without auth check
  return NextResponse.next();
}

// Minimal matcher to avoid unnecessary overhead
export const config = {
  matcher: [
    /*
     * Match only specific paths that would need auth later:
     * - Protected API routes (if any)
     * - Dashboard routes
     * Exclude: static files, images, public routes
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
