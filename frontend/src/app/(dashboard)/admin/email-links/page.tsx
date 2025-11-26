"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { EmailLink } from "@/lib/types";
import { Button } from "@/components/ui/button";

export default function EmailLinksPage() {
  const [projectCodeFilter, setProjectCodeFilter] = useState<string>("");
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["email-links", projectCodeFilter],
    queryFn: () => api.getEmailLinks(projectCodeFilter || undefined),
  });

  const unlinkMutation = useMutation({
    mutationFn: (linkId: number) => api.unlinkEmail(linkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["email-links"] });
    },
  });

  if (isLoading) return <div className="p-6">Loading...</div>;

  const { links = [], total = 0 } = data || {};

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Email-Proposal Links Manager</h1>
        <p className="text-gray-600">
          Manage email-to-proposal links with confidence scores
        </p>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-blue-50 border border-blue-200 rounded">
          <div className="text-2xl font-bold text-blue-700">{total}</div>
          <div className="text-sm text-blue-600">Total Links</div>
        </div>
        <div className="p-4 bg-green-50 border border-green-200 rounded">
          <div className="text-2xl font-bold text-green-700">
            {links.filter((l: EmailLink) => l.link_type === "auto").length}
          </div>
          <div className="text-sm text-green-600">Auto-Linked</div>
        </div>
        <div className="p-4 bg-purple-50 border border-purple-200 rounded">
          <div className="text-2xl font-bold text-purple-700">
            {links.filter((l: EmailLink) => l.link_type === "manual").length}
          </div>
          <div className="text-sm text-purple-600">Manual Links</div>
        </div>
      </div>

      {/* Filter */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Filter by project code (e.g., BK-033)"
          value={projectCodeFilter}
          onChange={(e) => setProjectCodeFilter(e.target.value)}
          className="px-4 py-2 border rounded w-full max-w-md"
        />
      </div>

      {/* Links List */}
      <div className="space-y-4">
        {links.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No email links found
            {projectCodeFilter && " for this project code"}
          </div>
        ) : (
          links.map((link: EmailLink) => (
            <div
              key={link.link_id}
              className="border rounded-lg p-6 bg-white shadow-sm"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Header */}
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-lg font-semibold">
                      {link.project_code}
                    </span>
                    <span className="text-gray-600">•</span>
                    <span className="text-gray-600">{link.project_name}</span>
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        link.link_type === "auto"
                          ? "bg-green-100 text-green-700"
                          : "bg-purple-100 text-purple-700"
                      }`}
                    >
                      {link.link_type.toUpperCase()}
                    </span>
                  </div>

                  {/* Email Info */}
                  <div className="mb-4 p-4 bg-gray-50 rounded">
                    <div className="text-sm font-semibold mb-1">
                      Email #{link.email_id}
                    </div>
                    <div className="text-sm text-gray-700 mb-1">
                      <span className="font-medium">Subject:</span>{" "}
                      {link.subject}
                    </div>
                    <div className="text-sm text-gray-600 mb-1">
                      <span className="font-medium">From:</span>{" "}
                      {link.sender_email}
                    </div>
                    <div className="text-sm text-gray-600 mb-1">
                      <span className="font-medium">Date:</span>{" "}
                      {new Date(link.email_date).toLocaleDateString()}
                    </div>
                    {link.category && (
                      <div className="text-sm text-gray-600">
                        <span className="font-medium">Category:</span>{" "}
                        {link.category}
                      </div>
                    )}
                    {link.snippet && (
                      <div className="text-sm text-gray-700 italic mt-2">
                        &quot;{link.snippet.substring(0, 200)}...&quot;
                      </div>
                    )}
                  </div>

                  {/* Link Metadata */}
                  <div className="flex items-center gap-4 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">Confidence:</span>
                      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500"
                          style={{
                            width: `${(link.confidence_score || 0) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="text-sm font-semibold">
                        {((link.confidence_score || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {link.match_reasons && (
                    <div className="text-sm text-gray-600">
                      <span className="font-semibold">Match Reasons:</span>{" "}
                      {link.match_reasons}
                    </div>
                  )}

                  <div className="text-xs text-gray-500 mt-2">
                    Linked on {new Date(link.created_at).toLocaleString()}
                  </div>
                </div>

                {/* Actions */}
                <div className="ml-4">
                  <Button
                    onClick={() => {
                      if (
                        confirm(
                          `Are you sure you want to unlink this email from ${link.project_code}?`
                        )
                      ) {
                        unlinkMutation.mutate(link.link_id);
                      }
                    }}
                    variant="outline"
                    className="border-red-600 text-red-600 hover:bg-red-50"
                    disabled={unlinkMutation.isPending}
                  >
                    Unlink
                  </Button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Summary Footer */}
      {links.length > 0 && (
        <div className="mt-6 text-sm text-gray-600 text-center">
          Showing {links.length} of {total} total email links
          {projectCodeFilter && ` for project code "${projectCodeFilter}"`}
        </div>
      )}
    </div>
  );
}
