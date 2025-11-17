#!/usr/bin/env python3
"""
enhanced_report_generator.py

Generates BEAUTIFUL executive reports with charts and big numbers
"""

import os
import json
from datetime import datetime
from pathlib import Path

class EnhancedReportGenerator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.reports_dir = self.project_root / 'reports' / 'daily'
        self.tracking_file = self.project_root / 'tracking' / 'change_history.json'
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _load_history(self):
        """Load change history for trend data"""
        if self.tracking_file.exists():
            with open(self.tracking_file, 'r') as f:
                return json.load(f)
        return {'snapshots': [], 'decisions': []}

    def _get_trend_data(self):
        """Get historical data for charts"""
        history = self._load_history()
        snapshots = history.get('snapshots', [])[-30:]  # Last 30 snapshots

        dates = []
        emails = []
        proposals = []
        documents = []
        contacts = []

        for snapshot in snapshots:
            dates.append(snapshot['timestamp'][:10])  # YYYY-MM-DD
            db = snapshot.get('database', {})
            emails.append(db.get('emails', 0))
            proposals.append(db.get('proposals', 0))
            documents.append(db.get('documents', 0))
            contacts.append(db.get('contacts_only', 0))

        return {
            'dates': dates,
            'emails': emails,
            'proposals': proposals,
            'documents': documents,
            'contacts': contacts
        }

    def generate_html_report(self, data):
        """Generate BEAUTIFUL executive report"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"bensley_brain_report_{date_str}.html"
        filepath = self.reports_dir / filename

        stats = data.get('database_stats', {})
        changes = data.get('changes', {})
        trend_data = self._get_trend_data()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bensley Brain Executive Report - {date_str}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .header h1 {{
            font-size: 48px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            font-size: 18px;
            color: #666;
        }}

        /* EXECUTIVE SUMMARY */
        .executive-summary {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .executive-summary h2 {{
            font-size: 32px;
            margin-bottom: 30px;
            color: #1a1a1a;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 30px;
            color: white;
            position: relative;
            overflow: hidden;
        }}
        .metric-card::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        }}
        .metric-value {{
            font-size: 56px;
            font-weight: bold;
            margin-bottom: 10px;
            position: relative;
        }}
        .metric-label {{
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.9;
            position: relative;
        }}
        .metric-change {{
            font-size: 18px;
            margin-top: 10px;
            position: relative;
        }}
        .metric-change.positive {{ color: #4ade80; }}
        .metric-change.negative {{ color: #f87171; }}

        /* ALIGNMENT STATUS */
        .alignment-status {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .status-header {{
            display: flex;
            align-items: center;
            margin-bottom: 30px;
        }}
        .status-icon {{
            font-size: 64px;
            margin-right: 20px;
        }}
        .status-text h2 {{
            font-size: 32px;
            margin-bottom: 5px;
        }}
        .status-text p {{
            font-size: 18px;
            color: #666;
        }}
        .progress-bar {{
            height: 40px;
            background: #e5e7eb;
            border-radius: 20px;
            overflow: hidden;
            margin-bottom: 20px;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 18px;
            transition: width 1s ease;
        }}

        /* CHARTS */
        .charts-section {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .charts-section h2 {{
            font-size: 28px;
            margin-bottom: 30px;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            margin-bottom: 40px;
        }}

        /* DETAILS SECTION */
        .details-section {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .details-section h2 {{
            font-size: 28px;
            margin-bottom: 20px;
            color: #1a1a1a;
        }}
        .details-section h3 {{
            font-size: 22px;
            margin-top: 30px;
            margin-bottom: 15px;
            color: #333;
        }}

        /* CRITICAL FINDINGS */
        .finding {{
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            border-left: 5px solid;
        }}
        .finding.critical {{
            background: #fee;
            border-color: #ef4444;
        }}
        .finding.warning {{
            background: #fef9e7;
            border-color: #f59e0b;
        }}
        .finding.positive {{
            background: #efe;
            border-color: #22c55e;
        }}
        .finding-icon {{
            font-size: 24px;
            margin-right: 10px;
        }}

        /* RECOMMENDATIONS */
        .recommendations {{
            background: linear-gradient(135deg, #f0f7ff 0%, #e0f2fe 100%);
            border-radius: 15px;
            padding: 30px;
            margin-top: 30px;
        }}
        .recommendations h3 {{
            color: #0066cc;
            margin-bottom: 20px;
        }}
        .recommendations ol {{
            margin-left: 20px;
        }}
        .recommendations li {{
            margin: 15px 0;
            font-size: 18px;
        }}

        /* TABLE */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}
        th {{
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
        }}
        tr:hover {{
            background: #f9fafb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <h1>🧠 Bensley Brain</h1>
            <p class="subtitle">Daily Intelligence Report · {datetime.now().strftime('%B %d, %Y')}</p>
        </div>

        <!-- EXECUTIVE SUMMARY -->
        <div class="executive-summary">
            <h2>📊 Executive Summary</h2>
            <div class="metrics-grid">
                {self._generate_metric_card('Proposals', stats.get('proposals', 0), changes)}
                {self._generate_metric_card('Emails', stats.get('emails', 0), changes)}
                {self._generate_metric_card('Documents', stats.get('documents', 0), changes)}
                {self._generate_metric_card('Contacts', stats.get('contacts_only', 0), changes)}
                {self._generate_metric_card('Database', f"{stats.get('db_size_mb', 0):.0f} MB", changes)}
                {self._generate_metric_card('Indexes', stats.get('indexes', 0), changes)}
            </div>
        </div>

        <!-- ALIGNMENT STATUS -->
        {self._generate_alignment_section(data.get('alignment', {}))}

        <!-- CHARTS -->
        <div class="charts-section">
            <h2>📈 Growth Over Time</h2>
            <div class="chart-container">
                <canvas id="trendsChart"></canvas>
            </div>
        </div>

        <!-- CRITICAL FINDINGS -->
        <div class="details-section">
            <h2>🔍 Critical Audit Findings</h2>
            {self._generate_findings_html(data.get('audit_findings', {}))}
        </div>

        <!-- RECOMMENDATIONS -->
        <div class="details-section">
            <div class="recommendations">
                <h3>🎯 Top Recommendations for Tomorrow</h3>
                {self._generate_recommendations_list(data.get('recommendations', []))}
            </div>
        </div>

        <!-- DETAILED CHANGES -->
        <div class="details-section">
            <h2>📝 What Changed Today</h2>
            {self._generate_detailed_changes(changes, data.get('git_activity', {}))}
        </div>

        <!-- SUMMARY TEXT -->
        <div class="details-section">
            <h2>✨ Daily Summary</h2>
            <p style="font-size: 18px; line-height: 1.8; color: #374151;">
                {data.get('daily_summary', {}).get('summary', 'No summary available')}
            </p>
        </div>
    </div>

    <script>
        // TREND CHART
        const ctx = document.getElementById('trendsChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(trend_data['dates'])},
                datasets: [
                    {{
                        label: 'Emails',
                        data: {json.dumps(trend_data['emails'])},
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }},
                    {{
                        label: 'Contacts',
                        data: {json.dumps(trend_data['contacts'])},
                        borderColor: '#764ba2',
                        backgroundColor: 'rgba(118, 75, 162, 0.1)',
                        tension: 0.4,
                        fill: true
                    }},
                    {{
                        label: 'Documents',
                        data: {json.dumps(trend_data['documents'])},
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4,
                        fill: true
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'top',
                        labels: {{
                            font: {{ size: 14 }},
                            padding: 20
                        }}
                    }},
                    title: {{
                        display: true,
                        text: 'Database Growth Trends',
                        font: {{ size: 18 }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            font: {{ size: 12 }}
                        }}
                    }},
                    x: {{
                        ticks: {{
                            font: {{ size: 12 }},
                            maxRotation: 45,
                            minRotation: 45
                        }}
                    }}
                }}
            }}
        }});

        // Animate progress bar
        window.addEventListener('load', () => {{
            const progressFill = document.querySelector('.progress-fill');
            if (progressFill) {{
                setTimeout(() => {{
                    progressFill.style.width = progressFill.dataset.width;
                }}, 500);
            }}
        }});
    </script>
</body>
</html>"""

        filepath.write_text(html)
        print(f"   ✅ Enhanced HTML report: {filepath}")
        return filepath

    def _generate_metric_card(self, label, value, changes):
        """Generate a metric card with big numbers"""
        # Calculate change if available
        change_html = ""
        if label.lower() in [k.lower() for k in changes.get('database_changes', {}).keys()]:
            for key, change_data in changes.get('database_changes', {}).items():
                if key.lower() == label.lower():
                    change_val = change_data.get('change', 0)
                    if change_val != 0:
                        change_class = 'positive' if change_val > 0 else 'negative'
                        change_html = f'<div class="metric-change {change_class}">{change_val:+,} today</div>'

        # Format value
        if isinstance(value, (int, float)) and not isinstance(value, str):
            formatted_value = f"{value:,}"
        else:
            formatted_value = value

        return f"""
        <div class="metric-card">
            <div class="metric-value">{formatted_value}</div>
            <div class="metric-label">{label}</div>
            {change_html}
        </div>"""

    def _generate_alignment_section(self, alignment):
        """Generate alignment status section"""
        on_track = alignment.get('on_track', True)
        progress = alignment.get('progress_pct', 0)
        phase = alignment.get('current_phase', 'Unknown')
        notes = alignment.get('notes', '')

        icon = '✅' if on_track else '⚠️'
        status_text = 'ON TRACK' if on_track else 'NEEDS ATTENTION'
        status_color = '#22c55e' if on_track else '#f59e0b'

        return f"""
        <div class="alignment-status">
            <div class="status-header">
                <div class="status-icon">{icon}</div>
                <div class="status-text">
                    <h2 style="color: {status_color};">{status_text}</h2>
                    <p>{phase}</p>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" data-width="{progress}%" style="width: 0%;">{progress}% Complete</div>
            </div>
            <p style="font-size: 18px; color: #374151;">{notes}</p>
        </div>"""

    def _generate_findings_html(self, audit):
        """Generate audit findings with icons"""
        html = ""

        critical = audit.get('critical_issues', [])
        warnings = audit.get('warnings', [])
        positive = audit.get('positive', [])

        if critical:
            html += "<h3>🔴 Critical Issues</h3>"
            for issue in critical:
                html += f'<div class="finding critical"><span class="finding-icon">🔴</span>{issue}</div>'

        if warnings:
            html += "<h3>🟡 Warnings</h3>"
            for warning in warnings:
                html += f'<div class="finding warning"><span class="finding-icon">🟡</span>{warning}</div>'

        if positive:
            html += "<h3>🟢 What's Working Well</h3>"
            for item in positive:
                html += f'<div class="finding positive"><span class="finding-icon">🟢</span>{item}</div>'

        return html if html else "<p>No audit findings available</p>"

    def _generate_recommendations_list(self, recommendations):
        """Generate recommendations list"""
        if not recommendations:
            return "<p>No specific recommendations</p>"

        html = "<ol>"
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        html += "</ol>"
        return html

    def _generate_detailed_changes(self, changes, git_activity):
        """Generate detailed changes section"""
        html = ""

        # Database changes
        db_changes = changes.get('database_changes', {})
        if db_changes:
            html += "<h3>Database Changes</h3>"
            html += "<table><thead><tr><th>Metric</th><th>Before</th><th>After</th><th>Change</th></tr></thead><tbody>"
            for key, data in db_changes.items():
                change_val = data.get('change', 0)
                change_style = 'color: #22c55e;' if change_val > 0 else 'color: #ef4444;' if change_val < 0 else ''
                html += f"""<tr>
                    <td><strong>{key}</strong></td>
                    <td>{data.get('before', 0):,}</td>
                    <td>{data.get('after', 0):,}</td>
                    <td style="{change_style}"><strong>{change_val:+,}</strong></td>
                </tr>"""
            html += "</tbody></table>"
        else:
            html += "<p>No database changes detected today</p>"

        # Git activity
        commits = git_activity.get('commit_messages', [])
        if commits:
            html += f"<h3>Git Commits ({len(commits)} today)</h3><ul>"
            for commit in commits[:10]:
                html += f"<li><code>{commit}</code></li>"
            html += "</ul>"

        return html

if __name__ == '__main__':
    # Test the enhanced report
    generator = EnhancedReportGenerator()

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
            }
        },
        'git_activity': {
            'commit_messages': ['Add migration 011', 'Add migration 012'],
        },
        'daily_summary': {
            'summary': 'Fixed critical issues from agent audit. Added enhanced categorization, extracted contacts, and added performance indexes. On track for Phase 1 completion.'
        },
        'audit_findings': {
            'critical_issues': ['Email content table still empty'],
            'warnings': ['Need to import remaining 2,215 emails'],
            'positive': ['Contact extraction working perfectly', 'Database well-optimized']
        },
        'recommendations': [
            'Re-run email_content_processor.py',
            'Import remaining 2,215 emails',
            'Build query interface'
        ],
        'alignment': {
            'on_track': True,
            'current_phase': 'Phase 1: Proposal Intelligence System',
            'progress_pct': 80,
            'notes': 'Critical fixes completed. Ready to continue with email import.'
        }
    }

    html_path = generator.generate_html_report(test_data)
    print(f"\nTest report generated: {html_path}")
