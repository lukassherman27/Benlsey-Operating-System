#!/usr/bin/env python3
"""
Query Brain - Natural Language Query System

Ask questions about your business data in plain English:
- "Show me all proposals from 2024"
- "Which clients have we contacted this month?"
- "Find all documents for BK-069"
- "What's the health score of active projects?"
- "What did the client say about the stone issue?" (uses meeting transcripts)

Works WITHOUT AI initially (pattern matching)
Can be enhanced WITH Claude API for smarter queries
"""

import sqlite3
import re
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

# Database path from environment or default
DB_PATH = os.getenv("DATABASE_PATH", "database/bensley_master.db")


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

    # =========================================================================
    # MEETING TRANSCRIPTS - Added for AI-powered context queries
    # =========================================================================

    def get_meeting_transcripts(self, project_code: str, limit: int = 5) -> list:
        """
        Get recent meeting transcripts for a project.

        Args:
            project_code: The project code (e.g., "22 BK-095")
            limit: Maximum number of transcripts to return

        Returns:
            List of transcript dictionaries with summary, key_points, action_items
        """
        try:
            self.cursor.execute("""
                SELECT
                    id,
                    audio_filename,
                    summary,
                    key_points,
                    action_items,
                    participants,
                    meeting_type,
                    sentiment,
                    processed_date,
                    recorded_date
                FROM meeting_transcripts
                WHERE detected_project_code = ?
                   OR detected_project_code LIKE ?
                   OR detected_project_code LIKE ?
                ORDER BY COALESCE(recorded_date, processed_date) DESC
                LIMIT ?
            """, (project_code, f"%{project_code}%", f"{project_code}%", limit))

            transcripts = []
            for row in self.cursor.fetchall():
                transcripts.append({
                    "id": row[0],
                    "filename": row[1],
                    "summary": row[2],
                    "key_points": self._safe_json_loads(row[3], []),
                    "action_items": self._safe_json_loads(row[4], []),
                    "participants": self._safe_json_loads(row[5], []),
                    "type": row[6],
                    "sentiment": row[7],
                    "date": row[8] or row[9]
                })

            return transcripts
        except Exception as e:
            print(f"Error fetching meeting transcripts: {e}")
            return []

    def _safe_json_loads(self, value, default):
        """Safely parse JSON string, return default if fails"""
        if not value:
            return default
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default

    def get_project_context(self, project_code: str) -> dict:
        """
        Gather all context for a project to answer queries.
        Used for AI-powered queries with full context.

        Args:
            project_code: The project code

        Returns:
            Dictionary with project info, emails, transcripts, etc.
        """
        context = {
            "project_info": self._get_project_info(project_code),
            "recent_emails": self._get_recent_emails(project_code),
            "meeting_transcripts": self.get_meeting_transcripts(project_code),
            "rfis": self._get_rfis(project_code),
            "invoices": self._get_invoices(project_code),
        }
        return context

    def _get_project_info(self, project_code: str) -> dict:
        """Get basic project/proposal info"""
        try:
            self.cursor.execute("""
                SELECT
                    project_code, project_name, status, health_score,
                    days_since_contact, is_active_project, client_name
                FROM proposals
                WHERE project_code = ? OR project_code LIKE ?
                LIMIT 1
            """, (project_code, f"%{project_code}%"))
            row = self.cursor.fetchone()
            if row:
                return dict(row)
            return {}
        except Exception:
            return {}

    def _get_recent_emails(self, project_code: str, limit: int = 10) -> list:
        """Get recent emails for a project"""
        try:
            self.cursor.execute("""
                SELECT
                    e.subject, e.sender_email, e.date, e.body_preview
                FROM emails e
                LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
                LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
                WHERE p.project_code = ? OR p.project_code LIKE ?
                ORDER BY e.date DESC
                LIMIT ?
            """, (project_code, f"%{project_code}%", limit))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception:
            return []

    def _get_rfis(self, project_code: str) -> list:
        """Get RFIs for a project"""
        try:
            self.cursor.execute("""
                SELECT rfi_number, subject, status, created_date, due_date
                FROM rfis
                WHERE project_code = ? OR project_code LIKE ?
                ORDER BY created_date DESC
                LIMIT 10
            """, (project_code, f"%{project_code}%"))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception:
            return []

    def _get_invoices(self, project_code: str) -> list:
        """Get invoices for a project"""
        try:
            self.cursor.execute("""
                SELECT invoice_number, amount, status, invoice_date, due_date
                FROM invoices
                WHERE project_code = ? OR project_code LIKE ?
                ORDER BY invoice_date DESC
                LIMIT 10
            """, (project_code, f"%{project_code}%"))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception:
            return []

    # =========================================================================
    # PROMPT FORMATTING - For AI-powered queries
    # =========================================================================

    def format_transcripts_for_prompt(self, transcripts: list) -> str:
        """Format meeting transcripts for inclusion in AI prompt."""
        if not transcripts:
            return "No meeting transcripts available."

        lines = []
        for t in transcripts:
            lines.append(f"### Meeting: {t['filename']} ({t['date']})")
            lines.append(f"Type: {t['type']} | Sentiment: {t['sentiment']}")
            if t['summary']:
                lines.append(f"Summary: {t['summary']}")
            if t['key_points']:
                lines.append("Key Points:")
                for point in t['key_points']:
                    lines.append(f"  - {point}")
            if t['action_items']:
                lines.append("Action Items:")
                for item in t['action_items']:
                    # Handle both string and dict action items
                    if isinstance(item, dict):
                        task = item.get('task') or item.get('description', str(item))
                    else:
                        task = str(item)
                    lines.append(f"  - {task}")
            lines.append("")

        return "\n".join(lines)

    def build_query_prompt(self, query: str, context: dict) -> str:
        """
        Build prompt for Claude/GPT with all available context.

        Args:
            query: The user's question
            context: Dictionary from get_project_context()

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a helpful assistant for Bensley Design Studios.
Answer the following question based on the project data provided.

## Question:
{query}

## Project Information:
{json.dumps(context.get('project_info', {}), indent=2)}

## Recent Emails ({len(context.get('recent_emails', []))} total):
{self._format_emails_for_prompt(context.get('recent_emails', []))}

## Meeting Transcripts ({len(context.get('meeting_transcripts', []))} total):
{self.format_transcripts_for_prompt(context.get('meeting_transcripts', []))}

## Open RFIs ({len(context.get('rfis', []))} total):
{self._format_rfis_for_prompt(context.get('rfis', []))}

## Invoices ({len(context.get('invoices', []))} total):
{self._format_invoices_for_prompt(context.get('invoices', []))}

Answer the question based on this data. If you cannot find relevant information,
say so clearly. Reference specific emails or meetings when possible.
"""
        return prompt

    def _format_emails_for_prompt(self, emails: list) -> str:
        """Format emails for prompt"""
        if not emails:
            return "No recent emails."
        lines = []
        for e in emails[:5]:
            lines.append(f"- {e.get('date', 'N/A')}: {e.get('subject', 'No subject')} (from: {e.get('sender_email', 'unknown')})")
        return "\n".join(lines)

    def _format_rfis_for_prompt(self, rfis: list) -> str:
        """Format RFIs for prompt"""
        if not rfis:
            return "No RFIs."
        lines = []
        for r in rfis:
            lines.append(f"- RFI #{r.get('rfi_number', 'N/A')}: {r.get('subject', 'No subject')} - Status: {r.get('status', 'unknown')}")
        return "\n".join(lines)

    def _format_invoices_for_prompt(self, invoices: list) -> str:
        """Format invoices for prompt"""
        if not invoices:
            return "No invoices."
        lines = []
        for i in invoices:
            lines.append(f"- Invoice #{i.get('invoice_number', 'N/A')}: ${i.get('amount', 0):,.2f} - Status: {i.get('status', 'unknown')}")
        return "\n".join(lines)


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
