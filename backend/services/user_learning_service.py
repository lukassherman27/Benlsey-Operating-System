"""
User Learning Service - Learn user preferences and patterns

Tracks and learns:
- Query patterns (what Bill checks every Monday)
- Preferred metrics and filters
- Dashboard usage patterns
- Suggestion acceptance rates

Can suggest automations like:
- "Would you like a weekly follow-up summary email?"
- "You check 'Needs Follow-up' every Monday - want me to send a reminder?"

Created: 2025-11-26 by Agent 5 (Bensley Brain Intelligence)
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import Counter

DB_PATH = os.getenv("DATABASE_PATH", "database/bensley_master.db")


class UserLearningService:
    """Learn user preferences from their behavior"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # QUERY LOGGING
    # =========================================================================

    def log_query(self, query_text: str, query_type: str = None,
                  filters_used: Dict = None, results_count: int = 0,
                  execution_time_ms: int = 0, user_id: str = 'bill') -> int:
        """
        Log a user query for pattern analysis.

        Args:
            query_text: The natural language query
            query_type: Category (proposal, project, meeting, email, etc.)
            filters_used: Dict of filters applied
            results_count: Number of results returned
            execution_time_ms: Query execution time
            user_id: User identifier

        Returns:
            Log entry ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now()

        try:
            cursor.execute("""
                INSERT INTO user_query_log (
                    query_text, query_type, filters_used, results_count,
                    execution_time_ms, user_id, query_timestamp,
                    day_of_week, hour_of_day
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_text,
                query_type,
                json.dumps(filters_used) if filters_used else None,
                results_count,
                execution_time_ms,
                user_id,
                now.isoformat(),
                now.weekday(),  # 0=Monday
                now.hour
            ))

            log_id = cursor.lastrowid
            conn.commit()
            return log_id

        finally:
            conn.close()

    # =========================================================================
    # PATTERN DETECTION
    # =========================================================================

    def analyze_query_patterns(self, user_id: str = 'bill', days: int = 30) -> Dict[str, Any]:
        """
        Analyze query patterns for a user.

        Returns insights about:
        - Most common query types
        - Day/time patterns
        - Preferred filters
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get query history
        cursor.execute("""
            SELECT query_text, query_type, filters_used, day_of_week, hour_of_day
            FROM user_query_log
            WHERE user_id = ?
            AND query_timestamp > datetime('now', '-' || ? || ' days')
            ORDER BY query_timestamp DESC
        """, (user_id, days))

        queries = [dict(row) for row in cursor.fetchall()]
        conn.close()

        if not queries:
            return {'patterns': [], 'suggestions': []}

        # Analyze patterns
        patterns = []
        suggestions = []

        # 1. Day of week patterns
        day_counts = Counter(q['day_of_week'] for q in queries)
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        most_active_day = max(day_counts, key=day_counts.get) if day_counts else None
        if most_active_day is not None and day_counts[most_active_day] >= 3:
            patterns.append({
                'type': 'weekly_day_preference',
                'description': f'Most active on {day_names[most_active_day]}',
                'day': most_active_day,
                'day_name': day_names[most_active_day],
                'count': day_counts[most_active_day]
            })

        # 2. Time of day patterns
        hour_counts = Counter(q['hour_of_day'] for q in queries)
        peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None
        if peak_hour is not None and hour_counts[peak_hour] >= 3:
            patterns.append({
                'type': 'time_preference',
                'description': f'Usually queries around {peak_hour}:00',
                'hour': peak_hour,
                'count': hour_counts[peak_hour]
            })

        # 3. Query type patterns
        type_counts = Counter(q['query_type'] for q in queries if q['query_type'])
        if type_counts:
            top_types = type_counts.most_common(3)
            patterns.append({
                'type': 'query_type_preference',
                'description': f'Most common queries: {", ".join([t[0] for t in top_types])}',
                'types': dict(top_types)
            })

        # 4. Detect repetitive patterns (same query on same day/time)
        query_day_combos = Counter(
            (q['query_type'], q['day_of_week'])
            for q in queries if q['query_type']
        )

        for (qtype, day), count in query_day_combos.items():
            if count >= 2 and qtype:
                patterns.append({
                    'type': 'recurring_check',
                    'description': f'Checks {qtype} on {day_names[day]}s ({count} times)',
                    'query_type': qtype,
                    'day': day,
                    'day_name': day_names[day],
                    'occurrences': count
                })

                # Generate suggestion
                suggestions.append({
                    'type': 'automation',
                    'title': f'Weekly {qtype.title()} Summary',
                    'description': f'You check {qtype} every {day_names[day]}. Would you like an automatic summary email?',
                    'trigger': {
                        'day': day,
                        'query_type': qtype
                    }
                })

        # 5. Keyword analysis
        words = []
        for q in queries:
            words.extend(q['query_text'].lower().split())

        # Filter common words
        stopwords = {'show', 'me', 'all', 'the', 'a', 'an', 'from', 'for', 'with', 'what', 'which', 'are', 'is'}
        filtered_words = [w for w in words if w not in stopwords and len(w) > 2]
        word_counts = Counter(filtered_words)

        top_keywords = word_counts.most_common(10)
        if top_keywords:
            patterns.append({
                'type': 'keyword_interest',
                'description': f'Frequently searches for: {", ".join([w[0] for w in top_keywords[:5]])}',
                'keywords': dict(top_keywords)
            })

        return {
            'total_queries': len(queries),
            'analysis_period_days': days,
            'patterns': patterns,
            'suggestions': suggestions
        }

    # =========================================================================
    # PATTERN STORAGE
    # =========================================================================

    def save_learned_pattern(self, user_id: str, pattern_type: str,
                             pattern_description: str, pattern_data: Dict,
                             confidence: float = 0.5) -> int:
        """Save a learned pattern"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Check if pattern already exists
            cursor.execute("""
                SELECT pattern_id, occurrences FROM learned_user_patterns
                WHERE user_id = ? AND pattern_type = ?
                AND pattern_data = ?
            """, (user_id, pattern_type, json.dumps(pattern_data)))

            existing = cursor.fetchone()

            if existing:
                # Update occurrence count
                cursor.execute("""
                    UPDATE learned_user_patterns
                    SET occurrences = occurrences + 1,
                        confidence = ?,
                        last_seen = datetime('now')
                    WHERE pattern_id = ?
                """, (min(confidence + 0.1, 1.0), existing['pattern_id']))
                pattern_id = existing['pattern_id']
            else:
                # Insert new pattern
                cursor.execute("""
                    INSERT INTO learned_user_patterns (
                        user_id, pattern_type, pattern_description,
                        pattern_data, confidence, occurrences, last_seen
                    ) VALUES (?, ?, ?, ?, ?, 1, datetime('now'))
                """, (user_id, pattern_type, pattern_description,
                      json.dumps(pattern_data), confidence))
                pattern_id = cursor.lastrowid

            conn.commit()
            return pattern_id

        finally:
            conn.close()

    def get_active_patterns(self, user_id: str = 'bill') -> List[Dict]:
        """Get all active learned patterns for a user"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM learned_user_patterns
            WHERE user_id = ?
            AND confidence >= 0.5
            ORDER BY confidence DESC, occurrences DESC
        """, (user_id,))

        patterns = []
        for row in cursor.fetchall():
            p = dict(row)
            if p.get('pattern_data'):
                try:
                    p['pattern_data'] = json.loads(p['pattern_data'])
                except (json.JSONDecodeError, TypeError):
                    pass
            patterns.append(p)

        conn.close()
        return patterns

    # =========================================================================
    # SUGGESTION GENERATION
    # =========================================================================

    def generate_suggestions(self, user_id: str = 'bill') -> List[Dict]:
        """
        Generate personalized suggestions based on learned patterns.
        """
        patterns = self.get_active_patterns(user_id)
        analysis = self.analyze_query_patterns(user_id)

        suggestions = analysis.get('suggestions', [])

        # Add pattern-based suggestions
        for pattern in patterns:
            ptype = pattern.get('pattern_type')
            pdata = pattern.get('pattern_data', {})

            if ptype == 'recurring_check' and pattern.get('occurrences', 0) >= 3:
                suggestions.append({
                    'type': 'scheduled_report',
                    'title': f'Automated {pdata.get("query_type", "").title()} Report',
                    'description': f'Based on your pattern, you might want a scheduled report',
                    'confidence': pattern.get('confidence', 0.5),
                    'pattern_id': pattern.get('pattern_id')
                })

            if ptype == 'keyword_interest':
                keywords = list(pdata.get('keywords', {}).keys())[:3]
                if keywords:
                    suggestions.append({
                        'type': 'alert',
                        'title': f'Alert for {", ".join(keywords)}',
                        'description': f'Get notified when emails mention these topics',
                        'keywords': keywords
                    })

        return suggestions

    def record_suggestion_response(self, pattern_id: int, accepted: bool) -> None:
        """Record whether user accepted or rejected a suggestion"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE learned_user_patterns
                SET suggestion_made = 1,
                    suggestion_accepted = ?
                WHERE pattern_id = ?
            """, (1 if accepted else 0, pattern_id))

            # Adjust confidence based on response
            if accepted:
                cursor.execute("""
                    UPDATE learned_user_patterns
                    SET confidence = MIN(confidence + 0.1, 1.0)
                    WHERE pattern_id = ?
                """, (pattern_id,))
            else:
                cursor.execute("""
                    UPDATE learned_user_patterns
                    SET confidence = MAX(confidence - 0.2, 0)
                    WHERE pattern_id = ?
                """, (pattern_id,))

            conn.commit()

        finally:
            conn.close()


# CLI for testing
if __name__ == '__main__':
    import sys

    service = UserLearningService()

    if len(sys.argv) > 1 and sys.argv[1] == '--analyze':
        user_id = sys.argv[2] if len(sys.argv) > 2 else 'bill'
        print(f"\n📊 Analyzing patterns for user: {user_id}\n")

        analysis = service.analyze_query_patterns(user_id)

        print(f"Total queries in last 30 days: {analysis['total_queries']}")
        print("\n=== PATTERNS DETECTED ===\n")

        for p in analysis['patterns']:
            print(f"  [{p['type']}] {p['description']}")

        if analysis['suggestions']:
            print("\n=== SUGGESTIONS ===\n")
            for s in analysis['suggestions']:
                print(f"  💡 {s['title']}")
                print(f"     {s['description']}")

    elif len(sys.argv) > 1 and sys.argv[1] == '--log':
        # Log a test query
        query = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else 'Show me proposals'
        log_id = service.log_query(query, query_type='proposal')
        print(f"Logged query (ID: {log_id}): {query}")

    else:
        print("Usage:")
        print("  python user_learning_service.py --analyze [user_id]  # Analyze patterns")
        print("  python user_learning_service.py --log 'query text'   # Log a query")
