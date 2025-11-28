"""
Service layer for project financials management
Handles payment tracking, invoice management, and financial calculations
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
import sqlite3


class FinancialService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_financials_by_proposal(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Get all financial records for a specific proposal"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                f.*,
                m.milestone_name,
                m.milestone_type
            FROM project_financials f
            LEFT JOIN project_milestones m ON f.milestone_id = m.milestone_id
            WHERE f.proposal_id = ?
            ORDER BY f.due_date ASC
        """, (proposal_id,))

        financials = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return financials

    def get_financial_by_id(self, financial_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific financial record by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_financials
            WHERE financial_id = ?
        """, (financial_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def create_financial(self, data: Dict[str, Any]) -> int:
        """Create a new financial record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO project_financials (
                proposal_id,
                payment_type,
                milestone_id,
                amount,
                currency,
                percentage_of_total,
                due_date,
                invoice_number,
                invoice_sent_date,
                payment_received_date,
                payment_method,
                status,
                days_outstanding,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('proposal_id'),
            data.get('payment_type'),
            data.get('milestone_id'),
            data.get('amount'),
            data.get('currency', 'USD'),
            data.get('percentage_of_total'),
            data.get('due_date'),
            data.get('invoice_number'),
            data.get('invoice_sent_date'),
            data.get('payment_received_date'),
            data.get('payment_method'),
            data.get('status', 'pending'),
            data.get('days_outstanding', 0),
            data.get('notes')
        ))

        financial_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return financial_id

    def update_financial(self, financial_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing financial record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build dynamic update query based on provided fields
        update_fields = []
        values = []

        allowed_fields = [
            'payment_type', 'milestone_id', 'amount', 'currency',
            'percentage_of_total', 'due_date', 'invoice_number',
            'invoice_sent_date', 'payment_received_date', 'payment_method',
            'status', 'days_outstanding', 'notes'
        ]

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])

        if not update_fields:
            conn.close()
            return False

        values.append(financial_id)
        query = f"UPDATE project_financials SET {', '.join(update_fields)} WHERE financial_id = ?"

        cursor.execute(query, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def delete_financial(self, financial_id: int) -> bool:
        """Delete a financial record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM project_financials WHERE financial_id = ?", (financial_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def get_financial_summary(self, proposal_id: int) -> Dict[str, Any]:
        """
        Generate financial summary for a proposal
        Returns totals, payments received, outstanding amounts
        """
        financials = self.get_financials_by_proposal(proposal_id)

        summary = {
            'proposal_id': proposal_id,
            'total_contract_value': 0.0,
            'total_paid': 0.0,
            'total_outstanding': 0.0,
            'total_overdue': 0.0,
            'pending_invoices': 0,
            'paid_invoices': 0,
            'overdue_invoices': 0,
            'payment_schedule': []
        }

        today = date.today()

        for financial in financials:
            amount = financial['amount'] or 0.0
            summary['total_contract_value'] += amount

            # Track paid vs outstanding
            if financial['status'] == 'paid':
                summary['total_paid'] += amount
                summary['paid_invoices'] += 1
            elif financial['status'] in ['pending', 'invoiced', 'overdue']:
                summary['total_outstanding'] += amount
                if financial['status'] == 'overdue':
                    summary['total_overdue'] += amount
                    summary['overdue_invoices'] += 1
                elif financial['status'] == 'invoiced':
                    summary['pending_invoices'] += 1

            # Check if overdue
            due_date = financial['due_date']
            is_overdue = False
            if due_date and financial['status'] != 'paid':
                due = datetime.strptime(due_date, '%Y-%m-%d').date()
                is_overdue = due < today

            summary['payment_schedule'].append({
                'financial_id': financial['financial_id'],
                'payment_type': financial['payment_type'],
                'milestone_name': financial.get('milestone_name'),
                'amount': amount,
                'currency': financial['currency'],
                'due_date': financial['due_date'],
                'invoice_number': financial['invoice_number'],
                'invoice_sent_date': financial['invoice_sent_date'],
                'payment_received_date': financial['payment_received_date'],
                'status': financial['status'],
                'is_overdue': is_overdue,
                'days_outstanding': financial['days_outstanding']
            })

        # Sort payment schedule by due date
        summary['payment_schedule'].sort(key=lambda x: x['due_date'] or '9999-12-31')

        return summary

    def get_overdue_payments(self) -> List[Dict[str, Any]]:
        """Get all overdue payments across all proposals"""
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today().isoformat()

        cursor.execute("""
            SELECT
                f.*,
                p.project_code,
                p.project_name,
                p.client_company
            FROM project_financials f
            JOIN projects p ON f.proposal_id = p.proposal_id
            WHERE f.due_date < ?
              AND f.status != 'paid'
              AND f.status != 'cancelled'
            ORDER BY f.due_date ASC
        """, (today,))

        payments = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return payments

    def get_upcoming_payments(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get payments due in the next N days"""
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today()
        future_date = (today + timedelta(days=days_ahead)).isoformat()
        today_str = today.isoformat()

        cursor.execute("""
            SELECT
                f.*,
                p.project_code,
                p.project_name,
                p.client_company
            FROM project_financials f
            JOIN projects p ON f.proposal_id = p.proposal_id
            WHERE f.due_date BETWEEN ? AND ?
              AND f.status != 'paid'
              AND f.status != 'cancelled'
            ORDER BY f.due_date ASC
        """, (today_str, future_date))

        payments = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return payments

    def record_payment(self, financial_id: int, payment_date: str, payment_method: Optional[str] = None) -> bool:
        """
        Record a payment as received
        Updates status to 'paid' and sets payment_received_date
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        update_data = {
            'status': 'paid',
            'payment_received_date': payment_date
        }

        if payment_method:
            update_data['payment_method'] = payment_method

        # Build update query
        update_fields = [f"{k} = ?" for k in update_data.keys()]
        values = list(update_data.values())
        values.append(financial_id)

        cursor.execute(f"""
            UPDATE project_financials
            SET {', '.join(update_fields)}
            WHERE financial_id = ?
        """, values)

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def send_invoice(self, financial_id: int, invoice_number: str, invoice_date: str) -> bool:
        """
        Mark invoice as sent
        Updates status to 'invoiced' and records invoice details
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE project_financials
            SET status = 'invoiced',
                invoice_number = ?,
                invoice_sent_date = ?
            WHERE financial_id = ?
        """, (invoice_number, invoice_date, financial_id))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def calculate_payment_percentages(self, proposal_id: int) -> bool:
        """
        Calculate and update percentage_of_total for all financials in a proposal
        Based on total contract value
        """
        financials = self.get_financials_by_proposal(proposal_id)

        # Calculate total
        total_value = sum(f['amount'] or 0.0 for f in financials)

        if total_value == 0:
            return False

        conn = self._get_connection()
        cursor = conn.cursor()

        # Update each financial with percentage
        for financial in financials:
            amount = financial['amount'] or 0.0
            percentage = (amount / total_value) * 100.0

            cursor.execute("""
                UPDATE project_financials
                SET percentage_of_total = ?
                WHERE financial_id = ?
            """, (percentage, financial['financial_id']))

        conn.commit()
        conn.close()

        return True
