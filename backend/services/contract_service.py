"""
Contract Service

Handles contract-related operations:
- Finding latest contracts for projects (PDF documents)
- Comparing contracts
- Version tracking
- Contract generation
- Contract terms and payment schedules
- Project relationships (parent-child, additional services)
- Fee breakdown management
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from .base_service import BaseService


class ContractService(BaseService):
    """Service for contract operations"""

    def get_latest_contract_for_project(
        self,
        project_code: str,
        contract_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent contract for a project

        Args:
            project_code: Project code (e.g., "25-042")
            contract_type: Optional filter ('bensley_contract', 'external_contract')

        Returns:
            Latest contract attachment or None
        """
        sql = """
            SELECT
                a.attachment_id,
                a.filename,
                a.filepath,
                a.filesize,
                a.document_type,
                a.contract_direction,
                a.is_signed,
                a.is_executed,
                a.version_number,
                a.created_at,
                e.email_id,
                e.subject,
                e.sender_email,
                e.date AS email_date,
                p.project_name
            FROM email_attachments a
            JOIN emails e ON a.email_id = e.email_id
            LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
            LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE p.project_code = ?
            AND a.document_type IN ('bensley_contract', 'external_contract')
        """
        params = [project_code]

        if contract_type:
            sql += " AND a.document_type = ?"
            params.append(contract_type)

        sql += " ORDER BY a.created_at DESC LIMIT 1"

        return self.execute_query(sql, tuple(params), fetch_one=True)

    def get_all_contracts_for_project(
        self,
        project_code: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all contracts for a project, grouped by type

        Args:
            project_code: Project code

        Returns:
            Dict with 'bensley_contracts' and 'external_contracts' lists
        """
        sql = """
            SELECT
                a.attachment_id,
                a.filename,
                a.filepath,
                a.document_type,
                a.contract_direction,
                a.is_signed,
                a.version_number,
                a.created_at,
                e.subject,
                e.sender_email,
                e.date AS email_date
            FROM email_attachments a
            JOIN emails e ON a.email_id = e.email_id
            LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
            LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE p.project_code = ?
            AND a.document_type IN ('bensley_contract', 'external_contract')
            ORDER BY a.created_at DESC
        """
        results = self.execute_query(sql, (project_code,))

        bensley_contracts = [r for r in results if r['document_type'] == 'bensley_contract']
        external_contracts = [r for r in results if r['document_type'] == 'external_contract']

        return {
            'bensley_contracts': bensley_contracts,
            'external_contracts': external_contracts
        }

    def find_contracts_by_filename(
        self,
        search_term: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search contracts by filename

        Args:
            search_term: Search string
            limit: Max results

        Returns:
            List of matching contracts
        """
        sql = """
            SELECT
                a.attachment_id,
                a.filename,
                a.filepath,
                a.document_type,
                a.contract_direction,
                a.created_at,
                e.subject,
                e.sender_email,
                p.project_code,
                p.project_name
            FROM email_attachments a
            JOIN emails e ON a.email_id = e.email_id
            LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
            LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE a.document_type IN ('bensley_contract', 'external_contract')
            AND (a.filename LIKE ? OR e.subject LIKE ?)
            ORDER BY a.created_at DESC
            LIMIT ?
        """
        search_pattern = f"%{search_term}%"
        return self.execute_query(sql, (search_pattern, search_pattern, limit))

    def compare_contracts(
        self,
        attachment_id_1: int,
        attachment_id_2: int
    ) -> Dict[str, Any]:
        """
        Compare two contracts (returns metadata, AI comparison would be added later)

        Args:
            attachment_id_1: First contract
            attachment_id_2: Second contract

        Returns:
            Comparison metadata
        """
        # Get both contracts
        sql = """
            SELECT
                attachment_id,
                filename,
                filepath,
                document_type,
                filesize,
                created_at
            FROM email_attachments
            WHERE attachment_id IN (?, ?)
        """
        contracts = self.execute_query(sql, (attachment_id_1, attachment_id_2))

        if len(contracts) != 2:
            return {'error': 'One or both contracts not found'}

        # Check if comparison already exists
        sql = """
            SELECT comparison_summary, key_differences, risk_flags
            FROM contract_comparisons
            WHERE (attachment_id_1 = ? AND attachment_id_2 = ?)
               OR (attachment_id_1 = ? AND attachment_id_2 = ?)
        """
        existing = self.execute_query(
            sql,
            (attachment_id_1, attachment_id_2, attachment_id_2, attachment_id_1),
            fetch_one=True
        )

        return {
            'contract_1': contracts[0],
            'contract_2': contracts[1],
            'comparison': existing if existing else None,
            'needs_ai_comparison': existing is None
        }

    def get_contract_versions(
        self,
        attachment_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get version history for a contract

        Args:
            attachment_id: Contract to check

        Returns:
            List of all versions (current and superseded)
        """
        # Find the chain of versions
        versions = []

        # Get current contract
        current = self.execute_query(
            """
            SELECT
                attachment_id,
                filename,
                version_number,
                supersedes_attachment_id,
                created_at
            FROM email_attachments
            WHERE attachment_id = ?
            """,
            (attachment_id,),
            fetch_one=True
        )

        if not current:
            return versions

        versions.append(current)

        # Walk back through versions
        prev_id = current.get('supersedes_attachment_id')
        while prev_id:
            prev = self.execute_query(
                """
                SELECT
                    attachment_id,
                    filename,
                    version_number,
                    supersedes_attachment_id,
                    created_at
                FROM email_attachments
                WHERE attachment_id = ?
                """,
                (prev_id,),
                fetch_one=True
            )
            if prev:
                versions.append(prev)
                prev_id = prev.get('supersedes_attachment_id')
            else:
                break

        return versions

    def get_contract_stats(self) -> Dict[str, Any]:
        """Get contract statistics"""
        stats = {}

        # Total contracts
        stats['total_contracts'] = self.count_rows(
            'email_attachments',
            "document_type IN ('bensley_contract', 'external_contract')"
        )

        # By type
        stats['bensley_contracts'] = self.count_rows(
            'email_attachments',
            "document_type = 'bensley_contract'"
        )

        stats['external_contracts'] = self.count_rows(
            'email_attachments',
            "document_type = 'external_contract'"
        )

        # Signed vs unsigned
        stats['signed'] = self.count_rows(
            'email_attachments',
            "document_type IN ('bensley_contract', 'external_contract') AND is_signed = 1"
        )

        stats['unsigned'] = stats['total_contracts'] - stats['signed']

        # Recent contracts (last 30 days)
        sql = """
            SELECT COUNT(*) as count
            FROM email_attachments
            WHERE document_type IN ('bensley_contract', 'external_contract')
            AND datetime(created_at) >= datetime('now', '-30 days')
        """
        result = self.execute_query(sql, fetch_one=True)
        stats['recent_30_days'] = result['count'] if result else 0

        return stats

    def get_all_contracts(
        self,
        contract_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "DESC"
    ) -> Dict[str, Any]:
        """
        Get all contracts with pagination

        Args:
            contract_type: Filter by type (bensley_contract, external_contract)
            page: Page number
            per_page: Results per page
            sort_by: Column to sort by
            sort_order: ASC or DESC

        Returns:
            Paginated contract results
        """
        sql = """
            SELECT
                a.attachment_id,
                a.filename,
                a.filepath,
                a.document_type,
                a.contract_direction,
                a.is_signed,
                a.filesize,
                a.created_at,
                e.subject,
                e.sender_email,
                e.date AS email_date,
                p.project_code,
                p.project_name
            FROM email_attachments a
            JOIN emails e ON a.email_id = e.email_id
            LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
            LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE a.document_type IN ('bensley_contract', 'external_contract')
        """
        params = []

        if contract_type:
            sql += " AND a.document_type = ?"
            params.append(contract_type)

        # Validate sort field
        valid_sort_fields = ['created_at', 'filename', 'filesize']
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'

        sql += f" ORDER BY a.{sort_by} {sort_order}"

        return self.paginate(sql, tuple(params), page, per_page)

    # ==================== CONTRACT RELATIONSHIPS ====================

    def get_project_family(self, project_code: str) -> Dict:
        """
        Get complete project family tree including parent and all children.
        Returns parent project + all related additional services/components.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # First, check if this project has a parent
            cursor.execute("""
                SELECT parent_project_code, relationship_type, component_type
                FROM projects
                WHERE project_code = ?
            """, (project_code,))

            row = cursor.fetchone()
            if row and row[0]:
                # This is a child project, get the parent instead
                parent_code = row[0]
            else:
                # This is the parent (or standalone)
                parent_code = project_code

            # Get parent project details
            cursor.execute("""
                SELECT project_code, project_name, status, total_fee_usd,
                       contract_signed_date, project_type
                FROM projects
                WHERE project_code = ?
            """, (parent_code,))

            parent = cursor.fetchone()
            if not parent:
                return {"error": f"Project {project_code} not found"}

            parent_data = {
                "project_code": parent[0],
                "project_name": parent[1],
                "status": parent[2],
                "total_fee_usd": parent[3],
                "contract_signed_date": parent[4],
                "project_type": parent[5],
                "is_parent": True
            }

            # Get all children (additional services, components, extensions)
            cursor.execute("""
                SELECT project_code, project_name, status, total_fee_usd,
                       relationship_type, component_type, contract_signed_date
                FROM projects
                WHERE parent_project_code = ?
                ORDER BY contract_signed_date
            """, (parent_code,))

            children = []
            total_additional_fees = 0

            for row in cursor.fetchall():
                child = {
                    "project_code": row[0],
                    "project_name": row[1],
                    "status": row[2],
                    "total_fee_usd": row[3],
                    "relationship_type": row[4],
                    "component_type": row[5],
                    "contract_signed_date": row[6]
                }
                children.append(child)

                if row[3]:  # total_fee_usd
                    total_additional_fees += row[3]

            # Calculate combined total
            parent_fee = parent_data["total_fee_usd"] or 0
            combined_total = parent_fee + total_additional_fees

            return {
                "parent": parent_data,
                "children": children,
                "summary": {
                    "parent_fee_usd": parent_fee,
                    "additional_services_fee_usd": total_additional_fees,
                    "combined_total_usd": combined_total,
                    "child_count": len(children)
                }
            }

    def link_projects(self, parent_code: str, child_code: str,
                     relationship_type: str, component_type: Optional[str] = None) -> Dict:
        """
        Create parent-child relationship between projects.

        Args:
            parent_code: Parent project code (main contract)
            child_code: Child project code (additional service/component)
            relationship_type: 'additional_services', 'extension', 'component', 'amendment'
            component_type: Optional type like 'restaurant', 'club', 'landscape'
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Verify both projects exist
            cursor.execute("SELECT project_code FROM projects WHERE project_code = ?", (parent_code,))
            if not cursor.fetchone():
                return {"error": f"Parent project {parent_code} not found"}

            cursor.execute("SELECT project_code FROM projects WHERE project_code = ?", (child_code,))
            if not cursor.fetchone():
                return {"error": f"Child project {child_code} not found"}

            # Update child project with parent reference
            cursor.execute("""
                UPDATE projects
                SET parent_project_code = ?,
                    relationship_type = ?,
                    component_type = ?,
                    updated_at = ?
                WHERE project_code = ?
            """, (parent_code, relationship_type, component_type,
                  datetime.now().isoformat(), child_code))

            conn.commit()

            return {
                "success": True,
                "parent": parent_code,
                "child": child_code,
                "relationship": relationship_type,
                "component": component_type
            }

    def get_all_project_families(self) -> List[Dict]:
        """Get all parent projects with their children"""
        cursor = self.conn.cursor()

        # Get all parent projects (those that have children)
        cursor.execute("""
            SELECT DISTINCT parent_project_code
            FROM projects
            WHERE parent_project_code IS NOT NULL
        """)

        families = []
        for row in cursor.fetchall():
            parent_code = row[0]
            family = self.get_project_family(parent_code)
            if "error" not in family:
                families.append(family)

        return families

    # ==================== CONTRACT TERMS ====================

    def get_contract_terms(self, project_code: str) -> Optional[Dict]:
        """Get contract terms for a project"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT contract_id, project_code, contract_signed_date,
                   contract_start_date, total_contract_term_months, contract_end_date,
                   total_fee_usd, payment_schedule, contract_type,
                   retainer_amount_usd, final_payment_amount_usd,
                   early_termination_terms, amendment_count, original_contract_id,
                   contract_document_path, confirmed_by_user, confidence
            FROM contract_terms
            WHERE project_code = ?
        """, (project_code,))

        row = cursor.fetchone()
        if not row:
            return None

        payment_schedule = json.loads(row[7]) if row[7] else None

        return {
            "contract_id": row[0],
            "project_code": row[1],
            "contract_signed_date": row[2],
            "contract_start_date": row[3],
            "total_contract_term_months": row[4],
            "contract_end_date": row[5],
            "total_fee_usd": row[6],
            "payment_schedule": payment_schedule,
            "contract_type": row[8],
            "retainer_amount_usd": row[9],
            "final_payment_amount_usd": row[10],
            "early_termination_terms": row[11],
            "amendment_count": row[12],
            "original_contract_id": row[13],
            "contract_document_path": row[14],
            "confirmed_by_user": bool(row[15]),
            "confidence": row[16]
        }

    def create_contract_terms(self, project_code: str, contract_data: Dict) -> Dict:
        """Create contract terms for a project"""
        cursor = self.conn.cursor()

        # Generate contract_id
        cursor.execute("SELECT MAX(CAST(SUBSTR(contract_id, 2) AS INTEGER)) FROM contract_terms WHERE contract_id LIKE 'C%'")
        max_id = cursor.fetchone()[0] or 0
        contract_id = f"C{max_id + 1:04d}"

        # Serialize payment schedule to JSON if provided
        payment_schedule_json = None
        if contract_data.get("payment_schedule"):
            payment_schedule_json = json.dumps(contract_data["payment_schedule"])

        cursor.execute("""
            INSERT INTO contract_terms (
                contract_id, project_code, contract_signed_date, contract_start_date,
                total_contract_term_months, contract_end_date, total_fee_usd,
                payment_schedule, contract_type, retainer_amount_usd,
                final_payment_amount_usd, early_termination_terms,
                amendment_count, original_contract_id, contract_document_path,
                confirmed_by_user, confidence, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contract_id,
            project_code,
            contract_data.get("contract_signed_date"),
            contract_data.get("contract_start_date"),
            contract_data.get("total_contract_term_months"),
            contract_data.get("contract_end_date"),
            contract_data.get("total_fee_usd"),
            payment_schedule_json,
            contract_data.get("contract_type", "fixed_fee"),
            contract_data.get("retainer_amount_usd"),
            contract_data.get("final_payment_amount_usd"),
            contract_data.get("early_termination_terms"),
            contract_data.get("amendment_count", 0),
            contract_data.get("original_contract_id"),
            contract_data.get("contract_document_path"),
            contract_data.get("confirmed_by_user", 0),
            contract_data.get("confidence"),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        self.conn.commit()

        return {"success": True, "contract_id": contract_id, "project_code": project_code}

    # ==================== FEE BREAKDOWN ====================

    def get_fee_breakdown(self, project_code: str) -> List[Dict]:
        """Get phase-based fee breakdown for a project"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT breakdown_id, project_code, phase, phase_fee_usd,
                   percentage_of_total, payment_status, invoice_id,
                   expected_payment_date, actual_payment_date,
                   confirmed_by_user, confidence
            FROM project_fee_breakdown
            WHERE project_code = ?
            ORDER BY
                CASE phase
                    WHEN 'mobilization' THEN 1
                    WHEN 'concept' THEN 2
                    WHEN 'schematic' THEN 3
                    WHEN 'dd' THEN 4
                    WHEN 'cd' THEN 5
                    WHEN 'ca' THEN 6
                    ELSE 7
                END
        """, (project_code,))

        breakdown = []
        for row in cursor.fetchall():
            breakdown.append({
                "breakdown_id": row[0],
                "project_code": row[1],
                "phase": row[2],
                "phase_fee_usd": row[3],
                "percentage_of_total": row[4],
                "payment_status": row[5],
                "invoice_id": row[6],
                "expected_payment_date": row[7],
                "actual_payment_date": row[8],
                "confirmed_by_user": bool(row[9]),
                "confidence": row[10]
            })

        return breakdown

    def create_standard_fee_breakdown(self, project_code: str, total_fee: float,
                                     breakdown_percentages: Optional[Dict[str, float]] = None) -> Dict:
        """
        Create standard phase breakdown for a project.

        Args:
            project_code: Project code
            total_fee: Total contract fee in USD
            breakdown_percentages: Dict of phase -> percentage (e.g. {'concept': 0.25, 'dd': 0.35})
        """
        cursor = self.conn.cursor()

        # Standard phases if not provided (Bensley standard fee structure)
        if not breakdown_percentages:
            breakdown_percentages = {
                'mobilization': 0.15,           # 15% Mobilization
                'concept': 0.25,                # 25% Concept Design
                'dd': 0.30,                     # 30% Detailed Design (Design Development)
                'cd': 0.15,                     # 15% Construction Documents
                'ca': 0.15                      # 15% Construction Observation
            }

        # Verify percentages sum to 1.0
        total_pct = sum(breakdown_percentages.values())
        if abs(total_pct - 1.0) > 0.01:
            return {"error": f"Percentages sum to {total_pct}, must equal 1.0"}

        created_ids = []

        for phase, percentage in breakdown_percentages.items():
            # Generate breakdown_id
            cursor.execute("SELECT MAX(CAST(SUBSTR(breakdown_id, 2) AS INTEGER)) FROM project_fee_breakdown WHERE breakdown_id LIKE 'B%'")
            max_id = cursor.fetchone()[0] or 0
            breakdown_id = f"B{max_id + 1:05d}"

            phase_fee = total_fee * percentage

            cursor.execute("""
                INSERT INTO project_fee_breakdown (
                    breakdown_id, project_code, phase, phase_fee_usd,
                    percentage_of_total, payment_status, confirmed_by_user,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'pending', 0, ?, ?)
            """, (
                breakdown_id,
                project_code,
                phase,
                phase_fee,
                percentage,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            created_ids.append(breakdown_id)

        self.conn.commit()

        return {
            "success": True,
            "project_code": project_code,
            "breakdown_ids": created_ids,
            "total_fee_usd": total_fee
        }

    # ==================== CONTRACT ANALYSIS ====================

    def get_contracts_expiring_soon(self, days: int = 90) -> List[Dict]:
        """Get contracts expiring within N days"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT ct.contract_id, ct.project_code, p.project_name,
                   ct.contract_end_date, ct.total_fee_usd,
                   julianday(ct.contract_end_date) - julianday('now') as days_remaining
            FROM contract_terms ct
            JOIN projects p ON ct.project_code = p.project_code
            WHERE julianday(ct.contract_end_date) - julianday('now') BETWEEN 0 AND ?
            ORDER BY days_remaining
        """, (days,))

        expiring = []
        for row in cursor.fetchall():
            expiring.append({
                "contract_id": row[0],
                "project_code": row[1],
                "project_name": row[2],
                "contract_end_date": row[3],
                "total_fee_usd": row[4],
                "days_remaining": int(row[5])
            })

        return expiring

    def get_monthly_fee_summary(self) -> Dict:
        """Get summary of all monthly/retainer contracts"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT ct.project_code, p.project_name, ct.retainer_amount_usd,
                   ct.contract_start_date, ct.contract_end_date
            FROM contract_terms ct
            JOIN projects p ON ct.project_code = p.project_code
            WHERE ct.contract_type = 'monthly' OR ct.retainer_amount_usd > 0
            ORDER BY ct.retainer_amount_usd DESC
        """)

        monthly_contracts = []
        total_monthly_revenue = 0

        for row in cursor.fetchall():
            monthly_contracts.append({
                "project_code": row[0],
                "project_name": row[1],
                "monthly_amount_usd": row[2],
                "start_date": row[3],
                "end_date": row[4]
            })

            if row[2]:
                total_monthly_revenue += row[2]

        return {
            "monthly_contracts": monthly_contracts,
            "total_monthly_revenue_usd": total_monthly_revenue,
            "contract_count": len(monthly_contracts)
        }
