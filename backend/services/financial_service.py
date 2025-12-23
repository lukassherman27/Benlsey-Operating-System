"""
Service layer for project financials management
Handles invoice stats, aging summaries, and project fee breakdowns
"""

from typing import List, Dict, Any
from datetime import date
import sqlite3
import re


class FinancialService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_invoice_stats(self) -> Dict[str, Any]:
        """
        Get basic invoice statistics for the /api/invoices/stats endpoint

        Returns:
            - total_invoices: Total count of all invoices
            - total_amount: Sum of all invoice amounts
            - paid_count: Count of paid invoices
            - outstanding_count: Count of unpaid invoices
            - total_paid: Sum of all payments received
            - total_outstanding: Sum of outstanding amounts
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_invoices,
                COALESCE(SUM(invoice_amount), 0) as total_amount,
                COUNT(CASE WHEN status = 'paid' THEN 1 END) as paid_count,
                COUNT(CASE WHEN status != 'paid' THEN 1 END) as outstanding_count,
                COALESCE(SUM(CASE WHEN status = 'paid' THEN payment_amount ELSE 0 END), 0) as total_paid,
                COALESCE(SUM(CASE WHEN status != 'paid' THEN invoice_amount - COALESCE(payment_amount, 0) ELSE 0 END), 0) as total_outstanding
            FROM invoices
        """)

        row = cursor.fetchone()
        conn.close()

        return {
            'total_invoices': row['total_invoices'] or 0,
            'total_amount': row['total_amount'] or 0.0,
            'paid_count': row['paid_count'] or 0,
            'outstanding_count': row['outstanding_count'] or 0,
            'total_paid': row['total_paid'] or 0.0,
            'total_outstanding': row['total_outstanding'] or 0.0
        }

    def get_invoice_aging_summary(self) -> Dict[str, Any]:
        """
        Get aging summary across all unpaid invoices
        Groups by aging buckets (Current, 1-30 days, 31-60 days, etc.)

        Returns:
            Dictionary with counts and totals for each aging bucket
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today().isoformat()

        cursor.execute("""
            SELECT
                CASE
                    WHEN due_date IS NULL OR due_date >= ? THEN 'Current'
                    WHEN julianday('now') - julianday(due_date) <= 30 THEN '1-30 days'
                    WHEN julianday('now') - julianday(due_date) <= 60 THEN '31-60 days'
                    WHEN julianday('now') - julianday(due_date) <= 90 THEN '61-90 days'
                    ELSE '90+ days'
                END as aging_bucket,
                COUNT(*) as invoice_count,
                SUM(invoice_amount - COALESCE(payment_amount, 0)) as total_outstanding
            FROM invoices
            WHERE status != 'paid'
            GROUP BY aging_bucket
            ORDER BY
                CASE aging_bucket
                    WHEN 'Current' THEN 1
                    WHEN '1-30 days' THEN 2
                    WHEN '31-60 days' THEN 3
                    WHEN '61-90 days' THEN 4
                    WHEN '90+ days' THEN 5
                    ELSE 6
                END
        """, (today,))

        aging_buckets = [dict(row) for row in cursor.fetchall()]
        conn.close()

        total_unpaid_invoices = sum(bucket['invoice_count'] for bucket in aging_buckets)
        total_unpaid_amount = sum(bucket['total_outstanding'] or 0 for bucket in aging_buckets)

        return {
            'aging_buckets': aging_buckets,
            'total_unpaid_invoices': total_unpaid_invoices,
            'total_unpaid_amount': total_unpaid_amount
        }

    def get_oldest_unpaid_invoices(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get oldest unpaid invoices (by days since invoice_date)

        Args:
            limit: Number of invoices to return (default 5)

        Returns:
            List of invoices sorted by days_outstanding DESC
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today().isoformat()

        cursor.execute("""
            SELECT
                i.invoice_id,
                p.project_code,
                p.project_title as project_name,
                '' as client_company,
                i.invoice_number,
                i.invoice_date,
                i.due_date,
                i.invoice_amount,
                i.invoice_amount - COALESCE(i.payment_amount, 0) as amount_outstanding,
                i.status,
                NULL as discipline,
                NULL as phase,
                CAST(julianday('now') - julianday(i.invoice_date) AS INTEGER) as days_outstanding,
                CASE WHEN i.due_date IS NOT NULL THEN CAST(julianday('now') - julianday(i.due_date) AS INTEGER) ELSE 0 END as days_overdue,
                CASE
                    WHEN i.due_date IS NULL OR i.due_date >= ? THEN 'Current'
                    WHEN julianday('now') - julianday(i.due_date) <= 30 THEN '1-30 days'
                    WHEN julianday('now') - julianday(i.due_date) <= 60 THEN '31-60 days'
                    WHEN julianday('now') - julianday(i.due_date) <= 90 THEN '61-90 days'
                    ELSE '90+ days'
                END as aging_bucket
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            WHERE i.status != 'paid'
            ORDER BY days_outstanding DESC
            LIMIT ?
        """, (today, limit))

        invoices = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return invoices

    def get_invoices_by_project(self, project_code: str) -> List[Dict[str, Any]]:
        """
        Get all invoices for a specific project

        Args:
            project_code: The project code to get invoices for

        Returns:
            List of invoices for the project
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                i.invoice_id,
                p.project_code,
                p.project_title as project_name,
                i.invoice_number,
                i.description,
                i.invoice_date,
                i.due_date,
                i.invoice_amount,
                i.invoice_amount as amount_usd,
                i.payment_amount,
                i.payment_amount as amount_paid,
                i.payment_date,
                i.status,
                fb.phase as discipline,
                fb.phase,
                (i.invoice_amount - COALESCE(i.payment_amount, 0)) as amount_outstanding
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            LEFT JOIN project_fee_breakdown fb ON i.breakdown_id = fb.breakdown_id
            WHERE p.project_code = ?
            ORDER BY i.invoice_date DESC
        """, (project_code,))

        invoices = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return invoices

    # Standard phase order for fee breakdown display
    PHASE_ORDER = [
        'Mobilization',
        'Concept Design',
        'Schematic Design',
        'Design Development',
        'Construction Documents',
        'Construction Drawings',
        'Construction Observation',
        'Construction Administration',
        'Additional Services',
    ]

    def get_fee_breakdown(self, project_code: str) -> List[Dict]:
        """Get fee breakdown for a project from project_fee_breakdown table

        Returns phases in correct order:
        Mobilization -> Concept -> Schematic -> DD -> CD -> CA
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Normalize project code - try both formats
        normalized_code = re.sub(r'^(\d{2})-BK-', r'\1 BK-', project_code)

        cursor.execute("""
            SELECT * FROM project_fee_breakdown
            WHERE project_code = ? OR project_code = ?
        """, (project_code, normalized_code))
        rows = cursor.fetchall()
        conn.close()

        breakdowns = [dict(row) for row in rows]

        def phase_sort_key(item):
            phase = item.get('phase', '')
            try:
                phase_idx = next(
                    i for i, p in enumerate(self.PHASE_ORDER)
                    if p.lower() in phase.lower() or phase.lower() in p.lower()
                )
            except StopIteration:
                phase_idx = 999
            return (item.get('discipline', ''), phase_idx, phase)

        return sorted(breakdowns, key=phase_sort_key)
