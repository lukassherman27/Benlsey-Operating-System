"""
Invoice Service

Handles actual invoices sent and payments received.
Separate from contract values which are future/potential revenue.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import sqlite3


class InvoiceService:
    """Service for managing actual invoices and payments"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_table_exists()

    def _get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table_exists(self):
        """Verify invoices table exists (table should already exist in OneDrive DB)"""
        # Table already exists in OneDrive database with correct schema
        # No need to create - just verify it exists
        conn = self._get_connection()
        cursor = conn.cursor()

        # Verify table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='invoices'
        """)

        if not cursor.fetchone():
            raise Exception("invoices table does not exist in database")

        conn.close()

    def create_invoice(self, data: Dict[str, Any]) -> int:
        """Create a new invoice"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Resolve project_code to project_id if needed
        project_id = data.get('project_id')
        if not project_id and 'project_code' in data:
            cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (data['project_code'],))
            row = cursor.fetchone()
            if row:
                project_id = row['project_id']

        cursor.execute("""
            INSERT INTO invoices (
                invoice_number,
                project_id,
                description,
                invoice_date,
                due_date,
                invoice_amount,
                status,
                notes,
                source_type,
                created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['invoice_number'],
            project_id,
            data.get('description'),
            data['invoice_date'],
            data.get('due_date'),
            data['invoice_amount'],
            data.get('status', 'sent'),
            data.get('notes'),
            data.get('source_type', 'manual'),
            data.get('created_by', 'system')
        ))

        invoice_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return invoice_id

    def record_payment(self, invoice_number: str, payment_data: Dict[str, Any]) -> bool:
        """Record a payment for an invoice"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE invoices
            SET status = 'paid',
                payment_date = ?,
                payment_amount = ?,
                notes = COALESCE(notes || ' | ', '') || ?
            WHERE invoice_number = ?
        """, (
            payment_data['payment_date'],
            payment_data['amount'],
            payment_data.get('payment_method', 'Payment recorded'),
            invoice_number
        ))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success

    def get_outstanding_invoices(self) -> List[Dict[str, Any]]:
        """Get all unpaid invoices"""
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today().isoformat()

        # Update overdue status
        cursor.execute("""
            UPDATE invoices
            SET status = 'overdue'
            WHERE status = 'sent'
            AND due_date < ?
        """, (today,))

        cursor.execute("""
            SELECT *,
                julianday(CURRENT_DATE) - julianday(due_date) as days_overdue
            FROM invoices
            WHERE status IN ('sent', 'overdue')
            ORDER BY due_date ASC
        """)

        invoices = [dict(row) for row in cursor.fetchall()]
        conn.commit()
        conn.close()

        return invoices

    def get_recent_payments(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recently paid invoices"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT i.*, p.project_code, p.project_title
            FROM invoices i
            LEFT JOIN projects p ON i.project_id = p.project_id
            WHERE i.status = 'paid'
            AND i.payment_date IS NOT NULL
            ORDER BY i.payment_date DESC
            LIMIT ?
        """, (limit,))

        payments = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return payments

    def get_revenue_stats(self) -> Dict[str, Any]:
        """Get revenue statistics (actual payments received)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Total invoiced
        cursor.execute("""
            SELECT
                COUNT(*) as total_invoices,
                SUM(invoice_amount) as total_invoiced
            FROM invoices
        """)
        invoice_stats = dict(cursor.fetchone())

        # Total paid (actual revenue)
        cursor.execute("""
            SELECT
                COUNT(*) as paid_count,
                SUM(payment_amount) as total_revenue
            FROM invoices
            WHERE status = 'paid'
        """)
        payment_stats = dict(cursor.fetchone())

        # Outstanding
        cursor.execute("""
            SELECT
                COUNT(*) as outstanding_count,
                SUM(invoice_amount) as total_outstanding
            FROM invoices
            WHERE status IN ('sent', 'overdue')
        """)
        outstanding_stats = dict(cursor.fetchone())

        # Overdue
        cursor.execute("""
            SELECT
                COUNT(*) as overdue_count,
                SUM(invoice_amount) as total_overdue
            FROM invoices
            WHERE status = 'overdue'
        """)
        overdue_stats = dict(cursor.fetchone())

        conn.close()

        return {
            'total_invoices': invoice_stats['total_invoices'] or 0,
            'total_invoiced': invoice_stats['total_invoiced'] or 0.0,
            'paid_invoices': payment_stats['paid_count'] or 0,
            'actual_revenue': payment_stats['total_revenue'] or 0.0,  # This is REAL revenue
            'outstanding_invoices': outstanding_stats['outstanding_count'] or 0,
            'total_outstanding': outstanding_stats['total_outstanding'] or 0.0,
            'overdue_invoices': overdue_stats['overdue_count'] or 0,
            'total_overdue': overdue_stats['total_overdue'] or 0.0,
        }

    def get_invoices_by_project(self, project_code: str) -> List[Dict[str, Any]]:
        """Get all invoices for a specific project"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT i.*, p.project_code, p.project_title
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            WHERE p.project_code = ?
            ORDER BY i.invoice_date DESC
        """, (project_code,))

        invoices = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return invoices

    def get_recent_paid_invoices(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get last N paid invoices (newest first)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                i.invoice_number,
                i.invoice_amount,
                i.payment_amount,
                i.payment_date,
                i.invoice_date,
                i.description,
                i.status,
                p.project_code,
                p.project_title
            FROM invoices i
            LEFT JOIN projects p ON i.project_id = p.project_id
            WHERE i.status = 'paid'
            AND i.payment_date IS NOT NULL
            ORDER BY i.payment_date DESC
            LIMIT ?
        """, (limit,))

        invoices = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return invoices

    def get_largest_outstanding_invoices(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get largest outstanding invoices by amount with phase/discipline info"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                i.invoice_number,
                i.invoice_amount,
                i.invoice_date,
                i.due_date,
                i.description,
                i.status,
                p.project_code,
                p.project_title,
                pfb.discipline,
                pfb.phase,
                pfb.scope,
                CASE
                    WHEN i.due_date IS NOT NULL THEN
                        CAST(julianday('now') - julianday(i.due_date) AS INTEGER)
                    ELSE
                        CAST(julianday('now') - julianday(i.invoice_date, '+30 days') AS INTEGER)
                END as days_overdue
            FROM invoices i
            LEFT JOIN projects p ON i.project_id = p.project_id
            LEFT JOIN project_fee_breakdown pfb ON i.breakdown_id = pfb.breakdown_id
            WHERE i.status = 'outstanding'
            ORDER BY i.invoice_amount DESC
            LIMIT ?
        """, (limit,))

        invoices = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return invoices

    def get_aging_breakdown(self) -> Dict[str, Any]:
        """
        Get invoice aging breakdown categorized by age
        Returns counts and amounts for 0-10, 10-30, 30-90, and 90+ days
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as count,
                SUM(outstanding_amount) as amount,
                CASE
                    WHEN days_overdue <= 10 THEN '0_to_10'
                    WHEN days_overdue <= 30 THEN '10_to_30'
                    WHEN days_overdue <= 90 THEN '30_to_90'
                    ELSE 'over_90'
                END as age_category
            FROM (
                SELECT
                    invoice_amount - COALESCE(payment_amount, 0) as outstanding_amount,
                    CASE
                        WHEN due_date IS NOT NULL THEN
                            CAST(julianday('now') - julianday(due_date) AS INTEGER)
                        ELSE
                            CAST(julianday('now') - julianday(invoice_date, '+30 days') AS INTEGER)
                    END as days_overdue
                FROM invoices
                WHERE status = 'outstanding'
                  AND invoice_amount - COALESCE(payment_amount, 0) > 0
            )
            GROUP BY age_category
        """)

        rows = cursor.fetchall()
        conn.close()

        # Initialize with zeros - new buckets
        breakdown = {
            '0_to_10': {'count': 0, 'amount': 0.0},
            '10_to_30': {'count': 0, 'amount': 0.0},
            '30_to_90': {'count': 0, 'amount': 0.0},
            'over_90': {'count': 0, 'amount': 0.0}
        }

        # Fill in actual values
        for row in rows:
            category = row['age_category']
            breakdown[category] = {
                'count': row['count'],
                'amount': row['amount'] or 0.0
            }

        return breakdown

    def get_invoice_aging_data(self) -> Dict[str, Any]:
        """
        Get complete invoice aging data for the widget
        Combines recent paid, largest outstanding, and aging breakdown
        """
        aging_breakdown = self.get_aging_breakdown()
        return {
            'recent_paid': self.get_recent_paid_invoices(5),
            'largest_outstanding': self.get_largest_outstanding_invoices(10),
            'aging_breakdown': aging_breakdown,
            'summary': {
                'total_outstanding_count': sum(
                    aging_breakdown[cat]['count']
                    for cat in ['0_to_10', '10_to_30', '30_to_90', 'over_90']
                ),
                'total_outstanding_amount': sum(
                    aging_breakdown[cat]['amount']
                    for cat in ['0_to_10', '10_to_30', '30_to_90', 'over_90']
                )
            }
        }