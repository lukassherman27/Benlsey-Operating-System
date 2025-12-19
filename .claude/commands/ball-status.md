# Ball Status Command

When user says "ball status" or runs /ball-status:

Show who has the ball on each active proposal.

## Query

```sql
-- Get ball status for each proposal with pending tasks
WITH proposal_balls AS (
  SELECT
    p.project_code,
    p.project_name,
    p.status,
    p.last_contact_date,
    julianday('now') - julianday(p.last_contact_date) as days_since_contact,
    SUM(CASE WHEN t.assignee IN ('us', 'Lukas', 'Bill', 'Brian', 'Team') AND t.status = 'pending' THEN 1 ELSE 0 END) as our_pending,
    SUM(CASE WHEN t.assignee NOT IN ('us', 'Lukas', 'Bill', 'Brian', 'Team') AND t.status = 'pending' THEN 1 ELSE 0 END) as their_pending,
    MIN(CASE WHEN t.assignee IN ('us', 'Lukas', 'Bill', 'Brian', 'Team') AND t.status = 'pending' THEN t.due_date END) as our_next_due,
    MIN(CASE WHEN t.assignee NOT IN ('us', 'Lukas', 'Bill', 'Brian', 'Team') AND t.status = 'pending' THEN t.due_date END) as their_next_due
  FROM proposals p
  LEFT JOIN tasks t ON t.project_code = p.project_code
  WHERE p.status NOT IN ('Lost', 'On Hold', 'Contract Signed')
  GROUP BY p.project_code
)
SELECT * FROM proposal_balls
WHERE our_pending > 0 OR their_pending > 0
ORDER BY days_since_contact DESC;
```

## Present Like This:

```
🎱 BALL STATUS - Active Proposals
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 BALL WITH US (we need to act):
┌─────────────┬────────────────────────┬──────────┬─────────────┐
│ Project     │ Name                   │ Tasks    │ Next Due    │
├─────────────┼────────────────────────┼──────────┼─────────────┤
│ 25 BK-087   │ Pearl Resorts Vahine   │ 3 tasks  │ Tomorrow    │
│ 25 BK-033   │ Ritz Carlton Nusa Dua  │ 1 task   │ Friday      │
└─────────────┴────────────────────────┴──────────┴─────────────┘

🟡 BALL WITH THEM (waiting on client):
┌─────────────┬────────────────────────┬──────────┬─────────────┐
│ Project     │ Name                   │ Waiting  │ Days Silent │
├─────────────┼────────────────────────┼──────────┼─────────────┤
│ 25 BK-042   │ Sabrah Saudi Arabia    │ Contract │ 5 days ⚠️   │
│ 25 BK-058   │ Fenfushi Maldives      │ Brief    │ 3 days      │
└─────────────┴────────────────────────┴──────────┴─────────────┘

🟢 NO PENDING TASKS:
- 25 BK-070: Last contact 2 days ago (healthy)
- 25 BK-078: Last contact 4 days ago (ok)

⚠️ = Consider sending nudge
```
