/**
 * NextAuth.js Type Extensions
 *
 * Extends the default NextAuth types to include custom user properties.
 */

import { DefaultSession, DefaultUser } from "next-auth";
import { DefaultJWT } from "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    accessToken: string;
    user: {
      role?: string;
      staffId?: string;
      department?: string;
      office?: string;
      seniority?: string;
      is_pm?: boolean;
    } & DefaultSession["user"];
  }

  interface User extends DefaultUser {
    accessToken?: string;
    role?: string;
    department?: string;
    office?: string;
    seniority?: string;
    is_pm?: boolean;
  }
}

declare module "next-auth/jwt" {
  interface JWT extends DefaultJWT {
    accessToken?: string;
    role?: string;
    staffId?: string;
    department?: string;
    office?: string;
    seniority?: string;
    is_pm?: boolean;
  }
}
