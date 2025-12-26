"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Transcripts page now redirects to unified Meetings & Recordings page.
 * All meeting recordings and transcripts are now shown together on /meetings.
 */
export default function TranscriptsPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to meetings page with recordings filter
    router.replace("/meetings");
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <p className="text-slate-500">Redirecting to Meetings & Recordings...</p>
    </div>
  );
}
