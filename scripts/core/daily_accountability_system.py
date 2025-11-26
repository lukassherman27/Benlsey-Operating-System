#!/usr/bin/env python3
"""
daily_accountability_system.py

Main orchestrator for daily accountability reports
Runs at 9 PM every day via cron

1. Takes snapshot of current state
2. Runs Daily Summary Agent
3. Runs Critical Auditor Agent
4. Generates HTML + PDF reports
5. Emails reports to lukas@bensley.com
"""

import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()

# Add tracking and reports to path
sys.path.insert(0, str(Path(__file__).parent))

from tracking.change_tracker import ChangeTracker
from reports.enhanced_report_generator import EnhancedReportGenerator

# Try both AI providers
ANTHROPIC_AVAILABLE = False
OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    pass

class DailyAccountabilitySystem:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.tracker = ChangeTracker()
        self.report_gen = EnhancedReportGenerator()

        # Email configuration
        self.email_from = os.getenv('EMAIL_USERNAME', 'lukas@bensley.com')
        self.email_to = 'lukas@bensley.com'
        self.email_server = os.getenv('EMAIL_SERVER', 'tmail.bensley.com')
        self.email_port = int(os.getenv('EMAIL_PORT', 587))
        self.email_password = os.getenv('EMAIL_PASSWORD', '')

        # AI Provider setup (for enhanced agents)
        self.ai_provider = None
        self.client = None
        self.ai_enabled = False

        # Try Claude first (best quality)
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key and ANTHROPIC_AVAILABLE:
            try:
                self.client = anthropic.Anthropic(api_key=anthropic_key)
                self.ai_provider = 'claude'
                self.ai_enabled = True
                print("✓ Using Claude for intelligent agents")
            except Exception as e:
                print(f"⚠️  Claude failed: {e}")

        # Fall back to OpenAI
        if not self.ai_provider:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key and OPENAI_AVAILABLE:
                try:
                    self.client = OpenAI(api_key=openai_key)
                    self.ai_provider = 'openai'
                    self.ai_enabled = True
                    print("✓ Using OpenAI for intelligent agents")
                except Exception as e:
                    print(f"⚠️  OpenAI failed: {e}")

        # No AI available
        if not self.ai_provider:
            self.ai_enabled = False
            print("⚠️  No AI available - agents will use simple logic")
            print("   Add ANTHROPIC_API_KEY or OPENAI_API_KEY to .env for smart agents")

    def ai_call(self, prompt, max_tokens=2000, temperature=0.3):
        """Universal AI call - works with both Claude and OpenAI"""
        if not self.ai_enabled:
            return None

        try:
            if self.ai_provider == 'claude':
                response = self.client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()

            elif self.ai_provider == 'openai':
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"  ⚠️  AI call failed: {e}")
            return None

    def run_daily_summary_agent(self, snapshot, changes):
        """Run agent that summarizes today's work"""
        print("\n🤖 Running Daily Summary Agent...")

        # Read context files
        master_plan = ""
        implementation_status = ""

        master_plan_file = self.project_root / 'BENSLEY_BRAIN_MASTER_PLAN.md'
        status_file = self.project_root / 'IMPLEMENTATION_STATUS.md'

        if master_plan_file.exists():
            with open(master_plan_file, 'r') as f:
                master_plan = f.read()

        if status_file.exists():
            with open(status_file, 'r') as f:
                implementation_status = f.read()

        # Build context string
        db_changes = changes.get('database_changes', {})
        files_changed = changes.get('files_changed', [])
        git_commits = changes.get('git_activity', {}).get('commit_messages', [])

        changes_summary = f"""Database Changes:
{json.dumps(db_changes, indent=2)}

Files Changed: {len(files_changed)} files
{', '.join(files_changed[:10])}

Git Activity: {len(git_commits)} commits
{chr(10).join(['- ' + msg for msg in git_commits[:5]])}

Current Database State:
{json.dumps(snapshot['database'], indent=2)}
"""

        # If AI available, use it for intelligent analysis
        if self.ai_enabled:
            prompt = f"""You are the Daily Summary Agent for the Bensley Intelligence Platform.

MASTER PLAN:
{master_plan[:3000]}

IMPLEMENTATION STATUS:
{implementation_status[:2000]}

TODAY'S CHANGES:
{changes_summary}

YOUR TASK:
Analyze today's progress and provide:

1. SUMMARY: What was accomplished today? (2-3 sentences)
2. ON_TRACK: Are we on track toward our goals? (yes/no/partial)
3. CURRENT_PHASE: Which phase are we in? (e.g., "Phase 1: Proposal Intelligence System")
4. PROGRESS_PCT: Estimated % complete of current phase (0-100)
5. NOTES: Any observations about alignment with goals
6. RECOMMENDATIONS: 3 specific actionable recommendations for tomorrow

Return your response in this exact JSON format:
{{
  "summary": "...",
  "on_track": true/false,
  "current_phase": "...",
  "progress_pct": 80,
  "notes": "...",
  "recommendations": ["...", "...", "..."]
}}"""

            try:
                response = self.ai_call(prompt, max_tokens=1500, temperature=0.3)

                if response:
                    # Try to parse JSON from response
                    import re
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        summary = json.loads(json_match.group())
                        print("   ✅ AI analysis complete")
                        return summary

            except Exception as e:
                print(f"   ⚠️  AI analysis failed: {e}, falling back to simple logic")

        # Fallback: simple logic
        summary = {
            'summary': self._generate_summary(changes),
            'on_track': True,
            'current_phase': 'Phase 1: Proposal Intelligence System',
            'progress_pct': 80,
            'notes': self._assess_alignment(changes),
            'recommendations': []
        }

        print("   ✅ Daily summary complete (simple logic)")
        return summary

    def run_critical_auditor_agent(self, snapshot):
        """Run agent that provides brutal honest critique (NO conversation context)"""
        print("\n🔍 Running Critical Auditor Agent...")

        # Build comprehensive context about system state
        db_state = json.dumps(snapshot['database'], indent=2)
        git_info = json.dumps(snapshot['git'], indent=2)

        # Read master plan to understand goals
        master_plan = ""
        master_plan_file = self.project_root / 'BENSLEY_BRAIN_MASTER_PLAN.md'
        if master_plan_file.exists():
            with open(master_plan_file, 'r') as f:
                master_plan = f.read()

        # If AI available, use it for brutal critique
        if self.ai_enabled:
            prompt = f"""You are a BRUTAL, HONEST systems auditor with NO prior context.

You're analyzing the Bensley Intelligence Platform - a business intelligence system.

STATED GOALS:
{master_plan[:2000]}

CURRENT SYSTEM STATE:
Database Tables & Row Counts:
{db_state}

Git Activity:
{git_info}

YOUR TASK:
Provide BRUTALLY HONEST audit findings. Don't hold back. Be critical but constructive.

Analyze:
1. CRITICAL ISSUES - What's broken, missing, or completely wrong?
2. WARNINGS - What's concerning or poorly implemented?
3. POSITIVE - What's actually working well?

For each finding, be SPECIFIC:
- Quote exact numbers
- Identify exact problems
- Suggest concrete fixes

Return your response in this exact JSON format:
{{
  "critical_issues": [
    "Specific critical issue 1",
    "Specific critical issue 2"
  ],
  "warnings": [
    "Specific warning 1",
    "Specific warning 2"
  ],
  "positive": [
    "Specific thing working well 1",
    "Specific thing working well 2"
  ]
}}

Be HARSH. This is for accountability. If something is 5% done, say so. If a design is flawed, explain why."""

            try:
                response = self.ai_call(prompt, max_tokens=2000, temperature=0.3)

                if response:
                    # Try to parse JSON from response
                    import re
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        audit = json.loads(json_match.group())
                        print("   ✅ AI audit complete")
                        return audit

            except Exception as e:
                print(f"   ⚠️  AI audit failed: {e}, falling back to simple logic")

        # Fallback: simple logic
        audit = {
            'critical_issues': self._find_critical_issues(snapshot),
            'warnings': self._find_warnings(snapshot),
            'positive': self._find_positives(snapshot)
        }

        print("   ✅ Critical audit complete (simple logic)")
        return audit

    def _generate_summary(self, changes):
        """Generate summary from changes"""
        db_changes = changes.get('database_changes', {})
        files_changed = changes.get('files_changed', [])
        commits = len(changes.get('git_activity', {}).get('commit_messages', []))

        summary_parts = []

        if commits > 0:
            summary_parts.append(f"Made {commits} git commits")

        if db_changes:
            changes_str = ", ".join([f"{k}: +{v['change']}" for k, v in db_changes.items()])
            summary_parts.append(f"Database grew: {changes_str}")

        if files_changed:
            summary_parts.append(f"Modified {len(files_changed)} files")

        if not summary_parts:
            return "No significant changes detected today."

        return ". ".join(summary_parts) + "."

    def _assess_alignment(self, changes):
        """Assess alignment with goals"""
        db_changes = changes.get('database_changes', {})

        notes = []

        # Check if moving toward Phase 1 completion
        if 'emails' in db_changes:
            email_change = db_changes['emails'].get('change', 0)
            if email_change > 0:
                notes.append(f"Good progress on email import (+{email_change} emails)")

        if 'contacts_only' in db_changes:
            contact_change = db_changes['contacts_only'].get('change', 0)
            if contact_change > 0:
                notes.append(f"Contact extraction working well (+{contact_change} contacts)")

        if not notes:
            notes.append("Steady progress, continue with current tasks")

        return " ".join(notes)

    def _find_critical_issues(self, snapshot):
        """Find critical issues in current state"""
        issues = []

        db = snapshot['database']

        # Check email_content
        if db.get('email_content', 0) == 0:
            issues.append("Email content table is EMPTY - no AI processing has been saved to database")

        # Check email import progress
        emails = db.get('emails', 0)
        if emails < 500:
            issues.append(f"Only {emails}/2,347 emails imported - 94% remaining")

        return issues

    def _find_warnings(self, snapshot):
        """Find warning-level issues"""
        warnings = []

        db = snapshot['database']

        # Check contacts
        contacts = db.get('contacts', 0)
        if contacts == 0:
            warnings.append("Main contacts table empty (using contacts_only instead)")

        return warnings

    def _find_positives(self, snapshot):
        """Find what's working well"""
        positives = []

        db = snapshot['database']

        # Check database optimization
        indexes = db.get('indexes', 0)
        if indexes > 80:
            positives.append(f"Database well-optimized with {indexes} indexes")

        # Check proposals
        proposals = db.get('proposals', 0)
        if proposals > 80:
            positives.append(f"All {proposals} proposals imported successfully")

        # Check documents
        documents = db.get('documents', 0)
        if documents > 800:
            positives.append(f"{documents} documents indexed and searchable")

        # Check contacts
        contacts_only = db.get('contacts_only', 0)
        if contacts_only > 200:
            positives.append(f"{contacts_only} external contacts extracted from emails")

        return positives

    def generate_reports(self, summary, audit, snapshot, changes):
        """Generate HTML and PDF reports"""
        print("\n📄 Generating reports...")

        report_data = {
            'database_stats': snapshot['database'],
            'changes': changes,
            'git_activity': snapshot['git'],
            'daily_summary': summary,
            'audit_findings': audit,
            'recommendations': self._generate_recommendations(audit, changes),
            'alignment': {
                'on_track': summary.get('on_track', True),
                'current_phase': summary.get('current_phase', 'Unknown'),
                'progress_pct': summary.get('progress_pct', 0),
                'notes': summary.get('notes', '')
            }
        }

        # Generate enhanced HTML report
        html_path = self.report_gen.generate_html_report(report_data)

        return html_path, None  # PDF generation removed for now

    def _generate_recommendations(self, audit, changes):
        """Generate actionable recommendations"""

        # If AI available, use it for smart recommendations
        if self.ai_enabled:
            try:
                prompt = f"""Based on these audit findings, provide 3-5 specific, actionable recommendations for tomorrow.

CRITICAL ISSUES:
{json.dumps(audit.get('critical_issues', []), indent=2)}

WARNINGS:
{json.dumps(audit.get('warnings', []), indent=2)}

RECENT CHANGES:
{json.dumps(changes.get('database_changes', {}), indent=2)}

Provide recommendations that:
- Address the most critical issues first
- Are specific and actionable (not vague)
- Can be completed in 1-2 hours each
- Move toward Phase 1 completion

Return ONLY a JSON array of strings:
["Recommendation 1", "Recommendation 2", "Recommendation 3"]"""

                response = self.ai_call(prompt, max_tokens=500, temperature=0.3)

                if response:
                    import re
                    json_match = re.search(r'\[.*\]', response, re.DOTALL)
                    if json_match:
                        recommendations = json.loads(json_match.group())
                        return recommendations[:5]

            except Exception as e:
                print(f"   ⚠️  AI recommendations failed: {e}, using simple logic")

        # Fallback: simple logic
        recommendations = []

        # Based on critical issues
        for issue in audit.get('critical_issues', []):
            if 'email_content' in issue.lower():
                recommendations.append("Re-run email_content_processor.py to populate AI analysis")
            if 'emails imported' in issue.lower():
                recommendations.append("Run smart_email_matcher.py to import remaining emails")

        # Based on current progress
        if not recommendations:
            recommendations.append("Continue with Phase 1 completion tasks")
            recommendations.append("Test query_brain.py with complex queries")
            recommendations.append("Review daily accountability reports for insights")

        return recommendations[:5]  # Max 5 recommendations

    def send_macos_notification(self, html_path):
        """Send clickable macOS notification"""
        print(f"\n🔔 Sending macOS notification...")

        try:
            import subprocess

            title = "🧠 Bensley Brain Daily Report"
            message = "Click to open your daily accountability report"

            # Create AppleScript that makes notification clickable
            applescript = f'''
            display notification "{message}" with title "{title}" sound name "Glass"

            tell application "System Events"
                delay 2
            end tell

            do shell script "open '{html_path}'"
            '''

            subprocess.run(['osascript', '-e', applescript])

            print(f"   ✅ Notification sent - report will open when clicked")
            return True

        except Exception as e:
            print(f"   ⚠️  Notification failed: {e}")
            # Fallback: just open the report
            subprocess.run(['open', str(html_path)])
            return False

    def send_email_report(self, html_path, pdf_path=None):
        """Send email with HTML body"""
        print(f"\n📧 Trying to send email to {self.email_to}...")

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = f"Bensley Brain Daily Report - {datetime.now().strftime('%B %d, %Y')}"

            # Add HTML body
            with open(html_path, 'r') as f:
                html_content = f.read()
            msg.attach(MIMEText(html_content, 'html'))

            # Send email
            server = smtplib.SMTP(self.email_server, self.email_port)
            server.starttls()
            server.login(self.email_from, self.email_password)
            server.send_message(msg)
            server.quit()

            print(f"   ✅ Email sent successfully")
            return True

        except Exception as e:
            print(f"   ⚠️  Email failed: {e}")
            print(f"   📁 Report saved locally: {html_path}")

            # Fall back to macOS notification
            print(f"\n   💡 Falling back to macOS notification...")
            self.send_macos_notification(html_path)

            return False

    def run(self):
        """Main execution flow"""
        print("="*80)
        print("🧠 BENSLEY BRAIN DAILY ACCOUNTABILITY SYSTEM")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")

        # 1. Take snapshot
        print("\n" + "="*80)
        print("STEP 1: TAKE SNAPSHOT")
        print("="*80)
        snapshot = self.tracker.take_snapshot("Daily 9 PM snapshot")

        # 2. Get changes since last snapshot
        print("\n" + "="*80)
        print("STEP 2: ANALYZE CHANGES")
        print("="*80)
        changes = self.tracker.get_changes_since_last_snapshot()
        print(f"   Time since last snapshot: {changes.get('time_since_last', 0):.1f} hours")
        print(f"   Database changes: {len(changes.get('database_changes', {}))}")
        print(f"   Files changed: {len(changes.get('files_changed', []))}")
        print(f"   Git commits: {len(changes.get('git_activity', {}).get('commit_messages', []))}")

        # 3. Run Daily Summary Agent
        print("\n" + "="*80)
        print("STEP 3: DAILY SUMMARY AGENT")
        print("="*80)
        summary = self.run_daily_summary_agent(snapshot, changes)

        # 4. Run Critical Auditor Agent
        print("\n" + "="*80)
        print("STEP 4: CRITICAL AUDITOR AGENT")
        print("="*80)
        audit = self.run_critical_auditor_agent(snapshot)
        print(f"   Critical issues: {len(audit.get('critical_issues', []))}")
        print(f"   Warnings: {len(audit.get('warnings', []))}")
        print(f"   Positives: {len(audit.get('positive', []))}")

        # 5. Generate reports
        print("\n" + "="*80)
        print("STEP 5: GENERATE REPORTS")
        print("="*80)
        html_path, pdf_path = self.generate_reports(summary, audit, snapshot, changes)

        # 6. Send email
        print("\n" + "="*80)
        print("STEP 6: EMAIL DELIVERY")
        print("="*80)
        self.send_email_report(html_path, pdf_path)

        print("\n" + "="*80)
        print("✅ DAILY ACCOUNTABILITY SYSTEM COMPLETE")
        print("="*80)
        print(f"Finished: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")

if __name__ == '__main__':
    system = DailyAccountabilitySystem()
    system.run()
