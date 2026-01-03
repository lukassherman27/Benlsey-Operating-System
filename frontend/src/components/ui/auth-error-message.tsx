"use client";

import { LogIn, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useRouter } from "next/navigation";
import { AuthError } from "@/lib/api";

interface AuthErrorMessageProps {
  error?: Error | null;
  className?: string;
}

/**
 * Displays a friendly sign-in prompt when an AuthError is detected.
 * Can be used in error states of components that fetch authenticated data.
 *
 * Usage:
 *   if (error instanceof AuthError) {
 *     return <AuthErrorMessage error={error} />;
 *   }
 */
export function AuthErrorMessage({ error, className }: AuthErrorMessageProps) {
  const router = useRouter();
  const isAuthError = error instanceof AuthError || error?.message?.includes("sign in");

  if (!isAuthError) {
    return (
      <Card className={className}>
        <CardContent className="py-12 text-center">
          <AlertCircle className="h-12 w-12 mx-auto mb-4 text-red-400" />
          <p className="text-lg font-medium text-red-700 mb-2">Something went wrong</p>
          <p className="text-sm text-red-600">{error?.message || "An unexpected error occurred"}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardContent className="py-12 text-center">
        <LogIn className="h-12 w-12 mx-auto mb-4 text-slate-400" />
        <p className="text-lg font-medium text-slate-700 mb-2">Sign in required</p>
        <p className="text-sm text-slate-500 mb-6">Please sign in to view this content</p>
        <Button onClick={() => router.push("/login")} className="gap-2">
          <LogIn className="h-4 w-4" />
          Sign In
        </Button>
      </CardContent>
    </Card>
  );
}

/**
 * Helper function to check if an error is an authentication error.
 */
export function isAuthError(error: unknown): error is AuthError {
  return error instanceof AuthError ||
    (error instanceof Error && error.message?.toLowerCase().includes("sign in"));
}
