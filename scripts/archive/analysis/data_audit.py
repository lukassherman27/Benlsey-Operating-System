#!/usr/bin/env python3
"""
Data Audit Script for BDS Operations Platform

Provides comprehensive analysis of data quality across the database:
- Missing data per project
- Data completeness scores
- Recommendations for manual entry

Usage:
    python scripts/analysis/data_audit.py
    python scripts/analysis/data_audit.py --project 24BK001
    python scripts/analysis/data_audit.py --export csv
"""

import sqlite3
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = os.getenv('DATABASE_PATH', PROJECT_ROOT / 'database' / 'bensley_master.db')


class DataAuditor:
    """Comprehensive data quality auditor for BDS database."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    def get_overall_stats(self) -> dict:
        """Get high-level database statistics."""
        cursor = self.conn.cursor()

        stats = {}
        queries = {
            'total_projects': "SELECT COUNT(*) FROM projects",
            'total_proposals': "SELECT COUNT(*) FROM proposals",
            'total_emails': "SELECT COUNT(*) FROM emails",
            'total_contacts': "SELECT COUNT(*) FROM contacts",
            'total_invoices': "SELECT COUNT(*) FROM invoices",
            'total_rfis': "SELECT COUNT(*) FROM rfis",
            'total_milestones': "SELECT COUNT(*) FROM project_milestones",
            'email_proposal_links': "SELECT COUNT(*) FROM email_proposal_links",
            'email_project_links': "SELECT COUNT(*) FROM email_project_links",
            'contact_project_links': "SELECT COUNT(*) FROM project_contact_links",
        }

        for key, query in queries.items():
            try:
                cursor.execute(query)
                stats[key] = cursor.fetchone()[0]
            except Exception as e:
                stats[key] = f"Error: {e}"

        return stats

    def get_phase_inconsistencies(self) -> list:
        """Check for phase name inconsistencies in fee_breakdowns."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT phase, COUNT(*) as count
            FROM project_fee_breakdown
            WHERE phase IS NOT NULL
            GROUP BY phase
            ORDER BY count DESC
        """)

        phases = cursor.fetchall()

        # Define standard phase names
        standard_phases = {
            'mobilization': 'Mobilization',
            'concept design': 'Concept Design',
            'conceptual design': 'Concept Design',
            'concept': 'Concept Design',
            'schematic design': 'Schematic Design',
            'design development': 'Design Development',
            'construction documents': 'Construction Documents',
            'construction drawing': 'Construction Documents',
            'construction observation': 'Construction Observation',
            'construction administration': 'Construction Observation',
        }

        inconsistencies = []
        for row in phases:
            phase_name = row['phase']
            phase_lower = phase_name.lower().strip()

            # Check if it matches any standard phase
            matched = False
            for pattern, standard in standard_phases.items():
                if pattern in phase_lower:
                    if phase_name != standard:
                        inconsistencies.append({
                            'current': phase_name,
                            'should_be': standard,
                            'count': row['count']
                        })
                    matched = True
                    break

            if not matched and row['count'] >= 2:
                inconsistencies.append({
                    'current': phase_name,
                    'should_be': '(non-standard phase)',
                    'count': row['count']
                })

        return inconsistencies

    def audit_project(self, project_code: str) -> dict:
        """Audit a single project for data completeness."""
        cursor = self.conn.cursor()

        # Get project info
        cursor.execute("""
            SELECT * FROM projects WHERE project_code = ?
        """, (project_code,))
        project = cursor.fetchone()

        if not project:
            return {'error': f'Project {project_code} not found'}

        audit = {
            'project_code': project_code,
            'project_title': project['project_title'],
            'missing': [],
            'present': [],
            'quality_score': 0
        }

        checks = [
            ('contract_value', "SELECT total_fee_usd FROM projects WHERE project_code = ?",
             lambda x: x and x[0] and x[0] > 0),
            ('fee_breakdown', "SELECT COUNT(*) FROM project_fee_breakdown WHERE project_code = ?",
             lambda x: x[0] > 0),
            ('invoices', "SELECT COUNT(*) FROM invoices i JOIN projects p ON i.project_id = p.project_id WHERE p.project_code = ?",
             lambda x: x[0] > 0),
            ('email_links', "SELECT COUNT(*) FROM email_project_links WHERE project_code = ?",
             lambda x: x[0] > 0),
            ('contacts', """SELECT COUNT(*) FROM project_contact_links pcl
                           JOIN proposals p ON pcl.proposal_id = p.proposal_id
                           WHERE p.project_code = ?""",
             lambda x: x[0] > 0),
            ('milestones', "SELECT COUNT(*) FROM project_milestones WHERE project_code = ?",
             lambda x: x[0] > 0),
            ('rfis', "SELECT COUNT(*) FROM rfis WHERE project_code = ?",
             lambda x: x[0] > 0),
        ]

        for check_name, query, validator in checks:
            try:
                cursor.execute(query, (project_code,))
                result = cursor.fetchone()
                if validator(result):
                    audit['present'].append(check_name)
                else:
                    audit['missing'].append(check_name)
            except Exception as e:
                audit['missing'].append(f"{check_name} (error: {e})")

        # Calculate quality score
        total_checks = len(checks)
        present_count = len(audit['present'])
        audit['quality_score'] = round((present_count / total_checks) * 100, 1)

        return audit

    def audit_all_projects(self) -> list:
        """Audit all projects and return sorted by quality score."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT project_code FROM projects ORDER BY project_code")

        audits = []
        for row in cursor.fetchall():
            audit = self.audit_project(row[0])
            audits.append(audit)

        # Sort by quality score (lowest first = needs most attention)
        audits.sort(key=lambda x: x.get('quality_score', 0))

        return audits

    def audit_proposals(self) -> dict:
        """Audit proposals for completeness."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                p.proposal_id,
                p.project_code,
                p.project_name,
                p.project_value,
                p.current_status,
                (SELECT COUNT(*) FROM email_proposal_links epl WHERE epl.proposal_id = p.proposal_id) as email_count,
                (SELECT COUNT(*) FROM project_contact_links pcl WHERE pcl.proposal_id = p.proposal_id) as contact_count
            FROM proposals p
            ORDER BY p.project_code
        """)

        proposals = cursor.fetchall()

        summary = {
            'total': len(proposals),
            'with_emails': 0,
            'with_contacts': 0,
            'with_value': 0,
            'incomplete': []
        }

        for p in proposals:
            missing = []

            if p['email_count'] == 0:
                missing.append('no_emails')
            else:
                summary['with_emails'] += 1

            if p['contact_count'] == 0:
                missing.append('no_contacts')
            else:
                summary['with_contacts'] += 1

            if not p['project_value'] or p['project_value'] == 0:
                missing.append('no_value')
            else:
                summary['with_value'] += 1

            if missing:
                summary['incomplete'].append({
                    'project_code': p['project_code'],
                    'project_name': p['project_name'],
                    'missing': missing
                })

        return summary

    def get_data_quality_report(self) -> str:
        """Generate a full data quality report."""
        lines = []
        lines.append("=" * 60)
        lines.append("BDS OPERATIONS PLATFORM - DATA QUALITY REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)

        # Overall stats
        stats = self.get_overall_stats()
        lines.append("\n📊 OVERALL STATISTICS")
        lines.append("-" * 40)
        for key, value in stats.items():
            lines.append(f"  {key.replace('_', ' ').title()}: {value}")

        # Phase inconsistencies
        phase_issues = self.get_phase_inconsistencies()
        if phase_issues:
            lines.append("\n⚠️  PHASE NAME INCONSISTENCIES")
            lines.append("-" * 40)
            lines.append("  These phase names need normalization:")
            for issue in phase_issues:
                lines.append(f"    '{issue['current']}' ({issue['count']} records) → '{issue['should_be']}'")

        # Project audits
        project_audits = self.audit_all_projects()

        lines.append("\n📁 PROJECT DATA COMPLETENESS")
        lines.append("-" * 40)

        # Summary by quality score
        critical = [p for p in project_audits if p['quality_score'] < 30]
        warning = [p for p in project_audits if 30 <= p['quality_score'] < 60]
        good = [p for p in project_audits if p['quality_score'] >= 60]

        lines.append(f"  🔴 Critical (< 30%): {len(critical)} projects")
        lines.append(f"  🟡 Warning (30-60%): {len(warning)} projects")
        lines.append(f"  🟢 Good (60%+): {len(good)} projects")

        # Show critical projects
        if critical:
            lines.append("\n  🔴 CRITICAL - Needs Immediate Attention:")
            for p in critical[:10]:
                lines.append(f"    {p['project_code']}: {p['quality_score']}% - Missing: {', '.join(p['missing'])}")

        # Proposal audit
        proposal_audit = self.audit_proposals()
        lines.append("\n📋 PROPOSAL DATA COMPLETENESS")
        lines.append("-" * 40)
        lines.append(f"  Total Proposals: {proposal_audit['total']}")
        lines.append(f"  With Emails: {proposal_audit['with_emails']} ({round(proposal_audit['with_emails']/proposal_audit['total']*100, 1)}%)")
        lines.append(f"  With Contacts: {proposal_audit['with_contacts']} ({round(proposal_audit['with_contacts']/proposal_audit['total']*100, 1)}%)")
        lines.append(f"  With Value: {proposal_audit['with_value']} ({round(proposal_audit['with_value']/proposal_audit['total']*100, 1)}%)")

        # Recommendations
        lines.append("\n💡 RECOMMENDATIONS")
        lines.append("-" * 40)

        if len(critical) > 0:
            lines.append(f"  1. Add fee breakdowns for {len([p for p in project_audits if 'fee_breakdown' in p['missing']])} projects")

        if phase_issues:
            lines.append(f"  2. Run phase normalization migration ({len(phase_issues)} inconsistent names)")

        lines.append(f"  3. Link contacts to projects (only {stats.get('contact_project_links', 0)} links exist)")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    def export_to_csv(self, output_dir: str = None):
        """Export audit data to CSV files."""
        import csv

        output_dir = output_dir or PROJECT_ROOT / 'exports'
        os.makedirs(output_dir, exist_ok=True)

        # Export project audits
        project_audits = self.audit_all_projects()
        with open(os.path.join(output_dir, 'project_audit.csv'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['project_code', 'project_title', 'quality_score', 'missing_data'])
            for p in project_audits:
                writer.writerow([
                    p['project_code'],
                    p.get('project_title', ''),
                    p['quality_score'],
                    ', '.join(p['missing'])
                ])

        print(f"Exported to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description='BDS Data Quality Audit')
    parser.add_argument('--project', '-p', help='Audit specific project code')
    parser.add_argument('--export', '-e', choices=['csv'], help='Export format')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    auditor = DataAuditor()

    try:
        if args.project:
            # Audit single project
            audit = auditor.audit_project(args.project)
            print(f"\nProject: {audit['project_code']} - {audit.get('project_title', 'N/A')}")
            print(f"Quality Score: {audit['quality_score']}%")
            print(f"Present: {', '.join(audit['present'])}")
            print(f"Missing: {', '.join(audit['missing'])}")
        elif args.export == 'csv':
            auditor.export_to_csv()
        else:
            # Full report
            report = auditor.get_data_quality_report()
            print(report)
    finally:
        auditor.close()


if __name__ == '__main__':
    main()
