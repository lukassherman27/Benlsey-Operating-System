# Weekly Changes API Integration Guide

## Overview

The `/api/proposals/weekly-changes` endpoint provides proposal pipeline changes for Bill's weekly reports. It returns what changed in the proposals pipeline over a specified period, grouped by change type.

## Backend Endpoint

### Endpoint Details
- **URL**: `/api/proposals/weekly-changes`
- **Method**: `GET`
- **Query Parameters**:
  - `days` (optional): Number of days to look back (default: 7, min: 1, max: 90)

### Response Structure

```json
{
  "period": {
    "start_date": "2025-11-11",
    "end_date": "2025-11-18",
    "days": 7
  },
  "summary": {
    "new_proposals": 5,
    "status_changes": 12,
    "stalled_proposals": 3,
    "won_proposals": 2,
    "total_pipeline_value": "$2.5M"
  },
  "new_proposals": [
    {
      "proposal_id": 123,
      "project_code": "PRJ-2025-001",
      "project_name": "Example Project",
      "client_company": "Acme Corp",
      "fee": 150000,
      "status": "proposal",
      "created_date": "2025-11-15"
    }
  ],
  "status_changes": [
    {
      "project_code": "PRJ-2025-002",
      "project_name": "Another Project",
      "client_company": "Tech Inc",
      "previous_status": "proposal",
      "new_status": "active",
      "changed_date": "2025-11-16"
    }
  ],
  "stalled_proposals": [
    {
      "proposal_id": 456,
      "project_code": "PRJ-2024-050",
      "project_name": "Stalled Project",
      "client_company": "Old Client",
      "days_since_contact": 35,
      "last_contact_date": "2025-10-14"
    }
  ],
  "won_proposals": [
    {
      "proposal_id": 789,
      "project_code": "PRJ-2025-003",
      "project_name": "Won Project",
      "client_company": "Happy Client",
      "fee": 250000,
      "signed_date": "2025-11-17"
    }
  ]
}
```

## Frontend Integration

### TypeScript Types

The following TypeScript interfaces have been added to `src/lib/types.ts`:

```typescript
export interface WeeklyChangeProposal {
  proposal_id: number;
  project_code: string;
  project_name: string;
  client_company: string;
  fee?: number;
  status?: string;
  created_date?: string;
}

export interface WeeklyChangeStatusChange {
  project_code: string;
  project_name: string;
  client_company: string;
  previous_status: string;
  new_status: string;
  changed_date: string;
}

export interface WeeklyChangeStalledProposal {
  proposal_id: number;
  project_code: string;
  project_name: string;
  client_company: string;
  days_since_contact: number;
  last_contact_date: string | null;
}

export interface WeeklyChangeWonProposal {
  proposal_id: number;
  project_code: string;
  project_name: string;
  client_company: string;
  fee: number;
  signed_date: string;
}

export interface ProposalWeeklyChanges {
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  summary: {
    new_proposals: number;
    status_changes: number;
    stalled_proposals: number;
    won_proposals: number;
    total_pipeline_value: string;
  };
  new_proposals: WeeklyChangeProposal[];
  status_changes: WeeklyChangeStatusChange[];
  stalled_proposals: WeeklyChangeStalledProposal[];
  won_proposals: WeeklyChangeWonProposal[];
}
```

### API Client Method

The API client method has been added to `src/lib/api.ts`:

```typescript
getProposalWeeklyChanges: (days = 7) =>
  request<ProposalWeeklyChanges>(
    `/api/proposals/weekly-changes${buildQuery({ days })}`
  )
```

### Usage in React Components

#### Basic Usage with React Query

