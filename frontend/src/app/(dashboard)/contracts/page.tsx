// DEPRECATED: Contracts page has been merged into Projects page
// This file redirects to /projects
// See git history for previous Contracts page implementation
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ContractsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/projects");
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <p className="text-slate-500">Redirecting to Projects...</p>
    </div>
  );
}
