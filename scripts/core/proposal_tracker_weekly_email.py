#!/usr/bin/env python3
"""
Proposal Tracker Weekly Emailer
Sends automated weekly proposal tracker summary to Bill
Runs every Monday morning with key metrics and updates
"""

import sqlite3
import smtplib
import os
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta
from typing import Dict, List
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.proposal_tracker_service import ProposalTrackerService

# Use absolute path to database
DB_PATH = os.path.join(os.path.dirname(__file__), "database/bensley_master.db")


class ProposalTrackerWeeklyEmailer:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.service = ProposalTrackerService(db_path)

        # Email configuration
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', 'lukas@bensley.com')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.recipient_email = 'bill@bensley.com'

    def format_currency(self, value: float) -> str:
        """Format value as currency"""
        if value >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"${value / 1_000:.0f}K"
        return f"${value:,.0f}"

    def get_weekly_summary(self) -> Dict:
        """Get proposal tracker summary"""
        return self.service.get_stats()

    def generate_html_email(self, stats: Dict) -> str:
        """Generate HTML email content"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{
            color: #1e40af;
            margin: 0;
            font-size: 28px;
        }}
        .date {{
            color: #6b7280;
            font-size: 14px;
            margin-top: 5px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin: 30px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .metric-card.green {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }}
        .metric-card.orange {{
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        }}
        .metric-card.blue {{
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        }}
        .metric-label {{
            font-size: 13px;
            opacity: 0.9;
            margin-bottom: 5px;
            font-weight: 500;
            letter-spacing: 0.5px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            margin: 0;
        }}
        .status-breakdown {{
            margin: 30px 0;
        }}
        .status-item {{
            background: #f9fafb;
            border-left: 4px solid #d1d5db;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .status-item.proposal-sent {{
            border-left-color: #10b981;
            background: #ecfdf5;
        }}
        .status-item.drafting {{
            border-left-color: #3b82f6;
            background: #eff6ff;
        }}
        .status-item.first-contact {{
            border-left-color: #f59e0b;
            background: #fffbeb;
        }}
        .status-item.on-hold {{
            border-left-color: #ef4444;
            background: #fef2f2;
        }}
        .status-name {{
            font-weight: 600;
            font-size: 15px;
        }}
        .status-count {{
            font-size: 14px;
            color: #6b7280;
            margin-right: 10px;
        }}
        .status-value {{
            font-weight: bold;
            font-size: 16px;
        }}
        .alert {{
            background: #fef3c7;
            border: 1px solid #fbbf24;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
        }}
        .alert-title {{
            color: #92400e;
            font-weight: bold;
            margin: 0 0 5px 0;
        }}
        .alert-text {{
            color: #78350f;
            margin: 0;
            font-size: 14px;
        }}
        .footer {{
            border-top: 1px solid #e5e7eb;
            margin-top: 40px;
            padding-top: 20px;
            text-align: center;
            color: #6b7280;
            font-size: 13px;
        }}
        .link-button {{
            display: inline-block;
            background: #2563eb;
            color: white;
            padding: 12px 24px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Weekly Proposal Tracker Summary</h1>
            <div class="date">{datetime.now().strftime("%B %d, %Y")}</div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card green">
                <div class="metric-label">TOTAL PROPOSALS</div>
                <div class="metric-value">{stats['total_proposals']}</div>
            </div>
            <div class="metric-card blue">
                <div class="metric-label">PIPELINE VALUE</div>
                <div class="metric-value">{self.format_currency(stats['total_pipeline_value'])}</div>
            </div>
            <div class="metric-card orange">
                <div class="metric-label">NEEDS FOLLOW-UP</div>
                <div class="metric-value">{stats['needs_followup']}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">AVG DAYS IN STATUS</div>
                <div class="metric-value">{stats['avg_days_in_status']:.0f}</div>
            </div>
        </div>
"""

        # Alert for follow-ups
        if stats['needs_followup'] > 0:
            html += f"""
        <div class="alert">
            <p class="alert-title">⚠️ Action Required</p>
            <p class="alert-text">{stats['needs_followup']} proposal{'s' if stats['needs_followup'] > 1 else ''} ha{'ve' if stats['needs_followup'] > 1 else 's'} been in the same status for more than 14 days and may need follow-up.</p>
        </div>
"""

        # Status breakdown
        html += """
        <div class="status-breakdown">
            <h2 style="color: #1e40af; font-size: 20px; margin-bottom: 15px;">Status Breakdown</h2>
"""

        status_classes = {
            "Proposal Sent": "proposal-sent",
            "Drafting": "drafting",
            "First Contact": "first-contact",
            "On Hold": "on-hold"
        }

        for status_item in stats['status_breakdown']:
            status = status_item['current_status']
            count = status_item['count']
            value = status_item['total_value']
            css_class = status_classes.get(status, '')

            html += f"""
            <div class="status-item {css_class}">
                <div>
                    <span class="status-name">{status}</span>
                    <span class="status-count">({count} proposal{'s' if count != 1 else ''})</span>
                </div>
                <div class="status-value">{self.format_currency(value)}</div>
            </div>
"""

        html += """
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="http://localhost:3002/tracker" class="link-button">View Full Tracker Dashboard</a>
        </div>

        <div class="footer">
            <p>This is an automated weekly summary from the Bensley Operations System.</p>
            <p>Generated on {}</p>
        </div>
    </div>
</body>
</html>
""".format(datetime.now().strftime("%B %d, %Y at %I:%M %p"))

        return html

    def send_email(self, test_mode: bool = False, recipient_override: str = None):
        """
        Send weekly proposal tracker email

        Args:
            test_mode: If True, print email instead of sending
            recipient_override: Override recipient email (for testing)
        """
        try:
            # Get stats
            print("Fetching proposal tracker stats...")
            stats = self.get_weekly_summary()

            # Generate email content
            print("Generating email content...")
            html_body = self.generate_html_email(stats)

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📊 Weekly Proposal Tracker Summary - {datetime.now().strftime('%B %d, %Y')}"
            msg['From'] = self.smtp_user
            msg['To'] = recipient_override or self.recipient_email

            # Attach HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            # Check for PDF attachment
            pdf_path = "/tmp/proposal_tracker_report.pdf"
            if os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
                    pdf_attachment.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=f"Proposal_Tracker_{datetime.now().strftime('%Y-%m-%d')}.pdf"
                    )
                    msg.attach(pdf_attachment)
                print(f"Attached PDF: {pdf_path}")

            if test_mode:
                print("\n" + "="*60)
                print("TEST MODE - Email would be sent with:")
                print(f"To: {msg['To']}")
                print(f"Subject: {msg['Subject']}")
                print(f"Total Proposals: {stats['total_proposals']}")
                print(f"Pipeline Value: {self.format_currency(stats['total_pipeline_value'])}")
                print(f"Needs Follow-up: {stats['needs_followup']}")
                print("="*60 + "\n")
                return True

            # Send email
            print(f"Sending email to {msg['To']}...")
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print("✅ Email sent successfully!")
            return True

        except Exception as e:
            print(f"❌ Error sending email: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Send weekly proposal tracker summary email')
    parser.add_argument('--test', action='store_true', help='Test mode - print email instead of sending')
    parser.add_argument('--recipient', type=str, help='Override recipient email')
    parser.add_argument('--db', type=str, default=DB_PATH, help='Database path')

    args = parser.parse_args()

    print("="*60)
    print("Proposal Tracker Weekly Email")
    print("="*60)

    emailer = ProposalTrackerWeeklyEmailer(args.db)
    success = emailer.send_email(test_mode=args.test, recipient_override=args.recipient)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