```typescript
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

function WeeklyChangesComponent() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['weekly-changes', 7],
    queryFn: () => api.getProposalWeeklyChanges(7),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  if (isLoading) {
    return <div>Loading weekly changes...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  if (!data) {
    return null;
  }

  return (
    <div>
      <h2>
        Weekly Changes ({data.period.start_date} to {data.period.end_date})
      </h2>

      <div>
        <h3>Summary</h3>
        <p>New Proposals: {data.summary.new_proposals}</p>
        <p>Status Changes: {data.summary.status_changes}</p>
        <p>Won Proposals: {data.summary.won_proposals}</p>
        <p>Pipeline Value: {data.summary.total_pipeline_value}</p>
      </div>

      <div>
        <h3>New Proposals</h3>
        {data.new_proposals.map(proposal => (
          <div key={proposal.proposal_id}>
            <strong>{proposal.project_code}</strong> - {proposal.project_name}
            <br />
            Client: {proposal.client_company}
          </div>
        ))}
      </div>
    </div>
  );
}
```

#### Advanced Usage with Custom Time Periods

```typescript
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

function WeeklyChangesWithControls() {
  const [days, setDays] = useState(7);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['weekly-changes', days],
    queryFn: () => api.getProposalWeeklyChanges(days),
    staleTime: 5 * 60 * 1000,
    enabled: true,
  });

  return (
    <div>
      <div>
        <label>
          Time Period:
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </label>
        <button onClick={() => refetch()}>Refresh</button>
      </div>

      {isLoading && <div>Loading...</div>}
      {error && <div>Error: {error.message}</div>}
      {data && (
        <div>
          {/* Render weekly changes data */}
        </div>
      )}
    </div>
  );
}
```

#### Error Handling Pattern

```typescript
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

function WeeklyChangesWithErrorHandling() {
  const { data, isLoading, error, isError } = useQuery({
    queryKey: ['weekly-changes', 7],
    queryFn: () => api.getProposalWeeklyChanges(7),
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    onError: (error) => {
      console.error('Failed to fetch weekly changes:', error);
      // You can also show a toast notification here
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin">Loading...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4">
        <h3 className="text-red-800 font-semibold">Failed to Load Data</h3>
        <p className="text-red-600">{error instanceof Error ? error.message : 'Unknown error'}</p>
      </div>
    );
  }

  return <div>{/* Render data */}</div>;
}
```

## Testing

### Manual Testing
1. Ensure the backend server is running on `http://localhost:8000`
2. Test the endpoint directly:
   ```bash
   curl "http://localhost:8000/api/proposals/weekly-changes?days=7"
   ```

### Using the Test Script
Run the provided test script to verify the API integration:
```bash
cd frontend
npx ts-node scripts/test-weekly-changes-api.ts
```

## Important Notes

1. **Backend Requirement**: The backend server must be running and accessible at the configured `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000`)

2. **Data Freshness**: The endpoint calculates data in real-time from the database. Consider implementing appropriate caching strategies in your React components using React Query's `staleTime` and `cacheTime` options.

3. **Performance**: The endpoint performs multiple database queries. For large datasets, it may take several seconds to respond. Implement loading states and consider timeouts.

4. **Date Formats**: All dates are returned as ISO 8601 strings (e.g., "2025-11-18").

5. **Currency Formatting**: The `total_pipeline_value` in the summary is pre-formatted as a string (e.g., "$2.5M" or "$150,000"). Individual proposal fees are returned as numbers.

## Method Signature

```typescript
api.getProposalWeeklyChanges(days?: number): Promise<ProposalWeeklyChanges>
```

**Parameters:**
- `days` (optional): Number of days to look back (default: 7)

**Returns:**
- Promise that resolves to `ProposalWeeklyChanges` object

**Throws:**
- Error if the API request fails
- Error if the backend is not accessible
- Error if the response format is invalid

## Next Steps

For Phase 1 integration, you can now:

1. Import the API method: `import { api } from '@/lib/api';`
2. Use it in your components with React Query
3. Access fully typed response data
4. Build UI components around the weekly changes data

The API is ready for frontend integration. The types are fully defined and the method includes proper error handling inherited from the base `request` function.
