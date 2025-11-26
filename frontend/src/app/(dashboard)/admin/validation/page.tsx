"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ValidationSuggestion } from "@/lib/types";
import { Button } from "@/components/ui/button";

export default function ValidationPage() {
  const [statusFilter, setStatusFilter] = useState<string>("pending");
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["validation-suggestions", statusFilter],
    queryFn: () => api.getValidationSuggestions(statusFilter),
  });

  const approveMutation = useMutation({
    mutationFn: (id: number) =>
      api.approveSuggestion(id, {
        reviewed_by: "admin",
        review_notes: "Approved via UI",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["validation-suggestions"] });
    },
  });

  const denyMutation = useMutation({
    mutationFn: ({
      id,
      notes,
    }: {
      id: number;
      notes: string;
    }) =>
      api.denySuggestion(id, {
        reviewed_by: "admin",
        review_notes: notes,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["validation-suggestions"] });
    },
  });

  if (isLoading) return <div className="p-6">Loading...</div>;

  const { suggestions = [], stats } = data || {};

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Data Validation Dashboard</h1>
        <p className="text-gray-600">Review AI-generated data corrections</p>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
          <div className="text-2xl font-bold text-yellow-700">{stats?.pending || 0}</div>
          <div className="text-sm text-yellow-600">Pending</div>
        </div>
        <div className="p-4 bg-green-50 border border-green-200 rounded">
          <div className="text-2xl font-bold text-green-700">{stats?.applied || 0}</div>
          <div className="text-sm text-green-600">Applied</div>
        </div>
        <div className="p-4 bg-blue-50 border border-blue-200 rounded">
          <div className="text-2xl font-bold text-blue-700">{stats?.approved || 0}</div>
          <div className="text-sm text-blue-600">Approved</div>
        </div>
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <div className="text-2xl font-bold text-red-700">{stats?.denied || 0}</div>
          <div className="text-sm text-red-600">Denied</div>
        </div>
      </div>

      {/* Suggestions List */}
      <div className="space-y-4">
        {suggestions.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No {statusFilter} suggestions found
          </div>
        ) : (
          suggestions.map((suggestion: ValidationSuggestion) => (
            <div
              key={suggestion.suggestion_id}
              className="border rounded-lg p-6 bg-white shadow-sm"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-lg font-semibold">
                      {suggestion.project_code}
                    </span>
                    <span className="text-gray-600">•</span>
                    <span className="text-gray-600">{suggestion.entity_name}</span>
                  </div>

                  <div className="mb-4">
                    <div className="text-sm text-gray-600 mb-1">Field: {suggestion.field_name}</div>
                    <div className="flex items-center gap-4">
                      <div>
                        <span className="text-sm text-gray-500">Current: </span>
                        <span className="font-mono text-sm px-2 py-1 bg-red-50 text-red-700 rounded">
                          {suggestion.current_value}
                        </span>
                      </div>
                      <span className="text-gray-400">→</span>
                      <div>
                        <span className="text-sm text-gray-500">Suggested: </span>
                        <span className="font-mono text-sm px-2 py-1 bg-green-50 text-green-700 rounded">
                          {suggestion.suggested_value}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Evidence */}
                  <div className="mb-4 p-4 bg-gray-50 rounded">
                    <div className="text-sm font-semibold mb-1">
                      Evidence ({suggestion.evidence_source}):
                    </div>
                    {suggestion.evidence_email_subject && (
                      <div className="text-sm text-gray-600 mb-1">
                        Subject: {suggestion.evidence_email_subject}
                      </div>
                    )}
                    <div className="text-sm text-gray-700 italic">
                      &quot;{suggestion.evidence_snippet}&quot;
                    </div>
                  </div>

                  {/* AI Reasoning */}
                  <div className="text-sm text-gray-600 mb-2">
                    <span className="font-semibold">AI Reasoning:</span>{" "}
                    {suggestion.reasoning}
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500">Confidence:</span>
                    <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500"
                        style={{
                          width: `${suggestion.confidence_score * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-sm font-semibold">
                      {(suggestion.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Actions */}
                {suggestion.status === "pending" && (
                  <div className="ml-4 flex flex-col gap-2">
                    <Button
                      onClick={() => approveMutation.mutate(suggestion.suggestion_id)}
                      className="bg-green-600 hover:bg-green-700"
                      disabled={approveMutation.isPending}
                    >
                      ✓ Approve
                    </Button>
                    <Button
                      onClick={() => {
                        const notes = prompt("Reason for denial:");
                        if (notes) {
                          denyMutation.mutate({
                            id: suggestion.suggestion_id,
                            notes,
                          });
                        }
                      }}
                      variant="outline"
                      className="border-red-600 text-red-600 hover:bg-red-50"
                      disabled={denyMutation.isPending}
                    >
                      ✗ Deny
                    </Button>
                  </div>
                )}
              </div>

              {/* Status Badge */}
              <div className="mt-4 flex items-center gap-2">
                <span
                  className={`text-xs px-2 py-1 rounded ${
                    suggestion.status === "pending"
                      ? "bg-yellow-100 text-yellow-700"
                      : suggestion.status === "applied"
                      ? "bg-green-100 text-green-700"
                      : suggestion.status === "approved"
                      ? "bg-blue-100 text-blue-700"
                      : "bg-red-100 text-red-700"
                  }`}
                >
                  {suggestion.status.toUpperCase()}
                </span>
                {suggestion.reviewed_by && (
                  <span className="text-xs text-gray-500">
                    Reviewed by {suggestion.reviewed_by} on{" "}
                    {new Date(suggestion.reviewed_at!).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
