"""
Base Service Class

Provides database connection and common utilities for all services.
All service classes should inherit from this.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()


class BaseService:
    """Base class for all data services"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize service with database connection

        Args:
            db_path: Path to SQLite database (defaults to DATABASE_PATH from .env)
        """
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', '~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db')

        self.db_path = Path(db_path).expanduser()

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        # Connection will be created per-request for thread safety
        self._conn = None

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections

        Usage:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, sql: str, params: tuple = (), fetch_one: bool = False) -> Any:
        """
        Execute a SELECT query and return results

        Args:
            sql: SQL query string
            params: Query parameters
            fetch_one: If True, return single row. If False, return all rows.

        Returns:
            Single row dict (if fetch_one=True) or list of row dicts
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)

            if fetch_one:
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

    def execute_update(self, sql: str, params: tuple = ()) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query

        Args:
            sql: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount

    def execute_many(self, sql: str, params_list: List[tuple]) -> int:
        """
        Execute multiple INSERT/UPDATE queries

        Args:
            sql: SQL query string
            params_list: List of parameter tuples

        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params_list)
            conn.commit()
            return cursor.rowcount

    def get_last_insert_id(self) -> int:
        """Get the ID of the last inserted row"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_insert_rowid()")
            return cursor.fetchone()[0]

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        sql = """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type='table' AND name=?
        """
        result = self.execute_query(sql, (table_name,), fetch_one=True)
        return result['COUNT(*)'] > 0

    def count_rows(self, table_name: str, where: str = None, params: tuple = ()) -> int:
        """
        Count rows in a table

        Args:
            table_name: Name of table
            where: Optional WHERE clause (without 'WHERE' keyword)
            params: Parameters for WHERE clause

        Returns:
            Row count
        """
        sql = f"SELECT COUNT(*) as count FROM {table_name}"
        if where:
            sql += f" WHERE {where}"

        result = self.execute_query(sql, params, fetch_one=True)
        return result['count']

    def validate_sort_column(self, column: str, allowed_columns: List[str]) -> str:
        """
        Validate sort column against whitelist to prevent SQL injection

        Args:
            column: Column name to sort by
            allowed_columns: List of allowed column names

        Returns:
            Validated column name

        Raises:
            ValueError: If column is not in whitelist
        """
        if column not in allowed_columns:
            raise ValueError(f"Invalid sort column: {column}. Allowed: {', '.join(allowed_columns)}")
        return column

    def validate_sort_order(self, order: str) -> str:
        """
        Validate sort order to prevent SQL injection

        Args:
            order: Sort order ('ASC' or 'DESC')

        Returns:
            Validated sort order (uppercase)

        Raises:
            ValueError: If order is not 'ASC' or 'DESC'
        """
        order_upper = order.upper()
        if order_upper not in ['ASC', 'DESC']:
            raise ValueError(f"Invalid sort order: {order}. Must be 'ASC' or 'DESC'")
        return order_upper

    def paginate(self, sql: str, params: tuple = (), page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Paginate query results

        Args:
            sql: Base SQL query (without LIMIT/OFFSET)
            params: Query parameters
            page: Page number (1-indexed)
            per_page: Results per page

        Returns:
            Dict with 'items', 'total', 'page', 'per_page', 'pages'
        """
        # Get total count
        count_sql = f"SELECT COUNT(*) as total FROM ({sql})"
        total = self.execute_query(count_sql, params, fetch_one=True)['total']

        # Get paginated results
        offset = (page - 1) * per_page
        paginated_sql = f"{sql} LIMIT ? OFFSET ?"
        items = self.execute_query(paginated_sql, params + (per_page, offset))

        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page  # Ceiling division
        }
