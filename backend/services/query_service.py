"""
Query Service

Wraps the QueryBrain natural language query system.
Provides service-level interface for natural language queries.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path to import query_brain
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from query_brain import QueryBrain
from .base_service import BaseService


class QueryService(BaseService):
    """Service for natural language queries"""

    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        self.query_brain = QueryBrain(str(self.db_path))

    def query(self, question: str) -> Dict[str, Any]:
        """
        Execute a natural language query

        Args:
            question: Natural language question

        Returns:
            Dict with query results and metadata
        """
        try:
            # Parse and execute query
            sql, params = self.query_brain.parse_query(question)

            # Execute the query
            results = self.execute_query(sql, params)

            return {
                'success': True,
                'question': question,
                'results': results,
                'count': len(results),
                'sql': sql,  # Include for debugging/transparency
                'params': params
            }

        except Exception as e:
            return {
                'success': False,
                'question': question,
                'error': str(e),
                'results': []
            }

    def get_query_suggestions(self) -> List[str]:
        """Get example query suggestions for users"""
        return [
            "Show me all proposals from 2024",
            "Find all documents for BK-069",
            "Which proposals have low health scores?",
            "Show me emails from this month",
            "List all contacts",
            "Find proposals for hotel clients",
            "Show me active projects",
            "What emails are unread?",
            "Find all contracts",
            "Show proposals that need follow-up"
        ]

    def get_supported_query_types(self) -> List[Dict[str, Any]]:
        """Get information about supported query types"""
        return [
            {
                'type': 'proposals',
                'description': 'Query proposals and projects',
                'examples': [
                    'Show me all proposals',
                    'Find active projects',
                    'Which proposals are from 2024?'
                ],
                'filters': ['year', 'status', 'project_code', 'active/pending/completed']
            },
            {
                'type': 'emails',
                'description': 'Query emails and communication',
                'examples': [
                    'Show me emails from this month',
                    'Find emails for BK-069',
                    'What are the unread emails?'
                ],
                'filters': ['date', 'project_code', 'month/week/today']
            },
            {
                'type': 'documents',
                'description': 'Query documents and files',
                'examples': [
                    'Find all documents for BK-069',
                    'Show me PDFs',
                    'What documents were modified this week?'
                ],
                'filters': ['project_code', 'file_type']
            },
            {
                'type': 'contacts',
                'description': 'Query contacts and people',
                'examples': [
                    'List all contacts',
                    'Find contacts for hotel projects'
                ],
                'filters': ['email_count', 'first_seen/last_seen']
            }
        ]
