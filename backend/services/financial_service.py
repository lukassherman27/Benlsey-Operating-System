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
                p.project_title,
                COALESCE(pr.client_company, 'Unknown')
            FROM project_financials f
            JOIN projects p ON f.proposal_id = p.project_id
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
                p.project_title,
                COALESCE(pr.client_company, 'Unknown')
            FROM project_financials f
            JOIN projects p ON f.proposal_id = p.project_id
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

    # ========================================================================
    # NEW METHODS FOR ENHANCED FINANCIAL DASHBOARD (Migration 023)
    # ========================================================================

    def get_dashboard_financial_metrics(self) -> Dict[str, Any]:
        """
        Get top-level financial metrics for dashboard overview
        Calculates directly from invoices and projects tables

        Returns:
            - total_contract_value: Sum of all active project contracts
            - total_invoiced: Sum of all invoiced amounts
            - total_paid: Sum of all payments received
            - total_outstanding: Total invoiced but not paid (not overdue)
            - total_overdue: Total invoiced and past due date
            - total_remaining: Total uninvoiced contract value
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today().isoformat()

        # Get total contract value and count of active projects
        cursor.execute("""
            SELECT
                SUM(total_fee_usd) as total_contract_value,
                COUNT(*) as active_project_count
            FROM projects
            WHERE is_active_project = 1
        """)
        project_metrics = cursor.fetchone()

        # Get total invoiced
        cursor.execute("""
            SELECT SUM(invoice_amount) as total_invoiced
            FROM invoices
        """)
        invoiced_row = cursor.fetchone()

        # Get total paid (including partial payments)
        # FIXED: Sum all payments regardless of status to capture partial payments
        cursor.execute("""
            SELECT SUM(COALESCE(payment_amount, 0)) as total_paid
            FROM invoices
        """)
        paid_row = cursor.fetchone()

        # Get outstanding (not overdue)
        cursor.execute("""
            SELECT SUM(invoice_amount - COALESCE(payment_amount, 0)) as outstanding
            FROM invoices
            WHERE status != 'paid'
              AND (due_date IS NULL OR due_date >= ?)
        """, (today,))
        outstanding_row = cursor.fetchone()

        # Get overdue
        cursor.execute("""
            SELECT SUM(invoice_amount - COALESCE(payment_amount, 0)) as overdue
            FROM invoices
            WHERE status != 'paid'
              AND due_date < ?
        """, (today,))
        overdue_row = cursor.fetchone()

        conn.close()

        total_contract_value = project_metrics['total_contract_value'] or 0.0
        total_invoiced = invoiced_row['total_invoiced'] or 0.0
        total_paid = paid_row['total_paid'] or 0.0
        total_outstanding = outstanding_row['outstanding'] or 0.0
        total_overdue = overdue_row['overdue'] or 0.0
        total_remaining = total_contract_value - total_invoiced

        return {
            'total_contract_value': total_contract_value,
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'total_outstanding': total_outstanding,
            'total_overdue': total_overdue,
            'total_remaining': total_remaining,
            'active_project_count': project_metrics['active_project_count'] or 0
        }

    def get_recent_payments(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get most recently paid invoices

        Args:
            limit: Number of recent payments to return (default 5)

        Returns:
            List of invoices sorted by payment_date DESC
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                i.invoice_id,
                i.invoice_number,
                p.project_code,
                p.project_title as project_title,
                '' as client_company,
                i.invoice_date,
                i.payment_date,
                i.invoice_amount,
                i.payment_amount,
                NULL as discipline,
                NULL as phase
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

    def get_projects_by_outstanding(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get projects with highest outstanding amounts

        Args:
            limit: Number of projects to return (default 5)

        Returns:
            List of projects sorted by outstanding_usd DESC
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today().isoformat()

        # Overdue = due_date < today, OR if no due_date, invoice_date + 30 days < today
        cursor.execute("""
            SELECT
                p.project_code,
                p.project_title as project_name,
                '' as client_company,
                p.total_fee_usd as contract_value,
                SUM(i.invoice_amount) as total_invoiced_usd,
                SUM(CASE WHEN i.status = 'paid' THEN i.payment_amount ELSE 0 END) as paid_to_date_usd,
                SUM(CASE WHEN i.status != 'paid' THEN i.invoice_amount - COALESCE(i.payment_amount, 0) ELSE 0 END) as outstanding_usd,
                SUM(CASE
                    WHEN i.status != 'paid' AND (
                        (i.due_date IS NOT NULL AND i.due_date >= ?) OR
                        (i.due_date IS NULL AND date(i.invoice_date, '+30 days') >= ?)
                    ) THEN i.invoice_amount - COALESCE(i.payment_amount, 0)
                    ELSE 0
                END) as outstanding_not_due,
                SUM(CASE
                    WHEN i.status != 'paid' AND (
                        (i.due_date IS NOT NULL AND i.due_date < ?) OR
                        (i.due_date IS NULL AND date(i.invoice_date, '+30 days') < ?)
                    ) THEN i.invoice_amount - COALESCE(i.payment_amount, 0)
                    ELSE 0
                END) as overdue_amount,
                SUM(CASE
                    WHEN i.status != 'paid' AND (
                        (i.due_date IS NOT NULL AND i.due_date < ?) OR
                        (i.due_date IS NULL AND date(i.invoice_date, '+30 days') < ?)
                    ) THEN 1
                    ELSE 0
                END) as overdue_invoice_count
            FROM projects p
            LEFT JOIN proposals pr ON p.project_code = pr.project_code
            LEFT JOIN invoices i ON p.project_id = i.project_id
            WHERE p.is_active_project = 1
            GROUP BY p.project_id, p.project_code, p.project_title, p.total_fee_usd
            HAVING outstanding_usd > 0
            ORDER BY outstanding_usd DESC
            LIMIT ?
        """, (today, today, today, today, today, today, limit))

        projects = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return projects

    def get_oldest_unpaid_invoices(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get oldest unpaid invoices (by days since invoice_date, not days overdue)

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

    def get_projects_by_remaining_value(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get projects with highest remaining uninvoiced contract value

        Args:
            limit: Number of projects to return (default 5)

        Returns:
            List of projects sorted by total_remaining_usd DESC
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.project_code,
                p.project_title as project_name,
                '' as client_company,
                p.total_fee_usd as contract_value,
                COALESCE(SUM(i.invoice_amount), 0) as total_invoiced_usd,
                p.total_fee_usd - COALESCE(SUM(i.invoice_amount), 0) as total_remaining_usd,
                CASE WHEN p.total_fee_usd > 0 THEN (COALESCE(SUM(i.invoice_amount), 0) / p.total_fee_usd) * 100 ELSE 0 END as percent_invoiced
            FROM projects p
            LEFT JOIN proposals pr ON p.project_code = pr.project_code
            LEFT JOIN invoices i ON p.project_id = i.project_id
            WHERE p.is_active_project = 1
            GROUP BY p.project_id, p.project_code, p.project_title, p.total_fee_usd
            HAVING total_remaining_usd > 0
            ORDER BY total_remaining_usd DESC
            LIMIT ?
        """, (limit,))

        projects = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return projects

    def get_project_financial_detail(self, project_code: str) -> Dict[str, Any]:
        """
        Get comprehensive financial breakdown for a specific project
        Includes contract details, phase breakdown, and invoice history

        Args:
            project_code: Project code (e.g., "25 BK-030")

        Returns:
            Dictionary with:
            - project_summary: Overall financial metrics
            - phase_breakdown: Financial status by discipline and phase
            - invoices: All invoices for this project
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get project summary from view
        cursor.execute("""
            SELECT * FROM v_project_financial_summary
            WHERE project_code = ?
        """, (project_code,))

        summary_row = cursor.fetchone()
        if not summary_row:
            conn.close()
            return None

        project_summary = dict(summary_row)

        # Get phase breakdown with invoicing progress
        cursor.execute("""
            SELECT
                breakdown_id,
                discipline,
                phase,
                phase_fee_usd,
                total_invoiced,
                percentage_invoiced,
                total_paid,
                percentage_paid,
                phase_fee_usd - total_invoiced as remaining_to_invoice
            FROM project_fee_breakdown
            WHERE project_code = ?
            ORDER BY discipline, phase
        """, (project_code,))

        phase_breakdown = [dict(row) for row in cursor.fetchall()]

        # Get all invoices for this project
        cursor.execute("""
            SELECT
                i.invoice_id,
                i.invoice_number,
                i.invoice_date,
                i.due_date,
                i.invoice_amount,
                i.payment_amount,
                i.invoice_amount - COALESCE(i.payment_amount, 0) as amount_outstanding,
                i.status,
                NULL as discipline,
                NULL as phase,
                CAST(julianday('now') - julianday(i.invoice_date) AS INTEGER) as days_outstanding,
                i.payment_date,
                i.notes
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            WHERE p.project_code = ?
            ORDER BY i.invoice_date DESC
        """, (project_code,))

        invoices = [dict(row) for row in cursor.fetchall()]

        # Get invoice-to-phase links for partial invoicing details
        cursor.execute("""
            SELECT
                ipl.link_id,
                ipl.invoice_id,
                ipl.breakdown_id,
                ipl.amount_applied,
                ipl.percentage_of_phase,
                pfb.discipline,
                pfb.phase,
                pfb.phase_fee_usd
            FROM invoice_phase_links ipl
            JOIN invoices i ON ipl.invoice_id = i.invoice_id
            JOIN project_fee_breakdown pfb ON ipl.breakdown_id = pfb.breakdown_id
            JOIN projects p ON i.project_id = p.project_id
            WHERE p.project_code = ?
            ORDER BY i.invoice_date DESC
        """, (project_code,))

        phase_links = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            'project_summary': project_summary,
            'phase_breakdown': phase_breakdown,
            'invoices': invoices,
            'phase_links': phase_links
        }

    def get_project_hierarchy(self, project_code: str) -> Dict[str, Any]:
        """
        Get hierarchical breakdown: Project → Discipline → Phase → Invoices

        Returns nested tree structure showing:
        - Disciplines (Architecture, Interior, Landscape)
          - Phases (Mobilization, Concept Design, etc.)
            - Invoices applied to that phase
            - Financial progress (fee, invoiced, paid, remaining)

        Args:
            project_code: Project code (e.g., '25-BK-033')

        Returns:
            {
                'project_code': '25-BK-033',
                'project_name': 'Mumbai Clubhouse',
                'total_contract_value': 1620000.0,
                'total_invoiced': 245000.0,
                'total_paid': 220000.0,
                'disciplines': {
                    'Architecture': {
                        'total_fee': 540000.0,
                        'total_invoiced': 100000.0,
                        'total_paid': 100000.0,
                        'phases': [
                            {
                                'phase': 'Mobilization',
                                'phase_fee': 27000.0,
                                'total_invoiced': 27000.0,
                                'total_paid': 27000.0,
                                'remaining': 0.0,
                                'phase_order': 1,
                                'invoices': [
                                    {
                                        'invoice_id': 1,
                                        'invoice_number': 'BK-001',
                                        'invoice_amount': 27000.0,
                                        'payment_amount': 27000.0,
                                        'amount_applied': 27000.0,
                                        'percentage_of_phase': 100.0,
                                        'status': 'paid'
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. Get project summary
        cursor.execute("""
            SELECT
                p.project_code,
                p.project_title as project_name,
                p.total_fee_usd as contract_value,
                (SELECT COALESCE(SUM(total_invoiced), 0)
                 FROM project_fee_breakdown
                 WHERE project_code = p.project_code) as total_invoiced,
                (SELECT COALESCE(SUM(total_paid), 0)
                 FROM project_fee_breakdown
                 WHERE project_code = p.project_code) as total_paid
            FROM projects p
            WHERE p.project_code = ?
        """, (project_code,))

        project_row = cursor.fetchone()
        if not project_row:
            conn.close()
            return {
                'success': False,
                'error': f'Project {project_code} not found'
            }

        project_info = dict(project_row)

        # 2. Get phase breakdown
        cursor.execute("""
            SELECT
                breakdown_id,
                discipline,
                phase,
                phase_fee_usd,
                total_invoiced,
                total_paid
            FROM project_fee_breakdown
            WHERE project_code = ?
            ORDER BY discipline, phase
        """, (project_code,))

        phase_breakdown = [dict(row) for row in cursor.fetchall()]

        # 3. Get invoices for this project (linked by breakdown_id)
        cursor.execute("""
            SELECT
                i.invoice_id,
                i.invoice_number,
                i.invoice_amount,
                i.payment_amount,
                i.invoice_date,
                i.due_date,
                i.payment_date,
                i.status,
                i.breakdown_id
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            WHERE p.project_code = ?
            ORDER BY i.invoice_date DESC
        """, (project_code,))

        invoices = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # 4. Build hierarchical structure
        hierarchy = self._build_hierarchy_tree(phase_breakdown, invoices)

        return {
            'success': True,
            'project_code': project_info['project_code'],
            'project_name': project_info['project_name'],
            'total_contract_value': project_info['contract_value'],
            'total_invoiced': project_info['total_invoiced'] or 0.0,
            'total_paid': project_info['total_paid'] or 0.0,
            'disciplines': hierarchy
        }

    def _build_hierarchy_tree(
        self,
        phase_breakdown: List[Dict[str, Any]],
        invoices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build nested tree structure from phase breakdown

        Args:
            phase_breakdown: List of phase records from project_fee_breakdown
            invoices: List of all project invoices (linked by breakdown_id)

        Returns:
            Nested dictionary: disciplines -> phases -> invoices
        """
        # Group invoices by breakdown_id
        invoices_by_phase = {}
        for invoice in invoices:
            breakdown_id = invoice.get('breakdown_id')
            if breakdown_id:
                if breakdown_id not in invoices_by_phase:
                    invoices_by_phase[breakdown_id] = []
                invoices_by_phase[breakdown_id].append(invoice)

        # Build discipline -> phase tree
        disciplines = {}

        for phase in phase_breakdown:
            discipline = phase['discipline']

            # Initialize discipline if not exists
            if discipline not in disciplines:
                disciplines[discipline] = {
                    'total_fee': 0.0,
                    'total_invoiced': 0.0,
                    'total_paid': 0.0,
                    'phases': []
                }

            # Add phase data
            phase_invoices = invoices_by_phase.get(phase['breakdown_id'], [])
            phase_invoiced = phase['total_invoiced'] or 0.0
            phase_paid = phase['total_paid'] or 0.0
            phase_fee = phase['phase_fee_usd'] or 0.0
            phase_remaining = phase_fee - phase_invoiced

            disciplines[discipline]['phases'].append({
                'breakdown_id': phase['breakdown_id'],
                'phase': phase['phase'],
                'phase_fee': phase_fee,
                'total_invoiced': phase_invoiced,
                'total_paid': phase_paid,
                'remaining': phase_remaining,
                'invoices': phase_invoices
            })

            # Accumulate discipline totals
            disciplines[discipline]['total_fee'] += phase_fee
            disciplines[discipline]['total_invoiced'] += phase_invoiced
            disciplines[discipline]['total_paid'] += phase_paid

        # Add remaining to each discipline
        for discipline in disciplines.values():
            discipline['remaining'] = discipline['total_fee'] - discipline['total_invoiced']

        return disciplines

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

        # Get total invoices and amounts
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

        # Calculate totals
        total_unpaid_invoices = sum(bucket['invoice_count'] for bucket in aging_buckets)
        total_unpaid_amount = sum(bucket['total_outstanding'] or 0 for bucket in aging_buckets)

        return {
            'aging_buckets': aging_buckets,
            'total_unpaid_invoices': total_unpaid_invoices,
            'total_unpaid_amount': total_unpaid_amount
        }

    def get_fee_breakdown(self, project_code: str) -> List[Dict]:
        """Get fee breakdown for a project from project_fee_breakdown table"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Normalize project code - try both formats (space and dash)
        # fee_breakdown table uses "25 BK-015" format (space before BK)
        # projects table may use "25-BK-015" format (dash before BK)
        import re
        # Convert "25-BK-015" to "25 BK-015"
        normalized_code = re.sub(r'^(\d{2})-BK-', r'\1 BK-', project_code)

        cursor.execute("""
            SELECT * FROM project_fee_breakdown
            WHERE project_code = ? OR project_code = ?
            ORDER BY discipline, phase
        """, (project_code, normalized_code))
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
