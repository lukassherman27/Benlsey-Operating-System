"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type SystemStats = Awaited<ReturnType<typeof api.getSystemStats>>;

export default function SystemStatusPage() {
  const { data: stats, isLoading, error, refetch, dataUpdatedAt } = useQuery({
    queryKey: ["system-stats"],
    queryFn: () => api.getSystemStats(),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <Card className="p-12 text-center">
          <div className="text-lg">Loading system status...</div>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Card className="p-12 text-center bg-red-50 border-red-200">
          <div className="text-lg text-red-900">Failed to load system stats</div>
          <div className="text-sm text-red-600 mt-2">{error instanceof Error ? error.message : "Unknown error"}</div>
          <Button onClick={() => refetch()} className="mt-4">Retry</Button>
        </Card>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">System Status Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Real-time monitoring of Bensley Intelligence Platform
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Last updated: {new Date(dataUpdatedAt).toLocaleTimeString()}
          </p>
        </div>

        <Button onClick={() => refetch()} variant="outline">
          Refresh
        </Button>
      </div>

      {/* API Health */}
      <Card className={`p-4 ${
        stats.api_health.status === 'healthy'
          ? 'bg-gradient-to-br from-green-50 to-green-100 border-green-200'
          : 'bg-gradient-to-br from-red-50 to-red-100 border-red-200'
      }`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium text-gray-700">API Status</div>
            <div className={`text-2xl font-bold ${
              stats.api_health.status === 'healthy' ? 'text-green-600' : 'text-red-600'
            }`}>
              {stats.api_health.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-600">Uptime</div>
            <div className="text-sm font-medium">{stats.api_health.uptime}</div>
          </div>
        </div>
      </Card>

      {/* Email Processing Status */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="p-4 bg-gradient-to-br from-blue-50 to-blue-100">
          <div className="text-sm text-gray-600">Total Emails</div>
          <div className="text-3xl font-bold text-blue-600">{stats.emails.total.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">All emails in system</div>
        </Card>

        <Card className="p-4 bg-gradient-to-br from-green-50 to-green-100">
          <div className="text-sm text-gray-600">Processed</div>
          <div className="text-3xl font-bold text-green-600">{stats.emails.processed.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">
            {stats.emails.percent_complete}% complete
          </div>
        </Card>

        <Card className="p-4 bg-gradient-to-br from-orange-50 to-orange-100">
          <div className="text-sm text-gray-600">Unprocessed</div>
          <div className="text-3xl font-bold text-orange-600">{stats.emails.unprocessed.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">Awaiting AI processing</div>
        </Card>

        <Card className="p-4 bg-gradient-to-br from-purple-50 to-purple-100">
          <div className="text-sm text-gray-600">Email Links</div>
          <div className="text-3xl font-bold text-purple-600">{stats.email_links.total.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">Email-proposal connections</div>
        </Card>
      </div>

      {/* Email Categories */}
      <Card className="p-6">
        <h2 className="text-xl font-bold mb-4">Email Categories</h2>
        <div className="grid grid-cols-3 gap-4">
          {Object.entries(stats.emails.categories).map(([category, count]) => (
            <div key={category} className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="text-sm font-medium capitalize">{category.replace('_', ' ')}</span>
              <span className="text-lg font-bold text-gray-700">{count}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Email Links Quality */}
      <Card className="p-6">
        <h2 className="text-xl font-bold mb-4">Email Links Quality</h2>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded">
            <div className="text-sm text-gray-600">AI Generated</div>
            <div className="text-2xl font-bold text-blue-600">{stats.email_links.auto}</div>
            <div className="text-xs text-gray-500 mt-1">Automatic links</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded">
            <div className="text-sm text-gray-600">Approved</div>
            <div className="text-2xl font-bold text-green-600">{stats.email_links.approved}</div>
            <div className="text-xs text-gray-500 mt-1">Human verified</div>
          </div>
          <div className="text-center p-4 bg-emerald-50 rounded">
            <div className="text-sm text-gray-600">Manual</div>
            <div className="text-2xl font-bold text-emerald-600">{stats.email_links.manual}</div>
            <div className="text-xs text-gray-500 mt-1">User created</div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded">
            <div className="text-sm text-gray-600">Low Confidence</div>
            <div className="text-2xl font-bold text-orange-600">{stats.email_links.low_confidence}</div>
            <div className="text-xs text-gray-500 mt-1">Needs review (&lt;70%)</div>
          </div>
        </div>
      </Card>

      {/* Business Data */}
      <div className="grid grid-cols-2 gap-4">
        {/* Proposals */}
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4">Proposals</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="text-sm font-medium">Total Proposals</span>
              <span className="text-lg font-bold text-gray-700">{stats.proposals.total}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-green-50 rounded">
              <span className="text-sm font-medium">Active Projects</span>
              <span className="text-lg font-bold text-green-600">{stats.proposals.active}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
              <span className="text-sm font-medium">In Progress</span>
              <span className="text-lg font-bold text-blue-600">{stats.proposals.proposal}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-red-50 rounded">
              <span className="text-sm font-medium">Lost</span>
              <span className="text-lg font-bold text-red-600">{stats.proposals.lost}</span>
            </div>
          </div>
        </Card>

        {/* Financials */}
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4">Financial Data</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="text-sm font-medium">Total Contracts</span>
              <span className="text-lg font-bold text-gray-700">{stats.financials.total_contracts}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="text-sm font-medium">Total Invoices</span>
              <span className="text-lg font-bold text-gray-700">{stats.financials.total_invoices}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-green-50 rounded">
              <span className="text-sm font-medium">Total Revenue</span>
              <span className="text-lg font-bold text-green-600">
                ${(stats.financials.total_revenue_usd / 1000).toFixed(0)}K
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Database Stats */}
      <Card className="p-6">
        <h2 className="text-xl font-bold mb-4">Database Statistics</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-sm text-gray-600">Database Size</div>
            <div className="text-2xl font-bold text-gray-700">{stats.database.size_mb} MB</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-sm text-gray-600">Total Tables</div>
            <div className="text-2xl font-bold text-gray-700">{stats.database.tables}</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-sm text-gray-600">Total Records</div>
            <div className="text-2xl font-bold text-gray-700">{stats.database.total_records.toLocaleString()}</div>
          </div>
        </div>
      </Card>

      {/* Quick Actions */}
      <Card className="p-6">
        <h2 className="text-xl font-bold mb-4">Quick Actions</h2>
        <div className="flex gap-3 flex-wrap">
          <Button onClick={() => window.location.href = '/admin/email-links'}>
            Email Links Manager
          </Button>
          <Button onClick={() => window.location.href = '/'} variant="outline">
            Dashboard
          </Button>
          <Button onClick={() => window.location.href = '/proposals'} variant="outline">
            Proposals
          </Button>
          <Button onClick={() => window.location.href = '/tracker'} variant="outline">
            Tracker
          </Button>
        </div>
      </Card>
    </div>
  );
}
