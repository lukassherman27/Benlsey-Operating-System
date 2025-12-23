"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface EmailLink {
  link_id: number;
  email_id: number;
  proposal_id: number;
  confidence_score: number;
  link_type: string;
  match_reasons: string | null;
  created_at: string;
  subject: string;
  sender_email: string;
  email_date: string;
  snippet: string;
  category: string;
  project_code: string;
  project_name: string;
  proposal_status: string;
}

interface Proposal {
  proposal_id: number;
  project_code: string;
  project_name: string;
  status: string;
}

export default function EmailLinksManagerPage() {
  const [links, setLinks] = useState<EmailLink[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState("all");
  const [selectedConfidence, setSelectedConfidence] = useState("all");
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = 50;

  // Bulk selection
  const [selectedLinks, setSelectedLinks] = useState<Set<number>>(new Set());
  const [selectAll, setSelectAll] = useState(false);

  // Edit dialog
  const [editingLink, setEditingLink] = useState<EmailLink | null>(null);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [proposalSearch, setProposalSearch] = useState("");

  // Fetch email links
  const fetchLinks = useCallback(async () => {
    try {
      setLoading(true);

      let url = `${API_BASE_URL}/api/admin/email-links?limit=${limit}&offset=${offset}`;

      if (selectedType !== "all") {
        url += `&link_type=${selectedType}`;
      }

      if (selectedConfidence === "low") {
        url += `&confidence_min=0&confidence_max=0.7`;
      } else if (selectedConfidence === "high") {
        url += `&confidence_min=0.7`;
      }

      const response = await fetch(url);
      const data = await response.json();

      setLinks(data.links || []);
      setTotal(data.total || 0);

    } catch (error) {
      console.error("Failed to fetch links:", error);
    } finally {
      setLoading(false);
    }
  }, [offset, selectedType, selectedConfidence, limit]);

  useEffect(() => {
    fetchLinks();
    setSelectedLinks(new Set()); // Clear selection when page changes
    setSelectAll(false);
  }, [fetchLinks]);

  const fetchProposals = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/proposals`);
      const data = await response.json();
      setProposals(data.proposals || []);
    } catch (error) {
      console.error("Failed to fetch proposals:", error);
    }
  };

  const deleteLink = async (linkId: number) => {
    if (!confirm("Delete this email-proposal link? This will help train the AI not to make similar links.")) return;

    try {
      await fetch(`${API_BASE_URL}/api/admin/email-links/${linkId}?user=bill@bensley.com`, {
        method: "DELETE"
      });

      // Remove from UI
      setLinks(links.filter(l => l.link_id !== linkId));
      setTotal(total - 1);
      selectedLinks.delete(linkId);
      setSelectedLinks(new Set(selectedLinks));

      alert("✅ Link deleted! AI will learn from this.");

    } catch (error) {
      console.error("Failed to delete link:", error);
      alert("Failed to delete link");
    }
  };

  const approveLink = async (linkId: number, retryCount = 0) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/email-links/${linkId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          link_type: "approved",
          confidence_score: 1.0,
          user: "bill@bensley.com"
        })
      });

      const result = await response.json();

      // Handle database locked error with retry (up to 3 times)
      if (result.detail && result.detail.includes("database is locked") && retryCount < 3) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        return approveLink(linkId, retryCount + 1);
      }

      if (!response.ok) {
        throw new Error(result.detail || "Failed to approve link");
      }

      // Update UI
      setLinks(links.map(l =>
        l.link_id === linkId
          ? { ...l, link_type: "approved", confidence_score: 1.0 }
          : l
      ));

      return true;

    } catch (error) {
      console.error("Failed to approve link:", error);
      alert(`❌ Failed to approve link: ${error instanceof Error ? error.message : 'Unknown error'}`);
      return false;
    }
  };

  // Bulk operations
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedLinks(new Set());
    } else {
      setSelectedLinks(new Set(filteredLinks.map(l => l.link_id)));
    }
    setSelectAll(!selectAll);
  };

  const handleSelectLink = (linkId: number) => {
    const newSelected = new Set(selectedLinks);
    if (newSelected.has(linkId)) {
      newSelected.delete(linkId);
    } else {
      newSelected.add(linkId);
    }
    setSelectedLinks(newSelected);
    setSelectAll(newSelected.size === filteredLinks.length);
  };

  const bulkApprove = async () => {
    if (selectedLinks.size === 0) return;
    if (!confirm(`Approve ${selectedLinks.size} selected links?`)) return;

    let successCount = 0;
    const selectedArray = Array.from(selectedLinks);

    for (const linkId of selectedArray) {
      const success = await approveLink(linkId);
      if (success) successCount++;
      await new Promise(resolve => setTimeout(resolve, 200)); // Throttle
    }

    alert(`✅ Approved ${successCount} of ${selectedArray.length} links!`);
    setSelectedLinks(new Set());
    setSelectAll(false);
  };

  const bulkDelete = async () => {
    if (selectedLinks.size === 0) return;
    if (!confirm(`Delete ${selectedLinks.size} selected links? This cannot be undone.`)) return;

    let successCount = 0;
    const selectedArray = Array.from(selectedLinks);

    for (const linkId of selectedArray) {
      try {
        await fetch(`${API_BASE_URL}/api/admin/email-links/${linkId}?user=bill@bensley.com`, {
          method: "DELETE"
        });
        successCount++;
        await new Promise(resolve => setTimeout(resolve, 200)); // Throttle
      } catch (error) {
        console.error(`Failed to delete link ${linkId}:`, error);
      }
    }

    // Refresh the list
    await fetchLinks();
    alert(`✅ Deleted ${successCount} of ${selectedArray.length} links!`);
    setSelectedLinks(new Set());
    setSelectAll(false);
  };

  // Edit dialog
  const openEditDialog = async (link: EmailLink) => {
    setEditingLink(link);
    setProposalSearch("");
    await fetchProposals();
  };

  const closeEditDialog = () => {
    setEditingLink(null);
    setProposalSearch("");
  };

  const saveEdit = async (newProposalId: number) => {
    if (!editingLink) return;

    try {
      // Delete old link
      await fetch(`${API_BASE_URL}/api/admin/email-links/${editingLink.link_id}?user=bill@bensley.com`, {
        method: "DELETE"
      });

      // Create new link
      const response = await fetch(`${API_BASE_URL}/api/admin/email-links`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email_id: editingLink.email_id,
          proposal_id: newProposalId,
          user: "bill@bensley.com"
        })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Failed to create new link");
      }

      alert("✅ Link updated successfully!");
      closeEditDialog();
      await fetchLinks();

    } catch (error) {
      console.error("Failed to save edit:", error);
      alert(`❌ Failed to save: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  // Filter by search query (client-side for current page)
  const filteredLinks = links.filter(link => {
    if (!searchQuery) return true;

    const query = searchQuery.toLowerCase();
    return (
      link.subject?.toLowerCase().includes(query) ||
      link.sender_email?.toLowerCase().includes(query) ||
      link.project_code?.toLowerCase().includes(query) ||
      link.project_name?.toLowerCase().includes(query) ||
      link.category?.toLowerCase().includes(query)
    );
  });

  const filteredProposals = proposals.filter(p => {
    if (!proposalSearch) return true;
    const query = proposalSearch.toLowerCase();
    return (
      p.project_code?.toLowerCase().includes(query) ||
      p.project_name?.toLowerCase().includes(query)
    );
  });

  const stats = {
    total: total,
    auto: links.filter(l => l.link_type === 'auto').length,
    manual: links.filter(l => l.link_type === 'manual').length,
    lowConfidence: links.filter(l => l.confidence_score < 0.7).length
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">📧 Email Links Training Center</h1>
          <p className="text-gray-600 mt-1">
            Review AI-generated email links, approve good ones, delete bad ones to train the system
          </p>
        </div>

        <Button
          onClick={fetchLinks}
          variant="outline"
        >
          🔄 Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="p-4 bg-gradient-to-br from-blue-50 to-blue-100">
          <div className="text-sm text-gray-600">Total Links</div>
          <div className="text-3xl font-bold text-blue-600">{total.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">All email-proposal connections</div>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-purple-50 to-purple-100">
          <div className="text-sm text-gray-600">AI Generated</div>
          <div className="text-3xl font-bold text-purple-600">{stats.auto}</div>
          <div className="text-xs text-gray-500 mt-1">Auto-linked by AI</div>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-green-50 to-green-100">
          <div className="text-sm text-gray-600">Manual/Approved</div>
          <div className="text-3xl font-bold text-green-600">{stats.manual}</div>
          <div className="text-xs text-gray-500 mt-1">Human verified</div>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-orange-50 to-orange-100">
          <div className="text-sm text-gray-600">Need Review</div>
          <div className="text-3xl font-bold text-orange-600">{stats.lowConfidence}</div>
          <div className="text-xs text-gray-500 mt-1">Low confidence (&lt; 70%)</div>
        </Card>
      </div>

      {/* Bulk Actions Bar */}
      {selectedLinks.size > 0 && (
        <Card className="p-4 bg-blue-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium text-blue-900">
              {selectedLinks.size} link{selectedLinks.size !== 1 ? 's' : ''} selected
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={bulkApprove}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                ✓ Approve Selected
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={bulkDelete}
                className="border-red-300 text-red-600 hover:bg-red-50"
              >
                🗑️ Delete Selected
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setSelectedLinks(new Set());
                  setSelectAll(false);
                }}
              >
                Clear Selection
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Filters */}
      <Card className="p-4">
        <div className="flex gap-4 items-center flex-wrap">
          <Input
            placeholder="🔍 Search emails, senders, projects, categories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="max-w-md flex-1"
          />

          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="border rounded px-3 py-2 bg-white"
          >
            <option value="all">All Types</option>
            <option value="auto">AI Generated</option>
            <option value="manual">Manual</option>
            <option value="approved">Approved</option>
          </select>

          <select
            value={selectedConfidence}
            onChange={(e) => setSelectedConfidence(e.target.value)}
            className="border rounded px-3 py-2 bg-white"
          >
            <option value="all">All Confidence</option>
            <option value="low">Low (&lt; 70%) - Needs Review</option>
            <option value="high">High (&ge; 70%)</option>
          </select>

          <Button
            variant="outline"
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={offset === 0}
          >
            ← Previous
          </Button>

          <span className="text-sm text-gray-600">
            {offset + 1}-{Math.min(offset + limit, total)} of {total.toLocaleString()}
          </span>

          <Button
            variant="outline"
            onClick={() => setOffset(offset + limit)}
            disabled={offset + limit >= total}
          >
            Next →
          </Button>
        </div>
      </Card>

      {/* Links Table */}
      <div className="space-y-3">
        {loading ? (
          <Card className="p-12 text-center">
            <div className="text-lg">Loading links...</div>
          </Card>
        ) : filteredLinks.length === 0 ? (
          <Card className="p-12 text-center text-gray-500">
            No links found matching your filters
          </Card>
        ) : (
          <>
            {/* Select All Header */}
            <Card className="p-3 bg-gray-50">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={selectAll}
                  onChange={handleSelectAll}
                  className="w-4 h-4"
                />
                <span className="text-sm font-medium text-gray-700">
                  Select All ({filteredLinks.length} on this page)
                </span>
              </div>
            </Card>

            {filteredLinks.map((link) => (
              <Card
                key={link.link_id}
                className={`p-4 hover:shadow-md transition-shadow ${
                  selectedLinks.has(link.link_id) ? 'border-blue-400 border-2' : ''
                }`}
              >
                <div className="flex justify-between items-start gap-4">
                  {/* Checkbox */}
                  <div className="pt-1">
                    <input
                      type="checkbox"
                      checked={selectedLinks.has(link.link_id)}
                      onChange={() => handleSelectLink(link.link_id)}
                      className="w-4 h-4"
                    />
                  </div>

                  <div className="flex-1 space-y-2">
                    {/* Email Info */}
                    <div>
                      <div className="font-semibold text-lg text-gray-900">
                        {link.subject || "(No Subject)"}
                      </div>
                      <div className="text-sm text-gray-600 flex items-center gap-3 mt-1">
                        <span>From: <strong>{link.sender_email}</strong></span>
                        <span>•</span>
                        <span>{new Date(link.email_date).toLocaleDateString()}</span>
                      </div>
                    </div>

                    {/* Link Info */}
                    <div className="flex items-center gap-3 text-sm flex-wrap">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-600">Linked to:</span>
                        <span className="bg-blue-600 text-white px-3 py-1 rounded-full font-medium">
                          {link.project_code}
                        </span>
                        <span className="font-medium">{link.project_name}</span>
                      </div>

                      <span className="text-gray-400">|</span>

                      <div className="flex items-center gap-2">
                        <span className="text-gray-600">Category:</span>
                        <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs font-medium">
                          {link.category}
                        </span>
                      </div>

                      <span className="text-gray-400">|</span>

                      <div className="flex items-center gap-2">
                        <span className="text-gray-600">Confidence:</span>
                        <span className={`font-bold text-lg ${
                          link.confidence_score >= 0.8 ? 'text-green-600' :
                          link.confidence_score >= 0.6 ? 'text-yellow-600' :
                          'text-orange-600'
                        }`}>
                          {(link.confidence_score * 100).toFixed(0)}%
                        </span>
                      </div>

                      <span className="text-gray-400">|</span>

                      <div className="flex items-center gap-2">
                        <span className="text-gray-600">Source:</span>
                        <span className={`text-xs px-2 py-1 rounded font-medium ${
                          link.link_type === 'auto' ? 'bg-blue-100 text-blue-800' :
                          link.link_type === 'manual' ? 'bg-green-100 text-green-800' :
                          link.link_type === 'approved' ? 'bg-emerald-100 text-emerald-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {link.link_type === 'auto' ? '🤖 AI' :
                           link.link_type === 'manual' ? '👤 Manual' :
                           link.link_type === 'approved' ? '✅ Approved' : link.link_type}
                        </span>
                      </div>

                      <span className="text-gray-400">|</span>

                      <div className="flex items-center gap-2">
                        <span className="text-gray-600">Status:</span>
                        <span className={`text-xs px-2 py-1 rounded font-medium ${
                          link.proposal_status === 'active' ? 'bg-green-100 text-green-800' :
                          link.proposal_status === 'proposal' ? 'bg-blue-100 text-blue-800' :
                          link.proposal_status === 'lost' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {link.proposal_status}
                        </span>
                      </div>
                    </div>

                    {/* Match Reasons */}
                    {link.match_reasons && (
                      <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                        <strong>Why linked:</strong> {link.match_reasons}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 flex-col">
                    {link.link_type === 'auto' && link.confidence_score < 0.95 && (
                      <Button
                        size="sm"
                        onClick={() => approveLink(link.link_id)}
                        className="bg-green-600 hover:bg-green-700 text-white"
                      >
                        ✓ Approve
                      </Button>
                    )}

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => openEditDialog(link)}
                      className="border-gray-300"
                    >
                      ✏️ Edit
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => deleteLink(link.link_id)}
                      className="border-red-300 text-red-600 hover:bg-red-50"
                    >
                      🗑️ Delete
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </>
        )}
      </div>

      {/* Bottom Pagination */}
      <Card className="p-4 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          Showing {offset + 1}-{Math.min(offset + limit, total)} of {total.toLocaleString()} links
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={offset === 0}
          >
            ← Previous
          </Button>

          <Button
            variant="outline"
            onClick={() => setOffset(offset + limit)}
            disabled={offset + limit >= total}
          >
            Next →
          </Button>
        </div>
      </Card>

      {/* Edit Dialog */}
      {editingLink && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl max-h-[80vh] overflow-auto p-6">
            <h2 className="text-2xl font-bold mb-4">Edit Email Link</h2>

            <div className="space-y-4">
              {/* Current Link */}
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm font-medium text-gray-700 mb-2">Current Link:</div>
                <div className="font-semibold">{editingLink.subject || "(No Subject)"}</div>
                <div className="text-sm text-gray-600">From: {editingLink.sender_email}</div>
                <div className="text-sm text-gray-600 mt-2">
                  Currently linked to: <strong>{editingLink.project_code}</strong> - {editingLink.project_name}
                </div>
              </div>

              {/* Search Proposals */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Change to different proposal:
                </label>
                <Input
                  placeholder="Search proposals by code or name..."
                  value={proposalSearch}
                  onChange={(e) => setProposalSearch(e.target.value)}
                  className="mb-3"
                />

                {/* Proposal List */}
                <div className="border rounded max-h-60 overflow-y-auto">
                  {filteredProposals.length === 0 ? (
                    <div className="p-4 text-center text-gray-500">
                      No proposals found
                    </div>
                  ) : (
                    filteredProposals.map((proposal) => (
                      <button
                        key={proposal.proposal_id}
                        onClick={() => saveEdit(proposal.proposal_id)}
                        className="w-full p-3 text-left hover:bg-blue-50 border-b last:border-b-0 transition-colors"
                      >
                        <div className="font-medium text-blue-600">{proposal.project_code}</div>
                        <div className="text-sm text-gray-600">{proposal.project_name}</div>
                        <div className="text-xs text-gray-500 mt-1">Status: {proposal.status}</div>
                      </button>
                    ))
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2 justify-end pt-4">
                <Button variant="outline" onClick={closeEditDialog}>
                  Cancel
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
