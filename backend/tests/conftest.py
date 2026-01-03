"""
Pytest configuration and fixtures for backend tests.

Provides:
    - FastAPI TestClient for API testing
    - Test database connection
    - Common fixtures for proposals, emails, etc.
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add backend and project root to path
backend_path = Path(__file__).parent.parent
project_root = backend_path.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(project_root))

# Set test database path (uses production db for now - read-only tests)
os.environ.setdefault(
    'DATABASE_PATH',
    str(project_root / "database" / "bensley_master.db")
)

from api.main import app
from api.dependencies import DB_PATH


@pytest.fixture(scope="session")
def client():
    """
    FastAPI TestClient fixture.

    Scoped to session for performance - reused across all tests.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def db_path():
    """Database path fixture."""
    return DB_PATH


@pytest.fixture
def sample_proposal_code():
    """A known proposal code for testing."""
    return "25 BK-033"
