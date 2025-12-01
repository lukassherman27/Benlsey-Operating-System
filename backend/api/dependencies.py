"""
API Dependencies - Shared dependencies for all routers

Usage:
    from api.dependencies import get_db, DB_PATH

    @router.get("/endpoint")
    async def endpoint(db = Depends(get_db)):
        ...
"""

import os
import sqlite3
from pathlib import Path
from typing import Generator
from contextlib import contextmanager

# Database path - use environment variable with fallback
DB_PATH = os.getenv(
    'BENSLEY_DB_PATH',
    os.path.join(
        Path(__file__).parent.parent.parent,
        "database",
        "bensley_master.db"
    )
)


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Database dependency for FastAPI endpoints.

    Yields a SQLite connection with Row factory enabled.
    Connection is automatically closed when the request completes.

    Usage:
        @router.get("/items")
        async def get_items(db = Depends(get_db)):
            cursor = db.cursor()
            cursor.execute("SELECT * FROM items")
            return cursor.fetchall()
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_db_context():
    """
    Context manager version for non-FastAPI use (background tasks, services).

    Usage:
        with get_db_context() as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM items")
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_db_connection() -> sqlite3.Connection:
    """
    Get a raw database connection (caller responsible for closing).

    Prefer get_db() with Depends() or get_db_context() instead.
    This is for backward compatibility with existing code.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
