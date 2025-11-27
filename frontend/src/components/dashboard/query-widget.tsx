"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Clock, TrendingUp, Loader2, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { toast } from "sonner";

interface QueryHistoryItem {
  query: string;
  timestamp: string;
  resultCount?: number;
}

interface QueryWidgetProps {
  compact?: boolean;
}

export function QueryWidget({ compact = true }: QueryWidgetProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);

  // Load query history from localStorage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem("queryHistory");
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error("Failed to load query history:", e);
      }
    }
  }, []);

  // Save query to history
  const saveToHistory = (queryText: string, resultCount?: number) => {
    const newItem: QueryHistoryItem = {
      query: queryText,
      timestamp: new Date().toISOString(),
      resultCount,
    };

    // Add to history (max 10 items)
    const updatedHistory = [newItem, ...history.filter((item) => item.query !== queryText)].slice(0, 10);
    setHistory(updatedHistory);
    localStorage.setItem("queryHistory", JSON.stringify(updatedHistory));
  };

  // Execute query
  const executeQuery = async (queryText?: string) => {
    const queryToExecute = queryText || query;
    if (!queryToExecute.trim()) {
      toast.error("Please enter a query");
      return;
    }

    setLoading(true);
    try {
      const response = await api.executeQuery(queryToExecute);

      if (response.success) {
        // Save to history
        saveToHistory(queryToExecute, response.count);

        // Navigate to full query page with results
        sessionStorage.setItem("queryResult", JSON.stringify(response));
        router.push("/query");
        toast.success(`Found ${response.count} result${response.count !== 1 ? "s" : ""}`);
      } else {
        toast.error(response.error || "Query failed");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to execute query");
    } finally {
      setLoading(false);
    }
  };

  // Handle key press
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !loading) {
      executeQuery();
    }
  };

  // Compact mode for dashboard
  if (compact) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="h-5 w-5 text-blue-600" />
            Quick Query
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search Input */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about projects, proposals, invoices..."
                className="pl-10"
                disabled={loading}
                aria-label="Quick query input"
              />
            </div>
            <Button
              onClick={() => executeQuery()}
              disabled={loading || !query.trim()}
              size="icon"
              aria-label="Execute query"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Recent Queries */}
          {history.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Clock className="h-3.5 w-3.5 text-gray-500" />
                <p className="text-xs font-medium text-gray-600">Recent Queries</p>
              </div>
              <div className="space-y-1">
                {history.slice(0, 5).map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => executeQuery(item.query)}
                    className={cn(
                      "w-full text-left px-3 py-2 rounded-md text-xs",
                      "bg-gray-50 hover:bg-gray-100 transition-colors",
                      "border border-gray-200 hover:border-gray-300",
                      "flex items-center justify-between gap-2"
                    )}
                    disabled={loading}
                  >
                    <span className="truncate text-gray-700">{item.query}</span>
                    {item.resultCount !== undefined && (
                      <span className="text-[10px] text-gray-500 flex-shrink-0">
                        {item.resultCount} results
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Popular Queries */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-3.5 w-3.5 text-blue-500" />
              <p className="text-xs font-medium text-gray-600">Popular</p>
            </div>
            <div className="space-y-1">
              {[
                "Show me all active projects",
                "Outstanding invoices over 90 days",
                "Proposals sent this month",
                "Projects in Thailand",
              ].map((popularQuery, idx) => (
                <button
                  key={idx}
                  onClick={() => executeQuery(popularQuery)}
                  className={cn(
                    "w-full text-left px-3 py-2 rounded-md text-xs",
                    "bg-blue-50 hover:bg-blue-100 transition-colors",
                    "border border-blue-200 hover:border-blue-300",
                    "text-blue-700"
                  )}
                  disabled={loading}
                >
                  {popularQuery}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Full mode (not used in dashboard, but available)
  return (
    <Card>
      <CardHeader>
        <CardTitle>Query Intelligence</CardTitle>
      </CardHeader>
      <CardContent>
        <p>Use the full query interface at /query for detailed results</p>
      </CardContent>
    </Card>
  );
}
