/**
 * Test script for the getProposalWeeklyChanges API method
 *
 * This demonstrates how to use the weekly changes endpoint from the frontend.
 * Run this with: npx ts-node scripts/test-weekly-changes-api.ts
 */

import { api } from '../src/lib/api';

async function testWeeklyChangesAPI() {
  console.log('Testing /api/proposals/weekly-changes endpoint...\n');

  try {
    // Test with default 7 days
    console.log('Fetching weekly changes (last 7 days)...');
    const weeklyChanges = await api.getProposalWeeklyChanges(7);

    console.log('\n=== PERIOD ===');
    console.log(`Start Date: ${weeklyChanges.period.start_date}`);
    console.log(`End Date: ${weeklyChanges.period.end_date}`);
    console.log(`Days: ${weeklyChanges.period.days}`);

    console.log('\n=== SUMMARY ===');
    console.log(`New Proposals: ${weeklyChanges.summary.new_proposals}`);
    console.log(`Status Changes: ${weeklyChanges.summary.status_changes}`);
    console.log(`Stalled Proposals: ${weeklyChanges.summary.stalled_proposals}`);
    console.log(`Won Proposals: ${weeklyChanges.summary.won_proposals}`);
    console.log(`Total Pipeline Value: ${weeklyChanges.summary.total_pipeline_value}`);

    console.log('\n=== NEW PROPOSALS ===');
    if (weeklyChanges.new_proposals.length > 0) {
      weeklyChanges.new_proposals.forEach((proposal, i) => {
        console.log(`${i + 1}. ${proposal.project_code} - ${proposal.project_name}`);
        console.log(`   Client: ${proposal.client_company}`);
        console.log(`   Status: ${proposal.status || 'N/A'}`);
        console.log(`   Created: ${proposal.created_date || 'N/A'}`);
      });
    } else {
      console.log('No new proposals in this period');
    }

    console.log('\n=== STATUS CHANGES ===');
    if (weeklyChanges.status_changes.length > 0) {
      weeklyChanges.status_changes.forEach((change, i) => {
        console.log(`${i + 1}. ${change.project_code} - ${change.project_name}`);
        console.log(`   ${change.previous_status} → ${change.new_status}`);
        console.log(`   Changed: ${change.changed_date}`);
      });
    } else {
      console.log('No status changes in this period');
    }

    console.log('\n=== STALLED PROPOSALS ===');
    if (weeklyChanges.stalled_proposals.length > 0) {
      weeklyChanges.stalled_proposals.forEach((proposal, i) => {
        console.log(`${i + 1}. ${proposal.project_code} - ${proposal.project_name}`);
        console.log(`   Client: ${proposal.client_company}`);
        console.log(`   Days Since Contact: ${proposal.days_since_contact}`);
        console.log(`   Last Contact: ${proposal.last_contact_date || 'Never'}`);
      });
    } else {
      console.log('No stalled proposals');
    }

    console.log('\n=== WON PROPOSALS ===');
    if (weeklyChanges.won_proposals.length > 0) {
      weeklyChanges.won_proposals.forEach((proposal, i) => {
        console.log(`${i + 1}. ${proposal.project_code} - ${proposal.project_name}`);
        console.log(`   Client: ${proposal.client_company}`);
        console.log(`   Fee: $${proposal.fee.toLocaleString()}`);
        console.log(`   Signed: ${proposal.signed_date}`);
      });
    } else {
      console.log('No won proposals in this period');
    }

    console.log('\n✓ API call successful!');

  } catch (error) {
    console.error('\n✗ API call failed:');
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

// Usage example in a React component:
/*
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

function WeeklyChangesComponent() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['weekly-changes', 7],
    queryFn: () => api.getProposalWeeklyChanges(7),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  if (isLoading) return <div>Loading weekly changes...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!data) return null;

  return (
    <div>
      <h2>Weekly Changes ({data.period.start_date} to {data.period.end_date})</h2>

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
            {proposal.project_code} - {proposal.project_name}
          </div>
        ))}
      </div>
    </div>
  );
}
*/

// Run the test if executed directly
if (require.main === module) {
  testWeeklyChangesAPI();
}

export { testWeeklyChangesAPI };
