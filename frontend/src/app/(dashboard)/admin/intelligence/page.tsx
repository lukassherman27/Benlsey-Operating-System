"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AISuggestion } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function AIIntelligencePage() {
  const [typeFilter, setTypeFilter] = useState<string>("");
  const queryClient = useQueryClient();

  // Fetch learning stats
  const { data: statsData } = useQuery({
    queryKey: ["learning-stats"],
    queryFn: () => api.getLearningStats(),
  });

  // Fetch pending suggestions
  const { data: suggestionsData, isLoading } = useQuery({
    queryKey: ["learning-suggestions", typeFilter],
    queryFn: () => api.getLearningPendingSuggestions(typeFilter || undefined),
  });

  // Fetch learned patterns
  const { data: patternsData } = useQuery({
    queryKey: ["learning-patterns"],
    queryFn: () => api.getLearningPatterns(),
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (suggestionId: number) =>
      api.approveLearning(suggestionId, "admin", true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["learning-suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["learning-stats"] });
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      api.rejectLearning(id, "admin", reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["learning-suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["learning-stats"] });
    },
  });

  // Generate rules mutation
  const generateRulesMutation = useMutation({
    mutationFn: () => api.generateRules(3),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["learning-patterns"] });
      queryClient.invalidateQueries({ queryKey: ["learning-stats"] });
    },
  });

  const stats = statsData;
  const suggestions = suggestionsData?.suggestions || [];
  const patterns = patternsData?.patterns || [];

  const suggestionTypes = [
    { value: "", label: "All Types" },
    { value: "follow_up_needed", label: "Follow-up Needed" },
    { value: "new_contact", label: "New Contact" },
    { value: "fee_change", label: "Fee Change" },
    { value: "deadline_detected", label: "Deadline" },
    { value: "status_change", label: "Status Change" },
    { value: "action_item", label: "Action Item" },
  ];

  const priorityColors: Record<string, string> = {
    critical: "bg-red-100 text-red-700 border-red-300",
    high: "bg-orange-100 text-orange-700 border-orange-300",
    medium: "bg-yellow-100 text-yellow-700 border-yellow-300",
    low: "bg-gray-100 text-gray-700 border-gray-300",
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">AI Intelligence Dashboard</h1>
        <p className="text-gray-600">
          Review AI suggestions and manage learned patterns
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
          <div className="text-2xl font-bold text-yellow-700">
            {stats?.suggestions?.pending || 0}
          </div>
          <div className="text-sm text-yellow-600">Pending Review</div>
        </div>
        <div className="p-4 bg-green-50 border border-green-200 rounded">
          <div className="text-2xl font-bold text-green-700">
            {(stats?.suggestions?.approved || 0) +
              (stats?.suggestions?.modified || 0)}
          </div>
          <div className="text-sm text-green-600">Approved</div>
        </div>
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <div className="text-2xl font-bold text-red-700">
            {stats?.suggestions?.rejected || 0}
          </div>
          <div className="text-sm text-red-600">Rejected</div>
        </div>
        <div className="p-4 bg-blue-50 border border-blue-200 rounded">
          <div className="text-2xl font-bold text-blue-700">
            {stats?.active_patterns || 0}
          </div>
          <div className="text-sm text-blue-600">Active Patterns</div>
        </div>
        <div className="p-4 bg-purple-50 border border-purple-200 rounded">
          <div className="text-2xl font-bold text-purple-700">
            {stats?.approval_rate
              ? `${(stats.approval_rate * 100).toFixed(0)}%`
              : "N/A"}
          </div>
          <div className="text-sm text-purple-600">Approval Rate</div>
        </div>
      </div>

      {/* Two column layout */}
      <div className="grid grid-cols-3 gap-6">
        {/* Suggestions Column */}
        <div className="col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Pending Suggestions</h2>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="border rounded px-3 py-1 text-sm"
            >
              {suggestionTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {isLoading ? (
            <div className="text-center py-8 text-gray-500">Loading...</div>
          ) : suggestions.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded border">
              <div className="text-gray-500">No pending suggestions</div>
              <div className="text-sm text-gray-400 mt-1">
                Suggestions are generated from email processing
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {suggestions.map((suggestion: AISuggestion) => (
                <div
                  key={suggestion.suggestion_id}
                  className="border rounded-lg p-4 bg-white shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Header */}
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className={`text-xs px-2 py-1 rounded border ${
                            priorityColors[suggestion.priority] || priorityColors.medium
                          }`}
                        >
                          {suggestion.priority.toUpperCase()}
                        </span>
                        <span className="text-xs px-2 py-1 bg-gray-100 rounded">
                          {suggestion.suggestion_type.replace(/_/g, " ")}
                        </span>
                        {suggestion.project_code && (
                          <span className="text-xs text-gray-500">
                            {suggestion.project_code}
                          </span>
                        )}
                      </div>

                      {/* Title & Description */}
                      <h3 className="font-semibold mb-1">{suggestion.title}</h3>
                      {suggestion.description && (
                        <p className="text-sm text-gray-600 mb-2">
                          {suggestion.description}
                        </p>
                      )}

                      {/* Source */}
                      <div className="text-xs text-gray-500 mb-2">
                        Source: {suggestion.source_reference}
                      </div>

                      {/* Confidence */}
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500">Confidence:</span>
                        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500"
                            style={{
                              width: `${suggestion.confidence_score * 100}%`,
                            }}
                          />
                        </div>
                        <span className="text-xs font-medium">
                          {(suggestion.confidence_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="ml-4 flex flex-col gap-2">
                      <Button
                        onClick={() =>
                          approveMutation.mutate(suggestion.suggestion_id)
                        }
                        className="bg-green-600 hover:bg-green-700 text-sm"
                        disabled={approveMutation.isPending}
                      >
                        Approve
                      </Button>
                      <Button
                        onClick={() => {
                          const reason = prompt("Reason for rejection:");
                          if (reason) {
                            rejectMutation.mutate({
                              id: suggestion.suggestion_id,
                              reason,
                            });
                          }
                        }}
                        variant="outline"
                        className="border-red-600 text-red-600 hover:bg-red-50 text-sm"
                        disabled={rejectMutation.isPending}
                      >
                        Reject
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Patterns Column */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Learned Patterns</h2>
            <Button
              onClick={() => generateRulesMutation.mutate()}
              disabled={generateRulesMutation.isPending}
              className="text-sm"
              variant="outline"
            >
              {generateRulesMutation.isPending
                ? "Generating..."
                : "Generate Rules"}
            </Button>
          </div>

          {patterns.length === 0 ? (
            <div className="text-center py-8 bg-gray-50 rounded border">
              <div className="text-gray-500">No patterns learned yet</div>
              <div className="text-sm text-gray-400 mt-1">
                Patterns are created from feedback
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {patterns.map((pattern) => (
                <div
                  key={pattern.pattern_id}
                  className="border rounded p-3 bg-white shadow-sm"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-sm">
                      {pattern.pattern_name}
                    </span>
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded ${
                        pattern.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {pattern.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    Type: {pattern.pattern_type}
                  </div>
                  <div className="flex items-center gap-4 mt-2 text-xs">
                    <span>
                      Confidence:{" "}
                      <strong>
                        {(pattern.confidence_score * 100).toFixed(0)}%
                      </strong>
                    </span>
                    <span>Evidence: {pattern.evidence_count}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Quick Actions */}
          <div className="mt-6 p-4 bg-gray-50 rounded border">
            <h3 className="text-sm font-semibold mb-3">Quick Actions</h3>
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full text-sm justify-start"
                onClick={() =>
                  window.open("/api/agent/follow-up/summary", "_blank")
                }
              >
                View Follow-up Summary
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
