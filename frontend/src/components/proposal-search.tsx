"use client";

import { useState } from "react";
import { Search, FileText, DollarSign, Calendar, AlertCircle } from "lucide-react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface ProposalDocument {
  file_name: string;
  file_path: string;
  document_type?: string;
}

interface ProposalEmail {
  subject: string;
  date: string;
  sender_name: string;
  sender_email: string;
  snippet?: string;
}

interface ProposalResult {
  source: string;
  project_code: string;
  project_name: string;
  client_company: string;
  project_value: number;
  status: string;
  last_contact_date: string;
  on_hold: number;
  health_score: number;
  documents?: ProposalDocument[];
  recent_emails?: ProposalEmail[];
}

export default function ProposalSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ProposalResult[]>([]);
  const [selectedProposal, setSelectedProposal] = useState<ProposalResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const searchProposals = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/query/search?q=${encodeURIComponent(searchQuery)}`
      );
      if (!response.ok) throw new Error("Search failed");
      const data = await response.json();

      if (data.success) {
        setResults(data.results);
      }
    } catch (error) {
      console.error("Search error:", error);
    } finally {
      setLoading(false);
    }
  };

  const getFullStatus = async (projectCode: string) => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/query/proposal/${projectCode}/status`
      );
      if (!response.ok) throw new Error("Failed to fetch proposal status");
      const data = await response.json();

      if (data.success) {
        setSelectedProposal(data.proposal);
        setShowDetails(true);
      }
    } catch (error) {
      console.error("Error fetching proposal details:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    searchProposals(query);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "proposal":
        return "bg-blue-100 text-blue-800";
      case "won":
        return "bg-green-100 text-green-800";
      case "lost":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getHealthColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">🔍 Proposal Intelligence Search</h2>

        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                if (e.target.value.length > 2) {
                  searchProposals(e.target.value);
                }
              }}
              placeholder="Search by project code (BK-070), name (Tel Aviv), or client..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

        <div className="mt-4 text-sm text-gray-600">
          <p>💡 Try: &quot;BK-070&quot; • &quot;Tel Aviv&quot; • &quot;Bodrum&quot; • &quot;India&quot; • &quot;Maldives&quot;</p>
        </div>
      </div>

      {/* Search Results */}
      {results.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">
            Found {results.length} result{results.length !== 1 ? "s" : ""}
          </h3>

          <div className="space-y-4">
            {results.map((proposal) => (
              <div
                key={proposal.project_code}
                className="border border-gray-200 rounded-lg p-4 hover:border-blue-400 hover:shadow-md transition-all cursor-pointer"
                onClick={() => getFullStatus(proposal.project_code)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-mono text-sm font-semibold text-gray-700">
                        {proposal.project_code}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(proposal.status)}`}>
                        {proposal.status}
                      </span>
                      {proposal.on_hold === 1 && (
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                          ⏸️ On Hold
                        </span>
                      )}
                    </div>

                    <h4 className="text-lg font-medium text-gray-900 mb-1">
                      {proposal.project_name}
                    </h4>

                    {proposal.client_company && (
                      <p className="text-sm text-gray-600 mb-2">
                        Client: {proposal.client_company}
                      </p>
                    )}

                    <div className="flex gap-4 text-sm text-gray-500">
                      {proposal.project_value && (
                        <div className="flex items-center gap-1">
                          <DollarSign className="w-4 h-4" />
                          ${proposal.project_value.toLocaleString()}
                        </div>
                      )}
                      {proposal.health_score && (
                        <div className="flex items-center gap-1">
                          <span className={`font-medium ${getHealthColor(proposal.health_score)}`}>
                            Health: {proposal.health_score}%
                          </span>
                        </div>
                      )}
                      {proposal.last_contact_date && (
                        <div className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          Last contact: {new Date(proposal.last_contact_date).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="text-sm text-blue-600 hover:text-blue-700">
                    View Details →
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detailed View Modal */}
      {showDetails && selectedProposal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 p-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-mono text-lg font-bold text-gray-700">
                      {selectedProposal.project_code}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedProposal.status)}`}>
                      {selectedProposal.status}
                    </span>
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {selectedProposal.project_name}
                  </h2>
                </div>
                <button
                  onClick={() => setShowDetails(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Key Info */}
              <div className="grid grid-cols-2 gap-4">
                {selectedProposal.client_company && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Client</label>
                    <p className="text-lg">{selectedProposal.client_company}</p>
                  </div>
                )}
                {selectedProposal.project_value && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Contract Value</label>
                    <p className="text-lg font-semibold text-green-600">
                      ${selectedProposal.project_value.toLocaleString()}
                    </p>
                  </div>
                )}
                {selectedProposal.health_score && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Health Score</label>
                    <p className={`text-lg font-semibold ${getHealthColor(selectedProposal.health_score)}`}>
                      {selectedProposal.health_score}%
                    </p>
                  </div>
                )}
                {selectedProposal.last_contact_date && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Last Contact</label>
                    <p className="text-lg">
                      {new Date(selectedProposal.last_contact_date).toLocaleDateString()}
                    </p>
                  </div>
                )}
              </div>

              {/* Documents */}
              {selectedProposal.documents && selectedProposal.documents.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <FileText className="w-5 h-5" />
                    Documents ({selectedProposal.documents.length})
                  </h3>
                  <div className="space-y-2">
                    {selectedProposal.documents.slice(0, 10).map((doc, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                      >
                        <div className="flex-1">
                          <p className="font-medium text-sm">{doc.file_name}</p>
                          <p className="text-xs text-gray-500">{doc.file_path}</p>
                        </div>
                        {doc.document_type && (
                          <span className="text-xs bg-gray-200 px-2 py-1 rounded">
                            {doc.document_type}
                          </span>
                        )}
                      </div>
                    ))}
                    {selectedProposal.documents.length > 10 && (
                      <p className="text-sm text-gray-500 text-center py-2">
                        ... and {selectedProposal.documents.length - 10} more
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Recent Emails */}
              {selectedProposal.recent_emails && selectedProposal.recent_emails.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-3">
                    📧 Recent Emails ({selectedProposal.recent_emails.length})
                  </h3>
                  <div className="space-y-3">
                    {selectedProposal.recent_emails.map((email, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-start justify-between mb-1">
                          <p className="font-medium text-sm">{email.subject}</p>
                          <span className="text-xs text-gray-500">
                            {new Date(email.date).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-xs text-gray-600">
                          From: {email.sender_name} ({email.sender_email})
                        </p>
                        {email.snippet && (
                          <p className="text-xs text-gray-500 mt-1">{email.snippet}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* No Results */}
      {query && !loading && results.length === 0 && (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p className="text-gray-600">
            Try searching by project code, name, or client company
          </p>
        </div>
      )}
    </div>
  );
}
