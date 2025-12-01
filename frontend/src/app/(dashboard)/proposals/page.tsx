"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Redirect /proposals to /tracker
 * The proposal tracker lives at /tracker, but some links point to /proposals
 * This page ensures those links don't 404
 */
export default function ProposalsRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/tracker");
  }, [router]);

  return (
    <div className="flex items-center justify-center h-64">
      <p className="text-slate-500">Redirecting to Proposal Tracker...</p>
    </div>
  );
}
