"""
File organization tests - Verify codebase structure follows standards.
"""

import os
from pathlib import Path


class TestScriptOrganization:
    """Test that scripts are properly organized."""

    def test_no_python_scripts_at_root(self, project_root):
        """Ensure no Python scripts are at project root."""
        root_py_files = list(project_root.glob("*.py"))
        assert len(root_py_files) == 0, f"Python files at root: {[f.name for f in root_py_files]}"

    def test_no_shell_scripts_at_root(self, project_root):
        """Ensure no shell scripts are at project root."""
        root_sh_files = list(project_root.glob("*.sh"))
        assert len(root_sh_files) == 0, f"Shell scripts at root: {[f.name for f in root_sh_files]}"

    def test_core_scripts_exist(self, project_root):
        """Check that expected core scripts exist."""
        expected_scripts = [
            "scripts/core/smart_email_brain.py",
            "scripts/core/query_brain.py",
            "scripts/core/import_all_data.py",
        ]
        for script_path in expected_scripts:
            full_path = project_root / script_path
            assert full_path.exists(), f"Missing core script: {script_path}"

    def test_archived_scripts_not_in_core(self, project_root):
        """Check that archived scripts aren't duplicated in core."""
        core_dir = project_root / "scripts" / "core"
        archive_dir = project_root / "scripts" / "archive"

        if not core_dir.exists() or not archive_dir.exists():
            return

        core_names = {f.name for f in core_dir.glob("*.py")}

        # Check deprecated folder
        deprecated_dir = archive_dir / "deprecated"
        if deprecated_dir.exists():
            deprecated_names = {f.name for f in deprecated_dir.glob("*.py")}
            overlap = core_names & deprecated_names
            assert len(overlap) == 0, f"Scripts in both core and deprecated: {overlap}"


class TestDocumentOrganization:
    """Test that documentation is properly organized."""

    def test_limited_markdown_at_root(self, project_root):
        """Ensure only essential markdown files at root."""
        allowed_root_md = {
            "README.md",
            "CLAUDE.md",
            "CONTRIBUTING.md",
            "DATABASE_MIGRATION_SUMMARY.md",
            "2_MONTH_MVP_PLAN.md",
            "CHANGELOG.md",
            "LICENSE.md",
        }

        root_md_files = {f.name for f in project_root.glob("*.md")}
        unexpected = root_md_files - allowed_root_md

        assert len(unexpected) == 0, f"Unexpected markdown at root: {unexpected}"

    def test_docs_subdirectories_exist(self, project_root):
        """Check that docs has proper subdirectories."""
        expected_subdirs = ["architecture", "guides", "archive"]
        docs_dir = project_root / "docs"

        if not docs_dir.exists():
            return

        for subdir in expected_subdirs:
            subdir_path = docs_dir / subdir
            assert subdir_path.exists(), f"Missing docs subdirectory: {subdir}"

    def test_no_session_files_at_root(self, project_root):
        """Ensure session/status files are in docs/sessions."""
        session_patterns = ["SESSION_*.md", "CURRENT_*.md", "TODAYS_*.md"]

        for pattern in session_patterns:
            matches = list(project_root.glob(pattern))
            assert len(matches) == 0, f"Session files at root: {[f.name for f in matches]}"


class TestBackendOrganization:
    """Test backend directory structure."""

    def test_backend_structure(self, project_root):
        """Check backend has expected directories."""
        expected_dirs = ["api", "services", "core"]
        backend_dir = project_root / "backend"

        for dirname in expected_dirs:
            dir_path = backend_dir / dirname
            assert dir_path.exists(), f"Missing backend directory: {dirname}"

    def test_no_debug_files_in_services(self, project_root):
        """Ensure no debug/test files in services directory."""
        services_dir = project_root / "backend" / "services"

        if not services_dir.exists():
            return

        service_files = [f.name for f in services_dir.glob("*.py")]
        debug_files = [f for f in service_files if f.startswith("debug_") or f.startswith("test_")]

        assert len(debug_files) == 0, f"Debug/test files in services: {debug_files}"

    def test_services_have_init(self, project_root):
        """Check that services directory has __init__.py."""
        init_path = project_root / "backend" / "services" / "__init__.py"
        assert init_path.exists(), "Missing __init__.py in services"


class TestDatabaseOrganization:
    """Test database directory structure."""

    def test_single_migrations_directory(self, project_root):
        """Ensure migrations are consolidated in one place."""
        # Check that backend doesn't have its own migrations
        backend_migrations = project_root / "backend" / "migrations"
        assert not backend_migrations.exists(), "backend/migrations should not exist"

        backend_db_migrations = project_root / "backend" / "database" / "migrations"
        assert not backend_db_migrations.exists(), "backend/database/migrations should not exist"

        # Main migrations should exist
        main_migrations = project_root / "database" / "migrations"
        assert main_migrations.exists(), "database/migrations should exist"

    def test_backups_in_correct_location(self, project_root):
        """Ensure database backups are in backups folder."""
        db_dir = project_root / "database"

        # Check for backup files at database root (should be in backups/)
        root_backups = list(db_dir.glob("*.backup*")) + list(db_dir.glob("*_backup*"))
        # Filter out the backups directory itself
        root_backups = [f for f in root_backups if f.is_file()]

        assert len(root_backups) == 0, f"Backup files at database root: {[f.name for f in root_backups]}"


class TestConfigFiles:
    """Test configuration files are in place."""

    def test_required_config_files_exist(self, project_root):
        """Check that essential config files exist."""
        required_files = [
            ".gitignore",
            ".editorconfig",
            "pyproject.toml",
            "Makefile",
            "requirements.txt",
        ]

        for filename in required_files:
            filepath = project_root / filename
            assert filepath.exists(), f"Missing config file: {filename}"

    def test_env_example_exists(self, project_root):
        """Check that .env.example exists for setup guidance."""
        env_example = project_root / ".env.example"
        assert env_example.exists(), "Missing .env.example"

    def test_no_env_file_committed(self, project_root):
        """Verify .env is gitignored (check .gitignore contains it)."""
        gitignore_path = project_root / ".gitignore"

        with open(gitignore_path) as f:
            content = f.read()
            assert ".env" in content, ".env should be in .gitignore"
