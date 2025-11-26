"""
Pytest configuration and shared fixtures for Bensley Operations Platform tests.
"""

import os
import sys
import sqlite3
import tempfile
from pathlib import Path

import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def database_path():
    """Return the path to the main database."""
    return PROJECT_ROOT / "database" / "bensley_master.db"


@pytest.fixture(scope="function")
def temp_database():
    """
    Create a temporary SQLite database for testing.
    Automatically cleaned up after test.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name

    # Create basic schema
    conn = sqlite3.connect(temp_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY,
            project_code TEXT UNIQUE,
            project_title TEXT,
            status TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS proposals (
            proposal_id INTEGER PRIMARY KEY,
            project_code TEXT,
            status TEXT,
            health_score REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            email_id INTEGER PRIMARY KEY,
            subject TEXT,
            sender TEXT,
            received_date TEXT
        )
    """)
    conn.commit()
    conn.close()

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture(scope="function")
def db_connection(temp_database):
    """
    Provide a database connection to the temp database.
    """
    conn = sqlite3.connect(temp_database)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def sample_project():
    """Sample project data for testing."""
    return {
        "project_code": "25 BK-TEST",
        "project_title": "Test Project",
        "status": "Active",
        "client_id": 1,
    }


@pytest.fixture(scope="session")
def sample_proposal():
    """Sample proposal data for testing."""
    return {
        "project_code": "25 BK-TEST",
        "status": "Proposal Sent",
        "health_score": 75.0,
    }


@pytest.fixture(scope="session")
def sample_email():
    """Sample email data for testing."""
    return {
        "subject": "RE: Project Update",
        "sender": "client@example.com",
        "received_date": "2025-11-26",
        "body": "Test email body content.",
    }


# Environment setup
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, temp_database):
    """
    Set up test environment variables.
    Uses temp database by default.
    """
    monkeypatch.setenv("DATABASE_PATH", temp_database)
    monkeypatch.setenv("TESTING", "true")
