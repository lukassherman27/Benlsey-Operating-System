"""
Invoice Service

Handles actual invoices sent and payments received.
Separate from contract values which are future/potential revenue.
"""

from typing import List, Dict, Any
from datetime import date
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
        """Verify invoices table exists"""
        conn = self._get_connection()
        cursor = conn.cursor()

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
                COALESCE(i.project_code, p.project_code) as project_code,
                COALESCE(p.project_title, i.project_code) as project_title
            FROM invoices i
            LEFT JOIN projects p ON i.project_code = p.project_code
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
                COALESCE(i.project_code, p.project_code) as project_code,
                COALESCE(p.project_title, i.project_code) as project_title,
                i.discipline,
                i.phase,
                NULL as scope,
                CASE
                    WHEN i.due_date IS NOT NULL THEN
                        CAST(julianday('now') - julianday(i.due_date) AS INTEGER)
                    ELSE
                        CAST(julianday('now') - julianday(i.invoice_date, '+30 days') AS INTEGER)
                END as days_overdue
            FROM invoices i
            LEFT JOIN projects p ON i.project_code = p.project_code
            WHERE i.status IN ('sent', 'overdue', 'outstanding')
            ORDER BY i.invoice_amount DESC
            LIMIT ?
        """, (limit,))

        invoices = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return invoices

    def get_aging_breakdown(self) -> Dict[str, Any]:
        """
        Get invoice aging breakdown categorized by age (active projects only)
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
                    i.invoice_amount - COALESCE(i.payment_amount, 0) as outstanding_amount,
                    CASE
                        WHEN i.due_date IS NOT NULL THEN
                            CAST(julianday('now') - julianday(i.due_date) AS INTEGER)
                        ELSE
                            CAST(julianday('now') - julianday(i.invoice_date, '+30 days') AS INTEGER)
                    END as days_overdue
                FROM invoices i
                JOIN projects p ON i.project_code = p.project_code
                WHERE p.is_active_project = 1
                  AND i.status IN ('sent', 'overdue', 'outstanding')
                  AND i.invoice_amount - COALESCE(i.payment_amount, 0) > 0
            )
            GROUP BY age_category
        """)

        rows = cursor.fetchall()
        conn.close()

        # Initialize with zeros
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
