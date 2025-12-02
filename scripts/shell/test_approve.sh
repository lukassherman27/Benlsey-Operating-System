#!/bin/bash

echo "Testing approve endpoint..."
curl -X POST http://localhost:8000/api/admin/validation/suggestions/13/approve \
  -H "Content-Type: application/json" \
  -d '{"reviewed_by": "test_user", "review_notes": "Test approval"}'

echo ""
echo "Testing deny endpoint..."
curl -X POST http://localhost:8000/api/admin/validation/suggestions/10/deny \
  -H "Content-Type: application/json" \
  -d '{"reviewed_by": "test_user", "review_notes": "Test denial"}'
