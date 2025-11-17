#!/usr/bin/env python3
"""
report_generator.py

Generates beautiful daily reports in both PDF and HTML formats
"""

import os
from datetime import datetime
from pathlib import Path
import json

class ReportGenerator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.reports_dir = self.project_root / 'reports' / 'daily'
        self.archive_dir = self.project_root / 'reports' / 'archive'
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(self, data):
        """Generate interactive HTML report"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"bensley_brain_report_{date_str}.html"
        filepath = self.reports_dir / filename

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bensley Brain Daily Report - {date_str}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a1a1a;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 15px;
        }}
        h2 {{
            color: #333;
            margin-top: 40px;
            border-left: 4px solid #0066cc;
            padding-left: 15px;
        }}
        h3 {{
            color: #555;
            margin-top: 25px;
        }}
        .metric {{
            display: inline-block;
            background: #f0f7ff;
            padding: 15px 25px;
            margin: 10px;
            border-radius: 8px;
            border-left: 4px solid #0066cc;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #0066cc;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
        }}
        .success {{ color: #22c55e; }}
        .warning {{ color: #f59e0b; }}
        .error {{ color: #ef4444; }}
        .info {{ color: #0066cc; }}
        .section {{
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 8px;
        }}
        .critical {{
            background: #fee;
            border-left: 4px solid #ef4444;
            padding: 15px;
            margin: 10px 0;
        }}
        .positive {{
            background: #efe;
            border-left: 4px solid #22c55e;
            padding: 15px;
            margin: 10px 0;
        }}
        .neutral {{
            background: #fef9e7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 10px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f0f7ff;
            color: #0066cc;
            font-weight: 600;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Courier New', monospace;
        }}
        ul {{
            line-height: 1.8;
        }}
        .timestamp {{
            color: #999;
            font-size: 14px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin: 0 5px;
        }}
        .badge-success {{ background: #22c55e; color: white; }}
        .badge-warning {{ background: #f59e0b; color: white; }}
        .badge-error {{ background: #ef4444; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Bensley Brain Daily Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>

        <!-- Metrics Dashboard -->
        <h2>📊 Today's Metrics</h2>
        <div class="section">
            {self._generate_metrics_html(data.get('database_stats', {}))}
        </div>

        <!-- Changes Summary -->
        <h2>📝 What Changed Today</h2>
        <div class="section">
            {self._generate_changes_html(data.get('changes', {}))}
        </div>

        <!-- Git Activity -->
        <h2>💻 Git Activity</h2>
        <div class="section">
            {self._generate_git_html(data.get('git_activity', {}))}
        </div>

        <!-- Daily Summary -->
        <h2>✨ Daily Summary</h2>
        <div class="section">
            {self._generate_summary_html(data.get('daily_summary', {}))}
        </div>

        <!-- Critical Audit -->
        <h2>🔍 Critical Audit Findings</h2>
        <div class="section">
            {self._generate_audit_html(data.get('audit_findings', {}))}
        </div>

        <!-- Recommendations -->
        <h2>🎯 Recommendations for Tomorrow</h2>
        <div class="section">
            {self._generate_recommendations_html(data.get('recommendations', []))}
        </div>

        <!-- Alignment Check -->
        <h2>🧭 Alignment with Goals</h2>
        <div class="section">
            {self._generate_alignment_html(data.get('alignment', {}))}
        </div>
    </div>
</body>
</html>"""

        filepath.write_text(html)
        print(f"   ✅ HTML report: {filepath}")
        return filepath

    def _generate_metrics_html(self, stats):
        """Generate metrics HTML"""
        metrics = [
            ('proposals', 'Proposals'),
            ('emails', 'Emails'),
            ('documents', 'Documents'),
            ('contacts_only', 'Contacts'),
            ('indexes', 'Indexes')
        ]

        html = ""
        for key, label in metrics:
            value = stats.get(key, 0)
            html += f"""
            <div class="metric">
                <div class="metric-value">{value:,}</div>
                <div class="metric-label">{label}</div>
            </div>"""

        # Database size
        db_size = stats.get('db_size_mb', 0)
        html += f"""
        <div class="metric">
            <div class="metric-value">{db_size:.1f} MB</div>
            <div class="metric-label">Database Size</div>
        </div>"""

        return html

    def _generate_changes_html(self, changes):
        """Generate changes HTML"""
        html = "<h3>Database Changes</h3>"

        db_changes = changes.get('database_changes', {})
        if db_changes:
            html += "<table><thead><tr><th>Metric</th><th>Before</th><th>After</th><th>Change</th></tr></thead><tbody>"
            for key, data in db_changes.items():
                change_val = data.get('change', 0)
                change_class = 'success' if change_val > 0 else 'error' if change_val < 0 else ''
                html += f"""<tr>
                    <td><strong>{key}</strong></td>
                    <td>{data.get('before', 0):,}</td>
                    <td>{data.get('after', 0):,}</td>
                    <td class="{change_class}"><strong>{change_val:+,}</strong></td>
                </tr>"""
            html += "</tbody></table>"
        else:
            html += "<p class='neutral'>No database changes detected</p>"

        # Files changed
        files = changes.get('files_changed', [])
        if files:
            html += "<h3>Files Modified</h3><ul>"
            for f in files:
                html += f"<li><code>{f}</code></li>"
            html += "</ul>"

        return html

    def _generate_git_html(self, git_activity):
        """Generate git activity HTML"""
        html = ""
        commits = git_activity.get('commit_messages', [])

        if commits:
            html = f"<p><strong>{len(commits)} commits today</strong></p><ul>"
            for commit in commits[:10]:
                html += f"<li><code>{commit}</code></li>"
            html += "</ul>"
        else:
            html = "<p class='neutral'>No commits today</p>"

        files_changed = git_activity.get('files_changed', [])
        if files_changed:
            html += f"<p><strong>{len(files_changed)} files changed</strong></p>"

        return html

    def _generate_summary_html(self, summary):
        """Generate daily summary HTML"""
        html = summary.get('summary', '<p>No summary available</p>')
        return f"<div>{html}</div>"

    def _generate_audit_html(self, audit):
        """Generate audit findings HTML"""
        critical = audit.get('critical_issues', [])
        warnings = audit.get('warnings', [])
        positive = audit.get('positive', [])

        html = ""

        if critical:
            html += "<h3 class='error'>🔴 Critical Issues</h3>"
            for issue in critical:
                html += f"<div class='critical'>{issue}</div>"

        if warnings:
            html += "<h3 class='warning'>🟡 Warnings</h3>"
            for warning in warnings:
                html += f"<div class='neutral'>{warning}</div>"

        if positive:
            html += "<h3 class='success'>🟢 What's Working Well</h3>"
            for item in positive:
                html += f"<div class='positive'>{item}</div>"

        if not (critical or warnings or positive):
            html = "<p class='neutral'>No audit findings available</p>"

        return html

    def _generate_recommendations_html(self, recommendations):
        """Generate recommendations HTML"""
        if not recommendations:
            return "<p class='neutral'>No specific recommendations</p>"

        html = "<ol>"
        for rec in recommendations:
            html += f"<li><strong>{rec}</strong></li>"
        html += "</ol>"

        return html

    def _generate_alignment_html(self, alignment):
        """Generate alignment check HTML"""
        on_track = alignment.get('on_track', True)
        phase = alignment.get('current_phase', 'Unknown')
        progress = alignment.get('progress_pct', 0)

        status_class = 'success' if on_track else 'warning'
        status_text = '✅ On Track' if on_track else '⚠️ Needs Attention'

        html = f"""
        <div class='{status_class}'>
            <h3>{status_text}</h3>
            <p><strong>Current Phase:</strong> {phase}</p>
            <p><strong>Progress:</strong> {progress}%</p>
            <p>{alignment.get('notes', '')}</p>
        </div>
        """

        return html

    def generate_pdf_report(self, data):
        """Generate PDF report (simplified version for email)"""
        # For now, we'll use a simple text-based approach
        # TODO: Add proper PDF generation with reportlab
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"bensley_brain_report_{date_str}.txt"
        filepath = self.reports_dir / filename

        report = f"""
BENSLEY BRAIN DAILY REPORT
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

{'='*80}
TODAY'S METRICS
{'='*80}

{self._generate_metrics_text(data.get('database_stats', {}))}

{'='*80}
WHAT CHANGED TODAY
{'='*80}

{self._generate_changes_text(data.get('changes', {}))}

{'='*80}
GIT ACTIVITY
{'='*80}

{self._generate_git_text(data.get('git_activity', {}))}

{'='*80}
DAILY SUMMARY
{'='*80}

{data.get('daily_summary', {}).get('summary', 'No summary available')}

{'='*80}
CRITICAL AUDIT FINDINGS
{'='*80}

{self._generate_audit_text(data.get('audit_findings', {}))}

{'='*80}
RECOMMENDATIONS FOR TOMORROW
{'='*80}

{self._generate_recommendations_text(data.get('recommendations', []))}

{'='*80}
ALIGNMENT WITH GOALS
{'='*80}

{self._generate_alignment_text(data.get('alignment', {}))}

"""

        filepath.write_text(report)
        print(f"   ✅ Text report (PDF placeholder): {filepath}")
        return filepath

    def _generate_metrics_text(self, stats):
        """Generate metrics as text"""
        text = ""
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                if isinstance(value, float) and value < 100:
                    text += f"{key}: {value:.1f}\n"
                else:
                    text += f"{key}: {value:,}\n"
        return text

    def _generate_changes_text(self, changes):
        """Generate changes as text"""
        text = ""

        db_changes = changes.get('database_changes', {})
        if db_changes:
            text += "Database Changes:\n"
            for key, data in db_changes.items():
                text += f"  {key}: {data.get('before', 0):,} → {data.get('after', 0):,} ({data.get('change', 0):+,})\n"
        else:
            text += "No database changes detected\n"

        files = changes.get('files_changed', [])
        if files:
            text += f"\nFiles Modified ({len(files)}):\n"
            for f in files:
                text += f"  - {f}\n"

        return text

    def _generate_git_text(self, git_activity):
        """Generate git activity as text"""
        commits = git_activity.get('commit_messages', [])
        if commits:
            text = f"{len(commits)} commits today:\n"
            for commit in commits[:10]:
                text += f"  - {commit}\n"
        else:
            text = "No commits today\n"
        return text

    def _generate_audit_text(self, audit):
        """Generate audit findings as text"""
        text = ""

        critical = audit.get('critical_issues', [])
        if critical:
            text += "CRITICAL ISSUES:\n"
            for issue in critical:
                text += f"  🔴 {issue}\n"

        warnings = audit.get('warnings', [])
        if warnings:
            text += "\nWARNINGS:\n"
            for warning in warnings:
                text += f"  🟡 {warning}\n"

        positive = audit.get('positive', [])
        if positive:
            text += "\nWHAT'S WORKING WELL:\n"
            for item in positive:
                text += f"  🟢 {item}\n"

        return text if text else "No audit findings available\n"

    def _generate_recommendations_text(self, recommendations):
        """Generate recommendations as text"""
        if not recommendations:
            return "No specific recommendations\n"

        text = ""
        for i, rec in enumerate(recommendations, 1):
            text += f"{i}. {rec}\n"
        return text

    def _generate_alignment_text(self, alignment):
        """Generate alignment check as text"""
        on_track = alignment.get('on_track', True)
        status = "✅ ON TRACK" if on_track else "⚠️  NEEDS ATTENTION"

        text = f"""{status}

Current Phase: {alignment.get('current_phase', 'Unknown')}
Progress: {alignment.get('progress_pct', 0)}%

{alignment.get('notes', '')}
"""
        return text

