"""
Smoke tests - Basic sanity checks that the system works.
These should pass quickly and catch obvious breakages.
"""

import os
import sqlite3
from pathlib import Path


class TestProjectStructure:
    """Test that project structure is correct."""

    def test_required_files_exist(self, project_root):
        """Check that essential files exist."""
        required_files = [
            "CLAUDE.md",
            "README.md",
            "requirements.txt",
            "Makefile",
            "pyproject.toml",
        ]
        for filename in required_files:
            filepath = project_root / filename
            assert filepath.exists(), f"Required file missing: {filename}"

    def test_required_directories_exist(self, project_root):
        """Check that essential directories exist."""
        required_dirs = [
            "backend",
            "backend/api",
            "backend/services",
            "frontend",
            "database",
            "scripts/core",
            "docs",
            "tests",
        ]
        for dirname in required_dirs:
            dirpath = project_root / dirname
            assert dirpath.exists(), f"Required directory missing: {dirname}"

    def test_no_files_at_root_that_shouldnt_be(self, project_root):
        """Check that root isn't polluted with scripts/docs."""
        # These patterns shouldn't be at root
        bad_patterns = [
            "import_*.py",
            "fix_*.py",
            "audit_*.py",
            "SESSION_*.md",
            "AGENT*_AUDIT*.md",
        ]
        import glob

        for pattern in bad_patterns:
            matches = list(project_root.glob(pattern))
            assert len(matches) == 0, f"Unexpected files at root matching {pattern}: {matches}"


class TestDatabase:
    """Test database connectivity and schema."""

    def test_main_database_exists(self, database_path):
        """Check that the main database file exists."""
        assert database_path.exists(), "Main database file not found"

    def test_database_has_core_tables(self, database_path):
        """Check that core tables exist in the database."""
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        core_tables = ["projects", "proposals", "invoices", "emails", "contacts"]

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        for table in core_tables:
            assert table in existing_tables, f"Core table missing: {table}"

        conn.close()

    def test_database_has_data(self, database_path):
        """Check that database has some data."""
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        assert project_count > 0, "No projects in database"

        cursor.execute("SELECT COUNT(*) FROM proposals")
        proposal_count = cursor.fetchone()[0]
        assert proposal_count > 0, "No proposals in database"

        conn.close()


class TestBackendImports:
    """Test that backend modules can be imported."""

    def test_import_main_app(self):
        """Test that FastAPI app can be imported."""
        try:
            from backend.api.main import app

            assert app is not None
        except ImportError as e:
            # Allow import to fail if dependencies missing in CI
            if "No module named" in str(e):
                import pytest

                pytest.skip(f"Skipping due to missing dependency: {e}")
            raise

    def test_import_core_services(self):
        """Test that core services can be imported."""
        services_to_test = [
            "backend.services.proposal_service",
            "backend.services.email_service",
            "backend.services.contract_service",
        ]

        for service_path in services_to_test:
            try:
                __import__(service_path)
            except ImportError as e:
                if "No module named" in str(e):
                    import pytest

                    pytest.skip(f"Skipping {service_path} due to missing dependency: {e}")
                raise


class TestScripts:
    """Test that core scripts are valid Python."""

    def test_core_scripts_syntax(self, project_root):
        """Check that core scripts have valid Python syntax."""
        import ast

        core_scripts_dir = project_root / "scripts" / "core"

        for script_path in core_scripts_dir.glob("*.py"):
            with open(script_path, "r") as f:
                source = f.read()

            try:
                ast.parse(source)
            except SyntaxError as e:
                raise AssertionError(f"Syntax error in {script_path.name}: {e}")


class TestConfiguration:
    """Test configuration files are valid."""

    def test_pyproject_toml_valid(self, project_root):
        """Check that pyproject.toml is valid TOML."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        pyproject_path = project_root / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            try:
                config = tomllib.load(f)
                assert "tool" in config or "project" in config
            except Exception as e:
                raise AssertionError(f"Invalid pyproject.toml: {e}")

    def test_gitignore_exists(self, project_root):
        """Check that .gitignore exists and has content."""
        gitignore_path = project_root / ".gitignore"
        assert gitignore_path.exists()

        with open(gitignore_path) as f:
            content = f.read()
            assert len(content) > 100, ".gitignore seems too small"
            assert "venv" in content, ".gitignore should ignore venv"
            assert "__pycache__" in content, ".gitignore should ignore __pycache__"
