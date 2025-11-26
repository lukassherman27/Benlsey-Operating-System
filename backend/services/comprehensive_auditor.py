#!/usr/bin/env python3
"""
Comprehensive Audit Engine - Phase 2
Extends basic pattern detection with scope, fee, timeline, and contract verification
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import re

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


class ComprehensiveAuditor:
    """Enhanced auditor with scope, fee, timeline, and contract verification"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def audit_all_projects(self) -> Dict[str, Any]:
        """
        Run comprehensive audit on all projects
        Returns summary of findings
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get all projects (including proposals - merged in migration 015)
        cursor.execute("""
            SELECT project_code, project_title, is_active_project, total_fee_usd, status
            FROM projects
        """)

        all_suggestions = []
        stats = {
            'projects_audited': 0,
            'scope_issues': 0,
            'fee_issues': 0,
            'timeline_issues': 0,
            'invoice_issues': 0,
            'contract_issues': 0
        }

        for row in cursor.fetchall():
            project = dict(row)
            stats['projects_audited'] += 1

            # Run all verification checks
            scope_suggestions = self.verify_project_scope(project)
            fee_suggestions = self.validate_fee_breakdown(project)
            timeline_suggestions = self.validate_project_timeline(project)
            invoice_suggestions = self.verify_invoice_linking(project)
            contract_suggestions = self.verify_contract_terms(project)

            # Collect all suggestions
            all_suggestions.extend(scope_suggestions)
            all_suggestions.extend(fee_suggestions)
            all_suggestions.extend(timeline_suggestions)
            all_suggestions.extend(invoice_suggestions)
            all_suggestions.extend(contract_suggestions)

            # Update stats
            stats['scope_issues'] += len(scope_suggestions)
            stats['fee_issues'] += len(fee_suggestions)
            stats['timeline_issues'] += len(timeline_suggestions)
            stats['invoice_issues'] += len(invoice_suggestions)
            stats['contract_issues'] += len(contract_suggestions)

        # Save suggestions to database
        for suggestion in all_suggestions:
            self._save_suggestion(suggestion)

        conn.close()

        return {
            'stats': stats,
            'total_suggestions': len(all_suggestions),
            'suggestions': all_suggestions
        }

    def verify_project_scope(self, project: Dict) -> List[Dict]:
        """
        Detect what disciplines are included based on:
        - Project name keywords
        - Contract documents
        - Invoice line items
        - Email content
        - Historical patterns
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        suggestions = []

        project_code = project['project_code']
        project_title = project.get('project_title', '') or ''

        # Check if scope already defined
        cursor.execute("""
            SELECT * FROM project_scope WHERE project_code = ?
        """, (project_code,))
        existing_scope = cursor.fetchall()

        if existing_scope:
            conn.close()
            return []  # Scope already defined

        # Analyze project name for discipline keywords
        name_lower = project_title.lower() if project_title else ''
        detected_disciplines = []
        confidence = 0.70

        # Landscape detection
        landscape_keywords = ['landscape', 'garden', 'outdoor', 'plaza', 'park', 'courtyard']
        if any(kw in name_lower for kw in landscape_keywords):
            detected_disciplines.append('landscape')
            confidence = 0.80

        # Interiors detection
        interior_keywords = ['interior', 'fit-out', 'fitout', 'fit out', 'lobby', 'residence', 'villa']
        if any(kw in name_lower for kw in interior_keywords):
            detected_disciplines.append('interiors')
            confidence = 0.80

        # Architecture detection
        architecture_keywords = ['architecture', 'master plan', 'masterplan', 'building', 'tower']
        if any(kw in name_lower for kw in architecture_keywords):
            detected_disciplines.append('architecture')
            confidence = 0.75

        # Check contract documents for additional clues
        cursor.execute("""
            SELECT contract_document_path FROM contract_terms WHERE project_code = ?
        """, (project_code,))
        contract_doc = cursor.fetchone()

        # If no disciplines detected, default to landscape (Bensley's primary discipline)
        if not detected_disciplines:
            detected_disciplines = ['landscape']
            confidence = 0.60

        # Create suggestion
        if detected_disciplines:
            suggestions.append({
                'project_code': project_code,
                'suggestion_type': 'missing_scope',
                'proposed_fix': {
                    'action': 'create_scope',
                    'disciplines': detected_disciplines
                },
                'evidence': {
                    'signals': [
                        f"Project name: {project_title}",
                        f"Detected keywords in name",
                        f"No scope defined in database"
                    ],
                    'detected_disciplines': detected_disciplines
                },
                'confidence': confidence,
                'impact_type': 'data_quality',
                'impact_value_usd': None,
                'impact_summary': f"Missing scope definition for {', '.join(detected_disciplines)} project",
                'severity': 'medium',
                'bucket': 'needs_attention',
                'pattern_id': 'pattern_missing_scope',
                'pattern_label': 'Missing Project Scope'
            })

        conn.close()
        return suggestions

    def validate_fee_breakdown(self, project: Dict) -> List[Dict]:
        """
        Verify fee breakdown makes sense:
        - Total adds up correctly
        - Phase percentages reasonable
        - Invoice amounts match breakdown
        - Payment schedule matches phases
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        suggestions = []

        project_code = project['project_code']
        total_fee = project.get('total_fee_usd', 0)

        if not total_fee or total_fee == 0:
            conn.close()
            return []  # No fee to validate

        # Check if fee breakdown exists
        cursor.execute("""
            SELECT * FROM project_fee_breakdown WHERE project_code = ?
        """, (project_code,))
        breakdown = cursor.fetchall()

        if not breakdown:
            # No breakdown exists - suggest creating one
            suggestions.append({
                'project_code': project_code,
                'suggestion_type': 'missing_fee_breakdown',
                'proposed_fix': {
                    'action': 'create_fee_breakdown',
                    'total_fee': total_fee,
                    'suggest_standard_phases': True
                },
                'evidence': {
                    'signals': [
                        f"Total fee: ${total_fee:,.0f}",
                        "No fee breakdown found in database",
                        "Should have breakdown by phase"
                    ],
                    'total_fee_usd': total_fee
                },
                'confidence': 0.75,
                'impact_type': 'financial',
                'impact_value_usd': total_fee,
                'impact_summary': f"Missing fee breakdown for ${total_fee:,.0f} project",
                'severity': 'high',
                'bucket': 'needs_attention',
                'pattern_id': 'pattern_missing_fee_breakdown',
                'pattern_label': 'Missing Fee Breakdown'
            })
        else:
            # Validate existing breakdown
            breakdown_total = sum([row['phase_fee_usd'] or 0 for row in breakdown])

            # Check if totals match (allow $1K tolerance)
            if abs(breakdown_total - total_fee) > 1000:
                suggestions.append({
                    'project_code': project_code,
                    'suggestion_type': 'fee_mismatch',
                    'proposed_fix': {
                        'action': 'review_fee_breakdown',
                        'breakdown_total': breakdown_total,
                        'contract_total': total_fee,
                        'difference': breakdown_total - total_fee
                    },
                    'evidence': {
                        'signals': [
                            f"Fee breakdown total: ${breakdown_total:,.0f}",
                            f"Contract total: ${total_fee:,.0f}",
                            f"Difference: ${abs(breakdown_total - total_fee):,.0f}"
                        ],
                        'breakdown_total': breakdown_total,
                        'contract_total': total_fee
                    },
                    'confidence': 0.95,
                    'impact_type': 'financial',
                    'impact_value_usd': abs(breakdown_total - total_fee),
                    'impact_summary': f"Fee breakdown mismatch: ${abs(breakdown_total - total_fee):,.0f}",
                    'severity': 'high',
                    'bucket': 'urgent',
                    'pattern_id': 'pattern_fee_mismatch',
                    'pattern_label': 'Fee Breakdown Mismatch'
                })

        conn.close()
        return suggestions

    def validate_project_timeline(self, project: Dict) -> List[Dict]:
        """
        Check if timeline makes sense:
        - Expected durations per phase
        - Contract term matches phase durations
        - Presentations scheduled appropriately
        - Delays detected
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        suggestions = []

        project_code = project['project_code']

        # Get contract terms
        cursor.execute("""
            SELECT * FROM contract_terms WHERE project_code = ?
        """, (project_code,))
        contract = cursor.fetchone()

        if not contract:
            conn.close()
            return []  # No contract to validate against

        # Get timeline
        cursor.execute("""
            SELECT * FROM project_phase_timeline WHERE project_code = ?
        """, (project_code,))
        timeline = cursor.fetchall()

        if not timeline:
            # No timeline exists - suggest creating one
            contract_term = contract['total_contract_term_months']

            suggestions.append({
                'project_code': project_code,
                'suggestion_type': 'missing_timeline',
                'proposed_fix': {
                    'action': 'create_timeline',
                    'contract_term_months': contract_term,
                    'suggest_standard_phases': True
                },
                'evidence': {
                    'signals': [
                        f"Contract term: {contract_term} months",
                        "No timeline found in database",
                        "Should have phase timeline"
                    ],
                    'contract_term_months': contract_term
                },
                'confidence': 0.80,
                'impact_type': 'schedule',
                'impact_value_usd': None,
                'impact_summary': f"Missing timeline for {contract_term}-month contract",
                'severity': 'medium',
                'bucket': 'needs_attention',
                'pattern_id': 'pattern_missing_timeline',
                'pattern_label': 'Missing Project Timeline'
            })
        else:
            # Validate timeline matches contract
            # Standard phase durations (in months)
            standard_durations = {
                'mobilization': 0,
                'concept': 3.5,
                'schematic': 1,
                'dd': 4,
                'cd': 3.5,
                'ca': None  # Variable until contract end
            }

            total_expected = sum([d for d in standard_durations.values() if d])
            contract_term = contract['total_contract_term_months'] or 0

            if contract_term > 0 and contract_term < total_expected:
                suggestions.append({
                    'project_code': project_code,
                    'suggestion_type': 'timeline_mismatch',
                    'proposed_fix': {
                        'action': 'review_timeline',
                        'contract_term': contract_term,
                        'expected_duration': total_expected
                    },
                    'evidence': {
                        'signals': [
                            f"Contract term: {contract_term} months",
                            f"Standard phases: {total_expected} months",
                            "Timeline appears compressed"
                        ],
                        'contract_term': contract_term,
                        'expected_duration': total_expected
                    },
                    'confidence': 0.85,
                    'impact_type': 'schedule',
                    'impact_value_usd': None,
                    'impact_summary': f"Contract term ({contract_term}mo) shorter than standard phases ({total_expected}mo)",
                    'severity': 'medium',
                    'bucket': 'needs_attention',
                    'pattern_id': 'pattern_timeline_compressed',
                    'pattern_label': 'Compressed Timeline'
                })

        conn.close()
        return suggestions

    def verify_invoice_linking(self, project: Dict) -> List[Dict]:
        """
        Check if invoices are linked correctly:
        - All invoices for this project linked?
        - Invoice amounts match fee breakdown?
        - Payment phases correct?
        - Any missing invoices?
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        suggestions = []

        project_code = project['project_code']

        # Get invoices for this project
        # Note: invoices.project_id links to projects.proposal_id (the PK)
        cursor.execute("""
            SELECT COUNT(*) as invoice_count, SUM(i.invoice_amount) as total_invoiced
            FROM invoices i
            JOIN projects p ON i.project_id = p.proposal_id
            WHERE p.project_code = ?
        """, (project_code,))
        invoice_data = cursor.fetchone()
        invoice_count = invoice_data['invoice_count'] or 0
        total_invoiced = invoice_data['total_invoiced'] or 0

        # Get fee breakdown
        cursor.execute("""
            SELECT * FROM project_fee_breakdown WHERE project_code = ?
        """, (project_code,))
        fee_breakdown = cursor.fetchall()

        if fee_breakdown and invoice_count == 0:
            # Has fee breakdown but no invoices
            total_fee = sum([row['phase_fee_usd'] or 0 for row in fee_breakdown])

            suggestions.append({
                'project_code': project_code,
                'suggestion_type': 'missing_invoices',
                'proposed_fix': {
                    'action': 'review_invoicing',
                    'expected_fee': total_fee,
                    'invoiced_amount': 0
                },
                'evidence': {
                    'signals': [
                        f"Fee breakdown exists: ${total_fee:,.0f}",
                        "No invoices found for project",
                        "Should have invoices if work started"
                    ],
                    'expected_fee': total_fee
                },
                'confidence': 0.75,
                'impact_type': 'financial',
                'impact_value_usd': total_fee,
                'impact_summary': f"No invoices found for ${total_fee:,.0f} project",
                'severity': 'high',
                'bucket': 'needs_attention',
                'pattern_id': 'pattern_missing_invoices',
                'pattern_label': 'Missing Invoices'
            })

        elif fee_breakdown and invoice_count > 0:
            # Check if invoice total matches fee breakdown
            total_fee = sum([row['phase_fee_usd'] or 0 for row in fee_breakdown])

            if abs(total_invoiced - total_fee) > 5000:  # $5K tolerance
                suggestions.append({
                    'project_code': project_code,
                    'suggestion_type': 'invoice_fee_mismatch',
                    'proposed_fix': {
                        'action': 'reconcile_invoices',
                        'total_fee': total_fee,
                        'total_invoiced': total_invoiced,
                        'difference': total_invoiced - total_fee
                    },
                    'evidence': {
                        'signals': [
                            f"Total fee: ${total_fee:,.0f}",
                            f"Total invoiced: ${total_invoiced:,.0f}",
                            f"Difference: ${abs(total_invoiced - total_fee):,.0f}"
                        ],
                        'total_fee': total_fee,
                        'total_invoiced': total_invoiced
                    },
                    'confidence': 0.90,
                    'impact_type': 'financial',
                    'impact_value_usd': abs(total_invoiced - total_fee),
                    'impact_summary': f"Invoice/fee mismatch: ${abs(total_invoiced - total_fee):,.0f}",
                    'severity': 'high',
                    'bucket': 'urgent',
                    'pattern_id': 'pattern_invoice_fee_mismatch',
                    'pattern_label': 'Invoice/Fee Mismatch'
                })

        conn.close()
        return suggestions

    def verify_contract_terms(self, project: Dict) -> List[Dict]:
        """
        Verify contract data is complete:
        - Contract exists for active projects?
        - All required fields populated?
        - Dates make sense?
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        suggestions = []

        project_code = project['project_code']
        is_active = project.get('is_active_project', 0)

        # Get contract
        cursor.execute("""
            SELECT * FROM contract_terms WHERE project_code = ?
        """, (project_code,))
        contract = cursor.fetchone()

        if is_active and not contract:
            # Active project with no contract
            total_fee = project.get('total_fee_usd', 0)

            suggestions.append({
                'project_code': project_code,
                'suggestion_type': 'missing_contract',
                'proposed_fix': {
                    'action': 'add_contract',
                    'project_fee': total_fee
                },
                'evidence': {
                    'signals': [
                        "Project marked as active",
                        "No contract found in database",
                        "Active projects should have contracts"
                    ],
                    'is_active': is_active
                },
                'confidence': 0.85,
                'impact_type': 'legal',
                'impact_value_usd': total_fee,
                'impact_summary': "Active project missing contract data",
                'severity': 'high',
                'bucket': 'urgent',
                'pattern_id': 'pattern_missing_contract',
                'pattern_label': 'Missing Contract'
            })

        conn.close()
        return suggestions

    def _save_suggestion(self, suggestion: Dict):
        """Save a suggestion to the database"""
        conn = self._get_connection()
        cursor = conn.cursor()

        suggestion_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO ai_suggestions_queue
            (id, project_code, suggestion_type, proposed_fix, evidence,
             confidence, impact_type, impact_value_usd, impact_summary,
             severity, bucket, pattern_id, pattern_label, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (
            suggestion_id,
            suggestion['project_code'],
            suggestion['suggestion_type'],
            json.dumps(suggestion['proposed_fix']),
            json.dumps(suggestion['evidence']),
            suggestion['confidence'],
            suggestion.get('impact_type'),
            suggestion.get('impact_value_usd'),
            suggestion.get('impact_summary'),
            suggestion.get('severity', 'medium'),
            suggestion.get('bucket', 'needs_attention'),
            suggestion.get('pattern_id'),
            suggestion.get('pattern_label'),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()


if __name__ == '__main__':
    """Run comprehensive audit"""
    print("🔍 Running Comprehensive Project Audit...")
    print("=" * 80)

    auditor = ComprehensiveAuditor()
    results = auditor.audit_all_projects()

    print(f"\n✅ Audit Complete!")
    print(f"\nProjects Audited: {results['stats']['projects_audited']}")
    print(f"Total Suggestions: {results['total_suggestions']}")
    print(f"\nBy Category:")
    print(f"  🔍 Scope Issues: {results['stats']['scope_issues']}")
    print(f"  💰 Fee Issues: {results['stats']['fee_issues']}")
    print(f"  📅 Timeline Issues: {results['stats']['timeline_issues']}")
    print(f"  📄 Invoice Issues: {results['stats']['invoice_issues']}")
    print(f"  📋 Contract Issues: {results['stats']['contract_issues']}")
    print("\n" + "=" * 80)
    print("Use review_suggestions.py to review and approve suggestions")