if __name__ == '__main__':
    # Test report generation
    generator = ReportGenerator()

    test_data = {
        'database_stats': {
            'proposals': 87,
            'emails': 132,
            'documents': 852,
            'contacts_only': 205,
            'indexes': 84,
            'db_size_mb': 28.5
        },
        'changes': {
            'database_changes': {
                'emails': {'before': 78, 'after': 132, 'change': 54},
                'contacts_only': {'before': 23, 'after': 205, 'change': 182}
            },
            'files_changed': ['database/migrations/011_improved_email_categories.sql',
                            'database/migrations/012_critical_query_indexes.sql']
        },
        'git_activity': {
            'commit_messages': ['Add migration 011', 'Add migration 012', 'Extract contacts'],
            'files_changed': ['database/migrations/011_improved_email_categories.sql']
        },
        'daily_summary': {
            'summary': 'Fixed critical issues from agent audit. Added enhanced categorization, extracted contacts, and added performance indexes.'
        },
        'audit_findings': {
            'critical_issues': ['Email content table still empty'],
            'warnings': ['Need to import remaining 2,215 emails'],
            'positive': ['Contact extraction working perfectly', 'Database well-indexed']
        },
        'recommendations': [
            'Import remaining emails using smart_email_matcher.py',
            'Re-run email content processor to populate email_content table',
            'Build query interface for natural language queries'
        ],
        'alignment': {
            'on_track': True,
            'current_phase': 'Phase 1: Proposal Intelligence System',
            'progress_pct': 80,
            'notes': 'Critical fixes completed. Ready to continue with email import.'
        }
    }

    html_path = generator.generate_html_report(test_data)
    pdf_path = generator.generate_pdf_report(test_data)

    print(f"\n✅ Reports generated:")
    print(f"   HTML: {html_path}")
    print(f"   PDF:  {pdf_path}")
