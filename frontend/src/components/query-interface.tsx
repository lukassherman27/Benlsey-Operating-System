"use client";

import { useState, useEffect, useRef } from "react";
import { Search, Loader2, Database, AlertCircle, Trash2, Download, MessageSquare, User, Bot } from "lucide-react";
import { api } from "@/lib/api";
import type { QueryResponse } from "@/lib/types";

interface QueryHistoryItem {
  query: string;
  timestamp: string;
  resultCount?: number;
}

// Chat message interface for conversation history
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  query?: string;  // Original query text for user messages
  results?: Record<string, unknown>[];  // Query results for assistant messages
  sql?: string;  // SQL query if applicable
  summary?: string;  // AI summary
  error?: string;  // Error message if query failed
}

export default function QueryInterface() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Chat history state
  const [conversation, setConversation] = useState<ChatMessage[]>([]);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const exampleQueries = [
    "What's the status on BK-070?",
    "Show me all active projects",
    "What are the fees for Tel Aviv project?",
    "Which projects need follow up?",
    "What's the last invoice for Wynn project?",
    "Show overdue payments",
    "List projects with no contact in 30 days",
    "What's the total contract value?",
  ];

  // Load conversation from localStorage on mount
  useEffect(() => {
    const savedConversation = localStorage.getItem("queryConversation");
    if (savedConversation) {
      try {
        const parsed = JSON.parse(savedConversation);
        // Convert timestamp strings back to Date objects
        const restored = parsed.map((msg: ChatMessage) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        setConversation(restored);
      } catch (e) {
        console.error("Failed to load conversation:", e);
      }
    }

    // Also load any widget result
    const savedResult = sessionStorage.getItem("queryResult");
    if (savedResult) {
      try {
        const parsed = JSON.parse(savedResult);
        setResults(parsed);
        sessionStorage.removeItem("queryResult");
      } catch (e) {
        console.error("Failed to load query result:", e);
      }
    }
  }, []);

  // Save conversation to localStorage when it changes
  useEffect(() => {
    if (conversation.length > 0) {
      localStorage.setItem("queryConversation", JSON.stringify(conversation));
    }
  }, [conversation]);

  // Scroll to bottom of chat when new messages are added
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [conversation]);

  // Save query to history
  const saveToHistory = (queryText: string, resultCount?: number) => {
    try {
      const savedHistory = localStorage.getItem("queryHistory");
      const history: QueryHistoryItem[] = savedHistory ? JSON.parse(savedHistory) : [];

      const newItem: QueryHistoryItem = {
        query: queryText,
        timestamp: new Date().toISOString(),
        resultCount,
      };

      // Add to history (max 10 items), remove duplicates
      const updatedHistory = [newItem, ...history.filter((item) => item.query !== queryText)].slice(0, 10);
      localStorage.setItem("queryHistory", JSON.stringify(updatedHistory));
    } catch (e) {
      console.error("Failed to save query history:", e);
    }
  };

  // Generate unique ID for messages
  const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;

  // Clear conversation history
  const clearConversation = () => {
    setConversation([]);
    setResults(null);
    setError(null);
    localStorage.removeItem("queryConversation");
  };

  // Export conversation to JSON
  const exportConversation = () => {
    const exportData = {
      exportedAt: new Date().toISOString(),
      messageCount: conversation.length,
      messages: conversation.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp.toISOString(),
        results: msg.results,
        sql: msg.sql,
        summary: msg.summary
      }))
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bensley-query-conversation-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Format conversation history for context
  const getConversationContext = () => {
    // Get last 5 messages for context
    return conversation.slice(-5).map(msg => ({
      role: msg.role,
      content: msg.content,
      results_count: msg.results?.length,
      sql: msg.sql
    }));
  };

  const executeQuery = async () => {
    if (!query.trim()) return;

    // Add user message to conversation
    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: query,
      timestamp: new Date(),
      query: query
    };
    setConversation(prev => [...prev, userMessage]);

    setLoading(true);
    setError(null);
    setResults(null);

    const currentQuery = query;
    setQuery(""); // Clear input immediately for better UX

    try {
      // Use the context-aware query endpoint if conversation exists
      const conversationContext = getConversationContext();
      const data = await api.executeQueryWithContext(currentQuery, conversationContext);

      if (data.success) {
        setResults(data);
        saveToHistory(currentQuery, data.count);

        // Add assistant message with results
        const assistantMessage: ChatMessage = {
          id: generateId(),
          role: 'assistant',
          content: data.summary || `Found ${data.count} result${data.count !== 1 ? 's' : ''}`,
          timestamp: new Date(),
          results: data.results,
          sql: data.sql,
          summary: data.summary
        };
        setConversation(prev => [...prev, assistantMessage]);
      } else {
        const errorMsg = data.error || "Query failed";
        setError(errorMsg);

        // Add error message to conversation
        const errorMessage: ChatMessage = {
          id: generateId(),
          role: 'assistant',
          content: `Sorry, I couldn't process that query: ${errorMsg}`,
          timestamp: new Date(),
          error: errorMsg
        };
        setConversation(prev => [...prev, errorMessage]);
      }
    } catch (err) {
      const errorMsg = err instanceof Error
        ? `Failed to execute query: ${err.message}`
        : "Failed to execute query. Please check if the backend is running.";
      setError(errorMsg);

      // Add error to conversation
      const errorMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: `Sorry, something went wrong: ${errorMsg}`,
        timestamp: new Date(),
        error: errorMsg
      };
      setConversation(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !loading) {
      executeQuery();
    }
  };

  // Helper to format timestamp
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Render results table for a message
  const renderResultsTable = (messageResults: Record<string, unknown>[]) => {
    if (!messageResults || messageResults.length === 0) return null;

    return (
      <div className="overflow-x-auto rounded-lg border border-gray-200 mt-3">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {Object.keys(messageResults[0]).map((key) => (
                <th
                  key={key}
                  className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {key.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {messageResults.slice(0, 10).map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50 transition-colors">
                {Object.values(row).map((value, vidx) => (
                  <td key={vidx} className="px-4 py-2 text-sm text-gray-900">
                    {value !== null && value !== undefined ? String(value) : "-"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {messageResults.length > 10 && (
          <div className="px-4 py-2 bg-gray-50 text-xs text-gray-500 text-center">
            Showing 10 of {messageResults.length} results
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-lg overflow-hidden flex flex-col" style={{ height: 'calc(100vh - 180px)', minHeight: '600px' }}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-white">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-600 rounded-lg">
              <MessageSquare className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Bensley Brain</h2>
              <p className="text-xs text-gray-500">AI-powered query assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {conversation.length > 0 && (
              <>
                <button
                  onClick={exportConversation}
                  className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  title="Export conversation"
                >
                  <Download className="h-5 w-5" />
                </button>
                <button
                  onClick={clearConversation}
                  className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Clear conversation"
                >
                  <Trash2 className="h-5 w-5" />
                </button>
              </>
            )}
          </div>
        </div>

        {/* Conversation History */}
        <div
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50"
        >
          {/* Empty State */}
          {conversation.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="p-4 bg-blue-100 rounded-full mb-4">
                <Database className="h-12 w-12 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Ask me anything about your projects
              </h3>
              <p className="text-sm text-gray-500 mb-6 max-w-md">
                I can help you find projects, check invoices, analyze emails, and much more.
                Your conversation history is preserved for follow-up questions.
              </p>
              <div className="flex flex-wrap gap-2 justify-center max-w-2xl">
                {exampleQueries.slice(0, 6).map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleExampleClick(example)}
                    className="px-3 py-2 text-sm bg-white border border-gray-200 hover:border-blue-400 hover:bg-blue-50 rounded-lg text-gray-700 transition-colors shadow-sm"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Chat Messages */}
          {conversation.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <Bot className="h-5 w-5 text-white" />
                </div>
              )}

              <div
                className={`max-w-[80%] ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white rounded-2xl rounded-tr-md px-4 py-3'
                    : 'bg-white border border-gray-200 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm'
                }`}
              >
                <p className={`text-sm ${message.role === 'user' ? 'text-white' : 'text-gray-900'}`}>
                  {message.content}
                </p>

                {/* Results for assistant messages */}
                {message.role === 'assistant' && message.results && message.results.length > 0 && (
                  renderResultsTable(message.results)
                )}

                {/* SQL Query for assistant messages */}
                {message.role === 'assistant' && message.sql && (
                  <details className="mt-2 group">
                    <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-700">
                      View SQL Query
                    </summary>
                    <pre className="mt-1 p-2 bg-gray-100 rounded text-xs overflow-x-auto">
                      {message.sql}
                    </pre>
                  </details>
                )}

                {/* Error indicator */}
                {message.error && (
                  <div className="flex items-center gap-1 mt-2 text-red-600">
                    <AlertCircle className="h-3 w-3" />
                    <span className="text-xs">Query failed</span>
                  </div>
                )}

                {/* Timestamp */}
                <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-blue-200' : 'text-gray-400'}`}>
                  {formatTime(message.timestamp)}
                </p>
              </div>

              {message.role === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                  <User className="h-5 w-5 text-white" />
                </div>
              )}
            </div>
          ))}

          {/* Loading indicator */}
          {loading && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                  <span className="text-sm text-gray-600">Thinking...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-200 bg-white">
          {/* Example queries when conversation exists */}
          {conversation.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              <span className="text-xs text-gray-500 self-center">Quick:</span>
              {["What's the total value?", "Show more details", "Filter by Thailand"].map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => handleExampleClick(example)}
                  className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded text-gray-600 transition-colors"
                >
                  {example}
                </button>
              ))}
            </div>
          )}

          <div className="flex gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={conversation.length > 0 ? "Ask a follow-up question..." : "Ask anything about your projects, invoices, or emails..."}
              aria-label="Query input"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50"
            />
            <button
              onClick={executeQuery}
              disabled={loading || !query.trim()}
              aria-label="Execute query"
              className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {loading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Search className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
