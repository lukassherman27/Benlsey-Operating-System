"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Suggestions page now redirects to the advanced admin suggestions page.
 * Dec 29, 2025: Consolidated duplicate pages. Issue #232.
 */
export default function SuggestionsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/admin/suggestions");
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <p className="text-slate-500">Redirecting to AI Review...</p>
    </div>
  );
}
