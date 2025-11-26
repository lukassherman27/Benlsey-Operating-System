#!/bin/bash
for id in 2027637 2027619 2027567 2027519 2027518 2027517 2027555 2026815 2026764 2026706; do
  echo ""
  echo "════════════════════════════════════════════════════════════════"
  echo "📧 EXAMPLE EMAIL #$id"
  echo "════════════════════════════════════════════════════════════════"
  
  sqlite3 database/bensley_master.db << SQL
.mode line
SELECT 
  'EMAIL ID' as field, email_id as value FROM emails WHERE email_id = $id
UNION ALL SELECT 'FROM', sender_email FROM emails WHERE email_id = $id
UNION ALL SELECT 'SUBJECT', subject FROM emails WHERE email_id = $id
UNION ALL SELECT 'DATE', strftime('%Y-%m-%d', date) FROM emails WHERE email_id = $id
UNION ALL SELECT '🎯 AI STAGE', stage FROM emails WHERE email_id = $id
UNION ALL SELECT '🎯 AI CATEGORY', category FROM emails WHERE email_id = $id;
SQL

  echo ""
  echo "🔗 LINKED TO PROPOSALS:"
  sqlite3 database/bensley_master.db "
    SELECT '  → ' || p.project_code || ': ' || p.project_name
    FROM email_proposal_links epl
    JOIN proposals p ON epl.proposal_id = p.proposal_id
    WHERE epl.email_id = $id
  " || echo "  (None)"
  
  echo ""
  echo "📄 EMAIL BODY (what AI read):"
  echo "---"
  sqlite3 database/bensley_master.db "SELECT SUBSTR(body_full, 1, 600) || '...' FROM emails WHERE email_id = $id"
  echo "---"
  echo ""
done
