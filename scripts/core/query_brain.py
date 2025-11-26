#!/usr/bin/env python3
"""
Query Brain - Natural Language Query System

Ask questions about your business data in plain English:
- "Show me all proposals from 2024"
- "Which clients have we contacted this month?"
- "Find all documents for BK-069"
- "What's the health score of active projects?"

Works WITHOUT AI initially (pattern matching)
Can be enhanced WITH Claude API for smarter queries
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime, timedelta
import json


class QueryBrain:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def parse_query(self, question):
        """Parse natural language question into SQL query"""
        question = question.lower().strip()

        # Detect what they're asking about
        query_type = self._detect_query_type(question)
        filters = self._extract_filters(question)

        return self._build_sql_query(query_type, filters)

    def _detect_query_type(self, question):
        """Detect what type of data they're asking about"""

        # Proposals
        if any(word in question for word in ['proposal', 'proposals', 'project', 'projects']):
            if 'health' in question or 'score' in question:
                return 'proposal_health'
            if 'active' in question:
                return 'active_projects'
            if 'status' in question:
                return 'proposal_status'
            return 'proposals'

        # Emails
        if any(word in question for word in ['email', 'emails', 'message', 'contacted', 'communication']):
            if 'unread' in question or 'new' in question:
                return 'unread_emails'
            return 'emails'

        # Documents
        if any(word in question for word in ['document', 'documents', 'file', 'files', 'pdf']):
            return 'documents'

        # Contacts
        if any(word in question for word in ['contact', 'contacts', 'people', 'client', 'clients']):
            return 'contacts'

        # Default
        return 'proposals'

    def _extract_filters(self, question):
        """Extract filters from the question"""
        filters = {
            'date_range': None,
            'project_code': None,
            'client': None,
            'status': None,
            'year': None,
            'month': None,
            'limit': 20
        }

        # Extract year
        year_match = re.search(r'\b(202[0-9])\b', question)
        if year_match:
            filters['year'] = int(year_match.group(1))

        # Extract project code (BK-XXX format)
        code_match = re.search(r'\b(bk-?\d{3,4})\b', question, re.IGNORECASE)
        if code_match:
            filters['project_code'] = code_match.group(1).upper()

        # Extract time periods
        if 'this month' in question or 'current month' in question:
            filters['month'] = datetime.now().month
            filters['year'] = datetime.now().year

        if 'this week' in question:
            week_ago = datetime.now() - timedelta(days=7)
            filters['date_range'] = ('>=', week_ago.strftime('%Y-%m-%d'))

        if 'today' in question:
            filters['date_range'] = ('>=', datetime.now().strftime('%Y-%m-%d'))

        # Extract status
        if 'active' in question:
            filters['status'] = 'active'
        if 'pending' in question:
            filters['status'] = 'pending'
        if 'completed' in question or 'done' in question:
            filters['status'] = 'completed'

        # Extract limit
        limit_match = re.search(r'\b(\d+)\s+(result|proposal|email|document|contact)', question)
        if limit_match:
            filters['limit'] = int(limit_match.group(1))
        elif 'all' in question:
            filters['limit'] = 10000

        return filters

    def _build_sql_query(self, query_type, filters):
        """Build SQL query based on type and filters"""

        # PROPOSALS
        if query_type == 'proposals':
            query = """
                SELECT
                    project_code,
                    project_name,
                    status,
                    health_score,
                    days_since_contact,
                    is_active_project
                FROM proposals
                WHERE 1=1
            """
            params = []

            if filters['project_code']:
                query += " AND project_code LIKE ?"
                params.append(f"%{filters['project_code']}%")

            if filters['year']:
                query += " AND strftime('%Y', created_at) = ?"
                params.append(str(filters['year']))

            if filters['status']:
                if filters['status'] == 'active':
                    query += " AND is_active_project = 1"
                else:
                    query += " AND status = ?"
                    params.append(filters['status'])

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(filters['limit'])

            return query, params

        # PROPOSAL HEALTH
        elif query_type == 'proposal_health':
            query = """
                SELECT
                    project_code,
                    project_name,
                    health_score,
                    days_since_contact,
                    status
                FROM proposals
                WHERE health_score IS NOT NULL
            """
            params = []

            if filters['status'] == 'active':
                query += " AND is_active_project = 1"

            query += " ORDER BY health_score ASC, days_since_contact DESC LIMIT ?"
            params.append(filters['limit'])

            return query, params

        # ACTIVE PROJECTS
        elif query_type == 'active_projects':
            query = """
                SELECT
                    project_code,
                    project_name,
                    status,
                    health_score,
                    days_since_contact
                FROM proposals
                WHERE is_active_project = 1
                ORDER BY health_score ASC
                LIMIT ?
            """
            return query, [filters['limit']]

        # EMAILS
        elif query_type == 'emails':
            query = """
                SELECT
                    e.subject,
                    e.sender_email,
                    e.date,
                    p.project_code
                FROM emails e
                LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
                LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
                WHERE 1=1
            """
            params = []

            if filters['project_code']:
                query += " AND p.project_code LIKE ?"
                params.append(f"%{filters['project_code']}%")

            if filters['date_range']:
                operator, date_val = filters['date_range']
                query += f" AND e.date {operator} ?"
                params.append(date_val)

            if filters['month'] and filters['year']:
                query += " AND strftime('%Y', e.date) = ? AND strftime('%m', e.date) = ?"
                params.append(str(filters['year']))
                params.append(f"{filters['month']:02d}")

            query += " ORDER BY e.date DESC LIMIT ?"
            params.append(filters['limit'])

            return query, params

        # DOCUMENTS
        elif query_type == 'documents':
            query = """
                SELECT
                    d.file_name,
                    d.file_path,
                    d.document_type,
                    d.file_size,
                    d.modified_date,
                    d.project_code
                FROM documents d
                WHERE 1=1
            """
            params = []

            if filters['project_code']:
                query += " AND d.project_code LIKE ?"
                params.append(f"%{filters['project_code']}%")

            query += " ORDER BY d.modified_date DESC LIMIT ?"
            params.append(filters['limit'])

            return query, params

        # CONTACTS
        elif query_type == 'contacts':
            query = """
                SELECT
                    email,
                    name,
                    email_count,
                    first_seen,
                    last_seen
                FROM contacts_only
                WHERE 1=1
                ORDER BY email_count DESC
                LIMIT ?
            """
            return query, [filters['limit']]

        # Default
        return "SELECT 'Unknown query type' as message", []

    def query(self, question):
        """Execute natural language query and return results"""
        print(f"\n🔍 Query: {question}")
        print("-" * 80)

        try:
            sql, params = self.parse_query(question)

            # Execute query
            self.cursor.execute(sql, params)
            results = self.cursor.fetchall()

            if not results:
                print("No results found.")
                return []

            # Display results
            self._display_results(results)

            return [dict(row) for row in results]

        except Exception as e:
            print(f"❌ Error: {e}")
            print(f"SQL: {sql}")
            print(f"Params: {params}")
            return []

    def _display_results(self, results):
        """Display results in a nice format"""
        if not results:
            return

        # Get column names
        columns = results[0].keys()

        print(f"\n✅ Found {len(results)} result(s)\n")

        # Display as table
        for i, row in enumerate(results, 1):
            print(f"Result {i}:")
            for col in columns:
                value = row[col]
                if value is not None:
                    print(f"  {col}: {value}")
            print()

    def interactive(self):
        """Interactive query mode"""
        print("="*80)
        print("🧠 BENSLEY BRAIN - QUERY SYSTEM")
        print("="*80)
        print("\nAsk questions in plain English. Examples:")
        print("  • Show me all proposals from 2024")
        print("  • Find all documents for BK-069")
        print("  • Which proposals have low health scores?")
        print("  • Show me emails from this month")
        print("  • List all contacts")
        print("\nType 'exit' to quit\n")

        while True:
            try:
                question = input("❓ Question: ").strip()

                if not question:
                    continue

                if question.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!")
                    break

                self.query(question)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")

    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 query_brain.py <database_path> [question]")
        print("\nExamples:")
        print('  python3 query_brain.py ~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db')
        print('  python3 query_brain.py ~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db "Show me all proposals from 2024"')
        sys.exit(1)

    db_path = sys.argv[1]
    brain = QueryBrain(db_path)

    # If question provided as argument, run it
    if len(sys.argv) > 2:
        question = ' '.join(sys.argv[2:])
        brain.query(question)
    else:
        # Otherwise, start interactive mode
        brain.interactive()
