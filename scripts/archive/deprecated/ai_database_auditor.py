#!/usr/bin/env python3
"""
AI Database Auditor - Pattern Detection Engine
Scans all projects and generates smart suggestions for database improvements
"""

import sqlite3
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

# Database configuration
DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

class DatabaseAuditor:
    """AI-powered database auditor that detects patterns and generates suggestions"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.suggestions = []
        self.patterns = {}

    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()

    def extract_year_from_code(self, project_code: str) -> Optional[int]:
        """Extract year from project code like '13 BK-024' -> 2013"""
        if not project_code:
            return None

        # Match patterns like "13 BK", "24 BK", "25 BK"
        match = re.match(r'^(\d{2})\s', project_code)
        if match:
            year_suffix = int(match.group(1))
            # Assume 00-30 = 2000-2030, 31-99 = 1931-1999
            if year_suffix <= 30:
                return 2000 + year_suffix
            else:
                return 1900 + year_suffix
        return None

    def get_all_projects(self) -> List[Dict]:
        """Get all projects from both proposals and projects tables"""
        cursor = self.conn.cursor()

        # Get from projects table (has all the rich data)
        cursor.execute("""
            SELECT
                proposal_id as id,
                project_code,
                project_name,
                status,
                is_active_project,
                total_fee_usd,
                paid_to_date_usd,
                outstanding_usd,
                contract_signed_date,
                health_score,
                days_since_contact,
                last_contact_date,
                next_action,
                'projects' as source_table
            FROM projects
        """)

        projects = []
        for row in cursor.fetchall():
            projects.append(dict(row))

        # Also get from proposals table (older data, fewer columns)
        cursor.execute("""
            SELECT
                project_id as id,
                project_code,
                project_title as project_name,
                status,
                0 as is_active_project,
                total_fee_usd,
                NULL as paid_to_date_usd,
                NULL as outstanding_usd,
                NULL as contract_signed_date,
                NULL as health_score,
                NULL as days_since_contact,
                NULL as last_contact_date,
                NULL as next_action,
                'proposals' as source_table
            FROM proposals
        """)

        for row in cursor.fetchall():
            projects.append(dict(row))

        return projects

    def count_invoices(self, project_code: str) -> int:
        """Count invoices for a project"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM documents
            WHERE project_code = ?
            AND document_type = 'invoice'
        """, (project_code,))
        result = cursor.fetchone()
        return result['count'] if result else 0

    def count_emails(self, project_code: str) -> int:
        """Count emails linked to a project"""
        cursor = self.conn.cursor()

        # Try from projects table first
        cursor.execute("""
            SELECT COUNT(DISTINCT e.email_id) as count
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            JOIN projects p ON epl.proposal_id = p.proposal_id
            WHERE p.project_code = ?
        """, (project_code,))
        result = cursor.fetchone()
        count = result['count'] if result else 0

        # Also try from proposals table
        cursor.execute("""
            SELECT COUNT(DISTINCT e.email_id) as count
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            JOIN proposals p ON epl.proposal_id = p.project_id
            WHERE p.project_code = ?
        """, (project_code,))
        result = cursor.fetchone()
        count += result['count'] if result else 0

        return count

    def get_days_since_contact(self, project_code: str) -> Optional[int]:
        """Get days since last contact"""
        cursor = self.conn.cursor()

        # Try both tables and get the most recent contact
        cursor.execute("""
            SELECT MAX(e.date) as last_contact
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            JOIN projects p ON epl.proposal_id = p.proposal_id
            WHERE p.project_code = ?
            UNION
            SELECT MAX(e.date) as last_contact
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            JOIN proposals p ON epl.proposal_id = p.project_id
            WHERE p.project_code = ?
        """, (project_code, project_code))

        dates = []
        for row in cursor.fetchall():
            if row['last_contact']:
                dates.append(row['last_contact'])

        if dates:
            try:
                last_contact_str = max(dates)
                last_contact = datetime.strptime(last_contact_str, '%Y-%m-%d %H:%M:%S')
                days = (datetime.now() - last_contact).days
                return days
            except:
                return None
        return None

    def check_year_based_status(self, project: Dict) -> List[Dict]:
        """Pattern: Projects from old years (< 2020) should likely be completed/archived"""
        suggestions = []

        year = self.extract_year_from_code(project['project_code'])
        if not year:
            return suggestions

        # Pattern: Very old projects (< 2020) marked as active
        if year < 2020 and project['is_active_project'] == 1:
            confidence = 0.92

            # Higher confidence if also no recent contact
            days_since_contact = self.get_days_since_contact(project['project_code'])
            if days_since_contact and days_since_contact > 730:  # 2 years
                confidence = 0.98

            suggestions.append({
                'project_code': project['project_code'],
                'suggestion_type': 'year_based_status',
                'proposed_fix': {
                    'status': 'completed' if year < 2018 else 'archived',
                    'is_active_project': 0
                },
                'evidence': {
                    'year': year,
                    'current_status': project['status'],
                    'is_active_project': project['is_active_project'],
                    'days_since_contact': days_since_contact,
                    'signals': [
                        f"Project code year: {year}",
                        f"Currently marked: active_project = {project['is_active_project']}",
                        f"Status: {project['status']}"
                    ]
                },
                'confidence': confidence,
                'pattern_id': 'pattern_year_old',
                'pattern_label': f'Legacy {year} projects still marked active'
            })

        return suggestions

    def check_invoice_presence(self, project: Dict) -> List[Dict]:
        """Pattern: Projects with invoices are NOT proposals, they're active/completed"""
        suggestions = []

        invoice_count = self.count_invoices(project['project_code'])

        # If has invoices but marked as proposal, that's wrong
        if invoice_count > 0 and project['status'] == 'proposal':
            suggestions.append({
                'project_code': project['project_code'],
                'suggestion_type': 'invoice_status_mismatch',
                'proposed_fix': {
                    'status': 'active_project',
                    'is_active_project': 1
                },
                'evidence': {
                    'invoices': invoice_count,
                    'current_status': project['status'],
                    'is_active_project': project['is_active_project'],
                    'signals': [
                        f"Found {invoice_count} invoices",
                        f"Currently marked: status = '{project['status']}'",
                        "Proposals don't have invoices - must be active/won project"
                    ]
                },
                'confidence': 0.95,
                'pattern_id': 'pattern_invoice_active',
                'pattern_label': 'Projects with invoices marked as proposals'
            })

        return suggestions

    def check_contact_history(self, project: Dict) -> List[Dict]:
        """Pattern: No contact in 2+ years likely means dead/archived"""
        suggestions = []

        days_since_contact = self.get_days_since_contact(project['project_code'])

        if not days_since_contact:
            return suggestions

        # No contact in 2+ years and still active = probably dead
        if days_since_contact > 730 and project['is_active_project'] == 1:
            # Higher confidence for older projects
            if days_since_contact > 1095:  # 3 years
                confidence = 0.90
                suggested_status = 'archived'
            else:
                confidence = 0.85
                suggested_status = 'on_hold'

            suggestions.append({
                'project_code': project['project_code'],
                'suggestion_type': 'no_contact_archived',
                'proposed_fix': {
                    'status': suggested_status,
                    'is_active_project': 0
                },
                'evidence': {
                    'days_since_contact': days_since_contact,
                    'years_since_contact': round(days_since_contact / 365, 1),
                    'current_status': project['status'],
                    'is_active_project': project['is_active_project'],
                    'signals': [
                        f"No contact in {days_since_contact} days ({round(days_since_contact/365, 1)} years)",
                        f"Currently marked: active_project = {project['is_active_project']}",
                        "Long silence suggests project is dead/archived"
                    ]
                },
                'confidence': confidence,
                'pattern_id': 'pattern_no_contact',
                'pattern_label': 'Projects with 2+ years no contact still active'
            })

        return suggestions

    def check_financial_risk(self, project: Dict) -> List[Dict]:
        """Pattern: High outstanding balance needs attention"""
        suggestions = []

        outstanding = project.get('outstanding_usd', 0) or 0
        total_fee = project.get('total_fee_usd', 0) or 0

        # High outstanding balance (>$500K) needs attention
        if outstanding > 500000:
            severity = 'high' if outstanding > 1000000 else 'medium'

            suggestions.append({
                'project_code': project['project_code'],
                'suggestion_type': 'financial_risk',
                'proposed_fix': {
                    'next_action': f'Follow up on ${outstanding:,.0f} outstanding payment'
                },
                'evidence': {
                    'outstanding_usd': outstanding,
                    'total_fee_usd': total_fee,
                    'percentage_unpaid': round((outstanding / total_fee * 100), 1) if total_fee > 0 else 0,
                    'signals': [
                        f"Outstanding balance: ${outstanding:,.0f}",
                        f"Total fee: ${total_fee:,.0f}",
                        f"Payment risk: {severity}"
                    ]
                },
                'confidence': 0.90,
                'pattern_id': 'pattern_financial_risk',
                'pattern_label': 'High outstanding balance projects'
            })

        return suggestions

    def classify_bucket(self, suggestion: Dict) -> str:
        """Classify suggestion into urgent/needs_attention/fyi bucket"""

        suggestion_type = suggestion['suggestion_type']
        confidence = suggestion['confidence']

        # Financial risk with high amounts = urgent
        if suggestion_type == 'financial_risk':
            outstanding = suggestion['evidence'].get('outstanding_usd', 0)
            if outstanding > 1000000:
                return 'urgent'
            elif outstanding > 500000:
                return 'needs_attention'

        # Very old projects still active = needs attention
        if suggestion_type == 'year_based_status':
            year = suggestion['evidence'].get('year', 2025)
            if year < 2018:
                return 'urgent'
            elif year < 2020:
                return 'needs_attention'

        # Invoice mismatch = needs attention (data quality)
        if suggestion_type == 'invoice_status_mismatch':
            return 'needs_attention'

        # No contact = needs attention or fyi
        if suggestion_type == 'no_contact_archived':
            days = suggestion['evidence'].get('days_since_contact', 0)
            if days > 1095:  # 3 years
                return 'needs_attention'
            else:
                return 'fyi'

        # Default based on confidence
        if confidence >= 0.9:
            return 'needs_attention'
        else:
            return 'fyi'

    def calculate_impact(self, suggestion: Dict, project: Dict) -> Dict:
        """Calculate impact of suggestion"""

        suggestion_type = suggestion['suggestion_type']

        if suggestion_type == 'financial_risk':
            outstanding = suggestion['evidence'].get('outstanding_usd', 0)
            return {
                'type': 'financial_risk',
                'value_usd': outstanding,
                'summary': f"${outstanding:,.0f} outstanding - needs payment follow-up",
                'severity': 'high' if outstanding > 1000000 else 'medium'
            }

        elif suggestion_type == 'year_based_status':
            year = suggestion['evidence'].get('year')
            return {
                'type': 'data_quality',
                'value_usd': None,
                'summary': f"{year} project marked active - likely completed",
                'severity': 'medium'
            }

        elif suggestion_type == 'invoice_status_mismatch':
            invoices = suggestion['evidence'].get('invoices', 0)
            return {
                'type': 'data_quality',
                'value_usd': None,
                'summary': f"Has {invoices} invoices but marked as proposal - incorrect status",
                'severity': 'medium'
            }

        elif suggestion_type == 'no_contact_archived':
            days = suggestion['evidence'].get('days_since_contact', 0)
            years = round(days / 365, 1)
            return {
                'type': 'operational',
                'value_usd': None,
                'summary': f"{years} years no contact - likely dead project",
                'severity': 'low'
            }

        return {
            'type': 'other',
            'value_usd': None,
            'summary': 'Data quality improvement',
            'severity': 'low'
        }

    def audit_project(self, project: Dict) -> List[Dict]:
        """Audit a single project and return all suggestions"""
        suggestions = []

        # Run all pattern checks
        suggestions.extend(self.check_year_based_status(project))
        suggestions.extend(self.check_invoice_presence(project))
        suggestions.extend(self.check_contact_history(project))
        suggestions.extend(self.check_financial_risk(project))

        # Enrich suggestions with metadata
        for suggestion in suggestions:
            suggestion['id'] = str(uuid.uuid4())
            suggestion['project_name'] = project['project_name']
            suggestion['is_active_project'] = project['is_active_project']
            suggestion['bucket'] = self.classify_bucket(suggestion)

            impact = self.calculate_impact(suggestion, project)
            suggestion['impact_type'] = impact['type']
            suggestion['impact_value_usd'] = impact['value_usd']
            suggestion['impact_summary'] = impact['summary']
            suggestion['severity'] = impact['severity']

            suggestion['auto_apply_candidate'] = 0  # Will be set later based on pattern stats
            suggestion['status'] = 'pending'
            suggestion['created_at'] = datetime.now().isoformat()

        return suggestions

    def run_audit(self) -> int:
        """Run audit on all projects and populate suggestions queue"""
        print("🔍 Starting database audit...")
        print(f"📊 Database: {self.db_path}\n")

        self.connect()

        # Get all projects
        projects = self.get_all_projects()
        print(f"Found {len(projects)} projects to audit\n")

        # Audit each project
        total_suggestions = 0
        pattern_counts = {}

        for i, project in enumerate(projects, 1):
            if i % 20 == 0:
                print(f"   Audited {i}/{len(projects)} projects...")

            suggestions = self.audit_project(project)

            for suggestion in suggestions:
                total_suggestions += 1
                self.suggestions.append(suggestion)

                # Track pattern counts
                pattern_id = suggestion['pattern_id']
                if pattern_id not in pattern_counts:
                    pattern_counts[pattern_id] = {
                        'label': suggestion['pattern_label'],
                        'count': 0,
                        'total_impact_usd': 0,
                        'confidence_sum': 0
                    }
                pattern_counts[pattern_id]['count'] += 1
                pattern_counts[pattern_id]['confidence_sum'] += suggestion['confidence']
                if suggestion['impact_value_usd']:
                    pattern_counts[pattern_id]['total_impact_usd'] += suggestion['impact_value_usd']

        print(f"\n✅ Audit complete!")
        print(f"📈 Generated {total_suggestions} suggestions across {len(pattern_counts)} patterns\n")

        # Save patterns
        self.save_patterns(pattern_counts)

        # Save suggestions
        self.save_suggestions()

        self.disconnect()

        return total_suggestions

    def save_patterns(self, pattern_counts: Dict):
        """Save pattern metadata to database"""
        cursor = self.conn.cursor()

        for pattern_id, data in pattern_counts.items():
            cursor.execute("""
                INSERT OR REPLACE INTO suggestion_patterns
                (pattern_id, label, detection_logic, confidence_threshold, total_suggestions, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                pattern_id,
                data['label'],
                f"Automated pattern detection - {data['label']}",
                0.7,
                data['count'],
                datetime.now().isoformat()
            ))

        self.conn.commit()
        print(f"💾 Saved {len(pattern_counts)} patterns to database")

    def save_suggestions(self):
        """Save all suggestions to database"""
        cursor = self.conn.cursor()

        # Clear existing pending suggestions
        cursor.execute("DELETE FROM ai_suggestions_queue WHERE status = 'pending'")

        # Insert new suggestions
        for suggestion in self.suggestions:
            cursor.execute("""
                INSERT INTO ai_suggestions_queue
                (id, project_code, suggestion_type, proposed_fix, evidence, confidence,
                 impact_type, impact_value_usd, impact_summary, severity, bucket,
                 pattern_id, pattern_label, auto_apply_candidate, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                suggestion['id'],
                suggestion['project_code'],
                suggestion['suggestion_type'],
                json.dumps(suggestion['proposed_fix']),
                json.dumps(suggestion['evidence']),
                suggestion['confidence'],
                suggestion['impact_type'],
                suggestion['impact_value_usd'],
                suggestion['impact_summary'],
                suggestion['severity'],
                suggestion['bucket'],
                suggestion['pattern_id'],
                suggestion['pattern_label'],
                suggestion['auto_apply_candidate'],
                suggestion['status'],
                suggestion['created_at']
            ))

        self.conn.commit()
        print(f"💾 Saved {len(self.suggestions)} suggestions to database\n")

    def print_summary(self):
        """Print summary of suggestions by bucket"""
        if not self.suggestions:
            print("No suggestions generated")
            return

        buckets = {'urgent': [], 'needs_attention': [], 'fyi': []}
        for s in self.suggestions:
            buckets[s['bucket']].append(s)

        print("=" * 60)
        print("SUGGESTION SUMMARY")
        print("=" * 60)

        for bucket in ['urgent', 'needs_attention', 'fyi']:
            items = buckets[bucket]
            if items:
                emoji = {'urgent': '🔴', 'needs_attention': '⚠️', 'fyi': '📊'}[bucket]
                print(f"\n{emoji} {bucket.upper().replace('_', ' ')}: {len(items)} suggestions")

                # Group by pattern
                patterns = {}
                for item in items:
                    pattern = item['pattern_label']
                    if pattern not in patterns:
                        patterns[pattern] = []
                    patterns[pattern].append(item)

                for pattern, items in patterns.items():
                    print(f"   ▶ {pattern}: {len(items)} items")

        print("\n" + "=" * 60)


def main():
    """Run database audit"""
    auditor = DatabaseAuditor()
    total = auditor.run_audit()
    auditor.print_summary()

    print(f"\n✅ Database audit complete!")
    print(f"📊 Total suggestions: {total}")
    print(f"🗄️  Data saved to ai_suggestions_queue table")
    print(f"\n🚀 Ready for frontend integration!\n")


if __name__ == "__main__":
    main()
