#!/usr/bin/env python3
"""
Document Query Interface
Ask natural language questions about proposals and documents
"""
import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime
from email.utils import parsedate_to_datetime
import json
from openai import OpenAI

class DocumentQuery:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Initialize OpenAI
        api_key = os.environ.get('OPENAI_API_KEY')
        self.ai_enabled = bool(api_key)
        if self.ai_enabled:
            self.client = OpenAI(api_key=api_key)

    def get_latest_proposal_for_project(self, project_code):
        """Get the most recent proposal document for a project"""
        self.cursor.execute("""
            SELECT
                d.*,
                di.fee_amount,
                di.fee_currency,
                di.scope_summary,
                di.timeline,
                di.executive_summary
            FROM documents d
            LEFT JOIN document_intelligence di ON d.document_id = di.document_id
            WHERE d.project_code = ?
              AND d.document_type = 'proposal'
            ORDER BY d.modified_date DESC
            LIMIT 1
        """, (project_code,))

        return self.cursor.fetchone()

    def compare_proposals(self, project_code):
        """Compare all proposal versions for a project"""
        self.cursor.execute("""
            SELECT
                d.*,
                di.fee_amount,
                di.fee_currency,
                di.scope_summary,
                di.executive_summary
            FROM documents d
            LEFT JOIN document_intelligence di ON d.document_id = di.document_id
            WHERE d.project_code = ?
              AND d.document_type = 'proposal'
            ORDER BY d.modified_date ASC
        """, (project_code,))

        return self.cursor.fetchall()

    def search_by_fee_range(self, min_fee=None, max_fee=None):
        """Find proposals within a fee range"""
        query = """
            SELECT
                d.project_code,
                d.file_name,
                di.fee_amount,
                di.fee_currency
            FROM documents d
            JOIN document_intelligence di ON d.document_id = di.document_id
            WHERE d.document_type = 'proposal'
        """

        params = []
        if min_fee:
            query += " AND CAST(di.fee_amount AS REAL) >= ?"
            params.append(min_fee)
        if max_fee:
            query += " AND CAST(di.fee_amount AS REAL) <= ?"
            params.append(max_fee)

        query += " ORDER BY CAST(di.fee_amount AS REAL) DESC"

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def find_document(self, project_code, doc_type='proposal'):
        """Find specific document for a project"""
        self.cursor.execute("""
            SELECT * FROM documents
            WHERE project_code = ?
              AND document_type = ?
            ORDER BY modified_date DESC
            LIMIT 1
        """, (project_code, doc_type))

        return self.cursor.fetchone()

    def display_proposal(self, proposal, show_full_text=False):
        """Display proposal information"""
        print("\n" + "="*80)
        print(f"📄 {proposal['file_name']}")
        print("="*80)

        if proposal['project_code']:
            print(f"\n🔗 Project: {proposal['project_code']}")

        if proposal['document_date']:
            print(f"📅 Date: {proposal['document_date']}")
        else:
            modified = datetime.fromisoformat(proposal['modified_date'])
            print(f"📅 Modified: {modified.strftime('%Y-%m-%d')}")

        if proposal['fee_amount'] and proposal['fee_amount'] not in ['not provided', 'Not provided', 'N/A', 'not specified']:
            currency = proposal['fee_currency'] or 'USD'
            print(f"💰 Fee: {currency} {proposal['fee_amount']}")

        if proposal['executive_summary']:
            print(f"\n📋 SUMMARY:")
            print(f"{proposal['executive_summary']}")

        if proposal['scope_summary']:
            print(f"\n🎯 SCOPE:")
            print(f"{proposal['scope_summary']}")

        if proposal['timeline']:
            print(f"\n⏱️  TIMELINE:")
            print(f"{proposal['timeline']}")

        print(f"\n📂 FILE: {proposal['file_path']}")

        if show_full_text and proposal['text_content']:
            print(f"\n📖 FULL TEXT:")
            print("="*80)
            print(proposal['text_content'][:2000])  # First 2000 chars
            if len(proposal['text_content']) > 2000:
                print("\n... [truncated]")

        print("="*80)

    def compare_and_display(self, project_code):
        """Compare all proposal versions and show differences"""
        proposals = self.compare_proposals(project_code)

        if not proposals:
            print(f"✗ No proposals found for {project_code}")
            return

        print("\n" + "="*80)
        print(f"📊 PROPOSAL COMPARISON: {project_code}")
        print("="*80)

        for i, prop in enumerate(proposals, 1):
            print(f"\n{'='*80}")
            print(f"VERSION {i} - {prop['file_name']}")
            print(f"{'='*80}")

            modified = datetime.fromisoformat(prop['modified_date'])
            print(f"📅 Date: {modified.strftime('%Y-%m-%d')}")

            if prop['fee_amount'] and prop['fee_amount'] not in ['not provided', 'Not provided', 'N/A']:
                currency = prop['fee_currency'] or 'USD'
                print(f"💰 Fee: {currency} {prop['fee_amount']}")
            else:
                print(f"💰 Fee: Not specified")

            if prop['scope_summary']:
                print(f"\n🎯 Scope: {prop['scope_summary']}")

            if i > 1:
                # Compare with previous version
                prev = proposals[i-2]
                print(f"\n🔄 CHANGES FROM PREVIOUS VERSION:")

                if prop['fee_amount'] != prev['fee_amount']:
                    print(f"  • Fee changed: {prev['fee_amount']} → {prop['fee_amount']}")

                if prop['scope_summary'] != prev['scope_summary']:
                    print(f"  • Scope updated")

        print("\n" + "="*80)

def main():
    if len(sys.argv) < 2:
        print("""
Document Query Interface

Usage:
  python3 document_query.py <db_path> <command> [args]

Commands:
  latest <project_code>              - Show latest proposal for project
  compare <project_code>             - Compare all proposal versions
  find <project_code> [type]         - Find specific document (default: proposal)

Examples:
  python3 document_query.py database/bensley_master.db latest BK-074
  python3 document_query.py database/bensley_master.db compare BK-033
  python3 document_query.py database/bensley_master.db find BK-074 contract
        """)
        return

    db_path = sys.argv[1]
    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        return

    if len(sys.argv) < 3:
        print("✗ Please specify a command")
        return

    query = DocumentQuery(db_path)
    command = sys.argv[2].lower()

    if command == 'latest':
        if len(sys.argv) < 4:
            print("✗ Please specify project code")
            return

        project_code = sys.argv[3].upper()
        proposal = query.get_latest_proposal_for_project(project_code)

        if proposal:
            query.display_proposal(proposal)
        else:
            print(f"✗ No proposal found for {project_code}")

    elif command == 'compare':
        if len(sys.argv) < 4:
            print("✗ Please specify project code")
            return

        project_code = sys.argv[3].upper()
        query.compare_and_display(project_code)

    elif command == 'find':
        if len(sys.argv) < 4:
            print("✗ Please specify project code")
            return

        project_code = sys.argv[3].upper()
        doc_type = sys.argv[4].lower() if len(sys.argv) > 4 else 'proposal'

        doc = query.find_document(project_code, doc_type)
        if doc:
            query.display_proposal(doc)
        else:
            print(f"✗ No {doc_type} found for {project_code}")

if __name__ == "__main__":
    main()
