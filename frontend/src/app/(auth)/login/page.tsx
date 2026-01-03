"use client";

/**
 * Login Page
 *
 * Simple email/password login form.
 */

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await signIn("credentials", {
        email,
        password,
        redirect: false,
      });

      if (result?.error) {
        setError("Invalid email or password");
      } else {
        router.push("/");
        router.refresh();
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-amber-50 via-stone-50 to-emerald-50">
      <div className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-amber-200/40 blur-3xl" />
      <div className="pointer-events-none absolute -right-20 top-12 h-80 w-80 rounded-full bg-emerald-200/40 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 left-1/3 h-64 w-64 -translate-x-1/2 rounded-full bg-slate-200/40 blur-3xl" />

      <div className="relative mx-auto flex min-h-screen max-w-6xl flex-col gap-10 px-6 py-12 lg:flex-row lg:items-center lg:gap-16">
        <div className="flex-1 space-y-6">
          <p className="text-xs uppercase tracking-[0.4em] text-slate-500">
            Bensley Design Studios
          </p>
          <h1 className="text-4xl font-semibold text-slate-900 sm:text-5xl lg:text-6xl font-serif">
            The Bensley Operating System
          </h1>
          <p className="max-w-xl text-base text-slate-600">
            A living workspace for proposals, projects, and revenue — tuned to the way your studio actually runs.
          </p>

          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { label: "Pipeline clarity", value: "Win work faster" },
              { label: "Project pulse", value: "Every phase, visible" },
              { label: "Finance signal", value: "Cash flow, live" },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-2xl border border-slate-200/70 bg-white/80 p-4 shadow-sm backdrop-blur"
              >
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
                  {item.label}
                </p>
                <p className="mt-2 text-sm font-medium text-slate-800">
                  {item.value}
                </p>
              </div>
            ))}
          </div>
        </div>

        <Card className="w-full max-w-md border-slate-200/70 bg-white/90 shadow-xl backdrop-blur">
          <CardHeader className="space-y-2">
            <CardTitle className="text-2xl font-semibold text-slate-900">
              Sign in
            </CardTitle>
            <CardDescription>
              Use your studio credentials to continue.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@bensley.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className="bg-slate-50/80"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="bg-slate-50/80"
                />
              </div>
              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}
              <Button
                type="submit"
                className="w-full bg-slate-900 text-white hover:bg-slate-800"
                disabled={loading}
              >
                {loading ? "Signing in..." : "Sign in"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
