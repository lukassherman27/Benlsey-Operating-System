#!/usr/bin/env python3
"""
Quick test of service layer
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.proposal_service import ProposalService
from backend.services.email_service import EmailService
from backend.services.document_service import DocumentService
from backend.services.query_service import QueryService

print("="*80)
print("🧪 TESTING SERVICE LAYER")
print("="*80)

# Test Proposal Service
print("\n1. Testing ProposalService...")
proposal_svc = ProposalService()

stats = proposal_svc.get_dashboard_stats()
print(f"   ✅ Dashboard stats: {stats['total_proposals']} proposals, {stats['active_projects']} active")

proposal = proposal_svc.get_proposal_by_code('BK-069')
if proposal:
    print(f"   ✅ Get proposal: {proposal['project_name']}")

# Test Email Service
print("\n2. Testing EmailService...")
email_svc = EmailService()

email_stats = email_svc.get_email_stats()
print(f"   ✅ Email stats: {email_stats['total_emails']} total, {email_stats['processed']} processed")

# Test Document Service
print("\n3. Testing DocumentService...")
doc_svc = DocumentService()

doc_stats = doc_svc.get_document_stats()
print(f"   ✅ Document stats: {doc_stats['total_documents']} documents")

# Test Query Service
print("\n4. Testing QueryService...")
query_svc = QueryService()

result = query_svc.query("Show me all proposals")
print(f"   ✅ Natural language query: Found {result['count']} results")

print("\n" + "="*80)
print("✅ ALL SERVICES WORKING")
print("="*80 + "\n")
