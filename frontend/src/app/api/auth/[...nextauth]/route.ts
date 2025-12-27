/**
 * NextAuth.js Route Handler
 *
 * Handles all /api/auth/* routes (signIn, signOut, session, etc.)
 */

import { handlers } from "@/lib/auth";

export const { GET, POST } = handlers;
