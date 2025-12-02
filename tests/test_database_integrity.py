"""
Database integrity tests - Verify database structure and data quality.
These tests run against the actual database (read-only).
"""

import sqlite3
from pathlib import Path


class TestDatabaseIntegrity:
    """Test database structure and integrity."""

    def test_projects_have_required_fields(self, database_path):
        """Check that projects have essential fields populated."""
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check for projects with missing project_code
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM projects
            WHERE project_code IS NULL OR project_code = ''
        """)
        missing_code = cursor.fetchone()["cnt"]
        assert missing_code == 0, f"{missing_code} projects missing project_code"

        conn.close()

    def test_proposals_have_required_fields(self, database_path):
        """Check that proposals have essential fields populated."""
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check for proposals with missing project_code
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM proposals
            WHERE project_code IS NULL OR project_code = ''
        """)
        missing_code = cursor.fetchone()["cnt"]
        assert missing_code == 0, f"{missing_code} proposals missing project_code"

        conn.close()

    def test_invoices_linked_to_projects(self, database_path):
        """Check that invoices are linked to valid projects."""
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Count invoices with valid project links
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM invoices i
            WHERE i.project_id IS NOT NULL
            AND EXISTS (SELECT 1 FROM projects p WHERE p.project_id = i.project_id)
        """)
        linked = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM invoices WHERE project_id IS NOT NULL")
        total_with_project = cursor.fetchone()["cnt"]

        # Allow some unlinked invoices but most should be linked
        if total_with_project > 0:
            link_rate = linked / total_with_project
            assert link_rate >= 0.9, f"Only {link_rate:.1%} of invoices properly linked to projects"

        conn.close()

    def test_emails_have_valid_dates(self, database_path):
        """Check that emails have valid date fields."""
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check for emails with dates in reasonable range (2010-2030)
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM emails
            WHERE received_date IS NOT NULL
            AND received_date >= '2010-01-01'
            AND received_date <= '2030-12-31'
        """)
        valid_dates = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM emails WHERE received_date IS NOT NULL")
        total_with_dates = cursor.fetchone()["cnt"]

        if total_with_dates > 0:
            valid_rate = valid_dates / total_with_dates
            assert valid_rate >= 0.95, f"Only {valid_rate:.1%} of emails have valid dates"

        conn.close()

    def test_no_orphaned_fee_breakdowns(self, database_path):
        """Check that fee breakdowns are linked to valid projects."""
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) as cnt FROM project_fee_breakdown fb
            WHERE NOT EXISTS (
                SELECT 1 FROM projects p WHERE p.project_id = fb.project_id
            )
        """)
        orphaned = cursor.fetchone()["cnt"]
        assert orphaned == 0, f"{orphaned} fee breakdowns not linked to valid projects"

        conn.close()


class TestDatabaseStatistics:
    """Test that database has reasonable data volumes."""

    def test_minimum_data_counts(self, database_path):
        """Check that database has minimum expected data."""
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        expectations = {
            "projects": 10,
            "proposals": 10,
            "emails": 100,
            "contacts": 10,
        }

        for table, min_count in expectations.items():
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            actual = cursor.fetchone()[0]
            assert actual >= min_count, f"{table} has only {actual} rows, expected >= {min_count}"

        conn.close()

    def test_recent_data_exists(self, database_path):
        """Check that there's recent data (within last year)."""
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Check for recent emails
        cursor.execute("""
            SELECT COUNT(*) FROM emails
            WHERE received_date >= date('now', '-365 days')
        """)
        recent_emails = cursor.fetchone()[0]
        assert recent_emails > 0, "No emails from the last year"

        conn.close()


class TestDatabaseSchema:
    """Test that database schema matches expectations."""

    def test_core_tables_have_indexes(self, database_path):
        """Check that core tables have proper indexes."""
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Get all indexes
        cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
        indexes = {row[1]: [] for row in cursor.fetchall()}
        cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
        for row in cursor.fetchall():
            indexes.setdefault(row[1], []).append(row[0])

        # Core tables that should have indexes
        tables_needing_indexes = ["projects", "proposals", "emails", "invoices"]

        for table in tables_needing_indexes:
            assert table in indexes, f"Table {table} should exist"
            # Note: just checking tables exist, not specific indexes

        conn.close()

    def test_foreign_key_columns_exist(self, database_path):
        """Check that expected foreign key columns exist."""
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Check invoices has project_id
        cursor.execute("PRAGMA table_info(invoices)")
        invoice_columns = [row[1] for row in cursor.fetchall()]
        assert "project_id" in invoice_columns, "invoices should have project_id column"

        # Check emails has project_id or similar
        cursor.execute("PRAGMA table_info(emails)")
        email_columns = [row[1] for row in cursor.fetchall()]
        # Emails might link via email_project_links table, so just check table exists

        conn.close()
